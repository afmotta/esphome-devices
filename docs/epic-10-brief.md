# Project Brief: Epic 10 - ESP32 Room Sensors & Zone Activity Tracking via UDP

**Epic:** 10 - ESP32 Room Sensors & Zone Activity Tracking via UDP  
**Date:** November 20, 2025  
**Status:** Planning  
**Version:** 1.0

---

## Executive Summary

**Product Concept:** Transition from Home Assistant-sourced room temperatures to autonomous ESP32-based room sensors that broadcast temperature and humidity data directly to distribution boards via UDP, combined with zone activity tracking that enables intelligent mixing group relay control.

**Primary Problem:** Current architecture depends on Home Assistant to provide room temperature data to distribution boards, creating operational coupling. Additionally, mixing group relays run continuously regardless of zone demand, wasting energy when no zones are open.

**Target System:** Existing 3-board ESPHome climate control installation (gruppo-miscelazione master, distribuzione-piano-terra/primo-piano slaves) with room-based PID controllers, now enhanced with external ESP32 room sensors and demand-based mixing group control.

**Key Value Proposition:** Decouple room sensing from Home Assistant infrastructure while adding intelligent demand-based control. ESP32 sensors broadcast autonomously via UDP (established in Epic 9), distribution boards track zone activity and publish binary "any zone open" indicators, and mixing groups respond only when actual heating/cooling demand exists—reducing energy waste and HA dependency simultaneously.

---

## Problem Statement

### Current State and Pain Points

**Architecture Evolution and Remaining Dependencies:**

The system has successfully implemented UDP peer-to-peer communication (Epic 9) but room temperature sensing still depends on Home Assistant:

1. **Epic 5 (HA-Only Sensors):** Room components source temperature exclusively from Home Assistant with 180-second emergency timeout
2. **Epic 9 (UDP Infrastructure):** Established packet_transport pattern for board-to-board communication, but no production deployment
3. **Current State:** Distribution boards receive room temps via HA API, not direct sensor communication

**Current Pain Points:**

1. **Operational HA Dependency for Room Sensing:**
   - Distribution boards require HA connectivity to receive room temperatures
   - HA restarts cause 180-second emergency timeout before PID shutdown
   - Room sensor updates flow through HA API, adding latency and failure points

2. **Inefficient Mixing Group Operation:**
   - Mixing group relays (circulation pumps) run continuously during heating/cooling season
   - No feedback mechanism to detect when all zones are closed
   - Energy waste when PIDs are OFF or satisfied but mixing groups keep running

3. **Asymmetric Communication Architecture:**
   - Epic 9 established UDP for supply temperatures (mixing group → distribution boards)
   - But room temperatures still flow through HA (sensors → HA → distribution boards)
   - Inconsistent patterns: some sensors use UDP, others use HA API

4. **External Sensor Management Complexity:**
   - ESP32 room sensors are standalone devices (not in this repo)
   - No clear integration pattern for external sensors to communicate with distribution boards
   - Assumption that external sensors will broadcast via UDP needs architectural support

### Impact of the Problem

**Quantified Impact:**

- **HA dependency duration:** Same as Epic 9 (30-60 seconds per restart × 2-4 restarts/month)
- **Mixing group runtime waste:** Estimated 20-30% of operating hours when no zones demand conditioning
- **Energy cost:** Circulation pumps running unnecessarily (~100W × wasted hours)
- **Sensor latency:** HA API polling adds 5-10 second delays vs. direct UDP (<1 second)

**Operational Issues:**

- Room temperature updates lag during HA performance issues
- Cannot deploy room sensors independently from HA infrastructure
- Mixing groups cannot optimize for demand-based operation
- Inconsistent architectural patterns complicate maintenance

**Strategic Misalignment:**

- Epic 9 established peer-to-peer UDP but hasn't eliminated HA operational dependencies
- Room sensors (the most critical real-time data) still route through slowest path
- Energy efficiency opportunity (demand-based relay control) unaddressed

---

## Proposed Solution

### Core Concept and Approach

**Dual-Track UDP Communication Architecture:**

Implement two complementary UDP communication patterns using ESPHome's native `packet_transport` platform established in Epic 9:

1. **Room-to-Distribution UDP Broadcasting:** External ESP32 room sensors broadcast temperature/humidity directly to distribution boards, eliminating HA dependency for room sensing
2. **Distribution-to-Mixing Zone Activity Signaling:** Distribution boards aggregate zone demand and broadcast "any zone open" binary sensors to mixing groups for intelligent relay control

