# Hardware Died: Which Device?

If you scanned a QR code stuck to a specific device, you probably want that device's
page directly — use the menu on the left, or the list below.

## First, two things to check before anything else

1. **Is it really dead, or is something upstream just unreachable?** A relay board
   that "isn't responding" might be fine — the real fault could be the shared RS485
   bus, a loose connector, or a power issue. Before swapping any board, do a quick
   triage: is the device powered (LED on, if it has one)? Are its wires seated? Is
   *only* this device affected, or is everything on its bus acting up (in which case
   see [Troubleshooting](../troubleshooting/rs485-modbus.md) or
   [CAN bus troubleshooting](../troubleshooting/canbus.md) first — you may not need
   to replace anything)?
2. **The golden rule, before you touch a reflash tool**: several devices in this
   house get their identity (which room, which node number) from a file in this
   repository, `registry/nodes.csv`. Git is the *only* backup of that data. If you've
   just edited the registry (adding a room, re-registering a swapped node), **push
   your commit and confirm it with `python3 canbus/tools/check_registry_pushed.py`
   before reflashing anything** — that command must print success (exit code 0). A
   registry change that's only on your laptop, reflashed to a device, is described
   elsewhere in this project as "an unbacked-up house." 🟢 This discipline is
   documented and load-bearing, not optional.

## Which page do you need?

| Symptom | Go to |
|---|---|
| A wall button or a room sensor stopped responding | [CAN Node](can-node.md) |
| One whole section of the house (a floor, a wing) stopped hearing CAN traffic | [CAN Bridge](bridge.md) |
| The "Nodes Missing" count is stuck high but everything otherwise works, or the health-monitor device itself looks offline in Home Assistant | [Health Monitor](health-monitor.md) |
| Climate control isn't actuating anything at all, or lighting isn't responding at all | [Controller (T-Connect Pro)](controller.md) |
| Relays aren't switching (pumps, valves, lighting circuits) but the controller itself seems fine | [Relay Board](relay-board.md) |
| Fancoils/mixing valves are stuck, 0-10V outputs aren't responding | [Analog Output Board](analog-board.md) |
| Ventilation (MEV) isn't responding | [MEV Unit](mev.md) |
| One room's temperature/humidity/air-quality reading looks frozen or clearly wrong | [Room Sensor Board](room-sensor.md) |

Still not sure? Start with [Everyday Monitoring](../monitoring.md) to check the
system's diagnostic entities — they usually point at the right device.

!!! note "Confidence tags used throughout this section"
    🟢 **VERIFIED** — confirmed by testing on real hardware.
    🔵 **DESIGNED** — built and expected to work this way, but not yet exercised
    against a real failure (true for most of this pre-live house).
    ⚠️ **KNOWN GAP** — no documented procedure exists; said so plainly rather than
    guessed at.
