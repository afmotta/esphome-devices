# ESPHome Devices - AI Assistant Guide

## Document Information

| Field | Value |
|-------|-------|
| **Project** | ESPHome Multi-Floor Climate Control System |
| **Version** | 1.3 |
| **Last Updated** | July 5, 2026 |
| **Purpose** | Guide AI assistants in understanding and working with this codebase |

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Tech Stack](#tech-stack)
3. [Repository Structure](#repository-structure)
4. [Key Conventions](#key-conventions)
5. [Component Architecture](#component-architecture)
6. [Development Workflow](#development-workflow)
7. [Testing & Deployment](#testing--deployment)
8. [Common Tasks](#common-tasks)
9. [Important Files Reference](#important-files-reference)
10. [Best Practices](#best-practices)

---

## Project Overview

### What This Is

This repo hosts the ESPHome systems for Alberto's three-floor residence. It contains **two subsystems**:

1. **Climate control** (everything outside `canbus/`) — a **pre-live ESPHome-based residential climate control system** for heating, cooling, and ventilation. Controller hardware is not yet finalized (a master-controller swap is under consideration). This document describes it.
2. **CAN bus wall buttons** (`canbus/`) — a pre-live CAN bus wall-button system (RP2040 nodes + ESP32-S3 gateway, dumb-nodes/smart-gateway design). See `canbus/CLAUDE.md` for its rules and `canbus/docs/canbus-smart-home-reference.md` for the protocol. Merged from `afmotta/canbus` (archived) with full history; old PR `#N` references in `canbus/` commit messages resolve in the archived repo. Its `registry/map.json` export and sensor CAN frames are consumed by the climate controller — that contract lives in-repo now.

BMAD epics are namespaced going forward: **HVAC-Epic N** (climate) vs **CAN-Epic N** (canbus). Historical canbus BMAD artifacts stay under `canbus/_bmad-output/`; new artifacts for both subsystems go to the root `_bmad-output/`.

### System Capabilities

- **Multi-zone climate control**: 13 independently controlled temperature zones across 3 floors
- **Dual-mode operation**: Radiant floor heating/cooling + fancoil units
- **Advanced PID control**: Precise temperature management with auto-tuning
- **Mechanical Extract Ventilation (MEV)**: Air quality monitoring and control
- **Autonomous operation**: RS485 Modbus RTU communication between boards for operation without Home Assistant
- **Home Assistant integration**: Full monitoring, dashboards, and overrides when available
- **Multi-tier failover**: Graceful degradation (Modbus → HA → Emergency shutdown)

### Building Layout

- **Ground Floor (Piano Terra)**: 5 zones (soggiorno/living room, cucina/kitchen, bagno/bathroom, anticamera/entry hall, locale tecnico/technical room)
- **First Floor (Primo Piano)**: 8 zones (4 bedrooms, 4 bathrooms, laundry room)
- **Second Floor (Secondo Piano)**: 1 zone (sottotetto/attic)

### Hardware

- **Kincony KC868-A6**: Master controller with 6 relays, 2 DACs, RS485, mixing valve control
- **Kincony KC868-A16**: Slave controllers with 16 relays for zone distribution (2 boards)
- **WaveShare ESP32-S3-POE**: Modern ESP32-S3 with Ethernet POE
- **S1 Pro Multi-Sense**: Custom sensor boards with LD2450 radar, air quality sensors
- **XY-MD02 Modbus Sensors**: Room temperature/humidity sensors
- **RS485 Modbus RTU**: Board-to-board communication at 9600 baud

---

## Tech Stack

### Primary Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **ESPHome** | 2026.3.0+ | ESP32 firmware framework (YAML-based) |
| **Python** | 3.x | Custom component development (LD2450 sensor driver) |
| **C++** | (ESP-IDF) | Low-level sensor integrations and performance-critical code |
| **YAML** | 1.2 | Configuration language for ESPHome |
| **Modbus RTU** | - | RS485 serial communication protocol |
| **Home Assistant** | 2024.x+ | Monitoring, dashboards, coordination (optional fallback) |

### Key ESPHome Platforms

- `climate.pid` - PID temperature controllers
- `modbus_controller` - Modbus RTU communication
- `uart` - RS485 serial communication
- `ethernet` / `wifi` - Network connectivity
- `api` - Home Assistant Native API
- `homeassistant` platform - Sensor fallback from HA
- `udp` / `packet_transport` - Board-to-board communication

### External APIs

- **OpenWeather API** (planned): Weather forecast integration for seasonal mode automation
- **Home Assistant API**: ESPHome Native API for monitoring and fallback sensor data

---

## Repository Structure

> **Note:** the tree below predates the in-progress layered restructure (see
> `_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/MIGRATION-MAP.md`)
> and will be rewritten as the four-system map in migration Phase 6. Until
> then: `canbus/` and `lighting/` aren't yet shown as top-level entries below
> (their own `CLAUDE.md`s are current); `hvac/` is shown since Phase 4 gathered
> it. There is no top-level `home-assistant/` any more (AD-5) — HA-side
> artifacts live per-system at `canbus/home-assistant/`, `lighting/home-assistant/`,
> and `hvac/home-assistant/dashboards/` (shown below).

```
esphome-devices/
├── registry/                  # house system-of-record (nodes.csv, node_id_hwm, bindings.yaml,
│                               #   map.json); per-file ownership, see registry/README.md
├── canbus/                    # CAN bus wall-button subsystem (see canbus/CLAUDE.md)
│   ├── firmware/              # Nodes (generated), gateway, bridge, protocol headers, tools,
│   │   │                      #   native tests
│   │   └── ...
│   ├── docs/                  # Protocol reference, runbooks
│   └── _bmad-output/          # Historical CAN-epic artifacts (frozen)
│
├── vesta/                     # Vesta Climate Framework (open-source library)
│   ├── packages/
│   │   ├── components/        # Reusable YAML component packages
│   │   │   ├── pid.yaml               # PID controller
│   │   │   ├── pid_autotune.yaml      # Auto-tuning logic
│   │   │   ├── pid_sensors.yaml       # PID input/output sensors
│   │   │   ├── radiant.yaml           # Radiant floor heating/cooling
│   │   │   ├── fancoil.yaml           # Fancoil unit control (analog 0-10V)
│   │   │   ├── heat_only_radiant.yaml # Heat-only radiant variant
│   │   │   ├── direct_pump.yaml       # Direct pump control
│   │   │   ├── mixing_pump.yaml       # Mixing valve + pump
│   │   │   ├── failover_sensor.yaml   # 3-tier sensor failover
│   │   │   ├── proportional_demand_sensor.yaml # Proportional demand
│   │   │   └── trend_sensor.yaml      # Rate-of-change sensor
│   │   ├── coordinators/      # Control pattern orchestrators
│   │   │   ├── fancoil_boost.yaml     # Radiant+fancoil boost coordination
│   │   │   ├── mev_ventilation.yaml   # MEV ventilation control
│   │   │   └── seasonal_mode.yaml     # Seasonal heat/cool mode switching
│   │   └── devices/           # Hardware board configurations
│   ├── docs/                  # Vesta documentation
│   ├── examples/              # Example configurations
│   ├── README.md              # Vesta project overview
│   └── CONTRIBUTING.md        # Contribution guidelines
│
├── boards/                    # Board hardware definitions
│   ├── base.yaml              # Common ESPHome settings
│   ├── a6.yaml                # KC868-A6 master board (mixing valves)
│   ├── a16.yaml               # KC868-A16 slave boards (relays)
│   ├── waveshare-s3.yaml      # ESP32-S3-POE board
│   ├── s1-pro-multi-sense.yaml # Sensor board
│   ├── *_ethernet.yaml        # Ethernet network configs
│   └── wifi.yaml              # WiFi network config
│
├── hvac/                       # HVAC (climate control) application system — see hvac/CLAUDE.md
│   ├── room_sensors.yaml      # Room sensor failover wiring
│   ├── mev_modbus.yaml        # MEV Modbus device driver
│   ├── mev_demand.yaml        # MEV demand signal aggregation
│   ├── rooms/                 # Room-specific configurations
│   │   ├── ground_floor/      # Ground floor rooms
│   │   ├── first_floor/       # First floor rooms
│   │   └── second_floor/      # Second floor rooms
│   └── home-assistant/        # Dashboards (Lovelace)
│
├── devices/                   # Main device configurations (entry points and their deployment variants, gathered together)
│   ├── climate-control.yaml   # Main HVAC system
│   ├── room-sensor-soggiorno.yaml # Standalone room sensor
│   ├── wall-sensor.yaml       # Wall-mounted sensor (SEN66)
│   ├── gateway.yaml           # CAN bus gateway firmware
│   ├── bridge.yaml            # CAN bus segment bridge firmware
│   ├── secrets.yaml.example   # Template for devices/secrets.yaml (gateway's secrets)
│   ├── locals/                # Local development/deployment configs
│   └── remotes/               # Remote GitHub-based deployment configs
│
├── libs/                      # Custom Python/C++ components
│   └── s1_pro/                # LD2450 radar driver
│
├── docs/                      # Project documentation and guides
│
├── _bmad/                     # BMAD framework (agents, workflows, tasks)
├── _bmad-output/              # BMAD artifacts (epics, stories, analysis)
│
├── secrets.yaml               # (gitignored) Credentials and secrets
└── TODO.md                    # Feature backlog (Italian)
```

---

## Key Conventions

### File Naming Conventions

#### Board Configs (`boards/`)
- Pattern: `[board_model]-[optional_variant].yaml`
- Examples: `a6.yaml`, `a16.yaml`, `waveshare-s3.yaml`, `s1-pro-multi-sense.yaml`
- Network configs: `[board]_ethernet.yaml`, `wifi.yaml`

#### Component Configs (`hvac/`)
- Pattern: `[component_type]_[variant].yaml` or `[feature].yaml`
- Examples: `modbus_relay_board.yaml`, `pid_autotune.yaml`, `fancoil.yaml`
- Descriptive, function-based names

#### Room Configs (`hvac/rooms/`)
- Pattern: Italian room names in snake_case
- Floor aggregators: `[floor]-floor.yaml`
- Room files: `[room_name].yaml`
- Examples: `soggiorno.yaml`, `camera_nord.yaml`, `bagno_padronale.yaml`

#### Device Configs (`devices/`)
- Pattern: kebab-case descriptive names
- Examples: `climate-control.yaml`, `room-sensor-soggiorno.yaml`

### Entity ID Naming Convention

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

### Code Style

#### YAML Formatting
- **Indentation**: 2 spaces (no tabs)
- **Key spacing**: Space after colon (`key: value`)
- **List items**: Dash with space (`- item`)
- **Comments**: Use `#` for inline comments
- **Long values**: Use YAML multi-line strings (`>` or `|`)

#### Variable Substitution
```yaml
# Substitution syntax
${variable_name}

# Default values
${variable_name:default_value}

# Example
sensor: ${temperature_sensor:sensor.default_temp}
```

#### Component Parameterization Pattern
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

---

## Component Architecture

### Package Composition Pattern

The codebase uses ESPHome's `packages` feature extensively for modularity and reusability.

#### Hierarchy

```
Device Config (devices/climate-control.yaml)
├── Board Package (boards/waveshare-s3.yaml)
│   ├── Base Package (boards/base.yaml)
│   └── Network Package (boards/*_ethernet.yaml or wifi.yaml)
├── Hardware Packages (vesta/packages/devices/modbus-io/modbus_relay_board.yaml)
└── Floor Packages (hvac/rooms/*/floor.yaml)
    └── Room Packages (hvac/rooms/*/*.yaml)
        ├── Sensors (hvac/room_sensors.yaml)
        ├── Radiant (vesta/packages/components/radiant.yaml)
        ├── Fancoil (vesta/packages/components/fancoil.yaml)
        └── Boost Coordinator (vesta/packages/coordinators/fancoil_boost.yaml)
```

#### Conditional Package Inclusion

```yaml
# Enable/disable features with substitutions
packages:
  network: ${ethernet_package if enable_ethernet else wifi_package}
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

### PID Control Architecture

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

### Modbus Communication Architecture

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

### Failover Architecture

**3-Tier Sensor Failover** (implemented in `failover_sensor.yaml`):

1. **Primary**: Local Modbus room sensor (fastest, most accurate)
2. **Fallback**: Home Assistant sensor (proven, reliable)
3. **Emergency**: Return NAN → triggers safe shutdown after 5 minutes

**Automatic Recovery**: System automatically switches back to Modbus when sensor recovers.

---

## Development Workflow

### Epic-Based Development Process

This project follows an **epic-driven development methodology** documented in `.bmad-core/`:

1. **Epic Brief** (`docs/epic-N-brief.md`): Defines user stories, technical specs, acceptance criteria
2. **Implementation**: Work through stories in priority order
3. **Testing**: Follow epic testing checklist
4. **Completion Report** (`docs/epic-N-completion-report.md`): Documents what was delivered
5. **Git Commit**: Pattern is "Epic N" (e.g., "Epic 16", "Epic 15")

### Git Workflow

```bash
# Typical workflow
git status                      # Check current state
git add [specific files]        # Stage specific files (avoid git add -A)
git commit -m "Epic N: [description]"
git push origin [branch]
```

**Git Conventions**:
- Commit messages: "Epic N: [description]" or "Epic N" for epic completion
- Never use `git add -A` or `git add .` (risks committing secrets)
- Add specific files by name
- Never force push to main/master
- Never skip hooks (pre-commit)

### Local Development

```bash
# Compile configuration
esphome compile devices/locals/climate-control.yaml

# Upload to device over network
esphome run devices/locals/climate-control.yaml

# Upload over USB (initial flash)
esphome run devices/locals/climate-control.yaml --device /dev/ttyUSB0

# View logs
esphome logs devices/locals/climate-control.yaml
```

### Remote/Production Deployment

```yaml
# devices/remotes/climate-control.yaml references GitHub
substitutions:
  github_ref: main
  github_username: !secret github_username
  github_pat: !secret github_pat

packages:
  device: github://${github_username}/esphome-devices@${github_ref}/devices/climate-control.yaml
```

Then deploy via Home Assistant ESPHome addon:
- Click "Install" on device card
- ESPHome pulls config from GitHub
- OTA update pushed to device

### Secrets Management

Never commit `secrets.yaml`. It contains:
```yaml
# secrets.yaml (gitignored)
wifi_ssid: "YourSSID"
wifi_password: "password"
encryption_key: "base64key..."
ota_password: "password"
github_username: "username"
github_pat: "ghp_token..."
```

Reference secrets in configs:
```yaml
substitutions:
  wifi_ssid: !secret wifi_ssid
  wifi_password: !secret wifi_password
```

---

## Testing & Deployment

### Testing Levels

1. **Component Testing**: Test individual component packages in isolation
2. **Integration Testing**: Test full device config compilation
3. **Hardware Testing**: Deploy to test board, verify outputs
4. **Production Testing**: Follow epic testing checklist

### Epic Testing Checklist Pattern

Each epic includes a detailed testing checklist (see `docs/epic-*-testing-checklist.md`):

```markdown
### Story X.Y: [Feature Name]
- [ ] Test condition 1
- [ ] Test condition 2
- [ ] Verify sensor readings
- [ ] Check Home Assistant integration
- [ ] Test failover scenario
```

### Validation Before Commit

```bash
# Always validate before committing
esphome config devices/locals/climate-control.yaml

# Check for syntax errors
grep -r "TODO\|FIXME" .

# Verify no secrets in tracked files
git diff --staged | grep -i "password\|secret\|api_key"
```

### OTA Update Safety

- ESPHome has password protection (`ota_password`)
- Never push to production without testing on dev board first
- Keep backup of last known good config
- Monitor logs during first 5 minutes after OTA update

---

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

### Creating Custom Components

For Python/C++ components:

1. Create directory in `libs/[component_name]/`
2. Add `__init__.py` (can be empty)
3. Add `sensor.py` or `[component].py` for Python logic
4. Add `.h` files for C++ header-only implementations
5. Reference in device config:
```yaml
external_components:
  - source:
      type: local
      path: libs/s1_pro
    components: [s1_pro]
```

---

## Important Files Reference

### Critical Configuration Files

| File | Purpose |
|------|---------|
| `devices/climate-control.yaml` | **Main entry point** - orchestrates entire system |
| `boards/base.yaml` | **Common settings** - logger, API, OTA for all devices |
| `boards/waveshare-s3.yaml` | Master board hardware definition |
| `vesta/packages/coordinators/fancoil_boost.yaml` | Radiant+fancoil boost coordination |
| `vesta/packages/coordinators/mev_ventilation.yaml` | MEV ventilation control |
| `vesta/packages/components/failover_sensor.yaml` | 3-tier sensor failover logic |
| `hvac/mev_modbus.yaml` | MEV Modbus device driver (project-specific) |

### Key Documentation Files

| File | Purpose |
|------|---------|
| `docs/architecture-diagram.md` | Mermaid diagrams of system architecture |
| `_bmad-output/planning-artifacts/prd.md` | Product Requirements Document |
| `_bmad-output/planning-artifacts/epics.md` | Master epic index (Epics 1-20) |
| `_bmad-output/analysis/brainstorming-session-2026-02-24.md` | Entity ID naming convention |
| `_bmad-output/analysis/brainstorming-session-2026-02-05.md` | Vesta open-source strategy |
| `TODO.md` | Feature backlog (in Italian) |

### Configuration Entry Points

| Path | Use Case |
|------|----------|
| `devices/locals/climate-control.yaml` | Local development and testing |
| `devices/remotes/climate-control.yaml` | Production deployment via GitHub |
| `devices/climate-control.yaml` | Core device configuration |

---

## Best Practices

### When Making Changes

1. **Read First**: Always read existing code before modifying
2. **Understand Context**: Review related components and documentation
3. **Test Locally**: Compile and test on development board before production
4. **Follow Patterns**: Match existing naming conventions and structure
5. **Document**: Update relevant docs and add comments for complex logic
6. **Epic-Driven**: Work within epic framework, follow testing checklists

### Code Quality

- **DRY Principle**: Use packages and parameterization to avoid duplication
- **Clear Naming**: Use descriptive, consistent entity names
- **Comments**: Explain WHY, not WHAT (code shows what)
- **YAML Formatting**: Consistent 2-space indentation, no tabs
- **Modular Design**: Keep components small and single-purpose

### Safety Considerations

- **No Hardcoded Secrets**: Always use `!secret` references
- **Sensor Failover**: Always implement failover for critical sensors
- **Emergency Shutdown**: Include safe shutdown logic for failures
- **Testing**: Never skip testing on critical climate control code
- **Version Control**: Commit working states frequently
- **OTA Safety**: Test OTA updates on non-production boards first

### Performance Optimization

- **Polling Intervals**: Don't poll Modbus sensors more frequently than necessary (30s is good)
- **Update Intervals**: Balance responsiveness vs. network traffic
- **Logger Level**: Use INFO in production, DEBUG only for troubleshooting
- **Conditional Compilation**: Disable unused features

### Home Assistant Integration

- **Dual Operation**: Design for autonomous operation, HA as enhancement
- **Fallback Sensors**: Use HA sensors as fallback, not primary
- **Entity Exposure**: Expose diagnostic sensors for monitoring
- **Friendly Names**: Use clear, descriptive names for HA entities

---

## Language Notes

### Italian Terms Throughout Codebase

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
| gruppo miscelazione | mixing valve group | Master controller name |
| distribuzione | distribution | Slave controller naming pattern |
| radiante | radiant | Radiant floor heating/cooling |

**Note**: Comments and documentation are in English, but entity IDs often use Italian room names.

---

## Getting Help

### Documentation Resources

1. **Architecture**: `docs/architecture-diagram.md` - System topology and data flows
2. **PRD**: `docs/prd.md` - Original project requirements
3. **Epics**: `docs/epic-*.md` - Feature development history
4. **BMAD Guide**: `.bmad-core/user-guide.md` - Development framework
5. **ESPHome Docs**: https://esphome.io/ - Platform documentation

### Troubleshooting

**Compilation Errors**:
- Check YAML syntax (indentation, colons, dashes)
- Verify all `!include` paths are correct
- Ensure all substitution variables are defined
- Check ESPHome version (min 2026.3.0)

**Modbus Issues**:
- Enable DEBUG logging for modbus_controller
- Check register addresses and data types
- Verify baud rate (9600, 8N1)
- Inspect RS485 wiring and termination

**PID Tuning**:
- Use auto-tune feature first (`pid_autotune.yaml`)
- Start with conservative gains (low Kp, very low Ki/Kd)
- Increase gradually while monitoring stability
- Different gains for heat vs. cool modes

**Sensor Failover**:
- Check failover logs in Home Assistant
- Verify Modbus sensor data age < 30s
- Ensure HA sensors are available and updating
- Monitor emergency shutdown triggers

### Community and Support

- **ESPHome Discord**: https://discord.gg/KhAMKrd
- **Home Assistant Community**: https://community.home-assistant.io/
- **ESPHome GitHub**: https://github.com/esphome/esphome

---

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

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-07-05 | 1.3 | Corrected climate-control status from "production/active, live" to pre-live; controller hardware swap under consideration | AI Assistant |
| 2026-07-05 | 1.2 | Merged afmotta/canbus as canbus/ subtree; documented two-subsystem layout and epic namespacing | AI Assistant |
| 2026-03-23 | 1.1 | Updated repo structure for Vesta extraction, added entity ID naming convention, updated file references for Epics 18-20 | AI Assistant |
| 2026-01-23 | 1.0 | Initial CLAUDE.md creation | AI Assistant |

---

**End of Document**

For questions or clarifications, refer to the documentation in `docs/` or the BMAD framework in `.bmad-core/`.
