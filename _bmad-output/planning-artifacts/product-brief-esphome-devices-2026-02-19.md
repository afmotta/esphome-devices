---
stepsCompleted: [1, 2, 3, 4, 5]
inputDocuments:
  - "_bmad-output/analysis/brainstorming-session-2026-02-05.md"
  - "_bmad-output/planning-artifacts/epic-19-brief.md"
date: 2026-02-19
author: Alberto
---

# Product Brief: Vesta Climate Framework - Phase 1 Completion

<!-- Content appended sequentially through collaborative workflow steps -->

## Executive Summary

Epic 19 extracted 5 production-proven components into the Vesta Climate Framework. This epic **completes Phase 1** by migrating all remaining reusable components — 15 additional packages covering PID zone control with production-tested presets, seasonal mode coordination, Modbus I/O board drivers, pump control, and a dew point utility — while reorganizing the package structure into a scalable taxonomy: `components/` for logical ESPHome wrappers, `coordinators/` for behavioral patterns, and `devices/` for hardware implementations. Each component includes full documentation and the existing docs/examples are updated for the new structure.

---

## Core Vision

### Problem Statement

Vesta Phase 1 shipped 5 components but left significant reusable value locked in the private esphome-devices codebase. The PID zone control stack (with production-tuned presets for radiant and fancoil systems), seasonal heat/cool mode management, Modbus I/O board drivers, and pump control patterns all solve problems that multi-zone HVAC integrators face repeatedly. Additionally, the Phase 1 package structure (`utils/` and `coordinators/`) doesn't scale — a clearer taxonomy is needed before the library grows further.

### Problem Impact

- ESPHome users building multi-zone systems lack open-source patterns for PID zone orchestration, seasonal mode switching, and Modbus I/O expansion
- The current `utils/` folder mixes sensors with unrelated components — confusing as the library grows
- Without the PID stack and seasonal mode, Vesta can't deliver on its promise of being a complete climate orchestration framework

### Why Existing Solutions Fall Short

- ESPHome's native `climate.pid` is powerful but users must read docs and pick props themselves — Vesta's PID wrappers provide production-tested presets for multi-zone HVAC
- No open-source project provides parameterized seasonal mode management (calendar-based + demand-driven transitions)
- Modbus relay/analog output wrappers exist in scattered forum posts but not as maintained, parameterized packages
- No single framework offers the full stack from sensor utilities through zone control to hardware abstraction

### Proposed Solution

Extract and generalize 15 additional components from the esphome-devices production system into Vesta, organized under a new package taxonomy:
- **`components/`** — Flat folder with logical ESPHome wrappers (sensors, PID presets, output patterns, pumps)
- **`coordinators/`** — Behavioral patterns (existing + seasonal mode)
- **`devices/modbus-io/`** — Modbus relay board and analog output board drivers

Restructure existing Phase 1 packages to match (move `utils/` contents to `components/`). Update all existing docs, examples, and README. Create doc pages for every new component.

### Key Differentiators

- **Complete zone control stack**: PID + radiant + fancoil + auto-tuning as composable, production-tested packages
- **Seasonal mode coordinator**: Calendar-based with demand-driven shoulder season transitions — novel for ESPHome
- **Modbus I/O abstraction**: Parameterized drivers for relay boards and analog output boards — board-agnostic
- **Production-proven**: Every component runs in a 13-zone, 3-floor residential system
- **Clean taxonomy**: `components/coordinators/devices` maps to how HVAC systems are built

---

## Target Users

### Primary Users

**The ESPHome HVAC Integrator** — Experienced ESPHome users building multi-zone climate control systems who need production-tested, composable packages rather than reinventing patterns from scratch.

- **Profile**: Comfortable with ESPHome's package system (`!include`, substitutions, lambdas). Already running or planning a multi-zone HVAC setup with radiant floors, fancoils, or both. May have Modbus I/O boards for relay expansion.
- **Current Pain**: Writes PID presets from scratch by reading ESPHome docs and tuning by trial-and-error. Cobbles together Modbus drivers from forum posts. No reference architecture for multi-zone orchestration, seasonal mode switching, or sensor failover.
- **Success Vision**: Includes Vesta packages with zone-specific parameters, gets production-tested defaults as a starting point, and can fine-tune from there. Focuses on their system's unique aspects rather than re-solving common problems.
- **Doc Needs**: Parameter reference tables, dependency maps, quick-start snippets. Skims narrative, goes straight to the API.

