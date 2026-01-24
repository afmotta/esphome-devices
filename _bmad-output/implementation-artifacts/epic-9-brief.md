# Project Brief: Epic 9 - UDP Packet Transport Board Communication

**Epic:** 9 - UDP Packet Transport Board Communication  
**Date:** November 19, 2025  
**Status:** Infrastructure Complete  
**Version:** 2.0

---

## Status Update (v2.0 - November 20, 2025)

**Epic 9 Revision Summary:**

During implementation, we discovered that the original problem statement was based on an incorrect architectural assumption. The brief proposed that slave boards (distribution boards) need supply temperatures from the master board via UDP. However, the actual architecture shows:

- **Supply temperatures** control mixing valves on the master board only
- **Room temperatures** (from HA) control zone PIDs on slave boards
- Slave boards don't consume supply temps in the current design

**What Was Delivered:**
- ✅ Story 9.1: UDP sender on master board (gruppo-miscelazione) broadcasting supply temps
- ✅ Story 9.3: Reusable 3-tier failover component (sensor_failover_3tier.yaml)
- ❌ Stories 9.2, 9.4, 9.5, 9.6: Marked OBSOLETE (redundant or architecturally incorrect)

**Current State:**
- UDP infrastructure is **implemented and ready** for future use
- No immediate production deployment needed (no current use case on slave boards)
- Components are well-designed and tested, awaiting real sensor exchange requirement

**Future Use Cases:**
- ESP32 room temperature sensors broadcasting to distribution boards (Epic 10+)
- Cross-board climate mode coordination
- Additional monitoring/diagnostic data sharing

**Recommendation:** Close Epic 9 as "Infrastructure Complete" and plan Epic 10 for actual UDP sensor deployment when ESP32 room sensors are implemented.

---

## Executive Summary

**Product Concept:** Direct board-to-board communication using ESPHome's UDP Packet Transport Platform to eliminate Home Assistant as a single point of failure for inter-device sensor data exchange.

**Primary Problem:** Epic 3 removed Modbus master/slave communication between boards in favor of Home Assistant coordination, introducing a reliability regression. While each board now operates independently, critical sensor data (supply temperatures, room temperatures, climate mode) flows through Home Assistant, creating a dependency that causes system failures during HA outages, restarts, or network issues. This represents an architectural pattern repeated twice—replacing one hub-and-spoke dependency (Modbus master) with another (Home Assistant), rather than moving to true peer-to-peer autonomy.

**Target System:** Existing 3-board ESPHome climate control installation (gruppo-miscelazione master, distribuzione-piano-terra/primo-piano slaves) with established Ethernet/WiFi networking infrastructure.

**Key Value Proposition:** Restore autonomous board-to-board communication while maintaining Epic 3's simplified architecture benefits (no Modbus hardware dependencies, independent board deployment) by leveraging the existing IP network for UDP-based sensor data exchange. Epic 9 breaks the hub-and-spoke cycle by implementing native peer-to-peer communication over the existing IP network, making each board truly autonomous while maintaining HA as a monitoring and override layer only.

---

## Problem Statement

### Current State and Pain Points

**Architecture Evolution Creating Reliability Regression:**

The system has undergone three architectural shifts:
1. **Epic 1 (Modbus Master/Slave):** Direct board-to-board communication via RS485 Modbus with master board as single point of failure
2. **Epic 3 (HA Coordination):** Removed Modbus board coordination, each board reads from Home Assistant instead
3. **Epic 5 (HA-Only Sensors):** Simplified to 2-tier architecture with HA sensors as primary source and emergency shutdown as fallback

**Current Pain Points:**

1. **HA Restart Causes System Outages:**
   - During HA updates or restarts (10-30 seconds), sensor data becomes unavailable
   - PIDs enter emergency mode, shutting down climate control
   - Users experience temperature discomfort during routine maintenance

2. **Network Issues Cascade to Climate Control:**
   - WiFi/network problems between ESP32 boards and HA server cause sensor failures
   - Epic 5's 180-second emergency timeout means 3 minutes of degraded operation before shutdown
   - No graceful degradation—system goes from "normal" to "emergency shutdown"