**Architecture Pattern:**

```
┌─────────────────────────────────────────────────────────────────┐
│    ESP32 Room Sensor (External, per room)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  UDP Sender (Native ESPHome)                             │   │
│  │   • Broadcasts room_temperature                          │   │
│  │   • Broadcasts room_humidity (optional)                  │   │
│  │   • Update interval: 30s                                 │   │
│  │   • broadcast_id: "room_{zone_slug}_temperature"         │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ UDP Packets (Port 6053)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  Distribution Board (piano-terra/primo-piano)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  UDP Receiver (Native packet_transport)                  │   │
│  │   • Receives room temperatures from ESP32 sensors        │   │
│  │   • Updates room component temperature inputs            │   │
│  │   • Falls back to HA if UDP unavailable (3-tier)         │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Zone Activity Aggregator (Binary Sensor)                │   │
│  │   • Tracks all zone PIDs on this board                   │   │
│  │   • Logic: ANY zone PID in HEAT/COOL mode = TRUE         │   │
│  │   • Binary sensor: "{board}_any_zone_open"               │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  UDP Sender (Native packet_transport)                    │   │
│  │   • Broadcasts binary sensor state                       │   │
│  │   • Update interval: 5s (fast response)                  │   │
│  │   • broadcast_id: "{board}_any_zone_open"                │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ UDP Packets (Port 6053)
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│       Mixing Group (gruppo-miscelazione)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  UDP Receiver (Native packet_transport)                  │   │
│  │   • Receives "any_zone_open" from both distributions     │   │
│  │   • binary_sensor: piano_terra_demand, primo_piano_demand│  │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Relay Control Logic (Enhanced)                          │   │
│  │   • Ground floor relay: piano_terra_demand == TRUE       │   │
│  │   • First floor relay: primo_piano_demand == TRUE        │   │
│  │   • Relays OFF when no demand (energy savings)           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Differentiators from Existing Solutions

**vs. Current Epic 5 HA-Only Architecture:**

| Aspect | Epic 5 (Current) | Epic 10 (Proposed) | Benefit |
|--------|------------------|-------------------|---------|
| **Room Sensing** | HA API sensors | UDP + HA fallback | Lower latency, HA-independent |
| **Sensor Source** | Assumes HA integration | Native ESP32 broadcast | Decoupled architecture |
| **Mixing Control** | Always-on relays | Demand-based relays | Energy savings 20-30% |
| **Failure Mode** | 180s timeout → emergency | UDP → HA → emergency | Graceful degradation |

**vs. Alternative Approaches:**

| Approach | Pros | Cons | Decision |
|----------|------|------|----------|
| **UDP Broadcast** | Direct communication, low latency | Requires ESP32 sensors | ✅ **Selected** |
| **Keep HA-Only** | No changes needed | Maintains operational coupling | ❌ Doesn't address problem |
| **MQTT Bridge** | Reliable delivery | Adds broker dependency | ❌ Violates Epic 9 peer-to-peer principle |
| **Modbus Revival** | Proven reliable | Requires RS485 wiring to rooms | ❌ Impractical for room sensors |

### Why This Solution Will Succeed

**Leverages Epic 9 Foundation:**
- UDP packet_transport infrastructure already proven and deployed
- No new protocols or platforms to learn
- Consistent architectural pattern across all board communication

**Minimal External Dependencies:**
- ESP32 room sensors are commodity hardware (ESP32 + DHT22/BME280)
- Standard ESPHome firmware on room sensors (no custom code)
- Sensors managed independently (not in this repo's scope)

**Incremental Deployment Path:**
- Room components maintain HA fallback via 3-tier failover (Epic 9 pattern)
- Can deploy room sensors one-by-one without system disruption
- Zone activity tracking is independent feature, can deploy separately

**Energy Efficiency Wins:**
- Immediate 20-30% reduction in mixing group runtime
- Simple binary demand logic (no complex optimization)
- User-visible cost savings (lower electricity bills)

---

## Target Users

### Primary User Segment: System Operators/Homeowners

**Profile:**
- Homeowners with multi-floor climate control systems
- Technical comfort level: Medium to high (willing to manage ESPHome devices)
- Current system users who experienced Epic 3-5 improvements and Epic 9 UDP infrastructure deployment

**Current Behaviors and Workflows:**
- Monitor climate control via Home Assistant dashboard
- Perform periodic HA updates/restarts (2-4 times/month)
- Manage ESPHome device firmware updates independently per board
- Coordinate HVAC maintenance during non-critical seasons

**Specific Needs and Pain Points:**
- Need climate control to operate autonomously during HA maintenance windows
- Want to reduce energy costs by eliminating unnecessary mixing group runtime
- Expect room temperature responsiveness without HA API latency
- Desire to add/upgrade room sensors without touching HVAC board configurations

**Goals They're Trying to Achieve:**
- Minimize climate disruption during routine HA maintenance
- Lower electricity bills through intelligent demand-based control
- Deploy modern room sensors (ESP32) without architectural constraints
- Maintain system reliability while reducing operational dependencies

---

### Secondary User Segment: System Developers/Maintainers

**Profile:**
- ESPHome developers maintaining this codebase
- Future contributors adding room-based features
- System integrators deploying similar multi-board HVAC systems

**Current Behaviors and Workflows:**
- Review Epic completion reports and architecture documentation
- Extend room components with new features (window detection, occupancy, etc.)
- Debug inter-board communication issues
- Validate changes via compilation and hardware testing

**Specific Needs and Pain Points:**
- Need consistent architectural patterns across all board communication
- Want reusable components that follow established conventions (Epic 2-9 patterns)
- Require clear integration contracts for external systems (ESP32 room sensors)
- Must maintain backward compatibility during UDP migration

**Goals They're Trying to Achieve:**
- Complete Epic 9's peer-to-peer vision by eliminating remaining HA dependencies
- Establish UDP sensor broadcasting as standard pattern for future features
- Create clear separation between room sensor hardware and HVAC control logic
- Enable incremental deployment without breaking existing functionality

---

## Goals & Success Metrics

### Business Objectives

- **Eliminate operational HA dependency for room sensing:** Room temperature data flows via UDP as primary path, HA used only for fallback, enabling climate control during HA maintenance windows
- **Reduce mixing group energy consumption by 20-30%:** Implement demand-based relay control that stops circulation pumps when no zones require conditioning
- **Complete Epic 9's peer-to-peer architecture vision:** Achieve symmetric UDP communication for both supply temperatures (mixing → distribution, Epic 9) and room temperatures (sensors → distribution, Epic 10)
- **Establish UDP sensor broadcasting as standard pattern:** Create reusable integration pattern for external ESP32 sensors that future features can leverage

### User Success Metrics

- **Climate disruption during HA restarts:** Zero emergency shutdowns during planned HA maintenance (UDP sensors maintain operation)
- **Sensor response latency:** Room temperature updates reflected in PID control within 2-3 seconds (vs. 5-10 seconds via HA API)
- **Mixing group idle time:** Relays turn OFF within 30 seconds of last zone closing (vs. running continuously)
- **Deployment flexibility:** Ability to add/replace room sensors without modifying distribution board firmware

### Key Performance Indicators (KPIs)

- **UDP Sensor Uptime:** Percentage of time room sensors successfully deliver temperature via UDP (target: >95%)
- **HA Fallback Frequency:** How often 3-tier failover switches from UDP to HA tier (target: <5% of readings)
- **Energy Savings:** kWh reduction in mixing group circulation pump consumption (baseline: current always-on operation, target: 20-30% reduction)
- **Relay Response Time:** Seconds from "last zone closed" to "relay OFF" (target: <30 seconds)
- **Emergency Shutdown Elimination:** Count of PIDs entering emergency mode during HA restarts (baseline: 2-4/month, target: 0/month)
- **Compilation Success:** All device configurations compile without errors after Epic 10 component integration (target: 100%)

---

## MVP Scope

### Core Features (Must Have)

- **UDP Room Sensor Receiver Component (`components/room_sensors_udp.yaml`):** Reusable package for receiving ESP32 room sensor broadcasts
  - **Rationale:** Distribution boards must consume temperature data from external ESP32 sensors via UDP as primary tier
  - **Variables:** `zone_slug`, `zone_name`, `esp32_provider_name` (ESPHome device name of room sensor)
  - **Integration:** Uses Epic 9's `packet_transport` sensor platform with `provider` mechanism
  - **Acceptance Criteria:** Successfully receives temperature broadcasts, updates internal sensors, integrates with existing room components

- **Update `components/room_sensors.yaml` (v6):** Enhance to support UDP as primary tier, HA as fallback
  - **Rationale:** Maintain Epic 5's 3-tier failover pattern but prioritize UDP over HA
  - **Changes:** Add UDP sensor references as Tier 1, shift HA sensors to Tier 2, keep emergency timeout as Tier 3
  - **Variables:** Add `use_udp` flag (default: false), `esp32_provider_name` (required when use_udp=true)
  - **Acceptance Criteria:** Backward compatible with Epic 5 deployments, new deployments can enable UDP via flag

- **Zone Activity Binary Sensor Component (`components/zone_activity_aggregator.yaml`):** Aggregates PID states into "any zone open" signal
  - **Rationale:** Distribution boards must publish demand status to mixing groups for relay control
  - **Logic:** `lambda` that checks all zone PIDs on the board; returns TRUE if ANY PID in HEAT/COOL action (not OFF/IDLE)
  - **Variables:** `board_slug`, `zone_pids` (list of PID climate entity IDs)
  - **Output:** Binary sensor `{board_slug}_any_zone_open`
  - **Acceptance Criteria:** Binary sensor correctly reflects zone demand, updates within 5 seconds of PID state changes

- **UDP Binary Sensor Broadcaster:** Configure `packet_transport` to broadcast zone activity binary sensors
  - **Rationale:** Mixing groups need to receive demand signals from distribution boards
  - **Implementation:** Inline configuration in distribution board device files (not separate component)
  - **Update Interval:** 5 seconds (faster than room temps for responsive relay control)
  - **Acceptance Criteria:** Binary sensor values broadcast via UDP, visible to mixing group receivers

- **Mixing Group Demand-Based Relay Control:** Update mixing group relay logic to respond to zone activity signals
  - **Rationale:** Enable energy savings by stopping circulation pumps when no zones need conditioning
  - **Changes:** Modify relay automation/lambda in `devices/gruppo-miscelazione.yaml`
  - **Logic:** Ground floor relay ON when `piano_terra_any_zone_open == TRUE`, first floor relay ON when `primo_piano_any_zone_open == TRUE`
  - **Acceptance Criteria:** Relays turn OFF when no zones open, turn ON within 30 seconds of zone opening

- **Epic 9 Sensor Failover Integration:** Leverage existing `sensor_failover_3tier.yaml` for UDP → HA → Emergency
  - **Rationale:** Reuse proven failover logic from Epic 9 for room temperature sensors
  - **No Changes Required:** Component already supports 3-tier failover with configurable sensor IDs
  - **Acceptance Criteria:** Room components use failover wrapper, diagnostic sensors show active tier

### Out of Scope for MVP

- **ESP32 Room Sensor Firmware/Management:** External ESP32 sensor configuration is not part of this repo (separate project)
- **Automatic Sensor Discovery via mDNS:** Static `provider` names in configuration, no dynamic discovery
- **Per-Zone Demand Broadcasting:** Only aggregate "any zone" binary, not individual zone status
- **Humidity Sensor Integration:** Focus on temperature only for MVP; humidity support deferred to Phase 2
- **Advanced Demand Logic:** No zone priority, load balancing, or optimization algorithms—simple binary ON/OFF
- **Mixing Group PID Coordination:** Relays respond to demand only, no supply temperature adjustments based on load
- **UDP Encryption/Authentication:** Local network only, no security layer
- **Legacy HA-Only Mode Deprecation:** Keep Epic 5 HA-only pattern as fallback, don't force UDP migration
- **Room Sensor Health Monitoring Dashboard:** Basic diagnostics only (tier status), no dedicated monitoring UI

### MVP Success Criteria

**Functional Requirements:**
1. Distribution boards successfully receive room temperatures via UDP from ESP32 sensors
2. Room components operate normally with UDP as Tier 1, gracefully fall back to HA when UDP unavailable
3. Distribution boards correctly aggregate zone PID states into "any zone open" binary sensor
4. Mixing groups receive zone activity signals via UDP and control relays accordingly
5. All device configurations compile without errors after Epic 10 component integration

**Performance Requirements:**
1. Room temperature updates via UDP have <2 second latency (sensor broadcast → PID update)
2. Zone activity binary sensor updates within 5 seconds of PID state change
3. Mixing group relays respond within 30 seconds of zone demand changes

**Reliability Requirements:**
1. System operates normally during HA restart (PIDs use UDP sensors, no emergency mode)
2. Failover to HA sensors occurs automatically when UDP sensors unavailable
3. Emergency shutdown still triggers if both UDP and HA sensors fail (180-second timeout preserved)

**Deployment Requirements:**
1. Room sensors can be added incrementally (per-room deployment, not all-or-nothing)
2. Existing Epic 5 deployments continue to work without modification (backward compatibility)
3. UDP features enabled via feature flags (`use_udp: true`) in device configurations

---

## Post-MVP Vision

### Phase 2 Features (After Epic 10 MVP Proven)

- **Humidity Sensor Integration:** Extend UDP receiver to support humidity broadcasts from ESP32 sensors
  - Add humidity to 3-tier failover (UDP → HA → NaN)
  - Enable future features like condensation prevention, comfort index calculations
  - Minimal complexity once temperature pattern proven

- **Per-Zone Demand Broadcasting:** Individual zone status available to mixing groups
  - Support future hardware upgrades (per-zone mixing valves or modulating pumps)
  - Enable load balancing and priority-based supply temperature optimization
  - Requires hardware changes (out of current scope)

- **Advanced Relay Control Logic:** Intelligent mixing group optimization
  - Staged relay startup (delay between ground/first floor to reduce inrush current)
  - Predictive relay control (turn ON 30 seconds before first zone opens based on room temp trends)
  - Load-based supply temperature adjustments (more zones = higher supply temp)

- **ESP32 Room Sensor Reference Implementation:** Example ESPHome config for room sensors
  - Document broadcast_id naming conventions
  - Provide DHT22/BME280/Dallas sensor examples
  - Battery optimization patterns for ESP32 deep sleep
  - Separate repo or docs/examples/ directory

- **UDP Sensor Health Dashboard:** Enhanced monitoring and diagnostics
  - Grafana/HA dashboard showing UDP vs HA tier usage per room
  - Packet loss analysis and network quality metrics
  - Alert on persistent UDP sensor failures

### Long-Term Vision (Epic 11+)

- **Complete HA Independence:** Zero critical-path HA dependencies
  - Move climate mode coordination to UDP (heating/cooling season signals)
  - UDP-based emergency condition broadcasting (cross-board safety coordination)
  - HA becomes pure monitoring/override layer with no operational role

- **Building-Wide Sensor Mesh:** All sensors broadcast via UDP
  - Outdoor temperature sensors feed mixing groups directly (no HA)
  - Occupancy sensors broadcast presence for room-level HVAC control
  - Window sensors broadcast open/close state for window detection (Epic 7 enhancement)

- **Advanced Multi-Zone Optimization:** Cross-board intelligence
  - Whole-house load balancing (coordinate supply temps across both mixing groups)
  - Predictive preheating/precooling based on room sensor trends
  - Energy cost optimization (time-of-use rate awareness)

- **Peer-to-Peer Coordination Protocol:** Standardized UDP messaging
  - Versioned JSON schema for sensor broadcasts
  - Board capability negotiation (what sensors/controls available)
  - Backward compatibility layer for mixed-version deployments

### Expansion Opportunities

- **Multi-Site Deployments:** VPN-based UDP for multiple buildings
  - Central monitoring board receives sensor data from remote sites
  - Shared outdoor sensors reduce hardware duplication
  - Requires security layer (DTLS encryption)

- **Community Reusable Packages:** Contribute to ESPHome ecosystem
  - Generic UDP sensor broadcaster component for any ESPHome device
  - 3-tier failover as standalone package (Epic 9 pattern)
  - Zone activity aggregator for multi-zone HVAC systems

- **Third-Party Integration Opportunities:** Commercial HVAC controllers
  - UDP sensor feeds to Nest/Ecobee thermostats
  - Integration with commercial BMS systems via UDP→Modbus gateway
  - Smart vent control based on UDP room sensor data

- **Energy Analytics Platform:** Historical tracking and optimization
  - Log mixing group relay states + room sensor data
  - Calculate actual energy savings vs. baseline
  - Machine learning recommendations for setpoint optimization

---

## Technical Considerations

### Platform Requirements

- **Target Platforms:** ESP32-based boards (KC868-A6/A16 for distribution/mixing boards, generic ESP32 for room sensors)
- **Network Support:** Ethernet (W5500) and WiFi (existing network infrastructure)
- **ESPHome Version:** Requires ESPHome 2023.x+ for native `packet_transport` platform support
- **Performance Requirements:** 
  - UDP packet processing <100ms latency
  - Binary sensor state evaluation <5 seconds
  - Firmware size must fit ESP32 flash limits (current usage ~60%, Epic 10 adds ~5-10%)

### Technology Preferences

- **Transport Protocol:** UDP via ESPHome native `packet_transport` platform (Epic 9 foundation)
- **Sensor Integration:** ESPHome `sensor.template` with lambda for 3-tier failover logic
- **Binary Sensor Aggregation:** ESPHome `binary_sensor.template` with lambda evaluating climate entity states
- **Relay Control:** Existing ESPHome switch/output platforms with updated automation logic
- **Data Format:** JSON serialization (native to packet_transport, no custom encoding)

### Architecture Considerations

**Repository Structure:**
- `components/room_sensors.yaml` updated to v6 (add UDP tier support)
- `components/zone_activity_aggregator.yaml` created (new component)
- Distribution board device files updated (add UDP broadcaster config)
- Mixing group device file updated (add UDP receiver + relay logic)

**Service Architecture:**
- **Stateless UDP Broadcasting:** Room sensors and distribution boards broadcast without expecting ACK
- **Receiver-Pull Pattern:** Mixing groups pull demand signals via packet_transport provider mechanism
- **3-Tier Failover Preservation:** Epic 9's `sensor_failover_3tier.yaml` component reused unchanged

**Integration Requirements:**
- **ESP32 Room Sensors:** External devices must broadcast with `broadcast_id: "room_{zone_slug}_temperature"`
- **ESPHome Device Names:** Room sensors must have consistent ESPHome names for `provider` references
- **Network Configuration:** All boards must be on same subnet for UDP broadcast/multicast
- **Port Allocation:** Continue using port 6053 (Epic 9 default)

**Security/Compliance:**
- **Network Isolation:** HVAC boards on dedicated VLAN (existing security posture)
- **No Authentication:** Local network trust model, UDP packets unauthenticated
- **Data Privacy:** Temperature data not considered sensitive, no encryption required
- **Firewall Rules:** UDP port 6053 allowed within HVAC VLAN only

---

## Constraints & Assumptions

### Constraints

- **Budget:** Zero additional hardware cost (leverages existing ESP32 boards, network infrastructure, and Epic 9 UDP foundation)
- **Timeline:** Target 2-3 week implementation (MVP scope achievable within single epic cycle based on Epic 6-9 velocity)
- **Resources:** Single developer (James/dev-agent), no additional team members required
- **Technical:**
  - ESP32 flash memory limits (~4MB, currently 60% utilized, ~1.6MB headroom)
  - Network bandwidth constraints (home network, ~100Mbps, UDP adds <1Kbps)
  - ESPHome platform capabilities (must use native features, no custom C++ components for maintainability)
  - Same subnet requirement for UDP broadcast (no multi-site routing)
  - Existing hardware limitations (2 mixing group relays, not per-zone)

### Key Assumptions

- **External ESP32 room sensors exist and broadcast correctly:** Epic 10 assumes sensors are deployed and configured outside this repo's scope
- **ESP32 sensors follow packet_transport broadcast pattern:** Sensors use ESPHome's native UDP broadcasting with agreed-upon `broadcast_id` naming convention
- **Network reliability is sufficient for UDP:** Local Ethernet/WiFi network has <1% packet loss, no major congestion issues
- **3-tier failover provides adequate reliability:** UDP → HA → Emergency pattern (Epic 9) is sufficient for room temperature sensing
- **Binary zone demand is sufficient for relay control:** Mixing groups only need "any zone open" signal, not per-zone granularity
- **Current mixing group hardware is adequate:** Two relays (ground floor + first floor) match binary demand model, no hardware upgrades needed
- **HA will remain available as fallback tier:** Home Assistant continues running even if not critical path (monitoring, overrides, sensor fallback)
- **Epic 9 UDP infrastructure is stable:** packet_transport platform works reliably (validated in Epic 9 but not heavily load-tested)
- **Room sensor update frequency (30s) is acceptable:** PIDs can tolerate 30-second temperature update intervals without control instability
- **Zone activity can be determined from PID climate state:** PID action (HEATING/COOLING/IDLE/OFF) accurately reflects whether zone is "open" (demanding conditioning)

---

## Risks & Open Questions

### Key Risks

- **External Sensor Dependency:** Epic 10 assumes ESP32 room sensors exist and broadcast correctly; if sensors don't exist or use incompatible protocols, Epic 10 delivers infrastructure without immediate value
  - **Impact:** HIGH - Core feature unusable without sensors
  - **Likelihood:** MEDIUM - Sensors managed externally, coordination required
  - **Mitigation:** Document broadcast_id convention clearly, provide ESP32 sensor config example (Phase 2), validate sensor deployment plan before starting implementation

- **Epic 9 UDP Infrastructure Instability:** Epic 10 builds on Epic 9's packet_transport foundation which has minimal real-world testing (mixing group broadcasts but no active receivers yet)
  - **Impact:** HIGH - Bugs in Epic 9 cascade to Epic 10
  - **Likelihood:** MEDIUM - Epic 9 compiled successfully but not deployed/tested under load
  - **Mitigation:** Validate Epic 9 thoroughly before Epic 10 (network capture, receiver testing on distribution boards), create Epic 9 validation story if needed

- **PID State Interpretation Errors:** Zone activity aggregator logic assumes PID climate state (IDLE/HEATING/COOLING/OFF) accurately reflects zone demand; misinterpretation causes incorrect relay control
  - **Impact:** MEDIUM - Relays turn ON when no demand (energy waste) or OFF when demand exists (comfort loss)
  - **Likelihood:** LOW - ESPHome climate states are standardized, but lambda logic could be buggy
  - **Mitigation:** Thorough testing of aggregator logic, diagnostic logging to verify state interpretation, manual validation during deployment

- **Network Reliability Degradation:** UDP packet loss increases due to WiFi interference, network congestion, or router issues; 3-tier failover handles <5% loss but >5% causes frequent HA fallback
  - **Impact:** MEDIUM - Defeats HA independence goal if fallback used frequently
  - **Likelihood:** LOW - Current network stable (Epic 9 validated), but environmental changes possible
  - **Mitigation:** Monitor UDP sensor tier usage via diagnostic sensors, address network issues if fallback frequency exceeds 5%

- **Firmware Size Overflow:** Epic 10 components push ESP32 flash usage beyond 4MB limits, causing compilation failures or OTA update failures
  - **Impact:** HIGH - Cannot deploy Epic 10 firmware
  - **Likelihood:** LOW - Estimated +1KB usage vs. 1.6MB headroom
  - **Mitigation:** Compile-test all device configs early in implementation, optimize component size if needed, remove unused features (logging verbosity, unnecessary platforms)

- **Backward Compatibility Breakage:** Updating room_sensors.yaml to v6 breaks existing Epic 5 deployments that don't use UDP
  - **Impact:** MEDIUM - Existing rooms stop working, requires immediate rollback
  - **Likelihood:** LOW - v6 designed with `use_udp: false` default for backward compatibility
  - **Mitigation:** Thorough testing with both use_udp=false (Epic 5 mode) and use_udp=true (Epic 10 mode), feature flag pattern proven in Epic 7-8

### Open Questions

- **How do we handle ESP32 room sensor discovery?** Static `provider` names require manual configuration per room. mDNS discovery could automate but adds complexity. MVP uses static names, Phase 2 explores discovery?
  
- **What happens when mixing group relay is OFF but zone suddenly opens?** Is 30-second delay acceptable (waiting for next binary sensor broadcast), or do we need faster updates (5s already planned) or instant ON trigger via HA automation?

- **Should humidity sensors follow same UDP pattern?** Temperature is MVP, but if ESP32 sensors already have humidity (DHT22/BME280), should Epic 10 support it or defer to Phase 2?

- **How do we baseline energy consumption before Epic 10?** Need current mixing group relay runtime metrics to prove 20-30% savings claim. Manual logging? HA energy dashboard? Separate measurement story?

- **What diagnostic visibility is needed for UDP sensors?** Epic 9's sensor_failover_3tier provides tier status. Is that sufficient, or do we need per-sensor packet counters, latency histograms, etc.?

- **Should zone activity aggregator be per-board or per-mixing-circuit?** Currently designing per-board (piano_terra_any_zone_open), but mixing circuits span boards (ground floor circuit serves ground floor zones). Does aggregation need to match circuit topology?

- **How do we validate Epic 10 without full ESP32 sensor deployment?** Can we mock UDP sensors for testing (netcat, Python script), or must we wait for real sensors?

### Areas Needing Further Research

- **ESPHome packet_transport load testing:** How many concurrent sensors can one distribution board receive from? Current architecture assumes ~5-6 room sensors per board, but max capacity unknown

- **UDP packet loss behavior under poor network conditions:** 3-tier failover handles loss, but what's the user experience? How quickly does HA fallback engage? Does it cause PID control instability?

- **PID control stability with 30-second sensor updates:** Current HA sensors update ~10-30s. Is 30s UDP interval acceptable, or will PIDs oscillate? Needs thermal modeling or empirical testing

- **Binary sensor state change latency in ESPHome:** How fast does distribution board detect PID state change and broadcast updated binary sensor? Lambda evaluation frequency, climate state polling interval, UDP transmission delay—sum of these determines relay response time

- **Mixing group relay inrush current:** When relay turns ON after being OFF, does inrush current cause issues (breaker trips, voltage sag)? Current always-on operation never tests OFF→ON transition. Phase 2 staged startup might be needed

- **ESP32 sensor battery life optimization:** If room sensors are battery-powered (ESP32 deep sleep), what update intervals are viable? 30s aggressive for battery, but PIDs need frequent updates. Trade-off analysis needed for wireless sensor deployment

---

## Next Steps

### Immediate Actions

1. **Validate Epic 9 UDP Infrastructure** - Test existing packet_transport broadcasting from mixing group, verify network capture shows UDP packets, document any issues discovered
2. **Confirm ESP32 Room Sensor Deployment Plan** - Coordinate with sensor team to validate sensors will broadcast via packet_transport with agreed-upon `broadcast_id` naming convention
3. **Baseline Current Mixing Group Energy Consumption** - Measure relay runtime over 1-week period to establish baseline for 20-30% savings calculation
4. **Review and Approve Epic 10 Brief** - PO/stakeholders review this brief, provide feedback, approve scope and timeline
5. **Create Epic 10 Story Breakdown** - PO (Sarah) creates individual stories from MVP scope (estimated 5-7 stories based on Epic 6-9 patterns)
6. **Assign to Dev Agent** - James (dev-agent) begins implementation starting with component updates and compile validation

### PM Handoff

This Project Brief provides the full context for **Epic 10 - ESP32 Room Sensors & Zone Activity Tracking via UDP**. 

**Key Context for PRD Development:**
- Epic 10 builds directly on Epic 9's UDP packet_transport infrastructure
- Dual-track approach: room sensor UDP receivers (HA independence) + zone activity broadcasting (energy efficiency)
- External ESP32 sensors assumed to exist and broadcast correctly (out of repo scope)
- Reuses Epic 9's sensor_failover_3tier component for UDP → HA → Emergency failover
- Target 2-3 week implementation, zero hardware cost, single developer

**Critical Dependencies to Address in PRD:**
1. Epic 9 validation must occur before Epic 10 implementation starts
2. ESP32 room sensor deployment must coordinate with Epic 10 timeline
3. Backward compatibility with Epic 5 (room_sensors v5) is requirement, not nice-to-have

**Suggested Story Breakdown (Initial):**
- Story 10.1: Update room_sensors.yaml to v6 (add UDP tier support with use_udp flag)
- Story 10.2: Create zone_activity_aggregator.yaml component (binary sensor logic)
- Story 10.3: Distribution board UDP integration (receivers + broadcasters)
- Story 10.4: Mixing group demand-based relay control
- Story 10.5: Compilation validation and backward compatibility testing
- Story 10.6: Integration testing and Epic 9 validation
- Story 10.7: Documentation (UDP sensor guide, migration guide, completion report)

**Open Questions Needing PRD Resolution:**
- Should humidity sensors be MVP or Phase 2? (depends on ESP32 sensor capabilities)
- Do we need mocking/simulation for testing without real sensors?
- What level of diagnostic visibility is required for UDP sensors?
- Should we include ESP32 sensor reference config in Epic 10 scope?

Please start in **PRD Generation Mode**, review this brief thoroughly, and work with the user to create the PRD section by section, asking for any necessary clarification or suggesting improvements based on this foundation.
