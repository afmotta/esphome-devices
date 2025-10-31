# Project Brief: Epic 7 - Window Detection & Climate Response

**Project:** ESPHome Multi-Floor Climate Control System  
**Epic:** 7 - Window Detection & Climate Response  
**Date:** October 30, 2025  
**Status:** Planning  
**Owner:** Alberto (System Owner)

---

## Executive Summary

**Epic 7: Window Detection & Climate Response** extends the ESPHome multi-floor climate control system with intelligent window-aware climate shutdown to prevent energy waste. When a window opens, the system will automatically pause fancoil-based climate control (after a configurable 3-minute grace period) to avoid conditioning outdoor air, while radiant floor systems continue operating normally due to their thermal mass characteristics. This enhancement prioritizes energy savings while maintaining user comfort through notification alerts and graceful degradation patterns established in Epic 5.

**Primary problem:** Climate control systems waste significant energy heating or cooling outdoor air when windows are open, with fancoil units being particularly inefficient in this scenario.

**Target users:** System owner (Alberto) managing a three-floor residential HVAC system with mixed equipment types (fancoils + radiant floor heating/cooling).

**Key value proposition:** Equipment-aware energy savings through automated climate response to window state, reusing proven Epic 5 emergency shutdown patterns for reliability and consistency.

---

## Problem Statement

### Current State

The ESPHome multi-floor climate control system operates continuously regardless of window state, resulting in significant energy waste when windows are open. Fancoil units, which actively blow conditioned air, are particularly inefficient in this scenario as they attempt to heat or cool outdoor air that immediately escapes through open windows. While radiant floor systems are less affected due to their thermal mass, fancoil-based climate control represents a substantial energy expenditure fighting an unwinnable battle.

### Pain Points

- **Energy Waste:** Climate control systems condition air that immediately escapes, with fancoils at maximum inefficiency
- **Equipment Stress:** PID controllers continuously adjust outputs attempting to reach setpoints that are impossible to achieve with open windows
- **Lack of Intelligence:** System has no awareness of window state, treating open-window scenarios identically to normal operation
- **User Frustration:** No feedback mechanism alerts users that climate control is operating inefficiently

### Impact

Energy costs accumulate unnecessarily during window-open periods, particularly problematic during peak heating (winter) and cooling (summer) seasons. The current system lacks the intelligence to distinguish between equipment types, making a one-size-fits-all solution suboptimal.

### Why Existing Solutions Fall Short

- **Manual intervention only:** Users must remember to manually disable climate control before opening windows
- **No equipment differentiation:** Generic solutions don't account for the different thermal characteristics of fancoils vs. radiant systems
- **Missing from current epics:** While Epic 5 handles sensor failures gracefully, it doesn't address the fundamentally different problem of intentional environmental changes (open windows)

### Urgency

With six rooms (4 ground floor + 2 first floor) equipped with fancoils and window sensors available through Home Assistant, the infrastructure exists to solve this problem. The proven Epic 5 emergency shutdown pattern provides a reliable architectural foundation, making this enhancement both timely and low-risk.

---

## Proposed Solution

### Core Concept

Implement equipment-aware window detection through a reusable `room_window_detection.yaml` component that integrates window state from Home Assistant with ESPHome's proven Epic 5 emergency shutdown pattern. The system will intelligently pause fancoil-based climate control when windows remain open beyond a configurable grace period, while allowing radiant floor systems to continue operating due to their fundamentally different thermal characteristics.

### Key Architecture

- **Opt-in Component Design:** Rooms explicitly include `room_window_detection.yaml` only when appropriate for their equipment type
- **State Machine Pattern:** Reuses Epic 5's proven Normal → Emergency → Recovering state flow, adapted for window detection:
  - **Normal:** Window closed or open < timeout, climate control active
  - **Window Open:** Window open > 3 minutes, PID forced OFF
  - **Window Recovering:** Window closed, 3-minute stability period before resuming
- **Mode-Aware Shutdown:** Configurable `window_shutdown_modes` parameter allows per-room control (e.g., fancoils: `[heating, cooling]`, radiant: `[]`)
- **Graceful Degradation:** If window sensors become unavailable, the system ignores window detection and relies on temperature sensors (fail-safe approach)

### Key Differentiators

1. **Equipment Intelligence:** Unlike generic window detection systems, this solution distinguishes between equipment types that benefit from shutdown (fancoils) vs. those that don't (radiant systems)
2. **User-Centric Timing:** 3-minute grace period prevents nuisance shutdowns during brief ventilation while still capturing energy-wasting scenarios
3. **Architectural Consistency:** Extends the production-validated Epic 5 emergency shutdown pattern rather than creating a parallel system
4. **Declarative Configuration:** Equipment-specific behavior is self-documenting through explicit `shutdown_modes` parameters