### Secondary Users

**The HA Climate Enthusiast** — Home Assistant power users who know YAML and want to graduate from simple on/off thermostats to proportional, multi-zone climate control but find the ESPHome PID learning curve steep.

- **Profile**: Runs Home Assistant, has ESPHome devices for sensors or simple switches. Understands YAML configuration but hasn't worked with PID controllers, Modbus, or complex ESPHome automations. Wants better comfort and efficiency from their HVAC.
- **Current Pain**: The gap between "I have ESPHome running" and "I have proper multi-zone climate control" is too wide. ESPHome PID docs require understanding control theory. No end-to-end examples showing how the pieces fit together.
- **Success Vision**: Includes Vesta's PID + radiant package for one zone without having to choose `kp`, `ki`, `kd` values — the production-tested presets remove the control theory barrier. Builds confidence to add more zones and customize thresholds over time.
- **Doc Needs**: Narrative guides explaining "why" before "how", complete worked examples, conceptual overviews. Needs the full picture before diving into parameters.

### User Journey

1. **Discovery**: Finds Vesta through ESPHome community forums, Home Assistant community, or GitHub search while looking for multi-zone PID examples or Modbus relay drivers.
2. **Onboarding**: Reads the README, sees the component overview table, follows the getting-started guide. Starts with one component (e.g., PID + radiant for a single zone). *Integrators* jump to the parameter reference; *enthusiasts* follow the narrative guide and complete example.
3. **Core Usage**: Includes Vesta packages in their ESPHome config via GitHub remote references. Passes zone-specific parameters (slug, name, sensor IDs, relay assignments). Customizes thresholds where defaults don't fit.
4. **Success Moment**: First zone runs with stable PID control using Vesta's production-tested presets as a starting point. *For the integrator*: realizes the full stack (sensors → PID → outputs → coordination) composes cleanly, and they can fine-tune from proven defaults rather than starting from zero. *For the enthusiast*: "I didn't have to choose PID parameters — Vesta's presets handled it."
5. **Long-term**: Adds more zones, adopts coordinators (fancoil boost, seasonal mode), contributes improvements back. Vesta becomes the foundation layer of their climate system.

---

## Success Metrics

### Delivery Completeness

| Metric | Target | Measurement |
|--------|--------|-------------|
| New components extracted | 15/15 | All components present in Vesta repo |
| Components compile standalone | 15/15 | ESPHome config validation with declared parameters only |
| Existing components unbroken | 5/5 | Phase 1 components compile after restructure |
| Package taxonomy applied | 100% | All packages in `components/`, `coordinators/`, or `devices/modbus-io/` |
| `utils/` folder eliminated | Yes | Contents moved to `components/`, no `utils/` remains |

### Documentation Coverage

| Metric | Target | Measurement |
|--------|--------|-------------|
| New component doc pages | 15/15 | Every new component has a doc page with parameter reference + usage example |
| Existing doc pages updated | 5/5 | Existing docs reflect new package paths and structure |
| README updated | Yes | Component overview table includes all 20 components with correct paths |
| Examples updated | Yes | Existing examples compile with new package paths |

### Quality Gates

- All components compile with `esphome config` validation
- No component references esphome-devices-specific entities (room names, hardware IDs)
- Every component's declared parameters are documented with types and defaults
- Dependency chains are explicit and documented (e.g., radiant → pid → trend_sensor)

### Business Objectives

N/A — This is an open-source project in early release. Adoption metrics (GitHub engagement, community feedback, external contributions) will be defined in a future epic after Phase 1 is complete and publicly announced.

### Key Performance Indicators

Deferred to post-release. This epic's KPI is binary: **Phase 1 is complete and shipped, or it isn't.**

---

## MVP Scope

### Core Features

**1. Package Restructure**
- Move existing `utils/` contents (trend_sensor, failover_sensor, proportional_demand_sensor) to `components/`
- Maintain `coordinators/` for behavioral patterns
- Create `devices/modbus-io/` for hardware drivers
- Update all existing docs, examples, and README to reflect new paths

**2. New Components — `components/` (10 packages)**

