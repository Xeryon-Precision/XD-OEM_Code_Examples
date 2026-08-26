"""Xeryon.py library for Python.

Supporting the XD-C, XD-M and XD-OEM controllers.

This module provides the :class:`Xeryon` controller object, the
:class:`Axis` and :class:`Communication` helper classes, and the
:class:`Stage`/:class:`Units` enums used to configure and drive
Xeryon piezo motion stages over a serial connection.
"""

import math
import threading
import time
from enum import Enum

import serial
import serial.tools.list_ports

# ---------------------------------------------------------------------------
# Library-wide configuration
# ---------------------------------------------------------------------------

#: Location of the settings_default.txt file.
SETTINGS_FILENAME = "settings_default.txt"

#: Version of this library.
LIBRARY_VERSION = "v2.0"

#: Debug mode. Handy when no stage is connected: it skips some checks,
#: e.g. when DPOS=.. is sent, EPOS isn't checked to be in range.
DEBUG_MODE = False

#: If True, a lot of data (new DPOS/EPOS, status messages, ...) is printed
#: to the console. If False, all console output is suppressed.
OUTPUT_TO_CONSOLE = True

#: If True, every line printed via outputConsole() (and the communication
#: thread's own lifecycle messages) is prefixed with a
#: "[YYYY-MM-DD HH:MM:SS.mmm]"
#: wall-clock timestamp. Set to False to go back to plain, unprefixed
#: output.
OUTPUT_CONSOLE_TIMESTAMPS = True

#: If True, the library won't wait until a position is reached: all
#: blocking functions are disabled. NOTE: if you enable this, do a
#: +/- 5 second timeout (time.sleep(5)) yourself after finding the index
#: of each stage.
DISABLE_WAITING = False

#: If True, the settings in settings_default.txt are automatically sent
#: to the connected stages on startup.
AUTO_SEND_SETTINGS = True

#: "ENBL=1" needs to be sent when an error occurs (thermal error - bits 2 &
#: 3, error limit - bit 16, or safety timeout - bit 18). Set this to True
#: to automatically send "ENBL=1" when these errors occur, bypassing this
#: safety feature.
AUTO_SEND_ENBL = False

#: Commands whose values are NOT cached as "settings" by this library.
NOT_SETTING_COMMANDS = [
    "DPOS", "EPOS", "HOME", "ZERO", "RSET", "INDX", "STEP", "MOVE", "STOP",
    "CONT", "SAVE", "STAT", "TIME", "SRNO", "SOFT", "XLA3", "XLA1", "XRT1",
    "XRT3", "XLS1", "XLS3", "SFRQ", "SYNC",
]
DEFAULT_POLI_VALUE = 200
AMPLITUDE_MULTIPLIER = 1456.0
PHASE_MULTIPLIER = 182

