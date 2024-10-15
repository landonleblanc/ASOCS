import time
from adafruit_datetime import datetime, timedelta
import board
import busio
import digitalio
import supervisor
import adafruit_ds3231
import storage
from max6675 import MAX6675
import neopixel

class Data:
    def __init__(self):
        self.air = 0
        self.oven = 0
        self.last_update = None
    
    def update(self, rtc, tc):
        self.air = rtc.temperature
        self.oven = tc.read()
        self.next_update = datetime(rtc.datetime.tm_year, rtc.datetime.tm_mon, rtc.datetime.tm_mday, rtc.datetime.tm_hour, rtc.datetime.tm_min, rtc.datetime.tm_sec) + timedelta(seconds=30) 

class Settings:
    def __init__(self, year, month, day):
        self.control_temp = None
        self.start_time = datetime(year, month, day, 11, 0, 0)
        self.end_time = datetime(year, month, day, 21, 45, 0)
        self.pid = False

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

def main(): 
    rtc, tc, relay, led = init_hw() #initialize the hardware components
    settings = Settings(rtc.datetime.tm_year, rtc.datetime.tm_mon, rtc.datetime.tm_mday) #initialize the settings class
    # settings.load() #load the settings from the settings.json file or use defaults if unsuccessful
    current_time = datetime(rtc.datetime.tm_year, rtc.datetime.tm_mon, rtc.datetime.tm_mday, rtc.datetime.tm_hour, rtc.datetime.tm_min, rtc.datetime.tm_sec)
    data = Data() #initialize the data class
    data.update(rtc, tc) #update the data class with the current values
    print('Startup complete, entering main loop...')
    while True:
        led.show()
        current_time = datetime(rtc.datetime.tm_year, rtc.datetime.tm_mon, rtc.datetime.tm_mday, rtc.datetime.tm_hour, rtc.datetime.tm_min, rtc.datetime.tm_sec)
        if current_time >= data.next_update:
            data.update(rtc, tc)
            print(f'[{current_time}]: Air: {data.air}°C Oven: {data.oven}°C')
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
    # if supervisor.runtime.serial_connected:
    #     while True:
    #         time.sleep(10)
    #         input('Enter debug mode? y/n?')
    #         if input == 'y':
    #             main()
    #         else:
    #             continue     
    # else:
    #     print('Not connected to serial, running main loop...')
    #     main()
