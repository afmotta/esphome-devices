# Project Brief: Epic 11 - ESP32 Room Sensors via UDP (Peer-to-Peer Sensor Architecture)

**Epic:** 11 - ESP32 Room Sensors via UDP  
**Date:** November 24, 2025  
**Status:** Draft  
**Priority:** High - Eliminates HA Dependency for Room Sensing

**Origin:** Story 10.1 deferred from Epic 10

---

## Executive Summary

Epic 11 implements peer-to-peer ESP32 room sensor communication via UDP, eliminating Home Assistant dependency for temperature and humidity data. External ESP32 devices (one per room) will broadcast sensor readings directly to distribution boards using the proven UDP infrastructure from Epic 9/10. This completes the autonomous sensor architecture, enabling the system to operate independently during HA outages while maintaining full integration when HA is available.

**Problem:** Current Epic 5 HA-only architecture means room temperature/humidity data flows through Home Assistant API, creating operational coupling and sensor latency. During HA restarts or network issues, room sensors become unavailable for 30-180 seconds.

**Solution:** ESP32 room sensors broadcast temperature/humidity via UDP (port 6053) every 10 seconds. Distribution boards receive broadcasts and use 3-tier failover (UDP → HA → NaN) for resilient room sensing independent of Home Assistant.

---

## Context: Epic 10 Deferral

**Why Story 10.1 Was Deferred:**

Epic 10's original scope included both ESP32 room sensors (Story 10.1) and zone activity tracking (Stories 10.2-10.7). During implementation, Story 10.1 was deferred to focus on validating Epic 9's UDP infrastructure with simpler binary sensor broadcasts (zone demand: true/false).

**What Epic 10 Delivered:**
- ✅ Zone activity aggregation and UDP broadcasting (binary sensors)
- ✅ Demand-based relay control (mixing group responds to zone demand)
- ✅ Epic 9 UDP infrastructure validated in production
- ✅ Proven pattern for UDP binary sensor broadcasts

**What Epic 10 Deferred (Story 10.1):**
- ❌ ESP32 room sensors broadcasting via UDP
- ❌ `sensor_failover_3tier.yaml` UDP tier integration
- ❌ External sensor device templates/examples

**Why Epic 11 Now:**
- Epic 9 proved UDP **float sensor** broadcasts (supply temperatures)
- Epic 10 proved UDP **binary sensor** broadcasts (zone demand)
- Epic 11 extends float sensor pattern to **room sensors** (temperature/humidity)
- UDP infrastructure is mature and production-validated

---

## Problem Statement

### Current Architecture and Pain Points

**Epic 5 HA-Only Sensor Architecture:**

Current room sensing relies exclusively on Home Assistant:
1. ESP32 room sensors → Home Assistant (ESPHome integration)
2. Home Assistant → Distribution boards (HA API pull)
3. Distribution boards → PID controllers (local sensor reference)

**Pain Points:**

1. **Operational HA Dependency:**
   - Room sensor updates require HA connectivity
   - HA restarts cause 30-180 second sensor blackout
   - API latency adds 5-10 seconds to sensor updates

2. **Asymmetric Communication Architecture:**
   - Supply temps use UDP (mixing → distribution) - fast, autonomous
   - Zone demand uses UDP (distribution → mixing) - fast, autonomous
   - **Room temps use HA API** (sensors → HA → distribution) - slow, HA-dependent

3. **Emergency Shutdown Delays:**
   - Epic 5 emergency condition waits 180 seconds for HA sensor timeout
   - PID continues operating on stale data during HA issues
   - Cannot distinguish "sensor failure" from "HA unavailable"

4. **Sensor Deployment Complexity:**
   - ESP32 room sensors must be integrated into HA first
   - Cannot test room sensors independently from HA infrastructure
   - Configuration changes require HA restart + ESPHome recompile

### Impact Quantification

**Operational Impact:**
- **HA restart frequency:** 2-4 times/month (updates, config changes)
- **Sensor blackout duration:** 30-180 seconds per restart
- **API latency overhead:** 5-10 seconds per sensor update
- **Emergency response delay:** 180 seconds to detect HA failure

