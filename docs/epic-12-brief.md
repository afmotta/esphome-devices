# Project Brief: Epic 12 - Autonomous Dew Point Protection for Radiant Cooling

**Epic:** 12 - Dew Point Protection  
**Date:** November 24, 2025  
**Status:** Draft (Deferred - Epic 11 takes priority)  
**Priority:** Critical Safety Feature

---

## Context: Epic 10 Completion Status

**Epic 10 Title:** ESP32 Room Sensors & Zone Activity Tracking via UDP

**What Epic 10 Actually Delivered (Stories 10.2-10.7):**
- ✅ Zone demand aggregation (binary sensors combining PID states)
- ✅ UDP broadcasting of zone demand (distribution boards → mixing group)
- ✅ Demand-based relay control (relays ON only when zones active)
- ✅ Epic 9 UDP infrastructure validated in production
- ✅ 20-30% relay runtime reduction (energy savings)

**What Epic 10 Deferred (Story 10.1):**
- ❌ ESP32 room sensors broadcasting temperature/humidity via UDP
- ❌ `room_sensors.yaml` v6 with UDP tier support
- ❌ Peer-to-peer room sensor architecture

**Implication for Epic 12:**
- Epic 10 proved UDP **binary sensor** broadcasting (zone demand: true/false)
- Epic 12 extends this to UDP **float sensor** broadcasting (dew point: temperature values)
- Same `packet_transport` platform, similar patterns, proven infrastructure
- Room sensors remain HA-only (Epic 5 architecture) until Story 10.1 is implemented

---

## Executive Summary

Epic 12 implements autonomous dew point protection for radiant cooling systems to prevent condensation damage when Home Assistant is unavailable. By calculating dew point temperature locally on ESPHome devices using room temperature and humidity data, the system will enforce a safety minimum on supply water temperature (dew point + 2°C) during cooling operations. This critical safety feature eliminates the risk of floor/wall condensation that could cause structural damage, mold growth, and expensive repairs.

**Problem:** Currently, if HA fails during radiant cooling, there is no protection against supply water temperature dropping below the dew point, which causes condensation on floors and walls.

**Solution:** ESPHome-native dew point calculation and automatic supply temperature limiting during cooling mode, independent of Home Assistant.

---

## Problem Statement

### Current State and Risk

**Radiant cooling systems face a critical safety challenge:**
- Chilled water circulating through floors/walls can reach temperatures below the dew point
- When surface temperature < dew point → condensation forms on floors and walls
- Condensation leads to:
  - **Structural damage** (wood floor warping, wall damage)
  - **Mold growth** (health hazards, expensive remediation)
  - **Safety hazards** (slippery floors)
  - **Expensive repairs** ($1,000s+ in damage)

### Current Architecture Gap

**Epic 5 HA-Only Architecture:**
- Room temperature sensors: HA-only (no Modbus hardware deployed yet)
- Humidity sensors: HA-only
- Dew point calculation: Non-existent
- Supply temperature limiting: PID controllers respond to room temp, no dew point awareness

**Single Point of Failure:**
- If Home Assistant fails during cooling → No sensor data available
- PIDs enter emergency shutdown (Epic 5 timeout protection)
- **BUT:** Existing chilled water in pipes/floors continues radiating cold
- **Risk window:** 15-30 minutes until water warms up naturally
- **Damage can occur:** Condensation starts within 5-10 minutes if dew point exceeded

### Why This Must Be Autonomous

**HA dependency is unacceptable for safety-critical features:**
1. **Network failures** (WiFi outage, HA restart during cooling)
2. **Maintenance windows** (HA updates, configuration changes)
3. **Integration failures** (Entity unavailable, sensor timeout)
4. **Physical damage risk** is immediate and expensive

**Requirement:** ESPHome must calculate dew point locally and enforce limits autonomously.

---

## Proposed Solution

### Core Approach

**Local Dew Point Calculation & Supply Temperature Limiting:**

