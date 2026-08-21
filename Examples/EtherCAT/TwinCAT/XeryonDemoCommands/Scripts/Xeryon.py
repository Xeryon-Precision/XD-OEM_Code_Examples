#=====================================================================================================
# Xeryon.py library for Python
# Supporting the XD-OEM controllers
#=====================================================================================================

#=====================================================================================================
# Imprt these libraries
#=====================================================================================================
import threading
from enum import Enum
import time
import math
import pyads
import re

#=====================================================================================================
# DEBUG MODE
# This variable is set to True if you are in debug mode.
# This is handy when no stage is connected.
# It ignores some checks, e.g.: if DPOS=.. 
# command is send and in Debug mode, the EPOS isn't checked if it's in range.
#=====================================================================================================
DEBUG_MODE = False

#=====================================================================================================
# OUTPUT_TO_CONSOLE
# If set to True, a lot of data is outputted to the console.
# e.g.: If you set DPOS=..., the new DPOS and EPOS are printed to the console.
# False: this blocks all output to the console.
#=====================================================================================================
OUTPUT_TO_CONSOLE = True  

#=====================================================================================================
# DISABLE WAITING
# If set to True, the library won't wait until the position is reached.
# All blocking functions will be disabled.
# NOTE: If you enable this, after finding the index of each stage, 
# do a +/- 5 second timeout (time.sleep(5))
#=====================================================================================================
DISABLE_WAITING = False

#=====================================================================================================
# AUTO_SEND_SETTINGS
# If set to True, the library will automatically send the settings in the settings_default.txt
# to the connected stages on startup.
#=====================================================================================================
AUTO_SEND_SETTINGS = True

#=====================================================================================================
# AUTO_SEND_ENBL
# "ENBL=1" needs to be send when an error occurs.
# Errors like: thermal error (bit 2&3), error limit (bit 16) or safety timeout (bit18)
# Set it to True to automatically send "ENBL=1" when these errors occur, bypassing this 'safety' feature.
#=====================================================================================================
AUTO_SEND_ENBL = False

#=====================================================================================================
# The value's of these commands don't get stored in this library.
#=====================================================================================================
NOT_SETTING_COMMANDS = ["DPOS", "EPOS", "HOME", "ZERO", "RSET", "INDX", "STEP", "MOVE", "STOP", "CONT", "SAVE", "STAT", "TIME", "SRNO", "SOFT", "XLA3", "XLA1", "XRT1", "XRT3", "XLS1", "XLS3", "SFRQ", "SYNC"]
DEFAULT_POLI_VALUE = 200
AMPLITUDE_MULTIPLIER = 1456.0
PHASE_MULTIPLIER = 182

# ---------------------------------------------------------------------------
# Symbol names (from XeryonDemo.Demo.MAIN.DriveX)
# ---------------------------------------------------------------------------
# NOTE: These used to be fixed module-level globals hardcoded to "MAIN.Drive1".
# That meant only a single drive/slave could ever be addressed - a second
# Xeryon()/Communication() instance would silently read/write the exact same
# PLC symbols as the first one. buildDriveSymbols() now builds a fresh set of
# symbol names for whichever drive base (e.g. "MAIN.Drive1", "MAIN.Drive2", ...)
# is passed in. Each Communication instance builds and stores its own copy
# (see Communication.__init__) instead of relying on shared globals.
# ---------------------------------------------------------------------------
DEFAULT_DRIVE_BASE = "MAIN.Drive1"

def buildDriveSymbols(drive_base):
    status_symbols = {
        # Xeryon STAT bit index -> PLC symbol
        0: f"{drive_base}.iDriveAmplifiersEnabled",
        1: f"{drive_base}.iDriveEndStop",
        2: f"{drive_base}.iDriveThermalProtection1",
        3: f"{drive_base}.iDriveThermalProtection2",
        4: f"{drive_base}.iDriveForceZero",
        5: f"{drive_base}.iDriveMotorOn",
        6: f"{drive_base}.iDriveClosedLoop",
        7: f"{drive_base}.iDriveEncoderIndex",
        8: f"{drive_base}.iDriveEncoderValid",
        9: f"{drive_base}.iDriveSearchingIndex",
        10: f"{drive_base}.iDrivePositionReached",
        11: f"{drive_base}.iDriveErrorCompensation",
        12: f"{drive_base}.iDriveEncoderError",
        13: f"{drive_base}.iDriveScanning",
        14: f"{drive_base}.iDriveLeftEndStop",
        15: f"{drive_base}.iDriveRightEndStop",
        16: f"{drive_base}.iDriveErrorLimit",
        17: f"{drive_base}.iDriveSearchingOptimalFrequency",
        18: f"{drive_base}.iDriveSafetyTimeoutTriggered",
        19: f"{drive_base}.iDriveBusy",           # was "EtherCatAcknowledge" slot
        20: f"{drive_base}.iDriveEmergencyStop",
        21: f"{drive_base}.iDrivePositionFail",
    }
    return {
        "STATUS_SYMBOLS": status_symbols,
        "BUSY_SYMBOL": f"{drive_base}.iDriveBusy",
        "EPOS_SYMBOL": f"{drive_base}.iDriveActualPosition",
        "TARGET_POS_SYMBOL": f"{drive_base}.qDriveTargetPos",  # DINT
        "SPEED_SYMBOL": f"{drive_base}.qDriveSpeed",           # DINT
        "ACC_SYMBOL": f"{drive_base}.qDriveAcc",               # INT
        "DEC_SYMBOL": f"{drive_base}.qDriveDec",               # INT
        "COMMAND_SYMBOL": f"{drive_base}.qCommand",            # STRING(4)
        "EXECUTE_SYMBOL": f"{drive_base}.qExecute",            # BYTE (1/0, not BOOL)
    }

# Kept for backwards compatibility with any code importing these names
# directly; they reflect the *default* drive base only. Communication no
# longer reads these globals internally (see Communication.__init__ below).
BASE = DEFAULT_DRIVE_BASE
_default_symbols = buildDriveSymbols(DEFAULT_DRIVE_BASE)
STATUS_SYMBOLS = _default_symbols["STATUS_SYMBOLS"]
BUSY_SYMBOL = _default_symbols["BUSY_SYMBOL"]
EPOS_SYMBOL = _default_symbols["EPOS_SYMBOL"]
TARGET_POS_SYMBOL = _default_symbols["TARGET_POS_SYMBOL"]
SPEED_SYMBOL = _default_symbols["SPEED_SYMBOL"]
ACC_SYMBOL = _default_symbols["ACC_SYMBOL"]
DEC_SYMBOL = _default_symbols["DEC_SYMBOL"]
COMMAND_SYMBOL = _default_symbols["COMMAND_SYMBOL"]
EXECUTE_SYMBOL = _default_symbols["EXECUTE_SYMBOL"]

