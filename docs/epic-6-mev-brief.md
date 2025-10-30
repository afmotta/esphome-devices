# Project Brief: MEV Board Integration for First Floor

**Epic:** 6 - MEV Board Integration  
**Version:** 1.0  
**Date:** October 30, 2025  
**Status:** Requirements Complete - Ready for Planning

---

## Executive Summary

This epic implements automated Mechanical Extract Ventilation (MEV) control for the first floor by adding a KC868-A6 ESPHome board to interface with a Cappellotto AIR FRESH I H EVO ventilation unit. The board exposes control entities (4 relays, 0-10V fan speed, alarm monitoring) to Home Assistant, which orchestrates autonomous humidity-based ventilation with air quality integration. The solution follows the established Epic 5 architecture pattern (HA-only sensors, exposed controls, autonomous operation if HA fails), integrating seamlessly with the existing 8 first-floor room sensors while maintaining the project's component-based, reusable design philosophy.

**Key Value:**
- Automated first-floor humidity control via centralized MEV system
- Air quality responsive ventilation (CO2/VOC sensors)
- Autonomous seasonal mode switching (winter/summer coordination)
- Alarm monitoring with HA notifications
- Hardware failure resilience (continues at last settings if HA disconnects)

---

## Problem Statement

### Current State and Pain Points

The first floor of the residence currently lacks automated ventilation control. The Cappellotto AIR FRESH I H EVO MEV system requires manual operation with no integration into the smart home automation. This creates several issues:

**Manual Control Limitations:**
- No humidity-based automatic activation
- No air quality response (CO2/VOC levels ignored)
- Manual seasonal mode switching (winter/summer)
- No visibility into system alarms or failures
- Occupant must remember to adjust ventilation

**Integration Gap:**
- 8 first-floor rooms already have temperature sensors (Epic 5)
- Room sensors could inform ventilation decisions but aren't connected
- Existing HA automation infrastructure can't control ventilation
- No coordination with heating/cooling system for optimal efficiency

**Comfort and Health Impact:**
- Inadequate ventilation when humidity rises (bathrooms, laundry)
- Poor air quality during high occupancy periods
- Energy waste from over-ventilation or running wrong seasonal mode
- Risk of condensation and mold from unmanaged humidity

### Why Existing Solutions Fall Short

**Manual Control:** The MEV unit has basic controls but no automation capability—requires constant occupant attention and adjustment.

**Standalone Smart Controllers:** Third-party ventilation controllers exist but:
- Don't integrate with existing ESPHome/HA infrastructure
- Can't leverage existing room sensors
- Require separate configuration and maintenance
- Lack the component-based reusability philosophy of this project

**Custom Integration:** Building MEV control into existing distribution boards would:
- Mix concerns (climate distribution vs. ventilation)
- Create tight coupling and complexity
- Make future MEV-only changes difficult

### Urgency and Importance

**Construction Timeline:** The house is under construction now (October 2025)—electrical planning for the MEV board must happen before walls close. Missing this window means retrofitting later at much higher cost.

**Health Priority:** Proper ventilation is critical for indoor air quality, particularly in bathrooms and sleeping areas. First floor includes 4 bedrooms and 3 bathrooms—high priority for humidity and air quality management.

**Architecture Consistency:** This epic establishes the pattern for mechanical systems integration (MEV, air conditioning, future systems), ensuring consistent design philosophy across the project.

---

## Proposed Solution

### Core Concept

Deploy a dedicated KC868-A6 ESPHome board mounted near the first-floor MEV unit, exposing all MEV controls as Home Assistant entities. The board acts as a hardware abstraction layer—no on-board logic, just clean interfaces. Home Assistant automation handles all intelligence: humidity-based fan speed calculation, seasonal mode switching, dehumidifier activation, and air quality response.

### Architecture Pattern

**Component-Based Design:**
- Reusable `components/mev.yaml` package (even though single instance initially)
- Device configuration: `devices/mev-primo-piano.yaml`
- Secrets/customization: `locals/mev-primo-piano.yaml`
- Remote config support: `remotes/mev-primo-piano.yaml`

