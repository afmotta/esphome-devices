---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - "_bmad-output/implementation-artifacts/epic-*.md"
  - "_bmad-output/planning-artifacts/product-brief-mev-modbus-2026-02-01.md"
date: 2026-02-01
project_name: ESPHome Multi-Floor Climate Control System
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
