# Story 19.1: Repository Scaffolding

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **climate control enthusiast and ESPHome community member**,
I want **a well-structured open-source repository called Vesta Climate Framework**,
so that **production-proven ESPHome climate control components can be shared with the community and adopted by other multi-zone HVAC integrators**.

## Acceptance Criteria

1. **AC-1:** Repository initialized at `vesta/` (already exists as git repo) with proper directory structure matching: `packages/utils/`, `packages/coordinators/`, `docs/`, `examples/`
2. **AC-2:** README.md explains the project purpose ("Vesta" - Roman goddess of the hearth), the Base + Boost innovation, 3-tier package structure (utils, coordinators, examples), and includes a component overview table linking to future component docs
3. **AC-3:** LICENSE file present (MIT license for maximum adoption)
4. **AC-4:** CONTRIBUTING.md describes how to propose new components, testing expectations (ESPHome config validation), coding standards (YAML formatting, parameterization pattern, header comments), and PR guidelines
5. **AC-5:** `.gitignore` configured for ESPHome build artifacts (`.esphome/`, `secrets.yaml`, `*.pyc`, etc.)
6. **AC-6:** Directory structure matches the target layout with placeholder `.gitkeep` files in empty directories

## Tasks / Subtasks

- [x] Task 1: Create directory structure (AC: #1, #6)
  - [x] 1.1: Create `packages/utils/` directory
  - [x] 1.2: Create `packages/coordinators/` directory
  - [x] 1.3: Create `docs/` directory
  - [x] 1.4: Create `examples/` directory
  - [x] 1.5: Add `.gitkeep` files to empty directories
- [x] Task 2: Create LICENSE file (AC: #3)
  - [x] 2.1: Create MIT LICENSE with year 2026, copyright holder Alberto
- [x] Task 3: Create .gitignore (AC: #5)
  - [x] 3.1: Add ESPHome build artifacts (`.esphome/`), secrets, Python cache, IDE files
- [x] Task 4: Create README.md (AC: #2)
  - [x] 4.1: Write project header with Vesta name, tagline, and purpose
  - [x] 4.2: Write "Why Vesta" section explaining the origin (production system, 13 zones, 3 floors)
  - [x] 4.3: Write "The Base + Boost Innovation" section (hero concept)
  - [x] 4.4: Create component overview table with 5 components, types, descriptions, and doc links
  - [x] 4.5: Write "Quick Start" section showing how to include a Vesta package via `!include`
  - [x] 4.6: Write "Architecture Philosophy" section summarizing key principles
  - [x] 4.7: Add prerequisites section (ESPHome 2025.12.0+, ESP32)
  - [x] 4.8: Add links to docs/, CONTRIBUTING.md, LICENSE
- [x] Task 5: Create CONTRIBUTING.md (AC: #4)
  - [x] 5.1: Write component proposal process
  - [x] 5.2: Document YAML coding standards (2-space indent, header comment format, parameter naming)
  - [x] 5.3: Document parameterization pattern (vars contract, defaults, types)
  - [x] 5.4: Document testing expectations (ESPHome `config` validation, example compilation)
  - [x] 5.5: Document PR guidelines (description, testing evidence, component doc included)

## Dev Notes

### Architecture & Context

- **Epic 19** is about extracting 5 production-proven components from `esphome-devices` into a new open-source project called "Vesta Climate Framework"
- Story 19.1 is pure scaffolding - no component code is extracted yet (that's stories 19.2-19.6)
- The `vesta/` directory already exists at the project root as a separate git repository (detected as git submodule/subrepo)
- All work should happen within the `vesta/` directory

### Target Repository Structure

```
vesta/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore
├── packages/
│   ├── utils/
│   │   └── .gitkeep
│   └── coordinators/
│       └── .gitkeep
├── examples/
│   └── .gitkeep
└── docs/
    └── .gitkeep
```

### Component Overview (for README table)

| Component | Type | Lines | Description | Status |
|-----------|------|-------|-------------|--------|
| Trend Sensor | Utility | 48 | Rate-of-change calculator with sliding window averaging | Planned (19.2) |
| Failover Sensor | Utility | 111 | 3-tier sensor failover with automatic recovery | Planned (19.3) |
| Proportional Demand Sensor | Utility | 83 | Converts sensor readings to 0-100% demand signals | Planned (19.4) |
| Fancoil Boost Coordinator | Coordinator | 313 | Base + Boost pattern for radiant floor + fancoil hybrid control | Planned (19.5) |
| MEV Ventilation Coordinator | Coordinator | 365 | Multi-demand ventilation orchestration with humidity state machine | Planned (19.6) |

### Key Innovation to Highlight in README

**"Base + Boost" Pattern**: Radiant floor and fancoil systems are treated as complementary layers rather than either/or alternatives. Radiant provides efficient baseline comfort; fancoils activate automatically when temperature delta, humidity, or PID saturation demands more capacity. Three activation triggers (reactive temperature, reactive humidity, predictive PID saturation) and AND-logic deactivation with anti-oscillation.

### 9 Foundational Principles (for Architecture Philosophy section)

1. Integrated Climate Orchestration
2. Single Source of Truth for Mode
3. HA-Enhanced, Not HA-Dependent
4. Minimal Zone Contract
5. Autonomous Core
6. Logic Lives on the Edge
7. Direct Board Communication
8. Heterogeneous Subsystem Support
9. Match Thermal Inertia to Disturbance Patterns

### YAML Coding Standards (for CONTRIBUTING.md)

From the existing esphome-devices codebase:
- **Indentation:** 2 spaces (no tabs)
- **Key spacing:** Space after colon (`key: value`)
- **List items:** Dash with space (`- item`)
- **Comments:** `#` for inline comments
- **Variable substitution:** `${variable_name}` with optional defaults `${var:default}`
- **Header comment block:** Each component should document purpose, required vars, optional vars, example usage
- **Parameterization:** All home-specific values must be substitution variables - zero hardcoded references

### ESPHome Package Inclusion Pattern (for Quick Start)

```yaml
# In your device config
packages:
  trend: !include
    file: vesta/packages/utils/trend_sensor.yaml
    vars:
      sensor_id: "my_trend"
      source_sensor: sensor.room_temperature
      unit_of_measurement: "°C/min"
```

Or via GitHub remote:
```yaml
packages:
  trend:
    url: github://username/vesta-climate-framework
    file: packages/utils/trend_sensor.yaml
    vars:
      sensor_id: "my_trend"
      source_sensor: sensor.room_temperature
      unit_of_measurement: "°C/min"
```

### Testing Approach

This is a scaffolding story - no ESPHome compilation needed. Validation is:
- Directory structure exists and matches target layout
- All markdown files are well-formatted and complete
- LICENSE is valid MIT text
- .gitignore covers ESPHome artifacts
- README renders correctly on GitHub

### Project Structure Notes

- The `vesta/` directory is a separate git repo inside `esphome-devices/` - treat it as the target repository root
- All paths in this story are relative to `vesta/`
- Do NOT modify any files in the parent `esphome-devices/` project
- The naming "Vesta" comes from the Roman goddess of the hearth - appropriate for a climate control framework

### References

- [Source: _bmad-output/planning-artifacts/epic-19-brief.md] - Full epic brief with all 7 stories
- [Source: _bmad-output/planning-artifacts/architecture.md] - System architecture (Sections 11, 2.3 for coding standards)
- [Source: components/trend_sensor.yaml] - 48 lines, standalone, zero home-specific refs
- [Source: components/failover_sensor.yaml] - 111 lines, standalone, zero home-specific refs
- [Source: components/proportional_demand_sensor.yaml] - 83 lines, depends on trend_sensor, needs param rename
- [Source: components/fancoil_boost_coordinator.yaml] - 313 lines, depends on trend_sensor, 10 hard entity refs
- [Source: components/mev.yaml] - 365 lines, depends on proportional_demand, 7+ hard entity refs
- [Source: CLAUDE.md] - Project conventions and coding standards

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (via Dev Agent - Amelia)

### Debug Log References

No errors encountered during implementation.

### Completion Notes List

- Created complete Vesta repository scaffolding in `vesta/` directory
- Directory structure: `packages/utils/`, `packages/coordinators/`, `docs/`, `examples/` with `.gitkeep` placeholders
- MIT LICENSE with 2026 copyright, Alberto as holder
- .gitignore covers `.esphome/`, `secrets.yaml`, Python cache, IDE files, `.DS_Store`
- README.md includes: project purpose and Vesta naming, Base + Boost innovation section, 5-component overview table with doc links, Quick Start (local + GitHub remote include), Architecture Philosophy (5 key principles highlighted), prerequisites, and documentation links
- CONTRIBUTING.md includes: component proposal process, YAML coding standards (2-space indent, header format, parameterization), variable naming conventions, testing expectations (`esphome config` validation), PR guidelines with checklist
- All 6 acceptance criteria verified and satisfied
- Story completed: 2026-02-08

### Change Log

- 2026-02-08: Story 19.1 implemented - Vesta repository scaffolding complete

### File List

- `vesta/packages/utils/.gitkeep` (new)
- `vesta/packages/coordinators/.gitkeep` (new)
- `vesta/docs/.gitkeep` (new)
- `vesta/examples/.gitkeep` (new)
- `vesta/LICENSE` (new)
- `vesta/.gitignore` (new)
- `vesta/README.md` (new)
- `vesta/CONTRIBUTING.md` (new)