**HA-Driven Control (Epic 5 Pattern):**
- Board exposes controls; HA orchestrates logic
- Sensors (humidity, CO2, VOC) sourced from HA
- Thermostat mode (heat/cool) sourced from HA for seasonal switching
- Autonomous operation: continues at last settings if HA connection lost

**Hardware Interface:**
- 4 Relay Outputs: Power, Winter/Summer mode, Dehumidifier, Cooling integration
- 1 Analog Output: DAC → 0-10V fan speed control (0-100%)
- 1 Analog Input: MEV alarm state (closed circuit = alarm condition)

### Key Differentiators

**Reusable Architecture:** Even for single device, component-based design enables:
- Easy addition of second MEV unit (ground floor, basement)
- Clean separation of concerns (board/component/device)
- Consistent patterns with rest of project

**HA Integration Excellence:**
- Leverages existing 8 first-floor room sensors (Epic 5)
- Coordinates with thermostat mode for seasonal optimization
- Notification system for alarm conditions
- Dashboard visibility and manual override capability

**Operational Resilience:**
- Autonomous operation if HA fails (continues last settings)
- No emergency shutdown (ventilation safer to continue than stop)
- Simple hardware abstraction = fewer failure modes

**Future-Proof Design:**
- Template for other mechanical systems (A/C units, heat pumps)
- Documented wiring and integration patterns
- Clean component interface for algorithm changes

---

## Target Users

### Primary User: Homeowner (System Operator)

**Profile:**
- Lives in three-floor residence with advanced climate control
- Technically capable (manages ESPHome/HA infrastructure)
- Values automation, efficiency, and indoor air quality
- Wants "set and forget" operation with monitoring capability

**Current Behaviors:**
- Actively manages ESPHome climate control system
- Monitors room temperatures via HA dashboards
- Performs system maintenance and updates
- Adjusts automation based on seasonal needs

**Needs and Pain Points:**
- Automatic humidity control without manual intervention
- Visibility into ventilation system status and alarms
- Integration with existing room sensors and automation
- Confidence that ventilation continues during HA maintenance

**Goals:**
- Maintain optimal indoor air quality automatically
- Reduce manual ventilation management
- Early warning of MEV system failures
- Efficient operation (right mode, right speed, right time)

### Secondary User: Home Assistant Automation

**Profile:**
- Software system orchestrating smart home functions
- Receives sensor data from multiple sources
- Executes automation rules based on conditions
- Provides dashboard interface and notifications

**Current Behaviors:**
- Monitors 8 first-floor room temperatures/sensors (Epic 5)
- Controls heating/cooling via PID climate entities
- Tracks thermostat mode (heat/cool/off) for coordination
- Sends notifications for system events

**Needs:**
- Clean entity interfaces to MEV controls
- Reliable state feedback from MEV board
- Sensor data from external humidity/air quality sensors
- Ability to override automatic control when needed

**Goals:**
- Optimize ventilation based on multi-sensor data
- Coordinate MEV operation with heating/cooling cycles
- Alert homeowner to alarm conditions
- Provide manual control interface via dashboard

---

## Goals & Success Metrics

### Business Objectives

- **Epic Completion:** MEV board operational and integrated by construction phase deadlines (Q4 2025)
- **Reusability:** Component architecture enables future MEV additions with <4 hours effort
- **Documentation Quality:** Complete wiring diagrams and integration guide for future reference
- **Zero Disruption:** Existing climate control system operates normally throughout implementation

### User Success Metrics

- **Automation Effectiveness:** MEV adjusts fan speed automatically based on humidity within 2 minutes of threshold crossing
- **Air Quality Response:** Fan speed increases when CO2/VOC levels exceed thresholds
- **Seasonal Accuracy:** Winter/Summer mode tracks thermostat mode with <5 minute lag
- **Alarm Notification:** HA notification delivered within 30 seconds of MEV alarm state
- **Uptime Resilience:** MEV continues operation at safe defaults during HA maintenance windows

### Key Performance Indicators (KPIs)

