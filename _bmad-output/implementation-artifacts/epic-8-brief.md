# Project Brief: Epic 8 - Unified State Machine Architecture

**Project:** ESPHome Multi-Floor Climate Control System  
**Epic:** 8 - Unified State Machine Architecture  
**Date:** October 31, 2025  
**Status:** Planning  
**Owner:** Alberto (System Owner)

---

## Executive Summary

**Epic 8: Unified State Machine Architecture** consolidates the existing parallel emergency shutdown and window detection state machines into a single, extensible coordination pattern using an event-driven aggregator design. The new `room_control_coordinator.yaml` component will act as a stateless control engine that reads condition states (emergency sensor failure, window open, future: occupancy) and coordinates PID climate control actions through a clean state+priority interface contract. This architectural simplification reduces code duplication by 40%, enables future condition additions without modifying core logic, and maintains the proven Epic 5/7 reliability patterns while improving system observability.

**Primary problem:** Two independent state machines (emergency shutdown, window detection) duplicate PID control logic and timing patterns, creating maintenance overhead and preventing scalable addition of future shutdown conditions (occupancy, equipment maintenance, etc.).

**Target users:** System owner (Alberto) managing a three-floor residential HVAC system with 6+ rooms currently using Epic 5 (emergency) and Epic 7 (window) patterns in production.

**Key value proposition:** Architectural consolidation that reduces complexity today while creating an extensible foundation for future safety-critical conditions (occupancy detection in Epic 9+), maintaining production reliability through phased migration.

---

## Problem Statement

### Current State

The ESPHome multi-floor climate control system has evolved through multiple epics to include two sophisticated shutdown coordination mechanisms:

- **Epic 5 (Emergency Shutdown):** `room_sensors.yaml` detects HA sensor failures, manages 3-state machine (Normal → Emergency → Recovering), sets global flags; `room_emergency_shutdown.yaml` monitors flags and forces PID OFF.
  
- **Epic 7 (Window Detection):** `room_window_detection.yaml` detects window-open conditions, manages identical 3-state machine, includes mode-awareness (shutdown only in cooling/heating), and directly controls PID.

Both mechanisms implement nearly identical patterns: 180-second trigger timeouts, recovery stability periods, PID control via `climate.control` API, and diagnostic text sensors. However, they operate completely independently with no coordination layer.

### Pain Points

- **Code Duplication:** PID control logic appears in two separate components with 60+ lines of duplicate state management and interval polling
- **Maintenance Burden:** Bug fixes or improvements to state machine logic must be applied twice
- **Coordination Gaps:** When multiple conditions trigger simultaneously (e.g., sensor fails AND window opens), behavior is undefined—both components try to control the same PID independently
- **Extensibility Blocked:** Adding a third condition (occupancy detection) would require copying the pattern again, compounding technical debt
- **Observability Limitations:** No single source of truth showing "why is PID OFF?"—must check multiple diagnostic sensors to understand system state

### Impact

Current architecture creates risk for production system reliability:
- Maintenance complexity increases linearly with each new condition (O(n) duplication)
- Race conditions possible when multiple conditions interact with PID simultaneously
- Debugging requires examining multiple components to understand control decisions
- Future Epic 9+ (occupancy detection) blocked by architectural limitations

### Why Existing Solutions Fall Short

- **Current pattern (separate components):** Works for 1-2 conditions but doesn't scale beyond that
- **Monolithic approach (single large component):** Would create unmaintainable complexity mixing detection logic with control logic
- **External HA automation:** Can't handle safety-critical conditions that must work when HA is down or slow

### Urgency

With Epic 9 (occupancy-based shutdown) already identified as a future need, and 6 rooms currently in production using Epic 5/7 patterns, addressing architectural debt now prevents costly refactoring later. The brainstorming session (October 31, 2025) revealed a clean separation-of-concerns pattern that can be implemented incrementally without disrupting production systems.

---

## Proposed Solution

### Core Concept

