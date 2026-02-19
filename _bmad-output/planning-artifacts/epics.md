---
stepsCompleted: [1, 2, 3, 'step-01-revalidated', 'step-02-epic-19-added', 'step-03-stories-formatted', 'step-04-validation-complete', 'step-01-epic-20-requirements', 'step-02-epic-20-designed', 'step-03-epic-20-stories', 'step-04-epic-20-validated']
inputDocuments:
  - "_bmad-output/implementation-artifacts/epic-*.md"
  - "_bmad-output/planning-artifacts/product-brief-mev-modbus-2026-02-01.md"
  - "_bmad-output/planning-artifacts/product-brief-esphome-devices-2026-02-19.md"
  - "_bmad-output/planning-artifacts/prd.md"
  - "_bmad-output/planning-artifacts/architecture.md"
date: 2026-02-19
project_name: ESPHome Multi-Floor Climate Control System
notes: "PRD and Architecture documents are outdated (Oct 2025). Epics 1-18 already created. Epic 19 in review. Epic 20 requirements extracted from product brief."
---

# ESPHome Climate Control - Epic Breakdown

## Overview

This document consolidates all epics for the ESPHome Multi-Floor Climate Control System, including 17 legacy epics imported from BMAD v4 and Epic 18 (MEV Modbus Migration) created in BMAD v6.

## Epic Index

| Epic | Title | Status |
|------|-------|--------|
| 1 | Autonomous Multi-Board Climate Control via RS485 Modbus | Complete |
| 2 | PID Architecture Simplification | Complete |
| 3 | HA-Coordinated Independent Boards | Complete |
| 4 | Room-Based Component Architecture | Complete |
| 5 | HA-Only Sensor Architecture | Complete |
| 6 | MEV Board Integration for First Floor | Complete |
| 7 | Window Detection & Climate Response | Complete |
| 8 | Unified State Machine Architecture | Complete |
| 9 | UDP Packet Transport Board Communication | Infrastructure Complete |
| 10 | ESP32 Room Sensors & Zone Activity Tracking via UDP | Complete |
| 11 | ESP32 Room Sensors via UDP | Deferred |
| 12 | Autonomous Dew Point Protection for Radiant Cooling | Deferred |
| 13 | Ground Floor Hybrid Radiant-Fancoil Cooling | Complete |
| 14 | Per-Room Fancoil Boost Control | Complete |
| 15 | Air Quality Sensor Broadcasting | Complete |
| 16 | First Floor MEV Intelligent Control | Draft |
| 17 | Three-Tier Seasonal Mode Selection | Draft |
| 18 | MEV Modbus Migration | New |
| 19 | Vesta Climate Framework - Open Source Extraction (Phase 1) | In Progress |
| 20 | Vesta Phase 1 Completion - Full Component Migration | New |

---

## Epic 1: Autonomous Multi-Board Climate Control via RS485 Modbus

Transform the ESPHome climate control system from Home Assistant-dependent to autonomous by implementing master/slave RS485 Modbus communication, eliminating single-point-of-failure while maintaining full HA integration and completing three-floor coverage.

**Status:** Complete
**Brief:** [epic-1-modbus-coordination.md](../../_bmad-output/implementation-artifacts/epic-1-modbus-coordination.md)

---

## Epic 2: PID Architecture Simplification

Eliminate unnecessary architectural complexity by replacing the `dual_pid.yaml` component pattern with standard ESPHome single PID climate controllers, reducing code maintenance burden and improving system clarity without changing functionality.

**Status:** Complete
**Brief:** [epic-2-pid-architecture-simplification.md](../../_bmad-output/implementation-artifacts/epic-2-pid-architecture-simplification.md)

---

## Epic 3: HA-Coordinated Independent Boards

Simplify system architecture by eliminating board-to-board Modbus master/slave communication while preserving Modbus for sensor/adapter connectivity, making each board independently coordinated through Home Assistant for improved maintainability and deployment flexibility.

**Status:** Complete
**Brief:** [epic-3-ha-coordinated-independent-boards.md](../../_bmad-output/implementation-artifacts/epic-3-ha-coordinated-independent-boards.md)

---

## Epic 4: Room-Based Component Architecture

Reorganize ESPHome components from functionality-based structure (PIDs, sensors, outputs) to room-based structure (Soggiorno, Cucina, Bagno, etc.) for improved maintainability, clarity, and easier per-room configuration management.

**Status:** Complete
**Brief:** [epic-4-room-based-component-architecture.md](../../_bmad-output/implementation-artifacts/epic-4-room-based-component-architecture.md)

---

## Epic 5: HA-Only Sensor Architecture

Introduce a simplified 2-tier temperature sensing architecture for room climate control, replacing the previous 3-tier Modbus-based system with a Home Assistant-centric approach that includes automatic emergency shutdown (3-minute timeout).

**Status:** Complete
**Brief:** [epic-5-ha-only-sensors.md](../../_bmad-output/implementation-artifacts/epic-5-ha-only-sensors.md)