### Why This Solution Succeeds

- **Low Risk:** Builds on proven patterns (Epic 5 state machine, Epic 4 room components, Epic 5 HA sensor integration)
- **Incremental Deployment:** Prototype with one room, validate, then roll out—no big-bang changes
- **Maintainable:** Separate component keeps concerns isolated and prevents bloat in existing room_sensors.yaml
- **Observable:** State machine provides clear diagnostic visibility ("Window Open" state) for debugging and user awareness

### High-Level Vision

A climate control system that intelligently adapts to real-world conditions, saving energy without sacrificing comfort or reliability. Users receive notifications when windows trigger shutdowns, maintaining awareness while the system handles the tedious monitoring automatically.

---

## Target Users

### Primary User Segment: Residential System Owner

**Profile:**
- Single-family residential HVAC system owner
- Technical proficiency: Advanced (manages ESPHome + Home Assistant)
- Existing investment in home automation infrastructure
- Environmental consciousness and energy efficiency focus

**Current Behaviors:**
- Manually monitors climate system performance
- Opens windows for ventilation without disabling climate control
- Reviews energy usage but lacks granular per-room insights
- Iteratively improves automation based on seasonal patterns

**Specific Needs:**
- Automatic climate response to window state without manual intervention
- System that distinguishes between equipment types (fancoils vs. radiant)
- Reliable operation even if window sensors fail
- Clear visibility into system state and shutdown reasons

**Goals:**
- Reduce energy waste from conditioning outdoor air
- Maintain comfort while allowing natural ventilation
- Minimize manual intervention in climate control
- Ensure system reliability matches existing Epic 5 standards

---

## Goals & Success Metrics

### Business Objectives

- **Energy Efficiency:** Eliminate wasted energy from heating/cooling outdoor air during window-open periods
- **System Intelligence:** Demonstrate equipment-aware automation that respects physical realities (thermal mass differences)
- **Architectural Excellence:** Maintain Epic 5/6 quality standards (graceful degradation, state machine observability)

### User Success Metrics

- **Reduced Manual Intervention:** User never needs to manually disable climate control before opening windows
- **Comfort Maintenance:** Room temperatures recover to setpoint within acceptable time after window closes
- **System Awareness:** User receives timely notifications when window-triggered shutdown occurs
- **Reliability:** System continues core climate control even if window sensors fail

### Key Performance Indicators (KPIs)

- **Window Detection Accuracy:** 100% of window open/close events detected within 10 seconds (HA sensor responsiveness)
- **False Shutdown Rate:** <1% (3-minute grace period prevents nuisance shutdowns from brief openings)
- **Recovery Time:** Climate control resumes within 3 minutes of window closing (matching Epic 5 recovery period)
- **Graceful Degradation:** 100% of sensor failures handled without manual intervention
- **Deployment Success:** Component deployed to all fancoil rooms within 1 week of validation

---

## MVP Scope

### Core Features (Must Have)

- **`room_window_detection.yaml` Component:** Reusable component with required vars (`zone_slug`, `ha_window_sensor_id`, `window_shutdown_modes`)
- **State Machine Implementation:** Normal → Window Open (180s timeout) → Window Recovering (180s stability) → Normal
- **PID Integration:** Force PID OFF when in "Window Open" state, resume when returning to "Normal"
- **Diagnostic Text Sensor:** Expose current state ("Normal", "Window Open", "Window Recovering") to Home Assistant
- **Graceful Degradation:** Ignore window detection if HA sensor unavailable (continue temperature-based control)
- **Mode-Aware Shutdown:** Configurable `shutdown_modes` parameter enables per-room equipment-specific behavior
- **Prototype Validation:** Deploy to one fancoil room (soggiorno), test all scenarios before rollout
- **Documentation:** Component usage guide, when to use window detection, troubleshooting

### Out of Scope for MVP

