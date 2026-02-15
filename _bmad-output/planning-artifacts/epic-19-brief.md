# Epic 19: Vesta Climate Framework - Open Source Extraction (Phase 1)

**Date:** February 7, 2026
**Status:** Draft
**Priority:** Medium
**Estimated Story Points:** 12

---

## Executive Summary

Extract and generalize 5 production-proven ESPHome climate control components from the esphome-devices codebase into a new open-source project called **Vesta** (Roman goddess of the hearth). The goal is to give back to the ESPHome/Home Assistant community by sharing reusable patterns that solve real multi-zone HVAC challenges.

### Key Innovation

**"Base + Boost" Pattern**: The hero component (Fancoil Boost Coordinator) treats radiant floor and fancoil systems as complementary layers rather than either/or alternatives. Radiant provides efficient baseline comfort; fancoils activate automatically when temperature delta, humidity, or PID saturation demands more capacity. This pattern is not documented elsewhere in the ESPHome ecosystem.

---

## Problem Statement

### Current State

- 5 battle-tested ESPHome components exist within a private residential climate control system
- These components solve problems that many HVAC integrators face (failover, proportional control, multi-subsystem coordination)
- The components are already well-parameterized and have no home-specific hardcoding
- No open-source ESPHome framework exists for multi-zone climate orchestration

### Why This Matters

- **Community gap**: ESPHome users building multi-zone HVAC systems reinvent the same patterns repeatedly
- **Proven patterns**: These components run in production controlling 13 zones across 3 floors - they work
- **Novel approaches**: The Base + Boost pattern and HA-optional architecture invert typical ESPHome thinking
- **Low extraction effort**: Components are already modular and parameterized

---

## Proposed Solution

### Scope: Phase 1 Only (Foundation Release)

Create the `vesta-climate-framework` repository with extracted, generalized, and documented components. Phase 2 (CLI tool) and Phase 3 (Web wizard) are explicitly out of scope.

### Component Inventory

| Component | Type | Lines | Extraction Effort | Dependencies |
|-----------|------|-------|-------------------|--------------|
| **Trend Sensor** | Utility | 48 | Low | None |
| **Failover Sensor** | Utility | 111 | Low | None |
| **Proportional Demand Sensor** | Utility | 83 | Low | trend_sensor |
| **Fancoil Boost Coordinator** | Coordinator | 313 | Medium | trend_sensor |
| **MEV Ventilation Coordinator** | Coordinator | 365 | Medium | proportional_demand_sensor → trend_sensor |

### Extraction Sequencing

```
Story 19.1: Repo scaffolding
    │
Story 19.2: Trend Sensor ← Quick win, establishes patterns
    │
    ├── Story 19.3: Failover Sensor (independent)
    │
    ├── Story 19.4: Proportional Demand Sensor (depends on trend)
    │
    ├── Story 19.5: Fancoil Boost Coordinator ← HERO (depends on trend)
    │
    └── Story 19.6: MEV Coordinator (depends on proportional_demand → trend)
            │
        Story 19.7: Documentation & examples (depends on all extractions)
```

### Target Repository Structure

```
vesta-climate-framework/
├── README.md                      # Project overview, hero component highlight
├── LICENSE                        # MIT or Apache 2.0
├── CONTRIBUTING.md                # How to contribute
├── packages/
│   ├── utils/
│   │   ├── trend_sensor.yaml
│   │   ├── failover_sensor.yaml
│   │   └── proportional_demand_sensor.yaml
│   └── coordinators/
│       ├── fancoil_boost.yaml
│       └── mev_ventilation.yaml
├── examples/
│   └── two_zone_radiant_fancoil.yaml
└── docs/
    ├── principles.md              # 9 foundational principles
    ├── getting-started.md
    ├── trend-sensor.md
    ├── failover-sensor.md
    ├── proportional-demand.md
    ├── fancoil-boost.md           # Deep dive on hero component
    └── mev-ventilation.md
```

---

## User Stories

| Story | Title | Points | Priority |
|-------|-------|--------|----------|
| 19.1 | Repository Scaffolding | 1 | High |
| 19.2 | Extract Trend Sensor (Quick Win) | 1 | High |
| 19.3 | Extract Failover Sensor | 2 | High |
| 19.4 | Extract Proportional Demand Sensor | 1 | High |
| 19.5 | Extract Fancoil Boost Coordinator (Hero) | 3 | High |
| 19.6 | Extract MEV Ventilation Coordinator | 2 | High |
| 19.7 | Documentation, Principles & Examples | 2 | Medium |

