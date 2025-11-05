# Project Brief: ESPHome Multi-Floor Climate Control - Brownfield Enhancement

## Executive Summary

This project enhances an existing ESPHome-based residential climate control system managing a three-floor HVAC installation by implementing autonomous RS485 Modbus RTU communication between ESP32 boards. The enhancement eliminates Home Assistant as a single point of failure while maintaining full integration for monitoring and overrides. The system currently controls ground floor heating/cooling using Kincony KC868-A6 (mixing valve master) and KC868-A16 (zone distribution) boards but depends entirely on Home Assistant for sensor data and coordination. By implementing master/slave Modbus communication, adding one A16 board for first-floor distribution, and configuring a 0-10V adapter for second-floor fancoil control, the system will achieve complete three-floor coverage with autonomous operation during Home Assistant outages, faster response times through local decision-making, and improved ground floor cooling automation coordinating fancoils (primary) with optional floor cooling.

## Problem Statement

**Current State and Pain Points:**

The existing ESPHome climate control system effectively manages heating and cooling across a three-floor residential installation using proven PID algorithms and well-tuned control parameters. However, the system architecture creates a critical dependency: **Home Assistant failure equals complete system failure**. All temperature sensor data flows through Home Assistant's `homeassistant` platform, and climate mode coordination (heat/cool switching) requires HA orchestration. When Home Assistant experiences downtime—whether from updates, crashes, network issues, or maintenance—the entire HVAC system becomes non-functional, leaving the home without climate control.

**Impact of the Problem:**

- **Comfort Risk**: Loss of heating during winter or cooling during summer creates uncomfortable or unsafe living conditions
- **System Damage Risk**: Uncontrolled temperature fluctuations could damage the HVAC equipment or cause condensation/moisture issues
- **Operational Overhead**: Manual intervention required during HA maintenance windows to ensure climate control continues
- **Incomplete Coverage**: Two floors (first floor distribution and second floor fancoil) remain unimplemented, limiting the system's full potential
- **Suboptimal Cooling**: Ground floor has both fancoils (fast, humidity control) and floor cooling (slow, efficient) but lacks intelligent coordination between them

**Why Existing Solutions Fall Short:**

The current architecture was designed with Home Assistant as the central orchestrator, which worked well initially but revealed its weakness during the first HA update that required a restart. The existing Kincony boards already have RS485 UART hardware configured but unused—a capability that could enable board-to-board communication but requires significant architectural changes to implement properly.

**Urgency and Importance:**

This is an active production system in a residential environment. Solving this now is critical because:
- Winter heating season is approaching (October 2025)
- The proven PID tuning and control logic must be preserved during the transition
- Adding the remaining two floors requires this architectural foundation to be in place first
- The system's reliability directly impacts daily comfort and safety for the household

## Proposed Solution

**Core Concept:**

Implement RS485 Modbus RTU master/slave architecture transforming the system from centrally-orchestrated to autonomously-coordinated while maintaining full Home Assistant integration. The `gruppo-miscelazione` (KC868-A6) becomes the Modbus master, polling slave devices and exposing coordination data (climate mode, supply temperatures, control signals) via Modbus registers. The `distribuzione-piano-terra` (KC868-A16) ground floor slave and new first floor A16 slave read master registers for autonomous operation, with intelligent failover to Home Assistant sensors if Modbus communication fails.

**Key Differentiators:**

1. **Autonomous Operation**: Boards communicate directly via RS485 without Home Assistant mediation, continuing climate control during HA outages
2. **Intelligent Failover**: Three-tier sensor hierarchy (Modbus primary → HA fallback → emergency safe shutdown) ensures graceful degradation
3. **Zero PID Disruption**: Preserves all existing tuning parameters—only the data source changes, not the control algorithms
4. **Modular Deployment**: Per-board `use_modbus` flags allow gradual rollout and instant rollback without reflashing
5. **Industrial-Grade Communication**: Modbus RTU over RS485 (proven in HVAC for decades) vs. WiFi/cloud dependencies

**Why This Succeeds Where Others Haven't:**

