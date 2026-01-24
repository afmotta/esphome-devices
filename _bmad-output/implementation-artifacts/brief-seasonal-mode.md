# Project Brief: Three-Tier Seasonal Mode Selection

## Executive Summary

**Product Concept:** An automated heat pump mode selection system that eliminates manual seasonal switching by combining calendar-based hard locks, weather intelligence, and demand-driven transitions.

**Primary Problem:** The current binary `summer_mode` switch requires manual intervention to toggle between heating and cooling seasons, leading to forgotten switches, inflexibility during shoulder seasons, and reactive responses after discomfort occurs.

**Target System:** ESPHome/Home Assistant-based HVAC control for a residential building in Milan with heat pump, radiant floors, fancoils, and MEV system.

**Key Value Proposition:** Zero manual interventions for seasonal mode switching while maintaining optimal comfort and energy efficiency year-round.

---

## Problem Statement

### Current State and Pain Points

The existing HVAC control system uses a binary `summer_mode` switch that must be manually toggled to change the heat pump's operating mode between heating (buffer hot) and cooling (buffer cold). This creates several issues:

1. **Human Error:** Forgetting to switch modes leads to discomfort (house too hot in spring because still in HEAT mode)
2. **Inflexibility:** Binary switch can't handle shoulder seasons (Mid April-May, September-Mid October) where needs vary day-to-day
3. **Reactive Response:** Mode changes happen after discomfort is noticed, not proactively
4. **Mental Load:** Homeowner must track weather patterns and remember to adjust settings

### Impact

- Comfort degradation during seasonal transitions
- Energy waste from running wrong mode
- User frustration with manual intervention requirements
- Suboptimal system utilization

### Why Existing Solutions Fall Short

- **Pure calendar-based:** Too constricted - can't handle unusual weather patterns
- **Pure temperature-driven:** Outdoor temp may be misleading - doesn't reflect building thermal state
- **Simple threshold automation:** Creates mode churn and doesn't account for forecast

### Urgency

The system is operational now with manual switching. This improvement enables truly autonomous operation and prepares the system for future enhancements (Epic 16 MEV humidity control depends on reliable mode state).

---

## Proposed Solution

### Core Concept: Three-Tier Decision Architecture

A layered approach that uses:

1. **Tier 1 - Calendar Gate:** Hard locks for core seasons (Oct 15 - Apr 15 → HEAT, Jun-Aug → COOL)
2. **Tier 2 - Weather Intelligence:** 24-hour temperature forecast guidance during shoulder seasons
3. **Tier 3 - Demand-Driven Transitions:** PID requests trigger actual mode changes

### Key Differentiators

- **Demand wins:** Unlike pure automation, the system trusts PID controllers to know actual room needs
- **No pre-conditioning:** Leverages fast heat pump response (minutes to condition buffer)
- **No automatic return to neutral:** Avoids mode churn by staying in mode until opposite is requested
- **Forecast as guidance, not gate:** Weather intelligence informs but doesn't override demand

### Why This Solution Will Succeed

1. **Matches real-world needs:** Milan has distinct seasons (hot summers, cold winters) with variable shoulder periods
2. **Leverages existing infrastructure:** PIDs already know room demand; this aggregates that signal
3. **Conservative defaults:** Hard locks during core seasons prevent obviously wrong states
4. **Self-correcting:** If forecast is wrong, demand override ensures correct action

### High-Level Vision

A fully autonomous seasonal mode system that:
- Never requires manual intervention
- Responds to actual building needs, not just external conditions
- Provides clear diagnostic visibility into decision-making
- Serves as foundation for advanced features (humidity control, energy optimization)

---

## Target Users

### Primary User Segment: Homeowner/System Operator

**Profile:**
- Technical homeowner managing ESPHome/Home Assistant smart home
- Located in Milan, Italy (continental climate with distinct seasons)
- Desires "set and forget" automation

**Current Behaviors:**
- Manually toggles `summer_mode` switch 2-4 times per year
- Sometimes forgets, leading to discomfort
- Monitors weather to decide when to switch

**Pain Points:**
- Mental overhead of tracking seasonal changes
- Uncertainty about optimal switching timing
- No visibility into why current mode was selected

**Goals:**
- Zero manual intervention for seasonal operation
- Confidence that system will "do the right thing"
- Visibility into system decisions when desired

---

## Goals & Success Metrics

### Business Objectives

