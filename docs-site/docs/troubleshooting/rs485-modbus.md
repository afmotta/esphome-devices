# RS485 / Modbus — Diagnose & Fix: Common Problems

RS485 is the wired bus that carries commands between a controller and the
"dumb" I/O boards it operates — relay banks, analog output boards, and the
ventilation (MEV) unit. Modbus RTU is the message format spoken over that
wire. This bus is **shared infrastructure used by both application systems
in the house**:

- The **climate** system has its own RS485 bus, on the climate controller,
  talking to an analog output board, a relay board, and the MEV unit.
- The **lighting** system has a separate, independent RS485 bus, on the
  lighting controller, talking to its own relay board.

These are two physically separate buses (not one shared wire), but they use
identical wiring rules, and the relay board's Modbus address (`0x2`) is
deliberately mirrored on both — so a single spare relay board works as a
drop-in replacement on either bus with no re-addressing. Both buses target
**38400 baud, 8 data bits, even parity, 1 stop bit ("38400 8E1")**. 🔵
DESIGNED — this is the target configuration; the parity/baud agreement
across all boards on each bus is still pending a physical bring-up check.

If your problem is with a room's temperature/comfort sensors specifically,
those do **not** travel over this bus at all (they arrive via CAN bus with a
Home Assistant fallback) — see [Climate](climate.md) instead. If your
problem is a light not responding to a switch, start at
[Lighting](lighting.md), which will point back here if the bus itself is
the suspect.

!!! note "How to read the confidence tags on this page"
    This system has not been physically installed yet. 🟢 VERIFIED = confirmed
    on a bench or in the field. 🔵 DESIGNED = built and intended to work this
    way, not yet proven against a real fault. ⚠️ KNOWN GAP = genuinely
    unresolved.

---

## No communication at all

**Symptom:** The controller's logs show every device on the bus failing to
respond ("no response", timeout errors on every poll), not just one device.

**Likely causes:**

- One or more devices are not powered on.
- A/B wiring is broken, reversed, or disconnected somewhere on the bus.
- Baud rate or parity mismatch between the controller and the I/O boards.
- Missing termination resistors causing signal reflections severe enough to
  block communication entirely.

**Diagnostic steps:**

1. **Check power** on every device on the bus — power LEDs lit, correct
   supply voltage for each device.
2. **Check wiring continuity**: with everything powered off, use a
   multimeter to confirm A-to-A and B-to-B continuity runs all the way from
   the controller to the last device, and that there's no A-to-B short.
3. **Check configuration**: does every device on the bus agree on 38400 8E1?
   The Waveshare I/O boards ship from the factory at 9600 8N1 and must be
   reconfigured to the bus's target settings before first use — an
   unreconfigured board is a classic "no communication" cause. The MEV unit
   is the least flexible bus member (its own factory default is 9600 8N1),
   so if it can't be moved to 38400 8E1, the whole bus may need to be
   reconciled to whatever the MEV can actually do, rather than the MEV being
   forced to the others. 🔵 DESIGNED
4. **Check termination**: power off the bus, disconnect the A/B pair from
   the controller, and measure resistance between A and B with a multimeter.
   See [Termination check](#termination-resistor-check) below.
5. **Isolate**: disconnect every device except the controller. The
   controller should report "no response" for everything (expected — no
   slaves are attached). Reconnect devices one at a time until communication
   resumes; the device you just added when it broke again is the suspect, or
   the wiring segment leading to it.

**Fix:**

- Power up any unpowered device.
- Repair broken/reversed wiring; re-seat and tighten all terminal-block
  screws.
- Reconfigure a board that's still on its factory 9600 8N1 default to the
  bus's 38400 8E1 target (consult that board's manual for the procedure).
- Install missing termination resistors (see below).

**When to escalate:** If wiring, power, and configuration all check out and
the bus still shows no communication at all, the controller's own RS485
transceiver may be the problem — see
[Controller replacement](../hardware/controller.md).

---

## Intermittent communication (works, then fails, then works again)

**Symptom:** Communication mostly works but drops out unpredictably. Logs
show occasional CRC (checksum) errors, roughly 1–10% of polls failing.

**Likely causes:**

- Missing or poorly seated termination resistors, causing reflections that
  corrupt some but not all messages.
- Loose terminal-block connections (intermittent contact).
- Electromagnetic interference (EMI) from nearby power cables, fluorescent
  fixtures, or variable-frequency drives.
- A cable run close to its maximum length for the baud rate in use.

**Diagnostic steps:**

1. Verify termination resistance (see below) — a missing terminator often
   causes exactly this "mostly works" pattern rather than total silence.
2. Re-seat and tighten every terminal-block connection on the bus; a loose
   screw can cause contact that comes and goes with vibration or temperature.
3. If the RS485 cable runs parallel to power cabling anywhere, or passes
   near known EMI sources, try moving it (minimum 30cm separation from power
   cables is the general rule) and see if the error rate changes.
