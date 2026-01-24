# Epic 8: Unified State Machine Architecture - Brainstorming Session Results

**Session Date:** October 31, 2025  
**Facilitator:** Business Analyst Mary 📊  
**Participant:** Alberto (System Owner)

---

## Executive Summary

**Topic:** Consolidating emergency shutdown and window detection state machines into a unified architectural pattern

**Session Goals:** Broadly explore multiple architectural approaches for unifying two parallel state machines (emergency sensor failure and window detection) that currently operate independently but perform similar coordination tasks.

**Techniques Used:**
1. Analogical Thinking (15 min) - Event-driven architecture patterns
2. First Principles Thinking (20 min) - Fundamental interface design
3. SCAMPER Method (20 min) - Systematic architectural exploration
4. Assumption Reversal (10 min) - Challenge core design assumptions

**Total Ideas Generated:** 25+ architectural concepts and design decisions

**Key Themes Identified:**
- **Separation of Concerns:** Conditions detect, coordinator controls (no overlap)
- **State Machine Engine:** Coordinator provides centralized state management for all conditions
- **Interface Minimalism:** Start simple (boolean), evolve to state+priority contract
- **Configuration-Driven:** Always-present conditions, enabled/disabled via vars
- **Extensibility First:** Design for future conditions (occupancy, etc.) from day one
- **Diagnostics Rich:** Multi-level visibility (per-condition + coordinator aggregate)

---

## Technique Sessions

### 1. Analogical Thinking - Event-Driven Architecture Patterns (15 min)

**Description:** Explored how event-driven software architectures solve similar multi-source coordination problems, drawing parallels to our shutdown condition coordination challenge.

**Ideas Generated:**

1. **Event Bus Pattern** - Central "room control bus" where conditions publish events (sensor_emergency, window_opened), coordinator subscribes and decides actions
2. **Event Aggregator Pattern** - Separate components for condition detection vs. shutdown decision making, with aggregator applying priority rules
3. **Reactive Streams Pattern** - State flows through transformation stages: raw sensor → condition detection → state filtering → action execution
4. **Saga/Workflow Pattern** - Multi-step orchestration with explicit states and transition guards, similar to current 3-state pattern but generalized

**Insights Discovered:**
- Event-driven patterns naturally separate "what happened" (conditions) from "what to do" (coordinator)
- Aggregator pattern provides clear extension point for future conditions
- Our current interval-based polling already approximates event processing
- ESPHome globals can serve as event flags in a publish-subscribe model

**Notable Connections:**
- Event Bus + Event Aggregator complement each other: bus = communication layer, aggregator = decision layer
- Saga pattern maps directly to our proven Epic 5 state machine (Normal → Emergency → Recovering)
- Reactive streams might be over-engineered for YAML, but transformation stages concept is valuable

**Decision Made:** Adopt Event Bus + Event Aggregator hybrid architecture

---

### 2. First Principles Thinking - Interface Contract Design (20 min)

**Description:** Broke down to fundamentals to discover the minimal, essential interface between conditions and coordinator. Started with "boolean flag" assumption and evolved through iterations.

**Ideas Generated:**

5. **Shutdown Condition Definition:** "A boolean flag representing whether shutdown is required" (initial)
6. **Interface Evolution:** Boolean insufficient due to recovery state complexity
7. **State Enum Contract:** Normal (0) / Active (1) / Recovering (2) - three distinct operational states
8. **Priority Addition:** Each condition specifies numeric priority (1=highest, 2=second, etc.)
9. **Final Interface:** State enum + Priority integer = minimal viable contract
10. **Condition Encapsulation:** Conditions manage internal complexity (timeouts, timestamps), expose only state+priority
11. **Recovery Ownership:** Per-condition recovery timers (internal), coordinator trusts the exposed state

**Insights Discovered:**
- Boolean flags work for "on/off" but fail to capture "transitioning" states
- Recovery is neither "active" nor "normal"—it's a distinct third state requiring representation
- Priority enables hierarchical coordination without conditions knowing about each other
- The simplest interface that ACTUALLY works is state+priority (not just boolean)

**Notable Connections:**
- State enum maps to text_sensor diagnostics naturally
- Priority hierarchy emerged from event aggregator pattern discussion
- Recovery state requirement drove interface complexity from boolean to enum

**Decision Made:** Interface contract = State enum (Normal/Active/Recovering) + Priority integer

---

### 3. SCAMPER Method - Systematic Architectural Modifications (20 min)

**Description:** Applied SCAMPER framework to systematically explore modifications to current architecture: Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse.

#### S - Substitute