**Total: 12 Story Points**

---

## Technical Specification

### Story 19.1: Repository Scaffolding

**Description:** Create the `vesta-climate-framework` repository with the directory structure, README, LICENSE, and contribution guidelines.

**Deliverables:**
- GitHub repository created
- README.md with project vision, "why Vesta" narrative, component overview table
- LICENSE file (MIT recommended for maximum adoption)
- CONTRIBUTING.md with guidelines for PRs, component proposals, testing expectations
- Directory structure: `packages/utils/`, `packages/coordinators/`, `docs/`, `examples/`
- `.gitignore` for ESPHome build artifacts

**Acceptance Criteria:**
- [ ] Repository created on GitHub
- [ ] README explains the project purpose, the 3-tier package structure, and links to component docs
- [ ] LICENSE file present
- [ ] CONTRIBUTING.md describes how to propose new components, testing expectations, and coding standards
- [ ] Directory structure matches the target layout
- [ ] Repository is public

---

### Story 19.2: Extract Trend Sensor (Quick Win)

**Description:** Extract the trend sensor utility as the first component. This establishes the extraction pattern (parameterization, documentation, examples) that all subsequent stories will follow.

**Source:** `components/trend_sensor.yaml` (48 lines)

**Generalization Work:**
- Review all parameter names for clarity outside this project's context
- Ensure no references to esphome-devices-specific entities
- Add header comment block with: purpose, required vars, optional vars, example usage

**Target:** `packages/utils/trend_sensor.yaml`

**Documentation:** `docs/trend-sensor.md`
- What it does and why you'd use it
- Parameter reference table
- Usage example showing inclusion via `!include` with vars
- How the sliding window moving average works

**Acceptance Criteria:**
- [ ] `packages/utils/trend_sensor.yaml` is self-contained and compiles with only its declared parameters
- [ ] All parameters documented with types and defaults
- [ ] `docs/trend-sensor.md` written with usage example
- [ ] Extraction pattern established (header format, parameter naming convention, doc structure)

---

### Story 19.3: Extract Failover Sensor

**Description:** Extract the 3-tier failover sensor utility. This component solves a universal reliability problem: how to keep climate control working when sensor sources fail.

**Source:** `components/failover_sensor.yaml` (111 lines)

**Generalization Work:**
- Abstract tier naming to be generic (Primary → Secondary → Emergency) while keeping the HA/UDP example
- Review parameter names - ensure `udp_sensor_id` and `ha_*_sensor_id` naming is intuitive for external users
- Consider whether tier sources should be more configurable (not everyone uses UDP)
- Add header comment block

**Target:** `packages/utils/failover_sensor.yaml`

**Documentation:** `docs/failover-sensor.md`
- The 3-tier failover concept with diagram
- When to use this vs simpler approaches
- Parameter reference
- Usage example with HA + UDP + emergency
- How automatic recovery works

**Acceptance Criteria:**
- [ ] `packages/utils/failover_sensor.yaml` compiles with declared parameters
- [ ] Tier architecture documented with ASCII/text diagram
- [ ] Parameter reference complete
- [ ] Usage example shows a realistic climate control scenario
- [ ] Automatic recovery behavior explained

---

### Story 19.4: Extract Proportional Demand Sensor

**Description:** Extract the proportional demand sensor, which converts any sensor reading into a 0-100% demand signal with optional rate-of-change boost.

**Source:** `components/proportional_demand_sensor.yaml` (83 lines)

**Generalization Work:**
- Current parameter names use `mev_slug`/`mev_name` prefix - generalize to component-agnostic naming
- Document the dependency on `trend_sensor.yaml` clearly
- Ensure HA input_number references are documented as optional configuration sources

**Target:** `packages/utils/proportional_demand_sensor.yaml`

**Documentation:** `docs/proportional-demand.md`
- Concept: turning sensor values into demand percentages
- The math: linear mapping with clamping and rate boost
- Dependency: requires trend_sensor
- Parameter reference
- Usage examples: humidity demand, CO2 demand, generic sensor demand