---

## Epic 6: MEV Board Integration for First Floor

Implement automated Mechanical Extract Ventilation (MEV) control for the first floor by adding a KC868-A6 ESPHome board to interface with a Cappellotto AIR FRESH I H EVO ventilation unit. The board exposes control entities (4 relays, 0-10V fan speed, alarm monitoring) to Home Assistant.

**Status:** Complete
**Brief:** [epic-6-mev-brief.md](../../_bmad-output/implementation-artifacts/epic-6-mev-brief.md)

---

## Epic 7: Window Detection & Climate Response

Extend the ESPHome climate control system with intelligent window-aware climate shutdown to prevent energy waste. When a window opens, the system automatically pauses fancoil-based climate control (after 3-minute grace period) while radiant floor systems continue operating due to thermal mass characteristics.

**Status:** Complete
**Brief:** [epic-7-brief.md](../../_bmad-output/implementation-artifacts/epic-7-brief.md)

---

## Epic 8: Unified State Machine Architecture

Consolidate existing parallel emergency shutdown and window detection state machines into a single, extensible coordination pattern using an event-driven aggregator design. The `room_control_coordinator.yaml` component acts as a stateless control engine that reads condition states and coordinates PID climate control actions.

**Status:** Complete
**Brief:** [epic-8-brief.md](../../_bmad-output/implementation-artifacts/epic-8-brief.md)

---

## Epic 9: UDP Packet Transport Board Communication

Direct board-to-board communication using ESPHome's UDP Packet Transport Platform to eliminate Home Assistant as a single point of failure for inter-device sensor data exchange.

**Status:** Infrastructure Complete
**Brief:** [epic-9-brief.md](../../_bmad-output/implementation-artifacts/epic-9-brief.md)
**Note:** UDP sender on master board implemented. Stories 9.2, 9.4-9.6 marked obsolete after architectural review.

---

## Epic 10: ESP32 Room Sensors & Zone Activity Tracking via UDP

Transition from Home Assistant-sourced room temperatures to autonomous ESP32-based room sensors that broadcast temperature and humidity data directly to distribution boards via UDP, combined with zone activity tracking that enables intelligent mixing group relay control.

**Status:** Complete
**Brief:** [epic-10-brief.md](../../_bmad-output/implementation-artifacts/epic-10-brief.md)

---

## Epic 11: ESP32 Room Sensors via UDP (Peer-to-Peer Sensor Architecture)

Implement peer-to-peer ESP32 room sensor communication via UDP, eliminating Home Assistant dependency for temperature and humidity data. External ESP32 devices broadcast sensor readings directly to distribution boards using Epic 9/10 UDP infrastructure.

**Status:** Deferred (from Epic 10 Story 10.1)
**Brief:** [epic-11-brief.md](../../_bmad-output/implementation-artifacts/epic-11-brief.md)

---

## Epic 12: Autonomous Dew Point Protection for Radiant Cooling

Implement autonomous dew point protection for radiant cooling systems to prevent condensation damage when Home Assistant is unavailable. ESPHome-native dew point calculation enforces safety minimum on supply water temperature (dew point + 2°C) during cooling operations.

**Status:** Deferred (Epic 11 takes priority)
**Brief:** [epic-12-brief.md](../../_bmad-output/implementation-artifacts/epic-12-brief.md)

---

## Epic 13: Ground Floor Hybrid Radiant-Fancoil Cooling

Implement comfort-first cooling strategy for ground floor by enabling radiant floor cooling as primary system, with fancoils providing supplementary capacity when radiant system cannot meet demand. Radiant provides superior thermal comfort; fancoils offer rapid response and dehumidification.

**Status:** Complete
**Brief:** [epic-13-brief.md](../../_bmad-output/implementation-artifacts/epic-13-brief.md)

---

## Epic 14: Per-Room Fancoil Boost Control

Refactor ground floor fancoil boost coordinator from shared floor-wide decision to independent per-room control. Each room (Soggiorno, Cucina) evaluates its own temperature delta against threshold and independently activates fancoil boost mode.

**Status:** Complete
**Brief:** [epic-14-brief.md](../../_bmad-output/implementation-artifacts/epic-14-brief.md)

---

## Epic 15: Air Quality Sensor Broadcasting

Extend UDP packet transport infrastructure to broadcast CO₂ and VOC/IAQ sensor data from room sensor ESP32 devices to central climate-control board. Enables floor-wide air quality aggregation required for MEV control in Epic 16.

**Status:** Complete
**Brief:** [epic-15-brief.md](../../_bmad-output/implementation-artifacts/epic-15-brief.md)

---

## Epic 16: First Floor MEV Intelligent Control

Implement intelligent control logic for First Floor MEV using dual-path architecture: Air Quality Path (CO₂ + VOC/IAQ) drives baseline ventilation, while Humidity Control Path uses fan-speed-triggered state machine to keep humidity within configurable window (40-60%).

**Status:** Draft
**Brief:** [epic-16-brief.md](../../_bmad-output/implementation-artifacts/epic-16-brief.md)

