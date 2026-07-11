# ESPHome Devices - AI Assistant Guide

## Document Information

| Field | Value |
|-------|-------|
| **Project** | ESPHome Multi-Floor Climate Control System |
| **Version** | 1.6 |
| **Last Updated** | July 11, 2026 |
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

This repo hosts the ESPHome systems for Alberto's three-floor residence, organized as a
**layered systems monorepo** (see `_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`):

1. **`canbus/`** (infrastructure) — a pre-live CAN bus transport system (RP2040 nodes +
   ESP32-S3 gateway): frames, heartbeats, node discovery/health, the bus definition. See
   `canbus/CLAUDE.md` for its rules and `canbus/docs/canbus-smart-home-reference.md` for
   the protocol. Merged from `afmotta/canbus` (archived) with full history; old PR `#N`
   references in `canbus/` commit messages resolve in the archived repo.
2. **`lighting/`** (application) — button decode → Home Assistant events and hold
   automations, built on the canbus transport. See `lighting/CLAUDE.md`.
3. **`hvac/`** (application) — a **pre-live ESPHome-based residential climate control
   system** for heating, cooling, and ventilation. Controller hardware is decided and
   implemented (ADR-0014: LilyGO T-Connect Pro + Modbus RTU I/O boards) but not yet
   physically deployed. Consumes `registry/map.json` and sensor CAN frames directly
   (contract lives in-repo). See `hvac/CLAUDE.md`.
4. **`vesta/`** (library) — the extractable, open-source climate-control component
   framework that `hvac/` composes from.

BMAD epics are namespaced: **CAN-Epic N** (canbus), **LIGHT-Epic N** (lighting),
**HVAC-Epic N** (climate). Historical canbus BMAD artifacts stay under
`canbus/_bmad-output/`; new artifacts for all systems go to the root `_bmad-output/`.

### System Capabilities

- **Multi-zone climate control**: 13 independently controlled temperature zones across 3 floors
- **Dual-mode operation**: Radiant floor heating/cooling + fancoil units
- **Advanced PID control**: Precise temperature management with auto-tuning
- **Mechanical Extract Ventilation (MEV)**: Air quality monitoring and control
- **Autonomous operation**: all relay/analog/MEV actuation runs on the one controller (the sole Modbus master) regardless of Home Assistant; room-sensor *data* specifically depends on the CAN→HA failover chain (`hvac/room_sensors.yaml`)
- **Home Assistant integration**: Full monitoring, dashboards, and overrides when available
- **Multi-tier failover**: Graceful degradation (CAN → HA → Emergency shutdown)

### Building Layout

- **Ground Floor (Piano Terra)**: 5 zones (soggiorno/living room, cucina/kitchen, bagno/bathroom, anticamera/entry hall, locale tecnico/technical room)
- **First Floor (Primo Piano)**: 8 zones (4 bedrooms, 4 bathrooms, laundry room)
- **Second Floor (Secondo Piano)**: 1 zone (sottotetto/attic)

### Hardware

Standardized per ADR-0014 — the same three devices serve both the HVAC and lighting systems, so one shelf of spares covers the whole house:

- **LilyGO T-Connect Pro**: ESP32-S3 controller with W5500 Ethernet and native RS485 + CAN transceivers — used as both the HVAC master (`devices/climate-control.yaml`) and the CAN-bus/lighting gateway (`devices/gateway.yaml`)
- **Waveshare Modbus RTU Relay 32CH**: 32-channel relay bank on RS485 — zone/pump switching (hvac) and lighting circuits (gateway), both at mirrored address `0x2`
- **Waveshare Modbus RTU Analog Output 8CH (B)**: 0-10V outputs (voltage variant) — fancoil/mixing-valve modulation (hvac only, address `0x1`)
- **S1 Pro Multi-Sense**: Custom sensor boards with LD2450 radar, air quality sensors
- **RS485 Modbus RTU**: single-master bus per system, target 38400 8E1 (pending the bring-up parity check, ADR-0014 §4)

---

## Tech Stack

### Primary Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **ESPHome** | 2026.5.0+ | ESP32 firmware framework (YAML-based); 2026.5.0 floor set by `boards/t-connect-pro.yaml` (`sntp`/`ds2484` verified there) |
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
- `homeassistant` platform - Room-sensor data from HA (primary failover tier)
- `udp` / `packet_transport` - Board-to-board communication

### External APIs

- **OpenWeather API** (planned): Weather forecast integration for seasonal mode automation
- **Home Assistant API**: ESPHome Native API for monitoring and fallback sensor data

---

## Repository Structure

This is a **layered systems monorepo** (see `ARCHITECTURE-SPINE.md`, AD-1/AD-10): one
shared infrastructure layer (`canbus/`), two application systems on top (`lighting/`,
`hvac/`), one extractable library (`vesta/`), and a `devices/` composition layer where
deployable entry points assemble packages across systems. **Each in-repo system directory
(`canbus/`, `lighting/`, `hvac/`) carries its own `CLAUDE.md` with its own rules** — this
root file is the map, not the rulebook (AD-10). Read the relevant system's `CLAUDE.md`
before working inside it. `vesta/` is the one exception: it's an extractable open-source
library with its own `README.md`/`CONTRIBUTING.md` instead of a `CLAUDE.md`.