**Acceptance Criteria:**
- [ ] `packages/utils/proportional_demand_sensor.yaml` compiles with trend_sensor as dependency
- [ ] Parameter names are component-agnostic (no `mev_` prefix)
- [ ] Dependency on trend_sensor clearly documented
- [ ] Rate boost feature explained with practical example
- [ ] At least 2 usage examples (humidity, CO2)

---

### Story 19.5: Extract Fancoil Boost Coordinator (Hero)

**Description:** Extract the flagship component. This is the project's differentiator - the "Base + Boost" pattern where radiant floor provides efficient baseline and fancoils activate as a responsive boost layer.

**Source:** `components/fancoil_boost_coordinator.yaml` (313 lines)

**Generalization Work:**
- Review all parameter names for external clarity
- Ensure room-specific naming is generic (`zone_slug` vs `room_slug` if appropriate)
- Document the three activation triggers and deactivation logic clearly
- Dependency on trend_sensor must be explicit

**Target:** `packages/coordinators/fancoil_boost.yaml`

**Documentation:** `docs/fancoil-boost.md` (deep dive)
- The problem: radiant vs fancoil, efficiency vs responsiveness
- The Base + Boost innovation: why complementary layers beat either/or
- Architecture diagram of the decision logic
- Three activation triggers explained:
  1. Reactive - Temperature delta exceeds threshold
  2. Reactive - Humidity exceeds threshold with hysteresis
  3. Predictive - PID saturation with no temperature improvement
- Deactivation logic (AND condition)
- Anti-oscillation: hysteresis dead band + minimum time-in-state
- Parameter reference (all thresholds, timings, defaults)
- Complete integration example: one zone with radiant PID + fancoil + boost coordinator
- Diagnostic sensors reference

**Acceptance Criteria:**
- [ ] `packages/coordinators/fancoil_boost.yaml` compiles with declared dependencies
- [ ] All three activation triggers documented with rationale
- [ ] Deactivation AND-logic documented
- [ ] Hysteresis and anti-oscillation behavior explained
- [ ] Complete integration example provided
- [ ] Dependency on trend_sensor documented
- [ ] Diagnostic sensors listed and explained

---

### Story 19.6: Extract MEV Ventilation Coordinator

**Description:** Extract the MEV ventilation coordinator with its multi-demand orchestration and humidity cascade state machine.

**Source:** `components/mev.yaml` (365 lines)

**Generalization Work:**
- Abstract hardware-specific relay names to generic outputs
- Generalize the 3-demand model (CO2, IAQ, humidity) to be configurable
- Document the humidity cascade state machine clearly
- Dependencies: proportional_demand_sensor → trend_sensor

**Target:** `packages/coordinators/mev_ventilation.yaml`

**Documentation:** `docs/mev-ventilation.md`
- Multi-demand orchestration: how multiple air quality inputs drive a single fan speed
- MAX aggregation: why the highest demand wins
- Humidity cascade state machine (Fan Only → Dehumidifying → Cooling)
- Escalation/de-escalation logic with delays
- Season awareness (cooling state disabled in winter)
- Hardware abstraction: relays, DAC output, alarm input
- Parameter reference
- Integration example

**Acceptance Criteria:**
- [ ] `packages/coordinators/mev_ventilation.yaml` compiles with declared dependencies
- [ ] Multi-demand orchestration pattern documented
- [ ] Humidity cascade state machine documented with state diagram
- [ ] Escalation/de-escalation timing explained
- [ ] Season awareness documented
- [ ] Dependency chain documented (proportional_demand → trend_sensor)
- [ ] Hardware requirements listed (relays, DAC, sensors)

---

### Story 19.7: Documentation, Principles & Examples

**Description:** Write the foundational documentation that ties the components together and helps users understand the architectural philosophy.

**Deliverables:**

**`docs/principles.md`** - The 9 foundational principles from the brainstorming session:
1. Integrated Climate Orchestration
2. Single Source of Truth for Mode
3. HA-Enhanced, Not HA-Dependent
4. Minimal Zone Contract
5. Autonomous Core
6. Logic Lives on the Edge
7. Direct Board Communication
8. Heterogeneous Subsystem Support
9. Match Thermal Inertia to Disturbance Patterns