1. **Dew Point Calculation (ESPHome Lambda)**
   - Use Magnus-Tetens formula for accurate dew point from T and RH
   - Calculate per-zone dew point every 30 seconds
   - Aggregate across all active cooling zones → use HIGHEST dew point

2. **Supply Temperature Safety Minimum**
   - During cooling mode: `supply_temp_min = max_zone_dew_point + 2.0°C`
   - Clamp PID output to prevent supply temp dropping below safety minimum
   - Example: Dew point 18°C → Enforce supply temp ≥ 20°C

3. **PID Integration**
   - Intercept PID heat/cool output in mixing group device
   - Apply safety clamp BEFORE output reaches DAC/valve control
   - Log warnings when dew point limiting is active

4. **Multi-Tier Failover for Humidity Data**
   - **Tier 1:** Local humidity sensor (when Modbus hardware deployed)
   - **Tier 2:** Home Assistant humidity sensor (current Epic 5 mode)
   - **Tier 3:** Conservative fallback (assume 70% RH) if no data available

### Key Differentiators

**vs. HA-based protection:**
- ✅ Autonomous (survives HA failure)
- ✅ Real-time response (<5 seconds)
- ✅ No network dependency
- ✅ Survives sensor failover (multi-tier)

**vs. Fixed safety limits:**
- ✅ Dynamic adjustment based on actual humidity conditions
- ✅ Maximizes cooling effectiveness while maintaining safety
- ✅ Seasonal adaptation (winter dry vs. summer humid)

---

## Target System

### Primary: Ground Floor Radiant Cooling

**Devices:**
- `distribuzione-piano-terra.yaml` (A16) - Zone controllers with humidity sensors
- `gruppo-miscelazione.yaml` (A6) - Mixing valve control with dew point enforcement

**Zones with Radiant Cooling:**
- Soggiorno (living room)
- Cucina (kitchen)
- Bagno (bathroom)
- Anticamera (entryway)

### Secondary: First Floor Radiant Cooling (Future)

**Device:**
- `distribuzione-primo-piano.yaml` (A16) - When cooling capability added

**Current state:** Heating-only, cooling not yet implemented

---

## Goals & Success Metrics

### Safety Objectives

**Primary Goal:** Zero condensation events during cooling operations

**Metrics:**
- ✅ Dew point calculation accuracy: ±0.3°C vs. reference calculator
- ✅ Supply temp enforcement: 100% compliance with `dew_point + 2°C` minimum
- ✅ Response time: <10 seconds from humidity spike to supply temp limit
- ✅ Failover reliability: Protection active even with sensor failures

### User Experience Targets

