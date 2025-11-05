# Project Brief: Epic 9 - Occupancy-Based Climate Optimization

**Project:** ESPHome Multi-Floor Climate Control System  
**Epic:** 9 - Occupancy-Based Climate Optimization  
**Date:** November 5, 2025  
**Status:** ❌ **CANCELLED - Home Assistant Implementation**  
**Cancellation Date:** October 2025  
**Owner:** Alberto (System Owner)

---

## ⚠️ CANCELLATION NOTICE

**Decision:** This epic has been cancelled. Occupancy-based climate control will be implemented as **Home Assistant automations** rather than ESPHome components.

**Rationale:**
- **Better Flexibility:** HA automations are easier to modify and test than ESPHome firmware
- **No Deployment Overhead:** Changes don't require firmware compilation and OTA updates to multiple boards
- **Richer Logic:** HA provides better tools for complex occupancy patterns and equipment-aware control
- **Easier Debugging:** HA automation debugging is simpler than ESPHome lambda troubleshooting

**Impact:**
- Epic 8 coordinator architecture remains unchanged (handles emergency + window conditions only)
- ESPHome boards continue to expose climate entities and condition states
- Occupancy detection, analysis, and control decisions occur at the Home Assistant level
- No new ESPHome components required (`room_occupancy_condition.yaml` will not be created)

**Implementation Approach:**
Occupancy control will be handled by HA automations that:
- Monitor occupancy sensors (PIR, mmWave, or composite entities)
- Distinguish equipment types (fancoil vs. radiant)
- Control climate entities directly (force OFF or adjust setpoints)
- Coordinate with window detection and emergency shutdown states

---

## ~~Original Executive Summary~~ (Preserved for Historical Reference)

---

## Executive Summary

**Epic 9: Occupancy-Based Climate Optimization** implements intelligent energy-saving control of climate systems in unoccupied rooms, leveraging the Epic 8 coordinator architecture foundation to add a third condition type (occupancy) with minimal implementation effort. By monitoring Home Assistant occupancy sensors (PIR, mmWave, or composite occupancy entities) and triggering optimized responses after configurable unoccupied periods (default: 2 hours), the system achieves 10-20% energy savings while maintaining comfort in occupied spaces. **For fancoil-equipped rooms, the system forces PID OFF (immediate shutdown).** **For radiant-only rooms, the system applies a reduced setpoint (e.g., 18°C heating, 28°C cooling) to maintain thermal mass while conserving energy.** The new `room_occupancy_condition.yaml` component conforms to the Epic 8 condition interface contract, enabling zero-modification integration with the existing `room_control_coordinator.yaml` across all 15+ rooms.

**Primary problem:** Heating and cooling unoccupied rooms wastes significant energy (estimated 10-20% of total HVAC consumption) and provides no comfort benefit. However, radiant systems have long reaction times (30-60 minutes to change temperature), making complete shutdown impractical. A hybrid approach is needed: fancoils can shut down immediately (fast response), while radiant systems need reduced setpoints to maintain thermal mass.

**Target users:** System owner (Alberto) managing a 15-room residential HVAC system with mixed equipment (fancoils + radiant heating/cooling), existing HA occupancy tracking, seeking automated energy optimization without sacrificing comfort or system performance.

**Key value proposition:** Automated energy savings through intelligent occupancy detection with equipment-aware control: fancoils shut down immediately (fast response), radiant systems reduce setpoints (preserve thermal mass). Zero coordinator modifications, leveraging Epic 8's extensible architecture to deliver 60% faster implementation (3-4 story points vs. 8-10 pre-Epic 8).

---

## Problem Statement

### Current State

The ESPHome multi-floor climate control system successfully maintains comfort across 15+ rooms using PID controllers with two safety-critical shutdown conditions:

- **Epic 5 (Emergency Shutdown):** Detects HA sensor failures, priority 1
- **Epic 7 (Window Detection):** Detects open windows, priority 2
- **Epic 8 (Unified Coordinator):** Aggregates conditions via state+priority interface, coordinates PID control

All rooms maintain setpoints regardless of occupancy status. Home Assistant tracks occupancy via multiple sensor types:
- **PIR motion sensors** - Detect movement in high-traffic areas
- **mmWave presence sensors** - Detect stationary presence (e.g., person sitting)
- **Composite occupancy entities** - Combine multiple sensor inputs for reliable occupancy state

Current behavior: Rooms continue heating/cooling even when unoccupied for hours (e.g., guest bedrooms, office during work hours, bathrooms between usage).

**System Equipment Context:**
The system uses two types of climate equipment with very different characteristics:
- **Fancoils:** Fast response (5-10 minutes), can be turned OFF immediately when unoccupied
- **Radiant heating/cooling:** Slow response (30-60 minutes), complete shutdown leads to:
  - Long recovery time when room becomes occupied (30-60 min to restore comfort)
  - Thermal shock to building structure (rapid temperature changes)
  - Energy inefficiency (high startup energy spike vs. maintaining lower setpoint)

