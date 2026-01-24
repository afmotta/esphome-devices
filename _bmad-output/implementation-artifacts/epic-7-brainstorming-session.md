# Epic 7: Window Detection & Climate Response - Brainstorming Session Results

**Session Date:** October 30, 2025  
**Facilitator:** Business Analyst Mary  
**Participant:** Alberto (System Owner)

---

## Executive Summary

**Topic:** Window detection (from Home Assistant) and climate system response logic for ESPHome multi-floor climate control

**Session Goals:** Focused ideation on response logic and integration patterns for window-triggered climate control adjustments

**Techniques Used:** 
1. SCAMPER Method (15 minutes) - Systematic enhancement exploration
2. Six Thinking Hats (15 minutes) - Multi-perspective evaluation
3. First Principles Thinking (10 minutes) - Core problem validation

**Total Ideas Generated:** 28 key ideas and design decisions

**Key Themes Identified:**
- **Architectural Consistency**: Extend Epic 5 emergency shutdown pattern for windows
- **Equipment-Aware Logic**: Only shutdown equipment that wastes energy (fancoils), not radiant systems
- **User-Centric Design**: 3-minute grace period allows ventilation without disruption
- **Graceful Degradation**: System remains reliable even if window sensors fail
- **Configurable Behavior**: Mode-aware shutdown allows per-room customization

---

## Technique Sessions

### SCAMPER Method - 15 minutes

**Description:** Systematic exploration of how to enhance existing room component architecture by Substituting, Combining, Adapting, Modifying, Putting to other use, Eliminating, and Reversing aspects of current climate control logic.

**Ideas Generated:**

1. **Extend emergency shutdown logic** - Window open = another shutdown trigger (like sensor unavailable)
2. **Window state + sensor state → smarter emergency logic** - Layered shutdown triggers for multiple conditions
3. **Adapt Epic 5 state machine:** Normal → Window Open (timeout-based) → Window Recovering → Normal
4. **PID stops if window open > timeout** - Grace period for brief ventilation without triggering shutdown
5. **Add "Window Open" state** to diagnostic text sensor alongside Normal/Emergency/Recovering
6. **Keep scope focused** - Window detection solely for climate control shutdown, no additional integrations (MEV, energy tracking, etc.)
7. **Maintain standard architectural patterns** - No complexity elimination or responsibility reversal needed

**Insights Discovered:**
- Timeout-based shutdown (not instant) allows brief room ventilation without system disruption
- State machine pattern from Epic 5 is proven and should be reused for consistency
- Keeping scope focused on core climate control prevents feature creep

**Notable Connections:**
- Epic 5 emergency shutdown pattern (sensor unavailable) maps perfectly to window detection
- 180-second timeout already proven in production for sensor emergencies
- Room-based component architecture (Epic 4) supports opt-in window detection

---

### Six Thinking Hats - 15 minutes

**Description:** Multi-perspective evaluation of window detection design, examining facts, benefits, risks, feelings, creativity, and implementation process.

#### 🤍 White Hat - Facts & Data

**Ideas Generated:**

9. **3-minute timeout** for window open → PID shutdown (configurable parameter)
10. **3-minute recovery** period after window closes before returning to Normal
11. **Symmetrical timing** with Epic 5 sensor emergency (180s = 3 minutes)

**Insights:** Reusing the proven 180-second timeout creates consistency and leverages production-validated timing.

#### 💛 Yellow Hat - Benefits & Optimism

**Ideas Generated:**

12. **Primary benefit: Energy savings** - Stop heating/cooling outdoor air
13. **Secondary benefit: Equipment protection** - PID not fighting losing battle
14. **Tertiary benefit: System consistency** - Reuses Epic 5 proven patterns

**Insights:** Energy efficiency is the measurable, primary value driver for this epic.

#### 🖤 Black Hat - Risks & Caution

**Ideas Generated:**

15. **Risk: User unaware of shutdown** → Mitigation: Notification when window-triggered shutdown occurs
16. **Risk: Room gets too cold/hot if user forgets window open** → Mitigation: Notification alerts user to close window
17. **Window sensor unavailable** → Ignore window detection, rely on temperature sensor only (Option C - graceful degradation)
18. **Graceful degradation**: System continues core function even if window detection fails

**Insights:** Fail-safe approach (ignore unavailable sensors) ensures system reliability matches Epic 5 patterns.

#### 🔴 Red Hat - Feelings & Intuition

**Ideas Generated:**

19. **CRITICAL INSIGHT: Window open should ONLY shutdown fancoils, NOT radiant floor heating/cooling**

**Insights:** Fancoils blow air and directly waste energy with open windows. Radiant floor systems have slow thermal mass and are barely affected by brief window openings - shutdown is unnecessary and counterproductive.

**Impact:** This intuition fundamentally changes the architecture from "all rooms respond to windows" to "equipment-specific response logic."

#### 🟢 Green Hat - Creativity & Alternatives

**Ideas Generated:**