**Ideas Generated:**

12. Keep interval-based polling (no substitution to event-driven triggers)
13. Keep per-condition text_sensors (no substitution to single unified sensor)
14. Keep manual include pattern (no substitution to plugin registry)

**Decision Made:** No substitutions needed—current patterns work well

#### C - Combine

**Ideas Generated:**

15. **Separate condition state machines + unified coordinator** - Keep detection independent, add coordinator for aggregation
16. **Single coordinator diagnostic** - Add coordinator text_sensor showing overall room control state
17. **Keep per-condition diagnostics** - Don't merge; maintain visibility at all levels

**Decision Made:** Conditions detect independently, coordinator aggregates and controls PID

#### A - Adapt

**Ideas Generated:**

18. **Stateless coordinator logic** - Coordinator has no state machine itself, just reads conditions and applies rules
19. **Epic 5 pattern reuse** - Leverage proven 3-state pattern but at condition level, not coordinator
20. **Epic 7 mode-awareness** - Per-condition mode requirements via vars (window: shutdown in cooling/heating)

**Decision Made:** Coordinator is stateless; conditions own state machines; mode-awareness per-condition

#### M - Modify

**Ideas Generated:**

21. **Remove PID control from conditions** - Both room_emergency_shutdown.yaml and room_window_detection.yaml lose PID control logic
22. **Conditions expose state+priority globals only** - No internal decision making about PID
23. **Coordinator trusts condition flags completely** - No second-guessing or validation

**Decision Made:** Clean separation—conditions are detectors, coordinator is controller

#### P - Put to Other Use

**Ideas Generated:**

24. **Future conditions:** Occupancy detection (Epic 9+), though humidity and schedules better in HA
25. **Scope focus:** Safety-critical conditions that need local ESPHome control (must work if HA down)

**Insight Discovered:** Design should accommodate future conditions but maintain ESPHome vs HA boundary (local safety vs remote orchestration)

#### E - Eliminate

**Ideas Generated:**

26. **Eliminate room_emergency_shutdown.yaml** - Component becomes obsolete, logic moves to coordinator
27. **Eliminate PID control from room_window_detection.yaml** - Moves to coordinator
28. **Eliminate duplicate interval polling** - Single coordinator interval replaces condition-level polling for PID

**Decision Made:** Add coordinator diagnostic, keep per-condition diagnostics (multi-level visibility)

#### R - Reverse / Rearrange

**Ideas Generated:**

29. **Always-present conditions, config-disabled via vars** - Instead of conditionally including components, compile all into coordinator and enable/disable via configuration

**Decision Made:** Major architectural shift—conditions always present, enabled/disabled declaratively

---

### 4. Assumption Reversal - Challenge Core Design (10 min)

**Description:** Challenged three fundamental assumptions to validate or improve architectural decisions.

**Assumptions Challenged:**

#### Assumption 1: "Conditions must be YAML components"

**Reversal explored:** Inline lambda functions in coordinator

**Decision Made:** **Confirmed** - Separate YAML components win for reusability

#### Assumption 2: "State machines must manage timeouts internally"

**Reversal explored:** Coordinator provides state machine engine, conditions report raw sensor state

**Decision Made:** **REVERSED** - Coordinator provides state machine engine with configurable per-room timeouts

**Breakthrough Insight:** This transforms conditions from "smart state machines" to "dumb sensors." The coordinator becomes the intelligent engine that interprets sensor data into state transitions.

#### Assumption 3: "Recovery is a distinct state"

**Reversal explored:** Recovery as "active with countdown" rather than separate state

**Decision Made:** **MODIFIED** - Single "Recovering" state at coordinator level, but track per-condition recovery countdowns for diagnostics

---

## Idea Categorization

### Immediate Opportunities

Ideas ready to implement in Epic 8:

1. **Room Control Coordinator Component**
   - Description: New `room_control_coordinator.yaml` component that reads condition states and controls PID
   - Why immediate: Core of Epic 8, enables all other changes
   - Resources needed: Component development, state machine engine implementation
   - Timeline: Epic 8 primary deliverable

2. **Condition Interface Standardization**
   - Description: Define and document state+priority global variable contract
   - Why immediate: Foundation for coordinator; conditions must conform
   - Resources needed: Interface specification document, naming conventions
   - Timeline: Epic 8 planning phase (before implementation)

3. **Simplified Condition Components**
   - Description: Refactor room_sensors.yaml and room_window_detection.yaml to remove PID control, expose only state+priority
   - Why immediate: Required for coordinator to work; simplifies existing components
   - Resources needed: YAML refactoring, testing in one room
   - Timeline: Epic 8 implementation phase

