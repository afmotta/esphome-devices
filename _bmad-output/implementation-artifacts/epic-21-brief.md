# Epic 21: Vesta CLI Configuration Generator

## Overview

Build a Python CLI tool that interactively guides users through describing their building, hardware, and HVAC subsystems, then generates a complete set of ESPHome YAML configuration files using Vesta packages. The tool replicates the manual process of composing Vesta packages — wiring vars, assigning relays, mapping sensors — through a guided wizard experience.

**Phase:** Vesta Phase 2 (from brainstorming session 2026-02-05)
**Priority:** High — removes the biggest barrier to Vesta adoption (manual YAML composition)

## Problem Statement

Vesta's package-based architecture is powerful but requires users to:
1. Understand the full component inventory and their parameterization contracts
2. Manually wire `vars:` blocks between packages (slug conventions, sensor IDs, relay assignments)
3. Know which components to combine for their specific HVAC topology (radiant-only, fancoil-only, hybrid)
4. Avoid entity ID collisions across floors and rooms
5. Correctly set up board hardware mappings (Modbus addresses, relay offsets, DAC outputs)

A CLI wizard eliminates these barriers by capturing the user's intent and generating correct configurations automatically.

## User Stories

### Story 21.1: Project Scaffolding & Data Model

**As a** Vesta developer,
**I want** a Python project with a well-defined data model for buildings, floors, zones, and subsystems,
**So that** the CLI has a solid foundation to build on.

#### Acceptance Criteria

- [ ] Python project initialized with `pyproject.toml` (or equivalent), installable via `pip install -e .`
- [ ] CLI entry point `vesta` works (e.g., `vesta --help` shows usage)
- [ ] CLI framework chosen and integrated (e.g., Click, Typer, or questionary for interactive prompts)
- [ ] Data model classes defined for:
  - **Building**: name, floors list, board list, network config
  - **Floor**: name, slug, zones list, shared parameters (pump type, boost thresholds)
  - **Zone**: room_slug, room_name, subsystems list, sensor config
  - **Subsystem**: type (radiant, heat_only_radiant, fancoil), relay/output assignment, PID gains
  - **Board**: model (A6, A16, WaveShare-S3, generic), Modbus address, relay count, DAC count, relay offset
  - **SensorConfig**: type (failover, direct), primary/secondary sources, Modbus address (if applicable)
  - **Coordinator**: type (fancoil_boost, mev_ventilation, seasonal_mode), zone/floor scope, parameters
- [ ] Data model supports serialization to/from a YAML or JSON project file (so users can save and re-run)
- [ ] Unit tests for data model serialization round-trip
- [ ] Project lives in `vesta/cli/` directory within the Vesta repository

#### Technical Notes

- The data model should mirror the Vesta package hierarchy: components → coordinators → devices
- Each subsystem type maps 1:1 to a Vesta package file
- Board relay/output assignments must track used slots to prevent collisions
- Consider using Pydantic or dataclasses for validation

---

### Story 21.2: Interactive Building Discovery Wizard

**As a** user setting up Vesta for the first time,
**I want** a guided wizard that asks me about my building layout and HVAC topology,
**So that** I can describe my system without reading all the Vesta documentation.

#### Acceptance Criteria

- [ ] `vesta init` command launches the interactive wizard
- [ ] Wizard collects building-level info: project name, ESPHome device name
- [ ] Wizard iterates through floors: name, slug, number of zones
- [ ] For each zone, wizard asks:
  - Room name and slug (with Italian name suggestions/examples)
  - Subsystem types: radiant (heat+cool), heat-only radiant, fancoil, or hybrid (radiant+fancoil)
  - Whether fancoil boost coordination is needed (auto-suggested for hybrid zones)
- [ ] Wizard asks about system-wide coordinators:
  - Seasonal mode: yes/no, calendar gate defaults
  - MEV ventilation: yes/no, which floor, demand sources