- **Entity Exposure:** 6 entities (4 switches, 1 number, 1 binary_sensor) visible in HA
- **Compilation Success:** ESPHome config compiles without errors, <60% flash usage, <15% RAM usage
- **Control Responsiveness:** Entity state changes reflected in hardware within 1 second
- **Documentation Completeness:** Wiring diagram covers all 6 connections (4 relays, 0-10V, alarm input)
- **Integration Testing:** All controls verified operational from HA dashboard

---

## MVP Scope

### Core Features (Must Have)

- **KC868-A6 Board Configuration:** Base hardware setup with WiFi/Ethernet connectivity to HA
- **Reusable MEV Component (`components/mev.yaml`):** Parameterized package accepting MEV-specific variables (relay IDs, DAC output, alarm input)
- **Device Configuration (`devices/mev-primo-piano.yaml`):** Complete device assembly including board + MEV component
- **4 Relay Controls:** Switches for Power, Winter/Summer mode, Dehumidifier, Cooling integration with friendly names
- **0-10V Fan Speed Control:** Number entity (0-100%) mapped to DAC output with proper voltage scaling
- **Alarm Input Monitoring:** Binary sensor reading MEV alarm state (closed circuit detection)
- **Wiring Diagram:** Detailed KC868-A6 → Cappellotto MEV connection schematic with pin mappings
- **HA Integration Guide:** Documentation for exposed entities, automation examples, testing checklist

### Out of Scope for MVP

- Home Assistant automation logic (user-implemented after board operational)
- Humidity/CO2/VOC sensor selection or installation (HA infrastructure concern)
- MEV unit physical installation and wiring (contractor responsibility)
- Performance tuning and optimization (deferred to operational phase)
- Multi-zone ventilation control (single centralized unit only)
- Advanced features (filter replacement tracking, energy monitoring, scheduling)

### MVP Success Criteria

**Functional Criteria:**
- ✅ Board compiles and flashes successfully
- ✅ All 4 relays toggle correctly from HA (verified with multimeter/visual)
- ✅ Fan speed control (0-100%) produces corresponding 0-10V output (verified with multimeter)
- ✅ Alarm input detects closed circuit and updates binary_sensor state in HA
- ✅ Entities have friendly names and appear in HA device registry under "MEV Primo Piano"
- ✅ Board continues operating at last settings when HA connection interrupted (5+ minute test)

**Documentation Criteria:**
- ✅ Wiring diagram includes all 6 connections with KC868-A6 pin numbers
- ✅ Integration guide explains entity purposes and provides automation examples
- ✅ Testing checklist covers all control verification steps

---

## Post-MVP Vision

### Phase 2 Features

**Enhanced Automation Intelligence:**
- Occupancy-based ventilation (increase when rooms occupied)
- Predictive humidity control (boost before showers/cooking based on schedule)
- Energy optimization (coordinate with electricity pricing, minimize when HVAC active)

**Advanced Monitoring:**
- Filter replacement tracking (hours-based or pressure sensor)
- Energy consumption monitoring (if MEV provides signal)
- Historical performance analytics (runtime, mode distribution, alarm frequency)

**Multi-Zone Support:**
- Per-room damper control (if zone-specific ventilation needed)
- Ground floor MEV addition (separate unit or shared control)

### Long-Term Vision

**Whole-Home Environmental Control:**
- Unified dashboard showing temperature, humidity, air quality, ventilation across all floors
- Coordinated HVAC + Ventilation strategies optimizing comfort and efficiency
- Predictive algorithms learning household patterns and preferences
- Integration with outdoor weather data for optimal fresh air intake timing

**Maintenance Intelligence:**
- Predictive maintenance alerts based on runtime and performance trends
- Integration with service scheduling systems
- Detailed diagnostics for troubleshooting without physical access

### Expansion Opportunities

- **Additional Mechanical Systems:** Apply same architecture to A/C units, heat pumps, air purifiers
- **Commercial Applications:** Multi-unit buildings, office spaces with centralized ventilation
- **Community Sharing:** Open-source component library for ESPHome/HA community

---

## Technical Considerations

### Platform Requirements

- **Target Platform:** ESPHome on KC868-A6 (ESP32-based)
- **Connectivity:** WiFi or Ethernet to Home Assistant
- **ESPHome Version:** Latest stable (2024.x or newer)
- **Home Assistant Version:** Compatible with homeassistant sensor platform (2024.x+)

