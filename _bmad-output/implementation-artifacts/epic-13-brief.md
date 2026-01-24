# Project Brief: Epic 13 - Ground Floor Hybrid Radiant-Fancoil Cooling

**Project:** ESPHome Multi-Floor Climate Control System  
**Epic:** 13 - Ground Floor Hybrid Radiant-Fancoil Cooling  
**Date:** December 26, 2025  
**Status:** Planning  
**Owner:** Alberto (System Owner)

---

## Executive Summary

**Epic 13: Ground Floor Hybrid Radiant-Fancoil Cooling** implements a comfort-first cooling strategy for the ground floor by enabling radiant floor cooling as the primary system, with fancoils providing supplementary capacity when the radiant system cannot meet demand. The radiant floor provides superior thermal comfort (silent, even temperature distribution), while fancoils offer rapid response and dehumidification capability when temperature delta exceeds a configurable threshold.

**Primary value:** Enhanced occupant comfort through radiant floor cooling, with fancoil boost for peak demand periods.

**Target system:** Ground floor zones (Soggiorno, Cucina, Bagno, Anticamera) with dual-system coordination for rooms with both radiant and fancoil capability.

**Key differentiator:** Comfort-first approach — radiant is primary, fancoil is secondary (inverse of typical boost patterns).

---

## Problem Statement

### Current State

The ground floor currently uses:
- **Radiant floor:** Heating only (`heat_only_radiant.yaml` component)
- **Fancoils:** Cooling only (Soggiorno, Cucina, Locale Tecnico)

This results in:
- **Suboptimal cooling comfort:** Fancoils create localized cold air drafts
- **Noise during cooling:** Fancoil fans produce audible noise vs. silent radiant
- **Unused cooling capacity:** Radiant floor infrastructure exists but isn't leveraged for cooling
- **Inconsistent experience:** First floor uses radiant cooling with superior comfort; ground floor doesn't

### Pain Points

1. **Comfort gap:** Cold air from fancoils creates uneven temperature distribution and drafts
2. **Noise:** Fancoil operation is audible, especially noticeable in living areas (Soggiorno)
3. **Underutilized infrastructure:** Ground floor radiant is capable of cooling but not configured for it
4. **Energy efficiency:** Radiant cooling is typically more efficient than forced-air fancoils

### Why Existing Solutions Fall Short

- **Fancoil-only cooling:** Works but sacrifices comfort and creates noise
- **Manual coordination:** Requires user intervention to balance systems
- **First floor pattern:** Uses radiant-only cooling; doesn't address dual-system coordination needed for ground floor

### Urgency

Summer 2026 cooling season approaches. Implementing radiant cooling provides:
- Time for PID tuning before peak demand
- Opportunity to validate dew point protection (Epic 12 dependency)
- Improved comfort for primary living spaces

---

## Proposed Solution

### Core Concept: Comfort-First Hybrid Cooling

**Primary cooling:** Radiant floor provides base cooling capacity with superior comfort
**Secondary cooling:** Fancoils boost when temperature delta exceeds threshold

### Operating Modes

| Mode | Radiant Floor | Fancoils | Trigger Condition |
|------|---------------|----------|-------------------|
| **Normal Cooling** | PID active | OFF | Default summer mode |
| **Boost Cooling** | Fully open (100%) | PID active | `(room_temp - setpoint) > threshold` |

### Mode Transition Logic

```
Boost Activation:   (current_temp - target_temp) > threshold
Boost Deactivation: (current_temp - target_temp) < (threshold / 2)
```

**Hysteresis:** Built-in to prevent oscillation (activate at 4°C, deactivate at 2°C)

### Threshold Configuration

- **Source:** Home Assistant `input_number.ground_floor_fancoil_boost_threshold`
- **Default fallback:** 4.0°C (if HA unavailable)
- **Scope:** Single threshold for entire ground floor
- **Hysteresis formula:** `threshold / 2`

### Dew Point Protection

Mirror first floor pattern:
- Calculate per-room dew point from temperature + humidity
- Aggregate `ground_floor_max_dew_point` from: Soggiorno, Cucina, Anticamera
- Mixing valve enforces: `supply_temp >= (max_dew_point + safe_margin)`

### Key Differentiators

1. **Radiant-primary strategy:** Unlike typical boost patterns, radiant is the preferred system
2. **ESPHome-native coordination:** Autonomous operation survives HA outages
3. **Configurable threshold:** Runtime adjustment via HA without recompilation
4. **Hysteresis-based transitions:** Prevents rapid cycling between modes

---

## Target Users

### Primary User: System Owner (Alberto)

