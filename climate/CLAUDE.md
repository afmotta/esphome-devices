# Climate Subsystem — AI Assistant Guide

This is the Climate application system (layered-restructure spine,
`docs/architecture/ARCHITECTURE-SPINE.md`).
It is **pre-live**: the controller hardware decision is finalized (ADR-0014 — LilyGO
T-Connect Pro + Modbus RTU I/O boards, implemented) but not yet physically deployed.
Everything below is scoped to `climate/`; entry
points that compose Climate packages (`devices/climate-control.yaml` and its
`devices/locals/` build wrapper) stay in
`devices/` (entry points and their variants live together; ADR-0023 retired the
`devices/remotes/` GitHub-pull variant).

## What's here

- `rooms/` — room and floor-aggregator configs (14 rooms across 3 floors),
  each including PID/radiant/fancoil packages from `climate/packages/components/`
- `packages/components/`, `packages/coordinators/` — Climate-owned reusable ESPHome
  packages for PID/radiant/fancoil/failover/demand logic and orchestration
- `mev_modbus.yaml`, `mev_demand.yaml` — MEV (Mechanical Extract Ventilation)
  Modbus driver and demand aggregation
- `room_sensors.yaml` — room sensor failover wiring
- `home-assistant/` — hand-authored Lovelace dashboards (`dashboards/`) and the HA-side configs (`ha-*-config.yaml`, `mev_helpers.yaml`)

## System overview

### System Capabilities

- **Multi-zone climate control**: 14 independently controlled temperature zones across 3 floors
- **Dual-mode operation**: Radiant floor heating/cooling + fancoil units. Each actuator has one PID whose heat and cool outputs are *separate* template outputs gated on the heat pump's mode (`hp_mode`: HEAT → heat only, COOL → cool only, SANITARY_ONLY → neither; `climate/protocol/pid_direction.h`, review R-01), so a PID can only actuate in the direction the water actually flows. Fancoils declare a `fancoil_role` (`boost`, `cool_only`, `heat_cool`)
- **Hybrid radiant + fancoil cooling ("base + boost")**: radiant floor/ceiling provides efficient baseline comfort; fancoils activate as a responsive boost layer when radiant cannot meet demand — evaluated independently per room (`climate/packages/coordinators/fancoil_boost.yaml`)
- **Advanced PID control**: Precise temperature management with auto-tuning
- **Autonomous dew-point protection**: ESPHome-native dew-point calculation sets the radiant-cooling supply-water target to dew point + `safe_margin` (default 2 °C, settable 1-5 °C) on the controller itself, and a hard interlock on each mixing valve shuts the chilled water whenever the supply falls below dew point + margin/2, independent of the PID (`climate/protocol/dew_point_interlock.h`, review N-01); it needs valid room readings, so a room whose dew point is NaN (CAN and HA tiers both gone) leaves the floor's supply minimum holding its previous value (`climate/room_sensors.yaml`, `climate/rooms/ground_floor/ground-floor.yaml`)
- **Window-aware climate response**: an open window pauses fancoil control after a grace period while radiant keeps running (thermal-mass characteristics make it safe)
- **Three-tier seasonal mode selection**: automated heat/cool mode via calendar hard-locks plus demand-driven shoulder-season transitions (`climate/packages/coordinators/seasonal_mode.yaml`)
- **Mechanical Extract Ventilation (MEV)**: two Modbus-controlled units of different models — the first-floor Cappellotto Air Fresh I with air-quality- and humidity-driven demand plus a dehumidification/integration cascade, alarm decoding, and filter-hour tracking (`climate/mev_modbus.yaml`, `climate/packages/coordinators/mev_ventilation.yaml`); and the ground-floor Innova HRP DOMO 60 HX, a passive **enthalpic** HRV driven by CO2/air-quality **and** humidity demand — high humidity raises ventilation and the enthalpic core passively manages moisture, so there is no active dehumidification cascade (its only actuator is fan speed) — on the shared 3-channel demand with a fan-only coordinator (`climate/mev_innova_modbus.yaml`, `climate/packages/coordinators/mev_ventilation_fan_only.yaml`; ADR-0018)
- **Autonomous operation**: all relay/analog/MEV actuation runs on the one controller (the sole Modbus master) regardless of Home Assistant (`api: reboot_timeout: 0s` on the controllers, and `wifi:` too on the dual-interface boards, so an HA or access-point outage never reboots them, R-02). Room-sensor *data* does not: it depends on the CAN→HA failover chain (`climate/room_sensors.yaml`), and while only `soggiorno` has a CAN sensor node (`registry/map.json`) an HA outage (no state-subscribed API client) over 300 s puts the other 13 of 14 zones in Emergency (PID outputs 0)
- **Home Assistant integration**: Full monitoring, dashboards, and overrides when available
- **Multi-tier failover**: Graceful degradation (CAN → HA → Emergency: NaN, PID outputs 0)