**User Experience:**
- Stale room temperatures during HA maintenance windows
- False emergency shutdowns when HA slow (not failed)
- Inconsistent sensor update rates (10s UDP vs 30s+ HA)

**Strategic Misalignment:**
- Epic 9/10 established peer-to-peer UDP for board communication
- Room sensors (most critical data) still route through slowest path
- Autonomous operation goal incomplete without autonomous room sensing

---

## Proposed Solution

### Core Approach

**3-Tier UDP Room Sensor Failover Architecture:**

Implement `sensor_failover_3tier.yaml` component with intelligent failover:

1. **Tier 1 (Preferred): UDP Broadcast from ESP32 Room Sensors**
   - External ESP32 devices broadcast temp/humidity every 10 seconds
   - Distribution boards receive via `packet_transport` platform
   - Fast updates (<1 second latency), autonomous operation

2. **Tier 2 (Fallback): Home Assistant API**
   - Existing Epic 5 HA sensor integration
   - 30-second timeout on UDP tier before falling back
   - Maintains backward compatibility with Epic 5 deployments

3. **Tier 3 (Emergency): NaN (Emergency Shutdown)**
   - No valid sensor data available (UDP failed + HA failed)
   - Triggers Epic 8 emergency condition after 180 seconds
   - Coordinator forces PID OFF (existing Epic 5 behavior)

### Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│ ESP32 Room Sensor (External Device, per room)              │
│                                                             │
│  Temperature Sensor (Dallas/DHT22/SHT3x)                   │
│  Humidity Sensor (DHT22/SHT3x)                             │
│  UDP Broadcaster (packet_transport platform)               │
│    - Broadcast ID: "{zone}_room_temp"                      │
│    - Broadcast ID: "{zone}_room_humidity"                  │
│    - Update interval: 10 seconds                           │
│    - Port: 6053 (ESPHome default)                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │ UDP Broadcast
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Distribution Board (A16)                                    │
│                                                             │
│  UDP Receiver (packet_transport platform)                  │
│    - Provider: "{zone}_room_sensor"                        │
│    - Sensors: temperature + humidity                       │
│                                                             │
│  3-Tier Failover (sensor_failover_3tier.yaml)             │
│    - Tier 1: UDP sensor (10s timeout)                     │
│    - Tier 2: HA sensor (30s timeout)                      │
│    - Tier 3: NaN → emergency condition                    │
│                                                             │
│  Room Component (room_sensors.yaml v6)                     │
│    - Delegates to sensor_failover_3tier                    │
│    - Exposes: {zone}_room_temp_abstracted                 │
│                                                             │
│  PID Controller (pid.yaml)                                 │
│    - Uses: {zone}_room_temp_abstracted                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Key Differentiators

**vs. Epic 5 HA-Only:**
- ✅ Autonomous operation (survives HA failures)
- ✅ Fast updates (10s vs 30s+)
- ✅ Low latency (<1s vs 5-10s)
- ✅ Distinguishes sensor failure from HA unavailability

**vs. Modbus Sensors (Story 1.6):**
- ✅ No wiring required (WiFi-based)
- ✅ Flexible placement (not limited by RS485 distance)
- ✅ Easy expansion (add sensor = new ESP32)
- ✅ Independent power (USB powered, not 12V DC)

**vs. Fixed UDP Only:**
- ✅ Backward compatible (HA fallback preserves Epic 5 behavior)
- ✅ Graceful degradation (still works if UDP fails)
- ✅ Deployment flexibility (can migrate room-by-room)

---

## Target System

### Primary: Ground Floor Room Sensors

**Zones requiring ESP32 room sensors:**
- Soggiorno (living room)
- Cucina (kitchen)
- Bagno (bathroom)
- Anticamera (entryway)
- Sala Pranzo (dining room)
- Locale Tecnico (technical room)

