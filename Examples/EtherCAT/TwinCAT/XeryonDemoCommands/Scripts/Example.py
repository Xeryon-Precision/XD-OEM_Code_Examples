from Xeryon import *                                     # Import the Xeryon library
import threading                                         # Needed to run multiple stages truly in parallel
from matplotlib import pyplot as plt                     # Import the matplotlib library

# ---------------------------------------------------------------------------
# Configuration: however many controllers/slaves you want to drive.
# Each entry is (net_id, port, drive_base, stage). Use the same net_id/port for
# drives that live in the SAME PLC/TwinCAT project (just different EtherCAT
# slave structs, e.g. MAIN.Drive1 / MAIN.Drive2 / MAIN.Drive3 / ...).
# Use a different net_id/port for drives on physically separate PLCs.
# ---------------------------------------------------------------------------
DRIVE_CONFIG = [
    ('127.0.0.1.1.1', pyads.PORT_TC3PLC1, "MAIN.Drive1", Stage.XLA_78),
    ('127.0.0.1.1.1', pyads.PORT_TC3PLC1, "MAIN.Drive2", Stage.XLS_312) 
    # NOTE : if we have only one controller on the backplane but we have configured
    #        two of them then the position will still be requested for the second one, 
    #        even if the indexation failed...
]

controllers = []
axes = []
 
for net_id, port, drive_base, stage in DRIVE_CONFIG:
    controller = Xeryon(net_id, port, drive_base=drive_base)
    axis = controller.addAxis(stage)
    controllers.append(controller)
    axes.append(axis)
 
for controller in controllers:
    controller.start()                                    # Start controller/comm thread for each slave
 
for axis in axes:
    axis.setUnits(Units.mm)                               # Cheap, no PLC round-trip wait - fine sequentially
 
# ---------------------------------------------------------------------------
# The full command sequence - including index search - runs per axis in its
# own thread, because findIndex/setDPOS/step/startScan/etc. all block the
# calling thread until they complete (or, for scans, until stopped). Running
# findIndex outside the threads would home each axis one after another -
# not what we want if all slaves should home at once.
# ---------------------------------------------------------------------------
def runSequence(axis):

    time.sleep(2)

    indexFound = axis.findIndex(0, 500000, 65000, 65000)   # Search for the index
 
    if not indexFound:
        # Without a valid encoder, isPositionReached() will never go True,
        # so setDPOS/step/startScan's internal "wait until done" loops would
        # block this thread forever, and join() on it in the main thread
        # would hang too. Bail out of THIS axis's sequence only - the other
        # axes' threads are unaffected and keep running.
        outputConsole(f"Index not found for axis {axis} - skipping its command sequence.", True)
        return
 
    axis.startLogging()                                   # Start logging (per-axis, right after indexing)
 
    axis.startScan(-1, 500000, 65000, 65000)              # Start scan in the -1 direction
    time.sleep(2)

    axis.startScan(1, 500000, 65000, 65000)               # Start scan in the 1 direction
    time.sleep(2)

    axis.startScan(-1, 500000, 65000, 65000)
    time.sleep(1)
    axis.stopScan()
    time.sleep(2)
    axis.startScan(-1, 500000, 65000, 65000, 1)
    time.sleep(2)
 
    axis.setDPOS(0, 500000, 65000, 65000)
    time.sleep(2)
    axis.setDPOS(50, 500000, 65000, 65000)
    time.sleep(2)
    axis.setDPOS(-10, 500000, 65000, 65000)
    time.sleep(2)
    axis.setDPOS(0, 500000, 65000, 65000)
    time.sleep(2)   
 
    for _ in range(0, 10):
        axis.step(1, 500000, 65000, 65000)
        time.sleep(0.5)
    time.sleep(2)
 
    axis.setUnits(Units.mu)
    axis.setDPOS(-10000, 500000, 65000, 65000)
    time.sleep(2)
  
threads = [threading.Thread(target=runSequence, args=(axis,)) for axis in axes]
 
for thread in threads:
    thread.start()                                         # All sequences now run concurrently
 
for thread in threads:
    thread.join()                                          # Wait for all of them to finish
 
 

# ---------------------------------------------------------------------------
# Status bits, per axis
# ---------------------------------------------------------------------------
for i, axis in enumerate(axes):
    print(f"--- Axis {i} ({DRIVE_CONFIG[i][2]}) status ---")
    print("Bit  0 = ", axis.isAmplifiersEnabled())         # Check bit 0
    print("Bit  1 = ", axis.isEndStop())                   # Check bit 1
    print("Bit  2 = ", axis.isThermalProtection1())        # Check bit 2
    print("Bit  3 = ", axis.isThermalProtection2())        # Check bit 3
    print("Bit  4 = ", axis.isForceZero())                 # Check bit 4
    print("Bit  5 = ", axis.isMotorOn())                   # Check bit 5
    print("Bit  6 = ", axis.isClosedLoop())                # Check bit 6
    print("Bit  7 = ", axis.isEncoderAtIndex())            # Check bit 7
    print("Bit  8 = ", axis.isEncoderValid())              # Check bit 8
    print("Bit  9 = ", axis.isSearchingIndex())            # Check bit 9
    print("Bit 10 = ", axis.isPositionReached())           # Check bit 10
    print("Bit 11 = ", axis.isErrorCompensation())         # Check bit 11
    print("Bit 12 = ", axis.isEncoderError())              # Check bit 12
    print("Bit 13 = ", axis.isScanning())                  # Check bit 13
    print("Bit 14 = ", axis.isAtLeftEnd())                 # Check bit 14
    print("Bit 15 = ", axis.isAtRightEnd())                # Check bit 15
    print("Bit 16 = ", axis.isErrorLimit())                # Check bit 16
    print("Bit 17 = ", axis.isSearchingOptimalFrequency()) # Check bit 17
    print("Bit 18 = ", axis.isSafetyTimeoutTriggered())    # Check bit 18
    print("Bit 19 = ", axis.isEtherCatAcknowledge())       # Check bit 19
    print("Bit 20 = ", axis.isEmergencyStop())             # Check bit 20
    print("Bit 21 = ", axis.isPositionFailTriggered())     # Check bit 21    


# ---------------------------------------------------------------------------
# Logging / plotting, per axis
# ---------------------------------------------------------------------------
def plotLog(axis, logs, label):
    if not logs or "EPOS" not in logs or len(logs["EPOS"]) == 0:
        print(f"No log data for {label} (its sequence was likely skipped after a failed index search).")
        return
    y = [axis.convertEncoderUnitsToUnits(v, axis.units) for v in logs["EPOS"]]
    plt.figure()                                          # New figure per axis
    plt.plot(y)
    plt.ylabel(f'EPOS ({axis.units})')
    plt.xlabel("Sample")
    plt.title(f"EPOS - {label}")
 
for i, axis in enumerate(axes):
    logs = axis.endLogging()
    plotLog(axis, logs, f"Axis {i} ({DRIVE_CONFIG[i][2]})")
 
plt.show()                                                 # Shows all figures at once

 
for controller in controllers:
    controller.stop()
 