### Building Layout

- **Ground Floor (Piano Terra)**: 5 zones (soggiorno/living room, cucina/kitchen, bagno/bathroom, anticamera/entry hall, locale tecnico/technical room)
- **First Floor (Primo Piano)**: 8 zones (4 bedrooms, 3 bathrooms, laundry room)
- **Second Floor (Secondo Piano)**: 1 zone (sottotetto/attic)


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

**One PID per actuator, direction-gated** (review R-01, `docs/reviews/2026-10-25-repo-review.md`).
Each zone actuator (radiant valve, fancoil 0-10V channel, floor mixing valve) has ONE PID whose
`heat_output`/`cool_output` are two *gated* template outputs, never the same output twice:

```yaml
# heat_only_radiant.yaml / radiant.yaml (shape)
output:
  - platform: template
    id: ${room_slug}_radiant_heat_output      # wired to the PID's heat_output
    type: float
    write_action:
      - lambda: |-
          id(${room_slug}_radiant_output).set_level(pid_direction::gated_level(
              pid_direction::Direction::HEAT, id(${seasonal_mode_id}).current_option().c_str(), state));
  # ...and ${room_slug}_radiant_cool_output with Direction::COOL, wired to cool_output
```

Why: ESPHome's PID ignores its HEAT/COOL mode when routing output (`pid_climate.cpp`
`write_output_()` sends value > 0 to heat_output and -value to cool_output). Wiring both to one
actuator drove it with |error| — an overheated room opened its valve in winter. The gate
(`climate/protocol/pid_direction.h`, natively tested) lets a direction actuate only while
`hp_mode` says the heat pump produces matching water (HEAT → heat, COOL → cool,
SANITARY_ONLY → neither). **Never wire heat_output and cool_output to the same output.**

Fancoils declare a required `fancoil_role`: `boost` (cooling boost, only the
`fancoil_boost` coordinator starts it), `cool_only`, or `heat_cool`.

**The radiant override is a convenience, never a safety bypass** (review R-05). The final stage
(`climate/protocol/radiant_override.h`) forces the valve closed whenever the zone temperature is NaN,
whatever the override says, and a NaN temperature that persists for `sensor_lost_grace` (default 120 s)
ends a running boost — the grace lets a boost restored from flash survive the boot-time NaN (R-16). A floor's pump
demand is `*_radiant_pid_is_active || *_radiant_override_active` for every radiant zone — read with
**`.state`**: `id(binary_sensor)` in a lambda is the sensor *pointer* (always true), which is how the
pump-demand sums were once stuck on; `scripts/verify_seasonal_mode_aggregation.py` enforces both.

**The dew-point minimum is a target; the interlock is the limit** (review N-01). In COOL each floor's
mixing-valve PID regulates the supply toward `{floor}_supply_temp_minimum` (max room dew point +
`{floor}_radiant_safe_margin`, default 2.0 °C, range 1-5 °C), which on its own cannot stop an overshoot.
`mixing_pump.yaml` therefore passes the valve's cool output through `climate/protocol/dew_point_interlock.h`:
below minimum − margin/2 (dew point + margin/2) the chilled water is shut, and it stays shut until the supply
is back at the minimum; a NaN supply, minimum or margin blocks too. It is evaluated on every PID write
(each supply reading) and shown as `{floor}_radiant_mixing_valve_dew_point_interlock` (COOL only).
`mixing_pump.yaml` requires `supply_minimum_id` and `safe_margin_id` for this.