| Component | Source | Description |
|-----------|--------|-------------|
| `pid.yaml` | `components/pid.yaml` | PID controller wrapper with production-tested presets |
| `pid_sensors.yaml` | `components/pid_sensors.yaml` | PID input/output diagnostic sensors |
| `pid_autotune.yaml` | `components/pid_autotune.yaml` | PID auto-tuning logic |
| `pid_autotune_with_fancoil.yaml` | `components/pid_autotune_with_fancoil.yaml` | Auto-tune variant for fancoil systems |
| `radiant.yaml` | `components/radiant.yaml` | Radiant floor heating/cooling zone |
| `fancoil.yaml` | `components/fancoil.yaml` | Fancoil unit control (analog 0-10V) |
| `heat_only_radiant.yaml` | `components/heat_only_radiant.yaml` | Heat-only radiant variant |
| `mixing_pump.yaml` | `components/mixing_pump.yaml` | Mixing valve + pump control |
| `direct_pump.yaml` | `components/direct_pump.yaml` | Direct pump control |
| `dew_point_sensor.yaml` | `components/dew_point_sensor.yaml` | Dew point calculation utility |

**3. New Coordinator — `coordinators/` (1 package)**

| Component | Source | Description |
|-----------|--------|-------------|
| `seasonal_mode.yaml` | `components/seasonal_mode.yaml` | Calendar-based + demand-driven heat/cool mode switching |

**4. New Device Drivers — `devices/modbus-io/` (4 packages)**

| Component | Source | Description |
|-----------|--------|-------------|
| `modbus_relay_board.yaml` | `components/modbus_relay_board.yaml` | Modbus relay board driver |
| `modbus_relay_switch.yaml` | `components/modbus_relay_switch.yaml` | Individual Modbus relay switch |
| `modbus_analog_output.yaml` | `components/modbus_analog_output.yaml` | Modbus 0-10V DAC output |
| `modbus_analog_outputs_board.yaml` | `components/modbus_analog_outputs_board.yaml` | Modbus analog outputs board driver |

**5. Documentation**
- Doc page for every new component (parameter reference + usage example)
- Update all existing Phase 1 doc pages for new paths
- Update README component overview table (all 20 components)
- Update existing examples for new package structure

**6. Migrate esphome-devices to consume Vesta**
- Update `esphome-devices` to reference Vesta packages via GitHub remote includes instead of local component files
- Remove all migrated component files from `esphome-devices/components/` (the 15 new + 5 existing that now live in Vesta)
- Update all room configs and device configs to use Vesta package paths
- Verify the production system compiles and works with Vesta as an external dependency

### Out of Scope

- **Phase 2 (CLI Tool)**: Scaffolding tool for generating configs — deferred per brainstorming roadmap
- **Phase 3 (Web Wizard)**: Browser-based configuration wizard — deferred
- **`boards/` tier**: Ready-to-use board definitions — future concept, noted in brainstorming for later iteration
- **Room templates**: User-specific zone configurations (`components/rooms/`) — must be created by each user for their house
- **MEV demand sensor** (`mev_demand.yaml`): User-specific demand mapping
- **MEV Modbus driver** (`mev_modbus.yaml`): Machine-specific device driver
- **Community announcement**: Forum posts, Discord — separate effort after Phase 1 stabilizes
- **CI/CD**: Automated testing pipeline — future improvement

### MVP Success Criteria

- All 15 new components compile standalone with declared parameters
- All 5 existing components compile after restructure (no regressions)
- `utils/` folder eliminated, all packages in the new taxonomy
- 100% documentation coverage — every component has a doc page
- README and examples updated for new structure
- esphome-devices compiles with zero local copies of migrated components — all 20 reference Vesta via GitHub remote includes

### Future Vision

Captured in the Vesta brainstorming session (`_bmad-output/analysis/brainstorming-session-2026-02-05.md`):
- **Phase 2**: CLI scaffolding tool — `vesta init` generates a starting config from zone/hardware questionnaire
- **Phase 3**: Web wizard — browser-based UI for the same scaffolding flow
- **`boards/` tier**: Curated, ready-to-use ESPHome board definitions for common hardware (Kincony, Waveshare, etc.)
- **Community contributions**: Device configs, new coordinators, additional Modbus device drivers
- **Adoption metrics**: GitHub engagement, community feedback, external PRs — defined after public announcement
