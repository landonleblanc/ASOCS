# Modules and Pinout
## DS3231 RTC
- GND(PIN 3)
- VCC
- SCL > I2C0 SCL(PIN 2)
- SDA > I2C0 SDA(PIN 1)

## MAX6675 Thermocouple
- GND(PIN18)
- VCC
- SCK > SPI0 SCK(PIN 24)
- CS > SPI0 TX(PIN 25)
- SO > SPI0 RX(PIN 21)

## Relay
- GND(PIN 3)
- VCC in GP2(PIN 7)
- VCC out VBUS(PIN 40)

## Neopixel LEDs
- GND(PIN 38)
- VCC
- Data GP28(PIN 34)