**Profile:**
- Technical residential system owner managing multi-floor HVAC
- Seeks optimal comfort in primary living spaces (Soggiorno, Cucina)
- Values silent operation and even temperature distribution
- Comfortable with ESPHome configuration and Home Assistant dashboards

**Needs:**
- Improved cooling comfort on ground floor
- Runtime adjustability of boost threshold
- Clear visibility into system state (which mode active, why)
- Reliable autonomous operation

**Goals:**
- Achieve first-floor-quality comfort on ground floor
- Reduce reliance on noisy fancoils for routine cooling
- Maintain safety (condensation prevention)
- Enable future enhancements (dehumidification mode)

---

## Goals & Success Metrics

### Comfort Objectives

- **Primary Goal:** Enable radiant floor cooling as primary ground floor cooling system
- **Boost capability:** Fancoils activate automatically when radiant insufficient
- **Silent operation:** Normal cooling mode produces zero audible noise

### Technical Objectives

- **Dew point safety:** Zero condensation events during radiant cooling
- **Autonomous operation:** System functions correctly during HA outages (5+ minutes)
- **Configurable threshold:** Adjustable via HA without firmware changes
- **Smooth transitions:** Hysteresis prevents mode oscillation

### Success Metrics

| Metric | Target |
|--------|--------|
| Condensation events | 0 |
| Mode oscillation frequency | <1 transition per hour during stable conditions |
| HA-unavailable operation | 100% functional with fallback threshold |
| User comfort satisfaction | Subjective improvement reported |
| PID tuning completion | All 4 radiant zones tuned for cooling mode |

---

## MVP Scope

### Core Features (Must Have)

**1. Ground Floor Radiant Cooling Migration**
- Convert `heat_only_radiant.yaml` → `radiant.yaml` for: Soggiorno, Cucina, Bagno, Anticamera
- Enable cool_output on radiant PIDs
- Update summer_mode behavior for cooling (currently forces OFF)

**2. Dew Point Calculation Infrastructure**
- Add `dew_point_sensor.yaml` to: Soggiorno, Cucina, Anticamera
- Create `ground_floor_max_dew_point` combination sensor
- Wire to mixing valve target temperature control

**3. Fancoil Boost Coordinator Component**
- New `components/fancoil_boost_coordinator.yaml`
- Monitor temperature delta vs HA threshold
- Control fancoil PID activation (ON when boost, OFF otherwise)
- Control radiant zone outputs (PID when normal, 100% when boost)
- Implement hysteresis logic

**4. HA Threshold Integration**
- Create `input_number.ground_floor_fancoil_boost_threshold` helper
- ESPHome number sensor for threshold with fallback default
- Hysteresis calculated as `threshold / 2`

**5. Zone Demand Aggregation Updates**
- Update `ground_floor_radiant_any_zone_open` to include cooling mode
- Ensure mixing pump activates during radiant cooling

**6. Minimum Time-in-State Protection**
- Prevent mode transitions within minimum duration (e.g., 10 minutes)
- Avoid wear on valves and user confusion from rapid cycling

**7. Diagnostic Sensors**
- `text_sensor.ground_floor_cooling_mode` - "Radiant Only" / "Fancoil Boost"
- `sensor.ground_floor_max_dew_point` - Current max dew point
- `binary_sensor.fancoil_boost_active` - Boost mode status

### Out of Scope for MVP

- ❌ **Dehumidification mode** (future epic)
- ❌ **Per-room boost thresholds** (single floor-wide threshold for MVP)
- ❌ **Rate-of-change triggering** (simple delta comparison only)
- ❌ **Time-of-day scheduling** (manual HA automations can layer this)
- ❌ **Locale Tecnico integration** (fancoil-only room, no radiant)
- ❌ **Complex comfort algorithms** (start simple, iterate)

### MVP Success Criteria

**Epic 13 MVP is complete when:**
1. ✅ All 4 ground floor radiant zones (Soggiorno, Cucina, Bagno, Anticamera) support cooling mode
2. ✅ Dew point protection active with supply temp limiting
3. ✅ Fancoil boost triggers correctly when delta > threshold
4. ✅ Fancoil boost deactivates with hysteresis when delta < threshold/2
5. ✅ System operates autonomously during HA restart (3-5 minute test)
6. ✅ Zero condensation observed during validation testing
7. ✅ Radiant PID parameters tuned for cooling (autotune or manual)

---

## Post-MVP Vision

### Phase 2 Features

**Dehumidification Mode:**
- Humidity threshold triggers fancoil operation
- Fancoil provides dehumidification without overcooling
- Coordinate with radiant for temperature maintenance

