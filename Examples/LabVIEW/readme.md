# LabVIEW Examples — XD-OEM Motor Controller

Xeryon's LabVIEW library handles all communication between the computer and an **XD-OEM** controller, and exposes simple functions to control the connected stage. It's compact and easy to use.

## Getting started

1. Open [`Xeryon Example project.lvproj`](Xeryon%20Example%20project.lvproj) in LabVIEW.
2. Make sure the device tuning file for your stage is in place under [`Preferences/`](Preferences/) — see [First-time use](#first-time-use) below. The files included here are tuned for the stages this example was built with, not blank samples, so swap in the file matching your own stage before running.
3. Open [`Static single axis example.vi`](Static%20single%20axis%20example.vi) — it handles both linear and rotating stages.
4. Before running, fill in the **Configuration** tab:
   - COM port and baud rate.
   - The stage's axis letter (use `X` for a single stage).
   - The stage's resolution and the working units you want it to use — linear and rotating stages differ here.
5. Run the VI, then press **Find Index** so the stage can find its reference position and establish an absolute position. After that, you can move the stage with its own controls.

## First-time use

The tuning files included under `Preferences/` match the demo stages this example was built with — swap them for your own stage(s) before controlling real hardware:

1. Get the `settings_default.txt` file provided with the Windows Interface for your stage.
2. Copy it into `Preferences/`, replacing the file for the example you're using (see [Preferences files](#preferences-files) below).
3. Open it and, on any line containing `%`, remove the `%` and everything after it on that line.
4. Find every line containing `MSPD` or `SSPD` and multiply its value by:
   - **1000** for a linear stage
   - **100** for a rotating stage

## Project structure

| Folder | Contents |
|--------|----------|
| [`Axis driver/`](Axis%20driver/) | Low-level VIs implementing the per-axis command protocol — sending/receiving commands, status bits, unit conversion. |
| [`Axis Manager/`](Axis%20Manager/) | VIs for reading axis configuration and managing/enumerating the configured axes. |
| [`Serial driver/`](Serial%20driver/) | VIs handling the underlying COM/serial transport. |
| [`Sequencer/`](Sequencer/) | The sequencer VI — intended as the main program once your axes are configured. |
| [`Preferences/`](Preferences/) | Saved Configuration-tab settings and per-stage device tuning files, read by the examples above. |

## Preferences files

| File | Purpose |
|------|---------|
| [`COM-port.txt`](Preferences/COM-port.txt) | Last-used COM port. |
| [`config.txt`](Preferences/config.txt) | Saved Configuration-tab settings — axis letter, stage/resolution code, and working range. |
| [`Single axis linear.txt`](Preferences/Single%20axis%20linear.txt) | Device tuning file (`settings_default.txt` equivalent) for a linear stage. |
| [`Single axis rotary.txt`](Preferences/Single%20axis%20rotary.txt) | Device tuning file for a rotary stage. |

## Requirements

- LabVIEW (version compatible with `Xeryon Example project.lvproj`)
- An XD-OEM controller connected over a COM (serial) port

> [!TIP]
> If you're looking for the same examples in Python or C++, see [`../Python/readme.md`](../Python/readme.md) or [`../CPP/readme.md`](../CPP/readme.md).
