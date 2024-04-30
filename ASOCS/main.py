import json
import random
import board
import busio
import time
import digitalio
import adafruit_ds3231
import adafruit_ssd1306
import rotaryio
from simple_pid import PID
from max6675 import MAX6675


def set_time(rtc):
    #This function is currently useless
    #TODO: Update to be updated via ui
    if rtc.datetime.tm_year == 0: #users sets the time if there isn't one
        print('Enter the current date and time in the following format then press enter:\n YYYY,MM,DD,HH,MM,SS,WDAY,DOY')
        t = input()
        t = t.split(',') #turn into list
        t.append(-1)#add dst to the end of the list
        t = time.struct_time(t) #structure the user input
        print(t)
        rtc.datetime = t #set the time
    return

def update_oled(oled, data, time, controlling, relay_state):
    oled.text(f'Time: {time.tm_hour}:{time.tm_min}', 0, 0, 1)
    oled.text(f'Air Temp: {data["air"]}C', 0, 10, 1)
    oled.text(f'Oven Temp: {data["oven"]}C', 0, 20, 1)
    if controlling:
        oled.text(f'Oven Ctrl: Enabled', 0, 30, 1)
    else:
        oled.text(f'Oven Ctrl: Disabled', 0, 30, 1)
    if relay_state:
        oled.text(f'Element: On', 0, 40, 1)
    else:
        oled.text(f'Element: Off', 0, 40, 1)
    oled.text(f'Press select for menu', 0, 50, 1)
    oled.show()
    return

def data_log():
    pass

def reset_oled(oled): #clears the oled display
    oled.fill(0)
    oled.show()
    return

def fill_oled_random(oled):
    for x in range(oled.width):
        for y in range(oled.height):
            oled.pixel(x, y, random.randint(0, 1))
    oled.show()
    return

def display_text(oled, text, duration=1):
    text = text.split('\n')
    for i in range(len(text)):
        oled.text(text[i], 0, i*10, 1)
    oled.show()
    time.sleep(duration)
    reset_oled(oled)
    return

def display_menu(oled, menu, encoder, button):
    selected = 0
    while True:
        oled.text(menu[selected], 0, 0, 1)
        oled.show()
        if button.value:
            return selected
        if encoder.position < 0:
            selected -= 1
            if selected < 0:
                selected = len(menu) - 1
        elif encoder.position > 0:
            selected += 1
            if selected > len(menu) - 1:
                selected = 0
        time.sleep(0.1)
    return

def init_hw():
    #Hardware Startup Sequence
    rtc_i2c = busio.I2C(board.GP19, board.GP18)#create an i2c object on pins 18 and 19
    oled_i2c = busio.I2C(board.GP13, board.GP12)#create an i2c object on pins 12 and 13
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, oled_i2c)#initialize the lcd
    fill_oled_random(oled)
    time.sleep(2)
    reset_oled(oled)
    print('Display initialized')
    display_text(oled, 'Initializing\nSystem...')
    rtc = adafruit_ds3231.DS3231(rtc_i2c)#initialize the ds3231
    #set_time()#set the time if it has defaulted
    print('RTC initialized')
    tc = MAX6675(board.GP2, board.GP3, board.GP4)
    print('Thermocouple initialized')
    relay = digitalio.DigitalInOut(board.GP28) #assign gpio pin 28 to the relay
    relay.direction = digitalio.Direction.OUTPUT
    print('Relay initialized')
    encoder = rotaryio.IncrementalEncoder(board.GP20, board.GP21)
    button = digitalio.DigitalInOut(board.GP22)
    button.direction = digitalio.Direction.INPUT
    button.pull = digitalio.Pull.UP
    print('Rotary encoder initialized')
    print('System Initialized')
    display_text(oled, 'System\nInitialized')
    reset_oled(oled)
    #End Hardware Startup Sequence
    return rtc, oled, tc, relay, encoder, button

def load_settings(oled):
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        print('Settings loaded successfully')
        display_text(oled, 'Settings\nLoaded')
        return settings
    except:
        settings = {'control_temp': 50, 'start_time': 660, 'end_time': 1020}
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        print('Settings not found, using defaults')
        display_text(oled, 'Settings\nNot Found\nUsing Defaults')
        return settings

def save_settings(settings):
    with open('settings.json', 'w') as f:
        json.dump(settings, f)
    try:
        with open('settings.json', 'r') as f:
            assert json.load(f) == settings 
        return True
    except:
        print('Error saving settings')
    return False

def init_pid(temp):
    pid = PID(1, 0.1, 0.05, setpoint=temp)
    pid.auto_mode = True
    pid.output_limits = (0, 10)
    return pid

def main():
    data = {'air': 15, 'oven': 15} #the measurement data. May add other measurements later
    rtc, oled, tc, relay, encoder, button = init_hw() #initialize the hardware components
    pid_time = 0 #How long the element should be turned on for in minutes
    controlling = False #whether or not the oven needs to be controlled
    settings = load_settings(oled) #load the settings from the settings.json file or use defaults if unsuccessful
    pid = init_pid(settings['control_temp']) #Creates the pid class
    i = 0
    while True:
        previous_data = data
        previous_controlling = controlling
        previous_relay_value = relay.value
        datetime = rtc.datetime
        time_min = int(datetime.tm_hour*60 + datetime.tm_min) #convert the time to minutes
        data['air'] = rtc.temperature #obtain the "air" temp from the rtc
        data['oven'] = tc.read() #obtain the oven temp from the thermocouple
        if controlling == False: #if we aren't currently controlling, check if the desired conditions are not met
            relay.value = False
            if data['oven'] < settings['control_temp'] and time_min > settings['start_time'] and time_min < settings['end_time']:
                controlling = True
                print('Conditions not met, turning oven PID control on')
        elif controlling == True:
            if time_min > settings['end_time']:
                controlling = False
                print('End time exceeded, turning oven PID control off')
            pid_output = pid(data['oven']) #if control is needed, run the PID
            pid_time = time_min + pid_output * 60 #set the ending time for the element
        if time_min < pid_time and controlling:
            relay.value = True #turn the element on if the pid duration hasn't finished
        else:
            relay.value = False #turn the element off
        if data != previous_data or controlling != previous_controlling or relay.value != previous_relay_value:
            update_oled(oled, data, datetime, controlling, relay.value) #update the oled display
        if not button.value:
            relay.value = False
            print('Button pressed')
            #display_text(oled, 'Button\nPressed')
        # i += 1
        # print(i)
        #time.sleep(0.01)
    
if __name__ == '__main__':
    main()
#TODO: Establish multiplier for pid output to time in minutes
#TODO: Store any user editable params in settings.json
#TODO: Implement a menu system
#TODO: Implement a logging system
#TODO: Implement rotary encoder for menu navigation