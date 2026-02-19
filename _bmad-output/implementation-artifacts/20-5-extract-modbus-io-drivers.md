# Story 20.5: Extract Modbus I/O Drivers

Status: done

## Story

As a **multi-zone HVAC integrator using ESPHome with Modbus expansion boards**,
I want **parameterized Modbus relay board and analog output drivers**,
so that **I can add I/O expansion to my system without writing Modbus register mappings from scratch**.

## Acceptance Criteria

1. **AC-1:** `modbus_relay_board.yaml` extracted to `packages/devices/modbus-io/` with full Vesta header
2. **AC-2:** `modbus_relay_switch.yaml` extracted to `packages/devices/modbus-io/` with full Vesta header
3. **AC-3:** `modbus_analog_output.yaml` extracted to `packages/devices/modbus-io/` with full Vesta header
4. **AC-4:** `modbus_analog_outputs_board.yaml` extracted to `packages/devices/modbus-io/` with full Vesta header
5. **AC-5:** Each component compiles standalone with only its declared parameters
6. **AC-6:** Drivers are board-agnostic (work with any Modbus relay/analog board)
7. **AC-7:** No references to esphome-devices-specific entities remain
8. **AC-8:** All parameters have header comment blocks with purpose, required vars, optional vars, example
9. **AC-9:** The Epic 19 extraction pattern is followed (header format per CONTRIBUTING.md)

## Tasks / Subtasks

- [x] Task 1: Extract `modbus_relay_switch.yaml` (AC: #2, #5, #7, #8, #9)
  - [x] 1.1: Create file with Vesta header
  - [x] 1.2: Already fully parameterized — add header docs only
- [x] Task 2: Extract `modbus_relay_board.yaml` (AC: #1, #5, #6, #7, #8, #9)
  - [x] 2.1: Create file with Vesta header
  - [x] 2.2: Change `substitutions:` → `defaults:`
  - [x] 2.3: Fix `!include` paths (`../components/` → same-directory filenames)
  - [x] 2.4: Add `controller_name` as required var
- [x] Task 3: Extract `modbus_analog_output.yaml` (AC: #3, #5, #7, #8, #9)
  - [x] 3.1: Create file with Vesta header (replace existing non-standard header)
  - [x] 3.2: Change `defaults:` var names if needed for consistency
- [x] Task 4: Extract `modbus_analog_outputs_board.yaml` (AC: #4, #5, #6, #7, #8, #9)
  - [x] 4.1: Create file with Vesta header
  - [x] 4.2: Change `substitutions:` → `defaults:`
  - [x] 4.3: Fix `!include` paths (`../components/` → same-directory filenames)
- [x] Task 5: Cross-component validation (AC: #5, #7)
  - [x] 5.1: Zero esphome-devices-specific references — verify via grep
  - [x] 5.2: All `!include` paths correct (same-directory filenames)

## Dev Notes

### Source File Analysis

- `modbus_relay_switch.yaml` (11 lines): Single relay switch via coil register. Already fully parameterized.
- `modbus_relay_board.yaml` (68 lines): 8-relay board aggregator. Uses `substitutions:` (should be `defaults:`).
- `modbus_analog_output.yaml` (81 lines): Single 0-10V output with PID integration. Has non-standard header.
- `modbus_analog_outputs_board.yaml` (61 lines): 8-channel analog board aggregator. Uses `substitutions:`.

### Key Changes from Source

1. `substitutions:` → `defaults:` in board aggregators
2. `!include` paths: `../components/modbus_relay_switch.yaml` → `modbus_relay_switch.yaml`
3. Add full Vesta headers to all 4 files
4. All files go in `vesta/packages/devices/modbus-io/`

### References

- [Source: components/modbus_relay_switch.yaml — 11 lines]
- [Source: components/modbus_relay_board.yaml — 68 lines]
- [Source: components/modbus_analog_output.yaml — 81 lines]
- [Source: components/modbus_analog_outputs_board.yaml — 61 lines]