---

## Epic 17: Three-Tier Seasonal Mode Selection

Implement automated heat pump mode selection that eliminates manual seasonal switching by combining calendar-based hard locks, weather intelligence (Phase 2), and demand-driven transitions. Calendar gates enforce mode during core seasons; shoulder seasons use PID demand to trigger transitions.

**Status:** Draft
**Brief:** [epic-17-brief.md](../../_bmad-output/implementation-artifacts/epic-17-brief.md)

---

## Epic 18: MEV Modbus Migration

**Status:** New (created 2026-02-01)
**Brief:** [product-brief-mev-modbus-2026-02-01.md](../../_bmad-output/planning-artifacts/product-brief-mev-modbus-2026-02-01.md)

Implement Modbus-first integration for Cappellotto Air Fresh I VMC, replacing relay-based control with Modbus writes for control signals (on/off, mode, dehumidify, integration) while retaining 0-10V DAC for fan speed modulation. Frees 4 relays, exposes 5 internal temperature sensors, 39 alarm types, and filter hour tracking.

### Requirements Inventory

#### Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | On/Off control via Modbus write to register 1106 (replaces relay_18) |
| FR2 | Summer/Winter mode control via Modbus write to register 1584 (replaces relay_19) |
| FR3 | Dehumidify request via Modbus write to register 1141 (replaces relay_20) |
| FR4 | Integration request via Modbus write to register 1140 (replaces relay_21) |
| FR5 | Fan speed control via existing 0-10V DAC (analog_output_7) - continuous modulation retained |
| FR6 | Read outdoor temperature sensor from register 501 |
| FR7 | Read water temperature sensor from register 502 |
| FR8 | Read exhaust temperature sensor from register 503 |
| FR9 | Read freecooling temperature sensor from register 511 |
| FR10 | Read evaporation temperature sensor from register 512 |
| FR11 | Read component states (fans, compressor, dampers, valves) from registers 385-386, 640-643 |
| FR12 | Read 39 alarm types from packed registers 769-771 |
| FR13 | Read cumulative alarm status from register 1104 |
| FR14 | Read filter hours limit from registers 1603-1604 |
| FR15 | Read filter hours current count from registers 1605-1606 |

#### Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | VMC configured with Modbus address 0x10 (one-time external setup) |
| NFR2 | VMC parity set to None (8N1) to match system bus at 9600 baud |
| NFR3 | ESP32 implements robust retry logic for Modbus communication |
| NFR4 | Home Assistant alerting for communication failures |
| NFR5 | VMC holds last commanded state on communication loss (no failover architecture) |

#### Additional Requirements

- Greenfield installation - no relay-based fallback needed
- VMC joins existing shared Modbus bus with analog output board (0x01) and relay boards (0x02, 0x03)
- Frees 4 relays (18-21) for future zone expansion
- Registers 500, 506 unavailable (headless operation) - room data provided by S1 Pro sensors
- Uses existing `modbus_controller` pattern from architecture

### FR Coverage Map

| FR | Epic 18 Sub-Epic | Description |
|----|------------------|-------------|
| FR1 | 18.1 Control | On/Off control via register 1106 |
| FR2 | 18.1 Control | Summer/Winter mode via register 1584 |
| FR3 | 18.1 Control | Dehumidify request via register 1141 |
| FR4 | 18.1 Control | Integration request via register 1140 |
| FR5 | 18.1 Control | Fan speed via 0-10V DAC |
| FR6 | 18.2 Telemetry | Outdoor temperature (register 501) |
| FR7 | 18.2 Telemetry | Water temperature (register 502) |
| FR8 | 18.2 Telemetry | Exhaust temperature (register 503) |
| FR9 | 18.2 Telemetry | Freecooling temperature (register 511) |
| FR10 | 18.2 Telemetry | Evaporation temperature (register 512) |
| FR11 | 18.2 Telemetry | Component states (registers 385-386, 640-643) |
| FR12 | 18.3 Diagnostics | 39 alarm types (registers 769-771) |
| FR13 | 18.3 Diagnostics | Cumulative alarm status (register 1104) |
| FR14 | 18.3 Diagnostics | Filter hours limit (registers 1603-1604) |
| FR15 | 18.3 Diagnostics | Filter hours current (registers 1605-1606) |

### Epic 18 Sub-Epics

#### 18.1: VMC Modbus Control

Full control of the VMC via Modbus, freeing 4 relays for future use. Enables on/off, mode switching, dehumidify and integration requests via Modbus writes while retaining continuous fan speed modulation via 0-10V DAC.

**FRs covered:** FR1, FR2, FR3, FR4, FR5

#### 18.2: VMC Telemetry & Status Monitoring

Full visibility into VMC internal state - temperatures and component operation. Enables monitoring of 5 internal temperature sensors and real-time component states for smarter automation decisions.

**FRs covered:** FR6, FR7, FR8, FR9, FR10, FR11

#### 18.3: VMC Diagnostics & Maintenance

