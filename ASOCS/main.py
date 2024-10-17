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

class Relay:
    def __init__(self, pin):
        self.relay = digitalio.DigitalInOut(pin)
        self.relay.direction = digitalio.Direction.OUTPUT

    def on(self):
        self.relay.value = True

    def off(self):
        self.relay.value = False

class LEDs:
    def __init__(self, pin):
        self.led = neopixel.NeoPixel(pin, 4)

    def off(self):
        self.led.fill((0, 0, 0))

    def solid(self, color):
        self.led.fill(color)

    def blink(self, color):
        self.led.fill(color)
        time.sleep(0.5)
        self.led.fill((0, 0, 0))
        time.sleep(0.5)

    def fade(self, color):
        #TODO add colors
        for i in range(0, 255, 5):
            self.led.fill((i, i, i))
            time.sleep(0.01)
        for i in range(255, 0, -5):
            self.led.fill((i, i, i))
            time.sleep(0.01)
    
    def scan(self, color):
        for i in range(4):
            self.led[i] = color
            time.sleep(0.5)
            self.led[i] = (0, 0, 0)

    def rainbow(self):
        for i in range(4):
            self.led[i] = (255, 0, 0)
            time.sleep(0.5)
            self.led[i] = (0, 255, 0)
            time.sleep(0.5)
            self.led[i] = (0, 0, 255)
            time.sleep(0.5)
            self.led[i] = (255, 255, 0)
            time.sleep(0.5)
            self.led[i] = (255, 0, 255)
            time.sleep(0.5)
            self.led[i] = (0, 255, 255)
            time.sleep(0.5)
            self.led[i] = (255, 255, 255)
            time.sleep(0.5)

class ASOCS:
    def __init__(self):
        self.rtc = None
        self.tc = None
        self.relay = None
        self.led = None

        self.current_time = None
        self.next_update = None

        self.control_temp = None
        self.start_time = None
        self.end_time = None

        self.air_temp = 0
        self.oven_temp = 0

    def init_hw(self):
        rtc_i2c = busio.I2C(sda=board.GP14, scl=board.GP15)
        self.rtc = adafruit_ds3231.DS3231(rtc_i2c)
        print('RTC initialized')
        self.tc = MAX6675(board.GP18, board.GP19, board.GP16)
        print('Thermocouple initialized')
        self.relay = Relay(board.GP28)
        print('Relay initialized')
        self.led = LEDs(board.GP22)
        print('LED initialized')
        print('System Initialized')

    def update_data(self):
        self.air_temp = self.rtc.temperature
        self.oven_temp = self.tc.read()
        self.next_update = self.current_time + timedelta(seconds=30)
    def load_settings(self):
        pass

    def save_settings(self):
        pass

def main():
    asocs = ASOCS()
    asocs.init_hw()
    asocs.load_settings()
    print('Startup complete, entering main loop...')
    asocs.current_time = datetime(asocs.rtc.datetime.tm_year, asocs.rtc.datetime.tm_mon, asocs.rtc.datetime.tm_mday, asocs.rtc.datetime.tm_hour, asocs.rtc.datetime.tm_min, asocs.rtc.datetime.tm_sec)
    asocs.update_data()
    while True:
        #update the current time
        asocs.current_time = datetime(asocs.rtc.datetime.tm_year, asocs.rtc.datetime.tm_mon, asocs.rtc.datetime.tm_mday, asocs.rtc.datetime.tm_hour, asocs.rtc.datetime.tm_min, asocs.rtc.datetime.tm_sec)
        #print the current time and temps over serial
        print(f'[{asocs.current_time}]: Air: {asocs.air_temp}°C Oven: {asocs.oven_temp}°C')
        #check if we need to update the data, updating if needed
        if asocs.current_time > asocs.next_update:
            asocs.update_data()
        
        #check we are within the time window for oven control
        if asocs.current_time > asocs.start_time and asocs.current_time < asocs.end_time:

            #turn on the heating element if the oven temp is less than the control temp, otherwise keep it off
            if asocs.oven_temp < asocs.control_temp:
                asocs.relay.on()
                asocs.led.solid((255, 0, 0))
            else:
                asocs.relay.off()
                asocs.led.off()
        time.sleep(0.01)

def standby():
        while True:
            time.sleep(10)
            input('Enter debug mode? y/n?')
            if input() == 'y':
                main()
            else:
                continue 

if __name__ == '__main__':
    main()
    if supervisor.runtime.serial_connected:
        #enter standby mode if serial is connected
        standby()
    else:
        #enter normal operation if serial is not connected
        main()
