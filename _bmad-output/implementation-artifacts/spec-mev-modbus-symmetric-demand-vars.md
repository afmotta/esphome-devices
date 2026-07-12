---
title: 'MEV Modbus Symmetric Demand Vars'
type: 'refactor'
created: '2026-07-12'
status: 'done'
route: 'one-shot'
---

# MEV Modbus Symmetric Demand Vars

## Intent

**Problem:** `hvac/mev_modbus.yaml` exposed only `humidity_sensor` as a caller-provided demand input while hardcoding the CO2, VOC, NOx, PM1.0, PM2.5, PM4.0, and PM10 aggregate sensors to first-floor IDs. That made the package contract asymmetric and prevented reuse by any non-first-floor MEV composition.

**Approach:** Make every MEV demand input explicit at the `mev_modbus.yaml` boundary and pass those vars through to `mev_demand.yaml`. Keep the current first-floor behavior by supplying the same first-floor aggregate IDs from the first-floor caller.

## Suggested Review Order

1. [../../hvac/mev_modbus.yaml](../../hvac/mev_modbus.yaml) -- Package contract: all demand sensor inputs are required vars and passed through symmetrically.
2. [../../hvac/rooms/first_floor/first-floor.yaml](../../hvac/rooms/first_floor/first-floor.yaml) -- Caller wiring: current first-floor aggregate IDs are supplied explicitly.

## Verification

**Commands:**
- `esphome config devices/locals/climate-control.yaml` -- expected: `INFO Configuration is valid!`

## Review Notes

Blind review produced one patch applied: clarify the MEV package doc comments with concrete examples for all demand sensor vars. Other findings were rejected as pre-existing architecture commentary or false positives for ESPHome merged-package ID resolution; no deferred work was created from this one-shot change.

## Follow-Up Change Log

### 2026-07-12 — PM1.0/PM4.0 demand vars
- Trigger: User asked to include PM1.0 and PM4.0 in air-quality demand after the previous v1 diagnostic-only decision was revisited.
- Change: MEV Modbus now exposes and passes `pm1_0_sensor` and `pm4_0_sensor` alongside the other pollutant aggregate vars.