This mixed equipment requires a **hybrid occupancy strategy** rather than one-size-fits-all shutdown.

### Pain Points

- **Energy Waste:** Significant HVAC energy spent maintaining full comfort in empty rooms (estimated 10-20% of total consumption)
- **Manual Intervention Required:** Users must remember to adjust thermostats when leaving rooms for extended periods
- **Forgotten Adjustments:** Users often forget to restore setpoints when returning, leading to discomfort
- **Inconsistent Behavior:** Some users manually adjust thermostats; others don't, creating unpredictable energy usage
- **No Automation:** Existing system has no awareness of room occupancy for energy optimization
- **Equipment Mismatch:** Simple ON/OFF approach doesn't account for radiant system characteristics
  - **Fancoils:** Can handle ON/OFF cycling without issues
  - **Radiant:** Complete shutdown causes long recovery times (30-60 min), uncomfortable when room becomes occupied
  - **User Impact:** "Room is freezing when I enter" complaints if radiant systems fully shut down

### Impact

- **Financial:** Estimated €200-400/year in unnecessary heating/cooling costs for unoccupied spaces
- **Environmental:** Wasted energy contributes to unnecessary CO2 emissions
- **User Experience:** No intelligent automation reduces perceived "smart home" value
- **System Potential:** Epic 8 coordinator architecture designed for this use case but not yet utilized

### Why Existing Solutions Fall Short

- **Manual thermostat adjustments:** Require user action, often forgotten, inconvenient
- **HA automations controlling setpoints:** Can conflict with PID controllers, don't integrate with emergency/window conditions
- **Simple timer-based shutdown:** Doesn't account for actual occupancy, can shut down occupied rooms
- **Per-room HA automation:** Duplicates logic across 15+ rooms, hard to maintain

### Urgency

Epic 8 completed successfully (November 4, 2025) with coordinator pattern proven across 15+ rooms. Occupancy detection is the natural next step, identified during Epic 8 planning as the primary use case for extensibility. Winter heating season underway makes energy savings immediately valuable. Implementation effort reduced 60% by Epic 8 foundation.

---

## Proposed Solution

### Core Concept

Implement an **equipment-aware occupancy condition** using the Epic 8 coordinator pattern that monitors Home Assistant occupancy sensors and triggers optimized responses based on room equipment type:

**For Fancoil-Equipped Rooms (Fast Response):**
- Trigger: Room unoccupied for >timeout (default: 2 hours)
- Action: Force PID OFF (complete shutdown)
- Recovery: Immediate resume when occupied (5-10 min to comfort)
- Rationale: Fancoils respond quickly, no thermal mass concerns

**For Radiant-Only Rooms (Slow Response):**
- Trigger: Room unoccupied for >timeout (default: 2 hours)
- Action: Apply reduced setpoint (e.g., 18°C heating, 28°C cooling)
- Recovery: Immediate return to normal setpoint when occupied (15-30 min to comfort)
- Rationale: Maintains thermal mass, prevents long recovery times

The new condition operates alongside emergency (priority 1), window (priority 2), and occupancy (priority 3) with automatic coordinator integration.

**Conditions (Detection Layer):**
- `room_emergency_condition.yaml` (Epic 5/8) - Sensor failures, priority 1
- `room_window_condition.yaml` (Epic 7/8) - Open windows, priority 2  
- **`room_occupancy_condition.yaml` (Epic 9, NEW)** - Unoccupied rooms, priority 3
- `room_emergency_condition_stub.yaml` / `room_window_condition_stub.yaml` - Stubs for rooms without features

**Coordinator (Control Layer):**
- `room_control_coordinator.yaml` (Epic 8) - **NO MODIFICATIONS REQUIRED**
- Automatically reads occupancy_state and occupancy_priority from new condition
- Applies priority hierarchy: Emergency > Window > Occupancy
- Controls PID based on highest-priority active condition
- **NEW:** Coordinator enhanced to support setpoint offset recommendations (for radiant rooms)

### Key Architecture Decisions

**1. Equipment-Aware Response Strategy (NEW - Critical Design Decision)**
- **Fancoil Rooms:** Force PID OFF when unoccupied (complete shutdown)
  - **Rationale:** Fast response (5-10 min), no thermal mass, immediate recovery acceptable
  - **Example Rooms:** Bedrooms with fancoils, bathrooms with fancoils
  - **Energy Savings:** 15-25% (full shutdown)
- **Radiant Rooms:** Apply reduced setpoint when unoccupied (partial reduction)
  - **Rationale:** Slow response (30-60 min), preserve thermal mass, prevent user discomfort
  - **Heating Setpoint:** 18°C (vs. 21°C normal) - 3°C reduction
  - **Cooling Setpoint:** 28°C (vs. 25°C normal) - 3°C reduction
  - **Example Rooms:** Living rooms, offices with radiant-only
  - **Energy Savings:** 8-12% (setpoint reduction, less than shutdown but maintains comfort)
- **Implementation:** Occupancy condition component includes `equipment_type` var (fancoil/radiant)
- **Benefit:** Balanced energy savings + user comfort across mixed equipment types

