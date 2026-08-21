# Xeryon EtherCAT Slave — Full State Lifecycle (TwinCAT Master)

**Source captures:**
- `scan_one_slave_270726.pcapng` — idle network + device scan + Init → PreOp
- `scan_one_slave_preop_to_op_270726.pcapng` — PreOp → SafeOp → Op + steady-state cyclic exchange

**Slave:** single Xeryon EtherCAT slave, no CoE/DS402 mailbox, proprietary PDO structure.
**Fixed station address assigned during scan:** `0x03E9` (1001 decimal).

---

## Phase 0 — Idle

The first ~37 s of the scan capture is background LAN traffic (SSDP, mDNS, DHCPv6) captured before the TwinCAT scan was triggered. No EtherCAT activity in this window.

---

## Phase 1 — Init: reset & port configuration (broadcast)

t ≈ 37.17 s. All commands are broadcast (`BWR`/`BRD`, ADP 0x0000, WC confirms exactly 1 slave present):

| Register | Command | Value | Meaning |
|---|---|---|---|
| 0x0101 (DL Control) | BWR | `0x00` | All 4 ports → Auto Loop |
| 0x0130 (AL Status) | BRD | `0x0001` | INIT confirmed, error = false |
| 0x0200 (ECAT IRQ Mask) | BWR | `0x0004` | Enable ESC Status Event interrupt |
| 0x0010 (Station Alias) | BWR | `0x0000` | Cleared — still position-addressed |
| 0x0300–0x0307 (CRC/RX error counters) | BWR | all `0x00` | Cleared on all 4 ports |
| 0x0600, 256 B (all 16 FMMU entries) | BWR | all zero | FMMU table cleared/deactivated |
| 0x0800, 256 B (all 8 Sync Managers) | BWR | all zero | SM table cleared/disabled |
| 0x0910, 32 B (DC System Time, Receive Time, Offset, Delay, Ctrl Error) | BWR | all zero | DC state cleared |
| 0x0981 (DC Activation) | BWR | `0x00` | Sync0/Sync1 off |
| 0x0930 (DC Speed Counter Start) | BWR | `0x1000` | DC speed-counter seed |
| 0x0934/0x0935 (DC filter depths) | BWR | `0x00` / `0x0c` | Sys-time-diff filter = 0, speed-counter filter = 12 |
| 0x0103 (DL Control byte 3) | BWR | `0x00` | Reserved/PDI bits |

This is a clean-slate reset applied to every slave found — nothing device-specific yet.

---

## Phase 2 — Init: identification (position-addressed)

- `APRD 0x0000` — Type register read
- EEPROM identification via `APWR 0x0502` (set word address) + `APRD 0x0508` (read data word):

| EEPROM word address | Value read | Field |
|---|---|---|
| 0x0008 | `0x004E` | Vendor ID (low word) |
| 0x000A | `0x0001` | Product Code (low word) |
| 0x000C | `0x0001` | Revision Number (low word) |
| 0x000E | (read once, first pass) | Serial Number (low word) |

TwinCAT uses this to match the slave against its known device/ESI database.

---

## Phase 3 — Init: fixed address assignment

`APWR 0x0010 = 0x03E9` — station address 1001 assigned. From this point on, the slave is addressed with `FPRD`/`FPWR` to `0x03E9` instead of positional addressing.

---

## Phase 4 — Init → PreOp request (retried 3×)

Each of 3 passes repeats broadcast reset → EEPROM ID → address assignment, then:

1. `APWR AL Control = 0x0001` (Init request, broadcast/position)
2. `FPWR AL Control = 0x0002` (PreOp request, fixed address 0x03E9)
3. `FPRD AL Status` polled after each write

On the 3rd pass (t ≈ 37.91 s), AL Status finally reads back `0x0002` (PreOp), AL Status Code `0x0000` (no error), and stays there — no further AL Control writes follow.

> No AL Status Code error was ever set during any pass. The 3 repeats look like TwinCAT's conservative re-verification behavior, not a fault.

---

## Phase 5 — PreOp steady state