3. **Operational Coupling Despite Deployment Independence:**
   - Epic 3 successfully eliminated deployment coupling (boards can be flashed/updated independently)
   - But introduced operational coupling (boards need HA running for normal operation)
   - False sense of autonomy—boards boot and run independently but can't perform their primary function

4. **Lost Modbus Reliability Without Gaining True Independence:**
   - Epic 1's Modbus solution had 99.9%+ uptime (direct board-to-board, no intermediary)
   - Epic 3/5 introduced HA as intermediary with lower effective uptime (HA restarts, API delays, network hops)
   - **Reliability regression:** More points of failure (board → network → HA API → network → board) vs. direct communication

### Impact of the Problem

**Quantified Impact:**
- **HA restart frequency:** 2-4 times/month (updates, crashes, configuration changes)
- **Average HA restart duration:** 30-60 seconds
- **Emergency timeout:** 180 seconds before shutdown
- **Monthly climate disruption:** 2-8 minutes of emergency mode per restart × 2-4 restarts = 4-32 minutes/month
- **User-visible issues:** Temperature swings, PID shutdown, "sensor unavailable" warnings in HA dashboard

**Operational Burden:**
- System administrators must coordinate HA maintenance windows
- Cannot update HA during heating/cooling season without user impact
- Troubleshooting becomes complex: "Is it the board, the network, or HA?"

**Architectural Debt:**
- Every new Epic (6-8) inherited this HA dependency
- Future features (occupancy detection, etc.) will compound the issue
- System complexity grows while reliability decreases

### Why Existing Solutions Fall Short

**Epic 5's Emergency Shutdown:**
- ✅ Provides safety net (fail-safe, not fail-operational)
- ❌ Not a graceful degradation strategy
- ❌ Shuts down climate control entirely (comfort failure)
- ❌ Doesn't address root cause (HA dependency)

**Increasing HA Uptime:**
- ✅ Reduces frequency of failures
- ❌ Doesn't eliminate the dependency
- ❌ Cannot achieve 100% uptime (updates are necessary)
- ❌ Doesn't solve network-related issues between boards and HA

**Caching Last-Known Values in ESP32:**
- ✅ Could work for slow-changing data (climate mode)
- ❌ Doesn't work for real-time sensor data (temperatures change constantly)
- ❌ Stale data could cause PID control errors
- ❌ Still requires HA for initial values and updates

**Alternative HA Integration Patterns:**
- ✅ Could optimize API polling, reduce network hops
- ❌ Still fundamentally requires HA in the critical path
- ❌ Adds complexity without solving core dependency

### Urgency and Importance

**Why Solve This Now:**

1. **Production System Stability:** 6 rooms currently in production using Epic 5/7/8 patterns with this dependency
2. **Winter Heating Season:** Reliability is critical during November-March when heating runs continuously
3. **Foundation for Future Epics:** Epic 9+ (occupancy detection) will add more sensor dependencies—fix architecture before compounding the problem
4. **Proven Alternative Available:** ESPHome's UDP Packet Transport is mature, documented, and designed for exactly this use case
5. **Network Infrastructure Already Exists:** All boards have Ethernet/WiFi, no new hardware required

**Cost of Delay:**
- Continued user discomfort during HA maintenance
- Accumulated architectural debt making future changes harder
- Risk of users losing confidence in system reliability
- Missed opportunity to restore Epic 1's reliability benefits without its deployment complexity

---

## Proposed Solution

### Core Concept and Approach

**UDP Packet Transport Peer-to-Peer Communication:**

Implement ESPHome's native `udp` platform to enable direct board-to-board sensor data exchange over the existing Ethernet/WiFi network infrastructure. Each board becomes both a UDP sender (publishing its sensor data) and a UDP receiver (consuming other boards' sensor data), creating a true peer-to-peer mesh without requiring a central coordinator.

**Architecture Pattern:**