### Technology Preferences

- **Framework:** `esp-idf` (matches existing board configurations)
- **Component Style:** YAML packages with `!include` and `vars` (established project pattern)
- **Board Base:** Reuse `boards/a6.yaml` (already defines RS485, I2C, PCF8574, etc.)
- **Variable Naming:** Follow existing conventions (`mev_slug`, `zone_name`, etc.)
- **Entity IDs:** Use template interpolation (`switch.${mev_slug}_power`, etc.)

### Hardware Interface Details

**DAC Output (0-10V Fan Speed):**
- KC868-A6 has built-in 0-10V DAC outputs (DAC_1/DAC_2)
- Direct connection to MEV fan speed input (no conversion needed)
- Linear control: 0V=0%, 10V=100%
- Document DAC configuration and pin mapping in wiring guide

**Relay Outputs:**
- Use PCF8574 expander relays (already configured in a6.yaml)
- Map 4 relays to: power, winter_summer, dehumidifier, cooling
- Note: PCF8574 relay IDs reused from existing board config

**Alarm Input:**
- Use PCF8574 input or GPIO direct (verify with existing board config)
- Closed circuit = alarm active (binary_sensor inverted logic if needed)
- Consider debounce timing for stable readings

### Architecture Considerations

**Repository Structure:**
```
components/
  mev.yaml              # Reusable MEV component
devices/
  mev-primo-piano.yaml  # Device assembly
locals/
  mev-primo-piano.yaml  # Secrets/substitutions
remotes/
  mev-primo-piano.yaml  # Remote config
docs/
  epic-6-mev-wiring-diagram.md
  epic-6-mev-integration-guide.md
```

**Component Interface (`components/mev.yaml`):**
```yaml
# Expected vars:
# - mev_slug: "mev_primo_piano"
# - mev_name: "MEV Primo Piano"
# - power_relay_id: ID of power relay
# - mode_relay_id: ID of winter/summer relay
# - dehumid_relay_id: ID of dehumidifier relay
# - cooling_relay_id: ID of cooling integration relay
# - fan_speed_dac: DAC output ID
# - alarm_input_id: Binary sensor input ID
```

**Security/Compliance:**
- WiFi credentials in `locals/secrets.yaml` (not committed)
- API encryption enabled (standard ESPHome practice)
- No external network access required (LAN-only operation)

---

## Constraints & Assumptions

### Constraints

**Budget:**
- KC868-A6 board: ~$50-70 USD
- Wiring materials: <$20 USD
- Total hardware cost: <$90 USD

**Timeline:**
- Construction phase: Q4 2025
- Epic completion target: Before drywall installation (exact date TBD with contractor)
- Implementation estimate: 2-3 user stories, 1-2 weeks elapsed time

**Resources:**
- Single developer (homeowner) with ESPHome expertise
- Access to MEV installation site during construction
- Existing ESPHome development environment and tools

**Technical:**
- KC868-A6 hardware fixed (already purchased/planned)
- Cappellotto MEV unit interface fixed (4 relays + 0-10V + alarm input)
- Must maintain compatibility with existing board architecture patterns
- Flash and RAM usage must stay within ESP32 limits (<80% each)

### Key Assumptions

- Cappellotto MEV wiring documentation accurate (per provided PDF)
- 0-10V fan speed control is linear (0V=0%, 10V=100%)
- KC868-A6 built-in 0-10V DAC outputs work reliably
- Alarm input is normally-open, closes on alarm condition
- Winter mode relay: closed=winter, open=summer (verify in MEV docs)
- Dehumidifier relay: closed=active, open=inactive (verify in MEV docs)
- Cooling integration relay: closed=active, open=inactive (verify in MEV docs)
- Home Assistant has access to humidity sensors (separate infrastructure)
- Home Assistant has access to air quality sensors (CO2/VOC - separate infrastructure)
- Existing thermostat mode entity available for seasonal switching
- WiFi/Ethernet connectivity stable at MEV installation location

---

## Risks & Open Questions

### Key Risks