4. Check the total cable length against the length limit for 38400 baud
   (500m) — see [Cable length](#cable-length-guidance) below.

**Fix:**

- Install/reseat termination resistors.
- Tighten all terminal connections.
- Re-route cable away from EMI sources or power cabling.
- If length is marginal, consider a lower baud rate as a *temporary*
  diagnostic step (not a permanent fix — see High Error Rate below) or a
  repeater if the run is genuinely too long.

**When to escalate:** If intermittent errors persist after termination,
connections, and routing are all confirmed good, treat it as a possible
cable-quality or connector-hardware issue and consider replacing the
affected cable segment.

---

## Some devices work, others don't

**Symptom:** The controller talks fine to some devices on the bus (e.g. the
relay board) but not others (e.g. the analog output board or MEV), even
though they're all on the same physical run.

**Likely causes:**

- Duplicate or wrong Modbus address on the non-responding device.
- A wiring break specifically between the last working device and the first
  non-working one.
- The non-responding device itself has failed or lost power.

**Diagnostic steps:**

1. **Check addresses.** Every device on a bus must have a unique Modbus
   address. On the climate bus: analog output board = `0x1`, relay board =
   `0x2`, MEV = `0x10`. On the lighting bus: relay board = `0x2`. A
   duplicate or misconfigured address will make a device silently
   unreachable (or cause it to respond to the wrong device's polls).
2. **Check wiring to the non-working device(s)**: A/B not swapped,
   continuity intact from the previous device in the chain.
3. **Isolate with a bypass test**: temporarily disconnect the suspect device
   and bridge the A/B wires straight through to whatever comes after it on
   the bus. If devices further down the chain start working again, the
   disconnected device (or the wiring immediately to it) was the problem.

   ```
   Before:
   Controller ─── Device 1 ─── Device 2 ─── Device 3
                              (device 3 unreachable)

   Bypass test (skip Device 2's wiring, jump straight through):
   Controller ─── Device 1 ──┐         ┌── Device 3
                              └─────────┘

   If Device 3 now responds, Device 2 (or its wiring) is the fault.
   ```

4. Check the failed device's own power supply.

**Fix:**

- Correct a duplicate/wrong address.
- Repair the wiring segment identified by the bypass test.
- Replace a device confirmed faulty by bypass testing — see
  [Relay board replacement](../hardware/relay-board.md),
  [Analog output board replacement](../hardware/analog-board.md), or
  [MEV replacement](../hardware/mev.md) as appropriate.

**When to escalate:** Once the bypass test has isolated a specific device or
cable segment, go straight to the matching hardware page rather than
re-testing further.

---

## High error rate (>5%)

**Symptom:** The bus mostly communicates, but CRC errors are frequent and
data occasionally looks corrupted or unreliable.

**Likely causes:**

- Termination or reflection issues (same root causes as intermittent
  communication, just more severe).
- Poor-quality or unshielded cable.
- Ground loops from shield grounded at both ends instead of one.
- Heavy EMI.

**Diagnostic steps:**

1. Re-verify termination resistance (below).
2. Confirm the cable is twisted-pair and shielded, and that the shield is
   grounded at the controller end **only** — grounding both ends creates a
   ground loop that injects noise.
3. As a *diagnostic-only* step, temporarily drop the baud rate (e.g. to
   9600) on every device on the bus at once. Lower baud rates are more
   noise-tolerant; if the error rate drops sharply, that confirms a signal-
   quality problem rather than a configuration one. Put the baud rate back
   to 38400 afterwards — this is a test, not a fix, and every device on the
   bus must change together or nothing will communicate at all.
4. If you have access to an oscilloscope, rounded edges on the waveform
   indicate reflections (termination), while noise spikes indicate EMI.

**Fix:**

- Fix termination.
- Replace unshielded/low-quality cable with shielded twisted-pair (Cat5e/
  Cat6 Ethernet cable, using one pair, works well and is easy to source).
- Ground the shield at one end only.
- Move the cable away from power wiring and other EMI sources.

**When to escalate:** If the error rate stays high after termination,
cabling, and grounding are all confirmed correct, this is worth treating as
a hardware fault in the controller's RS485 transceiver or a specific I/O
board — see [Controller replacement](../hardware/controller.md) or the
relevant board's hardware page.

---

## Termination resistor check

RS485 needs a 120Ω resistor at **each physical end** of the bus (the
controller end and the last device on the chain) — never in the middle.
With power off, disconnect the A/B pair at the controller and measure
resistance between A and B with a multimeter:

| Reading | Meaning |
|---|---|
| >1 kΩ (effectively open) | No terminators present — missing terminator(s) |
| ~120Ω | Only one end terminated |
| **~60Ω** | Both ends properly terminated — this is the target |
| <20Ω | Short circuit — a wiring fault, not a termination problem |

Two 120Ω resistors in parallel measure as 60Ω, which is why ~60Ω (not
~120Ω) is the number to look for when both ends are correctly terminated.

## Cable length guidance

At the project's target 38400 baud, the RS485 standard supports up to
**500m** of total cable length, with stubs (branches off the main run) kept
to 1m or less. House-scale wiring runs are expected to come in well under
100m per bus — comfortably inside that limit — but this hasn't been
measured yet since the physical installation hasn't happened
(⚠️ KNOWN GAP: real cable lengths for this house are not yet recorded
anywhere). If a run ever needs to exceed roughly 1000m, or you're
approaching 32 devices on one bus, a repeater becomes worth considering —
neither applies at this house's scale.

**Wiring topology matters as much as length**: RS485 must be wired as a
single daisy-chain (controller → device → device → … → last device), never
as a star with multiple branches from one point. A star topology causes
reflections at every branch and is very difficult to terminate correctly —
if you find star-style wiring, that alone can explain intermittent or high
error rates even with correct termination resistor values.

**When to escalate:** If none of the sections above resolve the problem,
or you suspect the fault is inside a specific board rather than the bus
itself, move to the relevant page under Hardware Died (starting at
[Which device died?](../hardware/index.md)).
