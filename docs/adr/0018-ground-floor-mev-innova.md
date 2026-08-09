---
adr: 0018
title: 'Second MEV on the ground floor (Innova HRP DOMO 60 HX), ventilation-driven humidity + air quality'
status: 'Accepted'
date: '2026-08-08'
deciders: ['Alberto']
author: 'Claude'
dependsOn:
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (this MEV is a fourth member of the climate rs485_bus, and reuses the free analog channel on the existing Analog Outputs Board)'
relatedDocuments:
  - docs/adr/0014-standardized-controller-modbus-io-hardware.md
  - climate/mev_innova_modbus.yaml
  - climate/mev_demand.yaml
  - climate/packages/coordinators/mev_ventilation_fan_only.yaml
  - climate/packages/ground_floor_air_quality_max_sensor.yaml
  - climate/rooms/ground_floor/ground-floor.yaml
  - climate/home-assistant/mev_helpers.yaml
  - climate/mev_modbus.yaml
---

# ADR-0018: Second MEV on the ground floor (Innova HRP DOMO 60 HX), ventilation-driven humidity + air quality

## Status

**Accepted** (2026-08-08). Adds a second MEV unit; does not amend ADR-0014, it extends the
climate `rs485_bus` with one more commodity Modbus member and claims the last free analog
channel. Pre-live like the rest of the climate system.

**Revised before merge** (2026-08-09): the first pass treated the ground-floor MEV as
*air-quality-only* on the assumption that the fancoils fully cover humidity. Two corrections —
the fancoils dehumidify **only in summer**, and the unit is the **enthalpic HRP DOMO 60 HX** —
mean humidity is added back as a **year-round demand channel**. The unit stays passive (fan
speed is its only actuator), so there is still no active dehumidification cascade. §Decision and
§Alternatives reflect the revised design; the air-quality-only demand/coordinator variants from
the first pass were folded back into the shared 3-channel files.

## Context

The house had one MEV, on the **first floor**: a Cappellotto Air Fresh I, driven over Modbus
(`climate/mev_modbus.yaml`) with a humidity **cascade** (Fan Only → Dehumidifying →
Integration) because that unit actively dehumidifies and, in summer, adds cooling integration.

The **ground floor** now needs its own mechanical ventilation. The chosen unit is a
**different model — an Innova HRP DOMO 60 HX**, a passive heat-recovery ventilation unit with
an **enthalpic core** that transfers moisture as well as heat. Its only actuator is fan speed;
it has no active dehumidifier, compressor, or cooling integration.

Humidity handling on the ground floor:

- The **fancoils dehumidify only in summer** (cooling season) — in winter they heat and
  cannot. So humidity is *not* fully covered by the fancoils.
- The enthalpic MEV can help manage humidity through **ventilation**: raising the fan when
  indoor humidity is high, while the enthalpic core passively limits/recovers moisture on the
  incoming airstream.

So the ground-floor MEV is driven by the **full three-channel demand — CO₂, Air Quality, and
Humidity** — but with a **fan-only** coordinator (no cascade), because the hardware is passive.
The humidity channel is left **active year-round**: in summer it complements the fancoils; in
winter it is the primary humidity path.

Two further facts shaped the design:

1. **The Cappellotto register map does not transfer.** `climate/mev_modbus.yaml` encodes the
   Cappellotto's dehumidifier/compressor/water-valve/reversing-valve registers and its 39
   alarm types. A passive HRV has no counterpart for most of these. Reusing that file would
   bind switches (dehumidifier @1141, integration @1140) to registers the Innova does not have.

2. **The ground floor has no air-quality sensors yet** (but does have humidity). Ground-floor
   rooms carry live temperature/humidity, but the per-room CAN pollutant stubs
   (`${room}_{co2,voc_index,nox_index,pm1_0,pm2_5,pm4_0,pm10}_can`, declared by
   `climate/room_sensors.yaml`) read NaN until an air-quality CAN kit is fitted and registered
   for each room. The demand math NaN-degrades to the minimum-fan floor, so the air-quality
   aggregation is safe to build ahead of the sensors; the **humidity channel is functional
   immediately** because room humidity is already live.

## Decision

Add the ground-floor MEV alongside the first-floor unit, reusing the parameterized MEV stack.
The demand side is identical to the first floor (all three channels); the coordinator is
fan-only because the hardware is passive:

- **Control split.** Fan speed is a **0-10V DAC** signal on `analog_output_8` (the one free
  channel on the existing Analog Outputs Board @0x1), exactly as the first-floor MEV uses
  `analog_output_7`. Power/mode/temperatures/filter/faults are **Modbus RTU** on the existing
  `rs485_bus` at a **new slave address `0x11`** (0x1 analog, 0x2 relay, 0x10 first-floor MEV
  are taken). The unit's serial port must be set to match the bus (target 38400 8E1, ADR-0014
  §4) and to address `0x11`.
