# Climate — Diagnose & Fix: Common Problems

The climate system controls radiant floor/ceiling heating and cooling plus
fancoil units across the house's three floors, using one controller that
reads room sensors over CAN bus (with a Home Assistant fallback) and drives
relays and 0-10V outputs over its own RS485/Modbus bus. This page covers
sensor-failover confusion, PID (temperature-control loop) tuning problems,
ventilation (MEV) issues, and the manual seasonal-mode switch. For wiring
and communication problems on the RS485 bus itself, see
[RS485 / Modbus](rs485-modbus.md). For an explanation of the sensor entity
IDs mentioned below, see [Everyday Monitoring](../monitoring.md).

!!! note "How to read the confidence tags on this page"
    This system has not been physically installed yet. 🟢 VERIFIED = confirmed
    on a bench or in the field. 🔵 DESIGNED = built and intended to work this
    way, not yet proven against a real fault. ⚠️ KNOWN GAP = genuinely
    unresolved.

---

## A room's temperature reading looks wrong, frozen, or missing

**Symptom:** A room's displayed temperature stops updating, jumps to an odd
value, or a diagnostic "sensor tier" entity shows something other than the
normal source.

**Background — how room sensor readings are chosen:** Each room's
temperature (and humidity) has up to three tiers, tried in order:

1. **Primary** — the CAN bus sensor reading, received directly by the
   controller. This is used whenever it has a real value.
2. **Secondary** — a Home Assistant sensor, used only when the primary is
   unavailable. It is treated as unavailable when Home Assistant reports the
   entity `unavailable`/`unknown`, or when Home Assistant has been
   disconnected from the controller for more than 5 minutes.
3. **Emergency** — used when *both* of the above are unavailable. The system
   publishes no usable number (internally, "not a number" / NaN) for that
   room's temperature.

A companion diagnostic sensor (the entity named `..._sensor_tier`) tells you
which tier is currently active, so you don't have to guess — see
[Everyday Monitoring](../monitoring.md) for the exact entity-naming pattern.

**Important — what "stuck in Emergency" actually means:** The Emergency tier
switches over **immediately**, the moment both the primary and secondary
readings go bad — there is no waiting period built into the sensor logic
itself. 🟢 VERIFIED (read directly from the failover component's code,
`climate/packages/components/failover_sensor.yaml`). The room's PID
controller then sees no usable reading and drops its outputs to 0 **right
away** (valve closed, fancoil off) — there is no "safe shutdown after 5
minutes" timer anywhere; older project documents that said so were wrong.
The only 5-minute figure is on the Home Assistant side: the secondary tier
is declared unavailable once Home Assistant has been disconnected from the
controller for 5 minutes (a grace period that rides out an HA restart),
so a frozen last value is never used indefinitely. 🔵 DESIGNED — covered by
automated tests, not yet bench-tested on the real controller. Note: an
`esphome logs` session left open counts as a Home Assistant connection and
keeps the secondary tier alive during an outage; use
`esphome logs --no-states`.

**Known gap (review R-05):** if the sensor dies during an active
fancoil/radiant boost, the boost override can keep the radiant valve open
(100% cold) until R-05 is fixed.

**Likely causes:**

- Primary (CAN) tier down: a CAN bus problem — see
  [CAN Bus troubleshooting](canbus.md), particularly the "node not
  responding" and "bridge segment down" sections.
- Secondary (HA) tier also down: Home Assistant itself unreachable, or the
  underlying HA sensor entity unavailable — see
  [Network / Home Assistant](network.md).
- Both down at once: usually means the CAN path failed *and* Home Assistant
  was also down/unreachable at the same time — check both independently
  rather than assuming one caused the other.

**Diagnostic steps:**

1. Check that room's `..._sensor_tier` diagnostic entity to see which tier
   is currently active.
2. If it's on Secondary, work the CAN bus checklist in
   [CAN Bus troubleshooting](canbus.md).
3. If it's in Emergency, check both the CAN path and Home Assistant/network
   connectivity — see [Network / Home Assistant](network.md).

**Fix:** Restore whichever upstream path (CAN or Home Assistant) is down;
the sensor tier recovers automatically and logs the recovery once a valid
reading is available again — no manual reset is needed.

**When to escalate:** If Primary and Secondary both look structurally fine
(bus healthy, HA reachable) and the reading is still wrong, this may be a
sensor hardware fault — see
[Room sensor board replacement](../hardware/room-sensor.md).

---

## A zone's temperature is oscillating, overshooting, or won't settle (PID tuning)

**Symptom:** A radiant or fancoil zone swings above and below its target
temperature instead of settling, or responds too slowly/too aggressively to
setpoint changes.

**Background:** Each zone actuator (radiant valve, fancoil) uses a PID
controller (a standard three-term control-loop algorithm) with **one set of
gains**. Heating and cooling share it: the controller's heat and cool outputs
are separate and are only let through in the direction the heat pump is
actually producing (`hp_mode`), so the PID cannot, for example, open a
radiant valve for cooling during the heating season. Radiant floor systems
are slow (they need gentle, patient gains); fancoils are fast (they use a
higher proportional gain but are tuned around small values — see the
defaults on [Routine Maintenance](../maintenance-tasks.md)). 🔵 DESIGNED

**Likely causes:**

- Gains too aggressive for that emitter type (most common cause of
  oscillation).
- Gains too conservative (most common cause of sluggish response/overshoot
  from a slow correction).
- Auto-tune run in the wrong season, or its result applied without halving
  (see the Fix section) — the gains come out about twice too high on loops
  that have both a heat and a cool output.

**Diagnostic steps:**