Implement a **coordinator-managed state machine engine** pattern that separates condition detection from control decisions:

**Conditions (Detection Layer):**
- `room_emergency_condition.yaml` (refactored from `room_sensors.yaml`) - Monitors HA sensor availability
- `room_window_condition.yaml` (refactored from `room_window_detection.yaml`) - Monitors HA window sensors
- Future: `room_occupancy_condition.yaml`, `room_maintenance_condition.yaml`, etc.
- **Interface contract:** Each exposes `${zone_slug}_${condition_id}_state` (enum: 0=Normal, 1=Active, 2=Recovering) and `${zone_slug}_${condition_id}_priority` (integer: 1=highest)
- **Responsibilities:** Detect conditions, manage internal state machines with timeouts, expose state+priority globals
- **Not responsible for:** PID control, coordination with other conditions, recovery arbitration

**Coordinator (Control Layer):**
- `room_control_coordinator.yaml` (NEW) - Stateless control engine
- **Responsibilities:** 
  - Poll all condition states via single interval
  - Apply priority hierarchy (Emergency=1 > Window=2 > Occupancy=3)
  - Control PID climate entity based on highest-priority active condition
  - Manage unified recovery state when conditions clear
  - Expose coordinator-level diagnostic showing "Shutdown (Emergency)" or "Normal" or "Recovering (2 conditions clearing)"
- **Configuration:** Per-room timeout overrides, enabled/disabled conditions, mode-awareness settings

### Key Architecture Decisions

From brainstorming session (see `docs/epic-8-brainstorming-session.md` for full rationale):

1. **Event Bus + Event Aggregator pattern** - Conditions publish state via globals, coordinator aggregates
2. **State enum + Priority interface** - Captures Normal/Active/Recovering with hierarchy
3. **Stateless coordinator** - All state complexity lives in conditions
4. **Always-present conditions** - Enabled/disabled via vars (e.g., `emergency_enabled: true`, `window_enabled: false` for rooms without windows)
5. **Coordinator-managed timeouts** - Conditions report raw triggers, coordinator applies per-room timing
6. **Per-condition mode-awareness** - Window condition keeps mode logic, emergency doesn't need it
7. **Multi-level diagnostics** - Keep per-condition sensors + add coordinator aggregate sensor

### Key Differentiators

1. **Separation of concerns:** Unlike monolithic approaches, conditions know nothing about PID control or other conditions
2. **Extensibility without modification:** Adding Epic 9 occupancy detection requires NO changes to coordinator—just include new condition component with conforming interface
3. **Production-safe migration:** Epic 5/7 components can coexist with Epic 8 during phased rollout
4. **Coordinator as engine:** Transforms conditions from "smart state machines managing PID" to "dumb sensors reporting facts"—intelligence centralized

### Why This Solution Succeeds

- **Proven patterns:** Builds on Epic 5 (state machines), Epic 7 (mode-awareness), Epic 4 (room composition)
- **Low risk:** Phased migration (1 room → validate → remaining 5+ rooms) with rollback capability
- **Maintainable:** Single PID control location, conditions isolated from each other
- **Observable:** Coordinator diagnostic shows aggregate state, conditions show individual state
- **Future-proof:** Priority hierarchy and interface contract support infinite future conditions

### High-Level Vision

A climate control system with a pluggable architecture where new shutdown conditions can be added as standalone components without touching existing logic, each condition declares its importance via priority, and the coordinator intelligently orchestrates all conditions into coherent control actions.

---

## Target Users

### Primary User Segment: Residential System Owner (Technical)

**Profile:**
- Single residential system owner managing complex multi-floor HVAC
- Technical proficiency: Advanced (comfortable with ESPHome YAML, Home Assistant automations, git workflows)
- Current system: 6+ rooms in production with Epic 5/7 patterns deployed
- Maintenance patterns: Regular updates, experimental new features in test rooms before rollout

