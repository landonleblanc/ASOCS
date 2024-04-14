import board
import busio
import time
import digitalio
import adafruit_ds3231
import adafruit_ssd1306
from simple_pid import PID
from max6675 import MAX6675

def get_date_time():
    raw_time = rtc.datetime#retrieve time from rtc
    print(raw_time)
    formatted_time = [raw_time.tm_year, raw_time.tm_mon, raw_time.tm_mday, raw_time.tm_hour, raw_time.tm_min] #save the data we want to a list
    for index, i in enumerate(formatted_time):  # add a leading zero to times less than 10
        if i < 10:
            formatted_time[index] = f'0{i}'
    formatted_time = [f'{formatted_time[0]}/{formatted_time[1]}/{formatted_time[2]}', f'{formatted_time[3]}:{formatted_time[4]}'] #format the time into a list, date and time
    return formatted_time

def set_time():
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

def need_pid(oven_temp, time):
    time = time.split(':')
    if oven_temp < control_temp and int(time[0]) > start_time and int(time[0]) < end_time:
        need_pid = True
        print('Conditions not met, turning oven PID on')
    else:
        need_pid = False
    return need_pid

def update_oled(oled, data):
    oled.fill(0)
    oled.text(f'Date: {data["date"]}', 0, 0, 2)  # Double the font size to 2
    oled.text(f'Time: {data["time"]}', 0, 20, 2)  # Double the font size to 2
    oled.text(f'Air Temp: {data["air"]}C', 0, 40, 2)  # Double the font size to 2
    oled.text(f'Oven Temp: {data["oven"]}C', 0, 60, 2)  # Double the font size to 2
    if control_enabled:
        oled.text(f'Oven Ctrl: Enabled', 0, 80, 2)  # Double the font size to 2
    else:
        oled.text(f'Oven Ctrl: Disabled', 0, 80, 2)  # Double the font size to 2
    oled.text(f'Press select for menu', 0, 100, 2)  # Double the font size to 2
    oled.show()
    
    oled.text(f'Date: {data["date"]}', 0, 0, 1)
    oled.text(f'Time: {data["time"]}', 0, 10, 1)
    oled.text(f'Air Temp: {data["air"]}C', 0, 20, 1)
    oled.text(f'Oven Temp: {data["oven"]}C', 0, 30, 1)
    if control_enabled:
        oled.text(f'Oven Ctrl: Enabled', 0, 40, 1)
    else:
        oled.text(f'Oven Ctrl: Disabled', 0, 40, 1)
    oled.text(f'Press select for menu', 0, 50, 1)
    oled.show()

def debug_log():
    pass

def data_log():
    pass

#Hardware Startup Sequence
rtc_i2c = busio.I2C(board.GP19, board.GP18)#create an i2c object on pins 18 and 19
oled_i2c = busio.I2C(board.GP13, board.GP12)#create an i2c object on pins 18 and 19
print('Initializing OLED...')
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, oled_i2c)#initialize the lcd
oled.fill(1)
oled.show()
time.sleep(0.5)
oled.fill(0)
oled.show()
print('OLED initialized')
oled.text('Initializing', 0, 0, 1)
oled.text('System...', 0, 10, 1)
oled.show()
print('Initializing RTC...')
rtc = adafruit_ds3231.DS3231(rtc_i2c)#initialize the ds3231
set_time()#set the time if it has defaulted
print('RTC initialized')
print('Initializing thermocouple...')
tc = MAX6675(board.GP2, board.GP3, board.GP4)
print('Thermocouple initialized')
time.sleep(1)
oled.text('System', 0, 0, 1)
oled.text('Initialized', 0, 10, 1)
oled.show()
oled.fill(0)
oled.show()
#End Hardware Startup Sequence

control_temp = 50
start_time = 11
end_time = 17
control_enabled = False
pid = PID(1, 0.1, 0.05, setpoint=control_temp)
relay = digitalio.DigitalInOut(board.GP28)
relay.direction = digitalio.Direction.OUTPUT
pid.auto_mode = True
pid.output_limits = (0, 10)
element_on_until = 0
#data dict for date, time, air temp, oven temp, if PID is needed, and relay status
data = {'date': '', 'time': '', 'air': 15, 'oven': 15, 'pid': False , 'relay': False}
while True:
    data['date'] = get_date_time()[0]
    data['time'] = get_date_time()[1]
    data['air'] = rtc.temperature #obtain the air temp from the rtc
    data['oven'] = tc.read() #obtain the oven temp from the thermocouple
    if data['pid'] == False:
        data['pid'] = need_pid(data['oven'], data['time']) #determine if the oven needs to be controlled
    elif data['pid'] == True:
        pid_output = pid(data['oven']) #if control is needed, run the PID
        print(f'PID output: {pid_output}')
        if pid_output > 0.5:
            data['relay'] = True
        else:
            data['relay'] = False
    else:
        data['relay'] = False
    relay.value = data['relay'] #set the relay to the PID output
    hour = data['time'].split(':')[0]
    if int(hour) > 17:
        data['pid'] = False
    print(f'Date: {data["date"]}, Time: {data["time"]}, Air Temp: {data["air"]}C, Oven Temp: {data["oven"]}C, PID Needed?: {data["pid"]}, Relay Status: {data["relay"]}')
    update_oled(oled, data)
    time.sleep(0.01)
#TODO: Remove data dictionary and use global variables
#TODO: Add pid output = some sort of time on for the relay
#TODO: Update get_date_time to use use epoch time instead of a formatted string. Only format when needed