### Future Innovations

Ideas requiring development in future epics:

4. **Occupancy-Based Shutdown (Epic 9+)**
   - Description: Additional condition that triggers shutdown when room unoccupied for extended period
   - Development needed: Occupancy sensor integration, state machine logic, energy-saving policy
   - Timeline estimate: Post-Epic 8, after coordinator pattern proven

5. **Dynamic Priority System**
   - Description: Priorities adjust based on context (time of day, PID mode, season)
   - Development needed: Priority calculation logic, context sensors, configuration DSL
   - Timeline estimate: Epic 10+, after multiple conditions in production

6. **Multi-Room Coordination**
   - Description: Building-wide coordinator that coordinates across room coordinators
   - Development needed: Inter-room communication, building-level policy engine
   - Timeline estimate: Epic 11+, architectural expansion

### Moonshots

Ambitious, transformative concepts for long-term consideration:

7. **Generic State Machine Engine Library**
   - Description: Extract coordinator's state machine logic into reusable ESPHome library for any multi-condition coordination
   - Transformative potential: Reusable across projects, community contribution
   - Challenges to overcome: ESPHome custom component development, API design, documentation

8. **Declarative Condition DSL**
   - Description: YAML-based domain-specific language for defining conditions without lambda code
   - Transformative potential: Non-programmers can add conditions via configuration
   - Challenges to overcome: Parser implementation, expression evaluation, security sandboxing

### Insights & Learnings

Key realizations from the session:

- **Interface minimalism drives clarity:** Starting with "just a boolean" forced us to discover what's ACTUALLY needed (state enum + priority)
- **Separation of concerns enables extensibility:** Conditions that don't know about PID control can't break it
- **Stateless coordinator is simpler:** All state complexity lives in conditions; coordinator just reads and decides
- **Always-present pattern reduces fragility:** Config-disabled conditions safer than conditional includes (no YAML composition surprises)
- **Per-condition diagnostics + coordinator diagnostic = full observability:** Can debug both "why" (condition states) and "what" (coordinator action)
- **Event-driven thinking clarifies architecture:** Even though implementation is interval-based, thinking in terms of events/aggregation revealed clean boundaries
- **Recovery as distinct state is essential:** Treating recovery as "still active" (PID stays OFF) vs. "back to normal" (PID resumes) requires explicit state
- **Priority hierarchy prevents conflict:** Emergency > Window ensures predictable behavior when multiple conditions trigger
- **Coordinator-managed timeouts enable per-room tuning:** Different rooms can have different timeout requirements without duplicating condition logic

---

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Define Condition Interface Contract

- **Rationale:** Foundation for entire Epic 8 architecture; coordinator and conditions must agree on contract before implementation begins
- **Next steps:**
  1. Document exact global variable naming convention (`${zone_slug}_${condition_id}_state` and `${zone_slug}_${condition_id}_priority`)
  2. Specify state enum values (0=Normal, 1=Active, 2=Recovering) and semantic meaning
  3. Define priority integer range and hierarchy (1=highest, Emergency=1, Window=2, Occupancy=3)
  4. Document minimal debugging globals each condition should expose (e.g., `last_trigger_time`)
  5. Create example condition component showing interface implementation
- **Resources needed:** Architecture documentation time, review with system owner
- **Timeline:** 1-2 days in Epic 8 planning phase (before coding begins)

#### #2 Priority: Design Coordinator State Machine Engine

- **Rationale:** This is the core innovation of Epic 8; transforms two parallel state machines into unified coordination
- **Next steps:**
  1. Flow diagram showing state transitions with multiple conditions
  2. Pseudocode for priority resolution logic
  3. Timeout application algorithm (per-condition trigger/recovery timeouts)
  4. PID control decision tree (when to turn OFF, when to allow resume)
  5. Diagnostic text_sensor format showing active conditions and countdowns
  6. Edge case handling (simultaneous triggers, recovery interruption, sensor unavailability)
- **Resources needed:** Architecture design time, state machine expertise, ESPHome lambda development
- **Timeline:** 2-3 days in Epic 8 design phase, before component implementation

#### #3 Priority: Migration Strategy from Epic 5/7 to Epic 8

- **Rationale:** 6+ rooms currently in production using Epic 5 (emergency) and Epic 7 (window) patterns; need safe migration path
- **Next steps:**
  1. Assess backward compatibility requirements (can old and new coexist?)
  2. Document step-by-step migration for single room (test subject)
  3. Create migration checklist for remaining rooms
  4. Define rollback procedure if Epic 8 has issues
  5. Plan phased rollout schedule (1 room → validate → remaining rooms)
  6. Update room component packages to use new coordinator pattern
