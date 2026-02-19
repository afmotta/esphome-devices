# Story 20.6: Documentation for New Components

Status: done

## Story

As a **Vesta user discovering the framework**,
I want **a doc page for every new component with parameter reference and usage examples**,
so that **I can understand what each component does and how to include it in my config**.

## Acceptance Criteria

1. **AC-1:** Each new component has a dedicated doc page in `docs/`
2. **AC-2:** Each doc page includes: purpose, parameter reference table, usage example
3. **AC-3:** README component table lists all 20 components with correct paths and doc links
4. **AC-4:** Getting-started guide updated to reference new component categories
5. **AC-5:** Complex components include narrative "how it works" sections

## Tasks / Subtasks

- [x] Task 1: Create doc pages for PID stack (pid, pid_sensors, pid_autotune, pid_autotune_with_fancoil)
- [x] Task 2: Create doc pages for zone components (heat_only_radiant, radiant, fancoil)
- [x] Task 3: Create doc pages for utilities (dew_point_sensor, direct_pump, mixing_pump)
- [x] Task 4: Create doc page for seasonal_mode coordinator
- [x] Task 5: Create doc pages for Modbus I/O drivers (relay board+switch, analog board+output)
- [x] Task 6: Update README component table
- [x] Task 7: Update getting-started.md

## Dev Notes

### Grouping Strategy

Some sub-components are never used standalone and are best documented alongside their parent:
- `pid_sensors.yaml` documented within `pid.md` (always auto-included by pid.yaml)
- `pid_autotune.yaml` and `pid_autotune_with_fancoil.yaml` combined in `pid-autotune.md`
- `modbus_relay_switch.yaml` documented within `modbus-relay-board.md`
- `modbus_analog_output.yaml` documented within `modbus-analog-board.md`

This gives 11 doc files covering all 15 components.

### References

- [Existing docs format: docs/trend-sensor.md]
- [README: vesta/README.md]
