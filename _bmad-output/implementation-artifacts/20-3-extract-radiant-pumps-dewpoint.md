# Story 20.3: Extract Heat-Only Radiant, Pumps & Dew Point

Status: done

## Story

As a **multi-zone HVAC integrator using ESPHome**,
I want **reusable packages for pump control and dew point calculation**,
so that **I can compose these building blocks into my system without writing boilerplate YAML**.

## Acceptance Criteria

1. **AC-1:** `mixing_pump.yaml` extracted to `packages/components/` with full Vesta header
2. **AC-2:** `direct_pump.yaml` extracted to `packages/components/` with full Vesta header
3. **AC-3:** `dew_point_sensor.yaml` extracted to `packages/components/` with full Vesta header
4. **AC-4:** Each component compiles standalone with only its declared parameters
5. **AC-5:** No component references esphome-devices-specific entities
6. **AC-6:** All parameters have header comment blocks with purpose, required vars, optional vars, example
7. **AC-7:** The Epic 19 extraction pattern is followed (header format per CONTRIBUTING.md)
8. **AC-8:** `heat_only_radiant.yaml` is confirmed already present (extracted in Story 20.2)

## Tasks / Subtasks

- [x] Task 1: Extract `mixing_pump.yaml` (AC: #1, #4, #5, #6, #7)
  - [x] 1.1: Create `vesta/packages/components/mixing_pump.yaml` with full Vesta header
  - [x] 1.2: Parameterized `one_wire_id` → `${one_wire_bus_id}` as required var
  - [x] 1.3: Parameterized dallas_temp sensor with `dallas_address` and `one_wire_bus_id`
  - [x] 1.4: PID gains as optional with defaults (kp: 0.2, ki: 0.01, kd: 0.0)
  - [x] 1.5: Updated `!include` path (`./pid.yaml` → `pid.yaml`)
  - [x] 1.6: Documented dependency chain: pid.yaml → pid_sensors.yaml
- [x] Task 2: Extract `direct_pump.yaml` (AC: #2, #4, #5, #6, #7)
  - [x] 2.1: Create `vesta/packages/components/direct_pump.yaml` with full Vesta header
  - [x] 2.2: Copied logic — fully parameterized
- [x] Task 3: Extract `dew_point_sensor.yaml` (AC: #3, #4, #5, #6, #7)
  - [x] 3.1: Create `vesta/packages/components/dew_point_sensor.yaml` with full Vesta header
  - [x] 3.2: Copied Magnus formula logic
  - [x] 3.3: Added optional vars `update_interval` (default: 30s) and `accuracy_decimals` (default: 0)
- [x] Task 4: Confirm `heat_only_radiant.yaml` presence (AC: #8)
  - [x] 4.1: Verified `vesta/packages/components/heat_only_radiant.yaml` exists (4593 bytes, from Story 20.2)
- [x] Task 5: Cross-component validation (AC: #4, #5)
  - [x] 5.1: Zero esphome-devices-specific references — verified via grep
  - [x] 5.2: All `!include` paths correct (same-directory filenames)

## Dev Notes

### Architecture Context

This story extracts 3 remaining components (mixing_pump, direct_pump, dew_point_sensor). `heat_only_radiant.yaml` was already extracted in Story 20.2 as a prerequisite for `radiant.yaml`.

### Source File Analysis

**`components/mixing_pump.yaml` (51 lines):**
- Includes a Dallas temperature sensor for the mixing valve supply temperature
- Includes PID controller for mixing valve position control
- Binary sensor wraps a trigger signal to control pump relay on/off
- **MUST PARAMETERIZE:** `one_wire_id: one_wire_01` is hardcoded — needs `one_wire_bus_id` var
- Dependencies: pid.yaml

**`components/direct_pump.yaml` (20 lines):**
- Simple binary sensor wrapper that turns a relay on/off based on a trigger signal
- No dependencies, fully parameterized
- Uses: `sensor_id`, `area_name`, `relay_id`

**`components/dew_point_sensor.yaml` (17 lines):**
- Magnus formula dew point calculation from temperature + humidity sensors
- No dependencies, fully parameterized
- Uses: `room_slug`, `room_name`, `humidity_sensor`, `temperature_sensor`

### Generalization Notes

1. **mixing_pump `one_wire_id`:** The Dallas sensor's `one_wire_id` is hardcoded to `one_wire_01`. For Vesta, add `one_wire_bus_id` as required var.
2. **mixing_pump variable names:** Source uses `area_slug`/`area_name`. Keep these — they're more generic than `room_slug` since pumps serve areas (floors), not individual rooms.
3. **dew_point_sensor naming:** Source uses `room_slug`/`room_name`. Keep consistent with other room-level components.

### Previous Story (20.2) Learnings

- Keep `room_slug`/`room_name` consistent across components at the same abstraction level
- Document dependency chains fully (including transitive deps like pid → pid_sensors)
- Add comments for implicit var passthrough in layered includes

### Project Structure Notes

- All new files go in `vesta/packages/components/`
- `!include` paths within components use just filenames (same directory)

### References

- [Source: components/mixing_pump.yaml — 51 lines, needs one_wire_id parameterization]
- [Source: components/direct_pump.yaml — 20 lines, fully parameterized]
- [Source: components/dew_point_sensor.yaml — 17 lines, fully parameterized]
- [Source: vesta/CONTRIBUTING.md — header format]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 20.3]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
N/A

### Completion Notes List
- 3 new component files created
- mixing_pump: parameterized `one_wire_id` (was hardcoded `one_wire_01`)
- dew_point_sensor: added optional `update_interval` and `accuracy_decimals` vars
- heat_only_radiant confirmed present from Story 20.2
- Zero esphome-devices-specific references

### Change Log
- Created 3 component files (2026-02-19)

### File List
- vesta/packages/components/mixing_pump.yaml (new)
- vesta/packages/components/direct_pump.yaml (new)
- vesta/packages/components/dew_point_sensor.yaml (new)