- **Brownfield-Aware**: Explicitly designed to enhance existing working system without disruption
- **Hardware-Ready**: Leverages unused RS485 UART capability already present on Kincony boards
- **ESPHome Native**: Uses ESPHome's native `modbus_controller` platform—no custom C++ components required
- **Production-Tested Pattern**: Master/slave Modbus architecture is the industrial BMS standard

**High-Level Vision:**

Complete three-floor autonomous climate control system where:
- Master (A6) coordinates climate mode and shares sensor data
- Ground floor slave (A16) manages 4 zones + 4 fancoils + optional floor cooling with intelligent coordination
- First floor slave (A16) manages mixing valve + zone distribution
- Second floor fancoil controlled via 0-10V Modbus adapter from ground floor
- Home Assistant monitors and provides overrides but is no longer critical path
- System responds faster (local decisions, no HA round-trip) and more reliably (survives HA outages)

**Future Enhancement Opportunities:**

Once the autonomous Modbus foundation is established, the system opens doors to:
- **Learning Mode**: Track thermal response patterns and suggest PID optimizations as building characteristics change
- **Advanced Diagnostics**: Surface Modbus health metrics, equipment runtime tracking, and predictive maintenance alerts
- **Smart Inference**: Detect window-opening events or equipment failures using existing sensor patterns
- **Weather-Aware Preconditioning**: Proactive heating/cooling adjustments based on forecast data

## Target Users

### Primary User: System Owner/Maintainer

**Profile:**
- Technical homeowner with ESPHome expertise and active production climate control system
- Comfortable with YAML configuration, ESPHome CLI, and Home Assistant integration
- Values system reliability and resilience over bleeding-edge features
- Has already invested significant effort in PID tuning and system optimization

**Current Behaviors and Workflows:**
- Manages ESPHome configurations using Git version control (locals/ for dev, remotes/ for production)
- Compiles and deploys firmware via ESPHome CLI during development, Home Assistant ESPHome Builder addon for production OTA updates
- Monitors system performance via Home Assistant dashboards
- Performs manual intervention during Home Assistant maintenance windows to ensure climate control continuity

**Specific Needs and Pain Points:**
- **Reliability**: System must operate during HA downtime (updates, crashes, network issues)
- **Preservation**: Cannot afford to lose working PID tuning or disrupt active climate control
- **Maintainability**: Configuration changes must be manageable via YAML, not custom code
- **Rollback Safety**: Must be able to quickly revert if issues arise (especially critical during heating season)

**Goals:**
- Achieve "set and forget" reliability where system maintains comfort regardless of HA availability
- Complete three-floor coverage with first floor distribution and second floor fancoil
- Improve ground floor cooling intelligence (coordinate fancoils with optional floor cooling)
- Maintain ability to monitor and override via Home Assistant when desired

### Secondary User: Future ESPHome Community Members (Optional)

**Profile:**
- Advanced ESPHome users implementing multi-zone climate control
- Looking for production-grade patterns for autonomous HVAC operation
- May discover this implementation via GitHub or ESPHome community forums

**Needs:**
- Reusable component packages demonstrating Modbus master/slave patterns
- Documentation showing brownfield migration approach (not just greenfield)
- Reference architecture for industrial-grade failover strategies

**Note:** While not the primary focus of this project, the modular package-based architecture and comprehensive documentation could benefit the broader ESPHome community if shared.

## Goals & Success Metrics

### Business Objectives

- **System Uptime**: Achieve 99.9% climate control uptime regardless of Home Assistant availability (climate control continues during HA outages)
- **Response Time**: Reduce temperature control response time by eliminating Home Assistant round-trip delays (target: local Modbus decisions within 500ms vs. multi-second HA delays)
- **Coverage Completion**: Successfully expand system from 1 floor (ground) to 3 floors (ground + first + second) with autonomous coordination
- **Zero Regression**: Maintain existing ±0.5°C temperature control accuracy throughout migration (prove PID preservation works)
- **Safe Deployment**: Enable gradual rollout with instant rollback capability via per-board configuration flags (no firmware reflash required)

### User Success Metrics

