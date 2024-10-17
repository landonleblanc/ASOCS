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
        #Hardware Startup Sequence
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
        self.next_update = datetime(self.rtc.datetime.tm_year, self.rtc.datetime.tm_mon, self.rtc.datetime.tm_mday, self.rtc.datetime.tm_hour, self.rtc.datetime.tm_min, self.rtc.datetime.tm_sec) + timedelta(seconds=30)

    def load_settings(self):
        pass

    def save_settings(self):
        pass

def main():
    asocs = ASOCS()
    asocs.init_hw()
    asocs.load_settings()
    print('Startup complete, entering main loop...')
    asocs.update_data()
    while True:
        asocs.update_data()
        print(f'[{asocs.current_time}]: Air: {asocs.air_temp}°C Oven: {asocs.oven_temp}°C')
        time.sleep(0.01)    



# def init_hw():
#     #Hardware Startup Sequence
#     rtc_i2c = busio.I2C(sda=board.GP14, scl=board.GP15)#create an i2c object on pins 21(SDA) and 22(SCL)
#     rtc = adafruit_ds3231.DS3231(rtc_i2c)#initialize the ds3231
#     print('RTC initialized')
#     tc = MAX6675(board.GP18, board.GP19, board.GP16)
#     print('Thermocouple initialized')
#     relay = digitalio.DigitalInOut(board.GP28) #assign gpio pin 28 to the relay
#     relay.direction = digitalio.Direction.OUTPUT
#     print('Relay initialized')
#     # Initialize the NeoPixel LED
#     num_pixels = 4
#     led = neopixel.NeoPixel(board.GP22, num_pixels)
#     # led = digitalio.DigitalInOut(board.GP27) #assign gpio pin 27 to the led
#     # led.direction = digitalio.Direction.OUTPUT
#     print('LED initialized')
#     print('System Initialized')
#     return rtc, tc, relay, led

# def main(): 
#     rtc, tc, relay, led = init_hw() #initialize the hardware components
#     settings = Settings(rtc.datetime.tm_year, rtc.datetime.tm_mon, rtc.datetime.tm_mday) #initialize the settings class
#     # settings.load() #load the settings from the settings.json file or use defaults if unsuccessful
#     current_time = datetime(rtc.datetime.tm_year, rtc.datetime.tm_mon, rtc.datetime.tm_mday, rtc.datetime.tm_hour, rtc.datetime.tm_min, rtc.datetime.tm_sec)
#     data = Data() #initialize the data class
#     data.update(rtc, tc) #update the data class with the current values
#     print('Startup complete, entering main loop...')
#     while True:
#         led.show()
#         current_time = datetime(rtc.datetime.tm_year, rtc.datetime.tm_mon, rtc.datetime.tm_mday, rtc.datetime.tm_hour, rtc.datetime.tm_min, rtc.datetime.tm_sec)
#         if current_time >= data.next_update:
#             data.update(rtc, tc)
#             print(f'[{current_time}]: Air: {data.air}°C Oven: {data.oven}°C')
#         if current_time > settings.start_time and current_time < settings.end_time:
#             if not settings.pid:
#                 if data.oven < settings.control_temp:
#                     relay.value = True
#                     led.value = True
#                 else:
#                     relay.value = False
#                     led.value = False

#         time.sleep(0.01)

def standby():
    pass

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
