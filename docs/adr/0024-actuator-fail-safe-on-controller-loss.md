---
adr: 0024
title: 'Actuator fail-safe on controller loss: board-native dead-man on the pump supply, with an external watchdog as fallback'
status: 'Proposed'
date: '2026-10-25'
deciders: ['Alberto']
author: 'AI Assistant'
dependsOn:
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (single Modbus master; Relay 32CH @0x2, Analog Output 8CH (B) @0x1)'
relatedDocuments:
  - docs/reviews/2026-10-25-repo-review.md
  - docs/adr/0014-standardized-controller-modbus-io-hardware.md
  - docs/heat-pump-integration.md
  - packages/devices/modbus-io/modbus_relay_board_32ch.yaml
  - packages/devices/modbus-io/modbus_relay_switch.yaml
  - packages/devices/modbus-io/modbus_analog_output.yaml
  - climate/packages/components/mixing_pump.yaml
  - climate/packages/components/direct_pump.yaml
  - climate/packages/components/heat_only_radiant.yaml
  - boards/t-connect-pro.yaml
---

# ADR-0024: Actuator fail-safe on controller loss

## Status

**Proposed** (2026-10-25). Nothing here is implemented: this record is the research, the options and a
recommendation for the owner to accept, amend or reject. Its subject is review item **R-09**
(*"if the master hangs, the Modbus relays keep their last state"*). The recommendation depends on
board behaviours that no primary document I could read confirms; they are listed as bench tests in
[Open questions](#open-questions-to-verify-on-hardware), and the decision should not be taken as
final until the first two pass.

## Context

The Climate controller (T-Connect Pro) is the sole Modbus master (ADR-0014). Two commodity boards hold
every actuator, and both are **stateful and unsupervised**: they execute the last command they received
and nothing asks them to prove the master is still alive.

| Board | Address | Carries | Stuck-state consequence |
|---|---|---|---|
| Relay 32CH | `0x2` | `relay_1..4` circulation pumps; `relay_6..17` radiant zone valves; `relay_18/19` planned for the heat pump's SG-Ready contacts (`docs/heat-pump-integration.md`) | Pumps on: running against closed/open valves, wear, and in cooling season circulating cold water through a mixing valve that is no longer being dew-point-protected (condensation). SG-Ready stuck at "forced-on": heat pump held at max boost |
| Analog Out 8CH (B) | `0x1` | `analog_output_1,2` mixing valves; `3..6` fancoil fans; `7,8` MEV fan speed | Valve frozen at its last opening; fans frozen at last speed |

### What already happens when the controller misbehaves (read from the code, ESPHome 2026.8.0)

- **Hung main loop: covered, quickly.** ESPHome enables the ESP-IDF task watchdog on the loop task only
  (`esp32/hal.cpp: esp_task_wdt_add(nullptr)`; idle tasks are not watched), with
  `CONFIG_ESP_TASK_WDT_PANIC=y` and a default `esp32: watchdog_timeout` of **5 s** (range 5-60 s,
  `esp32/__init__.py`). A loop that stops for more than 5 s panics and the chip reboots. This repo sets
  nothing, so the default applies.
- **What the reboot leaves on the boards: whatever was there.** The boards are separate devices; the
  reboot does not touch them. At boot the repo's relay switches use ESPHome's
  `modbus_controller` switch default `restore_mode: DISABLED` (`modbus_controller/switch/__init__.py`), so
  **nothing is written** at startup; the switch state is simply read back from the coil by polling. The
  analog `number` has no restore either; the board keeps its last voltage until the first PID write.
  Pumps are switched by an *edge-triggered* handler on a template binary sensor
  (`mixing_pump.yaml`, `direct_pump.yaml`), so they are re-commanded only when that sensor publishes its
  first value after boot, which is expected but not verified to fire.
- **Boot loop: not covered.** After `safe_mode: num_attempts` (default 10) failed boots, ESPHome enters
  safe mode, which brings up only the early-priority components (network, OTA) and reboots after
  `reboot_timeout` (default 5 min). Modbus and the control logic do not run in that state, so the boards
  stay frozen at the last commanded state for as long as the loop lasts.
- **Bus fault with a healthy controller: not covered.** The loop keeps feeding the watchdog; the
  `modbus_controller` merely marks the device offline (`on_offline` hook exists, unused). Nothing can
  actuate over a dead bus, and the relay board has deliberately no status sensor
  (`modbus_relay_board_32ch.yaml`), so there is not even a local alarm.
- **Controller power loss, or a hang that does not stall the loop task** (e.g. control logic wedged while the
  loop runs): not covered.

So the open hole is not "ESP32 reboots slowly"; it is **everything where the controller cannot or does not
write**: dead controller, dead bus, boot loop/safe mode, wedged logic.

### What the boards offer (research)

Confidence tags: **[W]** Waveshare wiki text, seen only as quoted by a search tool (see the access note
below); **[T]** third-party, measured on real hardware, README read directly; **[S]** ESPHome source read;
**[U]** unverified.

Access note: `www.waveshare.com` is unreachable from the research sandbox (the egress proxy answers 403 to
`CONNECT`; ADR-0014 recorded the same 403 for fetchers), so the wiki pages could not be opened. Everything
tagged [W] is the search tool's excerpt of the page, not my own reading.

**Relay 32CH**

- **Timed pulses exist [W].** Product page: *"Features flash-on, flash-off function, it is possible to turn on
  the relay for a while and then close it automatically via the command"*
  (<https://www.waveshare.com/modbus-rtu-relay-32ch.htm>). The 32CH protocol section lists, both **write-only,
  function code `0x05`**:
  - flash-on, channels 1-32: registers **`0x0200`-`0x021F`** (`0x0200 + channel - 1`);
  - flash-off, channels 1-32: registers **`0x0400`-`0x041F`** (`0x0400 + channel - 1`);
  - value = delay, *"Delay time: data*100ms"*, e.g. `0x0007` = 700 ms; maximum reported as `0x7FFF`
    (about 54.6 min) by a secondary excerpt of the Spotpear mirror [U].
  - Source: <https://www.waveshare.com/wiki/Modbus_RTU_Relay_32CH>; same scheme in the shared protocol
    template <https://www.waveshare.com/wiki/Template:Modbus_RTU_Relay_Protocol_V2>. Example frames quoted
    from sibling boards: `01 05 02 00 00 07 8D B0` (relay 1 flash-on 700 ms), `01 05 04 01 00 06 1D 38`
    (relay 2 flash-off 600 ms).
- **Pulse semantics, measured [T].** Measured on a 30CH sibling (Modbus POE ETH Relay 30CH):
  - `flash_on` closes the coil for the duration, **then opens it and leaves it open**; `flash_off` is the mirror
    image and leaves it closed.
  - *"A plain on/off write while a pulse is running does nothing at all"* (the channel is hands-off until the
    countdown ends).
  - A new flash command on a running channel *replaces* the countdown ("a single-coil flash trigger register
    can only run one countdown at a time").
  - The author relies on this as the fail-safe: *"even if this gateway process hangs, the pulse still ends on
    time"*, and *"Flash stays hardware-timed"*.
  - Source: <https://github.com/pradki/waveshare-mqtt-gateway> (README, sections "Hardware" and "Reliability").
    Not Waveshare documentation, and a different board; the timing being a *hardware* timer is the author's
    inference, not a vendor statement.
- **Communication-loss timeout / watchdog: none found.** No retrieved Waveshare page or excerpt mentions a
  "no frames for N seconds, go to state X" setting. The registers I did see are `0x0000-0x001F` coils,
  `0x00FF` all-relays, flash `0x0200/0x0400`, UART `0x2000`, address `0x4000` and version `0x8000`. The
  *Relay (D)* page has a per-channel "control mode" block at `0x1000-0x1007`, but that belongs to the model
  with digital inputs (normal/linkage/toggle/edge-trigger) and is unrelated to bus supervision
  (<https://www.waveshare.com/wiki/Modbus_RTU_Relay_(D)>). Absence of evidence from excerpts, not proof of
  absence. [U]
- **Power-on default state: not documented in anything I could read.** Reasonable expectation is "all open"
  (de-energised) but this is not stated. [U]

**Analog Output 8CH (B)**

- Holding registers `4x0000-4x0007` = channels 1-8, read/write, FC `0x03`/`0x06`/`0x10`, value in mV
  (the (B) page's example `03 E8` = 1000 mV; the non-B page says µA, which is the current variant). UART
  parameters `4x2000`, device address `4x4000`, software version `4x8000` (read-only). [W]
  (<https://www.waveshare.com/wiki/Modbus_RTU_Analog_Output_8CH_(B)>,
  <https://www.waveshare.com/wiki/Modbus_RTU_Analog_Output_8CH>)
- **No flash/timed output, no timeout, no documented power-on value.** [W]/[U] Nothing board-native can make
  this board fall back to 0 V by itself.

### Consequence for the design space

Only the **relay board** has a hardware-timed, self-reverting primitive, and that primitive reverts to
**open**. The analog board has none. But the hazard analysis lets us avoid needing one:

- Every dangerous stuck-state on the water side needs **flow**. Flow needs a **circulation pump** (`relay_1..4`).
  With the pumps stopped, a mixing valve or fancoil valve frozen anywhere is inert, and a fancoil fan or
  radiant zone valve left on is harmless.
- A stuck MEV fan (`analog_output_7/8`) is the *benign* failure for ventilation. Forcing it to zero would be
  worse than leaving it.
- Radiant zone valves (`relay_6..17`, thermal actuators on 60 s slow PWM) are inert without a pump.
- The heat-pump SG-Ready contacts, when added, are the other thing that must not stay stuck: both open means
  SG state 2, normal operation (`docs/heat-pump-integration.md`).

So the circuits that need a dead-man are **the four pump relays, plus the SG-Ready pair once they exist**.
Everything else can stay as is.

## Options

Cost scale: S (<1 day / a few lines), M (a few days), L (hardware + electrician). Traffic figures assume
the repo's bus settings (38400 8E1, `turnaround_time: 100ms`, `send_wait_time: 250ms`): one write-single
transaction is about 5 ms of wire time plus the 100 ms turnaround, call it **~0.11 s of bus per command**.
The 2026.8.0 hub picks WRITE-class commands ahead of polling reads (`modbus.cpp`, `select_next_ready_`);
whether a custom raw command is classed as a write is not verified (O5).

### Option A: board-native dead-man, re-armed by the master

The master periodically sends `flash_on` (FC `0x05`, `0x0200 + ch - 1`, value N) for each protected channel. If
the master stops (death, hang, bus fault, boot loop, safe mode), the board's own timer ends the pulse and the
contact **opens**, within N x 100 ms.

- **A1, per-pump:** apply it to each of `relay_1..4` (and later SG-Ready).
- **A2, one master-enable relay (preferred variant):** re-arm **one** spare channel (e.g. `relay_22`, coil
  `0x15`, flash register `0x0215`) and wire its normally-open contact **in series with the common supply of the
  pump circuits** (the L feed to the COMs of `relay_1..4`, and the SG-Ready feed). Pump relays stay ordinary
  switches. Nothing else in the package model changes, and the "hands-off during pulse" quirk affects only
  the enable relay, which nothing else drives. One command per re-arm instead of four.
- **Protects:** dead/hung controller, dead RS485 bus or connector, crash loop, safe mode, the OTA window; any
  condition under which the master stops talking. Does *not* protect against a hung **relay board** MCU that
  freezes its timer (unknown), nor against a controller that is alive, talking and wrong.
- **Cost:** A2: S firmware (one script + `interval:`), M electrical (series contact in the pump supply; a
  small pump-load check against the relay's 250 VAC/10 A rating, or switch a contactor coil instead). A1:
  M firmware (see risks).
- **Traffic:** A2 ~0.11 s per 15 s (<1 %). A1 4x that. Protecting all 17 used relays would be ~12 % bus load
  on top of polling and is not warranted.
- **Risks:**
  - Behaviour is only [T]-measured on a sibling board. Must be bench-confirmed on the real 32CH (see O1-O3).
  - **Re-arm chatter:** if re-triggering a running pulse momentarily de-energises the coil, the enable relay
    (and, for A1, each pump) clicks every re-arm: 5 760 cycles/day, about 2 M per year, which would wear the
    relay out, and a flicker on a pump supply is unacceptable anyway. This is the make-or-break test.
  - **A1 only:** during a pulse a plain `off` is ignored, and the polled coil then reads ON. Pump `switch.turn_off` and
    any HA manual toggle of `relay_1..4` stop working until the pulse lapses (<= N x 100 ms). Pump relays must
    be `internal` and driven by a wrapper, and the edge-triggered handlers become periodic. That is the
    larger refactor of `mixing_pump.yaml`/`direct_pump.yaml`.
  - Pump overrun/lag of up to the pulse length on shutdown is acceptable (pump delay-off is usual).
  - A reboot is not a fault: the pulse is 60 s, a TWDT reboot is an estimated 10-20 s (not measured), so pumps do not drop during a quick
    recovery provided re-arming starts early in boot.
- **ESPHome mapping:** no new component. A raw frame through the existing hub, no CRC needed (the hub
  appends it; the custom command is "address + PDU", `modbus_controller.cpp: ModbusCommandItem::send`):

  ```yaml
  interval:
    - interval: 15s
      then:
        - lambda: |-
            // addr 0x02, FC 0x05, flash-on reg 0x0215 (relay_22), 600 x 100 ms = 60 s
            std::vector<uint8_t> f = {0x02, 0x05, 0x02, 0x15, 0x02, 0x58};
            id(relay_board_1)->queue_command(
                modbus_controller::ModbusCommandItem::create_custom_command(id(relay_board_1), f));
  ```

  Gate the lambda on "controller considers itself healthy" (see Option D) so a wedged control task stops
  re-arming. The same raw frame is also possible from a `write_lambda` on a `modbus_controller` switch,
  which is how A1 would be wired (a switch whose `turn_on` sends flash-on and whose `turn_off` sends
  nothing).

### Option B: board communication-loss timeout

A register that makes the board drop outputs after N seconds without a valid frame. **No evidence it exists
on either board** (see research). Would be the ideal (zero extra traffic, no semantics quirks). Action is an
inquiry, not a design: ask Waveshare support whether any firmware revision of the Relay 32CH or Analog 8CH (B)
has one. If yes, it supersedes A for that board. Cost S (an email), result unknown.

### Option C: external hardware watchdog

A retriggerable timer (off-the-shelf DIN-rail watchdog/timer relay, or a supervisor IC plus relay) that must
see a heartbeat from the controller, driving a normally-open contactor in the pump/SG supply.

- **Protects:** the widest set: A's cases plus a hung relay-board MCU, plus any logic wedge that stops the
  heartbeat. Independent of Waveshare firmware. If the controller's heartbeat is gated on recent *successful
  Modbus writes*, a dead bus trips it too.
- **Cost:** L: a part, DIN space, a mains contactor or relay, wiring, and a heartbeat signal. The T-Connect
  Pro has almost no free GPIO (ADR-0014 §5); IO4/IO5 (RS232 pins) are free but sit behind the RS232
  transceiver and would need level handling, **to be checked on the LilyGO schematic**. A creative alternative
  heartbeat is a relay-board contact (flash-on on a spare channel into the watchdog trigger), but that is
  Option A with extra parts.
- **Risks:** a new single point of failure that can itself nuisance-trip (cold house), another thing to
  commission; a trigger relay toggling at a fast heartbeat rate wears out, a slow one needs a long watchdog
  timeout. If the supply of the whole relay board were switched instead, the analog board would need a
  verified 0 V power-on state and the MEV fan would stop with it, so do not switch the analog board.
- **ESPHome mapping:** `interval: 1s` toggling a `output: gpio` pin, gated on a template boolean
  (loop alive, relay board `on_online`, last write acknowledged).

### Option D: firmware-only mitigations

Cheap and worth doing, but none of them acts when the controller is gone.

- **D1, safe-by-default boot:** `restore_mode: ALWAYS_OFF` on the pump relays (add an optional var to
  `modbus_relay_switch.yaml`, default `DISABLED` so lighting/other consumers are unchanged), and an
  `esphome: on_boot` (priority below the modbus hub) that writes `0` to `analog_output_1..6`. Closes the
  window "controller rebooted with stale outputs". The ALWAYS_OFF path runs in the switch's `setup()`, which
  may precede the hub's readiness (O6); `on_boot` is the safe alternative. Also makes the first-boot
  edge-trigger uncertainty irrelevant.
- **D2, keep the TWDT:** leave `esp32: watchdog_timeout` at 5 s (the floor). Optionally set it explicitly in
  `boards/t-connect-pro.yaml` so it is not an accident of defaults.
- **D3, observability:** wire `modbus_controller: on_offline` for `relay_board_1` and `analog_outputs_board_1`
  to a panel alarm and an HA notification (`relay_board_1` has no status sensor today). Surfaces a dead bus
  that A/C will otherwise convert silently into "house stops heating".
- **D4, health-gated re-arm:** the re-arm in A (or heartbeat in C) fires only if a software health predicate
  holds (e.g. a recent PID update tick, modbus not offline). Catches wedged logic under a live loop.
- **Protects:** reboot windows and (D3) human awareness. **Does not** protect: death, bus fault, boot loop.
- **Cost:** S. **Risks:** D1 bounces the pumps once on every reboot/OTA (they are re-commanded within
  seconds). Acceptable and arguably desirable.

### Comparison

| | Dead controller | Dead bus | Boot loop / safe mode | Hung relay board | Analog board | Cost | New failure modes |
|---|---|---|---|---|---|---|---|
| A2 master-enable + flash | yes | yes | yes | maybe [U] | via pump cut-off | S + M wiring | re-arm chatter [U] |
| A1 per-pump flash | yes | yes | yes | maybe [U] | via pump cut-off | M | HA/off writes ignored |
| B comm-loss timeout | yes | yes | yes | n/a | would cover | S (inquiry) | none known; may not exist |
| C external watchdog | yes | if gated | yes | yes | optional | L | nuisance trips, GPIO |
| D firmware only | no | no | no | no | boot only | S | pump bounce on boot |

## Decision (proposed)

**Adopt D + A2, hold C as the fallback, ask for B.**

1. **D1-D3 now** (no hardware dependency): safe-by-default boot for the pump relays and analog valves,
   explicit watchdog timeout, `on_offline` alarms.
2. **A2: a single master-enable relay.** One spare relay channel (`relay_22`) is flash-on re-armed every 15 s
   with a 60 s pulse (`0x0258`); its NO contact is in series with the supply of the four pump relays (and, when
   wired, SG-Ready). Re-arm is gated on a software health predicate (D4). Pumps and zone relays keep their
   current switch model and edge-triggered handlers. Fail-safe state = pumps off, SG-Ready normal.
   Rationale: it uses the one board-native, hardware-timed primitive found, adds one command per 15 s,
   leaves the existing drivers untouched, and the analog board needs nothing because the pump cut-off makes
   its stuck state inert. The 60 s window is short against the thermal mass of radiant floors and survives a
   TWDT reboot without interrupting the pumps.
3. **Gate:** do not wire anything until bench tests O1-O3 pass. If re-arm chatters (O2), the pulse does not
   self-revert as measured (O1), or the board's timer dies with its MCU in a way that matters (O4), switch to
   **C** (external watchdog contactor). Both A2 and C share the same series-contact wiring, so the electrical
   work is not wasted.
4. **B is a parallel inquiry** to Waveshare; if a comm-loss timeout turns out to exist it replaces A2.
5. **Out of scope:** the analog board gets no timeout; the MEV fans are deliberately left fail-as-is.

## Consequences

### Positive

- Pumps stop, and SG-Ready returns to normal operation, within <= 60 s of the controller falling silent for any
  reason, including cases the ESP32 watchdog cannot see (bus, boot loop, safe mode).
- Software change is tiny and local (a script, an `interval`, two optional vars). No changes to room/floor files.
- Wiring done for A2 is reusable if the project upgrades to C.

### Negative / costs

- **A new way to stop heating.** A silent controller now means a cold house (winter) or warm house (summer)
  instead of a runaway circuit. The D3 alarms are therefore part of the decision, not optional.
- One relay channel and a series contact to commission and document (`climate/CLAUDE.md` Appendix B: `relay_22`
  becomes "Pump master enable"; flash semantics noted next to the 32ch driver).
- `relay_22` is no longer an ordinary switch: the 32ch package still creates `switch.relay_22`, which
  must be marked `internal` and never written directly (writes are ignored while the pulse runs).
- A2 depends on undocumented-in-primary-sources behaviour of a board firmware. Mitigated by the bench gate.

## Alternatives considered

- **Rely on the ESP32 task watchdog alone:** covers only a stalled loop, and leaves boot loops, safe mode, a
  dead bus and a dead controller untouched (see Context).
- **Flash every used relay (A over 17 channels):** ~12 % bus load, semantics quirks on all zone relays, no
  extra safety (zone valves are inert without a pump).
- **Software-timer "pulses" (turn on, schedule turn-off in the master):** fails exactly when the master does;
  it is the thing this ADR exists to replace.
- **Home Assistant as supervisor:** HA cannot reach the boards if the controller or bus is down, and HA
  availability is explicitly not a dependency of actuation (root `CLAUDE.md`, Home Assistant Integration).
- **`flash_off` instead of `flash_on`:** reverts to *closed*; it is the wrong polarity for a fail-open
  design.
- **Cut power to both boards via the watchdog (C variant):** also zeroes the MEV fans, and the analog
  board's power-on output is undocumented.

## Open questions to verify on hardware

Bench-test on the actual Relay 32CH (a relay channel on a scope or continuity logger; a known-bad master
simulated by unplugging RS485, by `esphome` restart button, and by yanking controller power). In priority
order:

1. **O1, pulse semantics.** Send `flash_on` (FC 0x05, 0x0200+ch-1, value 600). Confirm: coil closes
   immediately; opens by itself after 60 s +/- 1 s; the 32CH honours N x 100 ms; `0x7FFF` is accepted (the
   documented maximum is unconfirmed); a plain `0x0000` write during the pulse is ignored (hands-off).
2. **O2, re-arm.** While a pulse runs, send a second `flash_on` (same value). Record on a contact logger: does the
   contact stay closed throughout (required), or does it click? Does the second command restart the full
   countdown (required) or extend/ignore it? Does a *shorter* second value cut the pulse short (useful for
   an "off now" path)?
3. **O3, master silent.** With the contact held by an active pulse, pull the RS485 plug and, separately, cut
   controller power: the contact must open at the expiry time and stay open without any bus traffic. Also
   check it stays open when the controller comes back and polls (reading coils must not restart anything).
4. **O4, board reset behaviour.** Power-cycle the relay board mid-pulse: what is the coil state after boot
   (documented nowhere I could read)? If it comes up ON, the A2 premise (de-energised = safe) needs a
   different wiring (use NC or invert).
5. **O5, bus under load.** Measure real transaction time with re-arm interleaved with the 2 s polling and
   the 30 s MEV polls; verify no re-arm is delayed past 15 s (watch `queue_command` timing at DEBUG), and
   that a failed/missed re-arm is tolerated (pulse 60 s vs interval 15 s = three misses).
6. **O6, boot ordering.** Confirm `restore_mode: ALWAYS_OFF` on a `modbus_controller` switch actually reaches the
   board when issued from `setup()` (hub readiness), and whether the first template-binary-sensor publish
   after boot fires the pump `on_state` handler. If either fails, use `on_boot` writes.
7. **O7, safe mode and TWDT.** Force a crash loop (>10 reboots) and confirm modbus is not running in safe
   mode (assumption in Context), and that the pumps drop at pulse expiry. Force a loop stall > 5 s and time
   the reboot-to-first-re-arm interval against the 60 s pulse.
8. **O8, analog board.** Read the voltage on each output at power-up and after a master silence; confirm the
   claim "no timeout" with a longer observation. If the power-on value is not 0 V, record what each valve
   and MEV actuator does at that value.
9. **O9, electrical.** Pump supply topology (shared L feed? per-pump fusing?), relay contact rating margin
   against pump inrush through a single series contact, whether a contactor is warranted, and what the
   Stiebel WPM expects when all consumer pumps stop (flow monitoring, buffer; ask the installer).
10. **O10, B inquiry.** Ask Waveshare support whether any firmware has a communication-loss timeout or a
    configurable power-on state for the Relay 32CH or Analog 8CH (B).
11. **O11, heartbeat for C.** If C is ever needed: which T-Connect Pro pin can carry a heartbeat (check the
    LilyGO schematic; IO4/IO5 sit behind the RS232 transceiver).

## Sources

- Waveshare Modbus RTU Relay 32CH wiki, flash-on `0x0200-0x021F`, flash-off `0x0400-0x041F`, FC `0x05`,
  delay x 100 ms: <https://www.waveshare.com/wiki/Modbus_RTU_Relay_32CH> (via search excerpt, page not opened)
- Waveshare relay protocol template: <https://www.waveshare.com/wiki/Template:Modbus_RTU_Relay_Protocol_V2>
  (via search excerpt)
- Waveshare product page, flash-on/flash-off feature statement:
  <https://www.waveshare.com/modbus-rtu-relay-32ch.htm> (via search excerpt)
- Waveshare Modbus RTU Analog Output 8CH (B) wiki, registers `4x0000-4x0007`, `4x2000`, `4x4000`, `4x8000`:
  <https://www.waveshare.com/wiki/Modbus_RTU_Analog_Output_8CH_(B)> and
  <https://www.waveshare.com/wiki/Modbus_RTU_Analog_Output_8CH> (via search excerpts)
- Relay (D) control-mode block `4x1000-4x1007` (not applicable):
  <https://www.waveshare.com/wiki/Modbus_RTU_Relay_(D)> (via search excerpt)
- Measured flash semantics on a 30CH sibling (third-party, read directly):
  <https://github.com/pradki/waveshare-mqtt-gateway>
- ESPHome 2026.8.0 sources read locally: `esphome/components/esp32/{__init__.py,hal.cpp}`,
  `esphome/components/safe_mode/{__init__.py,safe_mode.cpp}`,
  `esphome/components/modbus_controller/{__init__.py,modbus_controller.cpp,switch/}`,
  `esphome/components/modbus/modbus.cpp`.
