ASOCS(Assisted Solar Oven Control System) User Guide
Setup
Connect the thermocouple to the positive and negative terminals on the orange control box
Connect the yellow plug to AC power via extension cable
Connect the heating element to the orange outlet
Standard Use
Connect the white AC/DC adapter to AC power
After a few seconds the device should be started up and the screen should show the following display
By default ASOCS will only watch the temperature. The orange button will toggle temperature control
To enable the temperature control, press the orange button on the right
When control is enabled, the system will check if the oven has reached the desired temperature in the specified temperature window and start heating the oven if it has not
Pressing the orange button again will turn off the temperature control and turn off the heating element.
Changing Settings via PC
Disconnect the USB from the AC/DC adapter
Connect the USB to a computer
Navigate to “My Computer” 
There should be a USB drive named “Circuitpython”
Open the drive
There will be two files names “settings”, one is a TOML file and the other JSON
Right click on the settings JSON file
Select either “edit” or “open with” then “notepad
The settings that can be changed are as follows with a description
“control_temp” is the temperature at which the solar over will be controlled to
“start_time” is the time of day in minutes that oven control will begin, if needed
“end_time” is the time of day in minutes that the oven control will end
“kP” is the proportional gain. This is the gain that applies a control action proportional to the difference between the setpoint and the actual process variable. A higher Kp results in a stronger control action and faster response to changes in the process variable. However, too high of a Kp can cause the system to become unstable or lead to overshoot.
“kI” is the integral gain. This is the gain that adds up the errors over time and helps eliminate steady-state errors. Ki acts as a correction factor to adjust the control signal based on the accumulated error. A higher Ki results in a stronger correction, but it can also cause the system to become sluggish or unstable.
“kD” is the derivative gain. This is the gain that measures the rate of change of the error and applies a correction based on that rate. Kd acts as a damping factor to reduce overshoot and improve the response time. A higher Kd results in stronger damping, but it can also amplify noise in the system.
“reset_time” can be set to either “True” or “False”. Setting this to true will allow the system time to be changed. THIS SETTING IS CURRENTLY BROKEN
To change any setting change the number to the right of the colon
The control temp must be an integer
The time must be an integer and the time in minutes. This can be achieve with the following formula: hour * 60 + min
kP, kI, and kD are used for tuning the PID control to improve the stability and response times. At a later date I’ll work on a procedure on how to do this well and possibly make it an automated process.
The time reset function is currently not working
After changing a setting, select “File” then “Save”
Close the settings.json file
Disconnect the USB from the PC
Connect the USB to the AC/DC adapter

Setting the Time
Download and install TeraTerm
Disconnect the USB from the AC/DC adapter
Connect the USB to the PC
Open TeraTerm
Select the serial button
From the drop down select the comport
Select Connect
Disconnect and reconnect the USB
Enter the prompted number
Once temperatures start being output, disconnect the USB
Connect the USB to the AC/DC adapter

PID Tuning
Coming Soon