From t ≈ 37.91 s to the end of capture 1, and continuing into the start of capture 2:

- `FPRD 0x0130` (AL Status) and `FPRD 0x0300` (watchdog/CRC counters) polled every ~100 ms
- AL Status stays `0x0002` (PreOp), error = false throughout

---

## Phase 6 — PreOp → SafeOp: mailbox & process-data setup

t ≈ 1.35–1.37 s in capture 2.

**Sync Managers** (`FPWR`, 8 bytes each, fixed address 0x03E9):

| SM | Register | Start | Length | Access | Watchdog | Enable |
|---|---|---|---|---|---|---|
| SM0 (mailbox out) | 0x0800 | — | — | — | — | **Disabled** (all zero — no CoE mailbox on this slave) |
| SM1 (mailbox in) | 0x0808 | — | — | — | — | **Disabled** (all zero) |
| SM2 (outputs) | 0x0810 | `0x1000` | 20 B | Write | **Enabled** | True |
| SM3 (inputs) | 0x0818 | `0x1200` | 8 B | Read | Off | True |

**FMMUs** (`FPWR`, 16 bytes each):

| FMMU | Register | Logical Start | Length | Phys Start | Type | Active |
|---|---|---|---|---|---|---|
| FMMU0 (outputs) | 0x0600 | `0x01000000` | 20 B | `0x1000` | Write | Yes |
| FMMU1 (inputs) | 0x0610 | `0x01000000` | 8 B | `0x1200` | Read | Yes |

Both FMMUs share the same logical start address because the slave is exchanged with a single combined `LRW` datagram (read + write in one pass) rather than separate `LRD`/`LWR` commands — the write half lands on FMMU0/phys 0x1000, the read half on FMMU1/phys 0x1200, both within the same 20-byte logical window.

This device has no mailbox channel at all — SM0/SM1 stay disabled for the device's entire life. All communication runs through the two process-data Sync Managers (SM2 outputs / SM3 inputs) and their FMMUs. Only SM2 (outputs) has the local watchdog-trigger bit set — protecting against a stale/missing write from the master by falling back safely on the slave side.

---

## Phase 7 — SafeOp request/confirm + cyclic start

| Time | Event |
|---|---|
| t = 1.3675 s | `FPWR AL Control = 0x0004` (SafeOp requested) |
| t = 1.3715 s | `FPRD AL Status = 0x0004`, error = false — confirmed in ~4 ms |

The instant SafeOp is confirmed, cyclic `LRW` datagrams (20-byte logical read-write) begin, each frame also carrying a piggy-backed `BRD 0x0130` AL Status check.

---

## Phase 8 — Op request/confirm

| Time | Event |
|---|---|
| t = 1.3725 s | `FPWR AL Control = 0x0008` (Op requested) — one cycle after SafeOp confirmed |
| t = 1.3764 s | `FPRD AL Status = 0x0008`, error = false — confirmed in ~4 ms |

---

## Phase 9 — Operational steady state

- 2350 cyclic `LRW` exchanges over the remainder of the capture
- **Working counter = 3 on every single cycle** — zero drops, zero WC mismatches
- Average cycle period ≈ **2.04 ms**
- AL Status checked every cycle, stays `0x0008` (Op) throughout, error = false

---

## Summary

| Milestone | Outcome |
|---|---|
| Slaves found | 1 (confirmed via WC and ADP auto-increment on broadcast) |
| Fixed address | 0x03E9 |
| Mailbox (CoE) | Not present — SM0/SM1 disabled for life of device |
| Process data | SM2 (out, 20 B, watchdog-guarded) / SM3 (in, 8 B) via FMMU0/FMMU1 |
| Init → PreOp | 3 conservative retries, ~4.7 s wall clock (no errors) |
| PreOp → SafeOp → Op | < 10 ms once mailbox/SM/FMMU were configured |
| Cyclic exchange | 2350 cycles, WC = 3 throughout, ~2.04 ms period, zero faults |

No error codes or working-counter faults were observed anywhere across either capture.