**2. Occupancy Source:** Home Assistant occupancy sensors (not ESPHome hardware)
- **Rationale:** HA already has sophisticated occupancy tracking (PIR + mmWave fusion, timeout logic, room-level aggregation)
- **Benefit:** Reuse existing sensor infrastructure, no new hardware required
- **Implementation:** `homeassistant` platform binary_sensor or sensor entities

**2. Occupancy Source:** Home Assistant occupancy sensors (not ESPHome hardware)
- **Rationale:** HA already has sophisticated occupancy tracking (PIR + mmWave fusion, timeout logic, room-level aggregation)
- **Benefit:** Reuse existing sensor infrastructure, no new hardware required
- **Implementation:** `homeassistant` platform binary_sensor or sensor entities

**3. Unoccupied Timeout:** Configurable per room, default 2 hours
- **Rationale:** Prevents false shutdowns from brief absences (bathroom visits, fetching items)
- **Benefit:** Balances energy savings with user comfort
- **Examples:** Bedroom 30 min, Guest room 4 hours, Bathroom 15 min

**4. Recovery Behavior:** Immediate (0s recovery timeout)
- **Rationale:** When room becomes occupied, restore normal control immediately for comfort
- **Fancoil Rooms:** PID resumes normal operation (OFF → heating/cooling)
- **Radiant Rooms:** Setpoint restored to normal (18°C → 21°C), PID adjusts gradually
- **Difference from Emergency/Window:** Those need stability period; occupancy doesn't

**5. Priority 3 (Lowest):** Below emergency and window
- **Rationale:** Safety-critical conditions (emergency, window) override energy savings
- **Benefit:** If window opens while room unoccupied, window condition active (priority 2 < 3)
- **Example:** Unoccupied room + sensor fails → Emergency active, occupancy ignored

**6. Mode-Awareness:** Active in ALL climate modes (heat, cool, off)
- **Rationale:** Unoccupied rooms don't need conditioning regardless of season
- **Benefit:** Year-round energy savings
- **Difference from Window:** Window only triggers in cooling/heating modes

**6. Stub Pattern:** Rooms without occupancy sensors use stub
- **Rationale:** Coordinator expects occupancy globals from all rooms (always-present pattern from Epic 8)
- **Benefit:** Gradual rollout - add occupancy sensors room-by-room over time
- **Implementation:** `room_occupancy_condition_stub.yaml` exposes state=0, priority=99

### Key Differentiators

1. **Equipment-Aware Control:** Fancoils shut down (fast), radiant reduces setpoint (preserves thermal mass)
2. **Zero Coordinator Modifications:** Epic 8 interface contract enables plug-and-play condition addition
3. **Reuses Existing Sensors:** Leverages HA occupancy tracking investment, no new hardware
4. **Per-Room Configurability:** Timeout, occupancy sensor entity, equipment type, setpoints per room
5. **Priority Hierarchy Integration:** Works correctly when multiple conditions active simultaneously
6. **Immediate Resume:** No recovery timeout for comfort when room becomes occupied
7. **Proven Pattern:** Follows Epic 5/7/8 state machine architecture with 99.99% production uptime

### High-Level Vision

A climate control system that intelligently conserves energy by optimizing control in unoccupied rooms based on equipment characteristics: fancoils shut down completely (fast recovery), radiant systems reduce setpoints (maintain thermal mass). Climate resumes instantly when occupants return, all without requiring manual thermostat adjustments or complex Home Assistant automations. Occupancy becomes a first-class citizen in the room control logic alongside safety conditions, with equipment-aware optimization preventing user discomfort.

---

## Target Users

### Primary User Segment: Energy-Conscious System Owner

**Profile:**
- Residential system owner with 15+ rooms and existing HA occupancy sensor infrastructure
- Technical proficiency: Advanced (successful Epic 1-8 deployments, comfortable with YAML)
- Energy goals: Reduce HVAC waste without sacrificing comfort
- Already uses HA occupancy tracking for lighting automation

**Current Behaviors:**
- Manually adjusts thermostats in guest rooms when visitors leave
- Sometimes forgets to restore setpoints, leading to discomfort on room re-entry
- Monitors HA energy dashboard showing HVAC consumption
- Desires automated energy optimization but avoids complex HA automation scripts

**Specific Needs:**
- **Automated Shutdown:** Stop conditioning unoccupied rooms without manual intervention
- **Instant Resume:** Climate control resumes immediately when room becomes occupied
- **Per-Room Control:** Different timeout thresholds for different room types (bedroom vs. guest room)
- **Reliability:** No false shutdowns from brief absences (bathroom visits, fetching items)
- **Energy Visibility:** Dashboard showing which rooms shut down due to occupancy

**Goals:**
- Reduce HVAC energy consumption by 10-20% across heating and cooling seasons
- Maintain comfort in occupied spaces (no temperature deviation)
- Deploy occupancy detection to all 15+ rooms within 4-6 weeks
- Enable easy future expansion (add occupancy sensors to new rooms trivially)