#=====================================================================================================
# Main Xeryon Drive Class
#=====================================================================================================
class Xeryon:
    #=====================================================================================================
    # Global variables:
    #   - axis_list: A list storing all the axis in the system.
    #   - axis_letter_list: A list storing all the axis_letters in the system.
    #=====================================================================================================
    axis_list = None

    #=====================================================================================================
    # - @param - 
    # - @return: Return a Xeryon object
    #=====================================================================================================
    def __init__(self, net_id = None, port = None, drive_base = None):
        # drive_base: the PLC symbol prefix for this drive/slave, e.g.
        # "MAIN.Drive1" or "MAIN.Drive2". Defaults to "MAIN.Drive1" so
        # existing single-drive scripts keep working unchanged. Pass a
        # different drive_base per Xeryon() instance to address a second
        # (or third, ...) slave on the same or a different PLC connection.
        self.comm = Communication(self, net_id, port, drive_base)
        self.axis_list = []

    #=====================================================================================================
    # - This functions NEEDS to be ran before any commands are executed.
    #   This function starts the ethercat communication and configures the settings with the controller.
    # - @param - external_communication_thread: Specify if you want to use your own communication thread
    #          - external_settings_default: Specify if you want to use your own settings file
    # - @return: Nothing.
    #=====================================================================================================
    def start(self, external_communication_thread = False, external_settings_default = None):
        
        #=====================================================================================================
        # Check if there are any stages.
        # If there are no stages, raise an exception
        #=====================================================================================================
        if len(self.getAllAxis()) <= 0:
            raise Exception("Cannot start the system without stages. The stages don't have to be connnected, only initialized in the software.")
        
        #=====================================================================================================
        # Start the ethercat communication 
        #=====================================================================================================
        comm = self.getCommunication().start(external_communication_thread)

        #=====================================================================================================
        # Reset all axes
        #=====================================================================================================
#       for axis in self.getAllAxis():
#           axis.reset()
        
        #=====================================================================================================
        # Wait a bit to give the controller time to reset
        #=====================================================================================================
        time.sleep(0.2)

        #=====================================================================================================
        # Enable all axes
        #=====================================================================================================
        for axis in self.getAllAxis():
            axis.sendSetting("ENBL", 1)

        
    #=====================================================================================================
    # - This function sends STOP to the controller and closes the communication.
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def stop(self):

        #=====================================================================================================
        # Stop all axes
        #=====================================================================================================
        for axis in self.getAllAxis():
            axis.sendCommandOnly("STOP")
            time.sleep(0.001)
            axis.was_valid_DPOS = False
 
    #=====================================================================================================
    # - This function just stops moving.
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def stopMovements(self):

        #=====================================================================================================
        # Stop all axes
        #=====================================================================================================
        for axis in self.getAllAxis():
            axis.sendCommandOnly("STOP")
            axis.was_valid_DPOS = False

    #=====================================================================================================
    # - This function sends RESET to the controller, and resends all settings.
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def reset(self):
        
        #=====================================================================================================
        # Reset all axes
        #=====================================================================================================
        for axis in self.getAllAxis():
            axis.reset()
        time.sleep(0.2)

        #=====================================================================================================
        # If AUTO_SEND_SETTINGS is enabled, send the settings
        #=====================================================================================================
        if AUTO_SEND_SETTINGS:
            for axis in self.getAllAxis():
                axis.sendSettings()

    #=====================================================================================================
    # - This function returns a list containing all axis objects belonging to this controller.
    # - @param: None
    # - @return: A list containing all axis objects belonging to this controller.
    #=====================================================================================================
    def getAllAxis(self):
        return self.axis_list

    #=====================================================================================================
    # - This function adds an axis to the controller.
    # - @param: - stage: Specify the type of stage that is connected.
    # - @return: Returns an Axis object
    #=====================================================================================================
    def addAxis(self, stage):
        newAxis = Axis(self, stage)
        self.axis_list.append(newAxis)  # Add axis to axis list.
        return newAxis

    #=====================================================================================================
    # - This function returns the correct axis object. Or None if the axis does not exist.
    # - @param: - letter: Specify the axis letter
    # - @return: Returns the correct axis object. Or None if the axis does not exist.
    #=====================================================================================================
    def getAxis(self):

        #=====================================================================================================
        # Check if axis exists and return it
        #=====================================================================================================
        if len(self.getAllAxis()) > 0:
            return self.getAllAxis()[0]
            
        #=====================================================================================================
        # Axis does not exist, return None
        #=====================================================================================================
        return None
    
    #=====================================================================================================
    # - This function returns the communication class.
    # - @param: None
    # - @return: The communication class.
    #=====================================================================================================
    def getCommunication(self):
        return self.comm

#=====================================================================================================
# This class is only made for making the program more readable.
#=====================================================================================================
class Units(Enum):
    mm = (0, "mm")
    mu = (1, "mu")
    nm = (2, "nm")
    inch = (3, "inches")
    minch = (4, "milli inches")
    enc = (5, "encoder units")
    rad = (6, "radians")
    mrad = (7, "mrad")
    deg = (8, "degrees")

    def __init__(self, ID, str_name):
        self.ID = ID
        self.str_name = str_name

    def __str__(self):
        return self.str_name

    def getUnit(self, str):
        for unit in Units:
            if unit.str_name in str:
                return unit
        return None