- [ ] Wizard asks about sensor strategy:
  - Failover (HA primary + UDP secondary) vs direct sensor
  - Modbus room sensors: addresses per room
- [ ] Wizard produces a complete data model and saves it as a project file (e.g., `vesta-project.yaml`)
- [ ] Wizard supports re-running on an existing project file to modify/extend
- [ ] Input validation: slugs are valid ESPHome IDs, no duplicate slugs, no empty floors

#### Technical Notes

- Use progressive disclosure: start simple (floors, rooms), add complexity only when relevant (Modbus, MEV)
- Provide sensible defaults where possible (PID gains from Vesta defaults, standard relay layouts)
- The wizard should feel conversational, not like filling a form

---

### Story 21.3: Hardware Mapping Wizard

**As a** user with specific ESP32 boards and relay/DAC hardware,
**I want** the CLI to help me assign zones to physical board outputs,
**So that** I don't have to manually track relay numbers and Modbus addresses.

#### Acceptance Criteria

- [ ] Wizard asks about boards: how many, what type (A6, A16, WaveShare-S3, generic ESP32)
- [ ] For each board: Modbus address (if applicable), network type (Ethernet/WiFi), role (main controller, relay expansion, sensor board)
- [ ] Auto-assignment mode: CLI distributes zones to relays/outputs sequentially with user confirmation
- [ ] Manual assignment mode: user picks relay/output for each zone subsystem
- [ ] Collision detection: warn if two zones try to use the same relay or output
- [ ] For Modbus relay boards: track `id_offset` to avoid entity ID collisions across boards
- [ ] For analog output boards: track DAC channel assignments for fancoils
- [ ] Hardware map saved in the project file alongside the building model
- [ ] Summary display: show full relay/output assignment table before proceeding

#### Technical Notes

- Board definitions should reference Vesta `packages/devices/` configs
- The A16 has 16 relays (typically mapped as two 8-relay Modbus boards)
- Fancoils require analog outputs (0-10V DAC), radiant zones require relay outputs (zone valves)
- Pump relays are floor-scoped, not zone-scoped

---

### Story 21.4: YAML Configuration Generator

**As a** user who has completed the wizard,
**I want** the CLI to generate all ESPHome YAML configuration files,
**So that** I have a working system without manually writing YAML.

#### Acceptance Criteria

- [ ] `vesta generate` command reads the project file and produces YAML configs
- [ ] Generated file structure follows Vesta conventions:
  ```
  output/
  ├── devices/
  │   └── climate-control.yaml    # Main entry point
  ├── boards/
  │   └── [board configs]
  └── components/
      └── rooms/
          ├── [floor]/
          │   ├── [floor]-floor.yaml
          │   └── [room].yaml
          └── room_sensors.yaml (if using failover pattern)
  ```
- [ ] Vesta packages referenced via ESPHome remote GitHub packages, not local paths:

  ```yaml
  packages:
    radiant: !include
      url: https://github.com/afmotta/vesta
      file: packages/components/radiant.yaml
      ref: v1.0.0  # Pinned to Vesta release tag
      vars:
        room_slug: "living_room"
        # ...
  ```
- [ ] Vesta version tag is configurable in the project file (default: latest release)
- [ ] Main device config correctly composes all packages with proper remote references and `vars:` blocks
- [ ] Room configs include correct Vesta package references with all required vars populated
- [ ] Floor aggregator files include all room packages for that floor
- [ ] Coordinator packages (seasonal_mode, fancoil_boost, mev_ventilation) wired with correct entity ID references
- [ ] Board configs reference correct Vesta device packages with Modbus addresses and offsets
- [ ] All entity IDs follow the Vesta naming convention: `{scope}_{component}[_{mode}][_{aspect}]`
- [ ] Generated configs include placeholder `!secret` references for sensitive values (wifi_password, api_encryption_key, ota_password)
- [ ] Output directory is configurable (default: `./output/`)
- [ ] Generated files have clear header comments indicating they were auto-generated by Vesta CLI