**`docs/getting-started.md`:**
- Prerequisites (ESPHome version, hardware)
- How to include Vesta packages in your ESPHome config
- Recommended starting point (trend sensor → build up)
- Link to component docs

**`examples/two_zone_radiant_fancoil.yaml`:**
- Complete working example showing 2 zones with:
  - Radiant floor PID (base layer)
  - Fancoil (boost layer)
  - Boost coordinator
  - Trend sensor
  - Failover sensor
- Commented throughout to explain each section

**Final README polish:**
- Component overview table with links
- Quick start snippet
- Architecture philosophy summary

**Acceptance Criteria:**
- [ ] `docs/principles.md` documents all 9 principles with explanations
- [ ] `docs/getting-started.md` provides clear onboarding path
- [ ] `examples/two_zone_radiant_fancoil.yaml` is a complete, commented, compilable example
- [ ] README links to all component docs
- [ ] README includes component overview table

---

## Dependencies

### Prerequisites
- GitHub account for repository creation
- All 5 source components exist and are production-stable in esphome-devices

### Internal Dependencies
- Story 19.2 (Trend Sensor) should be completed first - establishes patterns
- Story 19.4 depends on 19.2 (proportional demand uses trend sensor)
- Story 19.5 depends on 19.2 (fancoil boost uses trend sensor)
- Story 19.6 depends on 19.4 (MEV uses proportional demand)
- Story 19.7 depends on all extraction stories

### External Dependencies
- None (all components already exist in the codebase)

---

## Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Components have hidden home-specific assumptions | Extraction breaks generality | Low | Components already parameterized; thorough review during extraction |
| Dependency chain too tight for standalone use | Adoption friction | Medium | Document minimal includes; consider inlining trend_sensor for simple use cases |
| Naming conventions confusing for external users | Poor adoption | Medium | Review all parameter names during extraction; get early feedback |
| Scope creep into Phase 2 (CLI/web) | Delayed delivery | Medium | Strict Phase 1 boundary; defer all tooling |
| License choice limits adoption | Reduced community impact | Low | MIT license recommended for maximum permissiveness |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Components extracted | 5/5 | All components in repo |
| Components compile standalone | 5/5 | ESPHome config validation |
| Documentation complete | 100% | Every component has a doc page |
| Example compiles | Yes | ESPHome config validation |
| Repository public | Yes | GitHub visibility |

---

## Out of Scope

- **Phase 2**: CLI scaffolding tool
- **Phase 3**: Web wizard
- **Community announcement**: Forum posts, Discord announcement (separate effort after repo stabilizes)
- **Device configs**: Hardware-specific device configurations (community-contributed later)
- **MEV device driver**: Machine-specific driver code (too hardware-specific)
- **CI/CD**: Automated testing pipeline (future improvement)

---

## Implementation Timeline

| Week | Stories | Milestone |
|------|---------|-----------|
| 1 | 19.1, 19.2, 19.3 | Repo + first two utilities |
| 2 | 19.4, 19.5 | Remaining utility + hero component |
| 3 | 19.6, 19.7 | MEV coordinator + documentation |

---

## Appendices

### A. Source Documents

- **Brainstorming Session:** `_bmad-output/analysis/brainstorming-session-2026-02-05.md`

### B. Component Source Locations

| Component | Source Path | Lines |
|-----------|-----------|-------|
| Trend Sensor | `components/trend_sensor.yaml` | 48 |
| Failover Sensor | `components/failover_sensor.yaml` | 111 |
| Proportional Demand | `components/proportional_demand_sensor.yaml` | 83 |
| Fancoil Boost | `components/fancoil_boost_coordinator.yaml` | 313 |
| MEV Ventilation | `components/mev.yaml` | 365 |

### C. Rejected Alternatives

| Alternative | Reason Rejected |
|-------------|----------------|
| Extract all components in one story | Too large, no intermediate validation |
| Start with hero component | Trend sensor establishes patterns more safely |
| Include device configs in Phase 1 | Too hardware-specific; community should contribute these |
| Include CLI tool in Phase 1 | Scope creep; templates + docs first, tooling second |
| Create ESPHome custom component (C++) | YAML packages are simpler, more accessible, easier to contribute to |

---

*Epic Brief Created: February 7, 2026*
*Based on: Brainstorming Session (2026-02-05)*
