---
workflowType: 'prd'
workflow: 'edit'
classification:
  domain: 'iot_embedded'
  projectType: 'iot_embedded'
  complexity: 'medium'
inputDocuments: []
lastEdited: '2026-02-15'
editHistory:
  - date: '2026-02-15'
    changes: 'Added Executive Summary, User Journeys, YAML frontmatter. Fixed filler, leakage, FR numbering. Note: §1-§3 hardware/architecture descriptions outdated.'
---

# ESPHome Multi-Floor Climate Control - Brownfield Enhancement PRD

## Executive Summary

This project delivers a **production residential climate control system** for a three-floor building in Milan, Italy, built on ESPHome with full autonomous operation independent of Home Assistant.

**The system** manages 13 temperature zones across 3 floors with dual-mode operation (radiant floor heating/cooling + fancoil units), PID-controlled precision, and intelligent seasonal mode management.

**Architecture:** A single ESP32-S3 POE climate controller runs all PID logic and zone coordination. 14 room sensor boards (ESP32-C3) broadcast temperature, humidity, CO2, and air quality data via UDP packet transport. Modbus RS485 extends the controller's I/O capacity through peripheral relay boards, analog output boards, and a MEV ventilation unit.

**Resilience:** A 3-tier sensor failover ensures continuous operation: Home Assistant sensors (primary), UDP packet transport (fallback), and emergency safe shutdown. The system operates autonomously — Home Assistant enhances monitoring and overrides but is not required for climate control.

**Key differentiator:** Unlike typical HA-dependent ESPHome setups, this system treats Home Assistant as optional. Local PID control, direct UDP sensor data, and Modbus I/O expansion provide full climate management without any cloud or server dependency.

---

## Document Information

| Field               | Value                                      |
| ------------------- | ------------------------------------------ |
| **Project**         | ESPHome Multi-Floor Climate Control System |
| **PRD Version**     | 1.2                                        |
| **Date**            | October 23, 2025                           |
| **Status**          | Draft                                      |
| **Target Audience** | Experienced ESPHome Users                  |

### Change Log

| Date       | Version | Description                                                                                      | Author                  |
| ---------- | ------- | ------------------------------------------------------------------------------------------------ | ----------------------- |
| 2025-10-09 | 1.0     | Initial brownfield PRD for RS485 Modbus board-to-board communication and automation enhancements | Mary (Business Analyst) |
| 2025-10-17 | 1.1     | Removed ground floor cooling automation from Epic 1 - deferred to future phase                   | Mary (Business Analyst) |
| 2025-10-23 | 1.2     | Added Epic 4: Room-Based Component Architecture refactoring                                      | Mary (Business Analyst) |
| 2026-02-15 | 1.3     | Added Executive Summary, User Journeys, YAML frontmatter. Fixed filler, leakage, FR numbering. Note: §1-§3 outdated. | John (PM - Edit Workflow) |

---

> **⚠ OUTDATED SECTIONS NOTICE:** Sections 1 through 3 below describe the system as of October 2025. The architecture has evolved significantly through Epics 15-19. Key differences: (1) Board-to-board sensor sharing now uses UDP packet transport, not Modbus RS485. (2) Modbus is used only for peripheral I/O expansion (relay boards, analog outputs, MEV). (3) The main controller is a WaveShare ESP32-S3-POE, not KC868-A6/A16. (4) 14 room sensor boards (S1-Pro-Multi-Sense, ESP32-C3) provide per-zone environmental data. See the Executive Summary for current architecture. A full PRD refresh is recommended.

## 1. Intro Project Analysis and Context

### 1.1 Existing Project Overview

#### Analysis Source
- **Type**: IDE-based fresh analysis
- **Context**: Working with existing ESPHome device configurations in `/Users/alberto/src/esphome-devices`
- **Documentation Status**: No existing architecture documentation - will be documented separately via document-project task

#### Current Project State

This is an **active production ESPHome-based home climate control system** managing a three-floor residential HVAC installation with the following characteristics:

**Current Coverage:**
- **Ground Floor (Piano Terra)**: Floor heating + 4 fancoils (primary cooling) + floor cooling (optional)
- **First Floor (Primo Piano)**: Floor heating + floor cooling (NOT YET IMPLEMENTED - needs new A16 board)
- **Second Floor (Secondo Piano)**: Single fancoil (NOT YET IMPLEMENTED - needs 0-10V Modbus adapter on ground floor A16)