```
esphome-devices/
├── registry/                  # house system-of-record (nodes.csv, node_id_hwm, bindings.yaml,
│                               #   map.json); per-file ownership, see registry/README.md
├── canbus/                    # CAN bus infrastructure system (see canbus/CLAUDE.md)
│   ├── protocol/               # Wire protocol + arbitration headers, native tests' target
│   ├── packages/               # Node-side and gateway-side ESPHome packages
│   ├── nodes/                  # Generated node firmware (never hand-edited)
│   ├── tools/                  # Registry/generator tooling (generate_nodes.py, etc.)
│   ├── tests/                  # Python + native C++ tests
│   ├── home-assistant/         # Arbitration automations, generated manifest package
│   ├── docs/                   # Protocol reference, runbooks
│   └── _bmad-output/           # Historical CAN-epic artifacts (frozen)
│
├── lighting/                  # Lighting application system (see lighting/CLAUDE.md)
│   ├── packages/               # Button-decode/HA-event + fallback packages
│   └── home-assistant/         # Hold automations
│
├── hvac/                       # HVAC (climate control) application system (see hvac/CLAUDE.md)
│   ├── room_sensors.yaml      # Room sensor failover wiring
│   ├── mev_modbus.yaml        # MEV Modbus device driver
│   ├── mev_demand.yaml        # MEV demand signal aggregation
│   ├── rooms/                 # Room-specific configurations
│   │   ├── ground_floor/      # Ground floor rooms
│   │   ├── first_floor/       # First floor rooms
│   │   └── second_floor/      # Second floor rooms
│   └── home-assistant/        # Dashboards (Lovelace)
│
├── vesta/                     # Vesta Climate Framework (open-source library, see vesta docs)
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
├── boards/                    # Board hardware definitions (shared, no owning system)
│   ├── t-connect-pro.yaml / t-connect-pro-ethernet.yaml / t-connect-pro-wifi.yaml # LilyGO T-Connect Pro (both controllers, ADR-0014)
│   ├── s1-pro-multi-sense.yaml # Sensor board
│   ├── base.yaml               # Legacy common settings (Gen-1 a6/a16 era; no current consumer)
│   └── wifi.yaml                # Legacy WiFi network config (Gen-1 a6/a16 era; no current consumer)
│
├── devices/                   # Main device configurations (entry points and their deployment variants, gathered together)
│   ├── climate-control.yaml   # Main HVAC system
│   ├── room-sensor-soggiorno.yaml # Standalone room sensor
│   ├── wall-sensor.yaml       # Wall-mounted sensor (SEN66)
│   ├── gateway.yaml           # CAN bus gateway firmware (composes canbus + lighting packages)
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
├── scripts/                   # Repo-level helper scripts (currently empty)
├── secrets.yaml               # (gitignored) Credentials and secrets
└── TODO.md                    # Feature backlog (Italian)
```

---

## Key Conventions

### File Naming Conventions

#### Board Configs (`boards/`)
- Pattern: `[board_model]-[optional_variant].yaml`
- Examples: `t-connect-pro.yaml`, `s1-pro-multi-sense.yaml`
- Network configs: `[board]-ethernet.yaml`, `[board]-wifi.yaml`

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
├── Board Package (boards/t-connect-pro.yaml)
│   └── Network Package (boards/t-connect-pro-ethernet.yaml or -wifi.yaml)
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

### Modbus Communication Architecture

**Single-master pattern** (ADR-0014; see `hvac/CLAUDE.md` for bus members, register
details, and polling intervals):
- One T-Connect Pro controller is the sole Modbus RTU master per system (hvac's
  `rs485_bus`; the gateway has its own, mirroring the relay bank address `0x2`)
- Commodity I/O boards (Relay 32CH, Analog Output 8CH (B), MEV) are polled/written
  directly — there are no slave controller boards and no board-to-board Modbus
- Room-sensor data does **not** travel over Modbus — it arrives via CAN/HA failover
  (see below)

### Failover Architecture

**2-Tier Sensor Failover** (implemented in `failover_sensor.yaml`, wired by `hvac/room_sensors.yaml`):