---

## Goals & Success Metrics

### Business Objectives

- **Energy Savings:** Reduce HVAC energy consumption by 10-20% through unoccupied room shutdown
- **Implementation Velocity:** Prove Epic 8 extensibility promise (3-4 story points vs. 8-10 pre-Epic 8, 60% reduction)
- **Comfort Preservation:** Maintain temperature accuracy in occupied rooms (±0.5°C from setpoint)
- **User Experience:** Zero manual thermostat adjustments for occupancy-based control

### User Success Metrics

- **Deployment Success:** All 15+ rooms receive occupancy detection capability within 6 weeks
- **Energy Savings Validation:** Measurable reduction in HVAC runtime for previously-unoccupied periods
- **Zero Comfort Complaints:** No reported issues with rooms being too cold/hot when occupied
- **Instant Resume Validation:** Climate control resumes within 10 seconds of room becoming occupied
- **Rollout Flexibility:** Rooms without occupancy sensors continue operating normally with stub component

### Key Performance Indicators (KPIs)

- **Interface Compliance:** 100% compliance with Epic 8 condition interface contract (state+priority globals)
- **Coordinator Stability:** Zero modifications required to `room_control_coordinator.yaml`
- **Implementation Effort:** ≤4 story points (vs. 8-10 for pre-Epic 8 equivalent)
- **Energy Savings:** 10-20% reduction in HVAC runtime for rooms with occupancy detection
- **False Shutdown Rate:** <1% (no shutdowns during actual occupancy due to sensor issues)
- **Resume Responsiveness:** Climate resumes within 10 seconds of occupancy detection
- **Migration Complexity:** Average 15 minutes per room to add occupancy detection
- **Documentation Completeness:** Experienced ESPHome user can add occupancy to new room using guide only

---

## MVP Scope

### Core Features (Must Have)

1. **Occupancy Condition Component**
   - **Description:** New `components/room_occupancy_condition.yaml` conforming to Epic 8 interface
   - **Rationale:** Core Epic 9 deliverable enabling occupancy-based optimization
   - **Features:**
     - Monitors HA binary_sensor or sensor for occupancy state
     - Triggers optimization after configurable unoccupied timeout (default: 2 hours)
     - Exposes `${zone_slug}_occupancy_state` (0=Normal, 1=Active, 2=Recovering)
     - Exposes `${zone_slug}_occupancy_priority` (=3)
     - **Equipment-aware control:** Configurable `equipment_type` var (fancoil/radiant)
     - **Fancoil mode:** Forces PID OFF when Active
     - **Radiant mode:** Applies setpoint offset when Active (e.g., -3°C heating, +3°C cooling)
     - Immediate recovery (0s timeout) when room becomes occupied
     - Diagnostic text_sensor showing "Occupied" / "Unoccupied (Fancoil OFF)" / "Unoccupied (Radiant Reduced)" / "Resuming"
     - Per-room configurable: timeout, equipment_type, setpoint offsets

2. **Occupancy Stub Component**
   - **Description:** New `components/room_occupancy_condition_stub.yaml` for rooms without sensors
   - **Rationale:** Maintain always-present pattern from Epic 8, enable gradual rollout
   - **Features:**
     - Exposes `${zone_slug}_occupancy_state` = 0 (always Normal)
     - Exposes `${zone_slug}_occupancy_priority` = 99 (never active)
     - Minimal resource usage (static globals only)

3. **Single-Room Validation**
   - **Description:** Deploy occupancy detection to two test rooms (one fancoil, one radiant)
   - **Rationale:** Validate both equipment patterns before system-wide rollout
   - **Validation Criteria:**
     - **Fancoil room:** Shuts down PID after 2 hours unoccupied, resumes immediately when occupied
     - **Radiant room:** Reduces setpoint after 2 hours unoccupied, restores immediately when occupied (no full shutdown)
     - Coordinator diagnostic shows appropriate shutdown reason ("Fancoil OFF" vs "Radiant Reduced")
     - Emergency and window conditions still override occupancy (priority hierarchy)
     - No false shutdowns during actual occupancy
     - **Comfort validation:** Radiant room comfortable within 15-20 minutes of occupation (vs. 30-60 min if fully shut down)

4. **Multi-Room Migration Guide**
   - **Description:** Step-by-step guide for adding occupancy detection to remaining rooms
   - **Rationale:** Enable safe production rollout across 15+ rooms with mixed equipment
   - **Content:**
     - How to add occupancy condition package to room YAML
     - Configuration vars (zone_slug, zone_name, ha_occupancy_sensor_id, unoccupied_timeout, **equipment_type**, **setpoint_offsets**)
     - **Equipment type selection:** How to determine fancoil vs. radiant per room
     - Using stub for rooms without occupancy sensors
     - Validation checklist per room (equipment-specific)
     - Troubleshooting guide (sensor entity_id, timeout tuning, comfort issues)

