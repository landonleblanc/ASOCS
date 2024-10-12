import sys
import time
import json
# import yaml
import board
import busio
import digitalio
import adafruit_ds3231
import storage
from max6675 import MAX6675
import neopixel


class Data:
    def __init__(self, rtc: object, tc: object) -> None:
        self.rtc = rtc
        self.tc = tc
        self.air = 0
        self.oven = 0
        self.last_update = None
        
    def update(self) -> None:
        self.air = self.rtc.temperature
        self.oven = self.tc.read()
        self.last_update = self.rtc.datetime
    
# class Time:
#     def __init__(self, rtc: object) -> None:
#         self.rtc = rtc
#         self.datetime = None
#         self.minutes = None
#         self.update()

#     def update(self) -> None:
#         self.datetime = self.rtc.datetime
#         self.timemin = int(self.datetime.tm_hour*60 + self.datetime.tm_min)

#     def set_time(self, hour: int, minute: int) -> None:
#         t = time.struct_time((self.datetime.tm_year, self.datetime.tm_mon, self.datetime.tm_mday, hour, minute, 0, 0, 0, 0))
#         self.rtc.datetime = t
#         self.update()

#     def formatted(self) -> str:
#         return f'{self.datetime.tm_hour}:{self.datetime.tm_min}'

class Settings:
    def __init__(self):
        self.control_temp = None
        self.start_time = None
        self.end_time = None
        self.pid = False

    def load(self):
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)
            self.control_temp = settings['control_temp']
            self.start_time = settings['start_time']
            self.end_time = settings['end_time']
            self.pid = settings['pid']
            print('Settings loaded successfully')
        except Exception as e:
            print(e)
            print('Settings not found')
    
    def save(self):
        make_filesystem_writable()
        settings = {
            'control_temp': self.control_temp,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'pid': self.pid
        }
        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(e)
            print('Error saving settings')

class Serial:
    def __init__(self):
        pass



def init_hw():
    #Hardware Startup Sequence
    rtc_i2c = busio.I2C(sda=board.GP14, scl=board.GP15)#create an i2c object on pins 21(SDA) and 22(SCL)
    rtc = adafruit_ds3231.DS3231(rtc_i2c)#initialize the ds3231
    print('RTC initialized')
    tc = MAX6675(board.GP18, board.GP19, board.GP16)
    print('Thermocouple initialized')
    relay = digitalio.DigitalInOut(board.GP28) #assign gpio pin 28 to the relay
    relay.direction = digitalio.Direction.OUTPUT
    print('Relay initialized')
    # Initialize the NeoPixel LED
    num_pixels = 4
    led = neopixel.NeoPixel(board.GP22, num_pixels)
    # led = digitalio.DigitalInOut(board.GP27) #assign gpio pin 27 to the led
    # led.direction = digitalio.Direction.OUTPUT
    print('LED initialized')
    print('System Initialized')
    return rtc, tc, relay, led

def make_filesystem_writable():
    try:
        if storage.getmount("/").readonly:
            # Remount the filesystem as read-write
            storage.remount("/", readonly=False)
            print("Filesystem remounted as writable")
    except Exception as e:
        print(e)
        print("Failed to remount filesystem as writable")

def main(): 
    rtc, tc, relay, led = init_hw() #initialize the hardware components
    data = Data(rtc, tc) #initialize the data class
    settings = Settings() #initialize the settings class
    settings.load() #load the settings from the settings.json file or use defaults if unsuccessful
    data.update() #update the data class with the current values
    print('Startup complete, entering main loop...')
    while True:
        current_time = rtc.datetime
        if current_time >= data.last_update + 1:
            data.update()
            print(f'[{current_time}]: {data.air}°C Oven: {data.oven}°C')
        if current_time > settings.start_time and current_time < settings.end_time:
            if not settings.pid:
                if data.oven < settings.control_temp:
                    relay.value = True
                    led.value = True
                else:
                    relay.value = False
                    led.value = False

        time.sleep(0.01)
    
if __name__ == '__main__':
    main()