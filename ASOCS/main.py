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
    def add_leading_zeros(num):
        return "{:02d}".format(num)
    oled.fill(0)
    hour = add_leading_zeros(time.tm_hour)
    minute = add_leading_zeros(time.tm_min)
    oled.text(f'Time: {hour}:{minute}', 0, 0, 1)
    oled.text(f'Air Temp: {data["air"]} C', 0, 10, 1)
    oled.text(f'Oven Temp: {data["oven"]} C', 0, 20, 1)
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

def reset_oled(oled): #clears the oled display
    oled.fill(0)
    oled.show()
    return

def fill_oled_random(oled, duration=1):
    for x in range(oled.width):
        for y in range(oled.height):
            oled.pixel(x, y, random.randint(0, 1))
    oled.show()
    time.sleep(duration)
    return

def display_text(oled, text, duration=1):
    text = text.split('\n')
    for i in range(len(text)):
        oled.text(text[i], 0, i*10, 1)
    oled.show()
    time.sleep(duration)
    reset_oled(oled)
    return

def update_menu(oled, selected):
    oled.fill(0)
    menu = ['System Time', 'Control Temp', 'Start Time', 'End Time', 'Save Settings', 'Exit']
    for i in range(len(menu)):
        if i == selected:
            oled.text(menu[i], 0, i*10, 1)
        else:
            oled.text(menu[i], 0, i*10, 1)
    oled.show()
    return

def menu(oled, encoder, button, rtc, settings):
    fill_oled_random(oled)
    selected = 0
    update_menu(oled, selected)
    while True:
        if encoder.position > 0:
            selected += 1
            encoder.position = 0
            print(selected)
            if selected > 6:
                selected = 0
            update_menu(oled, selected)
        elif encoder.position < 0:
            selected -= 1
            encoder.position = 0
            print(selected)
            if selected < 0:
                selected = 6
            update_menu(oled, selected)
        if not button.value:
            if selected == 0:
                rtc.datetime = set_time(rtc)
            elif selected == 1:
                pass
            elif selected == 2:
                pass
            elif selected == 3:
                pass
            elif selected == 4:
                pass
            elif selected == 5:
                pass
            elif selected == 6:
                break
    fill_oled_random(oled, 2)
    return

def init_hw():
    #Hardware Startup Sequence
    rtc_i2c = busio.I2C(board.GP19, board.GP18)#create an i2c object on pins 18 and 19
    oled_i2c = busio.I2C(board.GP13, board.GP12)#create an i2c object on pins 12 and 13
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, oled_i2c)#initialize the lcd
    fill_oled_random(oled, 3)
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
    time_min = 0
    while True:
        prev_time = time_min
        datetime = rtc.datetime
        time_min = int(datetime.tm_hour*60 + datetime.tm_min) #convert the time to minutes
        if time_min >= prev_time + 1:
            data['air'] = rtc.temperature #obtain the "air" temp from the rtc
            data['oven'] = tc.read() #obtain the oven temp from the thermocouple
            update_oled(oled, data, datetime, controlling, relay.value) #update the oled display
        if not controlling: #if we aren't currently controlling, check if the desired conditions are not met
            relay.value = False
            if data['oven'] < settings['control_temp'] and time_min > settings['start_time'] and time_min < settings['end_time']:
                controlling = True
                update_oled(oled, data, datetime, controlling, relay.value)
                print('Conditions not met, turning oven PID control on')
        elif controlling:
            if time_min > settings['end_time']:
                controlling = False
                update_oled(oled, data, datetime, controlling, relay.value)
                print('End time exceeded, turning oven PID control off')
            if data['oven'] < settings['control_temp'] and relay.value == False:
                pid_time = time_min + pid(data['oven']) #set the ending time for the element
                update_oled(oled, data, datetime, controlling, relay.value)
            if time_min < pid_time:
                relay.value = True #turn the element on if the pid duration hasn't finished
                update_oled(oled, data, datetime, controlling, relay.value)
            else:
                relay.value = False #turn the element off
                update_oled(oled, data, datetime, controlling, relay.value)
        if not button.value:
            relay.value = False
            print('Button pressed')
            menu(oled, encoder, button, rtc, settings)
        # i += 1
        # print(i)
        time.sleep(0.01)
    
if __name__ == '__main__':
    main()
#TODO: Implement a menu system
#TODO: Implement a logging system
#TODO: Implement rotary encoder for menu navigation