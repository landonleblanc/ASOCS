import time
import random
import busio
import adafruit_ssd1306


class display:
    def __init__(self, sda, scl):
        self.i2c = busio.I2C(sda=sda, scl=scl)
        self.dsp = adafruit_ssd1306.SSD1306_I2C(128, 32, self.i2c)
        return
    def fill_random(self, duration: int =1) -> None:
        for x in range(self.dsp.width):
            for y in range(self.dsp.height):
                self.dsp.pixel(x, y, random.randint(0, 1))
        self.dsp.show()
        time.sleep(duration)
        return
    def clear(self):
        self.dsp.fill(0)
        self.dsp.show()
        return
    def show_message(self, text: str, duration: int =2) -> None:
        text = text.split('\n')
        self.clear()
        for i in range(len(text)):
            self.dsp.text(text[i], 0, i*10, 1)
        self.dsp.show()
        time.sleep(duration)
        self.clear()
        return
    def show_status(self, data: object, status: object) -> None:
        self.clear()
        self.dsp.text(f'Air Temp: {data["air"]} C', 0, 10, 1)
        self.dsp.text(f'Oven Temp: {data["oven"]} C', 0, 20, 1)
        self.dsp.show()
        return
    def add_leading_zero(self, num: int) -> str:
        return "{:02d}".format(num)
    