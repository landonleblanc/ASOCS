import time
import json
import random
import board
import busio
import digitalio
import adafruit_ds3231
import storage
from simple_pid import PID
from max6675 import MAX6675
#TODO use datetime instead of time???

class Data:
    def __init__(self, rtc: object, tc: object) -> None:
        self.rtc = rtc
        self.tc = tc
        self.air = 0
        self.oven = 0
        return
    def update(self) -> None:
        self.air = self.rtc.temperature
        self.oven = self.tc.read()
        return
    
class Status:
    def __init__(self):
        self.relay_state = False
        return
    
class Time:
    def __init__(self, rtc: object) -> None:
        self.datetime = rtc.datetime
        self.timemin = int(self.datetime.tm_hour*60 + self.datetime.tm_min)
        return
    def update(self, rtc: object) -> None:
        self.datetime = rtc.datetime
        self.timemin = int(self.datetime.tm_hour*60 + self.datetime.tm_min)
        return



def set_time(rtc, oled):
    try:
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

def init_hw():
    #Hardware Startup Sequence
    rtc_i2c = busio.I2C(sda=board.GP16, scl=board.GP17)#create an i2c object on pins 21(SDA) and 22(SCL)
    rtc = adafruit_ds3231.DS3231(rtc_i2c)#initialize the ds3231
    print('RTC initialized')
    tc = MAX6675(board.GP2, board.GP3, board.GP4)
    print('Thermocouple initialized')
    relay = digitalio.DigitalInOut(board.GP28) #assign gpio pin 28 to the relay
    relay.direction = digitalio.Direction.OUTPUT
    print('Relay initialized')
    print('System Initialized')
    #End Hardware Startup Sequence
    return rtc, tc, relay

def load_settings():
    try:
        with open('settings.json', 'r') as f:
            settings = json.load(f)
        print('Settings loaded successfully')
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
        print(rtc.datetime)
        set_time(rtc, oled) #set the time if it has defaulted
    pid_time = 0 #How long the element should be turned on for in minutes
    controlling = False #whether or not the oven needs to be controlled
    settings = load_settings(oled) #load the settings from the settings.json file or use defaults if unsuccessful
    pid = init_pid(settings) #Creates the pid class
    time_min = 0
    enabled = False
    data['air'] = rtc.temperature #obtain the "air" temp from the rtc
    data['oven'] = tc.read() #obtain the oven temp from the thermocouple
    datetime = rtc.datetime
    print('Startup complete, entering main loop...')
    while True:
        prev_time = time_min
        datetime = rtc.datetime
        time_min = int(datetime.tm_hour*60 + datetime.tm_min) #convert the time to minutes
        if time_min >= prev_time + 1:
            data['air'] = rtc.temperature #obtain the "air" temp from the rtc
            data['oven'] = tc.read() #obtain the oven temp from the thermocouple
            print(f'Time:{datetime.tm_hour}:{datetime.tm_min} Air: {data["air"]} C Oven: {data["oven"]} C')
        if enabled:
            if controlling:
                if time_min > settings['end_time']:
                    controlling = False
                    print('End time exceeded, turning oven PID control off')
                if data['oven'] < settings['control_temp'] and relay.value == False:
                    pid_time = time_min + pid(data['oven']) #set the ending time for the element
                    print('Turning on oven element')
                if time_min < pid_time:
                    if relay.value == False:
                        relay.value = True #turn the element on if the pid duration hasn't finished
                else:
                    if relay.value == True:
                        relay.value = False #turn the element off
                    print('Turning off oven element')
                # update_oled(oled, data, datetime, controlling, relay.value, enabled)
            else:
                relay.value = False
                if data['oven'] < settings['control_temp'] and time_min > settings['start_time'] and time_min < settings['end_time']:
                    controlling = True
                    print('Conditions not met, turning oven PID control on')
        if button.value == False:  
            if enabled:
                print('Oven control disabled')
                relay.value = False
                enabled = False
            else:
                print('Oven control enabled')
                enabled = True
        time.sleep(0.01)
    
if __name__ == '__main__':
    main()