1. **Primary**: CAN sensor-kit measurement (received directly on the controller's own CAN interface)
2. **Fallback**: Home Assistant sensor (`homeassistant` platform)
3. **Emergency**: Return NAN → triggers safe shutdown after 5 minutes

**Automatic Recovery**: System automatically switches back to HA when its sensor recovers.

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

HVAC-specific tasks (adding a room, modifying PID parameters, adding/debugging Modbus
devices) are documented in `hvac/CLAUDE.md` — house-wide tasks only are listed here.

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
| `devices/gateway.yaml` | CAN bus / lighting gateway entry point |
| `boards/t-connect-pro.yaml` | Shared controller board (both entry points, ADR-0014) |
| `vesta/packages/coordinators/fancoil_boost.yaml` | Radiant+fancoil boost coordination |
| `vesta/packages/coordinators/mev_ventilation.yaml` | MEV ventilation control |
| `vesta/packages/components/failover_sensor.yaml` | 2-tier sensor failover logic |
| `hvac/mev_modbus.yaml` | MEV Modbus device driver (project-specific) |

### Key Documentation Files

| File | Purpose |
|------|---------|
| `_bmad-output/planning-artifacts/architecture-diagram.md` | Mermaid diagrams of system architecture |
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

- **Polling Intervals**: Don't poll Modbus I/O boards more frequently than necessary (relay/analog 2s, MEV 30s — see `hvac/CLAUDE.md`)
- **Update Intervals**: Balance responsiveness vs. network traffic
- **Logger Level**: Use INFO in production, DEBUG only for troubleshooting
- **Conditional Compilation**: Disable unused features

### Home Assistant Integration

- **Dual Operation**: Design actuation to run autonomously; HA enhances monitoring/overrides
- **Sensor Failover**: Room sensors are CAN-primary with a Home Assistant fallback tier (`hvac/room_sensors.yaml`) — always keep a non-HA tier for critical sensors
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
| gruppo miscelazione | mixing valve group | Historical Gen-1 master controller name (retired) |
| distribuzione | distribution | Historical Gen-1 slave-board naming pattern (retired) |
| radiante | radiant | Radiant floor heating/cooling |

**Note**: Comments and documentation are in English, but entity IDs often use Italian room names.

---

## Getting Help

### Documentation Resources

1. **Architecture**: `_bmad-output/planning-artifacts/architecture-diagram.md` - System topology and data flows
2. **PRD**: `_bmad-output/planning-artifacts/prd.md` - Original project requirements
3. **Epics**: `_bmad-output/implementation-artifacts/epic-*.md` - Feature development history
4. **BMAD Guide**: `.bmad-core/user-guide.md` - Development framework
5. **ESPHome Docs**: https://esphome.io/ - Platform documentation

### Troubleshooting

**Compilation Errors**:
- Check YAML syntax (indentation, colons, dashes)
- Verify all `!include` paths are correct
- Ensure all substitution variables are defined
- Check ESPHome version (min 2026.5.0 for the T-Connect Pro entry points)

**Sensor Failover**:
- Check failover logs in Home Assistant
- Ensure the CAN sensor-kit path (Tier 1) is available and updating
- Verify Home Assistant sensors (Tier 2) are arriving when CAN drops out
- Monitor emergency shutdown triggers

HVAC-specific troubleshooting (Modbus issues, PID tuning) and the Modbus register/relay/
sensor-address appendices and PID tuning guidelines are documented in `hvac/CLAUDE.md`.

### Community and Support

- **ESPHome Discord**: https://discord.gg/KhAMKrd
- **Home Assistant Community**: https://community.home-assistant.io/
- **ESPHome GitHub**: https://github.com/esphome/esphome

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-07-11 | 1.6 | HVAC-1.4: `hvac/room_sensors.yaml` flipped to CAN-primary/HA-secondary/Emergency failover (was HA-primary/UDP-secondary); updated failover-order bullets, the Failover Architecture section, and Best Practices/Troubleshooting sensor-failover language accordingly | AI Assistant |
| 2026-07-11 | 1.5 | ADR-0014 P6 hardware docs sweep: Hardware table rewritten to the standardized family (LilyGO T-Connect Pro + Waveshare Relay 32CH + Analog Output 8CH (B)); retired all Gen-1 controller/slave-board and Modbus-room-sensor claims; corrected autonomy story (single Modbus master; room sensors HA→UDP→Emergency); deleted the orphaned Gen-1 and ESP32-S3-POE board files and updated all references; ESPHome floor 2026.5.0 | AI Assistant |
| 2026-07-07 | 1.4 | Migration Phase 6b: rewrote Repository Structure to the actual four-system tree (canbus/lighting/hvac/vesta + top-level registry/devices); removed the "predates restructure" note; moved HVAC-only rules (entity-ID convention, PID architecture, Modbus/relay appendices, HVAC Common Tasks) to `hvac/CLAUDE.md` per AD-10 (root is the map, not the rules) | AI Assistant |
| 2026-07-05 | 1.3 | Corrected climate-control status from "production/active, live" to pre-live; controller hardware swap under consideration | AI Assistant |
| 2026-07-05 | 1.2 | Merged afmotta/canbus as canbus/ subtree; documented two-subsystem layout and epic namespacing | AI Assistant |
| 2026-03-23 | 1.1 | Updated repo structure for Vesta extraction, added entity ID naming convention, updated file references for Epics 18-20 | AI Assistant |
| 2026-01-23 | 1.0 | Initial CLAUDE.md creation | AI Assistant |

---

**End of Document**

For questions or clarifications, refer to the documentation in `docs/` or the BMAD framework in `.bmad-core/`.