#### Technical Notes

- Use Jinja2 or string templates — don't try to programmatically construct YAML ASTs
- The generator must understand Vesta's package dependency chain (radiant includes pid which includes pid_sensors)
- Cross-reference entity IDs between packages: fancoil_boost needs to reference the radiant PID's output sensor, the fancoil PID's ID, etc.
- Consider generating a `secrets.yaml.example` with all required secret keys

---

### Story 21.5: Validation & Dry Run

**As a** user who has generated configs,
**I want** to validate that the generated YAML is correct before flashing,
**So that** I can catch errors early.

#### Acceptance Criteria

- [ ] `vesta validate` command runs `esphome config` on the generated device config
- [ ] Clear error reporting: if validation fails, show which file/line has the issue
- [ ] `vesta generate --dry-run` shows what files would be created without writing them
- [ ] Pre-generation validation: check project file for common issues before generating (missing required fields, invalid slugs, unassigned relays)
- [ ] Post-generation summary: list all generated files, entity count, component count

#### Technical Notes

- `esphome config` requires ESPHome to be installed — document this as a prerequisite
- Validation is optional (user may not have ESPHome installed on the machine running the CLI)
- Consider running validation automatically after generation with a `--no-validate` opt-out

---

### Story 21.6: Documentation & User Guide

**As a** new Vesta user,
**I want** clear documentation on how to install and use the CLI tool,
**So that** I can get started without reading the source code.

#### Acceptance Criteria

- [ ] README in `vesta/cli/` with: installation instructions, quick start, full command reference
- [ ] Getting started tutorial: walk through creating a simple 2-zone system (matching the existing Vesta example)
- [ ] Project file reference: document the YAML schema with all fields and defaults
- [ ] Troubleshooting section: common errors and solutions
- [ ] Update Vesta main README to reference the CLI tool
- [ ] Example project files for common topologies:
  - Single-floor radiant-only (simplest case)
  - Multi-floor hybrid radiant+fancoil (production-like)
  - MEV-integrated system

#### Technical Notes

- Keep docs in `vesta/docs/cli/` or `vesta/cli/docs/`
- The tutorial should produce output that matches `vesta/examples/two_zone_radiant_fancoil.yaml`

---

## Dependencies

- **Requires:** Vesta Phase 1 complete (Epics 19-20) — all packages extracted and documented
- **Requires:** Vesta repository tagged with a semver release (e.g., `v1.0.0`) before Story 21.4. The Vesta repo (`github.com/afmotta/vesta`) currently has no tags — a first release tag must be created so generated configs can pin to a stable version via `ref:`.
- **No external service dependencies** — the CLI is a local tool

## Technical Constraints

- **Python 3.10+** (match ESPHome's minimum)
- **Minimal dependencies** — keep the install lightweight
- **No runtime ESPHome dependency** — CLI generates static YAML files; ESPHome is only needed for optional validation
- **Cross-platform** — must work on Linux, macOS, Windows

## Out of Scope

- Web wizard (Phase 3 — separate epic)
- Modifying existing configs (this epic covers initial generation only)
- OTA deployment or flashing (ESPHome handles this)
- Custom component development (C++/Python ESPHome components)
- Dashboard generation for Home Assistant

## Story Sequence

Recommended implementation order:

1. **21.1** Project Scaffolding & Data Model — foundation for everything
2. **21.2** Building Discovery Wizard — capture user intent
3. **21.3** Hardware Mapping Wizard — complete the data model
4. **21.4** YAML Configuration Generator — the core deliverable
5. **21.5** Validation & Dry Run — quality assurance
6. **21.6** Documentation & User Guide — adoption enablement

Stories 21.2 and 21.3 could potentially be merged if the wizard flow feels more natural as a single pass.