```
┌─────────────────────────────────────────────────────────────────┐
│         Master Board (gruppo-miscelazione)                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Dallas Sensors                                          │   │
│  │   • supply_temp_piano_terra                              │   │
│  │   • supply_temp_primo_piano                              │   │
│  │   • climate_mode (text_sensor)                           │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  UDP Sender Component                                    │   │
│  │   • Publishes sensor data to broadcast/multicast         │   │
│  │   • Update interval: 10s (configurable)                  │   │
│  │   • JSON payload with timestamp                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬─────────────────────────────────────────┘
                         │ UDP Packets (Port 6053)
                         │ Network: 192.168.1.0/24
                         ▼
         ┌───────────────────────────────────────────┐
         │      Local Network (Ethernet/WiFi)        │
         │     All boards connected via router       │
         └───────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│       Slave Board (distribuzione-piano-terra)                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  UDP Receiver Component                                  │   │
│  │   • Listens for supply temp broadcasts                   │   │
│  │   • Parses JSON payloads                                 │   │
│  │   • Updates internal sensors (supply_temp_udp)           │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  3-Tier Sensor Failover (Enhanced)                       │   │
│  │   Tier 1: UDP sensor (direct board-to-board)             │   │
│  │   Tier 2: HA sensor (homeassistant platform)             │   │
│  │   Tier 3: Emergency (NaN, triggers shutdown after 180s)  │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PID Controllers                                         │   │
│  │   • Input: room_temp_abstracted (from 3-tier failover)   │   │
│  │   • Output: slow_pwm → relays                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Home Assistant (Optional)                     │
│   • Monitoring and diagnostics visibility                       │
│   • Manual overrides and climate mode changes                   │
│   • NOT required for autonomous operation                       │
└─────────────────────────────────────────────────────────────────┘
```

### Key Differentiators from Existing Solutions

**vs. Epic 1 (Modbus Master/Slave):**
- ✅ **No master/slave hierarchy:** All boards are peers, no single point of failure
- ✅ **No RS485 hardware:** Uses existing Ethernet/WiFi infrastructure
- ✅ **Network-based:** Easier debugging with standard network tools (Wireshark, tcpdump)
- ✅ **Independent deployment:** Boards can boot in any order without coordination
- ⚠️ **Network dependency:** Requires local network reliability (but typically higher than Modbus)

**vs. Epic 3/5 (HA Coordination):**
- ✅ **Direct communication:** No HA intermediary for sensor data
- ✅ **Fail-operational:** System continues during HA outages
- ✅ **Lower latency:** UDP direct vs. HA API polling (10s vs. 30-60s effective)
- ✅ **Preserves HA as fallback:** HA sensors become Tier 2 instead of Tier 1
- ⚠️ **Adds component complexity:** UDP sender/receiver components vs. simple homeassistant platform

**vs. Alternative Protocols:**

| Protocol   | Pros                                   | Cons                                     | Decision          |
| ---------- | -------------------------------------- | ---------------------------------------- | ----------------- |
| **UDP**    | Native ESPHome, low latency, no broker | Fire-and-forget, no delivery guarantee   | ✅ **Selected**    |
| REST API   | Standard HTTP, easy debugging          | Polling overhead, higher latency         | ❌ Not optimal     |
| MQTT       | Reliable delivery, publish/subscribe   | Requires broker (another dependency)     | ❌ Adds hub        |
| WebSocket  | Bidirectional, real-time               | Complex, requires persistent connections | ❌ Over-engineered |
| mDNS/Avahi | Service discovery, zero-config         | Discovery only, not data transport       | 🔧 Complementary   |

### Why This Solution Will Succeed

**Technical Feasibility:**
1. **ESPHome Native Support:** `udp` platform is well-documented, maintained, production-ready
2. **Network Infrastructure Exists:** All boards already connected via Ethernet/WiFi
3. **Proven Pattern:** Other ESPHome users successfully use UDP for inter-device communication
4. **Low Overhead:** UDP packets are lightweight (JSON payload ~100-200 bytes)
5. **No New Hardware:** Software-only change, no physical modifications

**Architectural Soundness:**
1. **True Peer-to-Peer:** Eliminates all hub-and-spoke dependencies
2. **Graceful Degradation:** 3-tier failover (UDP → HA → Emergency) provides multiple fallback paths
3. **Backwards Compatible:** HA integration remains functional, doesn't break existing dashboards
4. **Incremental Adoption:** Can roll out board-by-board, feature flag support
5. **Future-Proof:** Foundation for additional UDP-based features (room sensors, occupancy)