5. **Occupancy Condition Documentation**
   - **Description:** Comprehensive documentation of occupancy condition behavior
   - **Rationale:** Support future maintenance and room additions
   - **Content:**
     - Component usage examples
     - Timeout tuning recommendations per room type
     - HA occupancy sensor requirements and entity_id format
     - State transition diagram
     - Integration with emergency and window conditions

### Out of Scope for Epic 9

- **Predictive Occupancy:** ML-based occupancy prediction deferred to future epic
- **Dynamic Timeout Adjustment:** Learning optimal timeouts per room deferred
- **Occupancy Sensors on ESPHome:** Only HA-managed occupancy sensors supported in MVP
- **~~Partial Shutdown:~~** ~~Reducing setpoints instead of full OFF deferred (Epic 10 energy optimization)~~ **NOW IN SCOPE:** Radiant rooms use setpoint reduction
- **Schedule Integration:** Time-based occupancy expectations (e.g., "office always unoccupied 6pm-8am") deferred
- **Multi-Room Occupancy Patterns:** "If all bedrooms unoccupied, assume away from home" deferred
- **Geofencing Integration:** Combining device location with occupancy deferred (identified in brainstorming, Epic 11+)
- **Per-Room Equipment Detection:** Manual configuration required (component doesn't auto-detect fancoil vs. radiant)

### MVP Success Criteria

**Epic 9 MVP is complete when:**
1. All 15+ rooms have occupancy detection (real sensors or stubs) integrated
2. Zero modifications made to `room_control_coordinator.yaml` (interface contract validated)
3. Single test room demonstrates correct shutdown→resume cycle
4. Energy monitoring shows measurable HVAC runtime reduction in unoccupied rooms
5. Occupancy condition documentation complete with migration guide
6. No comfort complaints from occupied rooms (no false shutdowns)
7. Priority hierarchy validated: Emergency and window conditions override occupancy

---

## Post-MVP Vision

### Phase 2 Features (Epic 10+)

**Energy State × Occupancy Matrix (Epic 10):**
- **Description:** Combine occupancy with energy abundance/scarcity state
- **Behavior:** 
  - Energy Abundance + Unoccupied → Keep running at full setpoint (thermal banking)
  - Energy Scarcity + Unoccupied → Aggressive reduction (Epic 9 behavior: fancoil OFF, radiant further reduced)
  - Energy Abundance + Occupied → Full comfort
  - Energy Scarcity + Occupied → Slightly reduced setpoints
- **Enabled by Epic 9:** Occupancy condition already in place, equipment-aware control proven
- **Note:** Epic 9 already implements setpoint reduction for radiant; Epic 10 adds dynamic adjustment based on energy state

**Dynamic Setpoint Adjustment:**
- **Description:** Adjust setpoint offsets based on energy price, battery state, solar production
- **Example:** High energy cost → radiant setpoint reduction increased (18°C → 16°C heating)
- **Implementation:** Coordinator reads energy state condition alongside occupancy

### Long-term Vision (12-24 months)

**Predictive Occupancy (Epic 12+):**
- **Description:** ML model predicts occupancy patterns, pre-conditions rooms before expected arrival
- **Example:** "Office typically occupied 9am-5pm weekdays" → start conditioning at 8:45am
- **Data Collection:** Epic 9 provides 2-3 months of occupancy history for model training

**Schedule-Aware Occupancy:**
- **Description:** Integrate calendar/schedule data with occupancy detection
- **Example:** "Guest room occupied this weekend (calendar event)" → shorter unoccupied timeout

**Multi-Room Occupancy Correlation:**
- **Description:** Detect whole-house patterns (all bedrooms unoccupied = away from home)
- **Benefit:** More aggressive shutdown when house is empty
- **Implementation:** Coordinator-level multi-room logic or HA automation

### Expansion Opportunities

**Geofencing + Occupancy (Epic 11):**
- **Description:** Combine device location (mobile phones) with room occupancy
- **Example:** "Family is 15 minutes away + house unoccupied" → pre-condition high-traffic rooms
- **Integration:** HA geofencing triggers pre-conditioning, occupancy prevents shutdown

**Adaptive Timeout Learning:**
- **Description:** System learns typical occupancy patterns per room, adjusts timeouts automatically
- **Example:** Bathroom typically unoccupied <10 minutes → reduce timeout to 15 minutes
- **Benefit:** Per-room optimization without manual configuration

**Occupancy-Aware Setpoints:**
- **Description:** Different setpoints for occupied vs. unoccupied (partial reduction)
- **Example:** Bedroom 22°C when occupied, 18°C when unoccupied (not OFF)
- **Benefit:** Faster recovery, reduced energy spikes on resume

---

## Technical Considerations

### Platform Requirements

- **Target Platform:** ESPHome 2024.x (current production version)
- **Hardware:** Existing KC868-A6/A16 boards, no new hardware required
- **HA Version:** Compatible with current Home Assistant installation (2024.x)
- **HA Occupancy Sensors:** Binary_sensor or sensor entities with boolean/0-1 values
- **Performance Requirements:** Occupancy check interval ≤10s, coordinator already polling at 5s

### Technology Preferences

- **Component Structure:** Standard ESPHome YAML with lambda C++ for timeout logic
- **State Storage:** ESPHome globals (in-memory, consistent with Epic 8 pattern)
- **Communication:** HA integration via `homeassistant` platform for occupancy sensors
- **Testing:** Manual validation in test room, phased production rollout (1 room → floor → all rooms)

### Architecture Considerations

- **Repository Structure:**
  - New component: `components/room_occupancy_condition.yaml`
  - New stub: `components/room_occupancy_condition_stub.yaml`
  - Updated: Room device packages include occupancy condition or stub
  - No changes: `components/room_control_coordinator.yaml` (zero modifications)

- **Service Architecture:**
  - Occupancy condition = independent state machine (reads HA sensor, sets globals)
  - Coordinator = aggregator (reads occupancy globals alongside emergency/window)
  - No direct communication between conditions (decoupled via globals)

- **Integration Requirements:**
  - HA occupancy entity IDs (binary_sensor or sensor) per room
  - Room device YAML updated to include occupancy package
  - Coordinator continues polling all condition states at 5s interval

- **Security/Compliance:**
  - Local control works when HA down (graceful degradation - last known occupancy state)
  - No cloud dependencies - existing pattern maintained
  - Secrets management via `locals/secrets.yaml` - existing pattern maintained

---

## Constraints & Assumptions

### Constraints

- **Budget:** $0 (software-only, leverages existing HA occupancy sensors)
- **Timeline:** 4-6 weeks total (1 week implementation, 1 week single-room validation, 2-4 weeks rollout)
- **Resources:** Solo developer (Alberto), part-time effort (evenings/weekends)
- **Technical:**
  - Must conform to Epic 8 condition interface contract (state+priority globals)
  - Cannot modify `room_control_coordinator.yaml` (interface contract validation)
  - Must work with existing HA occupancy sensor infrastructure
  - Must maintain ESPHome YAML composition patterns

### Key Assumptions

- HA occupancy sensors are reliable and responsive (≤10s latency)
- Existing occupancy entity IDs are stable and won't change during rollout
- 2-hour default timeout is appropriate for most rooms (can be tuned per room)
- Immediate recovery (0s timeout) provides best user experience
- Priority 3 (below emergency and window) is correct hierarchy
- Epic 8 coordinator pattern proven across 15+ rooms (validated November 2025)
- Room device packages can be updated via OTA without physical access
- Stub pattern from Epic 8 works for occupancy (always-present globals)
- Users accept PID OFF behavior for unoccupied rooms (vs. setpoint reduction)

---

## Risks & Open Questions

### Key Risks

- **False Shutdowns:** Occupancy sensors fail to detect presence, shutting down occupied rooms
  - **Mitigation:** Conservative default timeout (2 hours), per-room tuning
  - **Mitigation:** User can manually override via HA climate entity

- **Comfort Complaints:** Users perceive rooms as "too cold when I enter"
  - **Mitigation:** Immediate recovery (0s timeout) resumes heating/cooling instantly
  - **Mitigation:** Document expected behavior: room may be slightly cooler initially
  - **Future:** Predictive pre-conditioning based on patterns

- **Sensor Reliability:** HA occupancy sensors have high false-negative rate (miss presence)
  - **Mitigation:** Test with existing sensor infrastructure, identify problematic sensors
  - **Mitigation:** Increase timeout for rooms with unreliable sensors
  - **Mitigation:** Encourage mmWave sensors for stationary presence detection

- **Energy Savings Below Expectations:** Rooms not actually unoccupied long enough for savings
  - **Mitigation:** HA energy monitoring to measure actual savings per room
  - **Mitigation:** Adjust timeouts per room based on data

- **Coordinator Priority Logic Bug:** Occupancy incorrectly overrides emergency/window
  - **Mitigation:** Priority 3 is lowest (emergency=1, window=2), coordinator proven in Epic 8
  - **Mitigation:** Single-room validation tests priority hierarchy

### Open Questions

- **Optimal Default Timeout:** Is 2 hours the right default, or should it be shorter/longer?
  - **Resolution Strategy:** Start with 2 hours, collect data, adjust per room

- **Recovery Behavior:** Should recovery have a stability timeout (like emergency/window), or immediate?
  - **Current Decision:** Immediate (0s) for comfort; no stability period needed
  - **Rationale:** Occupancy re-detection is reliable, unlike sensor recovery

- **Partial Shutdown:** Should MVP support setpoint reduction instead of full OFF?
  - **Current Decision:** Deferred to Epic 10 (energy optimization with setpoint offsets)
  - **Rationale:** Full OFF is simpler for MVP, setpoint offsets require coordinator enhancement

- **Multi-Sensor Fusion:** Should occupancy condition support multiple sensors per room?
  - **Current Decision:** Single HA entity per room (HA does sensor fusion)
  - **Rationale:** Leverage HA's existing multi-sensor logic, don't duplicate in ESPHome

- **Occupancy Sensor Unavailability:** What happens if HA occupancy sensor goes offline?
  - **Resolution Strategy:** Treat as "unknown" → assume occupied (safe default, no shutdown)
  - **Alternative:** Configurable fallback behavior per room

### Areas Needing Further Research

- **Occupancy Sensor Quality Assessment:** Audit all 15+ rooms for sensor reliability before rollout
- **Energy Monitoring Setup:** Ensure HA energy dashboard captures per-room HVAC consumption
- **Timeout Tuning Strategy:** Develop guidelines for timeout selection per room type
- **User Education:** How to communicate occupancy-based shutdown behavior to household members

---

## Appendices

### A. Epic 8 Foundation Summary

**Interface Contract (from `epic-8-condition-interface-spec.md`):**
- State Global: `${zone_slug}_${condition_id}_state` (0=Normal, 1=Active, 2=Recovering)
- Priority Global: `${zone_slug}_${condition_id}_priority` (1=highest, 2=second, etc.)

**Existing Conditions:**
- Emergency: Priority 1 (sensor failure)
- Window: Priority 2 (open window)
- **Occupancy (Epic 9):** Priority 3 (unoccupied room)

**Coordinator Behavior:**
- Polls all condition states every 5 seconds
- Applies priority hierarchy: Lowest priority number wins
- Forces PID OFF when any condition Active or Recovering
- Exposes diagnostic text_sensor: "Shutdown: {Condition} ({State})" or "Normal (All Clear)"

**Key Benefit for Epic 9:**
- Occupancy condition implementation requires ZERO coordinator modifications
- Interface contract enables plug-and-play condition addition
- 60% reduction in implementation effort vs. pre-Epic 8

### B. Occupancy Condition State Transitions

```
┌─────────────┐
│   Normal    │  Room occupied or recently occupied
│  (state=0)  │  PID operates normally
└──────┬──────┘
       │
       │ [Unoccupied for >unoccupied_timeout (default 2h)]
       ▼
┌─────────────┐
│   Active    │  Room unoccupied beyond threshold
│  (state=1)  │  Coordinator forces PID OFF
└──────┬──────┘
       │
       │ [Room becomes occupied]
       ▼
┌─────────────┐
│ Recovering  │  Immediate (0s timeout)
│  (state=2)  │  Coordinator resumes PID
└──────┬──────┘
       │
       │ [Immediate transition]
       ▼
┌─────────────┐
│   Normal    │  PID operating normally
│  (state=0)  │  Room occupied
└─────────────┘
```

**Key Differences from Emergency/Window:**
- **No recovery timeout:** Immediate transition Recovering → Normal (0s vs. 60s)
- **Rationale:** Occupancy detection is reliable; no stability period needed
- **User Experience:** Climate resumes instantly when room becomes occupied

### C. Priority Hierarchy with Occupancy

| Priority | Condition | Trigger                  | Example Scenario                                       |
| -------- | --------- | ------------------------ | ------------------------------------------------------ |
| 1        | Emergency | HA sensor unavailable    | Sensor fails + room unoccupied → **Emergency active**  |
| 2        | Window    | Window open (heat/cool)  | Window opens + room unoccupied → **Window active**     |
| 3        | Occupancy | Room unoccupied >timeout | No higher conditions → **Occupancy active**            |
| 99       | Stub      | Never (stub always 0)    | Room without sensor → **Normal** (coordinator ignores) |

**Coordinator Logic:**
```
active_conditions = []
if emergency_state > 0: active_conditions.add((emergency_priority=1, "Emergency"))
if window_state > 0: active_conditions.add((window_priority=2, "Window"))
if occupancy_state > 0: active_conditions.add((occupancy_priority=3, "Occupancy"))

if active_conditions:
  highest_priority_condition = min(active_conditions, key=priority)
  force_pid_off()
  diagnostic = f"Shutdown: {condition_name} ({state_name})"
else:
  allow_pid_normal_operation()
  diagnostic = "Normal (All Clear)"
```

### D. Per-Room Timeout Recommendations

| Room Type       | Recommended Timeout | Rationale                                     |
| --------------- | ------------------- | --------------------------------------------- |
| Bedroom         | 30-60 minutes       | Typically occupied for long periods when used |
| Guest Room      | 4-8 hours           | Infrequently used, long unoccupied periods    |
| Bathroom        | 10-15 minutes       | Short usage periods, frequent unoccupied      |
| Living Room     | 1-2 hours           | High traffic but extended unoccupied periods  |
| Office          | 2-4 hours           | Occupied during work hours, empty otherwise   |
| Kitchen         | 1-2 hours           | Intermittent use throughout day               |
| Hallway/Laundry | 5-10 minutes        | Brief usage only                              |
| Default         | 2 hours             | Conservative for unknown room usage patterns  |

**Tuning Strategy:**
1. Deploy with 2-hour default across all rooms
2. Monitor HA energy dashboard for 2 weeks
3. Identify rooms with frequent false shutdowns (reduce timeout)
4. Identify rooms with insufficient savings (increase timeout or add occupancy sensor)

### E. References

- **Epic 8 Documentation:**
  - `docs/epic-8-brief.md` - Unified state machine architecture overview
  - `docs/epic-8-condition-interface-spec.md` - Interface contract for conditions
  - `docs/epic-8-coordinator-design.md` - Coordinator state machine algorithm
  - `docs/epic-8-completion-report.md` - Epic 8 delivery validation (November 4, 2025)

- **Existing Components:**
  - `components/room_control_coordinator.yaml` (231 lines) - Coordinator (no changes needed)
  - `components/room_emergency_condition.yaml` (206 lines) - Emergency detection (priority 1)
  - `components/room_window_condition.yaml` (258 lines) - Window detection (priority 2)
  - `components/room_emergency_condition_stub.yaml` (44 lines) - Stub pattern reference
  - `components/room_window_condition_stub.yaml` (44 lines) - Stub pattern reference

- **Brainstorming Session:**
  - `docs/future-features-brainstorming-session.md` - Epic 9 identified as #1 priority
  - Energy × Occupancy interaction matrix explored (deferred to Epic 10)

### F. Equipment Types and Room Classification

**Equipment Type Determination:**
```yaml
equipment_classification:
  fancoil:
    characteristics:
      - Response time: 5-10 minutes
      - Can handle ON/OFF cycling
      - No thermal mass concerns
      - Immediate shutdown appropriate
    occupancy_strategy: Force PID OFF when unoccupied
    typical_rooms:
      - Bedrooms with fancoils
      - Bathrooms
      - Small offices
  
  radiant:
    characteristics:
      - Response time: 30-60 minutes
      - High thermal mass (floor, ceiling, walls)
      - Complete shutdown causes long recovery
      - Thermal shock to structure
    occupancy_strategy: Reduce setpoint when unoccupied
    setpoint_offsets:
      heating: -3°C (21°C → 18°C)
      cooling: +3°C (25°C → 28°C)
    typical_rooms:
      - Living rooms
      - Large spaces with radiant-only
      - Offices with radiant floor/ceiling
  
  mixed:
    note: "Rooms with both fancoil AND radiant"
    recommendation: "Treat as fancoil (faster response dominates)"
    alternative: "Configure as radiant if user prioritizes comfort over savings"
```

**Room-by-Room Equipment Audit (Example):**
```yaml
piano_terra:
  soggiorno:
    equipment: radiant_only
    occupancy_strategy: setpoint_reduction
    heating_offset: -3°C
    cooling_offset: +3°C
  
  cucina:
    equipment: radiant_only
    occupancy_strategy: setpoint_reduction
    heating_offset: -3°C
    cooling_offset: +3°C
  
  camera_matrimoniale:
    equipment: fancoil + radiant
    occupancy_strategy: force_off  # Fancoil dominates
    note: "Fancoil provides fast response, radiant provides base comfort"
  
  bagno:
    equipment: fancoil_only
    occupancy_strategy: force_off
    note: "Fast recovery needed for bathroom comfort"
```

**Energy Savings by Equipment Type:**
```yaml
expected_savings:
  fancoil_rooms:
    strategy: Complete shutdown (PID OFF)
    savings: 15-25%
    rationale: "No conditioning during unoccupied periods"
  
  radiant_rooms:
    strategy: Setpoint reduction (-3°C heating, +3°C cooling)
    savings: 8-12%
    rationale: "Reduced output but maintaining thermal mass"
  
  system_wide:
    average: 10-20%
    note: "Blend of fancoil (higher savings) and radiant (lower but comfortable savings)"
```

---

## Next Steps

### Immediate Actions

1. **Review and validate this brief** - Confirm scope, timeline, and priority hierarchy with system owner
2. **Priority #1: Design occupancy condition component** - Draft `room_occupancy_condition.yaml` structure
3. **Priority #2: Identify test room** - Select room with reliable occupancy sensor for validation
4. **Priority #3: Audit HA occupancy sensors** - Review all 15+ rooms for sensor availability and entity IDs

### Transition to Implementation

Once this brief is approved, proceed to story creation and implementation:
1. **Story 9.1:** Occupancy condition component implementation
2. **Story 9.2:** Occupancy stub component implementation  
3. **Story 9.3:** Single-room validation (test room deployment)
4. **Story 9.4:** Multi-room rollout (remaining 14+ rooms)
5. **Story 9.5:** Documentation, energy monitoring dashboard, Epic 9 completion report

### Pre-Implementation Checklist

- [ ] Epic 9 brief reviewed and approved
- [ ] HA occupancy sensor entity IDs documented for all rooms
- [ ] Test room identified (e.g., Soggiorno with reliable PIR+mmWave sensor)
- [ ] Energy monitoring dashboard configured in HA
- [ ] Epic 8 completion validated (coordinator stable across 15+ rooms)

---

**Brief Status:** Ready for review and story creation

---

*Brief created using BMAD-METHOD™ analyst facilitation*
