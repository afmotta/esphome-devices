# ESPHome Devices - AI Assistant Guide

## Document Information

| Field | Value |
|-------|-------|
| **Project** | ESPHome Multi-Floor Climate Control System |
| **Version** | 1.0 |
| **Last Updated** | January 23, 2026 |
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

This is a **production ESPHome-based residential climate control system** for a three-floor HVAC installation in Milan, Italy. It's an active, live system that controls heating, cooling, and ventilation for a residential building.

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

```
esphome-devices/
├── boards/                    # Hardware board configurations
│   ├── base.yaml              # Common ESPHome settings
│   ├── a6.yaml                # KC868-A6 master board (mixing valves)
│   ├── a16.yaml               # KC868-A16 slave boards (relays)
│   ├── waveshare-s3.yaml      # ESP32-S3-POE board
│   ├── s1-pro-multi-sense.yaml # Sensor board (2157 lines)
│   ├── *_ethernet.yaml        # Ethernet network configs
│   └── wifi.yaml              # WiFi network config
│
├── components/                # Reusable YAML component packages
│   ├── pid.yaml               # PID controller (27 lines)
│   ├── pid_autotune.yaml      # Auto-tuning logic
│   ├── pid_sensors.yaml       # PID input/output sensors
│   ├── radiant.yaml           # Radiant floor heating/cooling
│   ├── fancoil.yaml           # Fancoil unit control (analog 0-10V)
│   ├── heat_only_radiant.yaml # Heat-only radiant variant
│   ├── modbus_relay_board.yaml # Relay board via Modbus
│   ├── modbus_relay_switch.yaml # Individual relay switch
│   ├── modbus_analog_output.yaml # 0-10V DAC output
│   ├── direct_pump.yaml       # Direct pump control
│   ├── mixing_pump.yaml       # Mixing valve + pump
│   ├── failover_sensor.yaml   # 3-tier sensor failover
│   ├── fancoil_boost_coordinator.yaml # Complex boost logic (313 lines)
│   ├── mev.yaml               # Mechanical Extract Ventilation (365 lines)
│   └── rooms/                 # Room-specific configurations
│       ├── ground_floor/      # Ground floor rooms
│       ├── first_floor/       # First floor rooms
│       └── second_floor/      # Second floor rooms
│
├── devices/                   # Main device configurations (entry points)
│   ├── climate-control.yaml   # Main HVAC system (2117 lines)
│   └── room-sensor-soggiorno.yaml # Standalone room sensor (372 lines)
│
├── libs/                      # Custom Python/C++ components
│   └── s1_pro/
│       ├── __init__.py        # Package marker
│       ├── sensor.py          # Python config validator (50 lines)
│       └── s1_pro.h           # C++ LD2450 radar driver
│
├── locals/                    # Local development/deployment configs
│   └── climate-control.yaml   # Wrapper for local testing
│
├── remotes/                   # Remote GitHub-based deployment configs
│   └── climate-control.yaml   # Wrapper for production deployment
│
├── docs/                      # Project documentation
│   ├── architecture-diagram.md # Mermaid diagrams
│   ├── prd.md                 # Product Requirements Document
│   ├── epic-*.md              # Sprint/epic documentation
│   ├── brief*.md              # Feature briefs
│   └── *.md                   # Various guides and docs
│
├── .bmad-core/                # Brownfield Management & Development framework
│   ├── agent-teams/           # AI agent team definitions
│   ├── agents/                # Individual agent configs
│   ├── templates/             # Document templates
│   ├── workflows/             # Development workflows
│   └── *.md                   # BMAD guides and documentation
│
├── .github/                   # GitHub workflows and chat modes
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

#### Component Configs (`components/`)
- Pattern: `[component_type]_[variant].yaml` or `[feature].yaml`
- Examples: `modbus_relay_board.yaml`, `pid_autotune.yaml`, `fancoil.yaml`
- Descriptive, function-based names

#### Room Configs (`components/rooms/`)
- Pattern: Italian room names in snake_case
- Floor aggregators: `[floor]-floor.yaml`
- Room files: `[room_name].yaml`
- Examples: `soggiorno.yaml`, `camera_nord.yaml`, `bagno_padronale.yaml`

#### Device Configs (`devices/`)
- Pattern: kebab-case descriptive names
- Examples: `climate-control.yaml`, `room-sensor-soggiorno.yaml`

### Entity Naming (Slug Pattern)

**Standard Format**: `{location}_{component}_{variant}`

Examples:
- `soggiorno_radiant` - Living room radiant floor
- `ground_floor_fancoil` - Ground floor fancoil
- `first_floor_mev` - First floor mechanical ventilation
- `pid_radiant_soggiorno` - PID controller for living room radiant
- `relay_1` through `relay_16` - Relay numbering per board

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
├── Hardware Packages (components/modbus_*_board.yaml)
└── Floor Packages (components/rooms/*/floor.yaml)
    └── Room Packages (components/rooms/*/*.yaml)
        ├── Sensors (components/room_sensors.yaml)
        ├── Radiant (components/radiant.yaml)
        ├── Fancoil (components/fancoil.yaml)
        └── Boost Coordinator (components/fancoil_boost_coordinator.yaml)
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
esphome compile locals/climate-control.yaml

# Upload to device over network
esphome run locals/climate-control.yaml

# Upload over USB (initial flash)
esphome run locals/climate-control.yaml --device /dev/ttyUSB0

# View logs
esphome logs locals/climate-control.yaml
```

### Remote/Production Deployment

```yaml
# remotes/climate-control.yaml references GitHub
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
esphome config locals/climate-control.yaml

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

1. Create room config file in `components/rooms/[floor]/[room_name].yaml`
2. Include sensor, radiant, fancoil packages with room-specific vars
3. Add room package to floor aggregator (`[floor]-floor.yaml`)
4. Assign relay numbers (ensure no conflicts)
5. Add Modbus register mappings if using remote sensors
6. Test compilation
7. Deploy and verify

Example:
```yaml
# components/rooms/ground_floor/new_room.yaml
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

| File | Lines | Purpose |
|------|-------|---------|
| `devices/climate-control.yaml` | 2117 | **Main entry point** - orchestrates entire system |
| `boards/base.yaml` | 20 | **Common settings** - logger, API, OTA for all devices |
| `boards/waveshare-s3.yaml` | ~200 | Master board hardware definition |
| `components/fancoil_boost_coordinator.yaml` | 313 | Complex boost algorithm for humidity control |
| `components/mev.yaml` | 365 | MEV ventilation control with air quality |
| `components/failover_sensor.yaml` | ~50 | 3-tier sensor failover logic |

### Key Documentation Files

| File | Purpose |
|------|---------|
| `docs/architecture-diagram.md` | Mermaid diagrams of system architecture |
| `docs/prd.md` | Product Requirements Document (61 KB) |
| `docs/epic-17-brief.md` | Latest epic: Seasonal mode automation |
| `docs/epic-16-*.md` | MEV integration documentation |
| `TODO.md` | Feature backlog (in Italian) |
| `.bmad-core/user-guide.md` | BMAD framework user guide |
| `.bmad-core/working-in-the-brownfield.md` | Brownfield development guide |

### Configuration Entry Points

| Path | Use Case |
|------|----------|
| `locals/climate-control.yaml` | Local development and testing |
| `remotes/climate-control.yaml` | Production deployment via GitHub |
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
| 2026-01-23 | 1.0 | Initial CLAUDE.md creation | AI Assistant |

---

**End of Document**

For questions or clarifications, refer to the documentation in `docs/` or the BMAD framework in `.bmad-core/`.