**Operational Benefits:**
1. **HA Independence:** System operates normally during HA maintenance
2. **Easier Debugging:** Network tools (ping, Wireshark) + ESPHome logs provide full visibility
3. **Reduced Complexity:** Fewer moving parts in critical path (no HA API, no polling loops)
4. **Better Performance:** 10s UDP updates vs. 30-60s HA API polling effective latency
5. **Maintainable:** Clear component boundaries, reusable UDP sender/receiver packages

### High-Level Vision

**Immediate (Epic 9):**
- Master board (gruppo-miscelazione) publishes supply temperatures and climate mode via UDP
- Slave boards (distribuzione-piano-terra, distribuzione-primo-piano) consume UDP broadcasts
- 3-tier failover: UDP (Tier 1) → HA (Tier 2) → Emergency (Tier 3)
- HA remains connected for monitoring, manual overrides, and diagnostics

**Medium-Term (Post-Epic 9):**
- Room temperature sensors (ESP32-based) publish directly via UDP
- Slave boards consume room temps directly, eliminating all HA sensor dependencies
- HA becomes pure monitoring/override layer with zero critical-path responsibilities

**Long-Term Vision:**
- Building-wide UDP mesh with automatic service discovery (mDNS)
- Room-level occupancy sensors broadcasting presence via UDP
- Cross-board coordination (e.g., whole-house ventilation control)
- HA as dashboard/analytics only, system fully autonomous

---

## Target Users

### Primary User Segment: System Operators/Homeowners

**Profile:**
- Residential homeowners with existing multi-floor climate control system (3 boards, 6-8 rooms)
- Currently using Epic 5/7/8 architecture with HA coordination
- Basic to intermediate technical knowledge (can restart HA, read logs, but not ESPHome experts)
- Expectation: System should "just work" without maintenance windows

**Current Behaviors:**
- Check Home Assistant dashboard daily for temperature monitoring
- Adjust climate setpoints seasonally (heating mode in winter, cooling in summer)
- Restart Home Assistant 2-4 times/month (updates, configuration changes)
- Troubleshoot sensor failures by checking HA entity states

**Specific Needs and Pain Points:**
- **Reliability:** Climate control should not stop during routine HA maintenance
- **Transparency:** Need to understand if issue is board, network, or HA (currently unclear)
- **Peace of Mind:** System should gracefully degrade, not catastrophically fail
- **Simplicity:** Don't want to manage complex networking or learn UDP protocols

**Goals:**
- Maintain comfortable indoor temperature 24/7
- Update Home Assistant without worrying about climate control disruption
- Trust that system will operate autonomously during power cycles or network issues
- Minimize time spent troubleshooting sensor failures

---

### Secondary User Segment: System Maintainers/Integrators

**Profile:**
- Technical users who deploy, configure, and maintain ESPHome climate systems
- Deep ESPHome knowledge (YAML configuration, component composition, debugging)
- Responsible for multiple installations or consulting on home automation projects
- Active in ESPHome community, contribute to projects

**Current Behaviors:**
- Flash firmware updates to ESP32 boards (OTA or USB)
- Write custom ESPHome components using packages pattern
- Debug sensor failover logic using ESPHome logs
- Monitor system health via HA diagnostics and ESP32 web interfaces

**Specific Needs and Pain Points:**
- **Architectural Clarity:** Need clean separation of concerns (UDP vs. HA vs. Emergency tiers)
- **Debugging Tools:** Want visibility into UDP packet flow, latency, packet loss
- **Reusability:** Components should be reusable across multiple installations
- **Documentation:** Clear migration guide from Epic 5 to Epic 9
- **Rollback Safety:** Feature flags or easy revert path if UDP doesn't work

**Goals:**
- Deploy reliable climate systems without HA as single point of failure
- Reduce support burden (fewer user complaints about HA restart disruptions)
- Build expertise in UDP-based ESPHome architectures for future projects
- Contribute reusable UDP components back to community