**Per-Room Boost Thresholds:**
- Individual room threshold configuration
- Account for different thermal characteristics (Cucina has cooking heat load)

**Advanced Triggering:**
- Rate-of-change detection (rapid temperature rise triggers earlier boost)
- Predictive boost based on time-of-day patterns

### Long-Term Vision

**Epic 14+: Intelligent Comfort Control**
- Occupancy-aware cooling (reduce capacity when rooms empty)
- Weather forecast integration (pre-cool before hot days)
- Energy optimization (prefer radiant during off-peak electricity rates)

**MEV Integration:**
- Coordinate MEV (ventilation) with humidity control
- Increase air exchange when dehumidification needed

---

## Technical Considerations

### Platform Requirements

**Target Devices:**
- `climate-control.yaml` (KC868-A16) - Zone distribution with radiant + fancoil control
- Mixing group - Dew point-based supply temperature limiting

**ESPHome Version:** Current (2024.x+) with lambda support

**Resource Constraints:**
- Flash usage increase: <5% (coordinator component, dew point sensors)
- RAM usage: Minimal (few additional globals)

### Architecture Considerations

**Component Structure:**
```
components/
  fancoil_boost_coordinator.yaml    # NEW: Mode coordination logic
  dew_point_sensor.yaml             # EXISTS: Per-room calculation
  radiant.yaml                      # EXISTS: Dual-mode radiant
  fancoil.yaml                      # EXISTS: Fancoil PID

components/rooms/ground_floor/
  soggiorno.yaml                    # UPDATE: Add radiant cooling + dew point
  cucina.yaml                       # UPDATE: Add radiant cooling + dew point
  bagno.yaml                        # UPDATE: Add radiant cooling
  anticamera.yaml                   # UPDATE: Add radiant cooling + dew point
  ground-floor.yaml                 # UPDATE: Add coordinator + max dew point
```

**Coordination Pattern:**
- Coordinator polls temperature delta vs threshold
- Controls fancoil PID enable/disable
- Controls radiant output mode (PID vs 100%)
- Reports state via diagnostic sensors

**Integration with Existing Systems:**
- Reuses Epic 5 sensor failover patterns (HA temperature sensors)
- Mirrors first floor dew point aggregation pattern
- Compatible with Epic 10 zone demand UDP broadcasting

### Key Dependencies

| Dependency | Status | Impact |
|------------|--------|--------|
| `radiant.yaml` component | ✅ Exists | Foundation for dual-mode |
| `dew_point_sensor.yaml` | ✅ Exists | Per-room calculation |
| First floor dew point pattern | ✅ Exists | Reference implementation |
| HA humidity sensors | ✅ Available | Required for dew point |
| Epic 12 (dew point protection) | 📋 Draft | Provides safety patterns |

---

## Constraints & Assumptions

### Constraints

- **Budget:** $0 (software-only changes)
- **Timeline:** Complete before summer 2026 cooling season
- **Resources:** Solo developer, part-time effort
- **Technical:**
  - Must maintain ESPHome YAML composition patterns
  - Cannot disrupt existing heating operation
  - Must work within A16 flash/RAM limits

### Key Assumptions

- Ground floor radiant infrastructure is physically capable of cooling (pipes, insulation)
- Humidity sensors in Soggiorno, Cucina, Anticamera are available via HA
- Mixing valve can handle cooling-mode supply temperature requirements
- PID parameters will need tuning for cooling (different dynamics than heating)
- Single floor-wide threshold is sufficient for MVP (per-room can come later)
- 4°C default threshold is reasonable starting point (adjustable via HA)
- Radiant cooling provides meaningful comfort improvement over fancoil-only

---

## Risks & Open Questions

### Key Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Condensation during transitions** | Medium | High | Ensure dew point protection always active; consider gradual transitions |
| **Threshold oscillation (hunting)** | Medium | Medium | Hysteresis + minimum time-in-state requirement |
| **Dew point sensor failure** | Medium | High | Sensor failover with conservative fallback (70% RH assumption) |
| **PID tuning for cooling** | High | Medium | Plan dedicated tuning phase; start with conservative parameters |
| **Zone demand aggregation** | Certain | High | Must update binary sensor to include cooling mode |
| **Asymmetric room behavior** | High | Medium | Accept for MVP; single threshold may overcool some rooms |
| **Radiant capacity unknown** | Medium | Medium | Start radiant-only, add fancoil boost if insufficient |
| **Mixing valve capacity** | Low-Medium | High | Validate chiller can supply 4 zones at full demand |

### Open Questions