#=====================================================================================================
# This class is the main class for the axis.
#=====================================================================================================
class Axis:
    axis_letter = None  # Stores the axis letter for this specific axis.
    xeryon_object = None  # Stores the "Xeryon" object.
    axis_data = None  # Stores all the data the controller sends.
    settings = None  # Stores all the settings from the settings file
    stage = None  # Specifies the type of stage used in this axis.
    units = Units.mm  # Specifies the units this axis is currently working in.
    update_nb = 0  # This number increments each time an update is recieved from the controller.
    was_valid_DPOS = False  # if True, the STEP command takes DPOS as the refrence. It's called "targeted_position=1/0" in the Microcontroller
    def_poli_value = str(DEFAULT_POLI_VALUE)

    isLogging = False  # Stores if this axis is currently "Logging": it's storing its axis_data.
    logs = {}  # This stores all the data. It's a dictionary of the form:

    previous_epos = [0,0] # Two samples to calculate speed
    previous_time = [0,0]

    # { "EPOS": [...,...,...], "DPOS": [...,...,...], "STAT":[...,...,...],...}

    #=====================================================================================================
    # - This function finds the index, after finding the index it goes to the index position.
    #   It blocks the program until the index is found.
    # - @param: direction: Specifies in which direction to start the search for the index.
    # - @return: None
    #=====================================================================================================
    def findIndex(self, direction, speed, acc, decc, forceWaiting = False):
       
        #=====================================================================================================
        # Send INDX to the controller.
        #=====================================================================================================
        self.sendCommand("INDX", direction, speed, acc, decc)
        self.was_valid_DPOS = False

        #=====================================================================================================
        # Wait for the index to be found.
        #=====================================================================================================
        if DISABLE_WAITING is False or forceWaiting is True:
            self.__waitForUpdate()
            self.__waitForUpdate()
            outputConsole("Searching index for axis " + str(self) + ".")

            #=====================================================================================================
            # Wait for the index to be found.
            #=====================================================================================================
            while not self.isEncoderValid():

                #=====================================================================================================
                # Check if searching for index bit is true.
                #=====================================================================================================
                if not self.isSearchingIndex():
                    outputConsole("Index is not found, but stopped searching for index.", True)
                    return False
                    break
                time.sleep(0.2)

        if self.isEncoderValid():
            outputConsole("Index of axis " + str(self) + " found.")
            return True

    #=====================================================================================================
    # - This function sends the DPOS command to the controller. This function makes use of the sendCommand 
    #   function, which is blocking the program until the position is reached.
    # - @param: - value: The new value DPOS has to become.
    #           - differentUnits: If the value isn't specified in the current units, specify the 
    #             correct units.
    #           - outputToConsole: Default set to True. If set to False, this function won't output text 
    #             to the console.
    # - @return: None
    #=====================================================================================================
    def setDPOS(self, position, speed, acc, decc, differentUnits=None, outputToConsole=True, forceWaiting = False):
        
        #=====================================================================================================
        # Take the current units.
        #=====================================================================================================
        unit = self.units 
        if differentUnits is not None:
            unit = differentUnits

        #=====================================================================================================
        # Convert the value into encoder units
        #=====================================================================================================
        DPOS = int(self.convertUnitsToEncoder(position, unit))
        error = False
        atEndPos = False

        if self.isAtLeftEnd() or self.isAtRightEnd():
            atEndPos = True
            print("at end position")


        #=====================================================================================================
        # Send DPOS to the controller.
        #=====================================================================================================
        self.sendCommand("DPOS", DPOS, speed, acc, decc)
        self.was_valid_DPOS = True

        if atEndPos:
            while (self.isAtLeftEnd() or self.isAtRightEnd()):
                outputConsole("wait until moved from limit, " + getDposEposString(position, self.getEPOS(), unit), False) 
                time.sleep(0.01) 

        #=====================================================================================================
        # Wait for the position to be reached.
        # Block all futher processes until position is reached.
        # This check isn't nessecary in DEBUG mode or when DISABLE_WAITING is True
        #=====================================================================================================
        if DEBUG_MODE is False and DISABLE_WAITING is False or forceWaiting is True:  
    
            #=====================================================================================================
            # Wait until EPOS is within PTO2 AND positionReached status is received.
            #=====================================================================================================
            #while not (self.__isWithinTol(DPOS) and self.isPositionReached()):
            while not (self.isPositionReached()):

                #=====================================================================================================
                # Check if stage is at left end or right end.
                #=====================================================================================================
                if self.isAtLeftEnd() or self.isAtRightEnd():
                    # TODO: fix this so it does not go off while positioning on the limit value. 
                    outputConsole("DPOS is out or range. (1) " + getDposEposString(position, self.getEPOS(), unit), True)
                    error = True
                    return False 
                
                #=====================================================================================================
                # Check if stage did not reach the position.
                #=====================================================================================================
                if self.isErrorLimit():
                    outputConsole("Position not reached. (5) ELIM Triggered.", True)
                    error = True
                    return False

                #=====================================================================================================
                # Check if stage did not reach the position.
                #=====================================================================================================
                if self.isSafetyTimeoutTriggered():
                    outputConsole("Position not reached. (6) TOU2 (Timeout 2) triggered.", True)
                    error = True
                    return False

                #=====================================================================================================
                # Check if stage did not reach the position.
                #=====================================================================================================
                if self.isPositionFailTriggered():
                    outputConsole("Position not reached. (8) TOU3 (Timeout 3) triggered, 'position fail' status bit 21 went high. ", True)
                    error = True
                    return False

                #=====================================================================================================
                # Check if stage did not reach the position.
                #=====================================================================================================
                if self.isThermalProtection1() or self.isThermalProtection2():
                    outputConsole("Position not reached. (7) amplifier error.", True)
                    error = True
                    return False
                
                time.sleep(0.01)

        #=====================================================================================================
        # Output the new DPOS & EPOS if necessary.
        #=====================================================================================================
        if outputToConsole and error is False and DISABLE_WAITING is False:
            outputConsole(getDposEposString(position, self.getEPOS(), unit))
        
        return True

    #=====================================================================================================
    # - This function is used to make the axis move in steps.
    # - @param: - value: The amount it needs to step (specified in the current units)
    # - @return: None
    #=====================================================================================================
    def step(self, value, speed, acc, decc, forceWaiting = False):

        #=====================================================================================================
        # Convert the value to encoder units.
        #=====================================================================================================
        step = self.convertUnitsToEncoder(value, self.units)

        #=====================================================================================================
        # Calculate the new DPOS.
        #=====================================================================================================
        # if self.was_valid_DPOS:
        #     new_DPOS = int(self.getData("DPOS")) + step
        # else:
        #  NOTE : 
        # was_valid_DPOS is set after new DPOS command is sent... DPOS can however not be requested via ethercat so it will remain 0 all the time
        # as such we can only rely on EPOS as EPOS (actual position) is always received via ethercat     
        new_DPOS = int(self.getData("EPOS")) + step

        #=====================================================================================================
        # Check if the stage is a rotating stage.
        #=====================================================================================================
        if not self.stage.isLineair:
            encoderUnitsPerRevolution = self.convertUnitsToEncoder(360, Units.deg)
            new_DPOS = -encoderUnitsPerRevolution/2 * (new_DPOS // (encoderUnitsPerRevolution/2) % 2) + (new_DPOS % (encoderUnitsPerRevolution/2))

        #=====================================================================================================
        # This is used so position is checked in here.
        #=====================================================================================================
        self.setDPOS(new_DPOS, speed, acc, decc, Units.enc, False, forceWaiting=forceWaiting)
        if DISABLE_WAITING is False:
            self.__waitForUpdate()  # Waits a couple of updates, so the EPOS is valid and doesn't lagg behind.
            outputConsole("Stepped: " + str(self.convertEncoderUnitsToUnits(step, self.units)) + " " + str(self.units) + " " + getDposEposString(self.getDPOS(), self.getEPOS(), self.units))

    #=====================================================================================================
    # - This function returns the current DPOS in the current units.
    # - @param: None
    # - @return: Return the desired position (DPOS) in the current units.
    #=====================================================================================================
    def getDPOS(self):
        return self.convertEncoderUnitsToUnits(self.getData("DPOS"), self.units)

    #=====================================================================================================
    # - This function returns the current EPOS in the current units.
    # - @param: None
    # - @return: Return the encoder position (EPOS) in the current units.
    #=====================================================================================================
    def getEPOS(self):
        return self.convertEncoderUnitsToUnits(self.getData("EPOS"), self.units)

    #=====================================================================================================
    # - This function returns the current Units this stage is working in.
    # - @param: None
    # - @return: Return the current units this stage is working in.
    #=====================================================================================================
    def getUnit(self):
        return self.units
    #=====================================================================================================
    # - This function sets the units this axis needs to work in.
    # - @param: - units: The units this axis needs to work in.
    # - @return: None
    #=====================================================================================================
    def setUnits(self, units):
        self.units = units

    #=====================================================================================================
    # - This function is used to set settings internally. sending of settings to the controller is done 
    #   via sendSetting
    # - @param: - tag: The tag that needs to be stored
    #           - value: The value
    # - @return: None
    #=====================================================================================================
    def setSetting(self, tag, value, fromSettingsFile=False):
        if fromSettingsFile:
            value = self.applySettingMultipliers(tag, value)
            if "MASS" in tag:
                tag = "CFRQ"
        if "?" not in str(value):
            self.settings.update({tag: value})

    #=====================================================================================================
    # - This function starts logging all data that the controller sends. It updates the POLI 
    #   (Polling Interval) to get more data.
    # - @param: - increase_poli: If true, the POLI will be increased to get more data.
    # - @return: None
    #=====================================================================================================
    def startLogging(self, increase_poli = True):
        self.isLogging = True
        if increase_poli:
            self.xeryon_object.getAllAxis()[0].setSetting("POLI", "1")
            self.sendSetting("POLI", 1)
        self.__waitForUpdate()

    #=====================================================================================================
    # - This function stops the logging of all the data. It updates the POLI (Polling Interval) back to 
    #   the default value.
    # - @param: None
    # - @return: The loged data.
    #=====================================================================================================
    def endLogging(self, convertTimeAndEpos=False):

        #=====================================================================================================
        # Variables
        #=====================================================================================================
        self.isLogging = False
        logs = self.logs
        self.logs = {}

        if convertTimeAndEpos:
                timestamps = [0]
                for i in range(1, len(logs["TIME"])):
                    t= logs["TIME"][i]
                    if t < logs["TIME"][i-1]:
                        t += 2**16
                    
                    dT =  (t - logs["TIME"][i-1])/10
                    
                    timestamps.append(round(timestamps[-1] + dT,2))
                
                epos_in_units = [self.convertEncoderUnitsToUnits(pos) for pos in logs["EPOS"]]

                logs["TIME"] = timestamps
                logs["EPOS"] = epos_in_units

        self.sendSetting("POLI", DEFAULT_POLI_VALUE)
        self.xeryon_object.getAllAxis()[0].setSetting("POLI", self.def_poli_value)
        return logs

    #=====================================================================================================
    # - This function starts a scan.
    # - @param: - direction: Positive or negative number.
    #           - execTime: How long the scan should be executed.
    # - @return: None
    #=====================================================================================================
    def startScan(self, direction, speed, acc, decc, execTime=None, untilLimit=False):
        self.sendCommand("SCAN", direction, speed, acc, decc)
        self.was_valid_DPOS = False

        if execTime is not None:
            time.sleep(execTime)
            self.sendSetting("SCAN", 0)
        
        #=====================================================================================================
        # Wait until the software limit is hit.
        #=====================================================================================================
        if untilLimit:
            self.__waitForUpdate()
            if int(direction) > 0:
                while not self.isAtRightEnd():
                    time.sleep(0.1)
            else:
                while not self.isAtLeftEnd():
                    time.sleep(0.1)

    #=====================================================================================================
    # - This function stops a scan.
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def stopScan(self):
        self.sendSetting("SCAN", 0)
        #time.sleep(0.001)
        self.was_valid_DPOS = False

    #=====================================================================================================
    # - This function sends a command with arguments to the controller.
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #=====================================================================================================
    def sendCommand(self, command, position, speed, acc, decc):
        self.xeryon_object.getCommunication().sendCommand(command, position, speed, acc, decc)

    #=====================================================================================================
    # - This function sends a command to the controller.
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #=====================================================================================================
    def sendCommandOnly(self, command):
        self.xeryon_object.getCommunication().sendCommandOnly(command)

   #=====================================================================================================
    # - This function sends a new setting to the controller.
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #=====================================================================================================
    def sendSetting(self, command, valueToSet):
        self.xeryon_object.getCommunication().sendSetting(command, valueToSet)

    #=====================================================================================================
    # - This function resets the axis.
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def reset(self):
        self.sendCommandOnly("RSET")
        self.was_valid_DPOS = False

    #===========================================================================
    # - This function check the status bits of amplifiers enabled.
    # - @param: None
    # - @return: True if the "Amplifiers enabled" flag is set to true.
    #===========================================================================
    def isAmplifiersEnabled(self, external_stat = None):
        return self.__getStatBitAtIndex(0, external_stat) == "1"
    
    #===========================================================================
    # - This fucntion check the status bits of end stop.
    # - @param: None
    # - @return: True if the "End stop" flag is set to true.
    #===========================================================================
    def isEndStop(self, external_stat = None):
        return self.__getStatBitAtIndex(1, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of thermal protection 1.
    # - @param: None
    # - @return: True if the "Thermal Protection 1" flag is set to true.
    #===========================================================================
    def isThermalProtection1(self, external_stat = None):
        return self.__getStatBitAtIndex(2, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of thermal protection 2.
    # - @param: None
    # - @return: True if the "Thermal Protection 2" flag is set to true.
    #===========================================================================
    def isThermalProtection2(self, external_stat = None):
        return self.__getStatBitAtIndex(3, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of force zero.
    # - @param: None
    # - @return: True if the "Force Zero" flag is set to true.
    #===========================================================================
    def isForceZero(self, external_stat = None):
        return self.__getStatBitAtIndex(4, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of motor on.
    # - @param: None
    # - @return: True if the "Motor On" flag is set to true.
    #===========================================================================
    def isMotorOn(self, external_stat = None):
        return self.__getStatBitAtIndex(5, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of closed loop.
    # - @param: None
    # - @return: True if the "Closed Loop" flag is set to true.
    #===========================================================================
    def isClosedLoop(self, external_stat = None):
        return self.__getStatBitAtIndex(6, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of encoder index.
    # - @param: None
    # - @return: True if the "Encoder index" flag is set to true.
    def isEncoderAtIndex(self, external_stat = None):
        return self.__getStatBitAtIndex(7, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of encoder valid.
    # - @param: None
    # - @return: True if the "Encoder Valid" flag is set to true.
    #===========================================================================
    def isEncoderValid(self, external_stat = None):
        return self.__getStatBitAtIndex(8, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of searching index.
    # - @param: None
    # - @return: True if the "Searching index" flag is set to true.
    #===========================================================================
    def isSearchingIndex(self, external_stat = None):
        return self.__getStatBitAtIndex(9, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of position reached.
    # - @param: None
    # - @return: True if the "Position Reached" flag is set to true.
    #===========================================================================
    def isPositionReached(self, external_stat = None):
        return self.__getStatBitAtIndex(10, external_stat) == "1"
    
    #===========================================================================
    # - This fucntion check the status bits of error compensation.
    # - @param: None
    # - @return: True if the "Error Compensation" flag is set to true.
    def isErrorCompensation(self, external_stat = None):
        return self.__getStatBitAtIndex(11, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of encoder error.
    # - @param: None
    # - @return: True if the "Encoder Error" flag is set to true.
    #===========================================================================
    def isEncoderError(self, external_stat = None):
        return self.__getStatBitAtIndex(12, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of scanning.
    # - @param: None
    # - @return: True if the "Scanning" flag is set to true.
    #===========================================================================
    def isScanning(self, external_stat = None):
        return self.__getStatBitAtIndex(13, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of left end stop.
    # - @param: None
    # - @return: True if the "Left end stop" flag is set to true.
    #===========================================================================
    def isAtLeftEnd(self, external_stat = None):
        return self.__getStatBitAtIndex(14, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of right end stop.
    # - @param: None
    # - @return: True if the "Right end stop" flag is set to true.
    #===========================================================================
    def isAtRightEnd(self, external_stat = None):
        return self.__getStatBitAtIndex(15, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of error limit.
    # - @param: None
    # - @return: True if the "ErrorLimit" flag is set to true.
    #===========================================================================
    def isErrorLimit(self, external_stat = None):
        return self.__getStatBitAtIndex(16, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of searching optimal frequency.
    # - @param: None
    # - @return: True if the "Searching Optimal Frequency" flag is set to true.
    #===========================================================================
    def isSearchingOptimalFrequency(self, external_stat = None):
        return self.__getStatBitAtIndex(17, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of safety timeout triggered.
    # - @param: None
    # - @return: True if the "Safety timeout triggered" flag is set to true.
    #===========================================================================
    def isSafetyTimeoutTriggered(self, external_stat = None):
        return self.__getStatBitAtIndex(18, external_stat) == "1"
    
    #===========================================================================
    # - This fucntion check the status bits of EtherCAT acknowledge.
    # - @param: None
    # - @return: True if the "EtherCAT acknowledge" flag is set to true.
    #===========================================================================
    def isEtherCatAcknowledge(self, external_stat = None):
        return self.__getStatBitAtIndex(19, external_stat) == "1"
    
    #===========================================================================
    # - This fucntion check the status bits of emergency stop. (NOT USED)
    # - @param: None
    # - @return: True if the "Emergency stop" flag is set to true.
    #===========================================================================
    def isEmergencyStop(self, external_stat = None):
        return self.__getStatBitAtIndex(20, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the status bits of position fail.
    # - @param: None
    # - @return: True if the "Position fail " flag is set to true.
    #===========================================================================
    def isPositionFailTriggered(self, external_stat = None):
        return self.__getStatBitAtIndex(21, external_stat) == "1"

    #===========================================================================
    # - This fucntion check the letter of the axis
    # - @param: None
    # - @return: The letter of the axis. If single axis system, it returns "X".
    #===========================================================================
    def getLetter(self):
        return self.axis_letter

    #===========================================================================
    # - Some settings have to be multiplied before it can be send to the controller.
    #   That's done in this function.
    # - @param: - tag:   The tag of the setting
    #           - value: The value of the setting
    # - @return: Return an adjusted value for this setting.
    #===========================================================================
    def applySettingMultipliers(self, tag, value):
        if "MAMP" in tag or "MIMP" in tag or "OFSA" in tag or "OFSB" in tag or "AMPL" in tag or "MAM2" in tag:
            value = str(int(int(value) * self.stage.amplitudeMultiplier))
        elif "PHAC" in tag or "PHAS" in tag:
            value = str(int(int(value) * self.stage.phaseMultiplier))
        elif "SSPD" in tag or "MSPD" in tag or "ISPD" in tag:
            value = str(int(float(value) * self.stage.speedMultiplier))
        elif "LLIM" in tag or "RLIM" in tag or "HLIM" in tag:
            if self.stage.isLineair:
                value = str(self.convertUnitsToEncoder(value, Units.mm))
            else:
                value = str(self.convertUnitsToEncoder(value, Units.deg))
        elif "POLI" in tag:
            self.def_poli_value = value
        elif "MASS" in tag:
            value = str(self.__massToCFREQ(value))
        elif "ZON1" in tag or "ZON2" in tag:
            if self.stage.isLineair:
                value = str(self.convertUnitsToEncoder(value, Units.mm))
            else:
                value = str(self.convertUnitsToEncoder(value, Units.deg))
        return str(value)

    #===========================================================================
    # - Initialize an Axis object.
    # - @param: - xeryon_object: This points to the Xeryon object.
    #           - axis_letter: This specifies a specific letter to this axis (str).
    #           - stage: This specifies the stage used in this axis (stage).
    # - @return: None
    #===========================================================================
    def __init__(self, xeryon_object, stage):
        self.xeryon_object = xeryon_object
        self.stage = stage
        self.axis_data = dict({"EPOS": 0, "DPOS": 0, "STAT": 0, "SSPD":0, "TIME":0})
        self.settings = dict({})
        if self.stage.isLineair:
            self.units = Units.mm
        else:
            self.units = Units.deg

        # IMPORTANT: 'logs' (and 'isLogging') are declared as class-level
        # attributes above. Assigning self.logs here gives THIS axis its own
        # dict. Without this, self.logs would resolve to the single shared
        # class-level dict, and receiveData()'s in-place mutations
        # (self.logs[tag].append(...)) would let every Axis instance write
        # into the SAME lists - corrupting each other's logged samples the
        # moment more than one axis logs concurrently.
        self.logs = {}

    #===========================================================================
    # - This function processes the commands that are send to this axis.
    #   if logging is enabled, this function will store the new incoming data.
    # - @param: - data: The command that is received.
    # - @return: None
    #===========================================================================
    def receiveData(self, data):
        if "=" in data:
            tag = data.split("=")[0]
            val = data.split("=")[1].rstrip("\n\r").replace(" ", "")
            
            if is_numeric(val):
                if tag not in NOT_SETTING_COMMANDS and "EPOS" not in tag and "DPOS" not in tag:
                    self.setSetting(tag, val, doNotSendThrough=True)
                else:
                    self.axis_data[tag] = val

                if "STAT" in tag:
                    if self.isSafetyTimeoutTriggered():
                        outputConsole("The safety timeout was triggered (TOU2 command). "
                                    "This means that the stage kept moving and oscillating around the desired position. "
                                    "A reset is required now OR 'ENBL=1' should be send.", True)
                    
                    if self.isPositionFailTriggered():
                        outputConsole("Safety timeout TOU3 went off, the 'position fail' status bit went high.")

                    if self.isThermalProtection1() or self.isThermalProtection2() or self.isErrorLimit() or self.isSafetyTimeoutTriggered():
                        if self.isErrorLimit():
                            outputConsole("Error limit is reached (status bit 16). A reset is required now OR 'ENBL=1' should be send.", True)

                        if self.isThermalProtection2() or self.isThermalProtection1():
                            outputConsole("Thermal protection 1 or 2 is raised (status bit 2 or 3). A reset is required now OR 'ENBL=1' should be send.", True)
                        
                        if self.isSafetyTimeoutTriggered():
                            outputConsole("Saftety timeout (TOU2 timeout reached) triggered. A reset is required now OR 'ENBL=1' should be send.", True)


                if "EPOS" in tag:
                    self.previous_epos = [self.previous_epos[-1], int(val)]
                    self.update_nb += 1

                if self.isLogging:
                    if tag not in ["SRNO", "XLS ", "XRTU", "XLA ", "XTRA", "SOFT", "SYNC"]:
                        if self.logs.get(tag) is None:
                            self.logs[tag] = []
                        
                        self.logs[tag].append(int(val))

                if "TIME" in tag:
                    self.previous_time = [self.previous_time[-1], int(val)]
                    t1 = self.previous_time[0]
                    t2 = int(val)
                    if t2 < t1:
                        t2 += 2**16

                    if len(self.previous_epos) >= 2:
                        if t2 - t1 > 0:
                            self.axis_data["SSPD"] = (self.previous_epos[1] - self.previous_epos[0])/((t2 - t1)*10)
                            
                            if self.isLogging:
                                if self.logs.get("SSPD") is None:
                                    self.logs["SSPD"] = []
                                self.logs["SSPD"].append(self.axis_data["SSPD"])
                    
                    pass

    #===========================================================================
    # - This function returns the value of a tag.
    #   eg: get("DPOS") returns the value stored for "DPOS".
    # - @param: - TAG: The tag requested.
    # - @return: Returns the value of this tag stored, if no data it returns None.
    #===========================================================================
    def getData(self, TAG):
        return self.axis_data.get(TAG)

    #===========================================================================
    # - This function sends ALL settings to the controller.
    # - @param: - value: None
    # - @return: None
    #===========================================================================
    def sendSettings(self):
        self.__sendCommand(
            str(self.stage.encoderResolutionCommand))
        for tag in self.settings:
            self.__sendCommand(str(tag) + "=" + str(self.getSetting(tag)))

    #===========================================================================
    # - This function is used to save the settings to the controller
    # - @param: None
    # - @return: None
    #===========================================================================
    def saveSettings(self):
        self.sendCommand("SAVE=0")

    #===========================================================================
    # - This function is used to convert a value to enconder units.
    # - @param: - value: The value that needs to be converted into encoder units.
    # - @return: The value converted into encoder units.
    #===========================================================================
    def convertUnitsToEncoder(self, value, units = None):
        if units is None:
            units = self.units
        value = float(value)
        if units == Units.mm:
            return round(value * 10 ** 6 * 1 / self.stage.encoderResolution)
        elif units == Units.mu:
            return round(value * 10 ** 3 * 1 / self.stage.encoderResolution)
        elif units == Units.nm:
            return round(value * 1 / self.stage.encoderResolution)
        elif units == Units.inch:
            return round(value * 25.4 * 10 ** 6 * 1 / self.stage.encoderResolution)
        elif units == Units.minch:
            return round(value * 25.4 * 10 ** 3 * 1 / self.stage.encoderResolution)
        elif units == Units.enc:
            return round(value)
        elif units == Units.mrad:
            return round(value * 10 ** 3 * 1 / self.stage.encoderResolution)
        elif units == Units.rad:
            return round(value * 10 ** 6 * 1 / self.stage.encoderResolution)
        elif units == Units.deg:
            return round(value * (2 * math.pi) / 360 * 10 ** 6 / self.stage.encoderResolution)
        else:
            self.xeryon_object.stop()
            raise ("Unexpected unit")

    #===========================================================================
    # - This function is used to convert a value from encoder units to another unit.
    # - @param: - value: The value that needs to be converted.
    # - @return: The value converted into the output unit.
    #===========================================================================
    def convertEncoderUnitsToUnits(self, value, units = None):
        if units is None:
            units = self.units
        value = float(value)
        if units == Units.mm:
            return value / (10 ** 6 * 1 / self.stage.encoderResolution)
        elif units == Units.mu:
            return value / (10 ** 3 * 1 / self.stage.encoderResolution)
        elif units == Units.nm:
            return value / (1 / self.stage.encoderResolution)
        elif units == Units.inch:
            return value / (25.4 * 10 ** 6 * 1 / self.stage.encoderResolution)
        elif units == Units.minch:
            return value / (25.4 * 10 ** 3 * 1 / self.stage.encoderResolution)
        elif units == Units.enc:
            return value
        elif units == Units.mrad:
            return value / (10 ** 3 * 1 / self.stage.encoderResolution)
        elif units == Units.rad:
            return value / (10 ** 6 * 1 / self.stage.encoderResolution)
        elif units == Units.deg:
            return value / ((2 * math.pi) / 360 * 10 ** 6 / self.stage.encoderResolution)
        else:
            self.xeryon_object.stop()
            raise ("Unexpected unit")

    #===========================================================================
    # - This function is used to send a command to the controller.
    #   NO "AXIS:" (e.g.: "X:") needs to be specified, just the command.
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #===========================================================================
    def sendSetting(self, command, valueToSet):
        self.xeryon_object.getCommunication().sendSetting(command, valueToSet)        

    #===========================================================================
    # - This function waits a couple of update messages.
    # - @param: - value: None
    # - @return: None
    #===========================================================================
    def __waitForUpdate(self):
        wait_nb = 3
    
        start_nb = int(self.update_nb)
        while (int(self.update_nb) - start_nb) < wait_nb:
            time.sleep(0.01)

    #===========================================================================
    # - This function returns the status bit at a specific index.
    # - @param: - bit_index: The index of the status bit.
    # - @return: The status bit (True of False).
    #===========================================================================
    def __getStatBitAtIndex(self, bit_index, external_stat = None):
        stat = self.getData("STAT")
        if external_stat is not None:
            stat = external_stat

        if stat is not None:
            bits = bin(int(stat)).replace("0b", "")[::-1]
            if len(bits) >= bit_index + 1:
                return bits[bit_index]
        return "0"

#===============================================================================
# This class handles the ethercat communication with the controller.
#===============================================================================
class Communication:
    stop_thread = False  # Boolean for stopping the thread.
    thread = None
    xeryon_object = None  # Link to the "Xeryon" object.

    def __init__(self, xeryon_object, net_id, port, drive_base = None):
        self.xeryon_object = xeryon_object
        self.readyToSend = []
        self.thread = None
        self.plc = None
        self.net_id = net_id
        self.port = port

        # Build this instance's own set of PLC symbol names so multiple
        # Communication objects (one per slave/drive) never collide on the
        # same MAIN.DriveX symbols.
        symbols = buildDriveSymbols(drive_base if drive_base is not None else DEFAULT_DRIVE_BASE)
        self.drive_base = drive_base if drive_base is not None else DEFAULT_DRIVE_BASE
        self.STATUS_SYMBOLS = symbols["STATUS_SYMBOLS"]
        self.BUSY_SYMBOL = symbols["BUSY_SYMBOL"]
        self.EPOS_SYMBOL = symbols["EPOS_SYMBOL"]
        self.TARGET_POS_SYMBOL = symbols["TARGET_POS_SYMBOL"]
        self.SPEED_SYMBOL = symbols["SPEED_SYMBOL"]
        self.ACC_SYMBOL = symbols["ACC_SYMBOL"]
        self.DEC_SYMBOL = symbols["DEC_SYMBOL"]
        self.COMMAND_SYMBOL = symbols["COMMAND_SYMBOL"]
        self.EXECUTE_SYMBOL = symbols["EXECUTE_SYMBOL"]
        pass

    #===========================================================================
    # - This function starts the ethercat communication
    # - @param: - external_communication_thread: If True, the function returns 
    #             the function that processes the data
    # - @return: None
    #===========================================================================
    def start(self, external_communication_thread = False):
          try:
            self.plc = pyads.Connection(self.net_id, self.port)
            self.plc.open()
            if external_communication_thread is False:
                self.stop_thread = False
                self.thread = threading.Thread(target=self.__processData)
                self.thread.daemon = True
                self.thread.start()
            else:
                return self.__processData
          except Exception as e:
            outputConsole("An error occured while trying to connect to PLC: ", True, True)
            outputConsole(str(e), True, True)
            raise Exception("Could not conect to PLC ")

    #===========================================================================
    # - This function sends the command with accoring arguments via ethercat
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #===========================================================================
    def sendCommand(self, command, position=0, speed=500000, acc=65000, decc=65000):
        self.plc.write_by_name(self.EXECUTE_SYMBOL, 0)
        self.plc.write_by_name(self.TARGET_POS_SYMBOL, position)
        self.plc.write_by_name(self.SPEED_SYMBOL, speed)
        self.plc.write_by_name(self.ACC_SYMBOL, acc)
        self.plc.write_by_name(self.DEC_SYMBOL, decc)
        self.plc.write_by_name(self.COMMAND_SYMBOL, command)
        self.plc.write_by_name(self.EXECUTE_SYMBOL, 1)        

   #===========================================================================
    # - This function sends the command with accoring arguments via ethercat
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #===========================================================================
    def sendCommandOnly(self, command):
        self.plc.write_by_name(self.EXECUTE_SYMBOL, 0)
        self.plc.write_by_name(self.COMMAND_SYMBOL, command)
        self.plc.write_by_name(self.EXECUTE_SYMBOL, 1)

   #===========================================================================
    # - This function sends the command with accoring arguments via ethercat
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #===========================================================================
    def sendSetting(self, command, value):
        self.plc.write_by_name(self.EXECUTE_SYMBOL, 0)
        self.plc.write_by_name(self.TARGET_POS_SYMBOL, value)
        self.plc.write_by_name(self.COMMAND_SYMBOL, command)
        self.plc.write_by_name(self.EXECUTE_SYMBOL, 1)

    #===========================================================================
    # - This function is ran in a seperate thread.
    # - @param: - external_while_loop: None.
    # - @return: None
    #===========================================================================
    def __processData(self, external_while_loop = False):
        try:
            while self.stop_thread is False:
 
                # Always refresh status + actual position, regardless of
                # whether a command is in flight.
                self.__pollStatusAndPosition()

                if external_while_loop is True:
                    return None

                # 
                # We need to check on status and position every ethercat cycle (LRW command). The demo 
                # application is using a cylce time of 1 millisecond. Time Measurements using 
                # time.perf_counter_ns() did reveal that it takes about 1 millisecond to read out all 
                # this info via ADS (only one slave connected). So sleeping for 1 millisecond would 
                # actually result in only having updates available after 2 milliseconds.    
                #
                #time.sleep(0.001)
 
            self.plc.close()
            print("ADS communication has stopped.")
        except Exception as e:
            print("An error occurred that crashed the ADS communication thread.")
            print(str(e))
            raise OSError(
                "An error occurred that crashed the ADS communication thread.\n"
                + str(e)
            )
        
    def __pollStatusAndPosition(self):
        axis = self.xeryon_object.getAllAxis()[0]  # single-axis per drive/Communication instance

        driveInputSymbols = list(self.STATUS_SYMBOLS.values()) + [self.EPOS_SYMBOL]
 
        try:
            inputs = self.plc.read_list_by_name(driveInputSymbols)

        except Exception as e:
            print(f"ADS read failed for driveInputSymbols: {e}")

        stat = 0
        
        for bit_index, symbol in self.STATUS_SYMBOLS.items():
            if inputs[symbol]:
                stat |= (1 << bit_index)
        axis.receiveData(f"STAT={stat}")
        axis.receiveData(f"EPOS={inputs[self.EPOS_SYMBOL]}")
  
    #===========================================================================
    # - This function closes the ethercat communication.
    # - @param: None
    # - @return: None
    #===========================================================================
    def closeCommunication(self):
        self.stop_thread = True
        self.plc.close()

#======================================================================================================================
# Stages class
#======================================================================================================================
class Stage(Enum):

    #======================================================================================================================
    # - Stages
    # - @param: - isLineair: True if the stage is lineair, False if it is rotary
    #           - encoderResolutionCommand: The command to set the encoder resolution.
    #           - encoderResolution: The encoder resolution in nanometer/microrad.
    #           - speedMultiplier: The speed multiplier.
    #======================================================================================================================
    XLS_312             = (True, "XLS1=312", 312.5, 1000)
    XLS_1250            = (True, "XLS1=1251", 1250, 1000)
    XLS_1250_OLD        = (True, "XLS1=1250", 1250, 1000)
    XLS_1250_OLD_2      = (True, "XLS1=1250", 312.5, 1000)
    XLS_78              = (True, "XLS1=78", 78.125, 1000)
    XLS_5               = (True, "XLS1=5", 5, 1000)
    XLS_1               = (True, "XLS1=1", 1, 1000)
    XLS_312_3N          = (True, "XLS3=312", 312.5,  1000)
    XLS_1250_3N         = (True, "XLS3=1251", 1250, 1000)
    XLS_1250_3N_OLD     = (True, "XLS3=1250", 312.5, 1000)
    XLS_78_3N           = (True, "XLS3=78", 78.125, 1000)
    XLS_5_3N            = (True, "XLS3=5", 5, 1000)
    XLS_1_3N            = (True, "XLS3=1", 1, 1000)
    XLA_312             = (True, "XLA1=312", 312.5, 1000)
    XLA_1250            = (True, "XLA1=1250", 1250, 1000)
    XLA_78              = (True, "XLA1=78", 78.125, 1000)
    XLA_OL              = (True, "XLA1=0", 1, 1000)
    XLA_OL_3N           = (True, "XLA3=0", 1, 1000)
    XLA_312_3N          = (True, "XLA3=312", 312.5, 1000)
    XLA_1250_3N         = (True, "XLA3=1250", 1250, 1000)
    XLA_78_3N           = (True, "XLA3=78", 78.125, 1000)
    XLA_312_5N          = (True, "XLA3=312", 312.5, 1000)
    XLA_1250_5N         = (True, "XLA3=1250", 1250, 1000)
    XLA_78_5N           = (True, "XLA3=78", 78.125, 1000)
    XLA_312_10N         = (True, "XLA3=312", 312.5, 1000)
    XLA_1250_10N        = (True, "XLA3=1250", 1250, 1000)
    XLA_78_10N          = (True, "XLA3=78", 78.125, 1000)
    XLA_312_OLD         = (True, "XLA=312", 312.5, 1000)
    XLA_1250_OLD        = (True, "XLA=1250", 1250, 1000)
    XLA_78_OLD          = (True, "XLA=78", 78.125, 1000)
    XRTA                = (False, "XRTA=109", (2 * math.pi * 1e6) / 57600, 100)
    XRTU_40_3           = (False, "XRT1=2", (2 * math.pi * 1e6) / 2764800 , 100)
    XRTU_40_19          = (False, "XRT1=18", (2 * math.pi * 1e6) / 345600 , 100)
    XRTU_40_49          = (False, "XRT1=47", (2 * math.pi * 1e6) / 135000 , 100)
    XRTU_40_109         = (False, "XRT1=73", (2 * math.pi * 1e6) / 86400, 100)
    XRTU_30_3           = (False, "XRT1=3", (2 * math.pi * 1e6) / 1843200, 100)
    XRTU_30_19          = (False, "XRT1=19", (2 * math.pi * 1e6) / 360000, 100)
    XRTU_30_49          = (False, "XRT1=49", (2 * math.pi * 1e6) / 144000, 100)
    XRTU_30_109         = (False, "XRT1=109", (2 * math.pi * 1e6) / 57600, 100)
    XRTU_60_3           = (False, "XRT3=3", (2 * math.pi * 1e6) /2073600, 100)
    XRTU_60_19          = (False, "XRT3=19", (2 * math.pi * 1e6) /324000, 100)
    XRTU_60_49          = (False, "XRT3=49", (2 * math.pi * 1e6) /129600, 100)
    XRTU_60_109         = (False, "XRT3=109", (2 * math.pi * 1e6) /64800, 100)
    XRTU_30_109_OLD     = (False, "XRTU=109", (2 * math.pi * 1e6) / 57600, 100)
    XRTU_40_73_OLD      = (False, "XRTU=73", (2 * math.pi * 1e6) / 86400, 100)
    XRTU_40_3_OLD       = (False, "XRTU=3", (2 * math.pi * 1e6) / 1800000, 100)

    def __init__(self, isLineair, encoderResolutionCommand, encoderResolution, speedMultiplier):

        self.isLineair = isLineair
        self.encoderResolutionCommand = encoderResolutionCommand
        self.encoderResolution = encoderResolution
        self.speedMultiplier = speedMultiplier
        self.amplitudeMultiplier = AMPLITUDE_MULTIPLIER
        self.phaseMultiplier = PHASE_MULTIPLIER

    #===========================================================================
    # - This is the function to get the stage type by specifying "stage_command"
    # - @param: - stage_command: String containing "XLS=.." or "XRTU=..." or ...
    # - @return: Stagetype, or none if invalid stage command
    #===========================================================================
    def getStage(self, stage_command):
        for stage in Stage:
            if stage_command in str(stage.encoderResolutionCommand).replace(" ", ""):
                return stage
        return None

#===============================================================================
# - This function returns the actual time in ms.
# - @param: None
# - @return: Returns the actual time in ms.
#===============================================================================
def getActualTime():
    """
    :return: Returns the actual time in ms.
    """
    return int(round(time.time() * 1000))

#===============================================================================
# - This function returns a string containting the EPOS & DPOS value's and the 
#   current units.
# - @param: DPOS, EPOS, Unit
# - @return: A string containting the EPOS & DPOS value's and the current units.
#===============================================================================
def getDposEposString(DPOS, EPOS, Unit):
    return str("DPOS: " + str(DPOS) + " " + str(Unit) + " and EPOS: " + str(EPOS) + " " + str(Unit))

#===============================================================================
# - This function outputs a message to the console.
# - @param: - message: The message to output to the console.
# - @return: None
#===============================================================================
def outputConsole(message, error=False, force=True):
    if OUTPUT_TO_CONSOLE is True:
        if error is True:
            print("\033[91m" + "ERROR: " + message + "\033[0m")
        else:
            print(message)

#===============================================================================
# - This function checks if a string is numeric.
# - @param: value: The string to check.
# - @return: True if the string is numeric, False if not.
#===============================================================================
def is_numeric(value):
    try:
        int(value)
        return True
    except ValueError:
        return False