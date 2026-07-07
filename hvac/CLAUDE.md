# HVAC (Climate Control) Subsystem — AI Assistant Guide

This is the HVAC application system (layered-restructure spine,
`_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`).
It is **pre-live**: controller hardware is not yet finalized (a master-controller
swap is under consideration). Everything below is scoped to `hvac/`; entry
points that compose HVAC packages (`devices/climate-control.yaml`, its
`devices/locals/` and `devices/remotes/` deployment variants) stay in
`devices/` (entry points and their variants live together).

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

## PID Control Architecture

**Dual PID Pattern**: Each zone has two PID controllers - one for heat mode, one for cool mode.

```yaml
climate:
  # Heat mode PID
  - platform: pid
    id: pid_heat_${room_slug}
    name: "PID Heat ${room_name}"
    sensor: ${temperature_sensor}
    control_parameters:
      kp: 0.8
      ki: 0.005
      kd: 0.05

  # Cool mode PID
  - platform: pid
    id: pid_cool_${room_slug}
    name: "PID Cool ${room_name}"
    sensor: ${temperature_sensor}
    control_parameters:
      kp: 1.2
      ki: 0.008
      kd: 0.08
```

**Mode Synchronization**: All zones switch between heat/cool modes simultaneously based on a master mode register (Modbus register 200).

## Modbus Communication Architecture

**Master/Slave Pattern**:
- **Master** (KC868-A6): Polls room sensors, writes to registers, coordinates mode
- **Slaves** (KC868-A16): Read from master registers, control local zones

**Register Map** (simplified):
- `200`: Climate mode (0=off, 1=heat, 2=cool)
- `300`: Master heartbeat counter
- `400-407`: Ground floor room sensor data (temp/humidity)
- `408-415`: First floor room sensor data

**Polling Intervals**:
- Master polls sensors: 30 seconds
- Slaves read from master: 10 seconds
- Heartbeat increment: 10 seconds

## Common Tasks

### Adding a New Room

1. Create room config file in `hvac/rooms/[floor]/[room_name].yaml`
2. Include sensor, radiant, fancoil packages with room-specific vars
3. Add room package to floor aggregator (`[floor]-floor.yaml`)
4. Assign relay numbers (ensure no conflicts)
5. Add Modbus register mappings if using remote sensors
6. Test compilation
7. Deploy and verify

Example:
```yaml
# hvac/rooms/ground_floor/new_room.yaml
defaults:
  room_slug: new_room
  room_name: "New Room"
  temperature_sensor: sensor.new_room_temp
  radiant_relay: relay_6
  fancoil_relay: relay_10

packages:
  sensors: !include ../../room_sensors.yaml
  radiant: !include ../../radiant.yaml
  fancoil: !include ../../fancoil.yaml
```

### Modifying PID Parameters

PID parameters are set at component inclusion:

```yaml
packages:
  pid: !include
    file: pid.yaml
    vars:
      circuit_slug: "radiant_soggiorno"
      circuit_name: "Radiant Soggiorno"
      sensor: sensor.soggiorno_temp
      kp: 0.8      # Proportional gain
      ki: 0.005    # Integral gain
      kd: 0.05     # Derivative gain
```

**Auto-tuning** is available via `pid_autotune.yaml` component.

### Adding Modbus Devices

1. Determine Modbus address (must be unique on bus)
2. Add to appropriate board's `modbus_controller` list
3. Create component package with register mappings
4. Include component in device config with parameters
5. Verify RS485 wiring (A to A, B to B, proper termination)

### Debugging Modbus Issues

```yaml
# Enable verbose modbus logging
logger:
  level: DEBUG
  logs:
    modbus_controller: DEBUG
    modbus: DEBUG
```

Common issues:
- Wrong baud rate (must be 9600)
- Incorrect address
- Missing termination resistors
- Swapped A/B wires
- Too many devices on bus (> 30)

## Appendices

### A. Modbus Register Quick Reference

| Range | Purpose | Data Type |
|-------|---------|-----------|
| 200 | Climate mode (0=off, 1=heat, 2=cool) | uint16 |
| 300 | Master heartbeat counter | uint16 |
| 400-407 | Ground floor room sensors (temp/humidity pairs) | int16 (scaled ×100) |
| 408-415 | First floor room sensors | int16 (scaled ×100) |

### B. Relay Assignment Reference

**Ground Floor Distribution Board (A16, Address 0x02)**:
- Relays 1-4: Zone radiant floor circuits
- Relays 5-8: Fancoil units
- Relays 9-12: (Reserved/future use)
- Relays 13-16: Pumps and auxiliary

**First Floor Distribution Board (A16, Address 0x03)**:
- Relays 1-8: Zone radiant floor circuits
- Relays 9-12: Fancoil units
- Relays 13-16: MEV and auxiliary

### C. Sensor Address Assignments

| Device | Modbus Address | Location |
|--------|---------------|----------|
| Master A6 | 0x01 | Technical room |
| Slave A16 #1 | 0x02 | Ground floor |
| Slave A16 #2 | 0x03 | First floor |
| Room sensor Soggiorno | 0x0A (10) | Living room |
| Room sensor Cucina | 0x0B (11) | Kitchen |
| Room sensor Bagno | 0x0C (12) | Bathroom |
| Room sensor Anticamera | 0x0D (13) | Entry hall |
| 0-10V Adapter | 0x1E (30) | Second floor fancoil |

### D. PID Tuning Guidelines

**Radiant Floor (Slow System)**:
- Kp: 0.5 - 1.0 (start at 0.8)
- Ki: 0.001 - 0.01 (start at 0.005)
- Kd: 0.01 - 0.1 (start at 0.05)

**Fancoil (Fast System)**:
- Kp: 1.0 - 2.0 (start at 1.2)
- Ki: 0.005 - 0.02 (start at 0.008)
- Kd: 0.05 - 0.2 (start at 0.08)

**Cooling Mode** (typically needs higher gains than heating):
- Increase all parameters by 20-50%
- Cooling has faster response due to air circulation

### Debugging Modbus and PID issues

**Modbus Issues**:
- Enable DEBUG logging for `modbus_controller`
- Check register addresses and data types
- Verify baud rate (9600, 8N1)
- Inspect RS485 wiring and termination

**PID Tuning**:
- Use auto-tune feature first (`pid_autotune.yaml`)
- Start with conservative gains (low Kp, very low Ki/Kd)
- Increase gradually while monitoring stability
- Different gains for heat vs. cool modes

## The room_slug contract with canbus

`registry/nodes.csv`'s `room_slug` column (spec-map-json-contract) joins a
CAN-bus wall-button node to a climate zone. The known-zone list is read from
this directory's room files (`hvac/rooms/**`, by file *contents* not
filenames — `ground_floor/bagno.yaml` declares `bagno_terra`) by
`canbus/tools/generate_nodes.py`'s `load_climate_zones()`, so it
can't drift as rooms are added, renamed, or removed. hvac only reads
`registry/map.json`; it never writes the registry (ADR-0009 §7 authority
boundary).

## Conventions

- Epic prefix: **HVAC-**. New BMAD artifacts go to the root `_bmad-output/`.
- File naming follows root `CLAUDE.md`'s general conventions (kebab-case device
  configs, `[component_type]_[variant].yaml` for component configs); this file
  is the sole owner of HVAC-specific rules — entity-ID convention, PID
  architecture, Modbus register/relay appendices, and PID/Modbus "Common
  Tasks" all live here, not in root `CLAUDE.md` (AD-10).
