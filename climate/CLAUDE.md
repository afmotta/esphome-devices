# Climate Subsystem — AI Assistant Guide

This is the Climate application system (layered-restructure spine,
`_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`).
It is **pre-live**: the controller hardware decision is finalized (ADR-0014 — LilyGO
T-Connect Pro + Modbus RTU I/O boards, implemented) but not yet physically deployed.
Everything below is scoped to `climate/`; entry
points that compose Climate packages (`devices/climate-control.yaml`, its
`devices/locals/` and `devices/remotes/` deployment variants) stay in
`devices/` (entry points and their variants live together).

## What's here

- `rooms/` — room and floor-aggregator configs (13 rooms across 3 floors),
  each including PID/radiant/fancoil packages from `climate/packages/components/`
- `packages/components/`, `packages/coordinators/` — Climate-owned reusable ESPHome
  packages for PID/radiant/fancoil/failover/demand logic and orchestration
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
soggiorno_temp_can                   # CAN temperature (primary)
soggiorno_temp_ha                    # Home Assistant temperature (fallback)
soggiorno_temp_abstracted            # Failover-resolved temperature
soggiorno_humidity_abstracted        # Failover-resolved humidity
soggiorno_dew_point                  # Calculated dew point
soggiorno_temp_abstracted_sensor_tier # Active failover tier

# Floor-scoped aggregates
ground_floor_radiant_any_zone_open   # Any radiant zone active
ground_floor_max_dew_point           # Max dew point for protection
ground_floor_fancoil_boost_threshold # Boost activation threshold

# Floor-scoped MEV
first_floor_mev_fan_speed            # MEV fan speed control
first_floor_mev_co2_demand           # CO2-based demand signal
first_floor_mev_air_quality_demand   # MAX of VOC/NOx/PM1.0/PM2.5/PM4.0/PM10 demand signals
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

**Mode Synchronization**: All zones switch between heat/cool modes simultaneously via the `hp_mode` `seasonal_mode` coordinator (a software `select` entity, not a Modbus register — see `climate/packages/coordinators/seasonal_mode.yaml`).

## Modbus Communication Architecture

**Single-master pattern** (ADR-0014): one T-Connect Pro controller is the sole Modbus RTU master on `rs485_bus` (RS485, target 38400 8E1, pending the bring-up parity check noted in ADR-0014 §4). There are no slave boards — every Modbus device is a commodity I/O board the master polls/writes directly:

| Device | Address | Role |
|---|---|---|
| Analog Outputs Board (Waveshare Modbus RTU Analog Output 8CH (B)) | `0x1` | 0-10V fancoil/valve modulation, channels → `analog_output_1..8` |
| Relay Board (Waveshare Modbus RTU Relay 32CH) | `0x2` | Radiant/fancoil/pump switching, channels → `relay_1..32` |
| MEV (Cappellotto Air Fresh I) | `0x10` | Ventilation control, see `climate/mev_modbus.yaml` for its register set |