**Hardware per room:**
- ESP32 board (ESP32-WROOM-32 or similar)
- Temperature sensor (Dallas DS18B20 or SHT3x combo)
- Humidity sensor (SHT3x or DHT22)
- USB power supply
- 3D printed enclosure (optional)

### Secondary: First Floor Room Sensors (Future)

**Zones:**
- 8 rooms on first floor (bagno grande, camera 1-6, corridoio)

**Current state:** Will use same ESP32 sensor template as ground floor

---

## Goals & Success Metrics

### Operational Objectives

**Primary Goal:** Eliminate HA dependency for room temperature sensing

**Metrics:**
- ✅ UDP sensor latency: <1 second from broadcast to PID input
- ✅ HA restart impact: PIDs continue operating on UDP sensors (zero blackout)
- ✅ Failover reliability: <30 seconds to detect UDP failure and switch to HA
- ✅ Sensor availability: >99.9% (only fails if UDP + HA both down)

### User Experience Targets

**Transparent Operation:**
- Room sensors "just work" regardless of HA state
- No configuration changes needed for HA maintenance
- Clear diagnostic sensors showing active tier (UDP/HA/Emergency)

**Performance:**
- Real-time sensor updates (10-second refresh)
- Immediate PID response to temperature changes
- No false emergency shutdowns during HA restarts

### Code Quality Metrics

- Flash usage increase: <5% (UDP receiver + failover logic)
- RAM usage increase: <2% (UDP packet buffers)
- Compilation: Zero errors, zero warnings
- Backward compatibility: Epic 5 deployments continue working

---

## MVP Scope

### Core Features (Must Have)

**1. sensor_failover_3tier.yaml Component**
- 3-tier failover logic: UDP → HA → NaN
- Template sensor with lambda implementing tier selection
- 10-second UDP timeout, 30-second HA timeout
- Status text sensor showing active tier
- Configurable via vars: zone_slug, udp_sensor_id, ha_sensor_id

**2. ESP32 Room Sensor Template**
- ESPHome YAML template for external room sensors
- Temperature sensor configuration (Dallas/SHT3x)
- Humidity sensor configuration (SHT3x/DHT22)
- UDP broadcaster setup (packet_transport)
- Example: `templates/esp32-room-sensor.yaml`

**3. Distribution Board UDP Receiver**
- packet_transport provider configuration per room sensor
- UDP receiver sensors for temperature + humidity
- Integration with room_sensors.yaml v6
- Device file updates for 6 ground floor rooms

**4. Room Component Integration**
- Update room_sensors.yaml v6 to support UDP mode
- Add use_udp flag (default: false for backward compatibility)
- When use_udp=true: delegate to sensor_failover_3tier.yaml
- When use_udp=false: preserve Epic 5 HA-only behavior

**5. Diagnostic Sensors (Home Assistant Exposed)**
- `text_sensor.{zone}_sensor_tier` - Active failover tier (UDP/HA/Emergency)
- `sensor.{zone}_room_temp_udp` - Direct UDP sensor reading
- `binary_sensor.{zone}_udp_sensor_online` - UDP sensor availability
- `sensor.{zone}_sensor_last_update` - Timestamp of last sensor update

**6. Migration and Testing**
- Pilot room deployment (single room validation)
- Batch migration script for remaining rooms
- HA restart test (verify zero blackout)
- UDP failure test (verify HA fallback)
- Documentation and deployment guide

### Out of Scope for MVP

- ❌ **Humidity UDP broadcasting** (defer to Epic 12 dew point protection)
- ❌ **Bidirectional communication** (room sensors → distribution only, no commands back)
- ❌ **Battery-powered sensors** (USB powered only for MVP)
- ❌ **OTA updates via distribution boards** (ESP32 sensors update via HA/web)
- ❌ **Automatic sensor discovery** (manual configuration in device YAML)

### MVP Success Criteria

