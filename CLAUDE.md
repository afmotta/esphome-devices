# ESPHome Devices - AI Assistant Guide

## Document Information

| Field | Value |
|-------|-------|
| **Project** | ESPHome Multi-Floor Climate Control System |
| **Version** | 1.17 |
| **Last Updated** | August 14, 2026 |
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
**layered systems monorepo** (see `docs/architecture/ARCHITECTURE-SPINE.md`):

1. **`canbus/`** (infrastructure) — a pre-live CAN bus transport system (RP2040 nodes +
   ESP32-S3 health monitor): frames, heartbeats, node discovery/health, the bus definition. See
   `canbus/CLAUDE.md` for its rules and `canbus/docs/canbus-smart-home-reference.md` for
   the protocol. Merged from `afmotta/canbus` (archived) with full history; old PR `#N`
   references in `canbus/` commit messages resolve in the archived repo.
2. **`lighting/`** (application) — button decode → Home Assistant events and hold
   automations, built on the canbus transport. See `lighting/CLAUDE.md`.
3. **`climate/`** (application) — a **pre-live ESPHome-based residential climate control
   system** for heating, cooling, and ventilation. Controller hardware is decided and
   implemented (ADR-0014: LilyGO T-Connect Pro + Modbus RTU I/O boards) but not yet
   physically deployed. Consumes `registry/map.json` and sensor CAN frames directly
   (contract lives in-repo). See `climate/CLAUDE.md`.
4. **Top-level `packages/`** — shared ESPHome packages that do not belong to a
  single application system, currently the Modbus I/O hardware drivers used by
  both Climate and lighting.

