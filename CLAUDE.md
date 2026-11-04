# ESPHome Devices - AI Assistant Guide

## Document Information

| Field | Value |
|-------|-------|
| **Project** | ESPHome Multi-Floor Climate Control System |
| **Version** | 1.27 |
| **Last Updated** | November 4, 2026 |
| **Purpose** | Guide AI assistants in understanding and working with this codebase |

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
4. **`hardware/`** (PCB sources) — the KiCad projects of the CAN node boards, generated
   by scripts: `hardware/nodo503/` (ESP32-C6 wall-button node, rev C) and `hardware/bridge/`
   (dual-TWAI CAN bridge). Merged from `afmotta/can-bus-node` (archived) with full history;
   old PR `#N` references in `hardware/` commit messages resolve in the archived repo. The
   projects carry their own toolchain (KiCad 7, Freerouting) and rules in `hardware/CLAUDE.md`
   (Italian); the generated `.kicad_*` files are never hand-edited.
5. **Top-level `packages/`** — shared ESPHome packages that do not belong to a
  single application system, currently the Modbus I/O hardware drivers used by
  both Climate and lighting.

Commits are prefixed with the system they touch (`canbus:`, `lighting:`, `climate:`, `hardware:`). The
durable design knowledge — architecture, ADRs, contracts, design notes — lives under `docs/`
(see [Important Files Reference](#important-files-reference)).

Climate-specific material — system capabilities, building layout, package-composition patterns, the sensor failover chain, operating principles and the Italian room-name glossary — lives in [`climate/CLAUDE.md`](climate/CLAUDE.md) (AD-10: this file is the map, not the rulebook).

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
| **ESPHome** | 2026.8.0+ | ESP32 firmware framework (YAML-based); 2026.8.0 is the one repo baseline (CI/`climate/tests/pyproject.toml` pin + active-board `min_version` floors). `boards/t-connect-pro.yaml` and `boards/an-penta-plus.yaml` require it for multi-interface `network:` (Ethernet + WiFi declared together, ADR-0022). Earlier floors still hold below it: 2026.7.0's modbus hub overhaul (explicit `send_wait_time`/`turnaround_time` in the entry points) and `rp2040:` → `rp2:` rename |
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
│   └── home-assistant/        # Dashboards (Lovelace) and the ha-*-config.yaml HA-side configs
│
├── hardware/                  # PCB sources for the CAN node boards (see hardware/CLAUDE.md)
│   ├── nodo503/                # ESP32-C6 wall-button node, rev C (generated KiCad project + out/)
│   ├── bridge/                 # ESP32-C6 dual-TWAI CAN bridge (generated KiCad project + out/)
│   ├── tools/                  # setup.sh: KiCad 7, Freerouting 1.9.0 (not part of the CI)
│   └── docs/                   # pipeline.md, decisioni.md (Italian)
│
├── packages/                  # Cross-system ESPHome packages (shared, no owning app system)
│   ├── devices/modbus-io/     # Relay/analog Modbus I/O board drivers used by climate + lighting
│   └── ui/dark_theme.yaml     # Shared LVGL dark theme for both T-Connect Pro onboard panels
│
├── boards/                    # Board hardware definitions (shared, no owning system)
│   ├── t-connect-pro.yaml / t-connect-pro-display.yaml # LilyGO T-Connect Pro (both controllers, ADR-0014; Ethernet+WiFi merged inline via network: priority:, ADR-0022)
│   ├── canbed-rp2040.yaml   # Longan Labs CANBed RP2040 node board (CAN bus button/sensor nodes)
│   ├── canbed-rp2040-can1.yaml # Second MCP2515 add-on for the CANBed (segment bridges, ADR-0017)
│   ├── lilygo-t-2can.yaml   # LilyGO T-2CAN dual-CAN board (second-source segment bridge, ADR-0017)
│   ├── bridge-c6-twai.yaml  # ESP32-C6 dual-TWAI bridge, hardware/bridge (preferred segment bridge, ADR-0025)
│   ├── esp32-c6-nodo503.yaml # ESP32-C6 wall node, hardware/nodo503 (ADR-0025)
│   └── s1-pro-multi-sense.yaml # Sensor board
│
├── devices/                   # Main device configurations (entry points and their deployment variants, gathered together)
│   ├── climate-control.yaml   # Main Climate system
│   ├── room-sensor-soggiorno.yaml # Standalone room sensor
│   ├── wall-sensor.yaml       # Wall-mounted sensor (SEN66)
│   ├── light-controller.yaml  # Lighting controller firmware (button events + relay bank; ADR-0015)
│   ├── health-monitor.yaml    # CAN bus health monitor firmware (transport health; ADR-0015)
│   ├── secrets.yaml.example   # Template for devices/secrets.yaml (device secrets)
│   └── locals/                # Local build wrappers (climate, sensors) — flashed/OTA'd from a local checkout (ADR-0023 retired devices/remotes/)
│
├── libs/                      # Custom Python/C++ components
│   ├── s1_pro/                # LD2450 radar driver
│   └── esphome_overrides/     # Local FORKS of core ESPHome components (shadow the built-ins)
│       └── ethernet/          # W5500 sharing one SPI controller with the onboard display (ADR-0016)
│                              #   ⚠ tracks the repo's pinned ESPHome (2026.8.0) — re-verify on every upgrade
│
├── docs/                      # Project knowledge base and guides
│   ├── adr/                    # Architecture Decision Records (the "why"; `docs/adr/` is the single index)
│   ├── architecture/          # ARCHITECTURE-SPINE.md (invariants) + architecture-diagram.md
│   ├── contracts/             # Frozen cross-system contracts (map.json, bindings arbitration)
│   ├── design-notes/          # Entity-naming convention, canbus implementation rules
│   ├── climate/               # Live climate docs: deployment runbook, RS485 wiring, heat-pump integration, window-sensor map, MEV manual
│   ├── archive/               # Historical (Gen-1 hardware, implemented proposals) — do not follow for current work
│   └── change_waveshare_relay_address.yaml # Relay-bank address commissioning tool (cited by the maintenance site)
│
├── docs-site/                 # Maintenance & support site (MkDocs, EN + IT; GitHub Pages)
│
├── scripts/                   # Repo checks: verification-battery.sh, check_repo_hygiene.py, check_on_boot_*.py, check_md_links.py, CI dummy secrets
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

#### `esphome: on_boot` is always a list with explicit priorities

Write every `on_boot:` as a **list**, one entry per hook, each with its own `priority:` (review R-18):

```yaml
esphome:
  on_boot:
    - priority: 200
      then:
        - lambda: 'ESP_LOGI("x", "up");'
```

ESPHome merges `packages:` with `merge_config()`: two **mapping**-form `on_boot` blocks become ONE trigger
(`then` lists concatenated, a single `priority` survives, so every other declared priority and the comments
justifying it are false), and a mapping mixed with a list silently **drops one side**. Lists concatenate into
independent triggers that really run at their own priority. `scripts/check_on_boot_form.py` (in the native
battery, pre-commit and CI) fails on any mapping-form `on_boot` or any entry without a `priority`;
`scripts/check_on_boot_resolved.py` (CI `esphome-config` job) compares the resolved trigger counts per entry
point with `scripts/on_boot_baseline.json` — re-run it with `--update` when you add or remove a hook on
purpose. Hooks that share a priority run in registration (list) order, which depends on package order: give
hooks that must be ordered distinct priorities.

#### YAML Formatting
- **Indentation**: 2 spaces (no tabs)
- **Key spacing**: Space after colon (`key: value`)
- **List items**: Dash with space (`- item`)
- **Comments**: Use `#` for inline comments
- **Long values**: Use YAML multi-line strings (`>` or `|`)

#### Naming and language

Comments and documentation are in English, but entity IDs often use Italian room names (`soggiorno`, `cucina`, `bagno`, …); the glossary is in `climate/CLAUDE.md`. `hardware/` documentation is in Italian (see `hardware/CLAUDE.md`).

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

### Deployment

Both T-Connect Pro controllers carry the onboard screen (standard on every build, ADR-0023), which
needs the local `ethernet` fork (`external_components: type: local`). That fork cannot travel through
ESPHome's `github://` packages, so the controllers are flashed and OTA-updated from a **local
checkout** with the `esphome run` commands above — not a GitHub-pull config. The former
`devices/remotes/` GitHub-package deployment was retired in ADR-0023 (it could only ever build a
screen-less config, which no physical controller runs).

### Secrets Management

Never commit `secrets.yaml`. It contains:
```yaml
# secrets.yaml (gitignored)
wifi_ssid: "YourSSID"
wifi_password: "password"
encryption_key: "base64key..."
ota_password: "password"
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

`libs/esphome_overrides/ethernet/` is a **local fork of a core ESPHome component** (W5500 sharing one SPI controller with the onboard display, ADR-0016). Upstream owes it no compatibility, so **every ESPHome version bump must** re-diff the upstream `ethernet/` component, re-apply the two `LOCAL FORK (esphome-devices)` changes, and re-run the bring-up check on `devices/locals/climate-control.yaml` (boot log `SPI host 2 already initialized (shared with 'spi:')`, liveness dot pulsing and green under tab-switch load). Skipping this does not fail the build — it fails the *panel*, silently, at runtime.

Full procedure: [`docs/design-notes/esphome-upgrade-fork-check.md`](docs/design-notes/esphome-upgrade-fork-check.md).

### Testing Levels

1. **Component Testing**: Test individual component packages in isolation
2. **Integration Testing**: Test full device config compilation (`esphome config`)
3. **Hardware Testing**: Deploy to test board, verify outputs
4. **Verification battery**: `scripts/verification-battery.sh` — the native/Python test
   suite plus `esphome config`/`compile` gates that CI (`.github/workflows/verify.yml`) runs

### Validation Before Commit

**Pre-commit** is configured in `.pre-commit-config.yaml` (review R-10): install it once per clone with
`pip install pre-commit && pre-commit install`, run it on demand with `pre-commit run --all-files`. It runs
yamllint (`.yamllint`), `scripts/check_repo_hygiene.py` and `scripts/verification-battery.sh --fast`
(`--native-only` minus the generator-idempotence step, so it works on a dirty tree, ~5 s). CI mirrors the
first two (plus `scripts/check_md_links.py`, relative Markdown links) as the `lint` job; the climate host e2e (`pytest climate/tests/e2e`) runs on every PR as the
`climate-e2e` job — serially, since every harness binds API port 6053 (never add `-n`). The slow gates
(idempotence, `esphome config`/`compile`) run in CI or via the full battery.

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
| `climate/packages/components/failover_sensor.yaml` | 3-tier sensor failover logic |
| `climate/mev_modbus.yaml` | MEV Modbus device driver (project-specific) |
| [Maintenance Guide](https://afmotta.github.io/esphome-devices/) (`docs-site/`) | Practical, non-expert-oriented operations/troubleshooting/hardware-replacement site (EN + IT), deployed via GitHub Pages |

### Key Documentation Files

| File | Purpose |
|------|---------|
| `docs/architecture/ARCHITECTURE-SPINE.md` | Architectural invariants (AD-1…AD-10) — the current authority |
| `docs/architecture/architecture-diagram.md` | Mermaid diagrams of system topology and data flows |
| `docs/adr/` | Architecture Decision Records — the reasoning behind decisions |
| `docs/contracts/` | Frozen cross-system contracts (`map.json`, bindings arbitration) |
| `docs/design-notes/entity-naming.md` | Entity ID naming convention |
| `docs/design-notes/canbus-implementation-rules.md` | CAN firmware implementation rules (lambda safety, protocol header, codegen) |
| `docs/design-notes/esphome-upgrade-fork-check.md` | Mandatory checklist for every ESPHome version bump (local `ethernet` fork) |
| `TODO.md` | Feature backlog (in Italian) |

### Configuration Entry Points

| Path | Use Case |
|------|----------|
| `devices/locals/climate-control.yaml` | The climate controller build (local flash/OTA; onboard screen standard) |
| `devices/climate-control.yaml` | Core composition (board + climate packages + panel); included by the local wrapper |

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
- **Never hardcode secrets** — always `!secret`; safety, failover and Home Assistant principles for the climate system are in `climate/CLAUDE.md` (Operating principles)

---

## Getting Help

1. **Architecture**: `docs/architecture/ARCHITECTURE-SPINE.md` (invariants) and
   `docs/architecture/architecture-diagram.md` (topology and data flows)
2. **Decisions**: `docs/adr/` - the reasoning behind significant decisions (see the directory listing for the full set)
3. **Maintenance & support**: https://afmotta.github.io/esphome-devices/ (`docs-site/`)
4. **ESPHome Docs**: https://esphome.io/ - Platform documentation

### Troubleshooting

**Compilation Errors**:
- Check YAML syntax (indentation, colons, dashes)
- Verify all `!include` paths are correct
- Ensure all substitution variables are defined
- Check ESPHome version (min 2026.8.0 — the one repo baseline; the T-Connect Pro / An-Penta boards require it for multi-interface `network:`)

**Sensor Failover**:
- Check failover logs in Home Assistant
- Ensure the CAN sensor-kit path (Tier 1) is available and updating
- Verify Home Assistant sensors (Tier 2) are arriving when CAN drops out
- Monitor for zones sitting in Emergency (all sensor tiers NaN)

Climate-specific troubleshooting (Modbus issues, PID tuning) and the Modbus register/relay/
sensor-address appendices and PID tuning guidelines are documented in `climate/CLAUDE.md`.

---

## Changelog

Version history lives in [`CHANGELOG.md`](CHANGELOG.md) (newest first). Add a row there, and bump the version in the table at the top, whenever this guide or the architecture it describes changes materially.