**Epic 11 is successful when:**
1. ✅ 6 ESP32 room sensors deployed and broadcasting via UDP
2. ✅ Distribution boards receive UDP sensors with <1 second latency
3. ✅ HA restart causes zero sensor blackout (PIDs continue on UDP)
4. ✅ UDP sensor failure triggers HA fallback within 30 seconds
5. ✅ All firmware compiles with flash <80% and RAM <15%
6. ✅ Backward compatibility: Epic 5 rooms without UDP continue working

---

## Post-MVP Vision

### Phase 2 Features (After Epic 11 MVP Proven)

**Humidity UDP Broadcasting:**
- Extend UDP broadcasts to include humidity data
- Enable Epic 12 dew point protection via UDP humidity
- Remove HA dependency for humidity sensing

**Enhanced Diagnostics:**
- UDP packet loss monitoring (% packets received)
- Sensor battery monitoring (if battery-powered sensors added)
- Historical sensor uptime tracking

**Simplified Deployment:**
- Web-based room sensor configuration tool
- Auto-discovery of UDP room sensors on network
- Bulk sensor firmware update via HA automation

### Long-Term Vision (Epic 13+)

**Battery-Powered Sensors:**
- Deep sleep mode (wake every 60 seconds, broadcast, sleep)
- Battery level monitoring and alerts
- Low-power sensors for closets, storage areas

**Advanced Sensor Mesh:**
- ESP32 sensors relay broadcasts for extended range
- Redundant sensor paths (multiple UDP routes)
- Automatic sensor health monitoring

**Integration with Epic 12 (Dew Point):**
- Room sensors broadcast both temperature and humidity
- Distribution boards calculate dew point per zone
- Mixing groups enforce supply temp limits autonomously

---

## Technical Considerations

### Platform Requirements

**ESP32 Room Sensors:**
- ESP32-WROOM-32 or ESP32-C3 (WiFi required)
- Temperature sensor: Dallas DS18B20 or SHT3x
- Humidity sensor: SHT3x or DHT22
- Power: USB 5V (1A sufficient)
- Enclosure: 3D printed or off-the-shelf project box

**Distribution Boards:**
- KC868-A16 (existing, no hardware changes)
- WiFi connectivity (already configured)
- ESPHome 2024.x+ with packet_transport support

### Architecture Considerations

**Component Structure:**
```
components/
  sensor_failover_3tier.yaml       # 3-tier failover logic (UDP → HA → NaN)
  room_sensors.yaml                # v6 with UDP mode support
templates/
  esp32-room-sensor.yaml           # ESP32 sensor device template
devices/
  distribuzione-piano-terra.yaml   # Updated with UDP receivers
  distribuzione-primo-piano.yaml   # Updated with UDP receivers
```

**Device Integration Pattern:**

Distribution board includes UDP provider per room:
```yaml
packet_transport:
  providers:
    - name: soggiorno_room_sensor
    - name: cucina_room_sensor
    # ... one per room
```

Room component uses UDP mode:
```yaml
sensors: !include
  file: ../../room_sensors.yaml
  vars:
    zone_slug: "soggiorno"
    zone_name: "Soggiorno"
    use_udp: true
    udp_sensor_id: "soggiorno_udp_temp"
    ha_temperature_sensor_id: "sensor.room_soggiorno_temperature"
```

**UDP Broadcast Pattern (ESP32 Sensor):**
```yaml
udp:
  id: udp_packet_transport

packet_transport:
  - platform: udp
    udp_id: udp_packet_transport
    update_interval: 10s
    sensors:
      - id: temperature_sensor
        broadcast_id: "soggiorno_room_temp"
      - id: humidity_sensor
        broadcast_id: "soggiorno_room_humidity"
```

### Network Considerations

**UDP Requirements:**
- Same subnet (ESPHome packet_transport limitation)
- Port 6053 (ESPHome default)
- Multicast or broadcast addressing
- <1% packet loss expected (local network)

**Bandwidth:**
- 14 room sensors × 2 readings (temp + humidity) × 10s interval
- ~28 UDP packets per 10 seconds
- <1 KB/s total bandwidth (negligible)

---

## Constraints & Assumptions