- **Eliminate manual mode switching:** 0 manual interventions required for seasonal operation
- **Maintain comfort:** No complaints related to wrong mode selection
- **Preserve energy efficiency:** No degradation vs. optimal manual switching

### User Success Metrics

- Time spent managing seasonal modes: **0 hours/year** (down from ~1-2 hours)
- Mode-related discomfort incidents: **0 per year**
- Dashboard "mode override active" frequency: **< 10% of shoulder season days**

### Key Performance Indicators (KPIs)

- **Mode Transition Accuracy:** > 95% of transitions appropriate for conditions
- **Calendar Lock Compliance:** 100% (system in correct mode during core seasons)
- **Demand Override Frequency:** Track but don't optimize (demand override is correct behavior)
- **Forecast Guidance Accuracy:** > 80% of shoulder season days, forecast matches actual need

---

## MVP Scope

### Core Features (Must Have)

- **Calendar Gate Implementation:** Automations that hard-lock HEAT (Oct 15 - Apr 15) and COOL (Jun-Aug)
- **Shoulder Season Entry:** Automations that set SANITARY_ONLY on Apr 15 and Sep 1
- **Demand-Driven HEAT Transition:** Automation triggered by any PID requesting heating action
- **Demand-Driven COOL Transition:** Automation triggered by any PID requesting cooling action
- **HP Mode Input Select:** `input_select.hp_mode` with HEAT/COOL/SANITARY_ONLY options
- **Mode Reason Tracking:** `input_select.hp_mode_reason` showing CALENDAR_LOCK/DEMAND/MANUAL

### Out of Scope for MVP

- Weather forecast integration (Phase 2)
- Forecast guidance sensor (Phase 2)
- Override detection indicator (Phase 2)
- Humidity forecast for MEV decisions (Phase 3)
- Energy impact analysis (Phase 3)
- Historical mode transition logging (Phase 3)
- Mobile notifications for mode changes

### MVP Success Criteria

The MVP is successful when:
1. System automatically enters HEAT mode on Oct 15 without intervention
2. System automatically enters COOL mode on Jun 1 without intervention
3. During shoulder seasons, first PID heating request triggers HEAT mode
4. During shoulder seasons, first PID cooling request triggers COOL mode
5. Mode stays locked until opposite demand or season change
6. Dashboard shows current mode and reason
7. System exits HEAT mode and enters Spring shoulder on Apr 15

---

## Post-MVP Vision

### Phase 2 Features (Weather Intelligence)

- Integrate Home Assistant weather forecast entity
- Create `sensor.hp_forecast_guidance` showing what forecast suggests
- Create `binary_sensor.hp_mode_override_active` when demand differs from guidance
- Dashboard showing forecast vs actual mode alignment
- Configurable thresholds via `input_number` entities (26°C cooling, 14°C heating)

### Phase 3 Features (Enhanced Diagnostics)

- Humidity forecast integration for MEV coordination (connects to Epic 16)
- Mode transition logging with timestamps and reasons
- Energy impact analysis (compare to baseline)
- Override frequency tracking and alerting
- Integration with long-term energy reporting

### Long-term Vision (1-2 Years)

- Machine learning to refine thresholds based on actual comfort outcomes
- Predictive pre-conditioning for high-demand events (guests arriving, returning from vacation)
- Integration with electricity pricing for cost-optimized mode timing
- Multi-zone awareness (different floors may have different optimal modes)

### Expansion Opportunities

- Apply same three-tier pattern to other seasonal decisions (e.g., window shading, pool heating)
- Share aggregated data for Milan climate community insights
- Package as reusable ESPHome/HA blueprint for similar projects

---

## Technical Considerations

### Platform Requirements

- **Target Platform:** Home Assistant automations + ESPHome devices
- **HA Version:** 2024.x or later (current installation)
- **ESPHome Version:** 2024.x or later (current installation)
- **Performance Requirements:** Mode transitions within 1 minute of trigger

### Technology Preferences

- **Automation Engine:** Home Assistant YAML automations (existing pattern)
- **State Storage:** HA input_select and input_number helpers
- **PID Integration:** ESPHome climate entities with `hvac_action` attribute
- **Weather Data:** HA weather integration (OpenWeatherMap or Met.no)

### Architecture Considerations

- **Repository Structure:** Automations in HA `automations.yaml` or packages
- **Service Architecture:** HA orchestrates, ESPHome devices expose PID states
- **Integration Requirements:** 
  - Read PID `hvac_action` from multiple ESPHome boards
  - Write to heat pump mode control (existing integration)
  - Read weather forecast entity