**Current Behaviors:**
- Reviews ESPHome logs to debug climate control issues
- Edits device YAML files to adjust timeout values or add new rooms
- Uses git branches for testing architectural changes before merging to main
- Monitors HA dashboard diagnostics to understand system state

**Specific Needs:**
- **Maintainability:** Reduce time spent applying bug fixes to multiple components
- **Extensibility:** Add occupancy detection (Epic 9) without major refactoring
- **Reliability:** Ensure production rooms continue operating during Epic 8 migration
- **Observability:** Quick diagnosis of "why is this room's PID OFF?" from single sensor

**Goals:**
- Migrate all 6+ rooms to Epic 8 unified architecture within 2-3 weeks
- Reduce future epic implementation time by 30%+ (no more pattern duplication)
- Maintain 99.9% uptime for climate control during migration
- Enable easy addition of Epic 9+ conditions via clean interface

---

## Goals & Success Metrics

### Business Objectives

- **Reduce maintenance overhead:** Consolidate duplicate PID control logic from 2 locations to 1 (measured by lines of code and component count)
- **Enable extensibility:** Support Epic 9+ condition additions with zero coordinator modifications (measured by interface stability)
- **Maintain reliability:** Zero climate control outages during Epic 8 migration (measured by uptime logs)
- **Improve velocity:** Reduce future epic implementation time by 30%+ (measured by Epic 9 development hours vs. Epic 7 baseline)

### User Success Metrics

- **Migration success rate:** 100% of rooms successfully migrated from Epic 5/7 to Epic 8 within 3 weeks
- **Rollback incidents:** 0 rooms requiring rollback to Epic 5/7 due to Epic 8 issues
- **Debugging time reduction:** 50% faster diagnosis of shutdown conditions via unified coordinator diagnostic
- **Configuration simplicity:** New room setup time reduced by 20% (fewer components to include)

### Key Performance Indicators (KPIs)