**Current Hardware:**
- **Kincony KC868-A6 Board** (6 relays, 6 inputs): Used in `gruppo-miscelazione` device for mixing valve control
  - Off-the-shelf board from Kincony (https://devices.esphome.io/devices/KinCony-KC868-A6)
  - Ethernet connectivity added via W5500 adapter connected to free GPIOs
  - Controls 1 mixing valve (Ground Floor circuit only)
  - Has RS485 UART configured but not actively used
  - Uses Dallas temperature sensors for supply temperature monitoring
- **Kincony KC868-A16 Board** (16 relays, 16 inputs): Used in `distribuzione-piano-terra` device for ground floor zone distribution
  - Off-the-shelf board from Kincony (https://devices.esphome.io/devices/KinCony-KC868-A16)
  - Controls 4 zone circuits via slow PWM (Soggiorno, Cucina, Bagno, Anticamera)
  - Controls 4 fancoils for primary cooling
  - Has 0-10V Modbus adapter capability for remote fancoil control (second floor)
  - Currently relies on Home Assistant for temperature sensor data
  - No RS485 communication configured

**Current Control Architecture:**
- **PID Controllers**: Dual PID controllers (heat/cool modes) for precise temperature control
- **Home Assistant Dependency**: Heavy reliance on HA for:
  - Temperature sensor data (via `homeassistant` platform)
  - Climate mode coordination (heat/cool mode switching)
  - Overall system orchestration
- **Single Point of Failure**: Home Assistant failure = system failure

**Deployment Model:**
- **`locals/` directory**: Development phase - direct firmware builds and flashing
- **`remotes/` directory**: Production phase - ESPHome Builder addon in Home Assistant references GitHub packages
- **Package-based architecture**: Modular configuration using `!include` for boards, components, and device-specific configs

### 1.2 Documentation Analysis

#### Available Documentation
- ☐ Tech Stack Documentation
- ☐ Source Tree/Architecture
- ☐ Coding Standards
- ☐ API Documentation
- ☐ External API Documentation
- ☐ UX/UI Guidelines
- ☐ Technical Debt Documentation

**Recommendation**: Run the `*document-project` task after this PRD is finalized to create comprehensive architecture documentation capturing the actual system structure, patterns, and technical constraints.

### 1.3 Enhancement Scope Definition

#### Enhancement Type
- ☑ **New Feature Addition** - RS485 Modbus board-to-board communication
- ☑ **Major Feature Modification** - Decentralize control logic from Home Assistant to ESPHome
- ☑ **Integration with New Systems** - Direct ESP32-to-ESP32 communication via Modbus
- ☑ **Bug Fix and Stability Improvements** - Eliminate single point of failure
- ☐ **Performance/Scalability Improvements**
- ☐ **Technology Stack Upgrade**
- ☐ **UI/UX Overhaul**

#### Enhancement Description

This enhancement **transforms the system from Home Assistant-dependent to autonomous** via master/slave board communication over RS485 Modbus RTU protocol. The system will gain the ability to operate independently during Home Assistant outages while maintaining full integration when HA is available. One additional board will be added to complete the system coverage of all three floors.

#### Impact Assessment
- ☐ Minimal Impact (isolated additions)
- ☐ Moderate Impact (some existing code changes)
- ☑ **Significant Impact** (substantial existing code changes)
- ☐ Major Impact (architectural changes required)

**Rationale**: While the core PID control logic remains unchanged, the data flow architecture must be substantially modified to:
1. Replace Home Assistant sensor dependencies with local sensors and Modbus data exchange
2. Implement Modbus server/client roles across boards
3. Add board discovery and failover logic
4. Maintain backward compatibility with Home Assistant integration

### 1.4 Goals and Background Context

#### Goals
- Eliminate Home Assistant as a single point of failure for climate control operations
- Enable master/slave board communication using RS485 Modbus RTU protocol with `gruppo-miscelazione` as master
- Add one new A16 board to complete three-floor coverage (First Floor zone distribution)
- Implement 0-10V Modbus adapter control for second floor fancoil via first floor A16
- Implement autonomous temperature sensor data sharing from master to slave boards
- Maintain full Home Assistant integration for monitoring, overrides, and advanced automation
- Improve system resilience and response time through local decision-making
- Preserve existing PID control algorithms and tuning parameters

#### Background Context

The current system has proven effective for climate control but suffers from critical weaknesses:
1. **Single Point of Failure**: Complete dependency on Home Assistant for sensor data and mode coordination
2. **Incomplete Coverage**: First floor distribution and second floor fancoil not yet implemented

When Home Assistant experiences downtime (updates, crashes, network issues), the entire climate control system becomes non-functional, potentially leading to uncomfortable conditions or system damage.

The existing A6 and A16 boards already have RS485 UART hardware configured but unused. By implementing Modbus RTU master/slave protocol with `gruppo-miscelazione` as the master controller, slave boards can receive temperature sensor data and coordination signals autonomously. This architecture change will allow the system to:
1. Continue operating during HA outages using master-coordinated sensor data and control signals
2. Respond faster to temperature changes without HA round-trip delays
3. Complete the three-floor system with one additional A16 board (first floor) and 0-10V Modbus adapter (second floor fancoil)
4. Maintain the proven PID control algorithms that have been tuned for the specific heating/cooling zones

The enhancement must be implemented carefully to preserve the existing working configuration while adding the new communication layer, ensuring a safe rollback path if issues arise.

---

## User Journeys

### UJ1: Homeowner — Set-and-Forget Climate Comfort

**User:** Residential occupant across 3 floors
**Goal:** Comfortable living environment with zero daily intervention

**Primary Flow:**
1. Homeowner sets desired temperature per zone once via Home Assistant dashboard
2. System maintains target temperature automatically across seasons (heat/cool mode transitions handled by seasonal mode logic)
3. Homeowner occasionally checks HA dashboard to verify room conditions (temperature, humidity, air quality)
4. If a room feels uncomfortable, homeowner adjusts setpoint via HA — system responds within minutes

**Key Expectations:**
- Temperature held within ±0.5°C of setpoint without manual intervention
- Seasonal transitions (heat ↔ cool) happen automatically based on calendar and demand
- System continues working during HA outages — no manual fallback needed
- Air quality (CO2, IAQ) monitored and ventilation adjusted automatically via MEV

**Related FRs:** FR1-FR5 (Modbus I/O), FR7 (failover), FR9 (PID preservation), FR10 (HA compatibility)

---

### UJ2: System Administrator — Parameter Tuning for Comfort Optimization

**User:** Technical owner maintaining the ESPHome system
**Goal:** Fine-tune system parameters to improve comfort across zones

**Primary Flow:**
1. Administrator monitors zone performance via HA dashboards (PID output, sensor tiers, temperature tracking)
2. Identifies zone with suboptimal comfort (overshoot, slow response, oscillation)
3. Adjusts PID parameters (Kp, Ki, Kd) or zone configuration via ESPHome YAML
4. Deploys updated firmware via OTA (local development) or HA ESPHome addon (production)
5. Monitors results and iterates

**Secondary Flows:**
- Adding new room sensors: Deploy new S1-Pro board, configure UDP broadcast, add room package to climate controller
- Diagnosing issues: Check ESPHome logs, sensor tier status, Modbus diagnostics in HA
- Seasonal adjustments: Modify seasonal mode calendar dates or transition thresholds

**Key Expectations:**
- All diagnostic data (PID terms, sensor sources, failover events) visible in HA
- Configuration changes via YAML without custom low-level code (FR12)
- OTA updates work reliably without physical device access
- Modular room components — changes to one zone don't affect others

**Related FRs:** FR9 (PID preservation), FR10 (HA compatibility), FR11 (diagnostics), FR12 (configuration)

---

### UJ3: System — Autonomous Operation and Failover

**User:** The climate control system operating without human intervention
**Goal:** Maintain safe, comfortable conditions regardless of external system availability

**Primary Flow (Normal Operation):**
1. Room sensors broadcast temperature, humidity, CO2, IAQ via UDP every 10 seconds
2. Climate controller receives sensor data, evaluates 3-tier failover (HA → UDP → Emergency)
3. PID controllers compute output for each zone based on setpoint and current temperature
4. Outputs drive zone valves (Modbus relays), mixing valves (Modbus 0-10V), and fancoils (Modbus 0-10V)
5. Mixing valve PIDs maintain supply water temperature based on zone demand
6. Seasonal mode logic manages heat/cool transitions based on calendar and demand signals

**Failover Flow:**
1. Home Assistant becomes unavailable → system detects HA sensor NaN
2. Failover tier switches from "HA" to "UDP" — PID controllers continue with UDP sensor data
3. All climate control continues uninterrupted
4. When HA recovers → automatic switch back to HA tier

**Emergency Flow:**
1. Both HA and UDP sensors become unavailable → sensor reports NaN
2. PID controllers fail-safe (stop heating/cooling output)
3. Zone valves close, pumps stop — system enters safe shutdown
4. When sensors recover → automatic restart of climate control

**Related FRs:** FR7 (failover), FR8 (autonomous mode switching), FR9 (PID preservation), FR13 (polling)

---

## 2. Requirements

### 2.1 Functional Requirements

**FR1**: The system SHALL implement Modbus RTU master/slave protocol over RS485 UART for board-to-board communication, allowing ESP32 devices to exchange temperature sensor data and control signals without Home Assistant intervention.

**FR2**: The `gruppo-miscelazione` device SHALL act as the Modbus master controller, polling slave devices and exposing coordination data (climate mode, supply temperatures, control signals).

**FR3**: All other boards (distribution and zone control boards) SHALL act as Modbus slaves, responding to master requests and executing commands based on master-provided data.

**FR4**: The `gruppo-miscelazione` (master) SHALL expose via Modbus registers:
   - Dallas temperature sensor readings for supply temperatures
   - Climate mode state (heat/cool/off)
   - Coordination signals for slave boards

**FR5**: The ground floor distribution device (slave) SHALL read temperature and coordination data via Modbus from the master instead of relying solely on Home Assistant room temperature sensors.

**FR6**: ONE new board SHALL be added to complete the system:
   - **First Floor Board** (Kincony KC868-A16): Zone distribution for Primo Piano heating/cooling with local Dallas sensors
   - **Second Floor Fancoil**: Controlled via 0-10V Modbus adapter connected to first floor A16 board

**FR7**: The system SHALL implement automatic failover: if Modbus communication fails, slave boards SHALL fall back to Home Assistant sensor data (if available) or safe default behavior.

**FR8**: Slave boards SHALL implement autonomous mode switching between heat/cool based on Modbus-received climate mode state from master, reducing dependency on Home Assistant's `sensor.thermostat_mode`.

**FR9**: The existing PID control loops (heat/cool dual PIDs) SHALL remain unchanged, continuing to use the current tuning parameters (kp, ki, kd values).

**FR10**: The system SHALL maintain full backward compatibility with Home Assistant, exposing all sensors, switches, and climate entities for monitoring and manual overrides.

**FR11**: Modbus communication errors SHALL be logged and exposed as diagnostic sensors in Home Assistant for monitoring and troubleshooting.

**FR12**: Each board SHALL support a configuration parameter to enable/disable Modbus communication, allowing gradual rollout and easy rollback to HA-dependent operation.

**FR13**: The master board SHALL poll slave boards at a configurable interval (default: 10 seconds) to maintain up-to-date system state and ensure slave responsiveness.

**FR14**: The system SHALL support room-level temperature and humidity measurement for each controlled zone, using either Modbus-based sensors or 1-Wire sensors (technology selection TBD during implementation).

**FR15**: Room temperature and humidity sensors SHALL be accessible to PID controllers for precise zone control and to Home Assistant for monitoring and advanced automation.

**FR16**: If Modbus sensors are used for room monitoring, they SHALL integrate into the existing master/slave architecture as either slave devices or sensors polled by slave boards.

### 2.2 Non-Functional Requirements

**NFR1**: Modbus communication response time SHALL be ≤ 500ms to ensure PID controllers receive timely temperature updates.

**NFR2**: The system SHALL maintain existing heating/cooling performance characteristics with ≤ ±0.5°C temperature deviation from current behavior.

**NFR3**: Firmware size SHALL remain within ESP32 flash constraints (current usage + Modbus implementation must fit in available flash).

**NFR4**: RS485 bus wiring SHALL support up to 1000 meters total cable length with proper master/slave addressing for up to 4 devices (1 master + 3 slaves currently, expandable).

**NFR5**: The system SHALL recover gracefully from Modbus communication failures within 30 seconds, either via Modbus reconnection or fallback to Home Assistant data.

**NFR6**: Configuration changes SHALL be possible via declarative configuration updates without requiring custom low-level code, using the platform's native component ecosystem.

**NFR7**: The system SHALL maintain the existing dual-path deployment model: local builds for development/testing and remote package-based builds for production deployment.

**NFR8**: Documentation SHALL be targeted at experienced ESPHome users familiar with PID control, RS485, and Modbus concepts.

**NFR9**: Room sensor integration SHALL be designed to support multiple sensor technologies (Modbus, 1-Wire, I2C) without requiring architectural changes to the master/slave Modbus communication system.

### 2.3 Compatibility Requirements

**CR1 - Existing Configuration Compatibility**: All existing device YAML configurations (`devices/`, `boards/`, `components/`) SHALL remain valid and functional. Modbus functionality SHALL be additive, not replacing existing structures.

**CR2 - Home Assistant Integration Compatibility**: All currently exposed entities (sensors, switches, climate controls) SHALL remain available in Home Assistant with identical entity IDs and attributes.

**CR3 - PID Tuning Preservation**: Current PID tuning parameters (heat_kp, heat_ki, heat_kd, cool_kp, cool_ki, cool_kd) SHALL be preserved exactly as configured, ensuring no disruption to tuned control loops.

**CR4 - Hardware Pin Compatibility**: RS485 UART pin assignments SHALL remain as currently configured (KC868-A6: TX=GPIO27, RX=GPIO14; KC868-A16: TX=GPIO13, RX=GPIO16). W5500 Ethernet adapter GPIO assignments on A6 SHALL be preserved.

**CR5 - Deployment Process Compatibility**: The existing locals/remotes deployment model SHALL be preserved, with remotes referencing GitHub packages via `!include` statements.

**CR6 - Component Modularity**: Existing component packages (`dual_pid.yaml`, `mixing_valve.yaml`, etc.) SHALL remain modular and reusable, with Modbus integration added as optional packages.

**CR7 - Sensor Technology Flexibility**: Room sensor integration SHALL support multiple technologies (Modbus sensors, 1-Wire sensors, I2C sensors) without requiring changes to core control logic, allowing technology selection during implementation phase.

---

## 3. Technical Constraints and Integration Requirements

### 3.1 Existing Technology Stack

**Languages**: YAML (ESPHome configuration DSL), C++ (underlying ESP-IDF framework)

**Frameworks**: 
- ESPHome (latest stable version)
- ESP-IDF framework (configured via `esp32.framework.type: esp-idf`)

**Hardware**:
- ESP32-DevKit boards (Kincony KC868 series)
- Kincony KC868-A6: 6 relays, 6 inputs, RS485, I2C (PCF8574), Dallas 1-Wire, RTC
  - Ethernet via W5500 adapter on free GPIOs (not native)
- Kincony KC868-A16: 16 relays, 16 inputs, RS485, I2C (2x PCF8574), 3x 1-Wire buses
  - Native Ethernet support
  - 0-10V Modbus adapter capability for remote device control
- Dallas DS18B20 temperature sensors (supply temperature monitoring)
- PCF8574 I2C GPIO expanders
- 0-10V Modbus adapter (for second floor fancoil control from first floor A16)
- Room sensors (TBD): Either Modbus temperature/humidity sensors OR 1-Wire temperature + I2C/1-Wire humidity sensors

**Communication Protocols**:
- WiFi (existing Home Assistant API integration)
- RS485 UART (hardware present, currently unused)
- I2C (PCF8574 GPIO expanders, RTC)
- 1-Wire (Dallas temperature sensors)

**External Dependencies**:
- Home Assistant (for monitoring, overrides, and advanced automation)
- ESPHome Dashboard / Builder Addon (for firmware compilation and OTA updates)

**Development Tools**:
- ESPHome CLI (local development)
- Home Assistant ESPHome Builder Addon (production deployment)
- Git/GitHub (version control and remote package hosting)

### 3.2 Integration Approach

**Modbus Integration Strategy**:
- Use ESPHome's native `modbus_controller` platform (available in recent ESPHome versions)
- **Master/Slave Architecture**: 
  - `gruppo-miscelazione` (KC868-A6) = Modbus Master (address 1) - polls slaves, coordinates system
  - `distribuzione-piano-terra` (KC868-A16) = Modbus Slave (address 2) - ground floor distribution
  - First floor board (KC868-A16) = Modbus Slave (address 3) - first floor m zone distribution + second floor fancoil via 0-10V adapter
  - 0-10V Modbus adapter = Controlled by first floor A16 for second floor fancoil
- Master polls each slave every 10 seconds for status, slaves respond to master requests only
- Register map design: Standard 16-bit holding registers for temperature values (scaled by 100 for 0.01°C precision)
- Baud rate: 9600 (already configured), 8N1 format, Modbus RTU framing

**Sensor Data Flow**:
- Current: Home Assistant → ESPHome via `homeassistant` platform
- Enhanced: 
  - Master reads local Dallas sensors → Master exposes via Modbus registers
  - Master polls slaves for status/diagnostics
  - Slaves read master registers → Use for PID controllers
  - Room sensors (temperature/humidity): 
    - **Option A (Modbus)**: Modbus sensor devices polled by master or slaves → shared via Modbus registers
    - **Option B (1-Wire)**: Local 1-Wire sensors on slave boards → exposed to master via Modbus if needed
  - Room sensor data used by PID controllers for precise zone control
- Fallback: If Modbus unavailable, slaves retain Home Assistant platform as backup

**Configuration Organization**:
- Create new component: `components/modbus_master.yaml` - master controller functionality
- Create new component: `components/modbus_slave.yaml` - slave device functionality
- Update `boards/a6.yaml` to support both master and slave roles (via vars)
- Create new board: `boards/a16_first_floor.yaml` for first floor zone distribution
- Create new component: `components/modbus_0_10v.yaml` - 0-10V Modbus adapter control
- Maintain separation: locals/ = absolute paths, remotes/ = GitHub package references

**Testing Integration Strategy**:
- Phase 1: Master functionality testing on `gruppo-miscelazione` (expose registers, handle slave requests)
- Phase 2: Two-board master/slave testing (Master A6 ↔ Slave A16)
- Phase 3: Three-board master/slave testing (1 master + 2 A16 slaves)
- Phase 4: 0-10V Modbus adapter testing for second floor fancoil control
- Phase 5: Failover testing (intentional Modbus/HA outages, slave fallback behavior)
- Use `locals/` directory for all testing before promoting to `remotes/`

### 3.3 Code Organization and Standards

**File Structure Approach**:
```
esphome-devices/
├── boards/                    # Hardware-specific base configurations
│   ├── base.yaml             # Common ESP32 + logger + API + OTA
│   ├── a6.yaml               # A6 hardware base
│   ├── a16.yaml              # A16 hardware base
│   ├── a16_first_floor.yaml  # NEW: First floor distribution board
│   └── wifi.yaml             # WiFi configuration
├── components/               # Reusable functional packages
│   ├── dual_pid.yaml         # Existing PID control
│   ├── mixing_valve.yaml     # Existing mixing valve control
│   ├── modbus_master.yaml    # NEW: Modbus master controller
│   ├── modbus_slave.yaml     # NEW: Modbus slave device
│   ├── modbus_sensor.yaml    # NEW: Modbus-based sensor wrapper
│   ├── modbus_0_10v.yaml     # NEW: 0-10V Modbus adapter control
│   └── room_sensors.yaml     # NEW: Room temp/humidity sensors (flexible tech)
├── devices/                  # Device-specific assemblies
│   ├── gruppo-miscelazione.yaml          # Master controller
│   ├── distribuzione-piano-terra.yaml    # Ground floor slave
│   └── distribuzione-primo-piano.yaml    # NEW: First floor slave
├── locals/                   # Development configs (absolute paths)
│   ├── gruppo-distribuzione.yaml  # Local variant
│   ├── gruppo-miscelazione.yaml
│   └── secrets.yaml
└── remotes/                  # Production configs (GitHub packages)
    ├── gruppo-miscelazione.yaml
    └── secrets.yaml
```

**Naming Conventions**:
- Component files: `{function}.yaml` (e.g., `modbus_server.yaml`)
- Board files: `{model}.yaml` or `{model}_{variant}.yaml`
- Device files: `{location}-{function}.yaml` (e.g., `fancoil-secondo-piano.yaml`)
- Variable substitution: `${variable_name}` in vars, `id(entity_id)` in lambdas
- Modbus entities: Prefix with `modbus_` (e.g., `modbus_temp_soggiorno`)

**Coding Standards**:
- Use package inclusion via `!include` for modularity
- Use `vars:` for parameterization of reusable components
- Prefer native ESPHome components over custom C++ when possible
- Use `internal: true` for entities not needed in Home Assistant
- Include descriptive `name:` for all entities exposed to HA
- Use consistent indentation (2 spaces)
- Add comments for non-obvious configuration choices (especially Modbus register mappings)

**Documentation Standards**:
- Each new component file SHALL include header comment explaining purpose and usage
- Modbus register map SHALL be documented in a separate `docs/modbus-register-map.md`
- YAML file comments SHALL explain the "why" not the "what" (YAML is self-documenting for "what")
- Update main README (to be created) with Modbus architecture diagram

### 3.4 Deployment and Operations

**Build Process Integration**:
- Development: `esphome compile locals/{device}.yaml`
- Upload: `esphome upload locals/{device}.yaml` (via USB or OTA)
- Production: Home Assistant ESPHome Builder addon compiles from `remotes/` GitHub references
- Validation: `esphome config {file}.yaml` to validate syntax before commit

**Deployment Strategy**:
1. **Development Phase**: Edit and test in `locals/` directory
   - Compile and upload directly to devices
   - Iterate on Modbus configuration and testing
2. **Staging Phase**: Copy tested configs to `devices/` and `components/`
   - Update `remotes/` configs to reference new components
   - Test full package inclusion from GitHub
3. **Production Phase**: Merge to main branch
   - Home Assistant ESPHome Builder addon auto-detects changes
   - OTA update to production devices

**Monitoring and Logging**:
- ESPHome logger: `level: DEBUG` during development, `INFO` in production
- Modbus communication errors → diagnostic `binary_sensor` in HA
- Temperature sensor availability → `binary_sensor` per sensor
- Failover events → `text_sensor` with last failover reason/timestamp
- Home Assistant history tracking for all sensors

**Configuration Management**:
- Secrets (WiFi passwords, API keys, OTA passwords): `secrets.yaml` (gitignored)
- Device-specific variables: Defined in device YAML files
- Shared parameters: Component `vars:` for reusable values
- Modbus addresses: Centralized in component defaults for easy reconfiguration

### 3.5 Risk Assessment and Mitigation

**Technical Risks**:
1. **Risk**: Modbus communication instability causing control loop disruption
   - **Mitigation**: Implement sensor timeout detection with automatic fallback to Home Assistant data
   - **Mitigation**: Add configurable Modbus enable/disable flag for quick rollback

2. **Risk**: RS485 bus electrical issues (ground loops, termination, cable quality)
   - **Mitigation**: Document proper RS485 wiring with termination resistors
   - **Mitigation**: Start with short cable runs during testing
   - **Mitigation**: Use twisted-pair shielded cable for production

5. **Risk**: Room sensor technology selection impacts system architecture (Modbus vs 1-Wire)
   - **Mitigation**: Design sensor abstraction layer supporting multiple technologies
   - **Mitigation**: Test both approaches in development: Modbus sensor on one zone, 1-Wire on another
   - **Mitigation**: Document trade-offs: Modbus (more devices on bus, standardized) vs 1-Wire (simpler, lower cost)

3. **Risk**: Modbus address conflicts or register mapping errors
   - **Mitigation**: Create comprehensive register map documentation
   - **Mitigation**: Implement Modbus diagnostic sensors showing read/write errors
   - **Mitigation**: Extensive testing of all register read/write operations

4. **Risk**: ESP32 firmware size growth exceeding flash capacity
   - **Mitigation**: Monitor compiled firmware size throughout development
   - **Mitigation**: Use `internal: true` aggressively to reduce Home Assistant entity overhead
   - **Mitigation**: Consider partition table adjustment if needed

**Integration Risks**:
1. **Risk**: Breaking existing PID control behavior during refactoring
   - **Mitigation**: Implement Modbus sensors alongside existing HA sensors initially
   - **Mitigation**: A/B testing comparing HA sensor vs Modbus sensor control performance
   - **Mitigation**: Preserve existing PID parameters exactly

2. **Risk**: Home Assistant integration regression (entity ID changes, missing attributes)
   - **Mitigation**: Entity ID compatibility testing before deployment
   - **Mitigation**: Maintain entity name consistency with current setup

3. **Risk**: locals/remotes package reference mismatches
   - **Mitigation**: Thorough testing of GitHub package inclusion in remotes/ before deployment
   - **Mitigation**: Version tagging of GitHub commits for rollback capability

**Deployment Risks**:
1. **Risk**: Firmware update bricking devices during heating season
   - **Mitigation**: Deploy during moderate weather conditions
   - **Mitigation**: Stage rollout: one device at a time
   - **Mitigation**: Keep USB cables connected for emergency serial flashing

2. **Risk**: Configuration errors causing loss of climate control
   - **Mitigation**: Extensive testing in locals/ before promoting to remotes/
   - **Mitigation**: Keep previous working firmware binaries for emergency rollback
   - **Mitigation**: Implement Modbus enable flag to disable new features without reflashing

---

## 4. Epic and Story Structure

### 4.1 Epic Approach

**Epic Structure Decision**: Single comprehensive epic with sequenced stories

**Rationale**: This enhancement represents a cohesive architectural change with tightly coupled components. All stories contribute to the single goal of autonomous board-to-board communication. Multiple epics would create artificial boundaries and complicate dependency management. The stories are sequenced to build incrementally from foundation (Modbus infrastructure) through integration (sensor migration) to completion (third board addition), ensuring each story delivers testable value while maintaining system stability.

The brownfield context reinforces this: a single existing system enhancement, not multiple independent features.

---

## 5. Epic 1: Autonomous Multi-Board Climate Control via RS485 Modbus

**Epic Goal**: Transform the ESPHome climate control system from Home Assistant-dependent to autonomous by implementing master/slave RS485 Modbus communication, eliminating single-point-of-failure while maintaining full HA integration, and completing three-floor coverage with one new A16 board and 0-10V Modbus adapter.

**Integration Requirements**: 
- Preserve all existing PID control logic, tuning parameters, and relay control patterns
- Maintain backward compatibility with Home Assistant entity structure
- Implement failover logic ensuring safe operation during communication failures
- Support gradual rollout with per-board Modbus enable flags

### Story 1.1: Modbus Master/Slave Infrastructure Foundation

**As a** system administrator,  
**I want** Modbus RTU master/slave infrastructure configured on existing boards,  
**so that** the master can coordinate slaves over RS485 without immediate changes to control logic.

#### Acceptance Criteria

1. KC868-A6 board (`gruppo-miscelazione`) configured as **Modbus Master** (address 1):
   - UART configured (TX=GPIO27, RX=GPIO14, 9600 baud, 8N1)
   - Can initiate read/write operations to slave addresses
   - Master polling logic framework in place
2. KC868-A16 board (`distribuzione-piano-terra`) configured as **Modbus Slave** (address 2):
   - UART configured (TX=GPIO13, RX=GPIO16, 9600 baud, 8N1)
   - Responds to master requests on address 2
   - Does not initiate communication (slave-only mode)
3. Modbus diagnostic sensors exposed to Home Assistant on master showing:
   - Each slave communication status (online/offline per slave)
   - Message error count per slave
   - Last successful poll timestamp per slave
4. Simple master→slave test succeeds (master reads a test register from slave)
5. Firmware compiles successfully for both master and slave roles
6. OTA updates work correctly with new Modbus-enabled firmware

#### Integration Verification

**IV1 - Existing Functionality Preserved**: 
- All existing PID climate controls continue to function using Home Assistant sensor data
- All relay outputs continue to operate correctly
- All Dallas temperature sensors continue to report to Home Assistant
- No change in heating/cooling behavior observed

**IV2 - Integration Point Verification**:
- Home Assistant API connection remains stable
- All existing entity IDs are unchanged
- WiFi connectivity is unaffected by Modbus UART initialization
- I2C devices (PCF8574, RTC) continue to function

**IV3 - Performance Impact Verification**:
- Firmware size increase documented and within acceptable limits
- No increase in CPU usage during idle state
- No delay in OTA update process
- Logger output shows Modbus initialization without errors

---

### Story 1.2: Modbus Master - Temperature Sensor and Coordination Data Exposure

**As a** master controller (gruppo-miscelazione),  
**I want** to expose my Dallas temperature sensors and coordination data via Modbus registers,  
**so that** slave boards can read supply temperatures and mode settings without Home Assistant.

#### Acceptance Criteria

1. Create reusable component `components/modbus_master.yaml` that:
   - Implements master controller functionality
   - Exposes local sensor values as Modbus holding registers
   - Supports parameterization via `vars:` (sensor IDs, register addresses)
   - Scales float temperature values to 16-bit integers (multiply by 100 for 0.01°C precision)
   - Implements polling logic for slave devices
2. `gruppo-miscelazione` (master) exposes via Modbus registers:
   - Register 100: Ground floor supply temp (dallas_0x81000000b3e6f628) - if sensor exists/added
   - Register 200: Climate mode (0=off, 1=heat, 2=cool)
   - Register 300: Master heartbeat/timestamp
3. Master responds correctly to slave read requests (function code 0x03)
4. Register values update in real-time as Dallas sensors report new temperatures
5. Documentation created: `docs/modbus-register-map.md` with master register definitions
6. Master status sensor in HA shows active polling state

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- Dallas sensors still report to Home Assistant via native ESPHome sensors
- Mixing valve PID controls continue using local sensor data unchanged
- No disruption to relay control or valve positioning

**IV2 - Integration Point Verification**:
- Test Modbus reads from slave (distribuzione-piano-terra reads master registers)
- Verify register values match Home Assistant sensor values (within 0.01°C)
- Confirm master handles invalid register requests gracefully (returns Modbus error, doesn't crash)

**IV3 - Performance Impact Verification**:
- No noticeable latency in Dallas sensor updates
- CPU usage increase ≤ 5% during Modbus reads
- Modbus response time ≤ 500ms

---

### Story 1.3: Modbus Slave - Master Data Reading and Response

**As a** slave distribution board (distribuzione-piano-terra),  
**I want** to read coordination data via Modbus from the master controller,  
**so that** I can operate independently without Home Assistant sensor dependencies.

#### Acceptance Criteria

1. Create reusable component `components/modbus_slave.yaml` that:
   - Implements slave device functionality (responds to master only)
   - Reads Modbus holding registers from master (address 1)
   - Exposes read values as ESPHome sensors
   - Supports parameterization via `vars:` (master address, register map, update interval)
   - Implements timeout handling and error sensors
   - Can expose local slave status registers for master to poll
2. `distribuzione-piano-terra` (slave) reads from master via Modbus:
   - Reads register 200 from master → `modbus_climate_mode` (heat/cool/off)
   - Reads register 300 from master → `modbus_master_heartbeat`
3. Slave attempts to read master registers every 10 seconds when Modbus enabled
4. Timeout handling: If Modbus read fails for >30 seconds, sensor reports "unavailable"
5. Diagnostic sensor shows Modbus read error count and last error timestamp
6. Slave exposes own status registers for master polling (e.g., register 1000: slave health status)
7. Room sensor integration framework in place (temperature/humidity reading support), with technology selection deferred to Story 1.6

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- Existing Home Assistant sensor integration (`sensor.termometro_soggiorno_temperature`) remains functional
- PID controllers still use HA sensor as primary source (no logic change yet)
- No disruption to existing slow PWM outputs or relay control

**IV2 - Integration Point Verification**:
- Verify Modbus sensor values on slave match master's exposed values (within 0.01°C for temps)
- Test Modbus communication during active heating/cooling cycles
- Confirm master→slave communication works reliably (no bus contention in master/slave architecture)

**IV3 - Performance Impact Verification**:
- Network traffic to Home Assistant remains unchanged
- PID control loop timing unaffected
- Modbus read operations complete within 500ms budget

---

### Story 1.4: Sensor Failover Logic Implementation

**As a** distribution board,  
**I want** automatic failover between Modbus sensors and Home Assistant sensors,  
**so that** the system remains operational during communication failures.

#### Acceptance Criteria

1. Create sensor selection logic in PID configurations:
   - Primary: Modbus sensor (if available and updated within 30 seconds)
   - Fallback: Home Assistant sensor (if available)
   - Emergency: Last known good value + safe shutdown after 5 minutes
2. Implement `template` sensor wrapper that selects best available source
3. Add configuration flag: `use_modbus: true/false` to enable/disable Modbus usage per device
4. Failover events logged and exposed as text sensor in Home Assistant:
   - "Modbus Active"
   - "Failover to Home Assistant"
   - "Emergency Mode - No Sensors"
5. Test scenarios:
   - Modbus communication failure → automatic HA failover
   - Home Assistant offline, Modbus active → system continues
   - Both offline → safe shutdown (turn off heating/cooling)
6. Recovery: When Modbus communication restored, automatic switch back from HA to Modbus

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- When `use_modbus: false`, system behaves exactly as before (HA sensors only)
- PID tuning parameters remain unchanged
- Relay control patterns identical

**IV2 - Integration Point Verification**:
- Simulate Modbus failure (disconnect RS485) → verify HA failover within 30s
- Simulate HA failure (disconnect WiFi) → verify Modbus continues operation
- Simulate both failures → verify safe shutdown after 5 minutes
- Restore connections → verify automatic recovery

**IV3 - Performance Impact Verification**:
- Failover transition completes within 30 seconds
- No temperature overshoot during failover
- Control loop stability maintained across failover events

---

### Story 1.5: First Floor A16 Board + Second Floor 0-10V Fancoil Control

**As a** system administrator,  
**I want** to add a new A16 board for first floor distribution and configure 0-10V Modbus adapter for second floor fancoil,  
**so that** all three floors are fully automated and integrated into the Modbus network.

#### Acceptance Criteria - First Floor Board (Slave Address 3)

1. Create new board configuration: `boards/a16_first_floor.yaml`
   - Based on `boards/a16.yaml` configured as Modbus slave (address 3)
   - Kincony KC868-A16 hardware base
   - Includes Dallas sensors for first floor supply temperature monitoring
2. Create new device configuration: `devices/distribuzione-primo-piano.yaml`
   - Mixing valve control for Primo Piano heating/cooling
   - Zone distribution control (similar to ground floor pattern)
   - Dual PID controllers (heat/cool modes)
   - Reads climate mode from master via Modbus
   - Local Dallas sensor for supply temperature control
3. Hardware installation documented: RS485 connection, mixing valve wiring, Dallas sensor placement, zone valve connections
4. Board joins Modbus network as slave successfully
5. First floor mixing valve responds to master climate mode commands
6. First floor supply temperature monitored and controlled via PID
7. First floor zone distribution operational

#### Acceptance Criteria - Second Floor 0-10V Fancoil (via Ground Floor A16)

1. Configure 0-10V Modbus adapter on ground floor A16 (`distribuzione-piano-terra`)
   - Create component `components/modbus_0_10v.yaml` for adapter control
   - 0-10V output control for fancoil speed/capacity
   - Temperature-based control logic
2. Second floor fancoil control implementation:
   - PID controller for temperature regulation using 0-10V output
   - Reads climate mode from master via Modbus (through ground floor A16)
   - Room temperature sensor integration (Modbus or 1-Wire)
3. Hardware installation documented: 0-10V wiring from ground floor A16 to second floor fancoil
4. Second floor fancoil responds to temperature setpoint changes
5. 0-10V signal properly controls fancoil capacity (0V = off, 10V = full capacity)

#### Acceptance Criteria - System Integration

1. Master polls both A16 slaves (addresses 2 and 3) successfully
2. All THREE boards (1 master + 2 A16 slaves) communicate on shared RS485 bus without conflicts
3. First floor A16 successfully controls second floor fancoil via 0-10V adapter
4. RS485 bus properly terminated at master and last slave
5. Home Assistant discovers all new entities from first floor board and second floor fancoil
6. Full system test: All three floors respond correctly to heat/cool mode changes

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- Gruppo-miscelazione (master, address 1) operation unaffected by new slave
- Distribuzione-piano-terra (slave, address 2) operation unaffected
- Existing Modbus communication continues without interruption
- Ground floor cooling automation (fancoils + floor cooling) continues to work
- Ground floor local fancoil control unaffected by 0-10V adapter addition

**IV2 - Integration Point Verification**:
- Test master polling both A16 slaves: Master successfully reads status from addresses 2 and 3
- Test slave reads from master: Both A16 slaves successfully read mode/coordination data
- Verify RS485 bus termination at both physical ends
- Confirm Modbus addressing: No address conflicts
- Test climate mode propagation: Mode change on master → all floors reflect change within 10s
- Test 0-10V fancoil control: Temperature setpoint changes → fancoil capacity adjusts appropriately

**IV3 - Performance Impact Verification**:
- Master polling cycle completes within 500ms for both A16 slaves
- No increase in communication errors with additional slave
- 0-10V control responds within 2 seconds of temperature changes
- Network traffic to Home Assistant scales linearly with new board
- Temperature control accuracy maintained across all three floors (±0.5°C)

---

### Story 1.6: Room Temperature and Humidity Sensor Integration

**As a** zone control system,  
**I want** room-level temperature and humidity measurement for each zone,  
**so that** PID controllers have accurate room conditions for precise climate control and humidity monitoring.

#### Acceptance Criteria

1. Create component `components/room_sensors.yaml` that:
   - Supports multiple sensor technologies via parameterization
   - **Option A**: Modbus temperature/humidity sensors
   - **Option B**: 1-Wire temperature sensors + I2C/1-Wire humidity sensors (e.g., SHT3x, DHT22)
   - Exposes unified sensor interface regardless of underlying technology
2. Implement room sensors for ground floor zones (distribuzione-piano-terra):
   - Soggiorno: Temperature + humidity sensor
   - Cucina: Temperature + humidity sensor
   - Bagno: Temperature + humidity sensor
   - Anticamera: Temperature + humidity sensor
3. Technology selection decision documented in `docs/sensor-technology-selection.md`:
   - **Modbus sensors**: Pros (standardized protocol, easy to add/remove), Cons (cost, bus loading)
   - **1-Wire sensors**: Pros (low cost, simple wiring), Cons (limited humidity sensor options)
   - Final selection rationale
4. Room sensor data:
   - Exposed to Home Assistant for monitoring
   - Available to PID controllers via ESPHome internal sensors
   - If Modbus sensors used: Integrated into master/slave Modbus network
   - If 1-Wire sensors used: Connected to slave board 1-Wire buses
5. PID controllers updated to use room temperature (not just supply temperature) for control:
   - Setpoint based on room temperature
   - Supply temperature managed by mixing valve based on room demand
6. Humidity data exposed to Home Assistant for monitoring and future automation

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- PID controllers can still use supply temperature if room sensors unavailable
- Existing Home Assistant sensor integration continues to work as fallback
- No disruption to relay control or existing automation

**IV2 - Integration Point Verification**:
- Test Modbus sensor integration (if selected): Sensors polled successfully, data updated every 10s
- Test 1-Wire sensor integration (if selected): All 4 zones report temperature/humidity without conflicts
- Verify room sensor data accuracy (compare with known-good reference sensors)
- Test PID control using room sensors: Verify setpoint tracking within ±0.5°C
- Verify humidity data exposed to Home Assistant for monitoring

**IV3 - Performance Impact Verification**:
- If Modbus sensors: Polling cycle completes within 500ms budget (master polls slaves + room sensors)
- If 1-Wire sensors: No increase in scan time for 1-Wire bus
- No degradation in temperature control accuracy
- CPU usage increase ≤ 5% with room sensor polling

---

### Story 1.7: Documentation, Deployment, and Production Readiness

**As a** system maintainer,  
**I want** comprehensive documentation and production-ready configuration,  
**so that** the system can be maintained, debugged, and expanded in the future.

#### Acceptance Criteria

1. **Modbus Register Map Documentation** (`docs/modbus-register-map.md`):
   - Complete table of all registers: Address | Device | Type | Description | Units | Scaling
   - Room sensor register assignments (if Modbus sensors used)
   - Example Modbus read/write commands
2. **Sensor Technology Selection Document** (`docs/sensor-technology-selection.md`):
   - Comparison of Modbus vs 1-Wire sensor approaches
   - Final technology selection rationale
   - Wiring diagrams for chosen sensor technology
   - Future expansion considerations
3. **Architecture Diagram** (`docs/architecture-diagram.md`):
   - Visual representation of three boards connected via RS485
   - Data flow: Sensors → Modbus → PID → Relays
   - Failover paths illustrated
4. **Deployment Guide** (`docs/deployment-guide.md`):
   - Step-by-step upgrade from current system to Modbus-enabled
   - Rollback procedure if issues arise
   - Testing checklist for each story
5. **RS485 Wiring Guide** (`docs/rs485-wiring.md`):
   - Proper twisted-pair wiring, shielding, termination
   - Troubleshooting guide for bus issues
6. **`remotes/` Configuration Updated**:
   - All production devices reference GitHub packages
   - Tested via Home Assistant ESPHome Builder addon
   - OTA update procedure validated
7. **Monitoring Dashboard in Home Assistant**:
   - Modbus communication health (all boards)
   - Sensor source indicators (Modbus vs HA)
   - Failover event log
   - Climate mode synchronization status
   - Room temperature/humidity for all zones
8. **Configuration Examples**:
   - Documented in each component file header
   - Example device configurations for future expansion

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- Final validation: All three floors maintain temperature setpoints ±0.5°C
- No increase in temperature overshoot or oscillation
- Relay cycling behavior unchanged

**IV2 - Integration Point Verification**:
- Deploy via `remotes/` configuration from GitHub
- OTA update all THREE devices successfully (1 master + 2 A16 slaves)
- Home Assistant restart: All entities rediscovered correctly
- 24-hour stability test: No Modbus errors or unexpected failovers
- Full cooling test: Ground floor fancoil/floor cooling automation working correctly
- 0-10V fancoil test: Second floor fancoil responds properly to temperature changes

**IV3 - Performance Impact Verification**:
- Document final firmware sizes (KC868-A6, KC868-A16 boards)
- Document CPU usage under normal operation
- Document Modbus message rate and bandwidth usage
- Verify system meets all NFRs (response time ≤500ms, temperature control ±0.5°C)

---

## 6. Success Metrics

**Primary Metrics**:
- **System Uptime**: Climate control continues during Home Assistant outages (target: 99.9% uptime regardless of HA availability)
- **Temperature Control Accuracy**: ±0.5°C from setpoint across all zones (maintain current performance)
- **Modbus Reliability**: <1% communication error rate under normal operation
- **Failover Speed**: Automatic sensor failover within 30 seconds of communication loss

**Secondary Metrics**:
- **Response Time**: Master polling cycle completes within 500ms for both A16 slaves (including room sensors if Modbus)
- **Deployment Success**: All three boards (1 master + 2 A16 slaves) upgraded via OTA without requiring physical access
- **Ground Floor Cooling Efficiency**: Fancoils activate within 30 seconds of cooling demand, floor cooling coordination smooth
- **0-10V Control Accuracy**: Second floor fancoil responds within 2 seconds to setpoint changes
- **Room Sensor Accuracy**: All room sensors report within ±0.3°C of reference sensors, humidity within ±5%
- **Maintainability**: Future board or sensor additions require <2 hours configuration time
- **Documentation Completeness**: Experienced ESPHome user can add additional slave boards, 0-10V devices, or room sensors using only provided documentation

---

## 7. Out of Scope

The following items are explicitly **out of scope** for this enhancement:

- **Ground Floor Cooling Automation**: Intelligent coordination between fancoils (primary cooling) and floor cooling (optional/supplemental) with humidity-aware logic — deferred to future phase (potential Epic 2)
- **Advanced Scheduling/Automation**: Complex time-based or occupancy-based automation remains Home Assistant's responsibility
- **Web UI on ESP32**: No local web interface for configuration (ESPHome/HA remains management interface)
- **PID Auto-Tuning**: Current PID parameters are manually tuned and frozen; auto-tuning not implemented
- **Energy Monitoring**: No power consumption tracking of relays or fancoils
- **Modbus TCP**: Only Modbus RTU over RS485 with master/slave architecture is supported (no TCP/IP Modbus, no mesh)
- **Non-ESPHome Modbus Devices**: System is not designed to integrate with third-party Modbus devices (e.g., commercial HVAC controllers)
- **Historical Data Logging**: Local logging on ESP32 is not implemented (Home Assistant provides this)
- **Advanced Humidity Control**: Basic humidity measurement implemented for monitoring, but advanced dehumidification control algorithms (e.g., dew point calculations, humidity PID) are not implemented in this phase
- **Multi-Technology Sensor Mix**: System will standardize on ONE room sensor technology (Modbus OR 1-Wire), not a mix of both in production

---

## 8. Assumptions and Dependencies

### Assumptions
1. RS485 bus wiring infrastructure can be installed in master/slave topology (cable runs estimated <50m total)
2. Current Home Assistant installation will remain available for monitoring and overrides (not being replaced, just made non-critical)
3. ESPHome continues to support Modbus RTU master/slave roles in future versions
4. Current PID tuning is optimal and doesn't need adjustment during migration
5. Dallas temperature sensors are sufficiently responsive for supply temperature PID control (no need for faster sensors)
6. First floor mixing valve hardware (relays, Dallas sensors, mixing valve actuator) is available or can be procured
7. Second floor fancoil wiring and control capabilities are available or can be installed
8. Room temperature/humidity sensors (either Modbus or 1-Wire) can be installed in each controlled zone
9. Room sensor technology selection (Modbus vs 1-Wire) will be finalized during Story 1.6 implementation based on cost, availability, and technical considerations
10. Two additional Kincony KC868-A6 boards (or compatible) are available for first and second floor installations

### Dependencies
1. **ESPHome Version**: Requires ESPHome ≥2023.x with `modbus_controller` platform support
2. **Hardware**: Kincony KC868-A6 and KC868-A16 boards must have functional RS485 transceivers and proper GPIO routing
3. **Testing Environment**: Ability to test Modbus communication during moderate weather (not extreme heating/cooling demand)
4. **Documentation Task**: Project architecture documentation should be created via `*document-project` task to support development
5. **GitHub Access**: `remotes/` deployment requires stable GitHub connectivity for package inclusion
6. **Room Sensor Hardware**: Availability of chosen sensor technology (Modbus temperature/humidity sensors OR 1-Wire temperature + I2C/1-Wire humidity sensors)

---

## 9. Next Steps

Upon PRD approval:

1. **Run `*document-project` Task**: Create comprehensive brownfield architecture documentation capturing current system state, technical constraints, and "gotchas" before modifications begin.

2. **Detailed Technical Design**: Architect to create detailed Modbus register map, component interfaces, and sensor selection logic design.

3. **Story Breakdown**: Product Owner to create individual story cards from this PRD's Epic section.

4. **Development Environment Setup**: Developer to prepare `locals/` test configurations with Modbus components for iterative testing.

5. **Hardware Preparation**: Procure one Kincony KC868-A16 board for first floor installation; prepare RS485 cables and termination resistors for master/slave bus topology. Ensure 0-10V Modbus adapter is available for second floor fancoil control.

6. **Stakeholder Review**: Present PRD to end users for feedback on failover behavior and monitoring requirements.

---

## Appendix A: Glossary

- **A6/A16 Board**: Kincony KC868 series ESP32-based control boards (KC868-A6 with 6 relays/inputs, KC868-A16 with 16 relays/inputs)
- **Modbus RTU**: Serial communication protocol (binary format) for industrial automation
- **RS485**: Differential serial communication hardware layer, suitable for long distances and noisy environments
- **PID Controller**: Proportional-Integral-Derivative control algorithm for precise temperature regulation
- **Mixing Valve**: Motorized valve that blends hot and cold water to achieve target supply temperature
- **Slow PWM**: Pulse-width modulation with long periods (30s) for thermal system control (floor heating/cooling)
- **Fancoil**: Air handler with fan and heat exchanger coil for zone temperature and humidity control
- **Dallas Sensor**: DS18B20 digital temperature sensor using 1-Wire protocol
- **ESPHome**: YAML-based firmware framework for ESP32/ESP8266 devices integrated with Home Assistant
- **Locals/Remotes**: Deployment model distinction (development vs. production configurations)

---

## Appendix B: Related GitHub Issues

_(No GitHub issues have been linked to this PRD. Add relevant issue references here as they are created.)_

---

## 10. Epic 4: Room-Based Component Architecture (Code Organization)

**Epic Goal**: Reorganize ESPHome components from functionality-based structure to room-based structure for improved maintainability, clarity, and easier per-room configuration management.

**Integration Requirements**: 
- Preserve all existing functionality and entity IDs (no breaking changes)
- Maintain backward compatibility with existing configurations
- Zero impact on temperature control behavior
- Purely organizational refactoring (no logic changes)

### Story 4.1: Create Room Component Template and Ground Floor Prototype

**As a** developer,  
**I want** a reusable room component template with clear vars interface,  
**so that** individual rooms can be instantiated as self-contained units.

#### Acceptance Criteria

1. Design room component vars interface:
   - Required vars: `room_name`, `room_slug`, `ha_temperature`, `default_target`, `relay_ids`, `pid_tuning`
   - Optional vars: `min_temp`, `max_temp`, `temp_step`, `pwm_period`
   - Vars documented in component header
2. Create `components/rooms/_templates/room_with_pid.yaml` template:
   - HA temperature sensor input
   - PID climate controller
   - PID output sensor for monitoring
   - Slow PWM output with relay control
   - All IDs parameterized via `${room_slug}`
3. Create `components/rooms/ground_floor/soggiorno.yaml` as prototype:
   - Instantiates room template with Soggiorno-specific vars
   - Tests all var substitutions work correctly
4. Update `devices/distribuzione-piano-terra.yaml` to use room component for Soggiorno:
   - Replace inline PID/sensor/output definitions with room package
   - Verify firmware compiles successfully
5. Document room component pattern in component file header
6. Test prototype: Deploy to device, verify Soggiorno functions identically to before

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- Soggiorno PID control behavior unchanged
- Entity ID `climate.pid_soggiorno` unchanged
- Temperature control accuracy maintained (±0.5°C)
- Relay control pattern identical

**IV2 - Integration Point Verification**:
- Soggiorno room component integrates with device-level climate mode coordination
- PID sensors exposed correctly to Home Assistant
- Slow PWM output controls correct relays (05, 06, 07)

**IV3 - Code Quality Verification**:
- Room component vars interface clear and well-documented
- Component file includes usage examples
- No code duplication between template and instance

---

### Story 4.2: Refactor Ground Floor Rooms (Cucina, Bagno, Anticamera)

**As a** developer,  
**I want** all ground floor rooms converted to room components,  
**so that** the complete ground floor uses consistent room-based architecture.

#### Acceptance Criteria

1. Create `components/rooms/ground_floor/cucina.yaml`:
   - Based on room template
   - Cucina-specific vars (relays 01, 02; default temp 22.0)
2. Create `components/rooms/ground_floor/bagno.yaml`:
   - Based on room template
   - Bagno-specific vars (relay 03; default temp 23.0)
3. Create `components/rooms/ground_floor/anticamera.yaml`:
   - Based on room template
   - Anticamera-specific vars (relay 04; default temp 20.0)
4. Update `devices/distribuzione-piano-terra.yaml`:
   - Replace all inline room definitions with room component packages
   - Preserve device-level climate mode coordination
   - Preserve switch management script
5. Verify all 4 rooms:
   - Firmware compiles successfully
   - All entity IDs unchanged
   - Temperature control behavior identical

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- All 4 ground floor zones control temperature correctly
- Entity IDs unchanged: `climate.pid_soggiorno`, `climate.pid_cucina`, etc.
- PID tuning parameters preserved
- Relay control patterns identical

**IV2 - Integration Point Verification**:
- Climate mode coordination updates all 4 rooms correctly
- Switch management script detects all relay states
- Home Assistant displays all entities correctly

**IV3 - Code Quality Verification**:
- Device file significantly simplified (room config co-located)
- Easy to understand which relays control which room
- Reduced code duplication across rooms

---

### Story 4.3: Refactor First Floor Rooms

**As a** developer,  
**I want** first floor rooms converted to room components,  
**so that** the entire system uses consistent room-based architecture.

#### Acceptance Criteria

1. Create `components/rooms/first_floor/zona_1.yaml`:
   - Based on room template (may need adaptations for first floor)
   - Zona 1-specific vars
2. Create `components/rooms/first_floor/zona_2.yaml`:
   - Based on room template
   - Zona 2-specific vars
3. Update `devices/distribuzione-primo-piano.yaml`:
   - Replace inline room definitions with room component packages
   - Preserve device-level climate mode coordination
4. Verify both first floor zones:
   - Firmware compiles successfully
   - All entity IDs unchanged
   - Temperature control behavior identical

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- Both first floor zones control temperature correctly
- Entity IDs unchanged: `climate.pid_primo_piano_zona_1`, `climate.pid_primo_piano_zona_2`
- PID tuning parameters preserved

**IV2 - Integration Point Verification**:
- Climate mode coordination updates both zones correctly
- Room components work correctly on first floor device

**IV3 - Code Quality Verification**:
- First floor device file simplified
- Consistent pattern across ground floor and first floor

---

### Story 4.4: Documentation, Cleanup, and Template Refinement

**As a** future developer,  
**I want** comprehensive documentation and refined templates,  
**so that** I can easily add new rooms or modify existing ones.

#### Acceptance Criteria

1. Refine room component template based on implementation learnings:
   - Address any issues found during Stories 4.1-4.3
   - Add additional parameterization if needed
   - Ensure template works for both ground floor and first floor
2. Create `docs/room-component-guide.md`:
   - How to create a new room component
   - Vars interface reference
   - Example: Adding a new room to existing device
   - Example: Creating room variant (e.g., bathroom with humidistat)
3. Update `docs/architecture.md`:
   - Document room-based component organization
   - Update component inventory
   - Explain room component pattern and benefits
4. Update `.github/copilot-instructions.md`:
   - Add room component patterns
   - File organization conventions
   - When to use room components vs inline definitions
5. Consider deprecating `pid_sensors.yaml`:
   - If functionality fully absorbed into room components
   - Move to `components/deprecated/` if no longer needed
6. Final validation:
   - All 6 rooms (4 ground floor + 2 first floor) use room components
   - Device files significantly simplified
   - Documentation complete

#### Integration Verification

**IV1 - Existing Functionality Preserved**:
- Complete system validation: All zones function identically to before refactoring
- No entity ID changes
- No temperature control regressions

**IV2 - Integration Point Verification**:
- Documentation accurate and usable
- Future developers can add rooms using guide
- Template flexible enough for common room variants

**IV3 - Code Quality Verification**:
- Code organization significantly improved
- Device files easier to understand
- Room components promote consistency and reduce errors

---

## Epic 4 Success Metrics

**Primary Metrics**:
- **Code Organization**: 6 rooms converted to room-based components (4 ground floor + 2 first floor)
- **Code Clarity**: Room configuration co-located in single file per room
- **Maintainability**: Room changes require editing single file (not multiple sections)
- **No Regressions**: Zero temperature control issues post-refactoring

**Secondary Metrics**:
- **Documentation Quality**: Complete room component guide enables future room additions
- **Template Reusability**: Room template successfully instantiates all 6 rooms
- **Developer Experience**: Device files 30-50% shorter and easier to understand
- **Consistency**: All rooms follow identical organizational pattern

---

**END OF PRD**
