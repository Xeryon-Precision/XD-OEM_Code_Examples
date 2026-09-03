# Scripts

Python scripts for driving Xeryon XD-OEM stages over EtherCAT through a Beckhoff
TwinCAT PLC, using [pyads](https://pypi.org/project/pyads/) (ADS) to talk to the
PLC symbols exposed by the accompanying TwinCAT project (see `../Demo`).

## Files

| File | Description |
|---|---|
| `Xeryon_EtherCAT.py` | The Xeryon control library. Wraps the PLC's `MAIN.DriveX` symbols (position, speed, status bits, ...) in a Python API: `Xeryon`, `Communication`, `Axis`, `Units`, `Stage`. |
| `Example.py` | Example script showing how to configure one or more drives/axes, home them, run scans and moves in parallel threads, read status bits, and log/plot position data. |

## Requirements

- Python 3
- [`pyads`](https://pypi.org/project/pyads/)
- [`matplotlib`](https://pypi.org/project/matplotlib/) (only needed for `Example.py`'s logging/plotting)
- A running TwinCAT PLC (local or remote) with the ADS route configured, running
  the project in `../Demo` and reachable via its AMS Net Id.

Install the Python dependencies:

```bash
pip install pyads matplotlib
```

## Quick start

1. Make sure the TwinCAT project is running on the target PLC and an ADS route
   to it exists (for a local PLC this is normally already the case).
2. Edit the `DRIVE_CONFIG` list at the top of `Example.py` to match your setup:

   ```python
   DRIVE_CONFIG = [
       ('127.0.0.1.1.1', pyads.PORT_TC3PLC1, "MAIN.Drive1", Stage.XLA_78),
       ('127.0.0.1.1.1', pyads.PORT_TC3PLC1, "MAIN.Drive2", Stage.XLA_312),
   ]
   ```

   Each tuple is `(net_id, port, drive_base, stage)`:
   - `net_id` / `port` — the AMS Net Id and ADS port of the PLC. Drives on the
     **same** PLC/TwinCAT project share the same `net_id`/`port` and are
     distinguished only by `drive_base` (e.g. `MAIN.Drive1`, `MAIN.Drive2`, ...).
     Drives on a physically separate PLC need a different `net_id`/`port`.
   - `drive_base` — the PLC symbol prefix for that EtherCAT slave, matching the
     `MAIN.DriveX` struct in the TwinCAT project.
   - `stage` — the connected stage type, from the `Stage` enum in `Xeryon_EtherCAT.py`.

3. Run the script:

   ```bash
   python Example.py
   ```

Each configured axis runs its full command sequence (index search, scans,
absolute/relative moves, stepping) in its own thread so multiple stages move
concurrently. Status bits are printed per axis, and (if logging captured data)
an `EPOS` plot is shown per axis at the end.

## Using `Xeryon_EtherCAT.py` in your own script

```python
from Xeryon_EtherCAT import *

controller = Xeryon('127.0.0.1.1.1', pyads.PORT_TC3PLC1, drive_base="MAIN.Drive1")
axis = controller.addAxis(Stage.XLA_78)

controller.start()          # opens the ADS connection, resets and enables the axis
axis.setUnits(Units.mm)

axis.findIndex(0, 100000, 65000, 65000)
axis.setDPOS(10, 500000, 65000, 65000)

controller.stop()
```

Key `Axis` methods:

- `findIndex(direction, speed, acc, decc)` — home the axis; blocks until the
  index is found (or fails).
- `setDPOS(position, speed, acc, decc)` — move to an absolute position and
  wait until it's reached.
- `step(value, speed, acc, decc)` — move by a relative amount.
- `startScan(direction, speed, acc, decc)` / `stopScan()` — continuous motion.
- `setUnits(units)` — switch working units (`Units.mm`, `Units.mu`, `Units.nm`, ...).
- `startLogging()` / `endLogging()` — capture position data over time for
  plotting/analysis.
- `isAmplifiersEnabled()`, `isEndStop()`, `isPositionReached()`, ... — read the
  drive's status bits.

To drive multiple slaves in parallel (as `Example.py` does), create one
`Xeryon` instance per drive with a distinct `drive_base` (and `net_id`/`port`
if on a different PLC), and run each axis's command sequence in its own
thread — most `Axis` calls block the calling thread until the motion
completes.

## Notes

- `DEBUG_MODE`, `OUTPUT_TO_CONSOLE`, `DISABLE_WAITING`, `AUTO_SEND_SETTINGS`
  and `AUTO_SEND_ENBL` at the top of `Xeryon_EtherCAT.py` are global switches that
  control console logging verbosity, whether blocking calls actually wait for
  the controller, and automatic settings/enable behavior on start/reset.
- `__pycache__/` contains compiled bytecode and is not part of the source.