- **Autonomous Operation Verified**: System successfully maintains climate control for 24+ hours during simulated Home Assistant outage
- **Failover Performance**: Automatic sensor failover (Modbus → HA → emergency) completes within 30 seconds with no temperature overshoot
- **Communication Reliability**: Modbus RTU communication maintains <1% error rate under normal operation across all boards
- **Deployment Success**: All three boards (1 master + 2 A16 slaves) upgraded via OTA without requiring physical access or USB flashing
- **Cooling Automation**: Ground floor fancoils activate within 30 seconds of cooling demand; floor cooling coordination transitions smoothly

### Key Performance Indicators (KPIs)

- **Modbus Communication Health**: <1% message error rate, 100% of slave polls complete within 500ms
- **Temperature Control Accuracy**: ±0.5°C from setpoint across all zones (maintain current performance standard)
- **Failover Speed**: Sensor source switching (Modbus failure → HA fallback) completes in ≤30 seconds
- **System Recovery**: Full system recovery from both Modbus and HA failures within 30 seconds of either service restoration
- **0-10V Control Accuracy**: Second floor fancoil responds within 2 seconds to setpoint changes via 0-10V Modbus adapter
- **Firmware Size**: Compiled firmware remains within ESP32 flash constraints (A6 and A16 current usage + Modbus implementation must fit)

## MVP Scope

### Core Features (Must Have)

- **Modbus Master/Slave Infrastructure**: Implement RS485 Modbus RTU communication between A6 master and A16 slaves with diagnostic sensors exposed to Home Assistant (communication status, error counts, last successful poll timestamps)

- **Master Coordination Data Exposure**: `gruppo-miscelazione` (A6 master) exposes Dallas temperature sensors and climate mode state via Modbus holding registers (16-bit, scaled by 100 for 0.01°C precision)

- **Slave Data Reading**: Ground floor A16 reads master registers for climate mode and coordination signals, updates every 10 seconds with timeout handling (sensor reports "unavailable" after 30 seconds)

- **Intelligent Sensor Failover**: Implement three-tier failover logic (Modbus primary → Home Assistant fallback → emergency safe shutdown after 5 minutes) with failover events logged and exposed as text sensors

- **First Floor A16 Board**: Add KC868-A16 slave (address 3) for first floor mixing valve control and zone distribution with local Dallas sensors and dual PID controllers reading climate mode from master

- **Second Floor 0-10V Fancoil Control**: Configure 0-10V Modbus adapter on ground floor A16 to control second floor fancoil with temperature-based PID regulation

- **Ground Floor Cooling Automation**: Implement intelligent coordination between fancoils (primary cooling) and floor cooling (optional/supplemental) with demand-based activation thresholds and humidity consideration (prefer fancoils when humidity >60%)

- **Gradual Rollout Support**: Per-board `use_modbus: true/false` configuration flag enabling Modbus functionality to be enabled/disabled without firmware reflash

- **PID Preservation**: All existing PID tuning parameters (kp, ki, kd values for heat/cool modes) preserved exactly as configured with zero changes to control algorithms

### Out of Scope for MVP