### Constraints

**Budget:** ~$210 (14 ESP32 sensors × $15 each = $210)

**Timeline:** 
- Epic 11 development: 2-3 weeks (8-10 story points)
- Hardware procurement: 1 week
- Deployment: 2 weeks (pilot + batch migration)

**Resources:**
- Dev agent: Component creation, device updates
- Alberto: Hardware assembly, sensor placement, deployment

**Technical:**
- WiFi coverage must reach all room sensor locations
- Same subnet requirement (ESPHome limitation)
- USB power outlets needed per room (or power adapters)

### Key Assumptions

1. **WiFi Coverage:**
   - All rooms have adequate WiFi signal for ESP32
   - No additional WiFi access points needed
   - 2.4GHz WiFi network available (ESP32 requirement)

2. **Network Stability:**
   - Local network packet loss <1%
   - Router handles UDP multicast/broadcast
   - No firewall blocking port 6053

3. **Sensor Accuracy:**
   - Dallas DS18B20: ±0.5°C (acceptable for HVAC)
   - SHT3x: ±0.2°C temperature, ±2% RH humidity
   - 10-second update rate sufficient for PID control

4. **Power Availability:**
   - USB power outlets available in each room
   - Or USB power adapters with long cables (5-10m)
   - Continuous power (no battery required for MVP)

5. **Deployment Model:**
   - ESP32 sensors configured via ESPHome (HA or web)
   - Distribution boards updated via OTA from Git
   - Room-by-room migration (not all-at-once)

---

## Risks & Open Questions

### Key Risks

**1. WiFi Coverage Gaps:**
- **Risk:** Some rooms may have weak WiFi signal for ESP32
- **Impact:** UDP broadcasts unreliable, frequent HA fallback
- **Mitigation:** WiFi survey before hardware purchase, WiFi extenders if needed

**2. UDP Packet Loss:**
- **Risk:** Local network congestion causes packet loss >1%
- **Impact:** Sensor updates delayed or missed, HA fallback triggered
- **Mitigation:** 10-second timeout on UDP tier, HA fallback is seamless

**3. ESP32 Hardware Reliability:**
- **Risk:** ESP32 boards may crash or reboot unexpectedly
- **Impact:** Sensor unavailable until reboot (30-60 seconds)
- **Mitigation:** Watchdog timers, HA fallback during reboots

**4. Configuration Complexity:**
- **Risk:** 14 ESP32 sensors × unique configuration = high maintenance
- **Impact:** Time-consuming updates, configuration drift
- **Mitigation:** Shared template file, scripted bulk updates

### Open Questions

1. **Should we use Dallas DS18B20 or SHT3x for temperature?**
   - Dallas: Cheaper, 1-Wire (easy wiring), ±0.5°C accuracy
   - SHT3x: More expensive, I2C, ±0.2°C accuracy, includes humidity
   - **Recommendation:** SHT3x for combo sensor (temp + humidity for Epic 12)

2. **Should ESP32 sensors broadcast humidity now or defer?**
   - Now: Enables Epic 12 immediately, more complete solution
   - Defer: Simpler MVP, proven Epic 9 float sensor pattern
   - **Recommendation:** Broadcast now (minimal overhead, enables Epic 12)

3. **Should we auto-discover UDP room sensors?**
   - Auto: ESP32 broadcasts discovery packet, distribution board auto-configures
   - Manual: Explicit provider configuration in device YAML
   - **Recommendation:** Manual for MVP (simpler, proven pattern)

4. **What fallback timeout for UDP tier?**
   - Conservative: 30 seconds (matches HA API typical response)
   - Moderate: 10 seconds (3 missed broadcasts = failover)
   - Aggressive: 5 seconds (responsive but more false failovers)
   - **Recommendation:** 10 seconds (balance responsiveness vs stability)

### Areas Needing Further Research

