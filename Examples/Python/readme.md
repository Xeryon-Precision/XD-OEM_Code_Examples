# Python Examples — XD-OEM Motor Controller

This folder contains Python examples for controlling an **XD-OEM motor controller**.

| Folder | Approach | Description |
|--------|----------|-------------|
| [`USB/`](USB/readme.md) | USB (library) | Example using the `Xeryon.py` library over USB (COM port) — connect, add axes, home, move, log, and plot motion data. |

> [!NOTE]
> See [`USB/readme.md`](USB/readme.md) for full setup and usage details before running anything.

## Requirements

- Python installed on the computer
- `Xeryon.py` library (included in `USB/`)
- `pyserial` and `matplotlib` — see [`USB/readme.md`](USB/readme.md) for install commands
- The `settings_default.txt` file provided with the Windows Interface for your stage(s) — the one included is only a sample