- Advanced scheduling/automation (remains Home Assistant's responsibility)
- Web UI on ESP32 devices (ESPHome/HA remains management interface)
- PID auto-tuning (current parameters are manually tuned and frozen)
- Energy monitoring/power consumption tracking
- Modbus TCP support (only Modbus RTU over RS485)
- Third-party Modbus device integration (system is ESPHome-only)
- Historical data logging on ESP32 (Home Assistant provides this)
- Advanced humidity control algorithms (basic measurement for fancoil prioritization only)
- Room sensor technology selection (deferred to implementation phase—will choose Modbus or 1-Wire based on cost/availability)

### MVP Success Criteria

**The MVP is considered successful when:**

1. All three boards (1 master + 2 A16 slaves) communicate reliably via Modbus with <1% error rate
2. System continues climate control for 24+ hours during simulated Home Assistant outage
3. Temperature control accuracy remains ±0.5°C across all zones (no degradation from current performance)
4. Failover between sensor sources (Modbus/HA/emergency) completes within 30 seconds
5. Ground floor cooling automation coordinates fancoils and floor cooling without rapid cycling (5-minute minimum stability)
6. Second floor fancoil responds to temperature changes via 0-10V control within 2 seconds
7. All boards can be upgraded via OTA without physical access
8. Configuration flag allows instant rollback to HA-dependent mode without reflashing

## Post-MVP Vision

### Phase 2 Features

Once the autonomous Modbus foundation is proven stable:

- **Room-Level Temperature and Humidity Sensors**: Deploy temperature/humidity sensors in each controlled zone (technology selection: Modbus sensors vs. 1-Wire + I2C/humidity sensors) to enable room-based PID control instead of supply-temperature-only control

- **Enhanced Diagnostics and Monitoring**: Comprehensive quality gate documentation, Modbus register maps, sensor technology selection rationale, RS485 wiring guides, and Home Assistant monitoring dashboard showing communication health and failover status

- **Learning Mode for PID Optimization**: Track thermal response patterns over time and suggest PID tuning adjustments as building characteristics change (seasonal variations, insulation improvements, window replacement)

- **Weather-Aware Preconditioning**: Integrate weather forecast data (via Home Assistant) to proactively adjust heating/cooling before temperature swings occur, reducing energy consumption and improving comfort

### Long-Term Vision (1-2 Years)

- **Occupancy-Based Zone Control**: **Note: Occupancy control will be implemented as Home Assistant automations, not ESPHome components.** Integrate presence sensors (PIR, mmWave, or HA-based) to reduce heating/cooling in unoccupied zones with "vacation mode" for extended absence. HA automations will monitor occupancy sensors and control climate entities directly (force OFF for fancoils, adjust setpoints for radiant systems).

- **Energy Cost Optimization**: Track electricity/gas costs per zone and optimize cooling strategy (fancoil vs. floor cooling) for cost efficiency, not just comfort, with time-of-use rate awareness

- **Advanced Humidity Management**: Dedicated dehumidification mode (cooling + air movement without overcooling) to prevent mold/condensation, moving beyond basic humidity monitoring to active humidity PID control

- **Backup Master Capability**: Implement failover where if master (A6) fails, a designated slave (A16) can assume coordination role, eliminating the master as a single point of failure

### Expansion Opportunities

- **Community Contribution Package**: Document and package the entire solution as a reusable "ESPHome Climate Control Suite" with installation guide, contributing production-grade patterns back to the ESPHome community

- **Modular HVAC Extensions**: Extend the master/slave architecture to manage additional subsystems (pool heating, greenhouse climate control, garage heating) using the same Modbus infrastructure

- **Thermal Comfort Score Control**: Move beyond raw temperature control to a multivariate "comfort score" combining temperature, humidity, and air movement (fancoil speed) based on comfort research

- **Smart Inference Features**: Detect window-opening events (sudden temperature drops), identify equipment failures (heating active but temperature not rising), and infer occupancy patterns from temperature recovery speeds—all without additional hardware

## Technical Considerations

### Platform Requirements

- **Target Platforms**: ESP32-based Kincony KC868 boards (A6 and A16 models)
- **Communication Protocols**: 
  - RS485 UART for Modbus RTU (9600 baud, 8N1 format)
  - WiFi/Ethernet for Home Assistant API integration (A6 via W5500 adapter, A16 native Ethernet)
  - I2C for PCF8574 GPIO expanders and RTC
  - 1-Wire for Dallas DS18B20 temperature sensors
- **Performance Requirements**: 
  - Modbus communication response time ≤500ms
  - Master polling cycle completes within 500ms for both A16 slaves
  - Sensor failover transitions complete within 30 seconds
  - 0-10V control response within 2 seconds

### Technology Preferences

- **Framework**: ESPHome (latest stable version, ≥2023.x with `modbus_controller` platform support)
- **ESP32 Framework**: ESP-IDF (configured via `esp32.framework.type: esp-idf`)
- **Communication**: Modbus RTU over RS485 (master/slave architecture, no Modbus TCP or mesh)
- **Configuration**: YAML-based ESPHome configuration DSL (prefer native components over custom C++)
- **Deployment**: 
  - Development: ESPHome CLI with `locals/` directory (absolute paths)
  - Production: Home Assistant ESPHome Builder addon with `remotes/` directory (GitHub package references via `!include`)
- **Version Control**: Git/GitHub for configuration management and remote package hosting
- **Hardware**: 
  - RS485: Twisted-pair shielded cable, proper termination resistors, <50m total cable runs
  - Temperature: Dallas DS18B20 sensors (supply temperature monitoring)
  - GPIO Expansion: PCF8574 I2C expanders for relay/input expansion

### Architecture Considerations

- **Repository Structure**: 
  - `boards/` — Hardware-specific base configurations (a6.yaml, a16.yaml, a16_first_floor.yaml)
  - `components/` — Reusable functional packages (dual_pid.yaml, modbus_master.yaml, modbus_slave.yaml, modbus_0_10v.yaml, cooling_automation.yaml)
  - `devices/` — Device-specific assemblies combining boards + components
  - `locals/` — Development configs with absolute paths
  - `remotes/` — Production configs with GitHub package references

- **Service Architecture**: 
  - Master/slave Modbus with deterministic addressing (A6=1, Ground A16=2, First A16=3)
  - Master polls slaves every 10 seconds
  - Slaves never initiate communication (strict master/slave discipline)

- **Integration Requirements**: 
  - Full backward compatibility with existing Home Assistant entities (identical entity IDs)
  - Preserve existing PID tuning parameters exactly
  - RS485 UART pin assignments must remain as currently configured (A6: TX=GPIO27/RX=GPIO14; A16: TX=GPIO13/RX=GPIO16)
  - W5500 Ethernet adapter GPIO assignments on A6 must be preserved

- **Security/Compliance**: 
  - Secrets (WiFi passwords, API keys, OTA passwords) managed via `secrets.yaml` (gitignored)
  - No cloud dependencies for climate control operation (Home Assistant is local)
  - System must fail safe (emergency mode shuts down heating/cooling, not leaves it running)

### Firmware Constraints

- **Flash Size**: Compiled firmware must remain within ESP32 flash capacity (current usage + Modbus implementation + room sensors)
- **Memory**: Aggressive use of `internal: true` for entities not needed in Home Assistant to reduce entity overhead
- **Modbus Register Map**: Standard 16-bit holding registers, temperature values scaled by 100 (0.01°C precision)
- **Failover Logic**: Three-tier sensor hierarchy implementation using ESPHome `template` sensors

## Constraints & Assumptions

### Constraints

- **Budget**: Hardware cost limited to one KC868-A16 board (~$50-80) plus 0-10V Modbus adapter (~$20-30), RS485 cabling/termination (~$20), and room sensors (cost TBD based on technology selection)

- **Timeline**: Implementation must be completed before winter heating season (target: November 2025) to avoid disrupting climate control during peak demand period

- **Resources**: Solo implementation by system owner with ESPHome expertise; no team support or dedicated QA resources available

- **Technical**: 
  - ESP32 flash memory finite—firmware size must stay within current partition constraints
  - RS485 bus limited to <50m total cable length across all devices
  - Existing PID tuning cannot be modified (brownfield constraint—months of tuning investment)
  - W5500 Ethernet adapter GPIO assignments on A6 are fixed (cannot be reassigned)
  - Must maintain production system operation throughout migration (no extended downtime acceptable)

### Key Assumptions

- RS485 bus wiring can be installed in master/slave topology with cable runs <50m total (wiring path feasibility confirmed)

- Current Home Assistant installation will remain available for monitoring and overrides (not being replaced, just made non-critical for operation)

- ESPHome will continue to support Modbus RTU master/slave roles in future versions (community commitment to industrial protocols)

- Current PID tuning is optimal and doesn't need adjustment during migration (thermal characteristics haven't changed)