**PID integral confined to the active direction** (review R-13). `pid.yaml` re-bounds every PID's
integral on each `hp_mode` change via `pid_direction::integral_bounds()`: HEAT → `[0, limit]`,
COOL → `[-limit, 0]`, SANITARY_ONLY keeps the previous bounds (`integral_limit` var, default 1.0,
output units). Without it the gated direction wound up a full actuator span. Side effects: the
first demand-tier intent in the new direction is delayed — in HEAT `is_cooling` only appears once
the integral has decayed to 0 (~200 s per unit of error at ki 0.005, mirror in COOL), which the
seasonal-mode coordinators reading `*_pid_is_active` see — and after a long SANITARY_ONLY the
previous season's bounds still apply (a SANITARY_ONLY restored at boot runs symmetric bounds);
both are bounded by `integral_limit`. Rationale: `pid_direction::integral_bounds`.

**Fancoil boot state is owned by the role** (review R-16). Each `fancoil_role_*.yaml` maps `hp_mode`
to the PID mode in one script (`${room_slug}_fancoil_sync_mode`); `fancoil.yaml` runs it from the select's
`on_value` *and* from an `esphome: on_boot` **list entry at priority -100**. `fancoil_boost.yaml`'s boot replay is
a separate entry at -110, so it runs after the role sync and has the last word on a restored boost. `on_boot` is
**always list-form with an explicit `priority:`** — package mappings merge into one trigger with a single surviving
priority and mixing forms drops a hook (review R-18; enforced by `scripts/check_on_boot_form.py`). Against a restored
boost under a non-COOL `hp_mode` the final PID mode (OFF or COOL) depends on that order, but it never actuates (the
cool output is gated on `hp_mode`) and the coordinator's season override ends the boost.
A reboot discards a manual or HA-set fancoil PID mode and returns to the role/`hp_mode` mapping (as an
`hp_mode` change already does); the window guard re-asserts OFF if the window is still open. A restored boost
surviving the boot-time NaN holds on the CAN tier only: on the HA tier the 300 s staleness grace exceeds
`sensor_lost_grace`.

**The window guard hands the fancoil back to its owner** (review R-14): it takes a required
`resume_script_id` and, after recovery, runs the role's `${room_slug}_fancoil_resume_mode` (boost: COOL
only if the boost is still running and `hp_mode` is COOL) instead of restoring a snapshot.

**Mode Synchronization**: All zones switch between heat/cool modes simultaneously via the `hp_mode` `seasonal_mode` coordinator (a software `select` entity, not a Modbus register — see `climate/packages/coordinators/seasonal_mode.yaml`).

## Modbus Communication Architecture

**Single-master pattern** (ADR-0014): one T-Connect Pro controller is the sole Modbus RTU master on `rs485_bus` (RS485, target 38400 8E1, pending the bring-up parity check noted in ADR-0014 §4). There are no slave boards — every Modbus device is a commodity I/O board the master polls/writes directly:

| Device | Address | Role |
|---|---|---|
| Analog Outputs Board (Waveshare Modbus RTU Analog Output 8CH (B)) | `0x1` | 0-10V fancoil/valve modulation, channels → `analog_output_1..8` |
| Relay Board (Waveshare Modbus RTU Relay 32CH) | `0x2` | Radiant/fancoil/pump switching, channels → `relay_1..32` |
| MEV first floor (Cappellotto Air Fresh I) | `0x10` | Ventilation + humidity cascade, see `climate/mev_modbus.yaml` for its register set |
| MEV ground floor (Innova HRP DOMO 60 HX) | `0x11` | Passive enthalpic HRV; CO2/air-quality + humidity ventilation demand, fan-only (no cascade), see `climate/mev_innova_modbus.yaml` (ADR-0018) |

