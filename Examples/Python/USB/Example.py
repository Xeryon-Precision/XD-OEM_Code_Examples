from Xeryon import *                                    # Import the Xeryon library
from matplotlib import pyplot as plt                    # Import the matplotlib library

controller  = Xeryon("COM52", 115200)                   # Setup serial communication, select the correct COM-port and baudrate
axisX       = controller.addAxis(Stage.XLS_312, "X")    # Add all axis and specify the correct encoder resolution, and give the axis a letter

controller.start()              # Start the controller
axisX.findIndex()               # Search for the index
axisX.setUnits(Units.mm)        # Set units to mm
axisX.startLogging()            # Start logging

axisX.startScan(-1)             # Start scan in the -1 direction
time.sleep(2)                   # Wait 2 seconds
axisX.startScan(1)              # Start scan in the 1 direction
time.sleep(2)                   # Wait 2 seconds

axisX.setSpeed(5)               # Set speed to 5 mm/s

axisX.startScan(-1)             # Start scan in the -1 direction
time.sleep(1)                   # Wait 1 second
axisX.stopScan()                # Stop scan
time.sleep(2)                   # Wait 2 seconds
axisX.startScan(-1, 1)          # Start scan in the -1 direction for 1 second
time.sleep(2)                   # Wait 2 seconds

axisX.setDPOS(0)                # Go to position 0 mm
time.sleep(2)                   # Wait 2 seconds
axisX.setDPOS(10)               # Go to position 10 mm
time.sleep(2)                   # Wait 2 seconds
axisX.setSpeed(200)             # Set speed to 200 mm/s
axisX.setDPOS(-10)              # Go to position -10 mm
time.sleep(2)                   # Wait 2 seconds
axisX.setDPOS(0)                # Go to position 0 mm
time.sleep(2)                   # Wait 2 seconds

for _ in range(0,10):           # Step 10 x 1 mm
    axisX.step(1)               # Step 1 mm
    time.sleep(0.5)             # Wait 0.5 seconds
time.sleep(2)                   # Wait 2 seconds

axisX.setUnits(Units.mu)        # Set units to mu
axisX.setDPOS(-10000)           # Go to position -10000 mu
time.sleep(2)                   # Wait 2 seconds

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

logs = axisX.endLogging()   # Stop logging
#print(logs)                # Print logs

unit_converted_epos = []                                                                            # Create empty list
for index in range(0, len(logs["EPOS"])):                                                           # Loop through all samples
    unit_converted_epos.append(axisX.convertEncoderUnitsToUnits(logs["EPOS"][index], axisX.units))  # Convert encoder units to units
y = unit_converted_epos                                                                             # Set y
plt.plot(y)                                                                                         # Plot
plt.ylabel('EPOS ('+str(axisX.units)+')')                                                           # Set y label
plt.xlabel("Sample")                                                                                # Set x label
plt.title("EPOS")                                                                                   # Set title
plt.show()                                                                                          # Show

controller.stop()                                                                                  # Stop the controller