class Xeryon:
    """Top-level controller object.

    Represents one Xeryon controller (XD-C, XD-M or XD-OEM), reachable over
    a single serial port, that can drive one or more :class:`Axis` objects.
    """

    def __init__(self, COM_port=None, baudrate=115200, settings_filename=None):
        """Create a Xeryon controller object.

        Args:
            COM_port: The COM port to use (str), or None to auto-detect it
                (see :meth:`findCOMPort`).
            baudrate: The baudrate to use (int).
            settings_filename: The settings file to load for this
                controller (via :meth:`start`/:meth:`reset`), or None to
                fall back to the module-level SETTINGS_FILENAME. Useful
                when running multiple controllers that each need their
                own settings file -- see :meth:`readSettings`.
        """
        self.comm = Communication(self, COM_port, baudrate)
        self.axis_list = []
        self.axis_letter_list = []
        self.master_settings = {}
        self.settings_filename = settings_filename

    def isSingleAxisSystem(self):
        """Return True if this is a single-axis system, False otherwise."""
        return len(self.getAllAxis()) <= 1

    def start(self, external_communication_thread=False, external_settings_default=None):
        """Start the system. Must be called before any other command.

        Starts the serial communication, resets all axes, loads and sends
        the settings file, enables all axes and requests a few key
        settings back from the controller.

        Args:
            external_communication_thread: If True, don't spawn an internal
                thread; instead return the function that processes serial
                data so the caller can drive it from their own thread/loop.
            external_settings_default: Path to a settings file to use for
                this call specifically. If not given, falls back to
                ``self.settings_filename`` (see :meth:`__init__`), then to
                the module-level SETTINGS_FILENAME -- see
                :meth:`readSettings` for the full resolution order.

        Returns:
            The internal data-processing function if
            ``external_communication_thread`` is True, otherwise None.

        Raises:
            Exception: If no axes have been added yet via :meth:`addAxis`.
        """
        if len(self.getAllAxis()) <= 0:
            raise Exception(
                "Cannot start the system without stages. The stages don't "
                "have to be connected, only initialized in the software."
            )

        comm = self.getCommunication().start(external_communication_thread)

        # Reset all axes and give the controller time to come back up.
        for axis in self.getAllAxis():
            axis.reset()
        time.sleep(0.2)

        # Load the settings file and push it to the controller.
        self.readSettings(external_settings_default)
        if AUTO_SEND_SETTINGS:
            self.sendMasterSettings()
            for axis in self.getAllAxis():
                axis.sendSettings()

        for axis in self.getAllAxis():
            axis.sendCommand("ENBL=1")

        # Request a few settings back so the library's cache is in sync
        # with the controller.
        for axis in self.getAllAxis():
            axis.sendCommand("HLIM=?")
            axis.sendCommand("LLIM=?")
            axis.sendCommand("SSPD=?")
            axis.sendCommand("PTO2=?")
            axis.sendCommand("PTOL=?")
            if "XRTA" in str(axis.stage):
                axis.sendCommand("ENBL=3")

        if external_communication_thread:
            return comm

    def stop(self):
        """Stop all axes and close the serial communication."""
        for axis in self.getAllAxis():
            axis.sendCommand("ZERO=0")
            axis.sendCommand("STOP=0")
            time.sleep(0.001)
            axis.was_valid_DPOS = False

        self.getCommunication().closeCommunication()
        outputConsole("Program stopped running.")

    def stopMovements(self):
        """Stop all axes from moving, without closing the communication."""
        for axis in self.getAllAxis():
            axis.sendCommand("STOP=0")
            axis.was_valid_DPOS = False

    def reset(self):
        """Send RESET to the controller and resend all settings."""
        for axis in self.getAllAxis():
            axis.reset()
        time.sleep(0.2)

        self.readSettings()
        if AUTO_SEND_SETTINGS:
            for axis in self.getAllAxis():
                axis.sendSettings()

    def getAllAxis(self):
        """Return the list of all :class:`Axis` objects on this controller."""
        return self.axis_list

    def addAxis(self, stage, axis_letter):
        """Add an axis to the controller.

        Args:
            stage: The :class:`Stage` type of the connected stage.
            axis_letter: The letter identifying this axis (str).

        Returns:
            The newly created :class:`Axis` object.
        """
        newAxis = Axis(self, axis_letter, stage)
        self.axis_list.append(newAxis)
        self.axis_letter_list.append(axis_letter)
        return newAxis

    def getCommunication(self):
        """Return the :class:`Communication` object for this controller."""
        return self.comm

    def getAxis(self, letter):
        """Return the :class:`Axis` object for ``letter``, or None if it
        doesn't exist."""
        if self.axis_letter_list.count(letter) == 1:
            indx = self.axis_letter_list.index(letter)
            if len(self.getAllAxis()) > indx:
                return self.getAllAxis()[indx]
        return None

    def readSettings(self, external_settings_default=None):
        """Read the settings file and cache the settings on each axis.

        Each line is attributed to an axis (based on an "X:" prefix, or to
        all axes on a single-axis system), parsed as ``TAG=value`` and
        stored via :meth:`Axis.setSetting`. Lines for axes that don't exist
        are ignored. ``%`` starts a comment.

        The filename to load is resolved in this order:

        1. ``external_settings_default``, if given.
        2. ``self.settings_filename``, if set on this controller (see
           :meth:`__init__`) -- this is what lets each controller have
           its own settings file when running more than one.
        3. The module-level SETTINGS_FILENAME.

        Args:
            external_settings_default: Path to a settings file to use for
                this call specifically, overriding both of the above.

        Raises:
            FileNotFoundError: If the resolved filename was explicitly
                chosen (options 1 or 2 above) and doesn't exist. If it
                fell back to the module-level default (option 3), a
                missing file is silently ignored instead, since that
                default may simply not apply to every setup.
        """
        filename = external_settings_default or self.settings_filename or SETTINGS_FILENAME
        was_explicit = external_settings_default is not None or self.settings_filename is not None
        try:
            with open(filename, "r") as file:
                for line in file.readlines():
                    if "=" not in line or line.find("%") == 0:
                        continue

                    line = line.strip("\n\r").replace(" ", "")
                    axis = self.getAllAxis()[0]

                    if ":" in line:
                        axis = self.getAxis(line.split(":")[0])
                        if axis is None:
                            continue
                        line = line.split(":")[1]
                    elif not self.isSingleAxisSystem():
                        # No axis prefix on a multi-axis system: this is a
                        # setting for the controller as a whole.
                        if "%" in line:
                            line = line.split("%")[0]
                        self.setMasterSetting(line.split("=")[0], line.split("=")[1], True)
                        continue

                    if "%" in line:
                        line = line.split("%")[0]

                    tag, value = line.split("=")[0], line.split("=")[1]
                    axis.setSetting(tag, value, True, doNotSendThrough=True)
        except FileNotFoundError:
            if was_explicit:
                raise
            else:
                outputConsole("No settings_default.txt found.")

    def setMasterSetting(self, tag, value, fromSettingsFile=False):
        """Add/update a controller-wide (master) setting.

        Args:
            tag: The setting's tag.
            value: The setting's value.
            fromSettingsFile: True if this setting came from the settings
                file (in which case it isn't sent to the controller here).
        """
        self.master_settings.update({tag: value})
        if not fromSettingsFile:
            self.comm.sendCommand(str(tag) + "=" + str(value))
        if "COM" in tag:
            self.setCOMPort(str(value))
    
    def sendMasterSettings(self, axis=False):
        """Send all cached master (controller-wide) settings.

        Args:
            axis: If not False, prefix each command with the letter of the
                first axis (``"X:TAG=value"``); otherwise send unprefixed.
        """
        prefix = ""
        if axis is not False:
            prefix = str(self.getAllAxis()[0].getLetter()) + ":"

        for tag, value in self.master_settings.items():
            self.comm.sendCommand(str(prefix) + str(tag) + "=" + str(value))

    def saveMasterSettings(self, axis=False):
        """Send SAVE=0 to the controller, persisting settings to flash.

        Args:
            axis: If None, save unprefixed; otherwise prefix with the
                letter of the first axis.
        """
        if axis is None:
            self.comm.sendCommand("SAVE=0")
        else:
            self.comm.sendCommand(str(self.getAllAxis()[0].getLetter()) + ":SAVE=0")

    def setCOMPort(self, com_port):
        """Set the COM port used for the serial communication."""
        self.getCommunication().setCOMPort(com_port)

    def findCOMPort(self):
        """Scan the available COM ports for a Xeryon controller (USB VID
        0x04D8) and set it as the active COM port if found."""
        if OUTPUT_TO_CONSOLE:
            print(
                "Automatically searching for COM-Port. If you want to speed "
                "things up you should manually provide it inside the "
                "controller object."
            )
        for port in serial.tools.list_ports.comports():
            if "04D8" in str(port.hwid):
                self.setCOMPort(str(port.device))
                break