Room temperature/humidity control data does **not** travel over this bus — it is CAN-primary (received directly on the controller's own CAN interface) with a Home Assistant fallback (see `room_sensors.yaml`); room air-quality/pollutant data (CO2, VOC index, NOx index, PM1.0/2.5/4.0/10) is likewise CAN-sourced, statically declared per room in the floor files (`climate/rooms/first_floor/first-floor.yaml`, `climate/rooms/ground_floor/ground-floor.yaml`) and dispatched by `climate/packages/can_sensor_receiver.yaml`, independent of Modbus (HVAC-1.5). Ground-floor rooms have no air-quality CAN kit registered yet, so their MEV's air-quality channel floors at minimum fan until the kits arrive; its humidity channel is live already (room humidity is sensed) (ADR-0018).

**HA-tier staleness (R-04)**: see [Sensor failover architecture](#sensor-failover-architecture).

**Polling Intervals**:
- Relay/analog board polling: 2 seconds (`update_interval` in each board's package include)
- MEV polling: 30 seconds (`climate/mev_modbus.yaml` / `climate/mev_innova_modbus.yaml` default)

## Package composition patterns

### Variable Substitution
```yaml
# Substitution syntax
${variable_name}

# Default values
${variable_name:default_value}

# Example
sensor: ${temperature_sensor:sensor.default_temp}
```

### Component Parameterization Pattern
```yaml
packages:
  component: !include
    file: component.yaml
    vars:
      slug: "entity_id"
      name: "Display Name"
      sensor: sensor.temperature
      param: value
```

### Package Composition Pattern

The codebase uses ESPHome's `packages` feature extensively for modularity and reusability.

#### Hierarchy

```
Device Config (devices/climate-control.yaml)
├── Board Package (boards/t-connect-pro.yaml)
│   └── Network: ethernet + wifi declared inline (network: priority:, ADR-0022)
├── Hardware Packages (packages/devices/modbus-io/modbus_relay_board.yaml)
└── Floor Packages (climate/rooms/*/*-floor.yaml)
    └── Room Packages (climate/rooms/*/*.yaml)
        ├── Sensors (climate/room_sensors.yaml)
        ├── Radiant (climate/packages/components/radiant.yaml)
        ├── Fancoil (climate/packages/components/fancoil.yaml)
        └── Boost Coordinator (climate/packages/coordinators/fancoil_boost.yaml)
```

#### Variable Passing Pattern

```yaml
# Parent includes child with parameters
packages:
  room: !include
    file: rooms/ground_floor/soggiorno.yaml
    vars:
      room_slug: "soggiorno"
      room_name: "Soggiorno"
      temperature_sensor: sensor.soggiorno_temp
      humidity_sensor: sensor.soggiorno_humidity
      radiant_relay: relay_1
      fancoil_relay: relay_5
```

## Sensor failover architecture

**3-Tier Sensor Failover** (implemented in `failover_sensor.yaml`, wired by `climate/room_sensors.yaml`):

1. **Primary**: CAN sensor-kit measurement (received directly on the controller's own CAN interface)
2. **Fallback**: Home Assistant sensor (`homeassistant` platform), gated for staleness (R-04): the HA tier
   reads NaN when HA reports `unavailable`/`unknown`, or when no state-subscribed API client has been
   connected for 5 minutes (`climate/protocol/ha_tier.h`, 300 s grace via `ha_staleness_grace_s`; the grace
   rides out an HA restart). For room sensors a frozen last value is never served indefinitely (other HA inputs such as outdoor temperature are not yet gated: R-12, R-08).
   While only `soggiorno` has a CAN sensor node (`registry/map.json`), the other 13 of the 14 zones depend only on this tier, so an HA outage longer than the
   grace puts those zones in Emergency — relay/analog/MEV actuation stays autonomous, but without
   room-sensor data there is nothing to regulate on. The grace is the lever to tune. Keep `esphome logs`
   sessions on `--no-states` during outage tests: a plain session counts as an HA connection.
3. **Emergency**: the failover returns NaN **immediately** once both tiers are NaN — it has no timer of its
   own. ESPHome's PID answers a NaN input by driving its outputs to 0 at once (`pid_climate.cpp`); there is
   no separate "safe shutdown after 5 minutes". The only 5-minute figure is the HA-tier grace above.
   The radiant override cannot bypass it: a NaN zone forces the valve closed at once, and a NaN that persists
   for `sensor_lost_grace` (default 120 s) ends a boost; the grace lets a boost restored from flash survive the
   boot-time NaN (reviews R-05, R-16).

**Automatic Recovery**: the failover switches back to the highest tier that has a valid reading again
(CAN preferred, then HA).

## Commissioning gates (progressive deployment)

Deployment is a **season-phased progressive rollout** on a single firmware image —
see `docs/climate/climate-deployment-runbook.md`. Features are gated at runtime, not at build
time, because the `any_pid_requesting_heat/cool` aggregation in
`devices/climate-control.yaml` hard-references every zone's PID (compiling zones out
would break the build). Three gates default to the safe state, so a freshly flashed
controller comes up idle:

| Gate | Default | Effect when off/held |
|---|---|---|
| `hp_mode_manual_hold` | **ON** | Calendar + demand tiers suspended; the operator owns `hp_mode` |
| `{zone}_boost_enabled` | **OFF** | No hybrid radiant+fancoil boost; an active boost drops to "Radiant Only" |
| `first_floor_mev_enabled` | **OFF** | Fan forced to 0; humidity cascade released to "Fan Only" |
| `ground_floor_mev_enabled` | **OFF** | Fan forced to 0 (passive enthalpic unit; CO2/air-quality + humidity demand, no cascade) |

MEV tuning values — minimum fan speed (both units) and the first-floor cascade's escalation/
de-escalation thresholds and delays — are persisted controller `number`s (`<mev_slug>_min_fan_speed`,
`_escalation_threshold`, `_deescalation_threshold`, `_escalation_delay`, `_deescalation_delay`;
review R-08b), not Home Assistant helpers, so they survive HA outages. Only the demand lower/upper
bounds still come from HA `input_number`s (`climate/home-assistant/mev_helpers.yaml`).
Ranges are deliberately narrow: first-floor min fan speed 0-30 % (ground floor 0-50 %), escalation threshold
50-100 %, de-escalation threshold 35-50 %, delays 1-120 min. The first-floor minimum (max 30) stays below the
de-escalation threshold (min 35) because the final fan speed is floored at the minimum: otherwise the cascade could
never de-escalate. Widen one range only together with the other (ADR-0018, R-08b). A value persisted under an older,
wider range is restored as-is (template numbers clamp only on writes), so re-enter it.

Two constraints drive the phase order and are easy to get wrong:

- **`hp_mode` mirrors the source, it does not command it.** The heat pump produces
  either hot or chilled water house-wide and the changeover happens at the source
  (no changeover relay exists). You can only commission the emitters for the season
  currently being produced, so full coverage spans both seasons.
- **First-floor cooling requires MEV.** The first floor cools via a radiant *ceiling*;
  its dew-point-limited supply only cools safely once MEV dehumidification has lowered
  the room dew point. MEV is commissioned in Phase 0, ahead of any cooling.

## Test & verify (from repo root)

```bash
# Native C++ receiver logic (no ESPHome deps). Both -I flags are required:
# climate/protocol/*.h include canbus' frozen headers by flat filename, the form
# ESPHome's flattened build needs (same pattern as lighting/tests).
g++ -std=c++17 -Wall -Wextra -Icanbus/protocol -Iclimate/protocol climate/tests/test_can_sensor_receiver.cpp -o /tmp/climate_can_sensor_receiver && /tmp/climate_can_sensor_receiver

# HA-tier staleness gate of the room-sensor failover (R-04); climate/outdoor.yaml reuses the
# same gate for the outdoor temperature (outdoor_temp_ha_gated, ha_outdoor_staleness_grace_s; R-12)
g++ -std=c++17 -Wall -Wextra -Iclimate/protocol climate/tests/test_ha_tier.cpp -o /tmp/climate_ha_tier && /tmp/climate_ha_tier

# Heat/cool direction gating of PID actuators (R-01)
g++ -std=c++17 -Wall -Wextra -Iclimate/protocol climate/tests/test_pid_direction.cpp -o /tmp/climate_pid_direction && /tmp/climate_pid_direction

# Radiant final stage: override vs PID, NaN stop (R-05)
g++ -std=c++17 -Wall -Wextra -Iclimate/protocol climate/tests/test_radiant_override.cpp -o /tmp/climate_radiant_override && /tmp/climate_radiant_override

# Dew-point interlock on the mixing valves' cool output (N-01)
g++ -std=c++17 -Wall -Wextra -Iclimate/protocol climate/tests/test_dew_point_interlock.cpp -o /tmp/climate_dew_point_interlock && /tmp/climate_dew_point_interlock

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
installed). Verification runs pin `esphome==2026.8.0` (`climate/tests/pyproject.toml`).

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
# (shape of climate/rooms/ground_floor/anticamera.yaml)
defaults:
  room_slug: "new_room"
  room_name: "New Room"
  temperature_sensor: new_room_temp_abstracted   # published by room_sensors.yaml

packages:
  sensors: !include
    file: ../../room_sensors.yaml
    vars:
      ha_temperature_sensor_id: "sensor.room_new_room_temperature"
      ha_humidity_sensor_id: "sensor.room_new_room_humidity"

  pid_radiant: !include
    file: ../../packages/components/radiant.yaml   # heat_only_radiant.yaml for heat-only zones
    vars:
      relay_id: relay_22   # pick an unallocated channel — see Appendix B

  # Optional fancoil: no dedicated relay (floor pump + 0-10V fan, Appendix B/C)
  # fancoil: !include
  #   file: ../../packages/components/fancoil.yaml
  #   vars:
  #     output_id: analog_output_N
  #     fancoil_role: boost   # boost | cool_only | heat_cool
```

A new radiant zone must also join its floor's pump-demand sum (`*_any_zone_open`, both
`_radiant_pid_is_active` and `_radiant_override_active`), the seasonal-mode aggregation in
`devices/climate-control.yaml` (`scripts/verify_seasonal_mode_aggregation.py` checks both), and — if it
cools — the floor's dew-point sources and supply-minimum room list, which must stay identical.

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
- Wrong register addresses or data types
- Missing termination resistors
- Swapped A/B wires
- Too many devices on bus (> 30)

## Appendices

### A. Modbus Register Quick Reference

**Relay Board (address `0x2`, 32 channels)** — coils `0x0000`-`0x001F` (channel N = coil N-1); FC `0x01` read, `0x05` write single, `0x0F` write multiple; write values `0xFF00`=on, `0x0000`=off, `0x5500`=toggle. No connectivity status register — communication failures surface per-switch (ESPHome marks a switch unavailable on read timeout). See `packages/devices/modbus-io/modbus_relay_board_32ch.yaml`.

**Analog Outputs Board (address `0x1`, 8 channels)** — holding registers `0x0000`-`0x0007` (channel N = register N-1); value in mV, `0`-`10000` = `0`-`10.00V`; FC `0x03`/`0x06`/`0x10`. See `packages/devices/modbus-io/modbus_analog_outputs_board.yaml`.

**MEV first floor (address `0x10`, Cappellotto Air Fresh I)** — device-specific register set (mode/on-off/dehumidify writes, 5 temperature sensors, component-state and 39-alarm-type reads, filter-hours tracking); see `climate/mev_modbus.yaml` for the full mapping, not duplicated here.

**MEV ground floor (address `0x11`, Innova HRP DOMO 60 HX)** — a passive **enthalpic** HRV (no dehumidifier/integration registers); driven by CO2/air-quality **and** humidity ventilation demand with a fan-only coordinator. Fan speed is 0-10V on `analog_output_8`, everything else is Modbus. Register bindings are transcribed in `climate/mev_innova_modbus.yaml` (marked `TODO(innova-register)` until the Innova manual is available; ADR-0018).

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
| `relay_18`-`relay_21` | — | Reserved (freed when MEV moved to Modbus control; no ESPHome zone binding) |
| `relay_22`-`relay_32` | — | Unallocated spare capacity |

Fancoil units have no dedicated relay of their own — each floor's fancoil circulation runs off that floor's shared direct/mixing pump relay (`relay_2`, `relay_4`); the fan itself is 0-10V modulated via the Analog Outputs Board (Appendix C).

### C. Modbus Bus Members

| Device | Modbus Address | Bus | Notes |
|--------|---------------|-----|-------|
| T-Connect Pro (master) | — | `rs485_bus` (38400 8E1 target) | The sole Modbus master; see `boards/t-connect-pro.yaml` |
| Analog Outputs Board 8CH (B) | `0x1` | `rs485_bus` | Channels → `analog_output_1..8`; room assignments below |
| Relay Board 32CH | `0x2` | `rs485_bus` | Channels → `relay_1..32`; see Appendix B |
| MEV (Cappellotto Air Fresh I) | `0x10` | `rs485_bus` | First floor; `climate/mev_modbus.yaml` |
| MEV (Innova HRP DOMO 60 HX) | `0x11` | `rs485_bus` | Ground floor; enthalpic HRV; CO2/air-quality + humidity, fan-only; `climate/mev_innova_modbus.yaml` (ADR-0018) |

Room temperature/humidity control data is **not** on this bus — it is CAN-primary/HA-fallback (see `room_sensors.yaml`); room CO2/VOC/NOx/PM air-quality data is likewise CAN-sourced (see `climate/rooms/first_floor/first-floor.yaml`), not Modbus. ADR-0014 §4 mirrors only the relay bank address (`0x2`) across the gateway's and this device's RS485 buses, so a spare Relay 32CH board swaps into either system without re-addressing; the analog board (`0x1`) and the two MEVs (`0x10`, `0x11`) are climate-only addresses with no gateway-side counterpart to mirror against.

**Analog output channel assignments** (from `climate/rooms/**`): `analog_output_1` — ground floor radiant mixing valve; `analog_output_2` — first floor radiant mixing valve; `analog_output_3` — Soggiorno fancoil; `analog_output_4` — Cucina fancoil; `analog_output_5` — Locale Tecnico fancoil; `analog_output_6` — Sottotetto fancoil; `analog_output_7` — first floor MEV fan speed; `analog_output_8` — ground floor MEV fan speed (Innova HRP DOMO 60 HX, ADR-0018).

### D. PID Tuning Guidelines

Defaults live in the component packages (`climate/packages/components/`); the table is what the code
ships, not a recommendation to retune. Zones normally just inherit these defaults.
Per-room `kp`/`ki`/`kd`/`pwm_period` vars passed to `radiant.yaml` or `heat_only_radiant.yaml` reach
the PID and slow PWM (fixed in review R-15; `radiant.yaml` restates the defaults to forward them — keep
both files' defaults in sync).

| Loop | Package | Kp | Ki | Kd | Notes |
|------|---------|----|----|----|-------|
| Radiant floor/ceiling (slow) | `heat_only_radiant.yaml` (used by `radiant.yaml`) | 0.8 | 0.005 | 0.05 | sane tuning range roughly Kp 0.5–1.0, Ki 0.001–0.01, Kd 0.01–0.1 |
| Fancoil (fast) | `fancoil.yaml` | 0.2 | 0.01 | 0.05 | already the "fast system" values; tune around them, not toward 1.0+ (a starting window of roughly Kp 0.1–0.5 is a suggestion, not a validated range) |
| Floor mixing valve | `mixing_pump.yaml` | 0.2 | 0.01 | 0.0 | |

**One gain set per actuator.** Since R-01 each actuator has a single PID whose heat and cool outputs are
gated on `hp_mode` (see "PID Control Architecture"), so heating and cooling share the same `kp`/`ki`/`kd`.
There are no separate per-mode gains to tune: tune once, in the season the loop actually works in.

**Autotune caveats** (`pid_autotune.yaml`, `pid_autotune_with_fancoil.yaml`):
- Run it in the loop's own season (`hp_mode` HEAT for a heating loop, COOL for a cooling one). In the
  wrong season the gated actuator stays at 0, the room never responds and the tune never completes.
- The autotuner assumes an output swing of -1..+1, but on a loop with both a heat and a cool output the
  gated opposite half-cycle only closes the valve, so the real swing is 0..1 and the estimated gains
  come out about 2x too high: **halve `kp`/`ki`/`kd`** only on dual-output loops: radiant zones on `radiant.yaml` and `heat_cool`
  fancoils. Do **not** halve heat-only loops (the bathroom/laundry zones on `heat_only_radiant.yaml`) or
  cool-only loops: they already model 0..1 correctly. The 2x factor is derived from the comments in
  `pid_autotune.yaml`, not bench-verified (verify at bring-up).
- The PID must not be OFF. `boost` fancoils sit OFF until the boost coordinator starts them, so set the
  fancoil PID to COOL by hand before pressing the button.
- For zones with a fancoil or boost coordinator use `pid_autotune_with_fancoil.yaml` (ends boost and
  turns the fancoil PID off first) and run it in HEAT.

**PID tuning tips** (Modbus debugging: see "Debugging Modbus Issues" under Common Tasks):
- Use auto-tune feature first (`pid_autotune.yaml`)
- Start with conservative gains (low Kp, very low Ki/Kd)
- Increase gradually while monitoring stability
- One gain set serves both directions (heat/cool outputs are gated, not separate PIDs); tune in the season the loop works in

## Operating principles

### Safety Considerations

- **Sensor Failover**: Always implement failover for critical sensors
- **Emergency Behavior**: When all sensor tiers are NaN, PID outputs drop to 0 immediately (no shutdown timer)
- **Testing**: Never skip testing on critical climate control code

Secrets, OTA and git rules are house-wide: see the root `CLAUDE.md`.

### Performance Optimization

- **Polling Intervals**: Don't poll Modbus I/O boards more frequently than necessary (see "Polling Intervals" above)
- **Update Intervals**: Balance responsiveness vs. network traffic
- **Logger Level**: Use INFO in production, DEBUG only for troubleshooting
- **Conditional Compilation**: Disable unused features

### Home Assistant Integration

- **Dual Operation**: Design actuation to run autonomously; HA enhances monitoring/overrides
- **Sensor Failover**: Room sensors are CAN-primary with a Home Assistant fallback tier (`climate/room_sensors.yaml`) — always keep a non-HA tier for critical sensors
- **Entity Exposure**: Expose diagnostic sensors for monitoring
- **Friendly Names**: Use clear, descriptive names for HA entities

## Italian terminology


The system was developed for an Italian residence, so many entity names use Italian terminology:

| Italian | English | Context |
|---------|---------|---------|
| soggiorno | living room | Most common zone name |
| cucina | kitchen | Room type |
| bagno | bathroom | Multiple bathrooms use qualifiers |
| camera | bedroom | Often with direction (nord/sud) or type |
| anticamera | entry hall / foyer | Ground floor zone |
| lavanderia | laundry room | First floor utility |
| sottotetto | attic | Second floor only zone |
| locale tecnico | technical room | Houses HVAC equipment |
| piano terra | ground floor | Building level 0 |
| primo piano | first floor | Building level 1 |
| secondo piano | second floor | Building level 2 |
| gruppo miscelazione | mixing valve group | Historical Gen-1 master controller name (retired) |
| distribuzione | distribution | Historical Gen-1 slave-board naming pattern (retired) |
| radiante | radiant | Radiant floor heating/cooling |

**Note**: Comments and documentation are in English, but entity IDs often use Italian room names.

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

- Prefix commits touching this system with `climate:`. Record significant decisions as new ADRs under `docs/adr/`.
- File naming follows root `CLAUDE.md`'s general conventions (kebab-case device
  configs, `[component_type]_[variant].yaml` for component configs); this file
  is the sole owner of Climate-specific rules — entity-ID convention, PID
  architecture, Modbus register/relay appendices, and PID/Modbus "Common
  Tasks" all live here, not in root `CLAUDE.md` (AD-10).