Proactive problem detection and condition-based maintenance tracking. Decodes 39 distinct alarm types, monitors cumulative alarm status, tracks filter hours, and enables Home Assistant alerting.

**FRs covered:** FR12, FR13, FR14, FR15 + NFR3, NFR4

---

### Story 18.1.1: VMC Modbus Controller Setup

As a **system operator**,
I want **the ESP32 to establish Modbus communication with the VMC at address 0x10**,
So that **I can control and monitor the VMC via the existing RS485 bus**.

**Acceptance Criteria:**

**Given** the VMC is configured with Modbus address 0x10 and 8N1 parity
**When** the ESP32 boots and initializes the modbus_controller
**Then** communication is established with the VMC on the shared RS485 bus
**And** the modbus_controller polls successfully without errors in logs
**And** retry logic handles transient communication failures gracefully

---

### Story 18.1.2: VMC Control Switches

As a **system operator**,
I want **to control VMC power, season mode, dehumidify, and integration functions via Modbus**,
So that **I can operate the VMC without consuming 4 relays**.

**Acceptance Criteria:**

**Given** Modbus communication is established (Story 18.1.1)
**When** I toggle the VMC power switch
**Then** register 1106 is written and the VMC turns on/off accordingly

**Given** the VMC is powered on
**When** I toggle the season mode switch
**Then** register 1584 is written and the VMC switches between Summer/Winter mode

**Given** the VMC is powered on
**When** I activate the dehumidify request
**Then** register 1141 is written and the VMC enters dehumidify mode

**Given** the VMC is powered on
**When** I activate the integration request
**Then** register 1140 is written and the VMC enables integration function

**And** all switches are exposed to Home Assistant with appropriate entity IDs
**And** relays 18-21 are no longer used for VMC control

---

### Story 18.1.3: VMC Fan Speed Integration

As a **system operator**,
I want **continuous fan speed control via 0-10V DAC to work alongside Modbus control**,
So that **the demand-based ventilation algorithm can modulate fan speed in real-time**.

**Acceptance Criteria:**

**Given** VMC is controlled via Modbus (Stories 18.1.1, 18.1.2)
**When** the existing analog_output_7 sends a 0-10V signal
**Then** the VMC fan speed responds proportionally (0-100%)
**And** fan speed modulation works independently of Modbus control state
**And** the existing MEV demand algorithm continues to function

---

### Story 18.2.1: VMC Temperature Sensors

As a **system operator**,
I want **to monitor all 5 internal VMC temperature sensors via Modbus**,
So that **I can understand VMC operating conditions and enable smarter automation decisions**.

**Acceptance Criteria:**

**Given** Modbus communication is established (Story 18.1.1)
**When** the modbus_controller polls the VMC
**Then** the following temperature sensors are read and exposed to Home Assistant:
- Outdoor temperature from register 501
- Water temperature from register 502
- Exhaust temperature from register 503
- Freecooling temperature from register 511
- Evaporation temperature from register 512

**And** sensor values are scaled correctly (register value ÷ 10 = °C)
**And** sensors update at the configured polling interval
**And** NaN/unavailable is reported if communication fails

---

### Story 18.2.2: VMC Component State Monitoring

As a **system operator**,
I want **to see real-time status of VMC internal components (fans, compressor, dampers, valves)**,
So that **I can verify the VMC is operating as expected and diagnose issues**.

**Acceptance Criteria:**

**Given** Modbus communication is established (Story 18.1.1)
**When** the modbus_controller polls the VMC
**Then** the following component states are decoded from packed registers and exposed as binary sensors:
- Fan states from registers 385-386
- Compressor state
- Damper positions
- Valve states from registers 640-643

**And** each component has a descriptive entity ID (e.g., `binary_sensor.vmc_compressor_active`)
**And** states update at the configured polling interval
**And** component states are exposed to Home Assistant for dashboard display

---

### Story 18.3.1: VMC Alarm Decoding

As a **system operator**,
I want **to decode and monitor all 39 VMC alarm types**,
So that **I can quickly identify specific problems without physical inspection of the unit**.

**Acceptance Criteria:**

**Given** Modbus communication is established (Story 18.1.1)
**When** the modbus_controller polls the VMC alarm registers
**Then** the following alarms are decoded from packed registers 769-771:
- Each of the 39 alarm types is exposed as a binary sensor
- Alarms have descriptive names (e.g., `binary_sensor.vmc_alarm_filter_dirty`)

**Given** the cumulative alarm register 1104 is read
**When** any alarm is active
**Then** a master `binary_sensor.vmc_alarm_active` indicates overall alarm state

**And** alarm binary sensors are exposed to Home Assistant
**And** alarm states persist until cleared by the VMC

---

### Story 18.3.2: VMC Filter Maintenance Tracking

As a **system operator**,
I want **to monitor filter runtime hours and compare against the configured limit**,
So that **I can perform condition-based filter maintenance instead of calendar-based**.

**Acceptance Criteria:**