- **Resources needed:** Migration guide documentation, testing time per room, validation criteria
- **Timeline:** Migration guide during Epic 8 implementation; actual room migrations over 1-2 weeks post-Epic 8 completion

---

## Reflection & Follow-up

### What Worked Well

- **Analogical thinking unlocked event-driven patterns:** Starting with familiar software architecture concepts provided immediate vocabulary and structure
- **First principles iteration revealed interface needs:** Starting with "boolean" and discovering it's insufficient led to optimal state+priority design
- **SCAMPER comprehensive coverage:** Systematic exploration prevented missing architectural alternatives
- **Assumption reversal validated key decisions:** Challenging "conditions are components" confirmed separation of concerns; reversing "conditions manage state" revealed coordinator engine breakthrough
- **Progressive narrowing from broad to specific:** Starting with exploration, then making decisions, created clear architectural path
- **Real-time decision capture:** Making decisions during brainstorming (not deferring) created momentum and clarity

### Areas for Further Exploration

- **Diagnostic output format:** Exact text sensor wording for coordinator state (e.g., "Shutdown (Emergency, P1)" vs. "Emergency Shutdown Active")
- **Configuration schema:** Detailed YAML structure for coordinator vars (defaults, overrides, condition-specific settings)
- **Testing strategy:** How to validate state machine engine with multiple condition combinations
- **Performance impact:** Does single coordinator interval with multiple condition reads affect ESPHome performance?
- **HA integration:** How should HA dashboard display coordinator state vs. individual condition states?

### Recommended Follow-up Techniques

- **Morphological Analysis:** Create matrix of coordinator parameters (timeout values, priority levels, state representations) and explore combinations for optimal defaults
- **Role Playing:** Brainstorm from different stakeholder perspectives (installer debugging in field, HA automation writer, future maintainer) to refine diagnostics and configuration
- **Scenario Planning:** Walk through edge cases (power loss during recovery, HA unavailable during condition trigger, multiple conditions rapidly cycling) to strengthen robustness

### Questions That Emerged

- Should coordinator expose a "last active condition" diagnostic for when all conditions clear but you want to know what triggered last shutdown?
- How should coordinator handle condition components that are missing (not included in device YAML)?
- Should there be a coordinator-level "master enable" flag that can disable all automated shutdown?
- What happens if a condition's priority global is not set or invalid?
- Should mode-awareness be enforced at coordinator level (global policy) or remain per-condition (flexible but complex)?
- How should coordinator handle PID climate entity being unavailable (entity not created yet at boot)?

### Next Session Planning

- **Suggested topics:**
  1. Epic 8 implementation details (state machine lambda code, configuration schema)
  2. Testing strategy and validation criteria (how to prove Epic 8 works correctly)
  3. Migration playbook (step-by-step room conversion procedures)
- **Recommended timeframe:** After interface contract documented (Priority #1 complete), before full implementation begins
- **Preparation needed:** Draft coordinator component skeleton, example condition showing interface compliance, list of edge cases to test

---

*Session facilitated using the BMAD-METHOD™ brainstorming framework*

---

## Appendix: Architectural Decisions Summary

For quick reference, key decisions made during this session:

| Decision Area | Choice | Rationale |
|--------------|--------|-----------|
| **Core Pattern** | Event Bus + Event Aggregator | Separates communication from decision making |
| **Condition Interface** | State enum + Priority integer | Captures operational state (Normal/Active/Recovering) with hierarchy |
| **Component Architecture** | Split: Conditions detect, Coordinator controls | Clean separation of concerns, extensible |
| **Coordinator State** | Stateless | All state complexity lives in conditions |
| **Condition Presence** | Always-present, config-disabled | Simpler than conditional includes |
| **Priority Hierarchy** | Static: Emergency(1) > Window(2) > Future(3+) | Predictable, simple to understand |
| **Recovery Management** | Single coordinator "Recovering" state, per-condition countdowns | Unified state with detailed diagnostics |
| **Timeout Ownership** | Coordinator manages all timeouts | Per-room configurability, conditions report raw state |
| **Mode-Awareness** | Per-condition via vars | Flexible (window needs it, emergency doesn't) |
| **Diagnostics** | Multi-level: per-condition + coordinator | Full observability for debugging |
| **PID Control** | Coordinator only | Single point of control |
| **Migration** | Phased rollout, backward compatible during transition | Safe production deployment |

---

**End of Brainstorming Session Document**