- **Security/Compliance:** No external data exposure; all processing local

---

## Constraints & Assumptions

### Constraints

- **Budget:** Zero additional hardware cost (software-only implementation)
- **Timeline:** Target completion before spring shoulder season (Mar 1, 2026)
- **Resources:** Single developer (homeowner) with limited time
- **Technical:** Must work with existing ESPHome PID architecture (Epic 2 pattern)

### Key Assumptions

- Heat pump can switch modes via existing HA integration (verified)
- PID `hvac_action` attribute reliably indicates heating/cooling demand
- Weather forecast is accurate enough for 24h guidance (not critical, demand overrides)
- Milan climate follows expected patterns (Dec-Feb cold, Jun-Aug hot)
- Buffer conditioning time is fast (< 5 minutes) making pre-conditioning unnecessary
- PIDs on multiple boards can be monitored by HA automations

---

## Risks & Open Questions

### Key Risks

- **PID Action Detection Reliability:** If `hvac_action` attribute is unreliable or delayed, demand-driven transitions may be sluggish
  - *Mitigation:* Test with current PIDs; fall back to output percentage monitoring if needed

- **Multi-Board Coordination Latency:** Checking PIDs across multiple ESPHome devices may introduce delay
  - *Mitigation:* Use HA state triggers rather than polling; consider UDP aggregation (Epic 10 pattern)

- **Weather Integration Availability:** Weather service outages could affect Phase 2 guidance
  - *Mitigation:* Guidance is advisory only; demand override ensures correct operation regardless

- **Edge Case: Rapid Oscillation:** In shoulder seasons, rapidly alternating heat/cool requests could cause HP stress
  - *Mitigation:* "No return to SANITARY" design prevents churn; HP has internal protection

### Open Questions

- Which HA weather integration provides most reliable 24h forecast for Milan?
- Should mode changes be logged to a dedicated history entity for analysis?
- How to handle HP maintenance mode (manual override needed)?
- Should there be a manual override option in dashboard for edge cases?

### Areas Needing Further Research

- Optimal threshold values (26°C cooling, 14°C heating) may need tuning after first shoulder season
- PID action detection method (hvac_action vs output percentage) needs testing
- Weather forecast accuracy for Milan - compare services before Phase 2

---

## Appendices

### A. Research Summary

**Source:** Brainstorming session (January 15, 2026)
**Document:** `docs/brainstorming-session-seasonal-mode.md`

Key findings from brainstorming:
- Calendar-based alone is "too constricted"
- Temperature-based alone is "misleading"
- Demand-driven with calendar gates emerged as optimal hybrid
- User confirmed Milan summers always need cooling (hard lock appropriate)
- User confirmed HP buffer conditioning is fast (no pre-conditioning needed)
- User preference: demand wins over forecast guidance

### B. Related Documentation

- Epic 16 Brief: `docs/epic-16-brief.md` (MEV humidity control, depends on mode state)
- Epic 10: UDP-based zone activity tracking (pattern for multi-board coordination)
- Architecture: `docs/architecture.md`

### C. References

- Home Assistant Climate Entity: https://www.home-assistant.io/integrations/climate/
- ESPHome PID Climate: https://esphome.io/components/climate/pid.html
- HA Weather Integration: https://www.home-assistant.io/integrations/weather/

---

## Next Steps

### Immediate Actions

1. Create `input_select.hp_mode` helper in Home Assistant
2. Create `input_select.hp_mode_reason` helper in Home Assistant
3. Implement calendar gate automations (Dec 1, Mar 1, Jun 1, Sep 1 triggers)
4. Implement demand-driven transition automations (PID action triggers)
5. Test PID `hvac_action` attribute reliability across all climate entities
6. Create simple dashboard card showing current mode and reason
7. Document automation YAML in repository

### PM Handoff

This Project Brief provides the full context for **Three-Tier Seasonal Mode Selection**. The system eliminates manual seasonal switching through a layered approach combining calendar locks, weather intelligence, and demand-driven transitions.

**Key Implementation Note:** This is a Home Assistant automation project, not an ESPHome component. The ESPHome PIDs expose state; HA orchestrates mode selection.

---

*Brief Created: January 15, 2026*
*Based on: Brainstorming Session Results (docs/brainstorming-session-seasonal-mode.md)*