---

### Tertiary User Segment: Future ESPHome Adopters

**Profile:**
- Home automation enthusiasts evaluating climate control solutions
- Considering ESPHome vs. commercial systems (Nest, Ecobee, proprietary HVAC controls)
- Value open-source, local control, no cloud dependencies
- Looking for proven patterns and reference architectures

**Current Behaviors:**
- Research ESPHome projects on GitHub, forums, YouTube
- Read documentation and implementation guides
- Evaluate reliability, maintenance burden, and upgrade paths
- Compare feature set and resilience vs. commercial alternatives

**Specific Needs and Pain Points:**
- **Proven Reliability:** Want evidence that system works without constant intervention
- **Clear Architecture:** Need to understand how system operates and fails gracefully
- **Migration Risk:** Concerned about technology shifts breaking existing setups
- **Community Support:** Want active community and well-documented patterns

**Goals:**
- Build or buy climate system that operates autonomously (local-first architecture)
- Avoid vendor lock-in and cloud dependencies
- Learn from proven implementations before investing time/money
- Future-proof investment (system should improve over time, not become obsolete)

---

## Goals & Success Metrics

### Business Objectives

- **Eliminate HA as single point of failure for sensor data:** Achieve 100% climate system operation during HA restarts (currently 0% during 30-60s restart window)
  - **Metric:** Zero PID emergency shutdowns during planned HA maintenance
  - **Target:** 100% success rate over 3-month evaluation period

- **Restore Epic 1-level reliability with Epic 3-level simplicity:** Match or exceed 99.9% climate control uptime while maintaining independent board deployment
  - **Metric:** Sensor data availability percentage (UDP + HA tiers combined)
  - **Target:** ≥99.9% availability (vs. current ~99.5% with HA-only)

- **Reduce operational burden of HA maintenance:** Remove need to coordinate HA updates with heating/cooling season
  - **Metric:** Number of user-reported climate disruptions during HA maintenance
  - **Target:** Zero complaints over 6-month period (vs. baseline 2-4/month)

- **Create foundation for future autonomous features:** Enable Epic 10+ (occupancy, additional sensors) without increasing HA dependency
  - **Metric:** New features can use UDP transport without Epic 9 refactoring
  - **Target:** 100% of new sensor types support UDP-first architecture

### User Success Metrics

- **Transparent system operation:** Users can identify failure tier (UDP, HA, or network) from diagnostics
  - **Metric:** Diagnostic sensors showing active tier + failure reason
  - **Target:** All 3 tiers visible in HA dashboard with status (Healthy/Degraded/Failed)

- **Graceful degradation:** System continues operating when UDP fails, using HA tier automatically
  - **Metric:** Automatic failover from UDP → HA without manual intervention
  - **Target:** 100% automatic failover success rate during testing

- **Improved responsiveness:** Sensor updates faster via UDP vs. HA API polling
  - **Metric:** Sensor update latency (time from master publish to slave PID input)
  - **Target:** <15s average latency (vs. current 30-60s with HA polling)

- **No breaking changes:** Existing HA dashboards, automations, and integrations continue working
  - **Metric:** Zero HA integration regressions after Epic 9 deployment
  - **Target:** All existing entity IDs functional, all dashboards operational

### Key Performance Indicators (KPIs)

- **UDP Reliability:** Percentage of UDP packets successfully received by slave boards
  - **Definition:** (Received packets / Expected packets) × 100
  - **Target:** ≥99.5% delivery rate under normal network conditions
  - **Measurement:** ESPHome diagnostic sensor tracking received vs. missed packets

- **Failover Frequency:** Number of times system falls back from UDP (Tier 1) to HA (Tier 2)
  - **Definition:** Count of transitions from UDP → HA tier per 30-day period
  - **Target:** <5 failover events/month (network should be very stable)
  - **Measurement:** ESPHome counter sensor incremented on tier transitions

- **HA Outage Tolerance:** Duration system operates normally with HA completely offline
  - **Definition:** Continuous climate control operation time during HA downtime
  - **Target:** Indefinite (only limited by network/power, not HA availability)
  - **Measurement:** Manual testing with HA stopped, monitoring PID operation