Commits are prefixed with the system they touch (`canbus:`, `lighting:`, `climate:`). The
durable design knowledge — architecture, ADRs, contracts, design notes — lives under `docs/`
(see [Important Files Reference](#important-files-reference)).

### System Capabilities

- **Multi-zone climate control**: 13 independently controlled temperature zones across 3 floors
- **Dual-mode operation**: Radiant floor heating/cooling + fancoil units
- **Hybrid radiant + fancoil cooling ("base + boost")**: radiant floor/ceiling provides efficient baseline comfort; fancoils activate as a responsive boost layer when radiant cannot meet demand — evaluated independently per room (`climate/packages/coordinators/fancoil_boost.yaml`)
- **Advanced PID control**: Precise temperature management with auto-tuning
- **Autonomous dew-point protection**: ESPHome-native dew-point calculation enforces a safety minimum on radiant-cooling supply water (dew point + 2 °C) even when Home Assistant is offline
- **Window-aware climate response**: an open window pauses fancoil control after a grace period while radiant keeps running (thermal-mass characteristics make it safe)
- **Three-tier seasonal mode selection**: automated heat/cool mode via calendar hard-locks plus demand-driven shoulder-season transitions (`climate/packages/coordinators/seasonal_mode.yaml`)
- **Mechanical Extract Ventilation (MEV)**: two Modbus-controlled units of different models — the first-floor Cappellotto Air Fresh I with air-quality- and humidity-driven demand plus a dehumidification/integration cascade, alarm decoding, and filter-hour tracking (`climate/mev_modbus.yaml`, `climate/packages/coordinators/mev_ventilation.yaml`); and the ground-floor Innova HRP DOMO 60 HX, a passive **enthalpic** HRV driven by CO2/air-quality **and** humidity demand — high humidity raises ventilation and the enthalpic core passively manages moisture, so there is no active dehumidification cascade (its only actuator is fan speed) — on the shared 3-channel demand with a fan-only coordinator (`climate/mev_innova_modbus.yaml`, `climate/packages/coordinators/mev_ventilation_fan_only.yaml`; ADR-0018)
- **Autonomous operation**: all relay/analog/MEV actuation runs on the one controller (the sole Modbus master) regardless of Home Assistant; room-sensor *data* specifically depends on the CAN→HA failover chain (`climate/room_sensors.yaml`)
- **Home Assistant integration**: Full monitoring, dashboards, and overrides when available
- **Multi-tier failover**: Graceful degradation (CAN → HA → Emergency shutdown)

### Building Layout

- **Ground Floor (Piano Terra)**: 5 zones (soggiorno/living room, cucina/kitchen, bagno/bathroom, anticamera/entry hall, locale tecnico/technical room)
- **First Floor (Primo Piano)**: 8 zones (4 bedrooms, 4 bathrooms, laundry room)
- **Second Floor (Secondo Piano)**: 1 zone (sottotetto/attic)

### Hardware

Standardized per ADR-0014 — the same three devices serve both the Climate and lighting systems, so one shelf of spares covers the whole house:

- **LilyGO T-Connect Pro**: ESP32-S3 controller with W5500 Ethernet and native RS485 + CAN transceivers — used as both the Climate controller (`devices/climate-control.yaml`) and the lighting controller (`devices/light-controller.yaml`)
- **Waveshare ESP32-S3-RS485-CAN**: WiFi-only ESP32-S3 board with isolated CAN + RS485 — the dedicated CAN bus health monitor (`devices/health-monitor.yaml`), split off the former combined gateway per ADR-0015
- **Waveshare Modbus RTU Relay 32CH**: 32-channel relay bank on RS485 — zone/pump switching (climate) and lighting circuits (lighting controller), both at mirrored address `0x2`
- **Waveshare Modbus RTU Analog Output 8CH (B)**: 0-10V outputs (voltage variant) — fancoil/mixing-valve modulation (climate only, address `0x1`)
- **S1 Pro Multi-Sense**: Custom sensor boards with LD2450 radar, air quality sensors
- **RS485 Modbus RTU**: single-master bus per system, target 38400 8E1 (pending the bring-up parity check, ADR-0014 §4)

---

## Tech Stack

### Primary Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **ESPHome** | 2026.7.0+ | ESP32 firmware framework (YAML-based); 2026.7.0 floor set by `boards/t-connect-pro.yaml` (2026.7.0 modbus hub overhaul — explicit `send_wait_time`/`turnaround_time` pinned in the entry points) and `boards/canbed-rp2040.yaml` (`rp2040:` → `rp2:` platform rename) |
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

This is a **layered systems monorepo** (see `docs/architecture/ARCHITECTURE-SPINE.md`, AD-1/AD-10): one
shared infrastructure layer (`canbus/`), two application systems on top (`lighting/`,
`climate/`), a small shared package layer (`packages/`), and a `devices/` composition layer where
deployable entry points assemble packages across systems. **Each in-repo system directory
(`canbus/`, `lighting/`, `climate/`) carries its own `CLAUDE.md` with its own rules** — this
root file is the map, not the rulebook (AD-10). Read the relevant system's `CLAUDE.md`
before working inside it. Climate-control reusable packages now live under `climate/packages/`;
shared hardware drivers live under top-level `packages/`.

```
esphome-devices/
├── registry/                  # house system-of-record (nodes.csv, node_id_hwm, bindings.yaml,
│                               #   map.json); per-file ownership, see registry/README.md
├── canbus/                    # CAN bus infrastructure system (see canbus/CLAUDE.md)
│   ├── protocol/               # Wire protocol + arbitration headers, native tests' target
│   ├── packages/               # Node-side and gateway-side ESPHome packages
│   ├── nodes/                  # Generated node/bridge firmware (never hand-edited; registry `profile`)
│   ├── tools/                  # Registry/generator tooling (generate_nodes.py, etc.)
│   ├── tests/                  # Python + native C++ tests
│   ├── home-assistant/         # Arbitration automations, generated manifest package
│   └── docs/                   # Protocol reference, runbooks
│
├── lighting/                  # Lighting application system (see lighting/CLAUDE.md)
│   ├── packages/               # Button-decode/HA-event + fallback packages
│   └── home-assistant/         # Hold automations
│
├── climate/                       # Climate control application system (see climate/CLAUDE.md)
│   ├── room_sensors.yaml      # Room sensor failover wiring
│   ├── mev_modbus.yaml        # MEV Modbus driver — first floor (Cappellotto, w/ humidity cascade)
│   ├── mev_innova_modbus.yaml # MEV Modbus driver — ground floor (Innova HRP DOMO 60 HX enthalpic, fan-only; ADR-0018)
│   ├── mev_demand.yaml        # MEV demand signal aggregation (CO2/air-quality/humidity; both MEVs)
│   ├── packages/              # Climate-owned reusable components/coordinators and generated routes
│   │   ├── components/        # PID, radiant/fancoil, failover, demand, pump packages
│   │   ├── coordinators/      # Seasonal mode, fancoil boost, MEV ventilation
│   │   └── generated/         # Generated CAN sensor routes (never hand-edited)
│   ├── rooms/                 # Room-specific configurations
│   │   ├── ground_floor/      # Ground floor rooms
│   │   ├── first_floor/       # First floor rooms
│   │   └── second_floor/      # Second floor rooms
│   └── home-assistant/        # Dashboards (Lovelace)
│
├── packages/                  # Cross-system ESPHome packages (shared, no owning app system)
│   ├── devices/modbus-io/     # Relay/analog Modbus I/O board drivers used by climate + lighting
│   └── ui/dark_theme.yaml     # Shared LVGL dark theme for both T-Connect Pro onboard panels
│
├── boards/                    # Board hardware definitions (shared, no owning system)
│   ├── t-connect-pro.yaml / t-connect-pro-ethernet.yaml / t-connect-pro-wifi.yaml # LilyGO T-Connect Pro (both controllers, ADR-0014)
│   ├── canbed-rp2040.yaml   # Longan Labs CANBed RP2040 node board (CAN bus button/sensor nodes)
│   ├── canbed-rp2040-can1.yaml # Second MCP2515 add-on for the CANBed (segment bridges, ADR-0017)
│   ├── lilygo-t-2can.yaml   # LilyGO T-2CAN dual-CAN board (preferred segment bridge, ADR-0017)
│   ├── s1-pro-multi-sense.yaml # Sensor board
│   ├── base.yaml               # Legacy common settings (Gen-1 a6/a16 era; no current consumer)
│   └── wifi.yaml                # Legacy WiFi network config (Gen-1 a6/a16 era; no current consumer)
│
├── devices/                   # Main device configurations (entry points and their deployment variants, gathered together)
│   ├── climate-control.yaml   # Main Climate system
│   ├── room-sensor-soggiorno.yaml # Standalone room sensor
│   ├── wall-sensor.yaml       # Wall-mounted sensor (SEN66)
│   ├── light-controller.yaml  # Lighting controller firmware (button events + relay bank; ADR-0015)
│   ├── health-monitor.yaml    # CAN bus health monitor firmware (transport health; ADR-0015)
│   ├── secrets.yaml.example   # Template for devices/secrets.yaml (device secrets)
│   ├── locals/                # Local development/deployment configs
│   └── remotes/               # Remote GitHub-based deployment configs
│
├── libs/                      # Custom Python/C++ components
│   ├── s1_pro/                # LD2450 radar driver
│   └── esphome_overrides/     # Local FORKS of core ESPHome components (shadow the built-ins)
│       └── ethernet/          # W5500 sharing one SPI controller with the onboard display (ADR-0016)
│                              #   ⚠ pinned to ESPHome 2026.7.1 — re-verify on every upgrade
│
├── docs/                      # Project knowledge base and guides
│   ├── adr/                    # Architecture Decision Records (ADR-0001…0017, the "why")
│   ├── architecture/          # ARCHITECTURE-SPINE.md (invariants) + architecture-diagram.md
│   ├── contracts/             # Frozen cross-system contracts (map.json, bindings arbitration)
│   ├── design-notes/          # Entity-naming convention, canbus implementation rules
│   └── (runbooks, wiring guides, HA config assets)
│
├── docs-site/                 # Maintenance & support site (MkDocs, EN + IT; GitHub Pages)
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

#### Component Configs (`climate/`)
- Pattern: `[component_type]_[variant].yaml` or `[feature].yaml`
- Examples: `modbus_relay_board.yaml`, `pid_autotune.yaml`, `fancoil.yaml`
- Descriptive, function-based names

#### Room Configs (`climate/rooms/`)
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
├── Hardware Packages (packages/devices/modbus-io/modbus_relay_board.yaml)
└── Floor Packages (climate/rooms/*/floor.yaml)
    └── Room Packages (climate/rooms/*/*.yaml)
        ├── Sensors (climate/room_sensors.yaml)
        ├── Radiant (climate/packages/components/radiant.yaml)
        ├── Fancoil (climate/packages/components/fancoil.yaml)
        └── Boost Coordinator (climate/packages/coordinators/fancoil_boost.yaml)
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

**Single-master pattern** (ADR-0014; see `climate/CLAUDE.md` for bus members, register
details, and polling intervals):
- One T-Connect Pro controller is the sole Modbus RTU master per system (the Climate controller's
  `rs485_bus`; the lighting controller has its own, mirroring the relay bank address `0x2`)
- Commodity I/O boards (Relay 32CH, Analog Output 8CH (B), MEV) are polled/written
  directly — there are no slave controller boards and no board-to-board Modbus
- Room-sensor data does **not** travel over Modbus — it arrives via CAN/HA failover
  (see below)

### Failover Architecture

**2-Tier Sensor Failover** (implemented in `failover_sensor.yaml`, wired by `climate/room_sensors.yaml`):

1. **Primary**: CAN sensor-kit measurement (received directly on the controller's own CAN interface)
2. **Fallback**: Home Assistant sensor (`homeassistant` platform)
3. **Emergency**: Return NAN → triggers safe shutdown after 5 minutes

**Automatic Recovery**: System automatically switches back to HA when its sensor recovers.

---

## Development Workflow

### Development Process

Keep it lightweight: land the change, and record any significant decision as a new ADR
under `docs/adr/` (with the alternatives and trade-offs considered). There is no
brief/checklist/completion-report ceremony.

### Git Workflow

```bash
# Typical workflow
git status                      # Check current state
git add [specific files]        # Stage specific files (avoid git add -A)
git commit -m "climate: [description]"   # prefix with the system touched
git push origin [branch]
```

**Git Conventions**:
- Commit messages: clear and descriptive, prefixed with the system touched (`canbus:`, `lighting:`, `climate:`) when it applies
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

### Upgrading ESPHome — required fork check

`libs/esphome_overrides/ethernet/` is a **local fork of a core ESPHome component**, copied from
2026.7.1 and carrying two changes that let the W5500 share an SPI controller with the onboard
display (ADR-0016). Upstream owes it no compatibility, so **every ESPHome version bump must**:

1. Diff the new upstream `esphome/components/ethernet/` against `libs/esphome_overrides/ethernet/`
   and re-apply the two changes (tolerate `ESP_ERR_INVALID_STATE` in
   `ethernet_component_esp32.cpp`; downgrade `_final_validate_spi`'s same-interface error in
   `__init__.py`). Both are marked `LOCAL FORK (esphome-devices)` in the source.
2. Re-run the bring-up check by flashing `devices/locals/climate-control-touch.yaml` — the
   Ethernet + panel build is itself the regression harness, since it exercises the shared bus in
   exactly the arrangement the fork enables. Confirm all three:
   - the boot log shows `SPI host 2 already initialized (shared with 'spi:')` — proof the shared
     path was taken rather than the old two-controller failure;
   - the status strip's liveness dot keeps pulsing, i.e. the display is still being flushed (a
     frozen dot is the "panel died" signal the old debug build's tick counter provided);
   - the dot stays green, i.e. the API — and therefore Ethernet — survived alongside it.

   Under load: switch tabs repeatedly (each is a full-screen repaint) while pinging the device.
   The fork's risk is the display holding the SPI bus long enough to stall the W5500, so packet
   loss or API drops during redraws is the failure to watch for.

Skipping this does not fail the build — it fails the *panel*, silently, at runtime.

The dedicated `t-connect-pro-debug*.yaml` bring-up harness that originally proved this was removed
on 2026-07-26 (its diagnosis is preserved in ADR-0016 and in the comments in
`boards/t-connect-pro-display.yaml`). If a future upgrade breaks the shared bus and you need to
bisect it away from the full climate config, ADR-0016 §Verification describes the three-way
experiment — spi3+Ethernet (fails), spi3+WiFi (control), spi2+Ethernet (fix) — well enough to
rebuild a throwaway harness from the board file.

### Testing Levels

1. **Component Testing**: Test individual component packages in isolation
2. **Integration Testing**: Test full device config compilation (`esphome config`)
3. **Hardware Testing**: Deploy to test board, verify outputs
4. **Verification battery**: `scripts/verification-battery.sh` — the native/Python test
   suite plus `esphome config`/`compile` gates that CI (`.github/workflows/verify.yml`) runs

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

Climate-specific tasks (adding a room, modifying PID parameters, adding/debugging Modbus
devices) are documented in `climate/CLAUDE.md` — house-wide tasks only are listed here.

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
| `devices/light-controller.yaml` | Lighting controller entry point (button events + relay bank) |
| `devices/health-monitor.yaml` | CAN bus health monitor entry point (transport health, ADR-0015) |
| `boards/t-connect-pro.yaml` | Shared controller board (both entry points, ADR-0014) |
| `climate/packages/coordinators/fancoil_boost.yaml` | Radiant+fancoil boost coordination |
| `climate/packages/coordinators/mev_ventilation.yaml` | MEV ventilation control |
| `climate/packages/components/failover_sensor.yaml` | 2-tier sensor failover logic |
| `climate/mev_modbus.yaml` | MEV Modbus device driver (project-specific) |
| [Maintenance Guide](https://afmotta.github.io/esphome-devices/) (`docs-site/`) | Practical, non-expert-oriented operations/troubleshooting/hardware-replacement site (EN + IT), deployed via GitHub Pages |

### Key Documentation Files

| File | Purpose |
|------|---------|
| `docs/architecture/ARCHITECTURE-SPINE.md` | Architectural invariants (AD-1…AD-10) — the current authority |
| `docs/architecture/architecture-diagram.md` | Mermaid diagrams of system topology and data flows |
| `docs/adr/` | Architecture Decision Records (ADR-0001…0019) — the reasoning behind decisions |
| `docs/contracts/` | Frozen cross-system contracts (`map.json`, bindings arbitration) |
| `docs/design-notes/entity-naming.md` | Entity ID naming convention |
| `docs/design-notes/canbus-implementation-rules.md` | CAN firmware implementation rules (lambda safety, protocol header, codegen) |
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
6. **Record Decisions**: Capture any significant decision as a new ADR under `docs/adr/`

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

- **Polling Intervals**: Don't poll Modbus I/O boards more frequently than necessary (relay/analog 2s, MEV 30s — see `climate/CLAUDE.md`)
- **Update Intervals**: Balance responsiveness vs. network traffic
- **Logger Level**: Use INFO in production, DEBUG only for troubleshooting
- **Conditional Compilation**: Disable unused features

### Home Assistant Integration

- **Dual Operation**: Design actuation to run autonomously; HA enhances monitoring/overrides
- **Sensor Failover**: Room sensors are CAN-primary with a Home Assistant fallback tier (`climate/room_sensors.yaml`) — always keep a non-HA tier for critical sensors
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

1. **Architecture**: `docs/architecture/ARCHITECTURE-SPINE.md` (invariants) and
   `docs/architecture/architecture-diagram.md` (topology and data flows)
2. **Decisions**: `docs/adr/` - the reasoning behind significant decisions (ADR-0001…0019)
3. **Maintenance & support**: https://afmotta.github.io/esphome-devices/ (`docs-site/`)
4. **ESPHome Docs**: https://esphome.io/ - Platform documentation

### Troubleshooting

**Compilation Errors**:
- Check YAML syntax (indentation, colons, dashes)
- Verify all `!include` paths are correct
- Ensure all substitution variables are defined
- Check ESPHome version (min 2026.7.0 for the T-Connect Pro and CAN-node entry points)

**Sensor Failover**:
- Check failover logs in Home Assistant
- Ensure the CAN sensor-kit path (Tier 1) is available and updating
- Verify Home Assistant sensors (Tier 2) are arriving when CAN drops out
- Monitor emergency shutdown triggers

Climate-specific troubleshooting (Modbus issues, PID tuning) and the Modbus register/relay/
sensor-address appendices and PID tuning guidelines are documented in `climate/CLAUDE.md`.

### Community and Support

- **ESPHome Discord**: https://discord.gg/KhAMKrd
- **Home Assistant Community**: https://community.home-assistant.io/
- **ESPHome GitHub**: https://github.com/esphome/esphome

---

## Changelog

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2026-08-14 | 1.17 | Added the QuinLED-An-Quad as a second lighting LED-strip controller and **CAN actuator node** (ADR-0021), a 4-channel, WiFi-only sibling of the An-Penta-Plus that **reuses ADR-0020's `CAT_OUTPUT` slice unchanged**. Board scaffolding (`boards/an-quad.yaml`; classic ESP32, four raw LEDC channels on GPIO16/17/5/19) and a lighting entry point (`devices/an-quad-1.yaml`) composing two `cwww` tunable-white strips over the four channels; WiFi + HA for normal control (`api: reboot_timeout: 0s`). Because the board has **no Ethernet PHY**, WiFi is declared **inline** in the board file — no `-wifi`/`-ethernet` split, no `network_package` indirection, no `enable_ethernet` toggle (the swappable-network pattern only earns its keep on the An-Penta-Plus, which has both). The HA-down fallback joins the house bus via an external SN65HVD230 transceiver on the An-Quad's spare expansion-header GPIOs (not a QWIIC header — the An-Quad has none), **GPIO22 (tx) / GPIO23 (rx), confirmed from the schematic**, isolated as `aux_gpio_1`/`aux_gpio_2` substitutions. The actuator YAML was **generalized**: `an_penta_can.yaml` → board-neutral `lighting/packages/led_can_actuator.yaml`, now composed by **both** `devices/an-penta-1.yaml` and `devices/an-quad-1.yaml` (they differed only in comments; board specifics — pins, channel wiring — live in the entry points). First-class registry node (node 103, new external-actuator profile `led-quad` beside `led-penta` in `generate_nodes.py` — reserves node_id + `node_map`/`map.json`/health, generates no node YAML). No protocol/binding/dispatch change — the `CAT_OUTPUT` slice, `BindingEntry`, and gateway fallback are reused verbatim; empty-manifest hash `d66767448ba37b2f` unchanged. Both actuator entry points (`an-penta-1`, `an-quad-1`) were added to CI's `esphome config` validate list + `ci-dummy-secrets.sh`, closing the gap where the An-Penta (ADR-0020) had no CI config-validation. Registry artifacts regenerate cleanly; native/Python battery passes (esphome CLI not available in-env for the local compile) | AI Assistant |
| 2026-08-11 | 1.16 | Added the QuinLED-An-Penta-Plus as a lighting LED-strip controller and integrated it as a **CAN actuator node** (ADR-0020). Board scaffolding (`boards/an-penta-plus.yaml` + `-ethernet`/`-wifi`; classic ESP32 + LAN8720, five raw LEDC channels, QWIIC expansion header) and a lighting entry point (`devices/an-penta-1.yaml`) composing two `cwww` tunable-white strips; it keeps WiFi + HA for normal control (`api: reboot_timeout: 0s` so it survives HA outages). The **HA-down fallback goes over a dedicated CAN channel, not HTTP**: the protocol's reserved `CAT_OUTPUT` slice is realized (`MSG_OUT_SET_CHANNEL` in `canbus_protocol.h`); the An-Penta joins the house bus via an external SN65HVD230 transceiver on the QWIIC header and applies OUTPUT commands to its strips (`lighting/packages/an_penta_can.yaml`), as a first-class registry node (node 102, new **external-actuator** profile `led-penta` in `generate_nodes.py` — reserves node_id + `node_map`/`map.json`/health, generates no node YAML). The binding manifest gains a first-class `output: <node>/<channel>` target beside `relay:` (frozen-additive `BindingEntry`: `target_kind`/`target_node_id`/`channel` — SPEC + drift test updated; empty-manifest hash `d66767448ba37b2f` unchanged), and the gateway fallback (`fire_binding_fallback`) sends a `CAT_OUTPUT` frame on `can0` instead of driving a relay. **Supersedes the withdrawn HTTP approach** (relay-id-32 overload, `web_server` POST). Protocol/binding/dispatch logic natively tested; both devices' firmware compiles | AI Assistant |
| 2026-08-07 | 1.15 | Removed the BMAD framework and all its tooling (`_bmad/`, the `bmad-*` skills, the OpenCode `.opencode/` and Copilot `.github/agents/`+`.github/chatmodes/` integrations) and consolidated the generated artifacts into a leaner knowledge base under `docs/`: unified ADRs 0001–0017 into `docs/adr/`, the architecture spine + diagram into `docs/architecture/`, the two frozen contracts into `docs/contracts/`, and the entity-naming + canbus implementation rules into `docs/design-notes/`; dropped the process history (completion reports, testing checklists, sprint/workflow status, retros, review passes, per-story files, phase specs, migration metas) and the superseded Oct-2025 PRD/architecture docs. Both `_bmad-output/` trees are gone. Also retired the **epic** organizing concept: the epics index/file is gone, its durable feature knowledge folded into System Capabilities, and the forward-going epic-prefixed commit convention replaced with plain system-prefixed commits (`canbus:`/`lighting:`/`climate:`); historical "Epic N" mentions in git history and ADR prose are left as-is. Repointed all cross-references (this file, the three system `CLAUDE.md`s, `docs-site` doc-map/confidence-ledger, canbus README/runbooks, dashboards) | AI Assistant |
| 2026-08-04 | 1.14 | ADR-0017: node composition is now driven by a single-valued `profile` column in `registry/nodes.csv` (`buttons` / `buttons+sensors` / `sensors` / `bridge` / `buttons+bridge`), replacing the `sensors` boolean — making "bridge AND sensors" unrepresentable rather than merely rejected (ADR-0005 single-purpose forwarders). `base_node.yaml` split into `node_core.yaml` + `buttons_8.yaml` so a bridge instantiates no button GPIOs; new `canbus/packages/bridge.yaml` + `boards/canbed-rp2040-can1.yaml` run the segment bridge on the fleet node board (CANBed RP2040 + a second MCP2515, CS GPIO8); `buttons+bridge` covers the boxes where a segment splits at a button box — buttons are the one sanctioned co-tenant of a forwarder, the sensor kit stays excluded. `map.json` keeps its frozen `nodes[].sensors` field, now derived, and adds `profile`. Amended same-day after a sourcing survey: the **LilyGO T-2CAN is restored as the preferred bridge board** (`boards/lilygo-t-2can.yaml`, profile `bridge-t2can`) with the CANBed + add-on kept as second source — 3.3 V raw-SPI MCP2515 modules turn out to be near-unobtainable at a supported crystal, making the cost saving nominal; `node_core.yaml` became board-agnostic so a profile selects its own MCU, and `canbus/archive/` is gone | AI Assistant |
| 2026-07-27 | 1.13 | Lighting panel brought to the climate panel's shape, so the two screens on identical hardware read as one system: read-only "Home" glance tab in large type (was "Status", a stack of default-size labels), the Buttons tab rebuilt from a single last-event line into the last 8 presses as aligned four-column rows (node/btn/gesture/age) fed by a header-accessor ring in `lighting/packages/ui/touch_ui_format.h`, the 32 hand-written relay cells collapsed into `relay_cell.yaml`/`relay_refresh.yaml` fragments that carry on/off via LVGL `checked` (so the OFF fill comes from the shared theme), an always-visible status strip with alarm precedence (manifest mismatch outranks HA-down) and a liveness pulse, and the 2 s refresh skipped while LVGL is paused. ALL OFF now iterates `relay_store()` instead of 32 named ids. Strip fills added to the shared palette in `packages/ui/dark_theme.yaml`; stale "runs WiFi" header in `devices/light-controller-touch.yaml` corrected | AI Assistant |
| 2026-07-26 | 1.12 | Climate touch UI reworked: shared LVGL dark theme extracted to `packages/ui/dark_theme.yaml` and adopted by both panels (a tabview covers the screen, so `lvgl: bg_color:` alone never made either panel dark — the tabview's own `tab_style`/`content_style` and a `theme:` block are what do it); zone rows rebuilt as four aligned columns (name/temp/target/state) from `climate/packages/ui/zone_row.yaml` + `zone_refresh.yaml` with semantic colour for heat/cool/idle and for degraded sensor tiers; tap-to-select zone rows; always-visible status strip on the LVGL top layer carrying alarms and a liveness pulse; two-column Home tab; 2 s refresh now skipped while LVGL is paused. Panel entry points consolidated: the four `t-connect-pro-debug*.yaml` bring-up builds deleted (their diagnosis preserved in ADR-0016 §Verification) and the fork's mandatory upgrade check repointed at `devices/locals/climate-control-touch.yaml`, whose new liveness dot makes it a better regression target; the WiFi touch variant committed rather than left as untracked WIP | AI Assistant |
| 2026-07-26 | 1.11 | ADR-0016: W5500 Ethernet and the onboard display now share ONE SPI controller (`spi2`), arbitrated by their CS lines, via a local fork of the core `ethernet` component in `libs/esphome_overrides/` — the previous two-controller arrangement was electrically impossible and the panel never rendered. Both touch builds keep Ethernet (lighting's forced WiFi override removed); panels idle asleep via LVGL `on_idle`. Added the mandatory fork re-verification step to the ESPHome upgrade procedure | AI Assistant |
| 2026-07-16 | 1.10 | Upgraded ESPHome to 2026.7.0 (pins in CI/`climate/tests/pyproject.toml`, floors in `boards/t-connect-pro.yaml` and new `boards/canbed-rp2040.yaml` `min_version`); pinned explicit modbus hub timing (250ms/100ms) against the 2026.7.0 default change; renamed `rp2040:` → `rp2:` | AI Assistant |
| 2026-07-12 | 1.9 | Renamed the active application system from `hvac/` to `climate/`, updated active tooling/docs to use `CLIMATE-Epic` for future work, and left historical implementation artifacts under their original names | AI Assistant |
| 2026-07-12 | 1.8 | Folded the Vesta package boundary back into the monorepo: climate packages now live under `climate/packages/`, shared Modbus I/O drivers under top-level `packages/devices/modbus-io/`, and active architecture/docs no longer treat Vesta as an extractable library | AI Assistant |
| 2026-07-12 | 1.7 | Raised the T-Connect Pro HVAC support floor to ESPHome 2026.6.5 after verifying the repo uses external Modbus slave devices but no ESPHome `modbus_server` blocks; updated version references accordingly | AI Assistant |
| 2026-07-11 | 1.6 | HVAC-1.4: `climate/room_sensors.yaml` flipped to CAN-primary/HA-secondary/Emergency failover (was HA-primary/UDP-secondary); updated failover-order bullets, the Failover Architecture section, and Best Practices/Troubleshooting sensor-failover language accordingly | AI Assistant |
| 2026-07-11 | 1.5 | ADR-0014 P6 hardware docs sweep: Hardware table rewritten to the standardized family (LilyGO T-Connect Pro + Waveshare Relay 32CH + Analog Output 8CH (B)); retired all Gen-1 controller/slave-board and Modbus-room-sensor claims; corrected autonomy story (single Modbus master; room sensors HA→UDP→Emergency); deleted the orphaned Gen-1 and ESP32-S3-POE board files and updated all references; ESPHome floor 2026.5.0 | AI Assistant |
| 2026-07-07 | 1.4 | Migration Phase 6b: rewrote Repository Structure to the actual four-system tree (canbus/lighting/climate/vesta + top-level registry/devices); removed the "predates restructure" note; moved HVAC-only rules (entity-ID convention, PID architecture, Modbus/relay appendices, HVAC Common Tasks) to `climate/CLAUDE.md` per AD-10 (root is the map, not the rules) | AI Assistant |
| 2026-07-05 | 1.3 | Corrected climate-control status from "production/active, live" to pre-live; controller hardware swap under consideration | AI Assistant |
| 2026-07-05 | 1.2 | Merged afmotta/canbus as canbus/ subtree; documented two-subsystem layout and epic namespacing | AI Assistant |
| 2026-03-23 | 1.1 | Updated repo structure for Vesta extraction, added entity ID naming convention, updated file references for Epics 18-20 | AI Assistant |
| 2026-01-23 | 1.0 | Initial CLAUDE.md creation | AI Assistant |

---

**End of Document**

For questions or clarifications, refer to the documentation in `docs/` and each system's `CLAUDE.md`.