- Dallas DS18B20 temperature sensors are sufficiently responsive for supply temperature PID control (no need for faster sensors)

- First floor mixing valve hardware (relays, Dallas sensors, actuator) and wiring infrastructure are available or can be procured

- Second floor fancoil can be controlled via 0-10V signal from ground floor A16's Modbus adapter (wiring path exists)

- Room temperature/humidity sensors (either Modbus or 1-Wire) can be physically installed in each controlled zone without extensive construction work

- Room sensor technology selection (Modbus vs 1-Wire) can be finalized during implementation phase based on cost, availability, and technical considerations

- Testing can be performed during moderate weather conditions (not during temperature extremes) to minimize risk to comfort/safety

- OTA firmware updates will work reliably for production deployment (no physical USB access required)

- Modbus communication at 9600 baud is sufficient for polling 2-3 slaves every 10 seconds (bandwidth adequate)

## Risks & Open Questions

### Key Risks

- **Modbus Communication Instability**: RS485 bus electrical issues (ground loops, inadequate termination, cable quality) could cause intermittent communication failures disrupting control loops
  - **Impact**: High—unreliable Modbus defeats the entire autonomous operation goal
  - **Mitigation**: Start with short cable runs during testing, use twisted-pair shielded cable, document proper termination, implement comprehensive diagnostic sensors