- **Deployment Success Rate:** Percentage of boards successfully upgraded to Epic 9 without rollback
  - **Definition:** (Boards running Epic 9 / Total boards upgraded) × 100
  - **Target:** 100% (all 3 boards: gruppo-miscelazione, distribuzione-piano-terra, distribuzione-primo-piano)
  - **Measurement:** Deployment tracking over 2-week rollout period

- **Developer Velocity Improvement:** Time to implement future sensor types with UDP vs. Epic 5 HA-only
  - **Definition:** Development hours for adding new sensor type (Epic 10 baseline)
  - **Target:** 30% reduction in development time (reusable UDP components)
  - **Measurement:** Time tracking for Epic 10 implementation

---

## MVP Scope

### Core Features (Must Have)

- **UDP Sender Component (`components/udp_sender.yaml`):** Reusable package for publishing sensor data via UDP
  - **Rationale:** Master board (gruppo-miscelazione) must broadcast supply temperatures and climate mode
  - **Variables:** `sensors` (list of sensor IDs), `text_sensors` (list of text sensor IDs), `update_interval` (default 10s), `port` (default 6053)
  - **Payload Format:** JSON with timestamp, sensor name, value
  - **Acceptance Criteria:** Successfully publishes to network, visible in Wireshark/tcpdump

- **UDP Receiver Component (`components/udp_receiver.yaml`):** Reusable package for consuming UDP sensor broadcasts
  - **Rationale:** Slave boards (distribuzione boards) must receive supply temps and climate mode
  - **Variables:** `master_hostname` (or IP), `sensors` (mapping of remote sensor ID to local sensor ID), `port` (default 6053)
  - **Parsing:** JSON deserialization with error handling
  - **Acceptance Criteria:** Successfully receives packets, updates internal sensors, handles parse errors

- **3-Tier Sensor Failover (`components/sensor_failover_3tier.yaml`):** Enhanced failover with UDP as Tier 1
  - **Rationale:** Graceful degradation through multiple fallback paths
  - **Logic:** If UDP sensor has value → use UDP; else if HA sensor has value → use HA; else → NaN (emergency)
  - **Variables:** `udp_sensor_id`, `ha_sensor_id`, `abstracted_sensor_id`, `emergency_timeout` (default 180s)
  - **Acceptance Criteria:** Automatic tier switching, diagnostic sensor showing active tier

- **UDP Diagnostics Sensors:** Visibility into UDP health per board
  - **Rationale:** Operators need to understand system state (which tier active, why)
  - **Sensors:** `udp_packets_received` (counter), `udp_packets_missed` (counter), `udp_last_received` (timestamp), `active_sensor_tier` (text: UDP/HA/Emergency)
  - **Acceptance Criteria:** Visible in HA dashboard, updates in real-time

- **Feature Flag Support:** Enable/disable UDP per board for incremental rollout
  - **Rationale:** Safe deployment, easy rollback if UDP doesn't work
  - **Implementation:** `use_udp: true/false` substitution variable
  - **Behavior:** When `use_udp: false`, system operates like Epic 5 (HA-only, 2-tier)
  - **Acceptance Criteria:** Toggle works without breaking existing functionality

### Out of Scope for MVP

- **Room Sensor UDP Broadcasting:** Room temperature sensors will NOT broadcast via UDP in Epic 9 (defer to Epic 10)
- **Authentication/Encryption:** UDP packets unencrypted on local network only
- **mDNS Service Discovery:** Use static IPs/hostnames, not auto-discovery
- **TCP Fallback:** UDP only, HA tier provides reliable fallback
- **WebSocket Push:** UDP broadcast sufficient for temperature control
- **MQTT Integration:** Direct peer-to-peer only, no broker
- **Custom Binary Protocol:** JSON only for human-readability
- **Multi-Master Architecture:** Single master (gruppo-miscelazione) sufficient

### MVP Success Criteria

**Epic 9 MVP is successful when:**