- ✅ ESP32 board selection (ESP32-WROOM vs ESP32-C3 vs others)
- ✅ Sensor selection (Dallas vs SHT3x cost/accuracy trade-off)
- ⏳ WiFi survey results (signal strength in all room locations)
- ⏳ 3D printable enclosure design (or off-the-shelf box selection)
- ⏳ USB power cable routing (wall-mounted vs desk placement)

---

## Story Breakdown (Preliminary)

### Story 11.1: sensor_failover_3tier Component
**Effort:** 2 story points (~1 day)

**Tasks:**
- Create `components/sensor_failover_3tier.yaml`
- Implement 3-tier failover logic (UDP → HA → NaN)
- Template sensor with lambda checking tier availability
- Status text sensor showing active tier
- Configurable timeouts via vars
- Compilation validation

### Story 11.2: ESP32 Room Sensor Template
**Effort:** 2 story points (~1 day)

**Tasks:**
- Create `templates/esp32-room-sensor.yaml`
- Temperature sensor configuration (SHT3x recommended)
- Humidity sensor configuration
- UDP broadcaster setup (packet_transport)
- Device-specific vars: zone_slug, sensor type, calibration offsets
- Example documentation

### Story 11.3: Distribution Board UDP Receiver
**Effort:** 3 story points (~2 days)

**Tasks:**
- Add packet_transport providers to distribution boards (6 rooms ground, 8 rooms first)
- UDP receiver sensors for temperature + humidity
- Update room_sensors.yaml v6 with use_udp flag
- Integration with sensor_failover_3tier
- Compilation validation (flash <80%)

### Story 11.4: Hardware Procurement and Assembly
**Effort:** 1 story point (~1 day elapsed, non-dev work)

**Tasks:**
- Order 14× ESP32 boards
- Order 14× SHT3x sensors (or Dallas + DHT22)
- Order USB cables and power adapters
- WiFi survey for sensor placement
- Assemble pilot room sensor (test build)

### Story 11.5: Pilot Room Deployment
**Effort:** 2 story points (~1 day)

**Tasks:**
- Deploy pilot ESP32 sensor (Soggiorno recommended)
- Configure distribution board UDP receiver
- Enable use_udp flag for pilot room
- Validation tests: UDP latency, HA restart, UDP failure
- Document issues and refinements

### Story 11.6: Batch Migration and Testing
**Effort:** 2 story points (~1 day)

**Tasks:**
- Deploy remaining 5 ground floor sensors
- Update distribution board configs
- Enable use_udp for all ground floor rooms
- HA restart test (verify zero blackout)
- Network validation (packet loss <1%)
- 48-hour stability monitoring

### Story 11.7: Documentation and Completion
**Effort:** 1 story point (~0.5 day)

**Tasks:**
- Epic 11 completion report
- ESP32 room sensor deployment guide
- UDP failover troubleshooting guide
- Update `.github/copilot-instructions.md` with Epic 11 patterns
- Update architecture.md with UDP room sensors

**Total Effort:** 13 story points (~2-3 weeks)

---

## Dependencies

### Required Before Starting Epic 11

- ✅ **Epic 5:** HA-only sensors (baseline architecture, HA fallback)
- ✅ **Epic 8:** Condition interface pattern (emergency detection reference)
- ✅ **Epic 9:** UDP infrastructure (packet_transport platform, float sensor broadcasts)
- ✅ **Epic 10:** UDP zone activity tracking (provider/receiver pattern reference)

### Enables Future Epics

- **Epic 12:** Dew point protection (humidity UDP broadcasts enable autonomous calculation)
- **Epic 13:** Advanced room sensing (humidity trends, occupancy integration)
- **Epic 14:** Weather-based optimization (room sensor data + weather forecast)

### Optional (Enhances but Not Required)

- Story 1.6 Modbus hardware deployment (alternative to UDP sensors, not competing)
- WiFi mesh network (improves sensor coverage, not required if single AP sufficient)

---

## Appendices

### A. ESP32 Hardware Selection

