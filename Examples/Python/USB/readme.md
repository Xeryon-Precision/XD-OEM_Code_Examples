# Python-Library
In this folder you will find an example using Python code over USB (COM port).

# Files:
These two are the two only required files:
* settings_default.txt: a sample file, you have to replace this one with the one provided with the Windows Interface
* Xeryon.py: this is the library. 

# Requirements
## Hardware
* Xeryon XD-OEM controller
* Xeryon motor
    * XLS
    * XVS
    * XLA
    * XRT-U
    * XVP
* USB cable
* Power adapter

## software
* setting_default.txt file
* Python installed on the computer
* Xeryon.py library
* Matplotlib library
```
pip install matplotlib
```
* Pyserial library
```
pip install pyserial
```

# Setting up controller
1. Connect your stage with the controller
2. Connect the controller with your computer using an USB cable
3. Power the controller

# Code example
## Imoprt library
Imprt all the fucntion from the Xeryon.py library and pyplot from matplotlib.
```py
from Xeryon import *                 # Import the Xeryon library
from matplotlib import pyplot as plt # Import the matplotlib library
```
## Initialize COM port
Select your COM port and the baudrate.
```py
controller = Xeryon("COM21", 115200) # Setup serial communication, select the correct COM-port and baudrate
```

## Initialize motor
Select the right type of XLS/XLA/XRT-U and give them a char as name.
```py
axisX = controller.addAxis(Stage.XLS_312, "X") # Add all axis and specify the correct encoder resolution, and give the axis a letter
```

## Starting the controller
First you need to start the motor.
```py
controller.start() # Start the controller
```

## Searching for the Index
The best thing to do in the beginnin is searching for the index.
```py
axisX.findIndex() # Search for the index
```

## Setting units
We will stat with using our mm.
```py
axisX.setUnits(Units.mm) # Set units to mm
```

## Start logging
If you want to have logged data you need to start the logging. You can call this function in your code at the location where you want the data logging to start.
```py
axisX.startLogging()     # Start logging
```

## Scaning
This code block shows a scan movend to the both sides.
```py
axisX.startScan(-1) # Start scan in the -1 direction
time.sleep(2)       # Wait 2 seconds
axisX.startScan(1)  # Start scan in the 1 direction
time.sleep(2)       # Wait 2 seconds
```

## change the speed
With this line of code you can chagne the speed. In this example we change it to 5 mm/s.
```py
axisX.setSpeed(5) # Set speed to 5 mm/s
```
## Scanning with a stop afther ... seconds
In this code block we show two ways of stopping a scan after 1 second. You can stop a scan by calling the **axisX.stopScan()** function. You can also specify in the **axisX.startScan(-1, 1)** fucntion after how many seconds the scan has to stop. In this example it is 1 second.
```py
axisX.startScan(-1)    # Start scan in the -1 direction
time.sleep(1)          # Wait 1 second
axisX.stopScan()       # Stop scan
time.sleep(2)          # Wait 2 seconds
axisX.startScan(-1, 1) # Start scan in the -1 direction for 1 second
time.sleep(2)          # Wait 2 seconds
```

## Going to a position
With the set **setDPOS()** function you can specify a spicif position the motor needs to move to. Earlier in the code we have set the units to mm, so **axisX.setDPOS(10)** means that the motor has to move to 10 mm.
```py
axisX.setDPOS(0)    # Go to position 0 mm
time.sleep(2)       # Wait 2 seconds
axisX.setDPOS(10)   # Go to position 10 mm
time.sleep(2)       # Wait 2 seconds
axisX.setSpeed(200) # Set speed to 200 mm/s
axisX.setDPOS(-10)  # Go to position -10 mm
time.sleep(2)       # Wait 2 seconds
axisX.setDPOS(0)    # Go to position 0 mm
time.sleep(2)       # Wait 2 seconds
```

## Steping
Another way of moving the motor is by taking steps. In this example we take 10 steps in the same direction.
```py
for _ in range(0,10): # Step 10 x 1 mm
    axisX.step(1)     # Step 1 mm
    time.sleep(0.5)   # Wait 0.5 seconds
time.sleep(2)         # Wait 2 seconds
```

## Change units
```py
axisX.setUnits(Units.mu) # Set units to mu
axisX.setDPOS(-10000)    # Go to position -10000 mu
time.sleep(2)            # Wait 2 seconds
```

## Stuts bits
```py
print("Bit  0 = ", axisX.isAmplifiersEnabled())         # Check bit 0
print("Bit  1 = ", axisX.isEndStop())                   # Check bit 1
print("Bit  2 = ", axisX.isThermalProtection1())        # Check bit 2
print("Bit  3 = ", axisX.isThermalProtection2())        # Check bit 3
print("Bit  4 = ", axisX.isForceZero())                 # Check bit 4
print("Bit  5 = ", axisX.isMotorOn())                   # Check bit 5
print("Bit  6 = ", axisX.isClosedLoop())                # Check bit 6
print("Bit  7 = ", axisX.isEncoderAtIndex())            # Check bit 7
print("Bit  8 = ", axisX.isEncoderValid())              # Check bit 8
print("Bit  9 = ", axisX.isSearchingIndex())            # Check bit 9
print("Bit 10 = ", axisX.isPositionReached())           # Check bit 10
print("Bit 11 = ", axisX.isErrorCompensation())         # Check bit 11
print("Bit 12 = ", axisX.isEncoderError())              # Check bit 12
print("Bit 13 = ", axisX.isScanning())                  # Check bit 13
print("Bit 14 = ", axisX.isAtLeftEnd())                 # Check bit 14
print("Bit 15 = ", axisX.isAtRightEnd())                # Check bit 15
print("Bit 16 = ", axisX.isErrorLimit())                # Check bit 16
print("Bit 17 = ", axisX.isSearchingOptimalFrequency()) # Check bit 17
print("Bit 18 = ", axisX.isSafetyTimeoutTriggered())    # Check bit 18
print("Bit 19 = ", axisX.isEtherCatAcknowledge())       # Check bit 19
print("Bit 20 = ", axisX.isEmergencyStop())             # Check bit 20
print("Bit 21 = ", axisX.isPositionFailTriggered())     # Check bit 21
```

## End logging
With the code below you are able to end the logging.
```py
logs = axisX.endLogging() # Stop logging
print(logs)               # Print logs
```

## Plot data
Here you can find an example of how to plod the data in a graf. In this graf we will plot the encoder positions.
```py
unit_converted_epos []                                                                             # Create empty list
for index in range(0, len(logs["EPOS"])):                                                          # Loop through all samples
    unit_converted_epos.append(axisX.convertEncoderUnitsToUnits(logs["EPOS"][index], axisX.units)) # Convert encoder units to units
y = unit_converted_epos                                                                            # Set y
plt.plot(y)                                                                                        # Plot
plt.ylabel('EPOS ('+str(axisX.units)+')')                                                          # Set y label
plt.xlabel("Sample")                                                                               # Set x label
plt.title("EPOS")                                                                                  # Set title
plt.show()                                                                                         # Show
```

## Stop controller
At the end of your code, it is best to stop the controller.
```py
controller.stop() # Stop the controller
```

# Output of the logged data
![Logged_Data](img/Logged_Data.jpeg)

# Note
* This code is tested in Python version 3.14.2
* This code is tested in VS Code
* This code does not work for the XLA-5-INTG