- **Code reduction:** 40% reduction in state machine + PID control code (target: ~150 lines eliminated)
- **Component consolidation:** Eliminate `room_emergency_shutdown.yaml` component entirely (1 → 0 dedicated shutdown components)
- **Interface compliance:** 100% of conditions (emergency, window, future occupancy) conform to state+priority contract
- **Diagnostic clarity:** Single coordinator text_sensor shows aggregate state in 100% of rooms
- **Migration duration:** Complete production rollout in ≤3 weeks from Epic 8 start
- **Future epic velocity:** Epic 9 (occupancy) implemented in ≤5 days (vs. Epic 7's 7 days baseline)

---

## MVP Scope

### Core Features (Must Have)

1. **Condition Interface Specification**
   - **Description:** Document exact global variable contract (`${zone_slug}_${condition_id}_state` enum, `${zone_slug}_${condition_id}_priority` integer)
   - **Rationale:** Foundation for all components; must be defined before any implementation
   - **Deliverable:** `docs/epic-8-condition-interface-spec.md`

2. **Room Control Coordinator Component**
   - **Description:** New `components/room_control_coordinator.yaml` with stateless coordination logic
   - **Rationale:** Core Epic 8 deliverable enabling all other changes
   - **Features:**
     - Interval-based polling of all enabled condition states
     - Priority resolution (highest active condition wins)
     - PID climate control via `climate.control` API
     - Configurable per-condition timeouts (trigger, recovery)
     - Mode-awareness pass-through (window condition settings respected)
     - Coordinator-level diagnostic text_sensor

3. **Refactored Emergency Condition**
   - **Description:** Simplify `room_sensors.yaml` or create new `room_emergency_condition.yaml`
   - **Rationale:** Must conform to new interface, remove PID control logic
   - **Changes:**
     - Remove all PID control code (move to coordinator)
     - Expose `${zone_slug}_emergency_state` and `${zone_slug}_emergency_priority` (=1)
     - Keep internal state machine and timeout logic (180s trigger, 60s recovery)
     - Keep diagnostic text_sensor for per-condition visibility

4. **Refactored Window Condition**
   - **Description:** Simplify `room_window_detection.yaml` to remove PID control
   - **Rationale:** Must conform to new interface
   - **Changes:**
     - Remove PID control code (move to coordinator)
     - Expose `${zone_slug}_window_state` and `${zone_slug}_window_priority` (=2)
     - Keep mode-awareness logic (window_shutdown_modes parameter)
     - Keep internal state machine and timeout logic

5. **Single-Room Migration Validation**
   - **Description:** Fully migrate one test room (e.g., Soggiorno) from Epic 5/7 to Epic 8
   - **Rationale:** Prove pattern works before rolling out to all rooms
   - **Validation criteria:**
     - Emergency shutdown triggers correctly (simulate HA sensor failure)
     - Window shutdown triggers correctly (open window in cooling mode)
     - Recovery works for both conditions
     - Coordinator diagnostic shows correct state
     - No PID control race conditions observed

6. **Migration Guide**
   - **Description:** Step-by-step documentation for converting rooms from Epic 5/7 to Epic 8
   - **Rationale:** Enables safe production rollout across all rooms
   - **Content:**
     - Before/after component inclusion patterns
     - Configuration changes needed
     - Validation checklist
     - Rollback procedure

### Out of Scope for Epic 8

- **New conditions:** Occupancy detection deferred to Epic 9+
- **Dynamic priorities:** Static hierarchy (Emergency > Window) sufficient for MVP
- **Multi-room coordination:** Building-wide policies deferred to Epic 11+
- **HA integration changes:** Coordinator state exposed same way as existing diagnostics
- **Backward compatibility layer:** Old Epic 5/7 components will be deprecated (not maintained alongside Epic 8)
- **Timeout optimization:** Use existing proven values (180s/60s); per-room tuning can happen post-MVP

### MVP Success Criteria

**Epic 8 MVP is complete when:**
1. All 6+ production rooms successfully migrated from Epic 5/7 to Epic 8 architecture
2. Zero climate control outages or rollbacks during migration
3. Single test room validates emergency + window conditions work correctly under coordinator
4. Interface specification documented and all conditions comply
5. Migration guide enables remaining rooms to convert in <30 minutes each
6. Code metrics show 40%+ reduction in state machine + PID control duplication
7. Coordinator diagnostic provides clear visibility into active conditions

---

## Post-MVP Vision

### Phase 2 Features (Epic 9+)

**Occupancy-Based Shutdown:**
- New `room_occupancy_condition.yaml` component
- Monitors HA occupancy sensors (PIR, mmWave, etc.)
- Priority 3 (lower than emergency, window)
- Triggers shutdown when room unoccupied for configurable duration (e.g., 2 hours)
- **Enabled by Epic 8:** No coordinator changes needed—just include new component with interface compliance

**Per-Room Timeout Customization:**
- Expose coordinator vars for per-condition timeout overrides
- Example: Bathroom has shorter emergency timeout (90s vs. 180s) due to faster temp changes
- **Epic 8 foundation:** Coordinator already designed for configurable timeouts

### Long-term Vision (12-24 months)

**Generic State Machine Engine Library:**
- Extract coordinator logic into reusable ESPHome custom component
- Share with ESPHome community for other multi-condition coordination needs
- Examples: Multi-source water leak detection, security system arming with multiple sensors

**Building-Wide Coordination (Epic 11+):**
- Cross-room policies (e.g., "if 3+ rooms trigger emergency, check distribution board")
- Equipment-level coordination (e.g., mixing valve groups coordinate shutdowns)
- Hierarchical coordinators (room-level → floor-level → building-level)

**Declarative Condition DSL:**
- YAML-based condition definition without lambda code
- Example: `condition: sensor.temperature > 30 for 5 minutes`
- Enables non-programmers to add simple conditions via configuration

### Expansion Opportunities

**Additional Condition Types:**
- Maintenance mode (manual override for equipment servicing)
- Equipment health monitoring (detect valve stuck, fan failure)
- Energy price optimization (shutdown during peak rate periods)
- Time-based scheduling (night setback, vacation mode)

**Enhanced Diagnostics:**
- Historical condition log (last 24 hours of state changes)
- Performance metrics (time spent in each state per condition)
- HA dashboard card showing condition timeline visualization

---

## Technical Considerations

### Platform Requirements

- **Target Platform:** ESPHome (current version in use: 2024.x)
- **Hardware:** Existing A6/A16 boards with Ethernet (no hardware changes)
- **HA Version:** Compatible with current Home Assistant installation (2024.x)
- **Performance Requirements:** Coordinator interval ≤5s (same as existing patterns), negligible ESP32 CPU impact

### Technology Preferences

- **Component Structure:** Standard ESPHome YAML with lambda C++ for logic
- **State Storage:** ESPHome globals (in-memory, non-persisted across reboots)
- **Communication:** HA integration via ESPHome native API (existing pattern)
- **Testing:** Manual validation in test room, then phased production rollout

### Architecture Considerations

- **Repository Structure:** 
  - New component: `components/room_control_coordinator.yaml`
  - Refactored: `components/room_sensors.yaml` (or new `room_emergency_condition.yaml`)
  - Refactored: `components/room_window_detection.yaml` (or new `room_window_condition.yaml`)
  - Deprecated: `components/room_emergency_shutdown.yaml` (moved to `components/deprecated/`)
  - Room packages in `components/rooms/` updated to use coordinator pattern

- **Service Architecture:** 
  - Conditions = independent state machines (detect, set globals)
  - Coordinator = aggregator + controller (read globals, control PID)
  - No direct communication between conditions (decoupled via globals)

- **Integration Requirements:**
  - HA sensor entity IDs (temperature, window binary_sensors) - existing
  - PID climate entity IDs - existing
  - No new HA integrations required

- **Security/Compliance:** 
  - Local control (works when HA down) - existing pattern maintained
  - No cloud dependencies - existing pattern maintained
  - Secrets management via `locals/secrets.yaml` - existing pattern maintained

---

## Constraints & Assumptions

### Constraints

- **Budget:** $0 (software-only changes, no hardware purchases)
- **Timeline:** 3 weeks total (1 week design/implementation, 2 weeks phased migration)
- **Resources:** Solo developer (Alberto), part-time effort (evenings/weekends)
- **Technical:** 
  - Must maintain ESPHome YAML composition patterns (no custom C++ components)
  - Cannot disrupt production climate control (phased migration required)
  - Must work with existing A6/A16 board firmware capacity

### Key Assumptions

- ESPHome globals performance is sufficient for 3-5 condition state variables per room
- Interval polling at 5-second frequency is adequate for coordinator responsiveness
- Existing HA sensor entity IDs remain stable (no entity_id changes during migration)
- Epic 5/7 patterns can coexist with Epic 8 during transition (different rooms use different patterns)
- Single test room validation is sufficient to de-risk production rollout
- 180s/60s timeout values proven in Epic 5/7 remain appropriate for coordinator
- Mode-awareness (window_shutdown_modes) can remain condition-level without coordinator logic
- Priority hierarchy (Emergency=1, Window=2) covers current needs; no dynamic priority needed for MVP

---

## Risks & Open Questions

### Key Risks

- **Migration complexity:** Migrating 6+ rooms without disrupting climate control requires careful sequencing and validation
  - **Mitigation:** Single test room validation, detailed migration checklist, rollback procedure documented

- **Coordinator bugs affect all conditions:** Centralizing PID control means coordinator bugs impact all shutdown logic
  - **Mitigation:** Extensive testing in test room, code review, gradual rollout room-by-room

- **Interface contract changes:** If interface needs modification after conditions implement it, refactoring required
  - **Mitigation:** Thorough interface design upfront, prototype with one condition before implementing all

- **Performance degradation:** Coordinator polling multiple globals could impact ESP32 responsiveness
  - **Mitigation:** Performance monitoring during test room validation, optimize if needed

- **Condition state drift:** If condition fails to update globals, coordinator has stale state
  - **Mitigation:** Coordinator logs when state unchanged for extended period (anomaly detection)

### Open Questions

- Should coordinator expose "last active condition" diagnostic for post-mortem debugging?
- How should coordinator handle missing condition components (included but `enabled: false` vs. not included at all)?
- Should there be coordinator-level "master enable" flag to disable all automated shutdown?
- What happens if condition's priority global is missing or invalid (0, negative, duplicate priority)?
- Should mode-awareness eventually move to coordinator level for consistency, or stay per-condition for flexibility?
- How should coordinator handle PID climate entity unavailable at boot (timing race condition)?

### Areas Needing Further Research

- **Edge case testing:** Systematic enumeration of all state transition combinations (emergency during window recovery, etc.)
- **Performance benchmarking:** Measure ESP32 CPU/memory impact of coordinator vs. current pattern
- **HA dashboard design:** Optimal visualization of coordinator state + per-condition states
- **Epic 9 preview:** Sketch occupancy condition to validate interface contract sufficiency

---

## Appendices

### A. Research Summary

**Brainstorming Session Results (October 31, 2025):**
- Full session documented in `docs/epic-8-brainstorming-session.md`
- 4 techniques used: Analogical Thinking, First Principles, SCAMPER, Assumption Reversal
- 29 ideas generated leading to 12 key architectural decisions
- Breakthrough insight: Coordinator-managed state machine engine transforms conditions from "smart" to "dumb sensors"

**Prior Epic Analysis:**
- **Epic 5 (Emergency Shutdown):** Proven 3-state machine pattern (Normal → Emergency → Recovering), 180s timeout, 60s recovery
- **Epic 7 (Window Detection):** Extended Epic 5 pattern with mode-awareness, separate component with duplicate logic
- **Key takeaway:** Patterns work reliably but duplication prevents scaling to 3+ conditions

### B. Architectural Decisions Summary

See `docs/epic-8-brainstorming-session.md` Appendix for full decision table. Key decisions:

| Decision | Choice | Impact |
|----------|--------|--------|
| Core Pattern | Event Bus + Aggregator | Separates detection from control |
| Interface | State enum + Priority | Captures Normal/Active/Recovering with hierarchy |
| Coordinator State | Stateless | Simplifies logic, state lives in conditions |
| Condition Presence | Always-present, config-disabled | Simpler than conditional includes |
| PID Control | Coordinator only | Single point of control |

### C. References

- **Copilot Instructions:** `.github/copilot-instructions.md` - Repository patterns and Epic summaries
- **Epic 5 Documentation:** `docs/epic-5-*.md` - Emergency shutdown pattern
- **Epic 7 Documentation:** `docs/epic-7-*.md` - Window detection pattern
- **Existing Components:**
  - `components/room_sensors.yaml` - Current emergency detection
  - `components/room_emergency_shutdown.yaml` - Current emergency control
  - `components/room_window_detection.yaml` - Current window detection + control

---

## Next Steps

### Immediate Actions

1. **Review and validate this brief** - Confirm scope, timeline, and approach align with system owner expectations
2. **Priority #1: Define interface contract** - Create `docs/epic-8-condition-interface-spec.md` with exact global naming, state enum values, priority hierarchy
3. **Priority #2: Design coordinator state machine** - Flow diagram, pseudocode for priority resolution, timeout logic, PID control decision tree
4. **Priority #3: Draft migration strategy** - Step-by-step guide for converting first test room from Epic 5/7 to Epic 8

### Transition to Implementation

Once this brief is approved, proceed to PRD creation with detailed:
- Component interface specifications
- Coordinator algorithm pseudocode
- Migration procedures and validation checklists
- Testing strategy for all state transition combinations
- Rollout plan with success criteria per room

---

**Brief Status:** Ready for review and PRD development

---

*Brief created using BMAD-METHOD™ analyst facilitation*