**Risk 1: MEV Wiring Documentation Accuracy**
- **Description:** Relay polarity assumptions (closed=active vs. open=active) based on documentation interpretation.
- **Impact:** MEDIUM - Wrong assumption = MEV operates opposite of intended
- **Mitigation:** Verify relay behavior with MEV technical support before installation; test each relay function individually during commissioning; document actual behavior vs. expected

**Risk 2: Construction Timeline Coordination**
- **Description:** Board installation must happen before drywall; delays in epic completion could miss the window.
- **Impact:** MEDIUM - Late installation = expensive retrofitting
- **Mitigation:** Prioritize wiring diagram and board mounting plan early; coordinate with contractor for installation slot; prepare board config in advance for rapid deployment

**Risk 3: Alarm Input Electrical Characteristics**
- **Description:** Unknown whether alarm output is dry contact, open-collector, or voltage signal; unknown current levels.
- **Impact:** LOW-MEDIUM - Incorrect connection could damage board or provide unreliable readings
- **Mitigation:** Verify alarm output electrical specs in MEV documentation or with manufacturer; use appropriate input protection (resistor/optocoupler if needed)

### Open Questions

- **Q1:** What is the exact electrical specification of the MEV alarm output? (Dry contact vs. voltage signal, current capacity)
- **Q2:** Should the board have local override switches (physical buttons) for manual MEV control during HA outages?
- **Q3:** What should happen if WiFi/Ethernet connection lost: maintain last state indefinitely, or timeout to a safe default after X hours?
- **Q4:** Should there be visual indicators (LEDs) on the board showing MEV operational state?
- **Q5:** Is there a specific mounting location requirement (distance from MEV unit, environmental protection, accessibility)?
- **Q6:** Should the component expose additional diagnostic sensors (uptime, WiFi signal strength, error counts)?

### Areas Needing Further Research

- **KC868-A6 DAC Configuration:** Review existing board config for DAC_1/DAC_2 usage and pin mappings
- **Cappellotto MEV Integration Examples:** Search for existing HA/ESPHome integrations with Cappellotto units
- **Relay Polarity Verification:** Contact Cappellotto technical support to confirm relay control logic
- **Humidity Sensor Selection:** Determine which HA-integrated humidity sensors will feed MEV automation (separate from this epic but impacts testing)
- **Air Quality Sensor Integration:** Identify CO2/VOC sensors and HA integration approach (separate epic dependency)

---

## Next Steps

### Immediate Actions

1. **Review Existing A6 Config:** Examine `boards/a6.yaml` to understand available DAC outputs and relay IDs for MEV component design
2. **MEV Technical Verification:** Contact Cappellotto support to confirm relay control logic and alarm output specs
3. **Create Epic Branch:** `git checkout -b epic-6` from `epic-5` branch
4. **Draft Component Structure:** Outline `components/mev.yaml` variable interface based on hardware review

### Architect/PM Handoff

This Project Brief provides complete requirements and context for Epic 6: MEV Board Integration. Next steps:

**For Solution Architect:**
- Design `components/mev.yaml` interface and implementation
- Create detailed wiring diagram (KC868-A6 → Cappellotto MEV)
- Specify DAC output configuration (DAC_1 or DAC_2 selection)
- Define entity naming conventions and HA device registry structure
- Document Epic 6 architecture decisions

**For Product Manager (PRD Creation):**
- Break epic into user stories (suggest: Story 6.1 Board Config, Story 6.2 MEV Component, Story 6.3 Documentation)
- Define acceptance criteria for each story
- Prioritize open questions that block implementation
- Create testing checklist for commissioning phase
- Coordinate with construction timeline for installation window

**Key Context for Handoff:**
- This epic follows Epic 5 architecture (HA-only sensors, exposed controls, autonomous fallback)
- Reusable component design even for single device (establishes pattern for future MEV/mechanical systems)
- Board exposes controls; HA provides intelligence (clear separation of concerns)
- Construction deadline drives timeline—prioritize wiring diagram and mounting plan

---

**Epic 6 Project Brief - Complete**  
**Status:** Ready for Architecture Design & PRD Development  
**Next Agent:** Solution Architect → Product Manager → Scrum Master → Developer
