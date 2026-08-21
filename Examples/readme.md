# Examples — XD-OEM Motor Controller

This folder contains example code and projects for controlling an **XD-OEM motor controller**, organized by language/platform:

| Folder | Language/Platform | Description |
|--------|--------------------|-------------|
| [`Python/`](Python/readme.md) | Python | USB (library) example for controlling the XD-OEM, using the `Xeryon.py` library. |
| [`CPP/`](CPP/readme.md) | C++ | USB (library) example for controlling the XD-OEM, using a cross-platform C++ SDK. |
| [`EtherCAT/`](EtherCAT/readme.md) | EtherCAT | A TwinCAT 3 project controlling one or more XD-OEM drives directly over EtherCAT. |
| [`LabVIEW/`](LabVIEW/readme.md) | LabVIEW | A full LabVIEW project (axis driver, sequencer, preferences) for controlling one or more XD-OEM axes from a LabVIEW application. |

> [!NOTE]
> All folders control the same XD-OEM controller, but use different languages and, in some cases, different physical interfaces (USB, EtherCAT). See the readme inside each folder for setup and usage details before running anything.

## Which one do I need?

- Using Python on a PC → see [`Python/readme.md`](Python/readme.md).
- Using C++ on a PC → see [`CPP/readme.md`](CPP/readme.md).
- Controlling the drive directly over an EtherCAT network → see [`EtherCAT/readme.md`](EtherCAT/readme.md).
- Using LabVIEW → see [`LabVIEW/readme.md`](LabVIEW/readme.md).