1. **PID tuning approach:** Autotune vs. manual parameter adjustment for cooling mode?
2. **Minimum time-in-state value:** 10 minutes sufficient, or need longer?
3. **Bagno inclusion:** Should Bagno (high humidity variance) be excluded from dew point aggregation permanently?
4. **Fallback behavior:** If all dew point sensors fail, should cooling be disabled entirely?
5. **Summer mode trigger:** How is summer/winter mode currently determined? (Manual HA switch? Automatic?)
6. **Mixing valve behavior:** Same valve for heating and cooling, or separate circuits?

### Areas Needing Further Research

- Actual radiant cooling capacity measurement (test run before full implementation)
- Optimal safe_margin for dew point (2°C industry standard, but validate)
- PID autotune availability and reliability for cooling mode
- Interaction with Epic 12 dew point protection (coordinate or duplicate?)

---

## Stories (Draft)

| # | Story | Description | Estimate |
|---|-------|-------------|----------|
| **13.1** | Radiant Dual-Mode Migration | Convert 4 ground floor rooms from `heat_only_radiant.yaml` to `radiant.yaml` | Small |
| **13.2** | Ground Floor Dew Point Infrastructure | Add per-room dew point sensors, create max aggregation | Small |
| **13.3** | Mixing Valve Dew Point Integration | Wire `ground_floor_max_dew_point` to supply temp control | Small |
| **13.4** | HA Threshold Configuration | Create `input_number` helper, ESPHome integration with fallback | Small |
| **13.5** | Fancoil Boost Coordinator Component | New component with mode logic, hysteresis, minimum time-in-state | Medium |
| **13.6** | Zone Demand Aggregation Update | Update binary sensors to include cooling mode | Small |
| **13.7** | Diagnostic Sensors | Add mode, dew point, boost status sensors | Small |
| **13.8** | PID Tuning for Cooling | Autotune or manual parameter adjustment for all 4 zones | Medium |
| **13.9** | Integration Testing | Full system validation, failover testing, comfort assessment | Medium |

---

## Appendices

### A. Current Ground Floor Configuration

| Room | Radiant | Fancoil | Dew Point (MVP) |
|------|---------|---------|-----------------|
| Soggiorno | ✅ Heat only → Cool | ✅ Available | ✅ Included |
| Cucina | ✅ Heat only → Cool | ✅ Available | ✅ Included |
| Bagno | ✅ Heat only → Cool | ❌ None | ❌ Excluded (humidity variance) |
| Anticamera | ✅ Heat only → Cool | ❌ None | ✅ Included |
| Locale Tecnico | ❌ None | ✅ Available | N/A |

### B. First Floor Reference Pattern

From `components/rooms/first_floor/first-floor.yaml`:
```yaml
sensor:
  - platform: combination
    id: first_floor_max_dew_point
    name: "Max Dew Point Primo piano"
    type: max
    sources:
      - source: camera_ospiti_dew_point
      - source: camera_nord_dew_point
      - source: camera_padronale_dew_point
      - source: camera_sud_dew_point
    on_value:
      then:
        - climate.control:
            id: pid_mixing_valve_first_floor_radiant
            target_temperature: !lambda "return (x + ${safe_margin});"
```

### C. Elicitation Session Summary

**Session Date:** December 26, 2025

**Key Decisions Made:**
- Threshold configurable via HA `input_number` (single floor-wide value)
- Hysteresis formula: `threshold / 2`
- ESPHome-native coordination (autonomous)
- Radiant fully open when fancoil boosts (simpler than assist mode)
- Dew point sources: Soggiorno, Cucina, Anticamera (Bagno excluded)
- Dehumidification mode: Out of scope (future epic)
- Simple logic first, iterate complexity later

**Risks Identified:**
- Condensation during transitions (High priority)
- Threshold oscillation (Medium, mitigated by hysteresis)
- PID tuning required for cooling mode (High priority)
- Zone demand aggregation update required (Certain)

---

## Next Steps

### Immediate Actions

1. **Review this brief** - Validate scope, assumptions, and risk mitigations
2. **Answer open questions** - Especially mixing valve configuration and summer mode trigger
3. **Create Story 13.1** - Start with radiant dual-mode migration (lowest risk, foundation for others)
4. **Test radiant cooling capacity** - Brief manual test to validate infrastructure works

### Transition to Implementation

Once brief approved:
1. Create detailed stories with acceptance criteria
2. Start with Story 13.1 (radiant migration) and 13.2 (dew point infrastructure)
3. Implement coordinator component (Story 13.5) after foundation ready
4. Plan PID tuning phase for early summer 2026

---

**Brief Status:** Ready for review

---

*Brief created using BMAD-METHOD™ analyst facilitation with advanced elicitation*
