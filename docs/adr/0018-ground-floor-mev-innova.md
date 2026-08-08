---
adr: 0018
title: 'Second MEV on the ground floor (Innova HRP DOMO 60 H), air-quality-only'
status: 'Accepted'
date: '2026-08-08'
deciders: ['Alberto']
author: 'Claude'
dependsOn:
  - 'ADR-0014: Standardized controller & Modbus I/O hardware (this MEV is a fourth member of the climate rs485_bus, and reuses the free analog channel on the existing Analog Outputs Board)'
relatedDocuments:
  - docs/adr/0014-standardized-controller-modbus-io-hardware.md
  - climate/mev_innova_modbus.yaml
  - climate/mev_demand_air_quality.yaml
  - climate/packages/coordinators/mev_ventilation_air_quality.yaml
  - climate/packages/ground_floor_air_quality_max_sensor.yaml
  - climate/rooms/ground_floor/ground-floor.yaml
  - climate/home-assistant/mev_helpers.yaml
  - climate/mev_modbus.yaml
---

# ADR-0018: Second MEV on the ground floor (Innova HRP DOMO 60 H), air-quality-only

## Status

**Accepted** (2026-08-08). Adds a second MEV unit; does not amend ADR-0014, it extends the
climate `rs485_bus` with one more commodity Modbus member and claims the last free analog
channel. Pre-live like the rest of the climate system.

## Context

The house had one MEV, on the **first floor**: a Cappellotto Air Fresh I, driven over Modbus
(`climate/mev_modbus.yaml`) with a humidity **cascade** (Fan Only → Dehumidifying →
Integration) because that unit actively dehumidifies and, in summer, adds cooling integration.

The **ground floor** now needs its own mechanical ventilation. The chosen unit is a
**different model — an Innova HRP DOMO 60 H**, a passive heat-recovery ventilation unit. It
renews air and recovers heat across an exchanger; it does **not** manage humidity. On the
ground floor, humidity control stays with the **fancoils** (the existing `fancoil_boost`
coordinator, unchanged). So the ground-floor MEV must be driven by **air quality only**.

Two facts shaped the design:

1. **The Cappellotto register map does not transfer.** `climate/mev_modbus.yaml` encodes the
   Cappellotto's dehumidifier/compressor/water-valve/reversing-valve registers and its 39
   alarm types. A passive HRV has no counterpart for most of these. Reusing that file would
   bind switches (dehumidifier @1141, integration @1140) to registers the Innova does not have.

2. **The ground floor has no air-quality sensors yet.** Ground-floor rooms currently carry
   only temperature/humidity. The per-room CAN pollutant stubs
   (`${room}_{co2,voc_index,nox_index,pm1_0,pm2_5,pm4_0,pm10}_can`, declared by
   `climate/room_sensors.yaml`) exist but read NaN until an air-quality CAN kit is fitted and
   registered for each room. The demand math already NaN-degrades to the minimum-fan floor, so
   the aggregation is safe to build ahead of the sensors.

## Decision

Add the ground-floor MEV as an **air-quality-only** unit alongside the first-floor unit,
reusing the parameterized MEV stack but with **new humidity-free variants** rather than
mutating the shared files:

- **Control split.** Fan speed is a **0-10V DAC** signal on `analog_output_8` (the one free
  channel on the existing Analog Outputs Board @0x1), exactly as the first-floor MEV uses
  `analog_output_7`. Power/mode/temperatures/filter/faults are **Modbus RTU** on the existing
  `rs485_bus` at a **new slave address `0x11`** (0x1 analog, 0x2 relay, 0x10 first-floor MEV
  are taken). The unit's serial port must be set to match the bus (target 38400 8E1, ADR-0014
  §4) and to address `0x11`.
- **Demand: air quality only.** `climate/mev_demand_air_quality.yaml` aggregates two top-level
  channels — CO₂ and Air Quality (the MAX of the six pollutant sub-channels) — with **no
  humidity channel**. Sources are new floor-level MAX aggregates
  (`climate/packages/ground_floor_air_quality_max_sensor.yaml`, instantiated seven times in
  `ground-floor.yaml`) over the five ground-floor rooms' CAN pollutant stubs. There is no
  ground-floor air-quality-MAX humidity aggregate.
- **Coordinator: fan path only.** `climate/packages/coordinators/mev_ventilation_air_quality.yaml`
  keeps the humidity-independent fan path (commissioning gate → 0, alarm → 0, else
  `min(100, max(demand, min_fan))`) and drops the entire cascade: the humidity-state `select`,
  the escalate/de-escalate scripts and transition sensors, and the dehumidifier/integration
  switches.
- **Assembly.** `climate/mev_innova_modbus.yaml` is the Innova top-level file (slug
  `ground_floor_mev`, name `MEV Piano Terra`). It composes the two variants, defines the 0-10V
  fan-speed number, declares the `rs485_bus` member at `0x11`, and carries the Innova Modbus
  register bindings.
- **Independent minimum fan speed.** The two units are different models, so the ground-floor
  MEV gets its own `input_number.ground_floor_mev_minimum_fan_speed`. The pollutant
  lower/upper bounds are **shared** with the first-floor unit — those are house-wide
  air-quality standards, not per-floor tuning.
- **Commissioning gate.** `ground_floor_mev_enabled` defaults OFF (RESTORE_DEFAULT_OFF), so a
  freshly flashed controller leaves the unit still, consistent with the other gates.

### Register-map dependency

The Innova HRP DOMO 60 H Modbus register map was not available at authoring time (not in the
repo — `docs/VMC MODBUS.pdf` is the *Cappellotto* manual — and `innova.it` is unreachable from
the build environment). The bus member, the 0-10V fan path, the demand aggregation and the
coordinator are complete and functional; the Innova register reads/writes in
`mev_innova_modbus.yaml` are marked `TODO(innova-register)` and must be filled from the manual
before the Modbus monitoring/control is live. Until then `ground_floor_mev_alarm_active` is a
safe `false` placeholder (the fan is never hard-off on a phantom alarm).

## Alternatives considered

- **Reuse `climate/mev_modbus.yaml` with a new address.** Rejected: it is the Cappellotto
  register map and drives dehumidifier/integration outputs the Innova does not have.
- **Keep the humidity channel but feed it a NaN dummy.** Rejected: leaves phantom
  `humidity_demand`/`humidity_rate`/`humidity_lower` entities and a "Humidity" dominant-demand
  option on a unit that, by design, does not manage humidity.
- **Slug-scope every HA helper (own pollutant bounds too).** Deferred: air-quality thresholds
  are floor-independent; only the minimum fan speed is genuinely per-unit. Easy to split later
  if a ground-floor-specific bound is ever wanted.

## Consequences

- The climate `rs485_bus` now has four members (0x1, 0x2, 0x10, **0x11**); `analog_output_8`
  is now allocated (no free analog channels remain).
- There are two commissioning gates for ventilation (`first_floor_mev_enabled`,
  `ground_floor_mev_enabled`).
- **Follow-up (hardware/registry):** real air-quality demand on the ground floor needs
  air-quality CAN sensor kits and `registry/nodes.csv` entries for the five ground-floor
  rooms; until then the unit floors at its minimum fan speed. The firmware is ready for them.
- **Follow-up (UI):** the touch UI shows only the first-floor MEV; a ground-floor row/tab is a
  separate change.