- **Breaking Existing PID Control**: Refactoring sensor data sources could inadvertently change control loop behavior even if tuning parameters preserved
  - **Impact**: Critical—loss of comfort or system instability during heating season
  - **Mitigation**: Implement Modbus sensors alongside HA sensors initially for A/B testing, gradual rollout with `use_modbus` flag, extensive validation before full deployment

- **Firmware Size Exceeding Flash Capacity**: Adding Modbus components, room sensors, and diagnostics may exceed ESP32 available flash memory
  - **Impact**: Medium—would require partition table changes or feature cuts
  - **Mitigation**: Monitor compiled firmware size throughout development, use `internal: true` aggressively, consider partition table adjustment if needed

- **Deployment During Heating Season**: Firmware update bricking device during cold weather creates immediate comfort/safety issue
  - **Impact**: High—loss of heating in winter is unacceptable
  - **Mitigation**: Deploy during moderate weather, stage rollout one device at a time, keep USB cables ready for emergency serial flashing, maintain previous working firmware binaries

- **Room Sensor Technology Selection Impact**: Choosing Modbus vs 1-Wire affects system architecture, cost, and polling cycle performance
  - **Impact**: Medium—wrong choice could require significant rework
  - **Mitigation**: Design sensor abstraction layer supporting multiple technologies, test both approaches in development, document trade-offs clearly

- **0-10V Wiring Distance Limitation**: Analog 0-10V signal from ground floor to second floor may be susceptible to noise or voltage drop over distance
  - **Impact**: Medium—poor fancoil control on second floor
  - **Mitigation**: Use shielded cable, test signal integrity before full deployment, consider backup plan of dedicated board if 0-10V proves unreliable

### Open Questions

- **Room sensor technology**: Modbus temperature/humidity sensors vs. 1-Wire temperature + I2C humidity sensors—which offers better cost/performance trade-off?

- **Modbus register addressing strategy**: Static register map vs. dynamic discovery—how to balance simplicity with extensibility?

- **RS485 termination**: Terminate at master + last slave, or at both physical bus ends—what's the actual cable topology?

- **Failover timing optimization**: Is 30-second failover window too slow, too fast, or just right for comfort maintenance?

- **Home Assistant entity preservation**: Will identical entity IDs be sufficient, or do attributes/state also need exact matching?

- **0-10V adapter configuration**: Which specific 0-10V Modbus adapter model/protocol will be used, and is it already available?

- **Testing without disruption**: How to comprehensively test autonomous operation without actually bringing down Home Assistant in production?

### Areas Needing Further Research

- **ESPHome Modbus implementation stability**: Review community forums/GitHub issues for known bugs or limitations with `modbus_controller` platform at scale

- **Dallas sensor response time characterization**: Measure actual temperature update frequency to confirm it meets PID control loop timing requirements

- **RS485 bus loading**: Calculate theoretical maximum Modbus message rate with 2-3 slaves at 9600 baud to confirm 10-second polling interval is conservative

