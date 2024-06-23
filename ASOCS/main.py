import json
import random
import board
import busio
import time
import digitalio
import adafruit_ds3231
import adafruit_ssd1306
import rotaryio
import storage
from simple_pid import PID
from max6675 import MAX6675
#TODO use datetime instead of time???

def set_time(rtc, oled):
    try:
        display_text(oled, 'Time reset\ndetected...')
        display_text(oled, 'See terminal\nfor instructions')
        print('Time reset detected, please set the time:')
        year = int(input('Enter the year: '))
        month = int(input('Enter the month: '))
        day = int(input('Enter the day: '))
        hour = int(input('Enter the hour: '))
        minute = int(input('Enter the minute: '))
        t = time.struct_time((year, month, day, hour, minute, 0, 0, 0, 0))
        print(f'Setting time to {t}')
        rtc.datetime = t #set the time
        print('Time set successfully')
        print("Disconnect the USB from the PC and connect to the power supply")
    except ValueError:
        print('Invalid input, please try again')
        set_time(rtc, oled)
    return

def update_oled(oled, data, time, controlling, relay_state, enabled):
    #TODO make all display functions and hw init functions into a class in submodule
    def add_leading_zeros(num):
        return "{:02d}".format(num)
    oled.fill(0)
    hour = add_leading_zeros(time.tm_hour)
    minute = add_leading_zeros(time.tm_min)
    oled.text(f'Time: {hour}:{minute}', 0, 0, 1)
    oled.text(f'Air Temp: {data["air"]} C', 0, 10, 1)
    oled.text(f'Oven Temp: {data["oven"]} C', 0, 20, 1)
    if enabled:
        oled.text(f'Control: Enabled', 0, 30, 1)
    else:
        oled.text(f'Control: Disabled', 0, 30, 1)
    if relay_state and controlling:
        oled.text(f'Status: Heating', 0, 40, 1)
    else:
        oled.text(f'Status: Idle', 0, 40, 1)
    oled.text(f'Toggle control -->', 0, 50, 1)
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

def display_text(oled, text, duration=2):
    text = text.split('\n')
    reset_oled(oled)
    for i in range(len(text)):
        oled.text(text[i], 0, i*10, 1)
    oled.show()
    time.sleep(duration)
    reset_oled(oled)
    return

def init_hw():
    #Hardware Startup Sequence
    rtc_i2c = busio.I2C(sda=board.GP16, scl=board.GP17)#create an i2c object on pins 21(SDA) and 22(SCL)
    oled_i2c = busio.I2C(scl=board.GP7, sda=board.GP6)#create an i2c object on pins 9(SDA) and 10(SCL)
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
    encoder = rotaryio.IncrementalEncoder(board.GP10, board.GP11)
    button = digitalio.DigitalInOut(board.GP13)
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
    except Exception as e:
        print(e)
        settings = {
            'control_temp': 50, 
            'start_time': 660, 
            'end_time': 1020, 
            'kP': 1,
            'kI': 0.1,
            'kD': 0.1,
            'reset_time': False}
        make_filesystem_writable()
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
        print('Settings not found, using defaults')
        display_text(oled, 'Settings\nNot Found\nUsing Defaults')
        return settings

def save_settings(settings):
    make_filesystem_writable()
    try:
        with open('settings.json', 'w') as f:
            json.dump(settings, f)
    except Exception as e:
        print(e)
        print('Error saving settings')
    try:
        with open('settings.json', 'r') as f:
            assert json.load(f) == settings 
        return True
    except Exception as e:
        print(f'Settings did not match: {e}')
    return False

def make_filesystem_writable():
    try:
        if storage.getmount("/").readonly:
            # Remount the filesystem as read-write
            storage.remount("/", readonly=False)
            print("Filesystem remounted as writable")
    except Exception as e:
        print(e)
        print("Failed to remount filesystem as writable")

def init_pid(settings):
    pid = PID(settings['kP'], settings['kI'], settings['kD'], setpoint=settings['control_temp'])
    pid.auto_mode = True
    pid.output_limits = (0, 10)
    return pid

def main(): 
    data = {'air': 15, 'oven': 15} #the measurement data. May add other measurements later
    rtc, oled, tc, relay, encoder, button = init_hw() #initialize the hardware components
    if rtc.datetime.tm_year <= 2000: #users sets the time if there isn't one
        set_time(rtc, oled) #set the time if it has defaulted
    pid_time = 0 #How long the element should be turned on for in minutes
    controlling = False #whether or not the oven needs to be controlled
    settings = load_settings(oled) #load the settings from the settings.json file or use defaults if unsuccessful
    # if settings['reset_time'] == True:
    #     set_time(rtc, oled)
    #     settings['reset_time'] = False
    #     save_settings(settings)
    pid = init_pid(settings) #Creates the pid class
    time_min = 0
    enabled = False
    data['air'] = rtc.temperature #obtain the "air" temp from the rtc
    data['oven'] = tc.read() #obtain the oven temp from the thermocouple
    datetime = rtc.datetime
    update_oled(oled, data, datetime, controlling, relay.value, enabled) #update the oled display
    print('Startup complete, entering main loop...')
    while True:
        prev_time = time_min
        datetime = rtc.datetime
        time_min = int(datetime.tm_hour*60 + datetime.tm_min) #convert the time to minutes
        if time_min >= prev_time + 1:
            data['air'] = rtc.temperature #obtain the "air" temp from the rtc
            data['oven'] = tc.read() #obtain the oven temp from the thermocouple
            print(f'Time:{datetime.tm_hour}:{datetime.tm_min} Air: {data["air"]} C Oven: {data["oven"]} C')
            update_oled(oled, data, datetime, controlling, relay.value, enabled) #update the oled display
        if enabled:
            if controlling:
                if time_min > settings['end_time']:
                    controlling = False
                    update_oled(oled, data, datetime, controlling, relay.value, enabled)
                    print('End time exceeded, turning oven PID control off')
                if data['oven'] < settings['control_temp'] and relay.value == False:
                    pid_time = time_min + pid(data['oven']) #set the ending time for the element
                    update_oled(oled, data, datetime, controlling, relay.value, enabled)
                    print('Turning on oven element')
                if time_min < pid_time:
                    if relay.value == False:
                        relay.value = True #turn the element on if the pid duration hasn't finished
                        update_oled(oled, data, datetime, controlling, relay.value, enabled)
                else:
                    if relay.value == True:
                        relay.value = False #turn the element off
                        update_oled(oled, data, datetime, controlling, relay.value, enabled)
                    print('Turning off oven element')
                # update_oled(oled, data, datetime, controlling, relay.value, enabled)
            else:
                relay.value = False
                if data['oven'] < settings['control_temp'] and time_min > settings['start_time'] and time_min < settings['end_time']:
                    controlling = True
                    update_oled(oled, data, datetime, controlling, relay.value, enabled)
                    print('Conditions not met, turning oven PID control on')
        if button.value == False:  
            if enabled:
                display_text(oled, 'Oven Control:\nDisabled')
                print('Oven control disabled')
                relay.value = False
                enabled = False
            else:
                display_text(oled, 'Oven Control:\nEnabled')
                print('Oven control enabled')
                enabled = True
            update_oled(oled, data, datetime, controlling, relay.value, enabled)
        time.sleep(0.01)
    
if __name__ == '__main__':
    main()