**Transparent Protection:**
- Cooling effectiveness maintained when conditions safe
- Graceful degradation (reduce cooling, don't shut down) when humidity high
- Clear diagnostic sensors showing dew point and limiting status

**Performance:**
- No false positives (unnecessary limiting when safe)
- Minimal comfort impact (2°C margin is industry standard)

### Code Quality Metrics

- Flash usage increase: <3% (dew point calculation is lightweight)
- RAM usage increase: <1% (minimal state storage)
- Compilation: Zero errors, zero warnings
- Documentation: Complete migration guide and safety validation procedures

---

## MVP Scope

### Core Features (Must Have)

**1. Dew Point Calculation Component**
- Magnus-Tetens formula implementation in ESPHome lambda
- Per-zone dew point calculation from temperature + humidity
- Aggregate max dew point across all active cooling zones
- Update interval: 30 seconds

**2. Multi-Tier Humidity Failover**
- Tier 1: Local Modbus humidity sensor (when hardware deployed)
- Tier 2: Home Assistant humidity sensor (current Epic 5 mode)
- Tier 3: Conservative fallback (70% RH assumption)
- Status text sensor showing active tier

**3. Supply Temperature Safety Limiting**
- Mixing group (gruppo-miscelazione) intercepts PID output
- Apply clamp: `supply_temp >= (max_dew_point + 2.0°C)` during cooling
- Only enforce during CLIMATE_ACTION_COOLING (not heating)
- Log warnings when limiting is active

**4. Diagnostic Sensors (Home Assistant Exposed)**
- `sensor.{zone}_dew_point` - Per-zone dew point temperature
- `sensor.max_dew_point_cooling_zones` - Aggregate maximum for active zones
- `sensor.supply_temp_safety_minimum` - Current enforced minimum
- `binary_sensor.dew_point_limiting_active` - Boolean status
- `text_sensor.humidity_data_source` - Failover tier status

**5. Safety Validation**
- Bench testing with reference dew point calculator
- Production validation during first cooling event (summer 2026)
- Intentional high-humidity test (bathroom with hot shower)

### Out of Scope for MVP

- ❌ **Per-zone supply temperature limiting** (single mixing valve serves all zones)
- ❌ **Humidity trend prediction** (future enhancement for proactive limiting)
- ❌ **HA notifications** (alerts can be added via HA automations post-MVP)
- ❌ **Historical dew point logging** (use HA history database)
- ❌ **Modbus humidity hardware deployment** (MVP uses Epic 5 HA-only sensors)

### MVP Success Criteria

**Epic 12 is successful when:**
1. ✅ Dew point calculation matches reference within ±0.3°C
2. ✅ Supply temperature never drops below `dew_point + 2°C` during cooling
3. ✅ Protection remains active during HA restart (3-5 minute test)
4. ✅ Failover to 70% RH assumption works when all sensors unavailable
5. ✅ All firmware compiles with flash <80% and RAM <15%
6. ✅ Zero condensation observed during intentional high-humidity test

---

## Post-MVP Vision

### Phase 2 Features (After Epic 12 MVP Proven)

**Advanced Humidity Management:**
- Humidity trend prediction (if RH rising rapidly → increase safety margin to +3°C)
- Per-room humidity monitoring dashboard in Home Assistant
- MEV coordination (increase air exchange when humidity high)

**User Notifications:**
- HA alert when dew point limiting reduces cooling effectiveness
- Daily summary of dew point events and limiting frequency
- Seasonal trends (summer humidity patterns)

**Hardware Integration:**
- Story 1.6 Modbus humidity sensors deployment (enable Tier 1 failover)
- Upgrade to calibrated high-accuracy humidity sensors (±2% RH vs. ±5% RH)

### Long-Term Vision (Epic 13+)

**Predictive Dew Point Management:**
- Weather forecast integration (predict high humidity days)
- Pre-cooling during low-humidity periods (thermal banking)
- Coordinate with dehumidification systems

**Advanced Control Strategies:**
- Per-zone mixing valves with individual dew point limits (requires hardware upgrade)
- Supply temperature modulation based on zone-specific dew points
- Humidity-aware PID tuning (gentler cooling when humid)

---

## Technical Considerations

### Platform Requirements

**Target Devices:**
- KC868-A16 (distribuzione boards) - Zone-level dew point calculation
- KC868-A6 (gruppo-miscelazione) - Supply temp limiting enforcement

**ESPHome Version:** Current (2024.x+) with lambda support

**Resource Constraints:**
- A6 flash: 2MB (currently 49.8%, target <80%)
- A16 flash: 3.8MB (currently 53%, target <80%)
- Dew point calculation: ~1KB code, negligible RAM

### Architecture Considerations

**Component Structure:**
```
components/
  dew_point_calculator.yaml          # Per-zone dew point calculation
  dew_point_aggregator.yaml          # Max across active cooling zones
  supply_temp_safety_limiter.yaml    # Mixing group enforcement
  sensor_failover_3tier.yaml         # Already exists (Epic 5)
```

**Device Integration:**
- Distribution boards: Include `dew_point_calculator.yaml` per room component
- Mixing group: Include `dew_point_aggregator.yaml` + `supply_temp_safety_limiter.yaml`

**UDP Broadcasting (Epic 9/10 Pattern):**
- Epic 9: Float sensor broadcasts (supply temperatures: mixing → distribution)
- Epic 10: Binary sensor broadcasts (zone demand: distribution → mixing)
- **Epic 11:** Float sensor broadcasts (dew points: distribution → mixing)
- Mixing group receives and aggregates dew points
- Fallback: HA sensors if UDP unavailable

### Dew Point Calculation Formula

**Magnus-Tetens Approximation:**
```cpp
// Input: T (°C), RH (0-100%)
// Output: Td (dew point in °C)

float a = 17.27;
float b = 237.7;
float alpha = ((a * T) / (b + T)) + ln(RH / 100.0);
float dew_point = (b * alpha) / (a - alpha);
```

**Accuracy:** ±0.4°C for T = -40°C to +50°C, RH = 1% to 100%

**Computational Cost:** ~100 floating-point operations → <1ms on ESP32

---

## Constraints & Assumptions

### Constraints

**Budget:** $0 (uses existing sensors and hardware)

**Timeline:** 
- Epic 11 development: 2-3 weeks (5-8 story points)
- Production validation: Summer 2026 (first cooling season)

**Resources:**
- Dev agent: Story implementation and component creation
- Alberto: Physical validation during cooling season

**Technical:**
- KC868-A6 2MB flash limit (must stay <80%)
- Single mixing valve per floor (cannot do per-zone supply temp limiting)
- Humidity sensor accuracy: ±5% RH (Modbus sensors when deployed)

### Key Assumptions

1. **Humidity sensor availability:**
   - MVP: HA sensors available (Epic 5 mode)
   - Phase 2: Modbus sensors deployed (Story 1.6 hardware pending)

2. **Cooling mode detection:**
   - PID climate entities expose `action` attribute
   - Can detect `CLIMATE_ACTION_COOLING` reliably

3. **Supply temperature control:**
   - Mixing valve control is sufficient for dew point protection
   - 2°C safety margin is adequate (industry standard)

4. **Sensor accuracy:**
   - Room temperature: ±0.3°C (sufficient for dew point calc)
   - Room humidity: ±5% RH (acceptable error margin)

5. **Response time:**
   - 30-second update interval is fast enough
   - Humidity changes slowly (10+ minutes for significant shifts)

---

## Risks & Open Questions

### Key Risks

**1. Humidity Sensor Accuracy:**
- **Risk:** ±5% RH error could miscalculate dew point by ±1°C
- **Impact:** May limit cooling unnecessarily (comfort reduction) or under-protect (condensation risk)
- **Mitigation:** Use 2°C safety margin (industry standard), validate with reference hygrometer

**2. HA Dependency for Humidity (MVP):**
- **Risk:** MVP still depends on HA for humidity data (Epic 5 HA-only sensors)
- **Impact:** If HA fails, fallback to 70% RH assumption may over-limit cooling
- **Mitigation:** Conservative fallback, encourage Story 1.6 Modbus deployment

**3. Single Mixing Valve per Floor:**
- **Risk:** Cannot do per-zone supply temp limiting (all zones share one mixing valve)
- **Impact:** Most conservative zone (highest dew point) limits all zones
- **Mitigation:** Acceptable trade-off for safety, document in migration guide

**4. First Cooling Season Validation:**
- **Risk:** Cannot fully validate until summer 2026 (heating-only currently)
- **Impact:** Bugs or tuning issues discovered 6+ months post-deployment
- **Mitigation:** Intentional high-humidity testing (bathroom steam test), bench validation

### Open Questions

1. **Should we broadcast dew point via UDP (Epic 10 pattern), or use HA sensors?**
   - Option A: UDP broadcasting (follows Epic 9/10 architecture, autonomous)
   - Option B: HA sensor pass-through (simpler, but HA-dependent)
   - **Recommendation:** Option A for consistency and autonomy

2. **What humidity assumption for Tier 3 fallback (no sensors)?**
   - Conservative: 70% RH (safe but may over-limit)
   - Moderate: 60% RH (balanced)
   - Aggressive: 50% RH (maximizes cooling, slight condensation risk)
   - **Recommendation:** 70% RH for MVP, make configurable

3. **Should we limit cooling output gradually or hard-clamp supply temp?**
   - Gradual: PID output reduction as dew point approached (complex)
   - Hard clamp: Enforce minimum supply temp (simple, proven)
   - **Recommendation:** Hard clamp for MVP (simpler, safer)

4. **Do we need per-zone dew point sensors exposed to HA?**
   - Yes: Useful for diagnostics and humidity monitoring
   - No: Only aggregate max needed for limiting
   - **Recommendation:** Yes, expose all dew points (low overhead)

### Areas Needing Further Research

- ✅ Magnus-Tetens formula validation (compare to NOAA calculator)
- ✅ Humidity sensor accuracy specs for Modbus sensors (Story 1.6)
- ✅ UDP broadcasting pattern (Epic 9 sensors, Epic 10 binary sensors - proven architecture)
- ⏳ Industry best practices for dew point safety margins (2°C standard?)
- ⏳ ESPHome lambda performance impact (dew point calculation cost)
- ⏳ UDP sensor broadcast structure for float values (extend Epic 9 pattern to dew point)

---

## Story Breakdown (Preliminary)

### Story 12.1: Dew Point Calculator Component
**Effort:** 2 story points (~1 day)

**Tasks:**
- Implement Magnus-Tetens formula in ESPHome lambda
- Create `components/dew_point_calculator.yaml` with vars: zone_slug, temp_sensor, humidity_sensor
- Add per-zone dew point sensor (exposed to HA)
- Add 3-tier humidity failover (Modbus → HA → 70% fallback)
- Bench test with reference calculator

### Story 12.2: Dew Point Aggregator Component
**Effort:** 2 story points (~1 day)

**Tasks:**
- Create `components/dew_point_aggregator.yaml` for mixing group
- Receive per-zone dew points via UDP (Epic 10 pattern)
- Calculate max dew point across all active cooling zones
- Expose `sensor.max_dew_point_cooling_zones` to HA
- Add cooling zone filter (only zones with `action == COOLING`)

### Story 12.3: Supply Temperature Safety Limiter
**Effort:** 3 story points (~2 days)

**Tasks:**
- Create `components/supply_temp_safety_limiter.yaml`
- Intercept PID output in mixing group device
- Apply clamp: `supply_temp >= (max_dew_point + 2.0°C)` during cooling
- Add `binary_sensor.dew_point_limiting_active` (status indicator)
- Add `sensor.supply_temp_safety_minimum` (diagnostic)
- Log warnings when limiting is active

### Story 12.4: Integration and Testing
**Effort:** 2 story points (~1 day)

**Tasks:**
- Integrate components into distribution board device files
- Integrate components into mixing group device file
- Compilation validation (all devices <80% flash)
- Bench test with simulated high humidity (70-80% RH)
- HA restart test (verify autonomous protection)
- Create intentional condensation test plan (bathroom steam)

### Story 12.5: Documentation and Completion
**Effort:** 1 story point (~0.5 day)

**Tasks:**
- Epic 12 completion report
- Dew point protection guide (safety validation procedures)
- Migration guide (upgrade from Epic 10)
- Update `.github/copilot-instructions.md` with Epic 12 patterns
- Update architecture.md with dew point protection

**Total Effort:** 10 story points (~2 weeks)

---

## Dependencies

### Required Before Starting Epic 11

- ✅ **Epic 5:** HA-only sensors (temperature + humidity via HA)
- ✅ **Epic 8:** Condition interface pattern (reference for component design)
- ✅ **Epic 9:** UDP infrastructure (packet_transport platform for sensor broadcasts)
- ✅ **Epic 10:** UDP zone activity tracking (binary sensor UDP broadcasting pattern reference)

**Note on Epic 10:** Epic 10 implemented zone demand broadcasting (distribution boards → mixing group) but **deferred Story 10.1 (ESP32 room sensors with UDP)**. Epic 11's dew point protection uses the same UDP patterns but for humidity/dew point data instead of zone demand.

### Enables Future Epics

- **Story 10.1 (Deferred):** ESP32 room sensors via UDP (can build on Epic 11 humidity patterns)
- **Epic 12:** Weather-based cooling optimization (dew point trends)
- **Epic 13:** MEV coordination (increase air exchange when humid)
- **Epic 14:** Predictive humidity management (weather forecast integration)

### Optional (Enhances but Not Required)

- Story 1.6 Modbus hardware deployment (enables Tier 1 humidity sensors)
- Per-zone mixing valves (future hardware upgrade for zone-specific limiting)

---

## Appendices

### A. Dew Point Calculation Reference

**Magnus-Tetens Formula:**
```
T = Room temperature (°C)
RH = Relative humidity (%)

a = 17.27
b = 237.7°C
α = [(a × T) / (b + T)] + ln(RH/100)
Td = (b × α) / (a - α)
```

**Example:**
- T = 24°C, RH = 60% → Td = 15.8°C
- Safety minimum supply temp = 15.8°C + 2°C = **17.8°C**

**Validation:**
- Compare to NOAA online calculator: https://www.weather.gov/epz/wxcalc_dewpoint
- Accuracy: ±0.4°C across typical residential conditions

### B. Condensation Risk Matrix

| Room Temp | Humidity | Dew Point | Safe Supply Temp |
| --------- | -------- | --------- | ---------------- |
| 22°C      | 50%      | 11.1°C    | ≥13.1°C          |
| 24°C      | 60%      | 15.8°C    | ≥17.8°C          |
| 26°C      | 70%      | 20.2°C    | ≥22.2°C          |
| 28°C      | 80%      | 24.4°C    | ≥26.4°C (!) ⚠️    |

**Key Insight:** At 28°C + 80% RH, safe supply temp is 26.4°C → **Cooling effectiveness severely limited!**

**Mitigation:** Coordinate with MEV system to reduce humidity before aggressive cooling.

### C. Related Documentation

**Epic 5 HA-Only Sensors:**
- `docs/epic-5-completion-report.md` - Sensor architecture baseline
- `docs/epic-5-ha-only-sensors.md` - Temperature + humidity HA integration

**Epic 9 UDP Infrastructure:**
- `docs/epic-9-brief.md` - UDP broadcasting pattern for sensor data

**Epic 10 Zone Activity Tracking:**
- `docs/epic-10-completion-report.md` - UDP binary sensor broadcasting pattern
- **Note:** Epic 10 deferred Story 10.1 (ESP32 room sensors) to Epic 11+, focused on zone demand tracking only

**Story 1.6 Room Sensors:**
- `docs/stories/1.6.room-sensor-integration.md` - Modbus humidity sensors (hardware pending)
- `docs/sensor-technology-selection.md` - Humidity sensor specs

### D. Safety Standards Reference

**Industry Best Practices:**
- **ASHRAE Standard 55:** Thermal comfort and condensation prevention
- **CIBSE Guide A:** Environmental design guidance for radiant systems
- **Typical safety margin:** Dew point + 2-3°C (residential/commercial)

**Residential Safety Margin:**
- **2°C margin:** Standard for residential systems (Epic 12 MVP)
- **3°C margin:** Conservative for high-risk areas (bathrooms, laundry rooms)
- **1°C margin:** Aggressive (commercial buildings with active dehumidification)

---

**Epic 12 Status:** Draft - Deferred (Epic 11 takes priority)

**Next Steps:**
1. Complete Epic 11 first
2. Review and approve Epic 12 brief after Epic 11 completion
3. Create Story 12.1 (Dew Point Calculator Component)
4. Begin implementation (target: 2-3 week timeline)

---

**Document Version:** 1.0  
**Author:** Mary (Business Analyst)  
**Date:** November 24, 2025
