# Story 20.7: Migrate esphome-devices to Vesta

Status: done

## Story

As the **esphome-devices system operator**,
I want **the production system updated to consume Vesta packages via local includes from the vesta/ directory**,
so that **there are no local duplicates of migrated components and the system validates that Vesta works as a dependency**.

## Acceptance Criteria

1. **AC-1:** All room configs and device configs reference Vesta packages instead of local component files
2. **AC-2:** All 20 local component files migrated to Vesta are removed from components/
3. **AC-3:** Components that remain local (room_sensors, mev_modbus, mev_demand) are unaffected
4. **AC-4:** Entity ID changes (summer_mode → hp_mode_summer) are updated in all references

## Tasks / Subtasks

- [x] Task 1: Update devices/climate-control.yaml
  - [x] 1.1: Add seasonal_mode_id and time_id to defaults
  - [x] 1.2: Update modbus board includes to vesta paths
  - [x] 1.3: Update seasonal_mode include to vesta path with new required vars
- [x] Task 2: Update floor aggregators
  - [x] 2.1: ground-floor.yaml — mixing_pump, direct_pump to vesta paths + add one_wire_bus_id
  - [x] 2.2: first-floor.yaml — mixing_pump to vesta path + add one_wire_bus_id
  - [x] 2.3: second-floor.yaml — direct_pump to vesta path
  - [x] 2.4: Update summer_mode references to hp_mode_summer in floor aggregators
- [x] Task 3: Update room files (15 rooms)
  - [x] 3.1: radiant/heat_only_radiant includes → vesta paths
  - [x] 3.2: fancoil includes → vesta paths
  - [x] 3.3: pid_autotune includes → vesta paths (add boost_active_global where needed)
  - [x] 3.4: fancoil_boost_coordinator → vesta fancoil_boost (soggiorno, cucina) with explicit vars
- [x] Task 4: Update room_sensors.yaml internal includes
  - [x] 4.1: failover_sensor → vesta path
  - [x] 4.2: dew_point_sensor → vesta path
- [x] Task 5: Remove 20 migrated files from components/
- [x] Task 6: Update mev_modbus.yaml cooling_mode_sensor: summer_mode → hp_mode_summer

## Dev Notes

### Entity ID Changes

- `summer_mode` → `hp_mode_summer` (referenced in ground-floor.yaml, first-floor.yaml)
- `season_classification` → `hp_mode_season`
- `check_calendar_gates` script → `hp_mode_check_calendar`
- `check_demand_transitions` script → `hp_mode_check_demand`

### New Required Vars

- `seasonal_mode_id: hp_mode` — added to climate-control.yaml defaults
- `time_id: pcf85063_time` — added to seasonal_mode include
- `one_wire_bus_id: one_wire_01` — added to mixing_pump includes
- `boost_active_global` — added to pid_autotune_with_fancoil includes

### Files to Remove (20)

Epic 19: trend_sensor, failover_sensor, proportional_demand_sensor, fancoil_boost_coordinator, mev
Epic 20: pid, pid_sensors, pid_autotune, pid_autotune_with_fancoil, radiant, heat_only_radiant, fancoil, mixing_pump, direct_pump, dew_point_sensor, seasonal_mode, modbus_relay_board, modbus_relay_switch, modbus_analog_output, modbus_analog_outputs_board

### Files Staying Local

- room_sensors.yaml (esphome-devices-specific 3-tier failover)
- mev_modbus.yaml (esphome-devices-specific)
- mev_demand.yaml (esphome-devices-specific)