- **Demand: CO₂ + Air Quality + Humidity.** Reuses the shared `climate/mev_demand.yaml`
  unchanged. Air-quality sources are floor-level MAX aggregates
  (`climate/packages/ground_floor_air_quality_max_sensor.yaml`, instantiated seven times in
  `ground-floor.yaml`) over the five ground-floor rooms' CAN pollutant stubs. The humidity
  source is a dedicated `ground_floor_mev_max_humidity` aggregate over **all five** rooms —
  deliberately including `bagno_terra`, unlike the boost/dew-point `ground_floor_max_humidity`
  that excludes it (shower spikes): for ventilation, bathroom humidity is exactly what should
  raise the fan.
- **Coordinator: fan path only.** `climate/packages/coordinators/mev_ventilation_fan_only.yaml`
  applies the min floor and alarm/gate safety to the aggregated demand (commissioning gate → 0,
  alarm → 0, else `min(100, max(demand, min_fan))`). It carries none of the cascade — no
  humidity-state `select`, no escalate/de-escalate scripts or transition sensors, no
  dehumidifier/integration switches. It is demand-source-agnostic, so the humidity channel
  reaches the fan through the demand MAX without any cascade machinery.
- **Assembly.** `climate/mev_innova_modbus.yaml` is the Innova top-level file (slug
  `ground_floor_mev`, name `MEV Piano Terra`). It composes `mev_demand.yaml` and
  `mev_ventilation_fan_only.yaml`, defines the 0-10V fan-speed number, declares the `rs485_bus`
  member at `0x11`, and carries the Innova Modbus register bindings.
- **Independent minimum fan speed; shared bounds.** The two units are different models, so the
  ground-floor MEV gets its own `input_number.ground_floor_mev_minimum_fan_speed`. The
  air-quality and humidity lower/upper bounds are **shared** with the first-floor unit — those
  are house-wide standards, not per-floor tuning.
- **Commissioning gate.** `ground_floor_mev_enabled` defaults OFF (RESTORE_DEFAULT_OFF), so a
  freshly flashed controller leaves the unit still, consistent with the other gates.

### Register-map dependency

The Innova HRP DOMO 60 HX Modbus register map was not available at authoring time (not in the
repo — `docs/VMC MODBUS.pdf` is the *Cappellotto* manual — and `innova.it` is unreachable from
the build environment). The bus member, the 0-10V fan path, the demand aggregation and the
coordinator are complete and functional; the Innova register reads/writes in
`mev_innova_modbus.yaml` are marked `TODO(innova-register)` and must be filled from the manual
before the Modbus monitoring/control is live. Until then `ground_floor_mev_alarm_active` is a
safe `false` placeholder (the fan is never hard-off on a phantom alarm).

## Alternatives considered

- **Reuse `climate/mev_modbus.yaml` with a new address.** Rejected: it is the Cappellotto
  register map and drives dehumidifier/integration outputs the passive Innova does not have.
- **Add the full Dehumidifying → Integration cascade for humidity.** Rejected: the 60 HX has no
  active dehumidification actuator. Humidity is handled purely by modulating ventilation, so a
  demand channel (not a cascade) is the right shape.
- **Make the humidity channel winter-only (season-gated).** Considered because the fancoils
  cover summer humidity, but rejected for simplicity: an always-on humidity channel reuses
  `mev_demand.yaml` verbatim, and in summer it merely complements the fancoils rather than
  fighting them. Can be revisited if summer over-ventilation proves a problem.
- **Air-quality-only (the first-pass design).** Superseded by the enthalpic model + the
  summer-only fancoil correction; its `mev_demand_air_quality.yaml` variant was removed and the
  coordinator variant renamed `mev_ventilation_fan_only.yaml` to reflect that its distinction is
  "no cascade", not "no humidity".

## Consequences

- The climate `rs485_bus` now has four members (0x1, 0x2, 0x10, **0x11**); `analog_output_8`
  is now allocated (no free analog channels remain).
- There are two commissioning gates for ventilation (`first_floor_mev_enabled`,
  `ground_floor_mev_enabled`).
- The ground-floor MEV's **humidity** channel is live immediately (room humidity is already
  sensed); its **air-quality** channel floors at the minimum fan until ground-floor rooms get
  air-quality CAN kits and `registry/nodes.csv` entries. The firmware is ready for them.
- **Follow-up (UI):** the touch UI shows only the first-floor MEV; a ground-floor row/tab is a
  separate change.