Room temperature/humidity control data does **not** travel over this bus — it is CAN-primary (received directly on the controller's own CAN interface) with a Home Assistant fallback (see `room_sensors.yaml`); room air-quality/pollutant data (CO2, VOC index, NOx index, PM1.0/2.5/4.0/10) is likewise CAN-sourced, statically declared per first-floor room in `climate/rooms/first_floor/first-floor.yaml` and dispatched by `climate/packages/can_sensor_receiver.yaml`, independent of Modbus (HVAC-1.5).

**Polling Intervals**:
- Relay/analog board polling: 2 seconds (`update_interval` in each board's package include)
- MEV polling: 30 seconds (`climate/mev_modbus.yaml` default)

## Test & verify (from repo root)

```bash
# Native C++ receiver logic (no ESPHome deps). Both -I flags are required:
# climate/protocol/*.h include canbus' frozen headers by flat filename, the form
# ESPHome's flattened build needs (same pattern as lighting/tests).
g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Iclimate/protocol climate/tests/test_can_sensor_receiver.cpp -o /tmp/climate_can_sensor_receiver && /tmp/climate_can_sensor_receiver

# Isolated receiver composition fixture (generated routes + receiver package,
# without the full climate controller)
esphome config climate/tests/compile_can_sensor_receiver.yaml

# The real climate controller entry point: config gate, then the full compile
esphome config devices/locals/climate-control.yaml
esphome compile devices/locals/climate-control.yaml
```

The whole cross-system battery (canbus generator/python/native tests, lighting,
these Climate checks, generator idempotence across `canbus`/`climate`/`registry`, and
the Climate package failover e2e) is codified in `scripts/verification-battery.sh`:
`bash scripts/verification-battery.sh` (or `--native-only` when ESPHome isn't
installed). Verification runs pin `esphome==2026.6.5` (`climate/tests/pyproject.toml`).

## Common Tasks

### Adding a New Room

1. Create room config file in `climate/rooms/[floor]/[room_name].yaml`
2. Include sensor, radiant, fancoil packages with room-specific vars
3. Add room package to floor aggregator (`[floor]-floor.yaml`)
4. Assign relay numbers (ensure no conflicts)
5. Add Modbus register mappings if using remote sensors
6. Test compilation
7. Deploy and verify

Example:
```yaml
# climate/rooms/ground_floor/new_room.yaml
defaults:
  room_slug: new_room
  room_name: "New Room"
  temperature_sensor: sensor.new_room_temp
  radiant_relay: relay_22   # pick an unallocated channel — see Appendix B
  # No fancoil_relay: fancoils have no dedicated relay (floor pump + 0-10V fan, Appendix B/C)

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
- Wrong baud rate/parity (target 38400 8E1 — see Appendix C)
- Incorrect address
- Missing termination resistors
- Swapped A/B wires
- Too many devices on bus (> 30)

## Appendices

### A. Modbus Register Quick Reference

**Relay Board (address `0x2`, 32 channels)** — coils `0x0000`-`0x001F` (channel N = coil N-1); FC `0x01` read, `0x05` write single, `0x0F` write multiple; write values `0xFF00`=on, `0x0000`=off, `0x5500`=toggle. No connectivity status register — communication failures surface per-switch (ESPHome marks a switch unavailable on read timeout). See `packages/devices/modbus-io/modbus_relay_board_32ch.yaml`.

**Analog Outputs Board (address `0x1`, 8 channels)** — holding registers `0x0000`-`0x0007` (channel N = register N-1); value in mV, `0`-`10000` = `0`-`10.00V`; FC `0x03`/`0x06`/`0x10`. See `packages/devices/modbus-io/modbus_analog_outputs_board.yaml`.

**MEV (address `0x10`)** — device-specific register set (mode/on-off/dehumidify writes, 5 temperature sensors, component-state and 39-alarm-type reads, filter-hours tracking); see `climate/mev_modbus.yaml` for the full mapping, not duplicated here.

### B. Relay Assignment Reference

Live channel mapping (single 32-channel Relay Board, address `0x2`, `id_offset: 0` → `relay_1..relay_32`). Source of truth is `devices/climate-control.yaml` and the room/floor files under `climate/rooms/**` — update this table whenever a relay assignment changes there.

| Relay | Zone / Circuit | Component |
|-------|-----------------|-----------|
| `relay_1` | Ground floor radiant | Mixing pump (`ground-floor.yaml`) |
| `relay_2` | Ground floor fancoil | Direct pump (`ground-floor.yaml`) |
| `relay_3` | First floor radiant | Mixing pump (`first-floor.yaml`) |
| `relay_4` | Second floor fancoil | Direct pump (`second-floor.yaml`) |
| `relay_5` | — | Unallocated |
| `relay_6` | Anticamera | Radiant |
| `relay_7` | Bagno (ground floor) | Radiant |
| `relay_8` | Cucina | Radiant |
| `relay_9` | Soggiorno | Radiant |
| `relay_10` | Bagno Grande | Radiant |
| `relay_11` | Bagno Ospiti | Radiant |
| `relay_12` | Bagno Padronale | Radiant |
| `relay_13` | Camera Nord | Radiant |
| `relay_14` | Camera Ospiti | Radiant |
| `relay_15` | Camera Padronale | Radiant |
| `relay_16` | Camera Sud | Radiant |
| `relay_17` | Lavanderia | Radiant |
| `relay_18`-`relay_21` | — | Reserved (freed by the Epic 18 MEV Modbus migration; no ESPHome zone binding) |
| `relay_22`-`relay_32` | — | Unallocated spare capacity |

Fancoil units have no dedicated relay of their own — each floor's fancoil circulation runs off that floor's shared direct/mixing pump relay (`relay_2`, `relay_4`); the fan itself is 0-10V modulated via the Analog Outputs Board (Appendix C).

### C. Modbus Bus Members

| Device | Modbus Address | Bus | Notes |
|--------|---------------|-----|-------|
| T-Connect Pro (master) | — | `rs485_bus` (38400 8E1 target) | The sole Modbus master; see `boards/t-connect-pro.yaml` |
| Analog Outputs Board 8CH (B) | `0x1` | `rs485_bus` | Channels → `analog_output_1..8`; room assignments below |
| Relay Board 32CH | `0x2` | `rs485_bus` | Channels → `relay_1..32`; see Appendix B |
| MEV (Cappellotto Air Fresh I) | `0x10` | `rs485_bus` | First floor only; `climate/mev_modbus.yaml` |

Room temperature/humidity control data is **not** on this bus — it is CAN-primary/HA-fallback (see `room_sensors.yaml`); room CO2/VOC/NOx/PM air-quality data is likewise CAN-sourced (see `climate/rooms/first_floor/first-floor.yaml`), not Modbus. ADR-0014 §4 mirrors only the relay bank address (`0x2`) across the gateway's and this device's RS485 buses, so a spare Relay 32CH board swaps into either system without re-addressing; the analog board (`0x1`) and MEV (`0x10`) are climate-only addresses with no gateway-side counterpart to mirror against.

**Analog output channel assignments** (from `climate/rooms/**`): `analog_output_1` — ground floor radiant mixing valve; `analog_output_2` — first floor radiant mixing valve; `analog_output_3` — Soggiorno fancoil; `analog_output_4` — Cucina fancoil; `analog_output_5` — Locale Tecnico fancoil; `analog_output_6` — Sottotetto fancoil; `analog_output_7` — first floor MEV fan speed; `analog_output_8` — unallocated.

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
- Verify baud rate/parity (target 38400 8E1 — see Appendix C)
- Inspect RS485 wiring and termination

**PID Tuning**:
- Use auto-tune feature first (`pid_autotune.yaml`)
- Start with conservative gains (low Kp, very low Ki/Kd)
- Increase gradually while monitoring stability
- Different gains for heat vs. cool modes

## The room_slug contract with canbus

`registry/nodes.csv`'s `room_slug` column (spec-map-json-contract) joins a
CAN-bus wall-button node to a climate zone. The known-zone list is read from
this directory's room files (`climate/rooms/**`, by file *contents* not
filenames — `ground_floor/bagno.yaml` declares `bagno_terra`) by
`canbus/tools/generate_nodes.py`'s `load_climate_zones()`, so it
can't drift as rooms are added, renamed, or removed. Climate only reads
`registry/map.json`; it never writes the registry (ADR-0009 §7 authority
boundary).

## Conventions

- Epic prefix: **CLIMATE-** for future work. Existing `HVAC-*` story IDs remain historical. New BMAD artifacts go to the root `_bmad-output/`.
- File naming follows root `CLAUDE.md`'s general conventions (kebab-case device
  configs, `[component_type]_[variant].yaml` for component configs); this file
  is the sole owner of Climate-specific rules — entity-ID convention, PID
  architecture, Modbus register/relay appendices, and PID/Modbus "Common
  Tasks" all live here, not in root `CLAUDE.md` (AD-10).