class Units(Enum):
    """Units an :class:`Axis` can report/accept positions and speeds in."""

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

    @staticmethod
    def getUnit(unit_str):
        """Return the :class:`Units` member whose name appears in
        ``unit_str``, or None if none matches."""
        for unit in Units:
            if unit.str_name in unit_str:
                return unit
        return None

class Axis:
    """Represents a single motorized axis on a Xeryon controller.

    All of the mutable per-axis state (settings cache, logs, running
    counters, ...) is created fresh in :meth:`__init__` so that separate
    ``Axis`` instances (as on a multi-axis XD-M controller) never
    accidentally share the same dict/list. Previously ``logs`` in
    particular was a class-level dict shared by every axis until
    :meth:`endLogging` first ran, which could mix logged samples from
    different axes together.
    """

    #: Class-level default; each instance gets its own copy in __init__.
    def_poli_value = str(DEFAULT_POLI_VALUE)

    def findIndex(self, forceWaiting=False, direction=0):
        """Find the encoder index and block until it's found.

        Args:
            forceWaiting: If True, wait for completion even if
                DISABLE_WAITING is set globally.
            direction: Direction to start searching the index in.

        Returns:
            True if the index was found, False if the controller stopped
            searching before finding it.
        """
        self.__sendCommand("INDX=" + str(direction))
        self.was_valid_DPOS = False

        if DISABLE_WAITING is False or forceWaiting is True:
            self.__waitForUpdate()
            self.__waitForUpdate()
            outputConsole("Searching index for axis " + str(self) + ".")

            # There can be a short delay between sending INDX and the
            # controller's STAT bits actually reflecting that the search
            # has started -- especially on a multi-axis system, where an
            # earlier axis's findIndex() call may return almost instantly
            # (e.g. because it hasn't started yet either) leaving little
            # real time for THIS axis's controller-side state to update
            # before we check it below. Without this, "not yet started"
            # and "already stopped without finding it" are indistinguishable,
            # and we'd report failure immediately while the stage is still
            # physically searching.
            start_wait_time = getActualTime()
            while not self.isSearchingIndex() and not self.isEncoderValid():
                if getActualTime() - start_wait_time > 3000:
                    outputConsole("Axis " + str(self) + ": index search did not start.", True)
                    return False
                time.sleep(0.05)

            while not self.isEncoderValid():
                if not self.isSearchingIndex():
                    outputConsole("Axis " + str(self) + ": index is not found, but stopped searching for index.", True)
                    return False
                time.sleep(0.2)

        if self.isEncoderValid():
            outputConsole("Index of axis " + str(self) + " found.")
            return True
        return False

    def move(self, value):
        """Send MOVE to the controller in the sign direction of ``value``
        (i.e. continuous jogging, not a move to an absolute position)."""
        value = int(value)
        direction = 0
        if value > 0:
            direction = 1
        elif value < 0:
            direction = -1
        self.sendCommand("MOVE=" + str(direction))

    def setDPOS(self, value, differentUnits=None, outputToConsole=True, forceWaiting=False):
        """Send a new desired position (DPOS) and, by default, block until
        it is reached.

        Args:
            value: The new DPOS value, in ``differentUnits`` or, if that's
                None, in the axis's current units.
            differentUnits: Units :class:`Units` member to interpret
                ``value`` in, if not the axis's current units.
            outputToConsole: If False, suppress the DPOS/EPOS console line
                for this call.
            forceWaiting: If True, wait for the position to be reached even
                if DISABLE_WAITING is set globally.

        Returns:
            True if the position was reached, False if an error condition
            (limit switch, error limit, safety/position timeout, thermal
            protection, or the overall move timeout) interrupted the move.
        """
        unit = differentUnits if differentUnits is not None else self.units
        DPOS = int(self.convertUnitsToEncoder(value, unit))

        self.__sendCommand("DPOS=" + str(DPOS))
        self.was_valid_DPOS = True

        # Block until EPOS is within tolerance of DPOS and the controller
        # reports "position reached" -- skipped in DEBUG_MODE/DISABLE_WAITING
        # unless forceWaiting is set.
        prefix = "Axis " + str(self) + ": "

        if (DEBUG_MODE is False and DISABLE_WAITING is False) or forceWaiting is True:
            start_time = getActualTime()
            start_epos = int(self.getData("EPOS") or 0)
            distance = abs(DPOS - start_epos)

            while not (self.__isWithinTol(DPOS) and self.isPositionReached()):
                if self.isAtLeftEnd() or self.isAtRightEnd():
                    outputConsole(prefix + "DPOS is out of range. (1) " + getDposEposString(value, self.getEPOS(), unit), True)
                    return False

                if self.isErrorLimit():
                    outputConsole(prefix + "Position not reached. (5) ELIM Triggered.", True)
                    return False

                if self.isSafetyTimeoutTriggered():
                    outputConsole(prefix + "Position not reached. (6) TOU2 (Timeout 2) triggered.", True)
                    return False

                if self.isPositionFailTriggered():
                    outputConsole(prefix + "Position not reached. (8) TOU3 (Timeout 3) triggered, 'position fail' status bit 21 went high.", True)
                    return False

                if self.isThermalProtection1() or self.isThermalProtection2():
                    outputConsole(prefix + "Position not reached. (7) amplifier error.", True)
                    return False

                if self.__timeOutReached(start_time, distance):
                    outputConsole(prefix + "Position not reached. (9) Timeout reached while waiting for DPOS.", True)
                    return False

                time.sleep(0.01)

        if outputToConsole and DISABLE_WAITING is False:
            outputConsole(prefix + getDposEposString(value, self.getEPOS(), unit))

        return True

    def setTRGS(self, value):
        """Send TRGS: the start position of the trigger pulses, in the
        axis's current units."""
        value_in_encoder_positions = int(self.convertUnitsToEncoder(value))
        self.sendCommand("TRGS=" + str(value_in_encoder_positions))

    def setTRGW(self, value):
        """Send TRGW: the width of the trigger pulses, in the axis's
        current units."""
        value_in_encoder_positions = int(self.convertUnitsToEncoder(value))
        self.sendCommand("TRGW=" + str(value_in_encoder_positions))

    def setTRGP(self, value):
        """Send TRGP: the pitch between trigger pulses, in the axis's
        current units."""
        value_in_encoder_positions = int(self.convertUnitsToEncoder(value))
        self.sendCommand("TRGP=" + str(value_in_encoder_positions))

    def setTRGN(self, value):
        """Send TRGN: the number of trigger pulses."""
        self.sendCommand("TRGN=" + str(int(value)))

    def getDPOS(self):
        """Return the desired position (DPOS), in the axis's current units."""
        return self.convertEncoderUnitsToUnits(self.getData("DPOS"), self.units)

    def getUnit(self):
        """Return the :class:`Units` this axis currently works in."""
        return self.units

    def step(self, value, forceWaiting=False):
        """Move by a relative amount, expressed in the axis's current units.

        Steps from DPOS if the last DPOS command was valid, otherwise from
        the current EPOS. On rotary stages the resulting position is
        wrapped into the [-180, 180) degree range (in encoder units).

        Args:
            value: The relative amount to step.
            forceWaiting: Passed through to :meth:`setDPOS`.

        Returns:
            True if the new position was reached, False otherwise (see
            :meth:`setDPOS`).
        """
        step = self.convertUnitsToEncoder(value, self.units)

        if self.was_valid_DPOS:
            new_DPOS = int(self.getData("DPOS")) + step
        else:
            new_DPOS = int(self.getData("EPOS")) + step

        if not self.stage.isLineair:
            encoderUnitsPerRevolution = self.convertUnitsToEncoder(360, Units.deg)
            new_DPOS = -encoderUnitsPerRevolution / 2 * (new_DPOS // (encoderUnitsPerRevolution / 2) % 2) \
                + (new_DPOS % (encoderUnitsPerRevolution / 2))

        success = self.setDPOS(new_DPOS, Units.enc, False, forceWaiting=forceWaiting)
        if DISABLE_WAITING is False:
            self.__waitForUpdate()  # Wait a couple of updates so EPOS is valid and doesn't lag behind.
            outputConsole(
                "Axis " + str(self) + ": stepped " + str(self.convertEncoderUnitsToUnits(step, self.units)) + " " + str(self.units)
                + " " + getDposEposString(self.getDPOS(), self.getEPOS(), self.units)
            )
        return success

    def getEPOS(self):
        """Return the encoder position (EPOS), in the axis's current units."""
        return self.convertEncoderUnitsToUnits(self.getData("EPOS"), self.units)

    def setUnits(self, units):
        """Set the :class:`Units` this axis should report/accept values in."""
        self.units = units

    def startLogging(self, increase_poli=True):
        """Start recording every incoming data field into ``self.logs``.

        Args:
            increase_poli: If True, temporarily raise the polling rate
                (POLI=1) on this axis and the first axis, to get more
                samples while logging.
        """
        self.isLogging = True
        if increase_poli:
            self.xeryon_object.getAllAxis()[0].setSetting("POLI", "1")
            self.setSetting("POLI", "1")
        self.__waitForUpdate()

    def endLogging(self, convertTimeAndEpos=False):
        """Stop logging, restore the default polling interval, and return
        the collected samples.

        Args:
            convertTimeAndEpos: If True, convert the raw "TIME" samples
                into cumulative milliseconds (handling the 16-bit
                controller timer wraparound) and "EPOS" samples into the
                axis's current units.

        Returns:
            A dict mapping each logged tag (e.g. "EPOS", "DPOS", "STAT",
            ...) to the list of values recorded for it.
        """
        self.isLogging = False
        logs = self.logs
        self.logs = {}

        if convertTimeAndEpos:
            timestamps = [0]
            for i in range(1, len(logs["TIME"])):
                t = logs["TIME"][i]
                if t < logs["TIME"][i - 1]:
                    t += 2 ** 16
                dT = (t - logs["TIME"][i - 1]) / 10
                timestamps.append(round(timestamps[-1] + dT, 2))

            logs["TIME"] = timestamps
            logs["EPOS"] = [self.convertEncoderUnitsToUnits(pos) for pos in logs["EPOS"]]

        self.setSetting("POLI", str(self.def_poli_value))
        self.xeryon_object.getAllAxis()[0].setSetting("POLI", str(self.def_poli_value))
        return logs

    def getFrequency(self):
        """Return the last known operating frequency (FREQ)."""
        return self.getData("FREQ")

    def setSetting(self, tag, value, fromSettingsFile=False, doNotSendThrough=False):
        """Cache a setting and (by default) send it to the controller.

        Args:
            tag: The setting's tag.
            value: The setting's value.
            fromSettingsFile: If True, run ``value`` through
                :meth:`applySettingMultipliers` first, and remap the
                "MASS" tag to "CFRQ".
            doNotSendThrough: If True, only update the local cache; don't
                send the command to the controller.
        """
        if fromSettingsFile:
            value = self.applySettingMultipliers(tag, value)
            if "MASS" in tag:
                tag = "CFRQ"
        if "?" not in str(value):
            self.settings.update({tag: value})
        if not doNotSendThrough:
            self.__sendCommand(str(tag) + "=" + str(value))
            time.sleep(0.001)

    def startScan(self, direction, execTime=None, untilLimit=False):
        """Start a continuous scan.

        Args:
            direction: Positive or negative number for the scan direction.
            execTime: If given, scan for this many seconds then send
                SCAN=0 to stop.
            untilLimit: If True, block until the corresponding software
                limit (left/right end) is hit.
        """
        self.__sendCommand("SCAN=" + str(int(direction)))
        self.was_valid_DPOS = False

        if execTime is not None:
            time.sleep(execTime)
            self.__sendCommand("SCAN=0")

        if untilLimit:
            self.__waitForUpdate()
            if int(direction) > 0:
                while not self.isAtRightEnd():
                    time.sleep(0.1)
            else:
                while not self.isAtLeftEnd():
                    time.sleep(0.1)

    def stopScan(self):
        """Stop a running scan (SCAN=0)."""
        self.__sendCommand("SCAN=0")
        self.was_valid_DPOS = False

    def setSpeed(self, speed):
        """Set the axis's speed (SSPD), given in the axis's current
        units per second."""
        if self.stage.isLineair:
            speed = int(self.convertEncoderUnitsToUnits(self.convertUnitsToEncoder(speed, self.units), Units.mu))
        else:
            speed = self.convertEncoderUnitsToUnits(self.convertUnitsToEncoder(speed, self.units), Units.deg)
            speed = int(speed) * 100
        self.setSetting("SSPD", str(speed))

    def getSetting(self, tag):
        """Return the cached value of the setting ``tag``, or None."""
        return self.settings.get(tag)

    def setPTOL(self, value):
        """Set PTOL (position tolerance 1), in encoder units."""
        self.setSetting("PTOL", value)

    def setPTO2(self, value):
        """Set PTO2 (position tolerance 2), in encoder units."""
        self.setSetting("PTO2", value)

    def sendCommand(self, command):
        """Send a raw ``"TAG=value"`` command to this axis.

        Commands in NOT_SETTING_COMMANDS are sent directly; anything else
        is treated (and cached) as a setting via :meth:`setSetting`.
        """
        tag = command.split("=")[0]
        value = str(command.split("=")[1])

        if tag in NOT_SETTING_COMMANDS:
            self.__sendCommand(command)
        else:
            self.setSetting(tag, value)

    def reset(self):
        """Send RSET=0 to reset this axis."""
        self.sendCommand("RSET=0")
        self.was_valid_DPOS = False

    # -- STAT status-bit helpers ------------------------------------------
    # Each of these reads a single bit out of the axis's cached STAT word
    # (or ``external_stat`` if given) via __getStatBitAtIndex(). See the
    # controller's manual for the full bit layout.

    def isAmplifiersEnabled(self, external_stat=None):
        """True if the "Amplifiers enabled" status bit is set."""
        return self.__getStatBitAtIndex(0, external_stat) == "1"

    def isEndStop(self, external_stat=None):
        """True if the "End stop" status bit is set."""
        return self.__getStatBitAtIndex(1, external_stat) == "1"

    def isThermalProtection1(self, external_stat=None):
        """True if the "Thermal protection 1" status bit is set."""
        return self.__getStatBitAtIndex(2, external_stat) == "1"

    def isThermalProtection2(self, external_stat=None):
        """True if the "Thermal protection 2" status bit is set."""
        return self.__getStatBitAtIndex(3, external_stat) == "1"

    def isForceZero(self, external_stat=None):
        """True if the "Force zero" status bit is set."""
        return self.__getStatBitAtIndex(4, external_stat) == "1"

    def isMotorOn(self, external_stat=None):
        """True if the "Motor on" status bit is set."""
        return self.__getStatBitAtIndex(5, external_stat) == "1"

    def isClosedLoop(self, external_stat=None):
        """True if the "Closed loop" status bit is set."""
        return self.__getStatBitAtIndex(6, external_stat) == "1"

    def isEncoderAtIndex(self, external_stat=None):
        """True if the "Encoder at index" status bit is set."""
        return self.__getStatBitAtIndex(7, external_stat) == "1"

    def isEncoderValid(self, external_stat=None):
        """True if the "Encoder valid" status bit is set."""
        return self.__getStatBitAtIndex(8, external_stat) == "1"

    def isSearchingIndex(self, external_stat=None):
        """True if the "Searching index" status bit is set."""
        return self.__getStatBitAtIndex(9, external_stat) == "1"

    def isPositionReached(self, external_stat=None):
        """True if the "Position reached" status bit is set."""
        return self.__getStatBitAtIndex(10, external_stat) == "1"

    def isErrorCompensation(self, external_stat=None):
        """True if the "Error compensation" status bit is set."""
        return self.__getStatBitAtIndex(11, external_stat) == "1"

    def isEncoderError(self, external_stat=None):
        """True if the "Encoder error" status bit is set."""
        return self.__getStatBitAtIndex(12, external_stat) == "1"

    def isScanning(self, external_stat=None):
        """True if the "Scanning" status bit is set."""
        return self.__getStatBitAtIndex(13, external_stat) == "1"

    def isAtLeftEnd(self, external_stat=None):
        """True if the "Left end stop" status bit is set."""
        return self.__getStatBitAtIndex(14, external_stat) == "1"

    def isAtRightEnd(self, external_stat=None):
        """True if the "Right end stop" status bit is set."""
        return self.__getStatBitAtIndex(15, external_stat) == "1"

    def isErrorLimit(self, external_stat=None):
        """True if the "Error limit" status bit is set."""
        return self.__getStatBitAtIndex(16, external_stat) == "1"

    def isSearchingOptimalFrequency(self, external_stat=None):
        """True if the "Searching optimal frequency" status bit is set."""
        return self.__getStatBitAtIndex(17, external_stat) == "1"

    def isSafetyTimeoutTriggered(self, external_stat=None):
        """True if the "Safety timeout triggered" (TOU2) status bit is set."""
        return self.__getStatBitAtIndex(18, external_stat) == "1"

    def isEtherCatAcknowledge(self, external_stat=None):
        """True if the "EtherCAT acknowledge" status bit is set."""
        return self.__getStatBitAtIndex(19, external_stat) == "1"

    def isEmergencyStop(self, external_stat=None):
        """True if the "Emergency stop" status bit is set. (Not used.)"""
        return self.__getStatBitAtIndex(20, external_stat) == "1"

    def isPositionFailTriggered(self, external_stat=None):
        """True if the "Position fail" (TOU3) status bit is set."""
        return self.__getStatBitAtIndex(21, external_stat) == "1"

    def getLetter(self):
        """Return this axis's letter (or "X" on a single-axis system)."""
        return self.axis_letter

    def applySettingMultipliers(self, tag, value):
        """Scale a raw settings-file value into what the controller expects.

        Several settings need a unit conversion or multiplier applied
        before they can be sent to the controller (amplitude/phase
        multipliers, speed multiplier, unit-to-encoder conversion for
        limits/zones, MASS -> CFRQ lookup, ...).

        Args:
            tag: The setting's tag.
            value: The raw value read from the settings file.

        Returns:
            The adjusted value, as a string.
        """
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

    def __init__(self, xeryon_object, axis_letter, stage):
        """Initialize an Axis object.

        Args:
            xeryon_object: The owning :class:`Xeryon` controller object.
            axis_letter: The letter identifying this axis (str).
            stage: The :class:`Stage` type used by this axis.
        """
        self.axis_letter = axis_letter
        self.xeryon_object = xeryon_object
        self.stage = stage
        self.axis_data = {"EPOS": 0, "DPOS": 0, "STAT": 0, "SSPD": 0, "TIME": 0}
        self.settings = {}
        self.units = Units.mm if self.stage.isLineair else Units.deg

        # All per-instance mutable state is created here (rather than as
        # class attributes) so that every Axis instance -- e.g. each axis
        # of a multi-axis XD-M controller -- gets its own independent
        # copy. In particular, ``logs`` used to be a single dict shared by
        # every Axis instance until the first call to endLogging(), which
        # could mix samples logged by different axes together.
        self.was_valid_DPOS = False  # If True, STEP takes DPOS as the reference (the microcontroller calls this "targeted_position=1/0").
        self.def_poli_value = str(DEFAULT_POLI_VALUE)
        self.isLogging = False  # Whether this axis is currently recording axis_data into self.logs.
        self.logs = {}  # {"EPOS": [...], "DPOS": [...], "STAT": [...], ...}
        self.update_nb = 0  # Incremented every time an update is received from the controller.
        self.previous_epos = [0, 0]  # Last two EPOS samples, used to estimate speed.
        self.previous_time = [0, 0]  # Last two TIME samples, used to estimate speed.

    def __massToCFREQ(self, mass):
        """Look up the CFRQ value corresponding to a MASS setting."""
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

    def __str__(self):
        return str(self.axis_letter)

    def __isWithinTol(self, DPOS):
        """Return True if the cached EPOS is within PTO2 (or PTOL, or a
        default of 10 encoder units) of ``DPOS``.

        Compares the *signed* distance between EPOS and DPOS. An earlier
        version of this check took abs(DPOS) and abs(EPOS) separately
        before comparing them, which meant a target of e.g. -4 mm was
        wrongly considered "already reached" the moment the stage was at
        +4 mm (same magnitude, opposite sign) -- causing setDPOS() to
        report success and log the *old* EPOS before the stage had moved
        at all.
        """
        DPOS = int(DPOS)
        if self.getSetting("PTO2") is not None:
            PTO2 = int(self.getSetting("PTO2"))
        elif self.getSetting("PTOL") is not None:
            PTO2 = int(self.getSetting("PTOL"))
        else:
            PTO2 = 10
        EPOS = int(self.getData("EPOS"))

        return abs(EPOS - DPOS) <= PTO2

    def __timeOutReached(self, start_time, distance):
        """Return True if more time has passed since ``start_time`` (in ms,
        see :func:`getActualTime`) than expected for the stage to travel
        ``distance`` encoder units, plus a 25% margin.

        If a TOUT setting is cached and implies a longer timeout (useful
        for quick, tiny movements where the speed-based estimate is
        inaccurate), that is used instead.

        Returns False -- i.e. "not timed out" -- if the SSPD setting isn't
        known yet or is zero, since the expected duration can't be
        computed in that case.
        """
        speed_setting = self.getSetting("SSPD")
        if speed_setting is None:
            return False
        try:
            speed = int(speed_setting)
        except (TypeError, ValueError):
            return False
        if speed == 0:
            return False

        timeout_t = (distance / speed * 1000) * 1.25

        tout_setting = self.getSetting("TOUT")
        if tout_setting is not None:
            TOUT = int(tout_setting) * 3
            if TOUT > timeout_t:
                timeout_t = TOUT

        return (getActualTime() - start_time) > timeout_t

    def receiveData(self, data):
        """Process one ``"TAG=value"`` line received from the controller.

        Updates the settings cache or axis_data as appropriate, raises
        console warnings on thermal/error/timeout status bits (and
        optionally auto-sends ENBL=1, see AUTO_SEND_ENBL), tracks EPOS/TIME
        samples to estimate speed, and appends to ``self.logs`` while
        logging is active.

        Args:
            data: One line of data from the controller, e.g. "EPOS=12345".
        """
        if "=" not in data:
            return

        tag = data.split("=")[0]
        val = data.split("=")[1].rstrip("\n\r").replace(" ", "")

        if not is_numeric(val):
            return

        if tag not in NOT_SETTING_COMMANDS and "EPOS" not in tag and "DPOS" not in tag:
            self.setSetting(tag, val, doNotSendThrough=True)
        else:
            self.axis_data[tag] = val

        if "STAT" in tag:
            prefix = "Axis " + str(self) + ": "

            if self.isSafetyTimeoutTriggered():
                outputConsole(
                    prefix + "the safety timeout was triggered (TOU2 command). This means "
                    "that the stage kept moving and oscillating around the desired "
                    "position. A reset is required now OR 'ENBL=1' should be sent.",
                    True,
                )

            if self.isPositionFailTriggered():
                outputConsole(prefix + "safety timeout TOU3 went off, the 'position fail' status bit went high.")

            if self.isThermalProtection1() or self.isThermalProtection2() or self.isErrorLimit() or self.isSafetyTimeoutTriggered():
                if self.isErrorLimit():
                    outputConsole(prefix + "error limit is reached (status bit 16). A reset is required now OR 'ENBL=1' should be sent.", True)

                if self.isThermalProtection2() or self.isThermalProtection1():
                    outputConsole(prefix + "thermal protection 1 or 2 is raised (status bit 2 or 3). A reset is required now OR 'ENBL=1' should be sent.", True)

                if self.isSafetyTimeoutTriggered():
                    outputConsole(prefix + "safety timeout (TOU2 timeout reached) triggered. A reset is required now OR 'ENBL=1' should be sent.", True)

                if AUTO_SEND_ENBL:
                    self.xeryon_object.setMasterSetting("ENBL", "1")
                    outputConsole(prefix + "'ENBL=1' is automatically sent.")

        if "EPOS" in tag:
            self.previous_epos = [self.previous_epos[-1], int(val)]
            self.update_nb += 1

        if self.isLogging and tag not in ["SRNO", "XLS ", "XRTU", "XLA ", "XTRA", "SOFT", "SYNC"]:
            self.logs.setdefault(tag, []).append(int(val))

        if "TIME" in tag:
            self.previous_time = [self.previous_time[-1], int(val)]
            t1 = self.previous_time[0]
            t2 = int(val)
            if t2 < t1:
                t2 += 2 ** 16

            if len(self.previous_epos) >= 2 and t2 - t1 > 0:
                self.axis_data["SSPD"] = (self.previous_epos[1] - self.previous_epos[0]) / ((t2 - t1) * 10)
                if self.isLogging:
                    self.logs.setdefault("SSPD", []).append(self.axis_data["SSPD"])

    def getData(self, TAG):
        """Return the cached value of ``TAG`` (e.g. "DPOS", "EPOS", "STAT"),
        or None if nothing has been received for it yet."""
        return self.axis_data.get(TAG)

    def sendSettings(self):
        """Send the stage's encoder-resolution command and every cached
        setting to the controller."""
        self.__sendCommand(str(self.stage.encoderResolutionCommand))
        for tag in self.settings:
            self.__sendCommand(str(tag) + "=" + str(self.getSetting(tag)))

    def saveSettings(self):
        """Send SAVE=0, persisting the current settings to flash."""
        self.sendCommand("SAVE=0")

    def convertUnitsToEncoder(self, value, units=None):
        """Convert ``value`` from ``units`` (or the axis's current units,
        if not given) into encoder units.

        Raises:
            ValueError: If ``units`` isn't a recognized :class:`Units`
                member. The controller is stopped first as a safety
                precaution.
        """
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
            raise ValueError("Unexpected unit: " + str(units))

    def convertEncoderUnitsToUnits(self, value, units=None):
        """Convert ``value`` from encoder units into ``units`` (or the
        axis's current units, if not given).

        Raises:
            ValueError: If ``units`` isn't a recognized :class:`Units`
                member. The controller is stopped first as a safety
                precaution.
        """
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
            raise ValueError("Unexpected unit: " + str(units))

    def __sendCommand(self, command):
        """Send a raw ``"TAG=value"`` command to the controller for this
        axis, automatically prefixing it with the axis letter (``"X:"``)
        on multi-axis systems. Do NOT include the axis prefix yourself."""
        tag = command.split("=")[0]
        value = str(command.split("=")[1])

        prefix = ""
        if not self.xeryon_object.isSingleAxisSystem():
            prefix = self.axis_letter + ":"

        command = tag + "=" + str(value)
        self.xeryon_object.getCommunication().sendCommand(prefix + command)

    def __waitForUpdate(self):
        """Block until a few new updates (scaled by the current POLI
        setting) have been received for this axis."""
        wait_nb = 3

        if self.getSetting("POLI") is not None:
            wait_nb = wait_nb / int(self.def_poli_value) * int(self.getSetting("POLI"))

        start_nb = int(self.update_nb)
        while (int(self.update_nb) - start_nb) < wait_nb:
            time.sleep(0.01)

    def __getStatBitAtIndex(self, bit_index, external_stat=None):
        """Return the status bit at ``bit_index`` ("0" or "1") from the
        cached STAT word, or from ``external_stat`` if given. Returns None
        if no STAT value is known yet or the bit is out of range (which
        compares equal to False against the "is*" checks that use it)."""
        stat = self.getData("STAT") if external_stat is None else external_stat

        if stat is not None:
            bits = bin(int(stat)).replace("0b", "")[::-1]
            if len(bits) >= bit_index + 1:
                return bits[bit_index]
        return "0"

class Communication:
    """Handles the serial communication with the controller.

    Outgoing commands are queued in ``readyToSend`` and written to the
    serial port by a background thread (or by an externally-driven loop,
    see :meth:`start`), which also reads and dispatches incoming data.
    Access to ``readyToSend`` is guarded by a lock: without it, a command
    appended by the main thread at the exact moment the background thread
    was rotating its send-queue could silently be dropped instead of sent.
    """

    def __init__(self, xeryon_object, COM_port, baud):
        """Create a Communication object.

        Args:
            xeryon_object: The owning :class:`Xeryon` controller object.
            COM_port: The COM port to use, or None to auto-detect it.
            baud: The baudrate to use.
        """
        self.xeryon_object = xeryon_object
        self.COM_port = COM_port
        self.baud = baud
        self.readyToSend = []
        self._lock = threading.Lock()
        self.stop_thread = False
        self.thread = None
        self.ser = None

    def start(self, external_communication_thread=False):
        """Open the serial port and start processing data.

        Args:
            external_communication_thread: If True, don't spawn a thread;
                instead return the data-processing function so the caller
                can drive it themselves.

        Returns:
            The data-processing function if
            ``external_communication_thread`` is True, otherwise None.

        Raises:
            Exception: If no COM port is known/found, or the port
                couldn't be opened.
        """
        if self.COM_port is None:
            self.xeryon_object.findCOMPort()
        if self.COM_port is None:
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
            outputConsole("An error occurred while trying to connect to COM: " + str(self.COM_port), True)
            outputConsole(str(e), True)
            raise Exception("Could not connect to COM " + str(self.COM_port))

    def sendCommand(self, command):
        """Queue ``command`` to be written to the serial port by the
        background thread. Thread-safe."""
        with self._lock:
            self.readyToSend.append(command)

    def setCOMPort(self, com_port):
        """Set the COM port to use."""
        self.COM_port = com_port

    def __processData(self, external_while_loop=False):
        """Main loop of the communication thread.

        Writes up to 10 queued commands to the serial port, then reads and
        dispatches up to 10 incoming lines to the right :class:`Axis`
        (based on an "X:" prefix, or the first axis if there is none/it
        doesn't match a known letter). Runs until :meth:`closeCommunication`
        is called (or, with ``external_while_loop``, only a single
        iteration is run so the caller can drive the loop itself).
        """
        try:
            while self.stop_thread is False and self.ser.is_open:
                with self._lock:
                    dataToSend = self.readyToSend[:10]
                    del self.readyToSend[:10]

                for command in dataToSend:
                    self.ser.write(str.encode(command.rstrip("\n\r") + "\n"))

                max_to_read = 10
                try:
                    while self.ser.in_waiting > 0 and max_to_read > 0:
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
                    print(getTimestampPrefix() + str(e))

                if external_while_loop is True:
                    return None

            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.close()
            print(getTimestampPrefix() + "Communication has stopped.")
        except Exception as e:
            print(getTimestampPrefix() + "An error has occurred that crashed the communication thread.")
            print(getTimestampPrefix() + str(e))
            raise OSError("An error has occurred that crashed the communication thread. \n" + str(e))

    def closeCommunication(self):
        """Signal the communication thread to stop and close the port."""
        self.stop_thread = True

class Stage(Enum):
    """Supported stage types.

    Each member's value is a ``(isLineair, encoderResolutionCommand,
    encoderResolution, speedMultiplier)`` tuple:

    - isLineair: True for linear stages, False for rotary stages.
    - encoderResolutionCommand: The command that sets the encoder
      resolution on the controller for this stage.
    - encoderResolution: The encoder resolution, in nanometer (linear
      stages) or microradian (rotary stages).
    - speedMultiplier: The multiplier applied to speed settings.
    """

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

    @staticmethod
    def getStage(stage_command):
        """Return the :class:`Stage` member whose encoderResolutionCommand
        contains ``stage_command`` (e.g. "XLS1=312"), or None if none
        matches."""
        for stage in Stage:
            if stage_command in str(stage.encoderResolutionCommand).replace(" ", ""):
                return stage
        return None

def getActualTime():
    """Return the current time in milliseconds (int)."""
    return int(round(time.time() * 1000))


def getDposEposString(DPOS, EPOS, Unit):
    """Return a "DPOS: .. <unit> and EPOS: .. <unit>" string for logging."""
    return "DPOS: " + str(DPOS) + " " + str(Unit) + " and EPOS: " + str(EPOS) + " " + str(Unit)


def getTimestampPrefix():
    """Return a "[YYYY-MM-DD HH:MM:SS.mmm] " string for the current
    wall-clock time, or "" if OUTPUT_CONSOLE_TIMESTAMPS is False."""
    if not OUTPUT_CONSOLE_TIMESTAMPS:
        return ""
    now = time.time()
    millis = int(now * 1000) % 1000
    return "[" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)) + "." + f"{millis:03d}" + "] "


def outputConsole(message, error=False):
    """Print ``message`` to the console if OUTPUT_TO_CONSOLE is True.

    Prefixed with a "[YYYY-MM-DD HH:MM:SS.mmm]" timestamp unless
    OUTPUT_CONSOLE_TIMESTAMPS is set to False.

    Args:
        message: The text to print.
        error: If True, print in red with an "ERROR: " prefix.
    """
    if OUTPUT_TO_CONSOLE is True:
        prefix = getTimestampPrefix()
        if error is True:
            print("\033[91m" + prefix + "ERROR: " + message + "\033[0m")
        else:
            print(prefix + message)


def is_numeric(value):
    """Return True if ``value`` can be parsed as a number (int or float).

    NOTE: this accepts float-looking strings like "3.14", unlike a naive
    ``int(value)`` check would.
    """
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False