20. **Mode-Aware Shutdown**: Room component has configurable `shutdown_modes` parameter
21. **Fancoil rooms**: Set `shutdown_modes: [cooling]` or `[heating, cooling]` based on need
22. **Radiant rooms**: Set `shutdown_modes: []` to disable window detection
23. **Flexibility**: Each room independently configures which modes trigger window shutdown

**Insights:** Declarative configuration makes equipment-specific behavior self-documenting and maintainable.

#### 🔵 Blue Hat - Process & Organization

**Ideas Generated:**

24. **Separate component**: `components/room_window_detection.yaml` for opt-in window detection
25. **Architecture**: Rooms include this component only if they need window response
26. **Keeps room_sensors.yaml clean**: Temperature/humidity logic stays separate from window logic

**Insights:** Separation of concerns prevents room_sensors.yaml from becoming bloated and maintains Epic 4 modularity.

---

### First Principles Thinking - 10 minutes

**Description:** Strip away assumptions to identify the irreducible core problem, then rebuild the solution from fundamentals.

**Ideas Generated:**

27. **Fundamental goal**: Stop fighting a losing battle (system efficiency) + Save money (economics)
28. **State machine is worth the complexity** - Provides debugging visibility, consistent with Epic 5 pattern, helps users understand system behavior

**Core Problem (Irreducible):**
- Stop wasting energy conditioning air that escapes through windows
- Save money on heating/cooling costs

**Minimum Solution:**
- Detect window open (from HA) → Stop fancoils → Resume when closed

**Essential Real-World Refinements:**
- ✅ 3-minute timeout (allows brief ventilation)
- ✅ 3-minute recovery (prevents oscillation)
- ✅ Mode-specific shutdown (only affects equipment that wastes energy)
- ✅ Notification (user awareness)
- ✅ Graceful degradation (sensor failure handling)
- ✅ State machine (debugging & visibility)

**Insights Discovered:**
- Every refinement in the design serves a real-world need
- State machine complexity is justified by debugging value and pattern consistency
- Equipment-aware logic (fancoils vs radiant) is essential, not optional

**Notable Connections:**
- Core problem maps to two Epic 5 principles: reliability (stop fighting losing battle) and efficiency (save money)
- All "essential refinements" align with existing epic patterns (timeouts, state machines, graceful degradation)

---

## Idea Categorization

### Immediate Opportunities
*Ideas ready to implement now*

1. **Create `components/room_window_detection.yaml`**
   - Description: Reusable component for window-triggered climate shutdown
   - Why immediate: Clean architecture, reuses Epic 5 patterns, opt-in design
   - Resources needed: Component YAML file, integration with room state machine

2. **Implement 3-minute timeout/recovery with state machine**
   - Description: Normal → Window Open (180s timeout) → Window Recovering (180s stability) → Normal
   - Why immediate: Proven timing from Epic 5, symmetrical design, no unknowns
   - Resources needed: State machine logic, delay timers, diagnostic text sensor updates

3. **Add configurable `window_shutdown_modes` parameter**
   - Description: Per-room list of modes that trigger shutdown (e.g., `[cooling]`, `[]`)
   - Why immediate: Declarative, self-documenting, enables fancoil-only response
   - Resources needed: Component vars, conditional logic based on current climate mode

### Future Innovations
*Ideas requiring development/research*

1. **HA notification integration**
   - Description: Notify user when window-triggered shutdown occurs
   - Development needed: Define notification entity/event, test HA integration
   - Timeline estimate: Story 1.2 or 1.3 (after core logic working)

2. **Per-room timeout customization**
   - Description: Allow rooms to override default 3-minute timeout
   - Development needed: Add optional var, ensure reasonable bounds (30s-600s)
   - Timeline estimate: Post-Epic 7 enhancement if needed

3. **Energy savings tracking**
   - Description: Log time spent in "Window Open" state for energy reporting
   - Development needed: Counter sensor, integration with HA energy dashboard
   - Timeline estimate: Separate epic or HA-side automation

### Moonshots
*Ambitious, transformative concepts*

1. **Multi-room window coordination**
   - Description: System detects "whole-floor ventilation" (multiple windows open) and coordinates response at building level
   - Transformative potential: Smart building behavior, optimal ventilation strategies
   - Challenges to overcome: Cross-board communication, complexity vs. benefit analysis

2. **Outdoor temperature integration for "free" heating/cooling**
   - Description: If outdoor temp favorable, keep windows open and disable climate control intelligently
   - Transformative potential: Maximum energy efficiency through natural ventilation
   - Challenges to overcome: Weather data integration, user experience complexity, mode detection logic

### Insights & Learnings

- **Equipment matters more than location**: The breakthrough insight was that fancoils (air handling) require different window response than radiant systems (thermal mass). Location/room is less relevant than equipment type.

- **Graceful degradation is non-negotiable**: Every Epic (5, 6, 7) reinforces that sensor failures must be handled gracefully. "Ignore unavailable sensor" is the right pattern.

- **Timeouts prevent false positives**: 3-minute grace period serves dual purpose: allows brief ventilation AND prevents nuisance shutdowns from sensor glitches or quick door openings.