- **HA Notification Integration** (deferred to Story 1.2 or post-MVP)
- **Per-Room Timeout Customization** (use global 3-minute default)
- **Energy Savings Tracking** (counter sensor, energy dashboard integration)
- **MEV Coordination** (window state doesn't influence mechanical ventilation)
- **Multi-Room Window Coordination** (building-level ventilation detection)
- **Outdoor Temperature Integration** ("free" heating/cooling through natural ventilation)
- **Multiple Windows Per Room** (assume single window sensor per room)

### MVP Success Criteria

- **Functional Completeness:** All 6 fancoil rooms successfully include window detection component
- **State Machine Validation:** All state transitions occur correctly within documented timing (180s timeout/recovery)
- **Equipment Differentiation:** Fancoil rooms shutdown with windows open, radiant rooms ignore window state
- **Reliability:** No climate control failures or false shutdowns during 7-day burn-in period
- **Documentation Quality:** Developer can add window detection to new room using only provided documentation

---

## Post-MVP Vision

### Phase 2 Features

- **HA Notification Integration:** Push notifications or persistent notifications when window-triggered shutdown occurs
- **Per-Room Timeout Customization:** Allow rooms to override default 3-minute timeout via optional var (30s-600s range)
- **Multiple Window Support:** Component accepts list of window sensors (any open = shutdown)
- **Enhanced Diagnostics:** Track time spent in "Window Open" state, expose as counter sensor

### Long-Term Vision

- **Energy Savings Dashboard:** Integration with HA energy dashboard showing per-room window-related energy savings
- **MEV Coordination (Epic 8):** Window open in room → boost MEV extraction for that zone
- **Intelligent Ventilation:** Outdoor temperature integration for "free" heating/cooling through natural ventilation
- **Learning Timeout:** ML-based per-room timeout optimization based on user patterns

### Expansion Opportunities

- **Multi-Building Pattern:** Adapt component for commercial installations with many rooms
- **Zone-Level Coordination:** Detect whole-floor ventilation patterns (multiple windows open) for building-level response
- **Integration with Other Epics:** Window state as input to future automation patterns (humidity control, air quality, etc.)

---

## Technical Considerations

### Platform Requirements

- **Target Platform:** ESPHome (existing KC868-A6, KC868-A16 boards)
- **HA Integration:** Binary sensors for window state (existing infrastructure)
- **Firmware Compatibility:** ESPHome ≥2023.x with native delay/timer support
- **Performance:** State machine transitions within 500ms (matching Epic 5 responsiveness)

### Technology Preferences

- **Component Architecture:** YAML-based ESPHome package composition (Epic 4 pattern)
- **State Management:** ESPHome script + delay actions for state machine implementation
- **Sensor Integration:** HA binary sensor platform (existing Epic 5 pattern)
- **Diagnostics:** Text sensor for state, binary sensor for window status passthrough

### Architecture Considerations

- **Repository Structure:** New file `components/room_window_detection.yaml`, room files include as package
- **Integration Pattern:** Opt-in component inclusion (rooms explicitly add window detection)
- **State Coordination:** Window state machine coordinates with Epic 5 sensor emergency state machine
- **Fail-Safe Design:** Window sensor unavailable = ignore window detection (system continues normally)

### Security/Compliance

- **No New Attack Surface:** Uses existing HA binary sensor integration (no new network exposure)
- **Privacy:** No data logging or external transmission (all local processing)
- **Reliability:** Graceful degradation ensures climate control continues even with window sensor failures

---

## Constraints & Assumptions

### Constraints

- **Budget:** No additional hardware required (window sensors already in HA)
- **Timeline:** Target 1 week from prototype to full rollout (low complexity, proven patterns)
- **Resources:** Single developer (James) with ESPHome expertise
- **Technical:** Must reuse Epic 5 patterns (no custom C++ components, ESPHome native only)

### Key Assumptions

- Window sensors in Home Assistant are reliable (≥95% uptime)
- 3-minute timeout is appropriate for all fancoil rooms (no per-room customization needed initially)
- Users prefer automatic shutdown vs. manual intervention (validated through brainstorming)
- Fancoil rooms benefit from window detection, radiant rooms do not (equipment-aware logic validated)
- Single window sensor per room is sufficient (multi-window support deferred)
- Notifications can be added post-MVP without architectural changes
- Epic 5 emergency shutdown pattern is extensible to window detection without conflicts

---

## Risks & Open Questions

### Key Risks

- **Risk: Window sensor unreliability** → Impact: False shutdowns or missed detections
  - **Mitigation:** 3-minute timeout prevents brief sensor glitches from triggering shutdown; graceful degradation ignores persistently unavailable sensors
  
- **Risk: User confusion from shutdown** → Impact: User doesn't understand why climate stopped
  - **Mitigation:** Diagnostic text sensor shows "Window Open" state; post-MVP notifications will enhance awareness
  
- **Risk: State machine conflicts** → Impact: Window state and sensor emergency state interact unexpectedly
  - **Mitigation:** Design window detection to integrate with Epic 5 logic (additive, not conflicting)
  
- **Risk: Incorrect equipment classification** → Impact: Radiant room shuts down unnecessarily or fancoil room doesn't shut down
  - **Mitigation:** Explicit per-room `shutdown_modes` configuration makes intent clear and self-documenting

### Open Questions

- Should window detection be mandatory for new fancoil rooms, or always opt-in? **Decision: Always opt-in for flexibility**
- What's the right balance between notification frequency and alert fatigue? **Defer to post-MVP iteration**
- Should system track window-open energy waste for reporting, or keep it simple? **Keep simple for MVP, track in Phase 2**
- How to handle rooms with multiple windows (any open = shutdown, or majority vote)? **Single window for MVP, any-open logic for Phase 2**
- Does notification need to differentiate between "window just opened" vs. "shutdown triggered after 3 min"? **Defer to notification design (post-MVP)**

### Areas Needing Further Research

- Optimal notification mechanism (HA automation vs. ESPHome event vs. persistent notification)
- Real-world window open duration patterns (validate 3-minute timeout appropriateness)
- State machine interaction testing (window + sensor emergency simultaneously)

---

## Appendices

### A. Research Summary

**Source:** Epic 7 Brainstorming Session (October 30, 2025)

**Key Findings:**
- **Equipment-Aware Logic:** Breakthrough insight that fancoils (air handling) require different response than radiant systems (thermal mass)
- **Timeout Validation:** 3-minute timeout serves dual purpose: allows brief ventilation AND prevents false positives from sensor glitches
- **Architectural Consistency:** Epic 5 emergency shutdown pattern maps perfectly to window detection use case
- **User-Centric Design:** Grace period more important than instant shutdown for user experience

**Brainstorming Techniques Used:**
1. SCAMPER Method - Systematic enhancement exploration
2. Six Thinking Hats - Multi-perspective evaluation  
3. First Principles Thinking - Core problem validation

**Total Ideas Generated:** 28 key ideas and design decisions

**See:** `docs/epic-7-brainstorming-session.md` for complete session results

### B. Stakeholder Input

**System Owner (Alberto):**
- Primary goal: Energy savings through efficient climate control
- Preference for reliable, proven patterns over novel approaches
- Comfort with opt-in architecture (explicit room configuration)
- Validated equipment-aware logic (fancoils only) through intuitive reasoning

### C. References

**Related Epics:**
- Epic 4: Room-Based Component Architecture - Provides modular room component pattern
- Epic 5: HA-Only Sensors & Emergency Shutdown - Provides state machine and graceful degradation patterns
- Epic 6: MEV Integration - Establishes pattern for mechanical system components

**Key Files:**
- `components/room_sensors.yaml` - Temperature/humidity sensor integration (v5)
- `components/room_emergency_shutdown.yaml` - Emergency shutdown pattern for sensor failures
- `components/rooms/ground_floor/*.yaml` - Example room implementations
- `.github/copilot-instructions.md` - Coding standards and patterns

**Documentation:**
- `docs/epic-5-ha-only-sensors.md` - HA sensor integration patterns
- `docs/epic-5-completion-report.md` - State machine implementation details
- `docs/architecture.md` - System architecture overview

---

## Next Steps

### Immediate Actions

1. **Create `components/room_window_detection.yaml`** (Priority #1)
   - Define required vars: `zone_slug`, `ha_window_sensor_id`, `window_shutdown_modes`
   - Define optional vars: `window_timeout`, `recovery_timeout`
   - Implement state machine: Normal → Window Open → Window Recovering → Normal
   - Integrate with PID emergency shutdown (force OFF in Window Open state)
   - Add diagnostic text sensor exposing current state

2. **Prototype with soggiorno fancoil room** (Priority #2)
   - Update `components/rooms/ground_floor/soggiorno.yaml` to include window detection
   - Deploy to `distribuzione-piano-terra` device
   - Test all scenarios: timeout, recovery, sensor unavailable
   - Validate state machine transitions and timing

3. **Document and roll out to remaining fancoil rooms** (Priority #3)
   - Create `docs/epic-7-window-detection-guide.md`
   - Update remaining fancoil rooms (cucina, bagno, anticamera, secondo piano)
   - Update `.github/copilot-instructions.md` with window detection patterns
   - Create testing checklist for validation

4. **Create Epic 7 stories in project management** (PM handoff)
   - Story 1.1: Component Foundation
   - Story 1.2: Prototype & Validation
   - Story 1.3: Rollout & Documentation

### PM Handoff

This Project Brief provides the full context for **Epic 7: Window Detection & Climate Response**. The brainstorming session has validated the design approach and identified all key decisions. Please review this brief and create detailed stories for the three-phase implementation plan:

1. **Foundation:** Create reusable window detection component
2. **Validation:** Prototype with one fancoil room, test all scenarios
3. **Rollout:** Document pattern and deploy to all fancoil rooms

The design is ready for implementation with minimal remaining unknowns. Notification integration is explicitly deferred to post-MVP for iterative refinement.

---

*Project Brief created: October 30, 2025*  
*Based on brainstorming session facilitated using the BMAD-METHOD™ framework*
