# Confidence Ledger

Almost nothing in this house has been tested in the field yet — the system is
"pre-live" (designed and largely built, but not physically installed). Every page on
this site tags its non-trivial claims 🟢 **VERIFIED**, 🔵 **DESIGNED**, or
⚠️ **KNOWN GAP** (see the [Glossary](glossary.md) for the full definitions). This page
is the master list of those tags in one place: every 🔵 DESIGNED claim that should be
flipped to 🟢 VERIFIED once someone confirms it against real hardware, and every
named ⚠️ KNOWN GAP that still needs an answer.

!!! note "This is a living document"
    If you field-test something on this list, update its row here (and on whichever
    page carries the original claim) rather than leaving both stale. If you find a
    🔵 DESIGNED claim on another page that isn't listed here yet, add it — that's the
    point of this page.

## Discrepancies (higher priority than a plain gap)

These aren't just unverified — the documentation and the actual code disagree with
each other, which is worse than a simple gap because it can mislead someone who
trusts the wrong source.

| Claim | The discrepancy | Status |
|---|---|---|
| Emergency sensor-failover "safe shutdown" timing | The root `CLAUDE.md` states the emergency tier "triggers safe shutdown **after 5 minutes**." The actual failover logic (`climate/packages/components/failover_sensor.yaml`) returns `NAN` (not-a-number) **immediately** once both the primary and secondary sensor sources are unavailable — there is no 5-minute timer anywhere in that file, and no timeout constant for it elsewhere in `climate/packages/`. It's not known whether some *downstream* consumer of the NaN value (a PID controller, a coordinator) independently waits 5 minutes before acting on it, or whether "5 minutes" is simply an inaccurate figure in the documentation. | ⚠️ **Unresolved discrepancy** — needs bench measurement of what actually happens end-to-end when a zone's sensor value goes NaN, and then either the code needs a real timer added or the "5 minutes" documentation needs correcting to match reality. Do not rely on a 5-minute grace period existing until this is resolved. |

## 🔵 DESIGNED claims awaiting field verification

| Claim | Where it's used | Source |
|---|---|---|
| CAN node in-place reflash (~5–10 min), board swap ("minutes per node"), and whole-house campaign (~2–3 working days) time estimates | [CAN Node replacement](../hardware/can-node.md) | `canbus/docs/reflash-campaign-runbook.md`, which explicitly marks its own time-budget table **"STUB — pending bench-timing"** and says the numbers are unvalidated estimates that must be measured on the bench before they can be trusted for planning. |
| A CAN node is declared "lost" after 3 missed heartbeats (90 seconds of silence) | [CAN Bus troubleshooting](../troubleshooting/canbus.md) | Implemented and covered by automated logic tests, but not yet exercised against a real bench or field failure. |
| The CAN bridge fails safe (goes silent rather than jamming the bus) and self-recovers from hangs via a hardware watchdog | [CAN Bus troubleshooting](../troubleshooting/canbus.md) | Built and intended to work this way; not yet proven against a real bridge fault. |
| The `ha_ready` gate's three-condition readiness logic (API connection, fresh heartbeat, matching binding-manifest hash) | [CAN Bus troubleshooting](../troubleshooting/canbus.md) | Implemented; not yet exercised against a real Home Assistant outage in the field. |
| Every fielded CAN node has USB access without needing to be unmounted or rewired | [CAN Node replacement](../hardware/can-node.md) | A design requirement (ADR-0008 §3), verified per-node only at installation time — not yet true of any node, since none are installed. |
| RS485 bus parity agreement: both the climate bus and the lighting bus can run all their devices at the target 38400 8E1 setting | [Hardware & Address Table](hardware-table.md), [RS485/Modbus troubleshooting](../troubleshooting/rs485-modbus.md) | Target configuration per ADR-0014 §4; pending a physical bring-up check, since the ventilation (MEV) unit is the least flexible bus member and is the binding constraint if it can't run at that setting. |
| Manually pulsing each relay/analog channel will confirm the wiring/actuator map matches the [relay assignment table](hardware-table.md) | `docs/climate-deployment-runbook.md` Phase 0.1 | The mapping is designed and documented; it has never been checked against physical wiring because the physical wiring doesn't exist yet. |
| MEV ventilation demand cascade (Fan Only → Dehumidifying → Integration) and the "any alarm forces fan to zero" safety hold | `docs/climate-deployment-runbook.md` Phase 0.2 | Implemented in `climate/mev_demand.yaml`/`mev_modbus.yaml`; not yet run against a real MEV unit. |
| Fancoil boost anti-cycling and clean handoff back to "Radiant Only" | `docs/climate-deployment-runbook.md` Phase A-C4 | Implemented in the boost coordinator; not yet run against real hardware. |
| Window-guard sensor logic self-activates when mapped and stays a safe no-op when unmapped or when Home Assistant is down | `climate/packages/components/window_guard.yaml`, `docs/climate-deployment-runbook.md` Phase C | Designed to degrade safely; not yet exercised against a real window sensor or a real Home Assistant outage. |
| DS2484 I²C-to-1-Wire bridge (address `0x18`) does not collide with the onboard touch controller on the shared I²C bus | ADR-0014 §5 | Flagged as an open item in the ADR itself, to be confirmed at hardware bring-up. |
| The on-hand Waveshare board really is the RS485-CAN variant with a CAN transceiver wired to GPIO15/16, and the second CAN tap it adds to the backbone doesn't need a termination change | ADR-0015 open items 1–3 | Assumed from the previous (pre-split) gateway board's known wiring; not yet bench-confirmed on the actual board. |

## ⚠️ Named KNOWN GAPs (no answer yet, stated plainly)

| Gap | Detail | Where it surfaces |
|---|---|---|
| Spare-stock policy | How many pre-flashed spare CAN boards should sit on the shelf for the board-swap replacement path, and under what `node_id` allocation discipline. Recorded verbatim in `canbus/_bmad-output/implementation-artifacts/deferred-work.md` as an open item of ADR-0008: *"Spare-stock policy (ADR-0008 open item 4) [ops / commissioning] — how many pre-flashed spare boards sit on the shelf for the board-swap path, and at what `node_id` allocation discipline (ADR-0007 id space). Supports `docs/reflash-campaign-runbook.md` Path B."* No answer has been recorded anywhere yet. | CAN node board-swap replacement |
| No hardware-replacement procedure for the MEV unit | No documented procedure exists anywhere in the repository for physically replacing the ventilation (MEV) unit itself — only for the Modbus wiring/communication side of it. | [MEV Unit](../hardware/mev.md) |
| No hardware-replacement procedure for room-sensor boards | No documented procedure exists for physically replacing an S1 Pro Multi-Sense board or a wall-mounted sensor board (the ones behind [Room Sensor Board](../hardware/room-sensor.md)) — only for the sensor data's software failover path. | [Room Sensor Board](../hardware/room-sensor.md) |
| Real RS485 cable lengths for this house | Cable-length guidance on the [RS485/Modbus troubleshooting page](../troubleshooting/rs485-modbus.md) is based on the RS485 standard's general limits, not on any measurement of this house's actual wiring runs, because the physical installation hasn't happened yet. | RS485/Modbus troubleshooting |

## Related

- [Glossary](glossary.md) — defines the 🟢/🔵/⚠️ tag system used across this site.
- [Document Map](doc-map.md) — for finding the underlying source document behind any
  claim listed here.
- [Hardware & Address Table](hardware-table.md) — several rows above reference its
  bus-parameter and relay-assignment claims.