1. Confirm which mode (heat or cool) the zone is actually in when the
   problem occurs — `hp_mode` (see the seasonal-mode section below) governs
   this: a PID only drives its actuator in the direction `hp_mode` allows
   (HEAT lets the heat output through, COOL the cool output, SANITARY_ONLY
   neither), so a zone that does nothing in the wrong season is expected.
2. Watch the zone's behavior over a full heating/cooling cycle, not just a
   few minutes — radiant floors respond over hours, so short-term "swings"
   may just be normal slow settling.

**Fix:**

1. **Use auto-tune first.** The auto-tune component
   (`climate/packages/components/pid_autotune.yaml`) exists specifically to
   avoid hand-guessing gains — run it before manually adjusting numbers.
   Run it in the season the loop actually works in; on loops that have both
   a heat and a cool output, halve the gains it reports; and for a `boost`
   fancoil, set its PID to COOL by hand first (it normally sits OFF until
   the boost starts it).
2. **If tuning by hand, start conservative**: low proportional gain (Kp),
   very low integral/derivative gains (Ki/Kd), then increase gradually while
   watching for stability. It's much easier to nudge a sluggish loop up than
   to calm down an oscillating one.
3. Change one gain at a time, and re-check in the season the problem
   appears in — heat and cool share one gain set, so a change affects both.

**When to escalate:** Persistent oscillation despite conservative,
auto-tuned gains suggests a mechanical problem (e.g. a stuck valve, a pump
not running, a relay not switching) rather than a tuning problem — check the
relevant actuator via [RS485 / Modbus](rs485-modbus.md) or the matching
hardware page before continuing to adjust PID numbers.

---

## Ventilation (MEV) isn't behaving as expected

!!! warning "Known gap"
    Beyond the register map used to talk to the MEV unit over Modbus
    (`climate/mev_modbus.yaml`), this project does not yet have dedicated
    MEV troubleshooting documentation. The list below is the genuinely known
    baseline, not a full diagnostic guide — treat anything not listed here
    as unverified. ⚠️ KNOWN GAP

**What is known:**

- The MEV (mechanical extract ventilation / whole-house ventilation) unit
  sits on the climate RS485 bus at Modbus address `0x10`.
- The MEV unit is the least flexible bus member — its own factory default
  communication settings are less adjustable than the other boards on the
  bus, which matters if you're troubleshooting a bus-wide communication
  problem (see [RS485 / Modbus](rs485-modbus.md)) rather than a
  ventilation-specific one.
- The MEV exposes a large set of alarm flags and component-state sensors
  (fans, compressor, dampers, valves, filter-hours-remaining) over Modbus —
  if the unit is misbehaving, check those diagnostic entities in Home
  Assistant first, since the unit reports its own fault conditions in
  detail.
- Fan speed is demand-driven (from CO2, air-quality, and humidity signals)
  rather than fixed, so speed changing on its own in response to those
  readings is expected behavior, not a fault.

**Diagnostic steps:**

1. Check the MEV's own alarm/diagnostic entities in Home Assistant first —
   an active alarm there is the unit self-reporting a real condition
   (including forcing fan speed to zero as a safety response), not a
   communication problem.
2. If there's no active alarm but the unit seems unresponsive, treat it as
   an RS485/Modbus communication problem — see
   [RS485 / Modbus](rs485-modbus.md), particularly the "some devices work,
   others don't" section, since the MEV is often the outlier device on a
   bus that's otherwise fine.

**When to escalate:** For anything beyond the basics above, this page can't
yet give you a reliable answer — go to
[MEV unit replacement/service](../hardware/mev.md) or treat it as a bus
communication problem via [RS485 / Modbus](rs485-modbus.md).

---

## A zone won't heat or won't cool (check `hp_mode` first)

**Symptom:** A zone that should be heating (or cooling) does nothing, or
behaves as if it's in the wrong mode entirely.

**Background:** The house has **one heat pump producing either hot water or
chilled water for the whole house at a time** — there is no changeover
relay and no automatic detection of which one it's currently making. A
software setting called `hp_mode` (a select entity, not a physical control)
tells every zone's PID controller which mode to run in — heat or cool — and
it must be **manually kept in sync** with whatever the heat pump is actually
producing at the source. 🔵 DESIGNED

This means `hp_mode` doesn't *command* the heat pump — it only mirrors what
the installer/technician has set at the heat pump itself. If `hp_mode` says
"heat" while the heat pump is actually producing chilled water (or vice
versa), zones will behave incorrectly even though every piece of hardware
is working exactly as instructed.

**Likely causes:**

- `hp_mode` disagrees with what the heat pump is actually producing right
  now (by far the most common cause of "nothing happens" or "wrong
  behavior" complaints).
- `hp_mode_manual_hold` is on (its default state) and nobody has set
  `hp_mode` to match the season yet — this is expected on a freshly
  commissioned system, not a fault.

**Diagnostic steps:**

1. **Check `hp_mode` before anything else.** Confirm it matches what the
   heat pump is actually producing at the source right now — ask whoever
   manages the heat pump if you're not sure.
2. Only once `hp_mode` is confirmed correct, treat the problem as a genuine
   zone/actuator fault and move to the RS485/Modbus or PID sections above.

**Fix:** Set `hp_mode` to match the season the heat pump is actually
producing. This is a manual step by design — there is no automatic
changeover detection to rely on.

**When to escalate:** Only after `hp_mode` is confirmed correct and the zone
still won't heat/cool should you treat this as a hardware fault — check the
relevant relay/valve/pump via [RS485 / Modbus](rs485-modbus.md) or the
matching hardware page.