**Given** Modbus communication is established (Story 18.1.1)
**When** the modbus_controller polls filter maintenance registers
**Then** the following sensors are exposed:
- Filter hours limit from registers 1603-1604 (32-bit value)
- Filter hours current from registers 1605-1606 (32-bit value)

**And** a calculated `sensor.vmc_filter_hours_remaining` shows hours until maintenance
**And** a `binary_sensor.vmc_filter_maintenance_due` triggers when remaining hours ≤ 0
**And** sensors are exposed to Home Assistant for dashboard and automation use

---

### Story 18.3.3: VMC Communication Health & Alerting

As a **system operator**,
I want **Home Assistant to alert me when VMC Modbus communication fails**,
So that **I'm aware of connectivity issues that could affect control**.

**Acceptance Criteria:**

**Given** the modbus_controller is configured with robust retry logic
**When** communication with the VMC fails
**Then** the ESP32 retries according to configured parameters
**And** after sustained failure, `binary_sensor.vmc_communication_error` becomes active

**Given** communication error is detected
**When** the error persists for more than 60 seconds
**Then** Home Assistant can trigger notifications (via existing automation patterns)

**Given** communication was previously failed
**When** communication recovers
**Then** `binary_sensor.vmc_communication_error` clears
**And** the VMC resumes normal operation with last commanded state

---

## Epic 18 Story Summary

| Story | Title | FRs/NFRs | Status |
|-------|-------|----------|--------|
| 18.1.1 | VMC Modbus Controller Setup | NFR1, NFR2, NFR3 | Ready |
| 18.1.2 | VMC Control Switches | FR1, FR2, FR3, FR4 | Ready |
| 18.1.3 | VMC Fan Speed Integration | FR5 | Ready |
| 18.2.1 | VMC Temperature Sensors | FR6, FR7, FR8, FR9, FR10 | Ready |
| 18.2.2 | VMC Component State Monitoring | FR11 | Ready |
| 18.3.1 | VMC Alarm Decoding | FR12, FR13 | Ready |
| 18.3.2 | VMC Filter Maintenance Tracking | FR14, FR15 | Ready |
| 18.3.3 | VMC Communication Health & Alerting | NFR3, NFR4 | Ready |

**Total: 8 stories covering all 15 FRs and 4 NFRs**

---

## Epic 19: Vesta Climate Framework - Open Source Extraction (Phase 1)

**Status:** In Progress (created 2026-02-07)
**Brief:** [epic-19-brief.md](../../_bmad-output/planning-artifacts/epic-19-brief.md)

Extract and generalize 5 production-proven ESPHome climate control components from the esphome-devices codebase into a new open-source project called **Vesta** (Roman goddess of the hearth). The "Base + Boost" pattern — where radiant floor provides efficient baseline comfort and fancoils activate as a responsive boost layer — is the hero component and project differentiator.

### Component Inventory

| Component | Type | Source Lines | Target |
|-----------|------|-------------|--------|
| Trend Sensor | Utility | 48 | `packages/utils/trend_sensor.yaml` |
| Failover Sensor | Utility | 111 | `packages/utils/failover_sensor.yaml` |
| Proportional Demand Sensor | Utility | 83 | `packages/utils/proportional_demand_sensor.yaml` |
| Fancoil Boost Coordinator | Coordinator | 313 | `packages/coordinators/fancoil_boost.yaml` |
| MEV Ventilation Coordinator | Coordinator | 365 | `packages/coordinators/mev_ventilation.yaml` |

### Story Summary

| Story | Title | Points | Dependencies | Status |
|-------|-------|--------|-------------|--------|
| 19.1 | Repository Scaffolding | 1 | None | Review |
| 19.2 | Extract Trend Sensor (Quick Win) | 1 | 19.1 | Review |
| 19.3 | Extract Failover Sensor | 2 | 19.1 | Review |
| 19.4 | Extract Proportional Demand Sensor | 1 | 19.2 | Review |
| 19.5 | Extract Fancoil Boost Coordinator (Hero) | 3 | 19.2 | Review |
| 19.6 | Extract MEV Ventilation Coordinator | 2 | 19.4 | Review |
| 19.7 | Documentation, Principles & Examples | 2 | All | Review |

**Total: 7 stories, 12 story points**

**Story files:** `_bmad-output/implementation-artifacts/19-*.md`

---

### Story 19.1: Repository Scaffolding

As a **climate control enthusiast and ESPHome community member**,
I want **a well-structured open-source repository called Vesta Climate Framework**,
So that **production-proven ESPHome climate control components can be shared with the community and adopted by other multi-zone HVAC integrators**.

**Acceptance Criteria:**

**Given** a new open-source project is being created
**When** the repository is initialized at `vesta/`
**Then** the directory structure matches: `packages/utils/`, `packages/coordinators/`, `docs/`, `examples/`
**And** README.md explains the Base + Boost innovation, 3-tier package structure, and component overview table
**And** MIT LICENSE file is present
**And** CONTRIBUTING.md describes component proposal process, YAML coding standards, and testing expectations
**And** `.gitignore` covers ESPHome build artifacts

