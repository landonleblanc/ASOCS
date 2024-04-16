import board
import busio
import time
import digitalio
import adafruit_ds3231
import adafruit_ssd1306
from simple_pid import PID
from max6675 import MAX6675

def set_time(rtc):
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

def update_oled(oled, data, time, controlling, relay_state):
    oled.text(f'Time: {time.tm_hour}:{time.tm_min}', 0, 10, 1)
    oled.text(f'Air Temp: {data["air"]}C', 0, 20, 1)
    oled.text(f'Oven Temp: {data["oven"]}C', 0, 30, 1)
    if controlling:
        oled.text(f'Oven Ctrl: Enabled', 0, 40, 1)
    else:
        oled.text(f'Oven Ctrl: Disabled', 0, 40, 1)
    if relay_state:
        oled.text(f'Element: On', 0, 50, 1)
    else:
        oled.text(f'Element: Off', 0, 50, 1)
    oled.text(f'Press select for menu', 0, 50, 1)
    oled.show()

def debug_log():
    pass

def data_log():
    pass

def reset_oled(oled):
    oled.fill(0)
    oled.show()
    return

def init_hw():
    #Hardware Startup Sequence
    rtc_i2c = busio.I2C(board.GP19, board.GP18)#create an i2c object on pins 18 and 19
    oled_i2c = busio.I2C(board.GP13, board.GP12)#create an i2c object on pins 12 and 13
    print('Initializing OLED...')
    oled = adafruit_ssd1306.SSD1306_I2C(128, 64, oled_i2c)#initialize the lcd
    oled.fill(1)
    oled.show()
    time.sleep(0.5)
    reset_oled(oled)
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
    print('Initializing relay...')
    relay = digitalio.DigitalInOut(board.GP28) #assign gpio pin 28 to the relay
    relay.direction = digitalio.Direction.OUTPUT
    print('Relay initialized')
    time.sleep(1)
    oled.text('System', 0, 0, 1)
    oled.text('Initialized', 0, 10, 1)
    oled.show()
    reset_oled(oled)
    #End Hardware Startup Sequence
    return rtc, oled, tc, relay

def system_settings():
    pass

def init_pid(temp):
    pid = PID(1, 0.1, 0.05, setpoint=temp)
    pid.auto_mode = True
    pid.output_limits = (0, 10)
    return pid



def main():
    control_temp = 50 #temp to control the oven to in C
    start_time = 11 #The time in hours at which the oven should reach the control temp and start controlling if not
    end_time = 17 #The latest time in hours at which the oven should be controlled if conditions are not met
    data = {'air': 15, 'oven': 15} #the measurement data. May add other measurements later
    rtc, oled, tc, relay = init_hw() #initialize the hardware components
    pid_time = 0 #How long the element should be turned on for in minutes
    controlling = False #whether or not the oven needs to be controlled
    pid = init_pid(control_temp) #Cretes the pid class
    while True:
        datetime = rtc.datetime
        time = int(datetime.tm_hour*60 + datetime.tm_min) #convert the time to minutes
        data['air'] = rtc.temperature #obtain the "air" temp from the rtc
        data['oven'] = tc.read() #obtain the oven temp from the thermocouple
        if controlling == False: #if we aren't currently controlling, check if the desired conditions are not met
            relay.value = False
            if data['oven'] < control_temp and time > start_time and time < end_time:
                controlling = True
                print('Conditions not met, turning oven PID control on')
        elif controlling == True:
            pid_output = pid(data['oven']) #if control is needed, run the PID
            pid_time = time + pid_output * 60 #set the ending time for the element
        if time < pid_time and controlling:
            relay.value = True #turn the element on if the pid duration hasn't finished
        else:
            relay.value = False #turn the element off
        update_oled(oled, data, datetime, controlling, relay.value) #update the oled display
        time.sleep(0.01)
    

if __name__ == '__main__':
    main()
#TODO: Add pid output = some sort of time on for the relay
#TODO: Update get_date_time to use use epoch time instead of a formatted string. Only format when needed
#TODO: Store any user editable params in settings.json