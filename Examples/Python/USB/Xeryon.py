#=====================================================================================================
# Xeryon.py library for Python
# Supporting the XD-C, XD-M and XD-OEM controllers
#=====================================================================================================

#=====================================================================================================
# Imprt these libraries
#=====================================================================================================
import serial
import threading
from enum import Enum
import time
import math
import serial.tools.list_ports
import re

#=====================================================================================================
# Global variables:
#   - SETTINGS_FILENAME: The location of the settings_default.txt file
#   - LIBRARY_VERSION: The version of the library
#=====================================================================================================
SETTINGS_FILENAME = "settings_default.txt"
#SETTINGS_FILENAME = "C://Users//PhilippeHiroux//OneDrive - XERYON//Documenten//XRT-U-30//settings_default.txt"
LIBRARY_VERSION = "v1.88"

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
    axis_letter_list = None
    master_settings = None

    #=====================================================================================================
    # - @param - COM_port: Specify the COM port used (string)
    #          - baudrate: Specify the baudrate (int)
    # - @return: Return a Xeryon object
    #=====================================================================================================
    def __init__(self, COM_port = None, baudrate = 115200):
        self.comm = Communication(self, COM_port, baudrate)
        self.axis_list = []
        self.axis_letter_list = []
        self.master_settings = {}

    #=====================================================================================================
    # - This function returns True if it's a single axis system, False if its a multiple axis system.
    # - @param: None
    # - @return: Returns True if it's a single axis system, False if its a multiple axis system.
    #=====================================================================================================
    def isSingleAxisSystem(self):
        return len(self.getAllAxis()) <= 1

    #=====================================================================================================
    # - This functions NEEDS to be ran before any commands are executed.
    #   This function starts the serial communication and configures the settings with the controller.
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
        # Start the serial communication
        #=====================================================================================================
        comm = self.getCommunication().start(external_communication_thread)

        #=====================================================================================================
        # Reset all axes
        #=====================================================================================================
        for axis in self.getAllAxis():
            axis.reset()
        
        #=====================================================================================================
        # Wait a bit to give the controller time to reset
        #=====================================================================================================
        time.sleep(0.2)        

        #=====================================================================================================
        # Read the settings file and send them to the controller
        #=====================================================================================================
        self.readSettings(external_settings_default)
        if AUTO_SEND_SETTINGS:
            self.sendMasterSettings()
            for axis in self.getAllAxis():
                axis.sendSettings()

        #=====================================================================================================
        # Enable all axes
        #=====================================================================================================
        for axis in self.getAllAxis():
            axis.sendCommand("ENBL=1")

        #=====================================================================================================
        # Send all the commands to the controller to read the settings
        #=====================================================================================================
        for axis in self.getAllAxis():
            axis.sendCommand("HLIM=?")
            axis.sendCommand("LLIM=?")
            axis.sendCommand("SSPD=?")
            axis.sendCommand("PTO2=?")
            axis.sendCommand("PTOL=?")
            if "XRTA" in str(axis.stage):
                axis.sendCommand("ENBL=3")
        
        #=====================================================================================================
        # Return the communication object
        #=====================================================================================================
        if external_communication_thread:
            return comm
        
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
            axis.sendCommand("ZERO=0")
            axis.sendCommand("STOP=0")
            time.sleep(0.001)
            axis.was_valid_DPOS = False

        #=====================================================================================================
        # Close the communication
        #=====================================================================================================
        self.getCommunication().closeCommunication()
        outputConsole("Program stopped running.")

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
            axis.sendCommand("STOP=0")
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
        # Read the settings file and send them to the controller
        #=====================================================================================================
        self.readSettings()

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
    #           - axis_letter: Specify the axis letter.
    # - @return: Returns an Axis object
    #=====================================================================================================
    def addAxis(self, stage, axis_letter):
        newAxis = Axis(self, axis_letter, stage)
        self.axis_list.append(newAxis)  # Add axis to axis list.
        self.axis_letter_list.append(axis_letter)
        return newAxis

    #=====================================================================================================
    # - This function returns the communication class.
    # - @param: None
    # - @return: The communication class.
    #=====================================================================================================
    def getCommunication(self):
        return self.comm

    #=====================================================================================================
    # - This function returns the correct axis object. Or None if the axis does not exist.
    # - @param: - letter: Specify the axis letter
    # - @return: Returns the correct axis object. Or None if the axis does not exist.
    #=====================================================================================================
    def getAxis(self, letter):

        #=====================================================================================================
        # Check if axis exists and return it
        #=====================================================================================================
        if self.axis_letter_list.count(letter) == 1:
            indx = self.axis_letter_list.index(letter)
            if len(self.getAllAxis()) > indx:
                return self.getAllAxis()[indx]
            
        #=====================================================================================================
        # Axis does not exist, return None
        #=====================================================================================================
        return None

    #=====================================================================================================
    # - This function reads the settings_default.txt file and processes each line.
    #   It first determines for what axis the setting is, then it reads the setting and saves it.
    #   If there are commands for axis that don't exist, it just ignores them.
    # - @param: - external_settings_default: Specify an external settings file
    # - @return: None
    #=====================================================================================================
    def readSettings(self, external_settings_default = None):

        #=====================================================================================================
        # Try this code
        #=====================================================================================================
        try:

            #=====================================================================================================
            # Open the settings_default.txt file
            #=====================================================================================================
            if external_settings_default is None:
                file = open(SETTINGS_FILENAME, "r")
            else:
                file = open(external_settings_default, "r")

            #=====================================================================================================
            # Go trough each line of the settings_default.txt file
            #=====================================================================================================
            for line in file.readlines():

                #=====================================================================================================
                # Check if it's a command
                #=====================================================================================================
                if "=" in line and line.find("%") != 0:

                    #=====================================================================================================
                    # Process the command
                    #=====================================================================================================
                    line = line.strip("\n\r").replace(" ", "")
                    axis = self.getAllAxis()[0]

                    #=====================================================================================================
                    # Check if axis is specified
                    #=====================================================================================================
                    if ":" in line:
                        axis = self.getAxis(line.split(":")[0])

                        #=====================================================================================================
                        # Check if axis exists
                        #=====================================================================================================
                        if axis is None:
                            continue

                        #=====================================================================================================
                        # Strip "X:" from command
                        #=====================================================================================================
                        line = line.split(":")[1]

                    #=====================================================================================================
                    # Check if it's a multi-axis system
                    #=====================================================================================================
                    elif not self.isSingleAxisSystem():
                       
                        #=====================================================================================================
                        # Romve comments from command
                        #=====================================================================================================
                        if "%" in line:
                            line = line.split("%")[0]
                        self.setMasterSetting(line.split("=")[0], line.split("=")[1], True)
                        continue

                    #=====================================================================================================
                    # Romve comments from command
                    #=====================================================================================================
                    if "%" in line:
                        line = line.split("%")[0]

                    #=====================================================================================================
                    # Split the command into tag and value
                    #=====================================================================================================
                    tag = line.split("=")[0]
                    value = line.split("=")[1]

                    #=====================================================================================================
                    # Update settings
                    #=====================================================================================================
                    axis.setSetting(tag, value, True, doNotSendThrough=True)

            #=====================================================================================================
            # Close the settings_default.txt file    
            #=====================================================================================================
            file.close()
        
        #=====================================================================================================
        # If the settings_default.txt file is not found
        #=====================================================================================================
        except FileNotFoundError as e:
            if external_settings_default is None:
                outputConsole("No settings_default.txt found.")
            else:
                raise e

        #=====================================================================================================
        # If something else went wrong
        #=====================================================================================================
        except Exception as e:
            raise e

    #=====================================================================================================
    # - This function adds a setting (tag, value) to the list of settings for the master
    # - @param: - tag: The tag of the setting
    #           - value: The value of the setting
    #           - fromSettingsFile: If the setting was read from the settings file
    # - @return: None
    #=====================================================================================================
    def setMasterSetting(self, tag, value, fromSettingsFile=False):
        self.master_settings.update({tag: value})
        if not fromSettingsFile:
            self.comm.sendCommand(str(tag)+"="+str(value))
        if "COM" in tag:
            self.setCOMPort(str(value))
    
    #=====================================================================================================
    # - This function sends the master settings to the controller
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def sendMasterSettings(self, axis=False):
        prefix = ""
        if axis is not False:
            prefix = str(self.getAllAxis()[0].getLetter()) + ":"

        for tag, value in self.master_settings.items():
            self.comm.sendCommand(str(prefix) + str(tag) + "="+str(value))

    #=====================================================================================================
    # - This function sends the master settings to the controller
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def saveMasterSettings(self, axis=False):
        if axis is None:
            self.comm.sendCommand("SAVE=0")
        else:
            self.comm.sendCommand(str(self.getAllAxis()[0].getLetter()) + ":SAVE=0")

    #=====================================================================================================
    # - This function sets the COM-port
    # - @param: - com_port: The COM-port to set
    # - @return: None
    #=====================================================================================================
    def setCOMPort(self, com_port):
        self.getCommunication().setCOMPort(com_port)

    #=====================================================================================================
    # - This function loops through every available COM-port.
    #   It check's if it contains any signature of Xeryon.
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def findCOMPort(self):
        if OUTPUT_TO_CONSOLE:
            print("Automatically searching for COM-Port. If you want to speed things up you should manually provide it inside the controller object.")
        ports = list(serial.tools.list_ports.comports())
        com_port = None
        for port in ports:
            if "04D8" in str(port.hwid):
                self.setCOMPort(str(port.device))
                break

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
    # - @param: direction: Specifies in whick direction to start the search for the index.
    # - @return: None
    #=====================================================================================================
    def findIndex(self, forceWaiting = False, direction=0):
       
        #=====================================================================================================
        # Send INDX to the controller.
        #=====================================================================================================
        self.__sendCommand("INDX=" + str(direction))
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
    # - This function sends the MOVE command to the controller.
    # - @param: value: The direction to move to.
    # - @return: None
    #=====================================================================================================
    def move(self, value):
        value = int(value)
        direction = 0
        if value > 0:
            direction = 1
        elif value < 0:
            direction = -1
        self.sendCommand("MOVE=" + str(direction))

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
    def setDPOS(self, value, differentUnits=None, outputToConsole=True, forceWaiting = False):
        
        #=====================================================================================================
        # Take the current units.
        #=====================================================================================================
        unit = self.units 
        if differentUnits is not None:
            unit = differentUnits

        #=====================================================================================================
        # Convert the value into encoder units
        #=====================================================================================================
        DPOS = int(self.convertUnitsToEncoder(value, unit))
        error = False

        #=====================================================================================================
        # Send DPOS to the controller.
        #=====================================================================================================
        self.__sendCommand("DPOS=" + str(DPOS))
        self.was_valid_DPOS = True

        #=====================================================================================================
        # Wait for the position to be reached.
        # Block all futher processes until position is reached.
        # This check isn't nessecary in DEBUG mode or when DISABLE_WAITING is True
        #=====================================================================================================
        if DEBUG_MODE is False and DISABLE_WAITING is False or forceWaiting is True:  
    
            #=====================================================================================================
            # Wait until EPOS is within PTO2 AND positionReached status is received.
            #=====================================================================================================
            while not (self.__isWithinTol(DPOS) and self.isPositionReached()):

                #=====================================================================================================
                # Check if stage is at left end or right end.
                #=====================================================================================================
                if self.isAtLeftEnd() or self.isAtRightEnd():
                    # TODO: fix this so it does not go off while positioning on the limit value. 
                    outputConsole("DPOS is out or range. (1) " + getDposEposString(value, self.getEPOS(), unit), True)
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
            outputConsole(getDposEposString(value, self.getEPOS(), unit))
        
        return True

    #=====================================================================================================
    # - This function sends the TRGS command to the controller. Define the start of the trigger pulses.
    # - @param: - value: The new value TRGS has to become.
    # - @return: None
    #=====================================================================================================
    def setTRGS(self, value):
        value_in_encoder_positions = int(self.convertUnitsToEncoder(value))
        self.sendCommand("TRGS=" + str(value_in_encoder_positions))

    #=====================================================================================================
    # - This function sends the TRGW command to the controller. Define the width of the trigger pulses.
    # - @param: - value: Width of the trigger pulses. Expressed in the current units.
    # - @return: None
    #=====================================================================================================
    def setTRGW(self, value):
        value_in_encoder_positions = int(self.convertUnitsToEncoder(value))
        self.sendCommand("TRGW=" + str(value_in_encoder_positions))

    #=====================================================================================================
    # - This function sends the TRGP command to the controller. Define the pitch of the trigger pulses.
    # - @param: - value: Pitch of the trigger pulses. Expressed in the current units.
    # - @return: None
    #=====================================================================================================
    def setTRGP(self, value):
        value_in_encoder_positions = int(self.convertUnitsToEncoder(value))
        self.sendCommand("TRGP=" + str(value_in_encoder_positions))

    #=====================================================================================================
    # - This function sends the TRGN command to the controller. Define the number of trigger pulses.
    # - @param: - value: Number of trigger pulses.
    # - @return: None
    #=====================================================================================================
    def setTRGN(self, value):
        self.sendCommand("TRGN=" + str(int(value)))

    #=====================================================================================================
    # - This function returns the current DPOS in the current units.
    # - @param: None
    # - @return: Return the desired position (DPOS) in the current units.
    #=====================================================================================================
    def getDPOS(self):
        return self.convertEncoderUnitsToUnits(self.getData("DPOS"), self.units)

    #=====================================================================================================
    # - This function returns the current Units this stage is working in.
    # - @param: None
    # - @return: Return the current units this stage is working in.
    #=====================================================================================================
    def getUnit(self):
        return self.units

    #=====================================================================================================
    # - This function is used to make the axis move in steps.
    # - @param: - value: The amount it needs to step (specified in the current units)
    # - @return: None
    #=====================================================================================================
    def step(self, value, forceWaiting = False):

        #=====================================================================================================
        # Convert the value to encoder units.
        #=====================================================================================================
        step = self.convertUnitsToEncoder(value, self.units)

        #=====================================================================================================
        # Calculate the new DPOS.
        #=====================================================================================================
        if self.was_valid_DPOS:
            new_DPOS = int(self.getData("DPOS")) + step
        else:
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
        self.setDPOS(new_DPOS, Units.enc, False, forceWaiting=forceWaiting)
        if DISABLE_WAITING is False:
            self.__waitForUpdate()  # Waits a couple of updates, so the EPOS is valid and doesn't lagg behind.
            outputConsole("Stepped: " + str(self.convertEncoderUnitsToUnits(step, self.units)) + " " + str(self.units) + " " + getDposEposString(self.getDPOS(), self.getEPOS(), self.units))

    #=====================================================================================================
    # - This function returns the current EPOS in the current units.
    # - @param: None
    # - @return: Return the encoder position (EPOS) in the current units.
    #=====================================================================================================
    def getEPOS(self):
        return self.convertEncoderUnitsToUnits(self.getData("EPOS"), self.units)

    #=====================================================================================================
    # - This function sets the units this axis needs to work in.
    # - @param: - units: The units this axis needs to work in.
    # - @return: None
    #=====================================================================================================
    def setUnits(self, units):
        self.units = units

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
            self.setSetting("POLI", "1")
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

        self.setSetting("POLI", str(self.def_poli_value))
        self.xeryon_object.getAllAxis()[0].setSetting("POLI", str(self.def_poli_value))
        return logs

    #=====================================================================================================
    # - This function returns the current frequency.
    # - @param: None
    # - @return: Return the frequency.
    #=====================================================================================================
    def getFrequency(self):
        return self.getData("FREQ")

    #=====================================================================================================
    # - This function is used to send settings to the controller.
    # - @param: - tag: The tag that needs to be stored
    #           - value: The value
    # - @return: None
    #=====================================================================================================
    def setSetting(self, tag, value, fromSettingsFile=False, doNotSendThrough=False):
        if fromSettingsFile:
            value = self.applySettingMultipliers(tag, value)
            if "MASS" in tag:
                tag = "CFRQ"
        if "?" not in str(value):
            self.settings.update({tag: value})
        if not doNotSendThrough:
            self.__sendCommand(str(tag) + "=" + str(value))
            time.sleep(0.001)

    #=====================================================================================================
    # - This function starts a scan.
    # - @param: - direction: Positive or negative number.
    #           - execTime: How long the scan should be executed.
    # - @return: None
    #=====================================================================================================
    def startScan(self, direction, execTime=None, untilLimit=False):
        self.__sendCommand("SCAN=" + str(int(direction)))
        self.was_valid_DPOS = False

        if execTime is not None:
            time.sleep(execTime)
            self.__sendCommand("SCAN=0")
        
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
        self.__sendCommand("SCAN=0")
        #time.sleep(0.001)
        self.was_valid_DPOS = False

    #=====================================================================================================
    # - This function sets the speed of the axis.
    # - @param: - speed: The new speed this axis needs to operate on.
    #                    The speed is specified in the current units/second.
    # - @return: None
    #=====================================================================================================
    def setSpeed(self, speed):

        #=====================================================================================================
        # Check if the stage is lineair and convert the speed to micrometer
        #=====================================================================================================
        if self.stage.isLineair:
            speed = int(self.convertEncoderUnitsToUnits(self.convertUnitsToEncoder(speed, self.units), Units.mu))

        #=====================================================================================================
        # Check if the stage is rotary and convert the speed to degrees
        #=====================================================================================================
        else:
            speed = self.convertEncoderUnitsToUnits(self.convertUnitsToEncoder(speed, self.units), Units.deg)
            speed = int(speed) * 100
        self.setSetting("SSPD", str(speed))

    #=====================================================================================================
    # - This function returns the value of the setting with the given tag.
    # - @param: - tag: The tag that indicates the setting.
    # - @return: The value of the setting with the given tag.
    #=====================================================================================================
    def getSetting(self, tag):
        return self.settings.get(tag)

    #=====================================================================================================
    # - This function sets the value of the setting PTOL with the given tag (in encoder units!).
    # - @param: - tag: The tag that indicates the setting.
    # - @return: None
    #=====================================================================================================
    def setPTOL(self, value):
        self.setSetting("PTOL", value)

    #=====================================================================================================
    # - This function sets the value of the setting PTO2 with the given tag (in encoder units!).
    # - @param: - tag: The tag that indicates the setting.
    # - @return: None
    #=====================================================================================================
    def setPTO2(self, value):
        self.setSetting("PTO2", value)

    #=====================================================================================================
    # - This function sends a command to the controller.
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #=====================================================================================================
    def sendCommand(self, command):

        #=====================================================================================================
        # Split the command to tag and value
        #=====================================================================================================
        tag = command.split("=")[0]
        value = str(command.split("=")[1])

        #=====================================================================================================
        # Send the command to the controller
        #=====================================================================================================
        if tag in NOT_SETTING_COMMANDS:
            self.__sendCommand(command)
        else:
            self.setSetting(tag, value)

    #=====================================================================================================
    # - This function resets the axis.
    # - @param: None
    # - @return: None
    #=====================================================================================================
    def reset(self):
        self.sendCommand("RSET=0")
        self.was_valid_DPOS = False

    #===========================================================================
    # - This fucntion check the status bits of amplifiers enabled.
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
    def __init__(self, xeryon_object, axis_letter, stage):
        self.axis_letter = axis_letter
        self.xeryon_object = xeryon_object
        self.stage = stage
        self.axis_data = dict({"EPOS": 0, "DPOS": 0, "STAT": 0, "SSPD":0, "TIME":0})
        self.settings = dict({})
        if self.stage.isLineair:
            self.units = Units.mm
        else:
            self.units = Units.deg

    #===========================================================================
    # - Conversion table to change the value of the setting "MASS" into a value for the settings "CFRQ".
    # - @param - mass: The value of the setting "MASS"
    # - @return: The value for the setting "CFRQ"
    #===========================================================================
    def __massToCFREQ(self, mass):
        mass = int(mass)
        if mass <= 50:
            return 100000
        if mass <= 100:
            return 60000
        if mass <= 250:
            return 30000
        if mass <= 500:
            return 10000
        if mass <= 1000:
            return 5000
        return 3000

    #===========================================================================
    # - This function returns the letter of the axis.
    # - @param: None
    # - @return: The letter of the axis.
    #===========================================================================
    def __str__(self):
        return str(self.axis_letter)

    #===========================================================================
    # - Check if the EPOS is within PTO2 of the desired position.
    # - @param: - DPOS: The desired position
    # - @return: True if EPOS is within PTO2 of DPOS. (PTO2 = Position Tolerance 2)
    #===========================================================================
    def __isWithinTol(self, DPOS):
        DPOS = abs(int(DPOS))
        if self.getSetting("PTO2") is not None:
            PTO2 = int(self.getSetting("PTO2"))
        elif self.getSetting("PTOL") is not None:
            PTO2 = int(self.getSetting("PTOL"))
        else:
            PTO2 = 10 #TODO
        EPOS = abs(int(self.getData("EPOS")))

        if DPOS - PTO2 <= EPOS <= DPOS + PTO2:
            return True

    #===========================================================================
    # - Check if the timeout time has been reached.
    # - @param: - start_time:  The time the command started in ms.
    #           - distance:    The distance the stage needs to travel.
    # - @return: True if the timeout time has been reached.
    #===========================================================================
    def __timeOutReached(self, start_time, distance):
        t = getActualTime()
        speed = int(self.getSetting("SSPD"))
        timeout_t = (distance / speed * 1000)
        timeout_t *= 1.25

        #===========================================================================
        # For quick and tiny movements, the method above is not accurate.
        # If the timeout_t is smaller than the specified TOUT&TOU2, use TOUT+TOU2
        #===========================================================================
        if self.getSetting("TOUT") is not None:
            TOUT = int(self.getSetting("TOUT"))*3
            if TOUT > timeout_t:
                timeout_t = TOUT

        return (t - start_time) > timeout_t

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

                        if AUTO_SEND_ENBL:
                            self.xeryon_object.setMasterSetting("ENBL", "1")
                            outputConsole("'ENBL=1' is automatically send.")

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
    def __sendCommand(self, command):
        tag = command.split("=")[0]
        value = str(command.split("=")[1])

        prefix = ""
        if not self.xeryon_object.isSingleAxisSystem():
            prefix = self.axis_letter + ":"

        command = tag + "=" + str(value)
        self.xeryon_object.getCommunication().sendCommand(prefix + command)

    #===========================================================================
    # - This function waits a couple of update messages.
    # - @param: - value: None
    # - @return: None
    #===========================================================================
    def __waitForUpdate(self):
        wait_nb = 3

        if self.getSetting("POLI") is not None:
            wait_nb = wait_nb / int(self.def_poli_value) * int(self.getSetting("POLI"))

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
# This class handles the serial communication with the controller.
#===============================================================================
class Communication:
    ser = None  # Holds the serial connection.
    readyToSend = None  # List that contains commands that are ready to send.
    stop_thread = False  # Boolean for stopping the thread.
    thread = None
    xeryon_object = None  # Link to the "Xeryon" object.

    def __init__(self, xeryon_object, COM_port, baud):
        self.xeryon_object = xeryon_object
        self.COM_port = COM_port
        self.baud = baud
        self.readyToSend = []
        self.thread = None
        self.ser = None
        pass

    #===========================================================================
    # - This function starts the serial communication on the specified COM port 
    #   and baudrate in a seperate thread.
    # - @param: - external_communication_thread: If True, the function returns 
    #             the function that processes the data
    # - @return: None
    #===========================================================================
    def start(self, external_communication_thread = False):
        if self.COM_port is None:
            self.xeryon_object.findCOMPort()
        if self.COM_port is None: #No com port found
            raise Exception("No COM_port could automatically be found. You should provide it manually.")

        try:
            self.ser = serial.Serial(self.COM_port, self.baud, timeout=0.01)
            self.ser.flush()
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            if external_communication_thread is False:
                self.stop_thread = False
                self.thread = threading.Thread(target=self.__processData)
                self.thread.daemon = True
                self.thread.start()
            else:
                return self.__processData
        except Exception as e:
            outputConsole("An error occured while trying to connect to COM: " + str(self.COM_port), True, True)
            outputConsole(str(e), True, True)
            raise Exception("Could not conect to COM " + str(self.COM_port))
        
    #===========================================================================
    # - This function adds the command to the readyToSend list.
    # - @param: - command: The command that needs to be send.
    # - @return: None
    #===========================================================================
    def sendCommand(self, command):
        self.readyToSend.append(command)

    #===========================================================================
    # - This function sets the COM port.
    # - @param: - com_port: The COM port.
    # - @return: None
    #===========================================================================
    def setCOMPort(self, com_port):
        self.COM_port = com_port

    #===========================================================================
    # - This function is ran in a seperate thread.
    # - @param: - external_while_loop: None.
    # - @return: None
    #===========================================================================
    def __processData(self, external_while_loop = False):
        try:
            while self.stop_thread is False and self.ser.is_open:

                dataToSend = list(self.readyToSend[0:10])
                self.readyToSend = self.readyToSend[10:]

                for command in dataToSend:
                    self.ser.write(str.encode(command.rstrip("\n\r") + "\n"))

                max_to_read = 10
                try:
                    while self.ser.in_waiting > 0 and max_to_read >0:
                        reading = self.ser.readline().decode()
                        if "=" in reading:
                            if len(reading.split(":")) == 2:
                                axis = self.xeryon_object.getAxis(reading.split(":")[0])
                                reading = reading.split(":")[1]
                                if axis is None:
                                    axis = self.xeryon_object.axis_list[0]
                                axis.receiveData(reading)
                            else:
                                axis = self.xeryon_object.axis_list[0]
                                axis.receiveData(reading)

                        max_to_read -= 1
                except Exception as e:
                    print(str(e))

                if external_while_loop is True:
                    return None    
                
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.close()
            print("Communication has stopped. ")
        except Exception as e:
            print("An error has occured that crashed the communication thread.")
            print(str(e))
            raise OSError("An error has occurred that crashed the communicaiton thread. \n" + str(e))
  
    #===========================================================================
    # - This function closes the serial communication.
    # - @param: None
    # - @return: None
    #===========================================================================
    def closeCommunication(self):
        self.stop_thread = True

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
    XRT_U_35_3          = (False, "XRT3=6", (2 * math.pi * 1e6) / 2093280, 100)
    XRT_U_35_100        = (False, "XRT3=101", (2 * math.pi * 1e6) / 64080, 100)
    XRT_U_35_250        = (False, "XRT3=251", (2 * math.pi * 1e6) / 21360, 100)

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