- **State machines provide observability**: While slightly more complex, state machines make debugging infinitely easier and help users understand system behavior.

- **Opt-in is better than opt-out**: Separate component that rooms include (vs. always-on feature with disable flag) makes the architecture cleaner and intent explicit.

---

## Action Planning

### Top 3 Priority Ideas

#### #1 Priority: Create room_window_detection.yaml component

**Rationale:** Foundation for entire epic, reuses proven patterns, clean architecture

**Next steps:**
1. Create `components/room_window_detection.yaml` with required vars:
   - `zone_slug` (for entity IDs)
   - `ha_window_sensor_id` (HA binary sensor entity)
   - `window_shutdown_modes` (list: e.g., `[cooling]` or `[]`)
2. Add optional vars:
   - `window_timeout: 180` (default 3 minutes)
   - `recovery_timeout: 180` (default 3 minutes)
3. Implement state machine: Normal → Window Open → Window Recovering → Normal
4. Add diagnostic text sensor showing current state
5. Integrate with PID emergency shutdown logic (force PID OFF in Window Open state)

**Resources needed:** 
- Epic 5 emergency_shutdown.yaml as reference
- room_emergency_shutdown.yaml pattern
- Understanding of delay/timer logic in ESPHome

**Timeline:** Story 1.1 - Foundation (1-2 days development)

---

#### #2 Priority: Prototype with one fancoil room (soggiorno)

**Rationale:** Validate design with real hardware before rollout, catch integration issues early

**Next steps:**
1. Update `components/rooms/ground_floor/soggiorno.yaml` to include window detection:
   ```yaml
   packages:
     window_detection: !include
       file: ../../room_window_detection.yaml
       vars:
         zone_slug: soggiorno
         ha_window_sensor_id: binary_sensor.soggiorno_window
         window_shutdown_modes: [cooling, heating]
   ```
2. Deploy to `distribuzione-piano-terra` device
3. Test scenarios:
   - Window open < 3 min → no shutdown
   - Window open > 3 min → PID stops, state = "Window Open"
   - Window closes → "Window Recovering" for 3 min → "Normal"
   - Sensor unavailable → ignored, system continues
4. Validate notification integration with HA

**Resources needed:**
- Test window sensor in HA (or mock for testing)
- Access to distribuzione-piano-terra device for deployment
- Monitoring logs during test

**Timeline:** Story 1.2 - Prototype & Validation (2-3 days including testing)

---

#### #3 Priority: Document pattern and roll out to remaining fancoil rooms

**Rationale:** Ensure maintainability, enable future room additions, complete system coverage

**Next steps:**
1. Create `docs/epic-7-window-detection-guide.md`:
   - Component usage examples
   - When to use window detection (fancoils yes, radiant no)
   - Configuration parameters
   - Troubleshooting common issues
2. Update remaining fancoil rooms:
   - Ground floor: cucina, bagno, anticamera (if applicable)
   - Second floor: fancoil room
3. Update `.github/copilot-instructions.md`:
   - Add window detection patterns
   - Document shutdown_modes convention
4. Create testing checklist for window detection validation

**Resources needed:**
- Documentation time
- Deployment access to all fancoil room devices
- Validation testing per room

**Timeline:** Story 1.3 - Rollout & Documentation (2-3 days)

---

## Reflection & Follow-up

### What Worked Well
- **SCAMPER provided systematic coverage** - Ensured we explored all enhancement angles
- **Red Hat intuition was breakthrough moment** - "Fancoils only" insight fundamentally improved design
- **First Principles validated design** - Confirmed we're not over-engineering
- **Building on Epic 5 patterns** - Consistency with proven architecture reduced decision paralysis

### Areas for Further Exploration
- **Notification mechanism details**: How/when to notify (HA automation vs. ESPHome event?)
- **Multiple windows per room**: Should component support list of window sensors or just one?
- **MEV coordination**: Deferred to out-of-scope, but could be valuable in future epic
- **Testing strategy without real sensors**: Mock sensor setup in HA for development/testing

### Recommended Follow-up Techniques
- **Morphological Analysis**: If notification design becomes complex, systematically explore notification × timing × content matrix
- **Assumption Reversal**: Before implementation, challenge "window must come from HA" assumption - any value in ESPHome-native window detection?
- **Five Whys**: If testing reveals unexpected behavior, use Five Whys to debug root causes

### Questions That Emerged
- Should window detection be mandatory for new fancoil rooms, or always opt-in?
- What's the right balance between notification frequency and alert fatigue?
- Should system track window-open energy waste for reporting, or keep it simple?
- How to handle rooms with multiple windows (any open = shutdown, or majority vote)?

### Next Session Planning
- **Suggested topics**: 
  - Epic 8: Advanced MEV coordination with window state
  - Notification architecture patterns across all epics
  - Energy monitoring and reporting framework
- **Recommended timeframe**: After Epic 7 implementation complete (2-3 weeks)
- **Preparation needed**: Review Epic 7 implementation learnings, gather user feedback on window detection behavior

---

*Session facilitated using the BMAD-METHOD™ brainstorming framework*
