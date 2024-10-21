import time
import json
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

    def solid(self, color: tuple):
        self.led.fill(color)

    def blink(self, color: tuple, rate: float = 0.2, blinks: int = 5):
        for i in range(blinks):
            self.led.fill(color)
            time.sleep(rate)
            self.led.fill((0, 0, 0))
            time.sleep(rate)

    def fade(self, color: tuple, rate: float = 1):
        #TODO add colors
        for i in range(0, 255, 5):
            self.led.fill((i, i, i))
            time.sleep(0.01)
        for i in range(255, 0, -5):
            self.led.fill((i, i, i))
            time.sleep(0.01)

    def rainbow(self, duration: int = 5):
        colors = [
            (255, 0, 0),    # Red
            (255, 115, 0),  # Orange
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (54, 0, 63),  # Purple
            (255, 255, 255) # White
        ]

        steps = 100
        for color in colors:
            # Fade in
            for i in range(steps):
                r = int(color[0] * i / steps)
                g = int(color[1] * i / steps)
                b = int(color[2] * i / steps)
                self.led.fill((r, g, b))
                time.sleep(duration / (len(colors) * steps * 2))
            # Fade out
            for i in range(steps, 0, -1):
                r = int(color[0] * i / steps)
                g = int(color[1] * i / steps)
                b = int(color[2] * i / steps)
                self.led.fill((r, g, b))
                time.sleep(duration / (len(colors) * steps * 2))

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
        try:
            with open('SETTINGS.json', 'r') as f:
                settings = json.load(f)
                self.control_temp = settings['temperature(C)']
                self.start_time = datetime(self.rtc.datetime.tm_year, self.rtc.datetime.tm_mon, self.rtc.datetime.tm_mday, settings['start_hour'], settings['start_minute'])
                self.end_time = datetime(self.rtc.datetime.tm_year, self.rtc.datetime.tm_mon, self.rtc.datetime.tm_mday, settings['end_hour'], settings['end_minute'])
                if settings['reset_time_hour'] != 0 and settings['reset_time_minute'] != 0:
                    self.update_time(settings['reset_time_hour'], settings['reset_time_minute'])
                print('Settings loaded')
                self.led.blink(color=(0, 255, 0), rate=0.4)
        
        except Exception:
            print('Failed to load settings, using defaults')
            self.control_temp = 60
            self.start_time = datetime(self.rtc.datetime.tm_year, self.rtc.datetime.tm_mon, self.rtc.datetime.tm_mday, 8, 0)
            self.end_time = datetime(self.rtc.datetime.tm_year, self.rtc.datetime.tm_mon, self.rtc.datetime.tm_mday, 18, 0)
            self.led.blink(color=(255, 0, 0), rate=0.4)

    def save_settings(self):
        pass

    def update_time(self, hour, minute):
        self.rtc.datetime = time.struct_time((self.rtc.datetime.tm_year, self.rtc.datetime.tm_mon, self.rtc.datetime.tm_mday, hour, minute, 0, 0, 0, -1))
        self.current_time = datetime(self.rtc.datetime.tm_year, self.rtc.datetime.tm_mon, self.rtc.datetime.tm_mday, self.rtc.datetime.tm_hour, self.rtc.datetime.tm_min, self.rtc.datetime.tm_sec)
        self.led.blink(color=(0, 0, 255), rate=0.4)

def main():
    asocs = ASOCS()
    asocs.init_hw()
    asocs.led.rainbow(duration=2)
    asocs.led.off()
    if asocs.rtc.lost_power:
        print('RTC lost power, time is not accurate')
        while True:
            asocs.led.blink(color=(255, 0, 0), rate=0.4)
    asocs.load_settings()

    print('Startup complete, entering main loop...')
    asocs.current_time = datetime(asocs.rtc.datetime.tm_year, asocs.rtc.datetime.tm_mon, asocs.rtc.datetime.tm_mday, asocs.rtc.datetime.tm_hour, asocs.rtc.datetime.tm_min, asocs.rtc.datetime.tm_sec)
    asocs.update_data()
    while True:
        #update the current time
        asocs.current_time = datetime(asocs.rtc.datetime.tm_year, asocs.rtc.datetime.tm_mon, asocs.rtc.datetime.tm_mday, asocs.rtc.datetime.tm_hour, asocs.rtc.datetime.tm_min, asocs.rtc.datetime.tm_sec)

        #check if we need to update the data, updating if needed
        if asocs.current_time > asocs.next_update:
            asocs.update_data()
            print(f'[{asocs.current_time}]: Air: {asocs.air_temp}°C Oven: {asocs.oven_temp}°C')
        #check we are within the time window for oven control
        if asocs.current_time > asocs.start_time and asocs.current_time < asocs.end_time:

            #turn on the heating element if the oven temp is less than the control temp, otherwise keep it off
            if asocs.oven_temp < asocs.control_temp:
                asocs.relay.on()
                asocs.led.solid((0, 255, 0))
            else:
                asocs.relay.off()
                asocs.led.off()
        time.sleep(0.01)

def standby():
    time.sleep(10)
    input('Enter debug mode? y/n?')
    if input() == 'y':
        main()
    else:
        print('Entering standby mode...')
        asocs = ASOCS()
        asocs.init_hw()
        asocs.led.fade(color=(54, 1, 63))

                

if __name__ == '__main__':
    main()
    if supervisor.runtime.serial_connected:
        #enter standby mode if serial is connected
        standby()
    else:
        #enter normal operation if serial is not connected
        main()