---

### Story 19.2: Extract Trend Sensor (Quick Win)

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable trend sensor package that calculates rate-of-change per minute with smoothing**,
So that **I can detect temperature/humidity trends and enable predictive climate control logic**.

**Acceptance Criteria:**

**Given** the source component `components/trend_sensor.yaml` (48 lines) is production-proven
**When** it is extracted to `packages/utils/trend_sensor.yaml`
**Then** it is self-contained and compiles with only its declared parameters
**And** all parameters are documented with types and defaults
**And** `docs/trend-sensor.md` is written with usage examples
**And** the extraction pattern (header format, naming convention, doc structure) is established for subsequent stories

---

### Story 19.3: Extract Failover Sensor

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable 3-tier sensor failover package that automatically switches between sensor sources**,
So that **my climate control system degrades gracefully when sensors fail instead of shutting down**.

**Acceptance Criteria:**

**Given** the source component `components/failover_sensor.yaml` (111 lines) is production-proven
**When** it is extracted to `packages/utils/failover_sensor.yaml`
**Then** tier names are generalized (Primary/Secondary/Emergency instead of HA/UDP/Emergency)
**And** parameter names are generic (`primary_sensor`/`secondary_sensor` instead of `ha_sensor`/`udp_sensor`)
**And** tier architecture is documented with ASCII diagram in `docs/failover-sensor.md`
**And** automatic recovery behavior is explained
**And** usage example shows a realistic climate control scenario

---

### Story 19.4: Extract Proportional Demand Sensor

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable proportional demand sensor that converts any sensor reading into a 0-100% demand signal with optional rate-of-change boost**,
So that **I can drive ventilation fan speeds, valve positions, or other actuators proportionally based on environmental conditions**.

**Acceptance Criteria:**

**Given** the source component `components/proportional_demand_sensor.yaml` (83 lines) depends on trend_sensor
**When** it is extracted to `packages/utils/proportional_demand_sensor.yaml`
**Then** parameter names are component-agnostic (no `mev_` prefix)
**And** dependency on trend_sensor is clearly documented
**And** rate boost feature is explained with practical example in `docs/proportional-demand.md`
**And** at least 2 usage examples are provided (humidity demand, CO2 demand)

---

### Story 19.5: Extract Fancoil Boost Coordinator (Hero)

As a **multi-zone HVAC integrator using ESPHome**,
I want **the "Base + Boost" pattern as a reusable coordinator that automatically activates fancoils when radiant floor cooling reaches its limits**,
So that **I get efficient baseline cooling from radiant floors with responsive fancoil boost when conditions demand it, without manual switching**.

**Acceptance Criteria:**

**Given** the source component `components/fancoil_boost_coordinator.yaml` (313 lines) is the project's hero component
**When** it is extracted to `packages/coordinators/fancoil_boost.yaml`
**Then** all three activation triggers are documented with rationale (reactive temperature, reactive humidity, predictive PID saturation)
**And** deactivation AND-logic is documented
**And** hysteresis dead band and minimum time-in-state anti-oscillation behavior is explained
**And** a complete integration example is provided (zone with radiant PID + fancoil + boost coordinator)
**And** dependency on trend_sensor is documented
**And** all diagnostic sensors are listed and explained

---

### Story 19.6: Extract MEV Ventilation Coordinator

As a **multi-zone HVAC integrator using ESPHome**,
I want **a reusable MEV ventilation coordinator with multi-demand orchestration and humidity cascade state machine**,
So that **I can control mechanical extract ventilation systems that respond to CO2, IAQ, and humidity with automatic mode escalation**.

**Acceptance Criteria:**

**Given** the source component `components/mev.yaml` (365 lines) depends on proportional_demand_sensor
**When** it is extracted to `packages/coordinators/mev_ventilation.yaml`
**Then** multi-demand MAX aggregation pattern is documented
**And** humidity cascade state machine is documented with state diagram (Fan Only → Dehumidifying → Cooling)
**And** escalation/de-escalation timing is explained
**And** season awareness is documented (cooling state disabled in winter)
**And** dependency chain is documented (proportional_demand → trend_sensor)
**And** hardware requirements are listed (relays, DAC, sensors)

---

### Story 19.7: Documentation, Principles & Examples

As a **potential Vesta user discovering the project**,
I want **clear documentation of the architectural philosophy, a getting-started guide, and a complete working example**,
So that **I can understand how the components fit together and start using them in my own ESPHome installation**.

**Acceptance Criteria:**

**Given** all 5 components have been extracted (Stories 19.2-19.6)
**When** the documentation is finalized
**Then** `docs/principles.md` documents all 9 foundational principles with explanations
**And** `docs/getting-started.md` provides a clear onboarding path with prerequisites and recommended starting point
**And** `examples/two_zone_radiant_fancoil.yaml` is a complete, commented, compilable example showing 2 zones with radiant PID, fancoil, boost coordinator, trend sensor, and failover sensor
**And** README links to all component docs and includes the component overview table