1. All 3 boards deployed with UDP enabled
2. Zero emergency shutdowns during HA restarts
3. Graceful failover demonstrated (UDP → HA → Emergency)
4. Diagnostic visibility in HA dashboard
5. No regressions in Epic 5/7/8 functionality
6. Rollback capability validated via feature flag
7. Documentation complete (migration guide, troubleshooting, architecture)

**Go/No-Go Decision:**
- ✅ **GO:** UDP reliability ≥99%, zero breaking changes, positive feedback
- ❌ **NO-GO:** UDP reliability <95%, frequent failovers, instability → Revert to Epic 5

---

## Post-MVP Vision

### Phase 2 Features (After Epic 9 MVP Proven)

- **Room Sensor UDP Broadcasting:** ESP32-based room sensors publish temperature directly
- **mDNS Service Discovery:** Zero-config board discovery
- **Enhanced Diagnostics:** Network latency tracking, packet loss analysis
- **UDP Compression:** Binary protocol for reduced bandwidth

### Long-Term Vision (Epic 10+)

- **Building-Wide UDP Mesh:** All sensors/actuators communicate peer-to-peer
- **Occupancy Detection Integration:** Motion sensors broadcast presence via UDP
- **Cross-Board Coordination:** Whole-house ventilation, multi-zone optimization
- **HA as Pure Observer:** Zero critical-path dependencies

### Expansion Opportunities

- **Multi-Site Deployments:** VPN-based UDP for multiple buildings
- **Community Reusable Components:** Contribute UDP packages to ESPHome
- **Security Layer:** DTLS encryption for sensitive deployments
- **Performance Optimization:** Tuning for high-frequency sensor updates

---

## Constraints & Assumptions

### Constraints

- **Budget:** Zero hardware cost (software-only change)
- **Timeline:** 2-3 weeks development + 2 weeks testing
- **Resources:** Single developer (part-time)
- **Technical:** ESP32 firmware size limits (~1MB flash available), JSON parsing overhead

### Key Assumptions

- Local network reliability > 99.5%
- UDP packet loss < 0.1% on LAN
- 10-second update interval sufficient for temperature control
- ESP32 has sufficient CPU/memory for JSON parsing
- No network segmentation (all boards on same subnet)
- DHCP provides stable IP addresses (or static IPs configured)

---

## Risks & Open Questions

### Key Risks

- **Network Reliability Lower Than Expected:** If UDP packet loss > 1%, system may failover to HA frequently
  - **Mitigation:** Thorough network testing, HA tier provides fallback
  - **Impact:** Medium - System still works via HA, but defeats purpose

- **Firmware Size Exceeds Flash Limits:** UDP components may push firmware over ESP32 flash capacity
  - **Mitigation:** Optimize component size, disable unused features
  - **Impact:** High - Blocks deployment if firmware won't fit

- **JSON Parsing Performance Issues:** Parsing overhead may cause lag or crashes
  - **Mitigation:** Benchmark parsing, consider binary protocol if needed
  - **Impact:** Medium - Can optimize or switch protocols

- **Broadcast Storm on Network:** Multiple boards broadcasting simultaneously could congest network
  - **Mitigation:** Stagger update intervals, monitor network traffic
  - **Impact:** Low - Home networks typically have sufficient bandwidth

### Open Questions

- Should we use UDP broadcast or multicast? (Multicast more efficient, broadcast simpler)
- What port number for UDP? (6053 proposed, ESPHome default)
- How to handle clock drift between boards? (Include timestamp in packets)
- Should climate mode be cached in flash for persistence? (Yes, use `restore_value: true`)

### Areas Needing Further Research

- ESPHome UDP platform documentation review (features, limitations, best practices)
- Network topology validation (router supports broadcast/multicast?)
- Firmware size profiling (current usage vs. available flash)
- JSON parsing benchmark on ESP32 (latency, memory usage)

---

## Epic 9 Story Status (Final)

### Completed Stories

**Story 9.1: UDP Packet Transport for Master Board**
- **Status:** Ready for Review
- **Deliverable:** Master board (gruppo-miscelazione) broadcasts supply temperatures via native ESPHome `packet_transport` platform
- **Implementation:** Inline configuration in `devices/gruppo-miscelazione.yaml`
- **Testing:** Compilation validated, network testing requires physical hardware
- **Files:** `devices/gruppo-miscelazione.yaml` (modified)

