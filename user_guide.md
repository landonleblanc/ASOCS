# ASOCS User Guide
## First Time Setup
![Wiring output photo](images/outputs.png)
1. Connect the thermocouple to the correct positions on the thermocouple termina
2. Connect the relay wires to the correct positions on the relay terminal
3. Connect the fan wires to the correct positions on the relay terminal
4. Connect the male AC plug to AC power via extension cable
5. Connect the heating element to the female AC plug
## Usage
Just plug it in and it will control the oven temperature during the control window!
## LED Indicators
- **Off**: The heating element is off.
- **Solid Orange**: The heating element is on.
- **Blinking Red forever**: An error has occured, most likely the system time was reset. Follow "Setting the time" below. If this issue persists, try replacing the battery.
- **2 Green blinks**: The user defined settings were sucessfully loaded.
- **5 Red blinks**: The user defined settings failed to load and the system will continue with the default settings. If this occurs, ensure SETTINGS.py is formatted correctly and the values are integers.
- **Fading Purple**: The device is connected to a computer and the system is idle.

## Device Settings
The following parameters can be changed to customize the behavior of the controller. All temperatures are in Celsius and the time is using a 24 hour clock. The control window is the time frame at which the system will monitor the conditions within the oven and turn on the heating element, if needed
- TEMPERATURE: This is the target temperature in Celsius that the controller will control to. Default is 50C
- START_TIME: A tuple (hour, minute) that marks the beginning of the control window. Example: (10, 45)
- END_TIME: A tuple (hour, minute) that marks the end of the control window. Example: (17, 30)
- RESET_TIME: A tuple (hour, minute) used to set the RTC time. Default is (0, 0). Example: (14, 30)

### Changing the settings
1. Disconnect the USB A cable from the power adapter
2. Connect the USB A cable to a computer (The device will appear as a storage device)
3. Open File Explorer and open CIRCUITPYTHON
4. Open SETTINGS.py with a text editor
5. Edit the value to the right of the equals sign to the desired value (e.g., TEMPERATURE = 65, START_TIME = (9, 0))
6. Save the file
7. Disconnect the USB A cable from the computer
8. Reconnect the USB A cable to the power adapter

### Setting the time
1. Disconnect the USB A cable from the power adapter
2. Connect the USB A cable to a computer (The device will appear as a storage device)
3. Open File Explorer and open CIRCUITPYTHON
4. Create a new file called time.txt
5. In the time.txt file, enter the current time in the format hour:minute (e.g., 14:30 for 2:30 PM)
6. Save the file
7. Disconnect the USB A cable from the computer
8. Connect the USB A cable to the power adapter
9. Upon startup the LEDs should blink blue indicating the time was successfully set and the time.txt file will be automatically deleted