**Recommended Board: ESP32-WROOM-32 DevKit V1**
- Cost: ~$8-12 per board
- WiFi: 2.4GHz 802.11b/g/n
- GPIO: 30+ pins (plenty for sensors)
- Power: USB 5V (500mA typical)
- ESPHome: Fully supported

**Alternative: ESP32-C3 SuperMini**
- Cost: ~$4-6 per board (cheaper!)
- WiFi: 2.4GHz 802.11b/g/n
- GPIO: 13 pins (sufficient for temp + humidity)
- Power: USB-C 5V (300mA typical)
- ESPHome: Supported (2023.11+)

**Sensor Options:**

| Sensor      | Type        | Accuracy       | Cost  | Interface | Recommendation |
|-------------|-------------|----------------|-------|-----------|----------------|
| DS18B20     | Temp only   | ±0.5°C         | $2-3  | 1-Wire    | OK (no humidity) |
| DHT22       | Temp + RH   | ±0.5°C, ±2% RH | $4-5  | 1-Wire    | Good |
| SHT3x       | Temp + RH   | ±0.2°C, ±2% RH | $6-8  | I2C       | **Best** (accurate) |

**Recommendation:** ESP32-C3 + SHT31 = $10-14 per room sensor (best value + accuracy)

### B. Network Configuration

**UDP Multicast Addressing:**
- ESPHome packet_transport uses broadcast by default
- Destination: 255.255.255.255 (subnet broadcast)
- Port: 6053 (ESPHome default)
- Protocol: UDP (connectionless)

**Router Configuration:**
- Enable UDP broadcast forwarding (usually default)
- No firewall rules needed (local subnet)
- QoS: Not required (<1 KB/s per sensor)

**Troubleshooting Packet Loss:**
```bash
# Capture UDP packets on distribution board
tcpdump -i wlan0 udp port 6053 -n -vv

# Monitor packet rate (should see ~2 packets/10s per sensor)
tcpdump -i wlan0 udp port 6053 | pv -l -i 10
```

### C. Related Documentation

**Epic 5 HA-Only Sensors:**
- `docs/epic-5-completion-report.md` - Baseline architecture
- `components/room_sensors.yaml` - v5/v8 HA-only implementation

**Epic 9 UDP Infrastructure:**
- `docs/epic-9-brief.md` - UDP float sensor broadcasts (supply temperatures)

**Epic 10 Zone Activity Tracking:**
- `docs/epic-10-completion-report.md` - UDP binary sensor broadcasts, provider pattern

**Story 1.6 Room Sensors:**
- `docs/stories/1.6.room-sensor-integration.md` - Modbus alternative (hardware pending)

### D. Deployment Checklist

**Pre-Deployment:**
- [ ] WiFi survey (signal strength >-70 dBm all locations)
- [ ] Order ESP32 boards (14× ESP32-C3 recommended)
- [ ] Order sensors (14× SHT31)
- [ ] Order USB cables and power adapters
- [ ] 3D print enclosures (optional)

**Pilot Room (Soggiorno):**
- [ ] Assemble ESP32 sensor (SHT31 wired)
- [ ] Flash ESP32 with template YAML
- [ ] Verify UDP broadcasts (tcpdump on distribution board)
- [ ] Update distribution board config (UDP receiver)
- [ ] Enable use_udp=true for Soggiorno
- [ ] Validation: HA restart test, UDP latency test

**Batch Deployment:**
- [ ] Assemble remaining 13 sensors
- [ ] Flash all sensors with unique zone configs
- [ ] Update distribution boards (ground + first floor)
- [ ] Enable use_udp=true for all rooms
- [ ] 48-hour stability test
- [ ] Document issues and solutions

---

**Epic 11 Status:** Draft - Ready for Story Breakdown

**Next Steps:**
1. Review and approve Epic 11 brief
2. WiFi survey to validate coverage
3. Hardware procurement (2-week lead time)
4. Create Story 11.1 (sensor_failover_3tier Component)
5. Begin implementation (target: 2-3 week timeline)

---

**Document Version:** 1.0  
**Author:** Mary (Business Analyst)  
**Date:** November 24, 2025