- **PCF8574 I2C + Modbus UART coexistence**: Verify no conflicts between I2C GPIO expanders and UART Modbus on same ESP32 (different buses, should be fine)

- **Room sensor placement optimization**: Research HVAC best practices for sensor placement to get representative room temperature readings (avoid drafts, direct sunlight, etc.)

- **Emergency mode behavior validation**: Define exact behavior during "both Modbus and HA failed" scenario—what's safest for system and building?

## Appendices

### A. Research Summary

**Existing Documentation Analysis:**
- **PRD Available**: Comprehensive Product Requirements Document (v1.0, October 9, 2025) detailing functional requirements, non-functional requirements, compatibility requirements, and technical constraints
- **Architecture Documentation**: To be created via `*document-project` task—current system lacks formal architecture documentation
- **Component Documentation**: Existing YAML configurations in `boards/`, `components/`, and `devices/` directories provide implicit architectural patterns

**Technical Feasibility:**
- **ESPHome Modbus Support**: Native `modbus_controller` platform available in ESPHome ≥2023.x versions with proven community usage
- **Hardware Capability**: Kincony KC868-A6 and KC868-A16 boards have RS485 UART hardware pre-configured but currently unused
- **Industrial Precedent**: Master/slave Modbus RTU over RS485 is the proven standard for industrial BMS (Building Management Systems) with decades of reliability data

**Competitive Analysis:**
- Commercial BMS solutions (Siemens Desigo, Honeywell EBI): Demonstrate master/slave autonomous operation as industry best practice
- ESPHome community projects: Multiple successful implementations of Modbus for pool control, greenhouse automation validate technical approach
- Home automation controllers: Critical infrastructure systems universally avoid single-point-of-failure dependencies

### B. Stakeholder Input

**Primary Stakeholder** (System Owner):
- Confirmed critical pain point: Home Assistant downtime = complete climate control failure
- Validated timing urgency: Winter heating season approaching, deployment must complete by November 2025
- Approved hardware approach: One A16 board + 0-10V adapter is cost-effective vs. two dedicated boards
- Emphasized preservation requirement: Cannot lose existing PID tuning investment

### C. References

- **ESPHome Documentation**: https://esphome.io/components/modbus_controller.html
- **Kincony KC868-A6**: https://devices.esphome.io/devices/KinCony-KC868-A6
- **Kincony KC868-A16**: https://devices.esphome.io/devices/KinCony-KC868-A16
- **Existing PRD**: `docs/prd.md` (ESPHome Multi-Floor Climate Control - Brownfield Enhancement PRD v1.0)
- **Project Repository**: GitHub repository with existing `boards/`, `components/`, `devices/` configurations

## Next Steps

### Immediate Actions

1. **Run `*document-project` task** to create comprehensive brownfield architecture documentation capturing current system state, technical constraints, and implementation patterns

2. **Procure hardware**: Order one KC868-A16 board for first floor, 0-10V Modbus adapter, RS485 cabling and termination resistors, plan room sensor procurement after technology selection

3. **Review PRD with PM agent** to create detailed implementation stories, epics, and acceptance criteria based on this project brief

4. **Set up development environment**: Prepare `locals/` test configurations with Modbus components for iterative testing in non-production environment

5. **Research sensor technology options**: Evaluate Modbus temperature/humidity sensors vs. 1-Wire + I2C alternatives (cost, wiring complexity, polling performance)

6. **Validate RS485 wiring paths**: Physically confirm cable routing from master to both slave locations is feasible within <50m constraint

### PM Handoff

This Project Brief provides the full context for **ESPHome Multi-Floor Climate Control - Brownfield Enhancement**. The comprehensive PRD (`docs/prd.md`) already exists with detailed functional requirements, epics, and stories.

**Next Phase**: Architecture creation and epic/story refinement. The PM should:
- Review this brief alongside the existing PRD
- Work with Architect to create detailed architecture documentation (via `*document-project` task)
- Refine epic and story acceptance criteria based on architectural decisions
- Coordinate with QA for risk profiling on high-risk stories (Modbus implementation, PID preservation, failover logic)