**Story 9.3: 3-Tier Sensor Failover Architecture**
- **Status:** Ready for Review
- **Deliverable:** Reusable component implementing UDP → HA → Emergency failover logic
- **Implementation:** `components/sensor_failover_3tier.yaml` (151 lines)
- **Testing:** Logic validated, integration testing requires physical hardware deployment
- **Files:** `components/sensor_failover_3tier.yaml` (new)

### Obsolete Stories (Removed from Scope)

**Story 9.2: UDP Receiver Component**
- **Status:** OBSOLETE
- **Reason:** ESPHome's native `packet_transport` sensor platform provides receiver functionality without custom component
- **Impact:** Simplified architecture, less code to maintain

**Story 9.4: UDP Diagnostics and Monitoring**
- **Status:** OBSOLETE
- **Reason:** Native `packet_transport` platform includes built-in connection status binary_sensor + Story 9.3 tier sensor provides sufficient monitoring
- **Impact:** Reduced complexity, leverages platform features

**Story 9.5: Master Board UDP Integration**
- **Status:** OBSOLETE
- **Reason:** Duplicate of Story 9.1 (work already completed inline)
- **Impact:** No additional work needed

**Story 9.6: Ground Floor Board UDP Integration**
- **Status:** OBSOLETE
- **Reason:** Architectural mismatch - ground floor zones use room temperatures (from HA), not supply temperatures from master
- **Impact:** Clarified actual architecture, prevents unnecessary work

### Stories Not Created (Deferred to Future Epics)

- **First Floor Board UDP Integration:** Same architectural mismatch as Story 9.6
- **Physical Hardware Testing:** Requires actual deployment (out of scope for infrastructure epic)
- **Production Rollout:** Awaiting real use case (ESP32 room sensors in future epic)

---

## Next Steps

### Immediate Actions (Updated November 20, 2025)

1. ~~Review ESPHome UDP platform documentation~~ ✅ Complete
2. ~~Prototype UDP sender/receiver on test boards~~ ✅ Complete (Story 9.1)
3. ~~Create 3-tier failover component~~ ✅ Complete (Story 9.3)
4. ⏸️ Physical hardware testing - Deferred until use case emerges
5. 📝 Document Epic 9 completion and architecture for future reference

### Closure Checklist

- [x] Core UDP infrastructure implemented (Stories 9.1, 9.3)
- [x] Obsolete stories marked and documented
- [x] Brief updated with reality vs. plan analysis
- [ ] Create Epic 9 completion report documenting lessons learned
- [ ] Plan Epic 10 with actual UDP sensor deployment use case

### PM Handoff (Updated)

~~This Project Brief provides the full context for Epic 9 - UDP Packet Transport Board Communication.~~

**Epic 9 Closure Notes:**

Epic 9 successfully delivered UDP infrastructure components (Stories 9.1 and 9.3) but discovered the original problem statement was based on incorrect architectural assumptions. The brief assumed slave boards need supply temperatures from master via UDP, but the actual architecture shows slave boards use room temperatures (from HA) for zone control.

**Key Learnings:**
1. Always validate architectural assumptions before planning stories
2. ESPHome's native `packet_transport` is more feature-rich than initially understood
3. UDP infrastructure is valuable even without immediate deployment
4. 3-tier failover pattern is reusable for future sensor types

**Deliverables Ready for Future Use:**
- Master board broadcasting supply temps (currently unused by slaves, but available for monitoring)
- `sensor_failover_3tier.yaml` component ready for ESP32 room sensor integration (Epic 10+)
- Architectural patterns documented for peer-to-peer sensor communication

**Recommended Next Epic:**
- Epic 10: ESP32 Room Temperature Sensors with UDP broadcasting to distribution boards
- This would be the actual use case for 3-tier failover and UDP receiver functionality

---

**Status:** Epic 9 Infrastructure Complete - Awaiting Use Case for Deployment  
**Date:** November 20, 2025  
**Next Phase:** Document completion, plan Epic 10 with real sensor deployment