---

## Epic 20: Vesta Phase 1 Completion - Full Component Migration

**Status:** New (created 2026-02-19)
**Brief:** [product-brief-esphome-devices-2026-02-19.md](../../_bmad-output/planning-artifacts/product-brief-esphome-devices-2026-02-19.md)

Complete Vesta Phase 1 by migrating all remaining reusable components (15 additional packages) from esphome-devices into Vesta, reorganizing the package structure into a scalable taxonomy (`components/`, `coordinators/`, `devices/`), creating full documentation, and migrating esphome-devices to consume Vesta as an external dependency.

### Requirements Inventory

#### Functional Requirements

| ID | Requirement |
|----|-------------|
| FR1 | Restructure package taxonomy: move `utils/` contents to `components/`, maintain `coordinators/`, create `devices/modbus-io/` |
| FR2 | Extract 10 new components to `components/`: pid, pid_sensors, pid_autotune, pid_autotune_with_fancoil, radiant, fancoil, heat_only_radiant, mixing_pump, direct_pump, dew_point_sensor |
| FR3 | Extract 1 new coordinator to `coordinators/`: seasonal_mode |
| FR4 | Extract 4 new device drivers to `devices/modbus-io/`: modbus_relay_board, modbus_relay_switch, modbus_analog_output, modbus_analog_outputs_board |
| FR5 | Create documentation for all 15 new components and update existing 5 component docs, README, and examples for new paths |
| FR6 | Migrate esphome-devices to consume Vesta via GitHub remote includes, remove all local copies of migrated components, verify production system compiles |

#### Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR1 | All components must compile standalone with `esphome config` validation using only declared parameters |
| NFR2 | No component may reference esphome-devices-specific entities (room names, hardware IDs) |
| NFR3 | Every component's parameters must be documented with types and defaults |
| NFR4 | Dependency chains must be explicit and documented (e.g., radiant → pid → trend_sensor) |

#### Additional Requirements

- Follow the extraction pattern established in Epic 19 (header comment block, parameter naming convention, doc structure)
- Each component doc page must include parameter reference table + usage example
- Existing Phase 1 examples must compile after restructure (no regressions)
- esphome-devices must compile with zero local copies of migrated components

### FR Coverage Map

| FR | Epic 20 | Description |
|----|---------|-------------|
| FR1 | 20.1 Restructure | Package taxonomy reorganization (utils/ → components/, create devices/modbus-io/) |
| FR2 | 20.2, 20.3 Components | 10 new components extracted to components/ (6 PID stack + 4 others) |
| FR3 | 20.4 Coordinator | Seasonal mode coordinator extracted to coordinators/ |
| FR4 | 20.5 Devices | 4 Modbus I/O drivers extracted to devices/modbus-io/ |
| FR5 | 20.6 Docs | Full documentation for all 20 components |
| FR6 | 20.7 Migration | esphome-devices consumes Vesta via GitHub remote includes |

### Story Summary

| Story | Title | FRs | Components | Status |
|-------|-------|-----|------------|--------|
| 20.1 | Package Restructure | FR1 | 3 moved | Ready |
| 20.2 | Extract PID Stack | FR2 (partial) | 6 new | Ready |
| 20.3 | Extract Heat-Only Radiant, Pumps & Dew Point | FR2 (remainder) | 4 new | Ready |
| 20.4 | Extract Seasonal Mode Coordinator | FR3 | 1 new | Ready |
| 20.5 | Extract Modbus I/O Drivers | FR4 | 4 new | Ready |
| 20.6 | Documentation for New Components | FR5 | 15 doc pages | Ready |
| 20.7 | Migrate esphome-devices to Vesta | FR6 | 20 migrated | Ready |

**Total: 7 stories covering all 6 FRs and 4 NFRs**

---

### Story 20.1: Package Restructure

As a **Vesta user**,
I want **the package structure reorganized into a clear taxonomy (components/, coordinators/, devices/)**,
So that **I can find packages intuitively and the framework scales as more components are added**.

**Acceptance Criteria:**

**Given** the existing Vesta repo has `packages/utils/` with trend_sensor, failover_sensor, proportional_demand_sensor
**When** the restructure is applied
**Then** all three files are moved to `packages/components/`
**And** `packages/utils/` is removed
**And** `packages/devices/modbus-io/` directory is created
**And** all existing docs are updated to reference new paths
**And** all existing examples compile with new package paths
**And** README component overview table reflects the new structure
**And** existing Phase 1 components still compile (no regressions)

---

### Story 20.2: Extract PID Stack

As a **multi-zone HVAC integrator using ESPHome**,
I want **production-tested PID controller wrappers with presets for radiant and fancoil systems**,
So that **I can set up proportional zone control with proven defaults instead of tuning from scratch**.

**Acceptance Criteria:**

