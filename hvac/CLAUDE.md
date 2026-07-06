# HVAC (Climate Control) Subsystem — AI Assistant Guide

This is the HVAC application system (layered-restructure spine,
`_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`).
It is **pre-live**: controller hardware is not yet finalized (a master-controller
swap is under consideration). Everything below is scoped to `hvac/`; entry
points that compose HVAC packages (`devices/climate-control.yaml`, its
`locals/`/`remotes/` variants) stay in `devices/` per AD-4.

## What's here

- `rooms/` — room and floor-aggregator configs (13 rooms across 3 floors),
  each including PID/radiant/fancoil packages from `vesta/packages/components/`
- `mev_modbus.yaml`, `mev_demand.yaml` — MEV (Mechanical Extract Ventilation)
  Modbus driver and demand aggregation
- `room_sensors.yaml` — room sensor failover wiring
- `home-assistant/dashboards/` — hand-authored Lovelace dashboards (Phase 3)

## Entity ID Naming Convention

**Pattern**: `{scope}_{component}[_{mode}][_{aspect}]`

| Position | Dimension | Required | Examples |
|----------|-----------|----------|---------|
| 1st | Scope | Yes | `soggiorno`, `cucina`, `camera_nord`, `ground_floor` |
| 2nd | Component | Yes | `radiant`, `fancoil`, `mev`, `pump`, `mixing` |
| 3rd | Mode | Optional | `heat`, `cool`, `pid`, `boost` |
| 4th | Aspect | Optional | `output`, `setpoint`, `kp`, `ki`, `kd`, `status` |

**Rules**:
1. Room names are atomic tokens (`camera_nord` is one slug, not two dimensions)
2. Floor scope is only used when no room applies (entity is floor-scoped)
3. Board-level hardware entities (`relay_1`, `dac_output_1`) are excluded — they keep their own convention
4. Each dimension is always a single underscore-delimited token
5. Convention applies to entity IDs only — file names and variable names are separate concerns

**Example Entity IDs**:

```
# Room-scoped radiant floor control
soggiorno_radiant                    # Radiant floor switch/output
soggiorno_radiant_pid                # PID climate entity
soggiorno_radiant_pid_output         # PID output value
soggiorno_radiant_pid_setpoint       # PID target temperature
soggiorno_radiant_pid_kp             # PID proportional gain
soggiorno_radiant_override           # Manual override switch
soggiorno_radiant_override_value     # Manual override percentage
soggiorno_radiant_pwm                # Slow PWM relay driver

# Room-scoped fancoil control
soggiorno_fancoil_pid                # Fancoil PID climate entity
soggiorno_boost_state                # Boost coordinator state
soggiorno_boost_active               # Boost active flag
soggiorno_temp_delta                  # Temperature delta from setpoint
soggiorno_temp_trend                  # Temperature rate of change

# Room-scoped sensors (failover tiers)
soggiorno_temp_udp                   # UDP temperature (primary)
soggiorno_temp_ha                    # Home Assistant temperature (fallback)
soggiorno_temp_abstracted            # Failover-resolved temperature
soggiorno_humidity_abstracted        # Failover-resolved humidity
soggiorno_dew_point                  # Calculated dew point
soggiorno_sensor_tier                # Active failover tier

# Floor-scoped aggregates
ground_floor_radiant_any_zone_open   # Any radiant zone active
ground_floor_max_dew_point           # Max dew point for protection
ground_floor_fancoil_boost_threshold # Boost activation threshold

# Floor-scoped MEV
first_floor_mev_fan_speed            # MEV fan speed control
first_floor_mev_co2_demand           # CO2-based demand signal
first_floor_mev_alarm_active         # Master alarm indicator
```

**Key Insight**: PID is a *mode of operation* ("radiant under PID control"), not a separate component. This keeps the model flat with a maximum of 4 segments.

**Italian Terms** (used throughout):
- `soggiorno` = living room
- `cucina` = kitchen
- `bagno` = bathroom
- `camera` = bedroom
- `anticamera` = entry hall
- `lavanderia` = laundry room
- `sottotetto` = attic
- `locale_tecnico` = technical room
- `piano_terra` = ground floor
- `primo_piano` = first floor
- `secondo_piano` = second floor

## The room_slug contract with canbus

`registry/nodes.csv`'s `room_slug` column (spec-map-json-contract) joins a
CAN-bus wall-button node to a climate zone. The known-zone list is read from
this directory's room files (`hvac/rooms/**`, by file *contents* not
filenames — `ground_floor/bagno.yaml` declares `bagno_terra`) by
`canbus/firmware/tools/generate_nodes.py`'s `load_climate_zones()`, so it
can't drift as rooms are added, renamed, or removed. hvac only reads
`registry/map.json`; it never writes the registry (ADR-0009 §7 authority
boundary).

## Conventions

- Epic prefix: **HVAC-**. New BMAD artifacts go to the root `_bmad-output/`.
- File naming and package composition patterns are documented in root
  `CLAUDE.md` pending its Phase 6 rewrite into a per-system map.