**Given** the source components exist in esphome-devices
**When** the following 6 components are extracted to `packages/components/`:
- `pid.yaml` — PID controller wrapper with production-tested presets
- `pid_sensors.yaml` — PID input/output diagnostic sensors
- `pid_autotune.yaml` — PID auto-tuning logic
- `pid_autotune_with_fancoil.yaml` — Auto-tune variant for fancoil systems
- `radiant.yaml` — Radiant floor heating/cooling zone
- `fancoil.yaml` — Fancoil unit control (analog 0-10V)

**Then** each component compiles standalone with only its declared parameters
**And** no component references esphome-devices-specific entities
**And** all parameters have header comment blocks with purpose, required vars, optional vars
**And** dependency chains are documented in headers (e.g., radiant depends on pid)
**And** the Epic 19 extraction pattern is followed (header format, parameter naming convention)

---

### Story 20.3: Extract Heat-Only Radiant, Pumps & Dew Point

As a **multi-zone HVAC integrator using ESPHome**,
I want **reusable packages for heat-only radiant zones, pump control, and dew point calculation**,
So that **I can compose these building blocks into my system without writing boilerplate YAML**.

**Acceptance Criteria:**

**Given** the source components exist in esphome-devices
**When** the following 4 components are extracted to `packages/components/`:
- `heat_only_radiant.yaml` — Heat-only radiant variant
- `mixing_pump.yaml` — Mixing valve + pump control
- `direct_pump.yaml` — Direct pump control
- `dew_point_sensor.yaml` — Dew point calculation utility

**Then** each component compiles standalone with only its declared parameters
**And** no component references esphome-devices-specific entities
**And** all parameters have header comment blocks
**And** the Epic 19 extraction pattern is followed

---

### Story 20.4: Extract Seasonal Mode Coordinator

As a **multi-zone HVAC integrator using ESPHome**,
I want **a seasonal mode coordinator that manages heat/cool mode transitions based on calendar and demand signals**,
So that **my system switches between heating and cooling seasons automatically without manual intervention**.

**Acceptance Criteria:**

**Given** the source component `components/seasonal_mode.yaml` exists in esphome-devices
**When** it is extracted to `packages/coordinators/seasonal_mode.yaml`
**Then** the component compiles standalone with only its declared parameters
**And** no references to esphome-devices-specific entities remain
**And** calendar-based mode locking is parameterized (configurable date ranges)
**And** demand-driven shoulder season transitions are parameterized
**And** all parameters have header comment blocks
**And** the Epic 19 extraction pattern is followed

---

### Story 20.5: Extract Modbus I/O Drivers

As a **multi-zone HVAC integrator using ESPHome with Modbus expansion boards**,
I want **parameterized Modbus relay board and analog output drivers**,
So that **I can add I/O expansion to my system without writing Modbus register mappings from scratch**.

**Acceptance Criteria:**

**Given** the source components exist in esphome-devices
**When** the following 4 components are extracted to `packages/devices/modbus-io/`:
- `modbus_relay_board.yaml` — Modbus relay board driver
- `modbus_relay_switch.yaml` — Individual Modbus relay switch
- `modbus_analog_output.yaml` — Modbus 0-10V DAC output
- `modbus_analog_outputs_board.yaml` — Modbus analog outputs board driver

**Then** each component compiles standalone with only its declared parameters
**And** drivers are board-agnostic (work with any Modbus relay/analog board, not just specific hardware)
**And** no references to esphome-devices-specific entities remain
**And** all parameters have header comment blocks
**And** the Epic 19 extraction pattern is followed

---

### Story 20.6: Documentation for New Components

As a **Vesta user discovering the framework**,
I want **a doc page for every new component with parameter reference and usage examples**,
So that **I can understand what each component does and how to include it in my config**.

**Acceptance Criteria:**

**Given** all 15 new components have been extracted (Stories 20.2-20.5)
**When** documentation is created
**Then** each of the 15 new components has a dedicated doc page in `docs/`
**And** each doc page includes: purpose description, parameter reference table (name, type, required/optional, default), usage example with `!include` and vars
**And** the README component overview table lists all 20 components with correct paths and links to doc pages
**And** the getting-started guide is updated to reference the new component categories
**And** doc pages for integrators include quick-reference parameter tables
**And** doc pages for complex components (seasonal_mode, PID stack) include narrative "why" sections for enthusiasts

---

### Story 20.7: Migrate esphome-devices to Vesta

As the **esphome-devices system operator**,
I want **the production system updated to consume Vesta packages via GitHub remote includes**,
So that **there are no local duplicates of migrated components and the system validates that Vesta works as an external dependency**.

**Acceptance Criteria:**

**Given** all 20 components are available in the Vesta repo (5 existing + 15 new)
**When** esphome-devices is migrated
**Then** all room configs and device configs reference Vesta packages via GitHub remote includes instead of local files
**And** all 20 local component files that were migrated to Vesta are removed from `esphome-devices/components/`
**And** `esphome config` validates successfully for the full production configuration
**And** components that remain local (mev_demand.yaml, mev_modbus.yaml, room templates) are unaffected
**And** the migration is documented (which files moved, how to update includes)
