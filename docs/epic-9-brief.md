# Project Brief: Epic 9 - REST API-Based Board Communication (Experimental)

**Project:** ESPHome Multi-Floor Climate Control System  
**Epic:** 9 - REST API Board Communication  
**Date:** November 5, 2025  
**Status:** Planning (Experimental)  
**Owner:** Alberto (System Owner)

---

## Executive Summary

**Epic 9: REST API-Based Board Communication** implements HTTP REST API as the primary communication layer between ESPHome boards, replacing both Modbus RTU and Home Assistant dependencies. By leveraging ESPHome's native `web_server` and `http_request` components, boards exchange sensor data, climate mode, and coordination signals directly over existing Ethernet/WiFi infrastructure without RS485 wiring.

**Goal:** Validate whether REST API communication can match or exceed Modbus reliability while offering superior debugging, flexibility, and implementation simplicity—and eliminate Home Assistant as a sensor data intermediary.

**Key advantages over Modbus + HA:**
- ✅ No RS485 wiring required (uses existing Ethernet/WiFi)
- ✅ Human-readable JSON (vs. binary registers)
- ✅ Web browser debugging (vs. serial logging)
- ✅ Flexible data structures (vs. fixed 16-bit registers)
- ✅ Standard HTTP tools (curl, Postman, browser)
- ✅ Direct ESPHome-to-ESPHome communication (no HA intermediary)
- ✅ Room sensors are ESPHome devices with web servers (accessible via REST)

**Trade-offs:**
- ⚠️ Higher latency (~2s vs. 500ms Modbus) - acceptable for HVAC
- ⚠️ Network-dependent (WiFi/Ethernet vs. dedicated RS485)
- ⚠️ More overhead (HTTP vs. Modbus binary protocol)

---

## Problem Statement

**Current State (Post-Epic 5):**
- Modbus RTU was removed for sensor communication in Epic 5
- Room sensors now sourced from Home Assistant
- Modbus retained only for 0-10V output adapters (fancoil control)
- Home Assistant is required intermediary for sensor data

**Limitations:**
- HA restart breaks sensor data flow
- HA becomes single point of failure for temperature control
- Sensor data latency through HA API layer
- Cannot operate autonomously during HA maintenance

**Question:** Can REST API provide direct ESPHome-to-ESPHome communication, eliminating HA dependency for sensor data while maintaining simplicity?

---

## Proposed Solution

### Architecture

**Master Board (gruppo-miscelazione):**
```yaml
web_server:
  port: 80
  version: 2  # JSON support

# Exposes endpoints:
# GET /sensor/supply_temp_piano_terra -> {"value": 42.5, "unit": "°C"}
# GET /text_sensor/climate_mode -> {"value": "heat"}
```

**Slave Boards (distribuzione-piano-*):**
```yaml
http_request:
  id: http_master
  timeout: 2s

sensor:
  # Supply temperature from master board
  - platform: http_request
    url: "http://gruppo-miscelazione.local/sensor/supply_temp"
    update_interval: 10s
    json_path: "$.value"
  
  # Room temperature from ESPHome sensor devices
  - platform: http_request
    url: "http://sensor-soggiorno.local/sensor/temperature"
    update_interval: 10s
    json_path: "$.value"
```

**Two-Tier Failover (REST → Emergency):**
```yaml
sensor:
  - platform: template
    name: "Supply Temp"
    lambda: |-
      if (id(use_rest_api) && id(http_temp).has_state()) {
        return id(http_temp).state;  // Tier 1: REST API (ESPHome-to-ESPHome)
      } else {
        return NAN;  // Tier 2: Emergency (local shutdown)
      }

  - platform: template
    name: "Room Temp Abstracted"
    lambda: |-
      if (id(http_room_temp).has_state()) {
        return id(http_room_temp).state;  // Direct REST from room sensor
      } else {
        return NAN;  // Emergency shutdown
      }
```

**Note on Home Assistant:** HA remains available for monitoring and manual overrides but is NOT required for autonomous operation. All sensor data flows directly between ESPHome devices via REST API.

**Note on Modbus:** Modbus RTU is retained exclusively for 0-10V output adapters (fancoil control). All sensor communication uses REST API.

### Comparison: Current (Epic 5) vs. REST API

| Aspect           | Epic 5 (HA Sensors)       | REST API (ESPHome-to-ESPHome) |
| ---------------- | ------------------------- | ----------------------------- |
| Infrastructure   | Ethernet/WiFi + HA        | Ethernet/WiFi only            |
| Data Format      | HA API                    | JSON                          |
| Debugging        | HA logs                   | Web browser                   |
| Latency          | ~1-5s (via HA)            | ~1-2s (direct)                |
| Extensibility    | HA entity changes         | Add JSON fields               |
| Complexity       | Medium (HA dependency)    | Low                           |
| HA Dependency    | Required (sensors)        | Optional (monitoring only)    |
| Sensor Placement | HA abstracts hardware     | Direct ESPHome REST endpoints |
| Autonomy         | HA restart breaks sensors | Full autonomous operation     |

---

## Goals & Success Metrics

### MVP Success Criteria

1. ✅ Master exposes REST API endpoints with JSON responses
2. ✅ Slave polls master endpoints successfully (10s interval)
3. ✅ **Room sensors are accessed via REST (ESPHome-to-ESPHome)**
4. ✅ Two-tier failover works (REST → Emergency, no HA intermediary)
5. ✅ 24+ hour autonomous operation **without Home Assistant**
6. ✅ <1% REST API error rate
7. ✅ ±0.5°C temperature accuracy maintained
8. ✅ Web browser inspection works (human-readable JSON)
9. ✅ Modbus 0-10V outputs continue to function (fancoil control)
10. ✅ 2-week reliability testing completes successfully

**Decision Point:** If MVP succeeds, expand to all boards. If reliability issues or excessive latency, revert to Epic 5 architecture (HA sensors).

---

## MVP Scope

### Core Features (Must Have)

- **Master REST Server:** Expose supply temps + climate mode as JSON endpoints
- **Slave REST Client:** Poll master via http_request every 10 seconds
- **Room Sensor REST Access:** Direct polling of ESPHome room sensor devices (no HA)
- **Two-Tier Failover:** REST → Emergency (HA removed from critical path)
- **Diagnostic Sensors:** REST API health, error counts, response times
- **Full Autonomy:** 24+ hour operation without Home Assistant
- **Preserve Modbus 0-10V:** Fancoil control via Modbus adapters unchanged

### Out of Scope

- ❌ Authentication/SSL (local network only)
- ❌ WebSocket push (polling only for MVP)
- ❌ Batch endpoints (one sensor per endpoint)
- ❌ Home Assistant as sensor intermediary (direct ESPHome-to-ESPHome only)
- ❌ Replacing Modbus 0-10V adapters (fancoil control stays on Modbus)

---

## Technical Approach

### Component Structure

**New Components:**
```
components/
├── rest_api_master.yaml     # web_server endpoints
├── rest_api_slave.yaml      # http_request polling
├── rest_api_failover.yaml   # 2-tier template sensors (REST → Emergency)
└── rest_api_room_sensor.yaml # Direct room sensor access via REST
```

### Implementation Strategy

**Phase 1: Master Server (Story 9.1)**
- Enable web_server component
- Expose supply temperature endpoints
- Expose climate mode endpoint
- Test with browser/curl

**Phase 2: Slave Client (Story 9.2)**
- Implement http_request polling
- Poll master supply temperature endpoints
- Poll ESPHome room sensor devices directly (no HA)
- Extract JSON values
- Create sensor entities
- Validate 10s polling works

**Phase 3: Failover Logic (Story 9.3)**
- Implement 2-tier template sensors (REST → Emergency)
- Remove Home Assistant from failover chain
- Add REST API diagnostics
- Test failover scenarios (network failure)
- Validate emergency shutdown when REST unavailable
- Measure transition times

**Phase 4: Reliability Testing (Story 9.4)**
- Deploy REST API to all boards
- Run 2-week reliability testing
- Test with Home Assistant offline (validate full autonomy)
- Monitor error rates (target: <1%)
- Monitor latency (REST ~2s acceptable)
- Document temperature control accuracy (±0.5°C maintained)
- Verify Modbus 0-10V outputs continue functioning (fancoil control)
- Make decision: Keep REST API or revert to Epic 5 (HA sensors)

---

## Dependencies

**Requires:**
- ✅ Epic 5 completed (HA-only sensors baseline)
- ✅ Stable Ethernet/WiFi on all boards
- ✅ mDNS working (.local hostnames)
- ✅ Room sensors are ESPHome devices with web_server enabled

**Enables:**
- ⏳ True Home Assistant independence (monitoring only)
- ⏳ Simplified architecture (eliminate HA sensor dependency)
- ⏳ Better observability (web browser debugging)

**Preserves:**
- ✅ Modbus 0-10V adapters for fancoil control (Epic 6)

---

## Risks & Mitigations

**Risk 1: Network Instability**
- Mitigation: Monitor error rates, use wired Ethernet
- Contingency: If >5% errors, abort and keep Modbus

**Risk 2: Excessive Latency**
- Mitigation: Measure P95 response times
- Contingency: If >5s consistently, abort

**Risk 3: Firmware Size**
- Mitigation: Monitor flash usage during compilation
- Contingency: Disable web_server UI if needed

**Risk 4: Rollback Complexity**
- Mitigation: Document Epic 5 rollback procedure
- Contingency: Restore HA sensor configuration if REST fails

---

## Next Steps

1. **Story Breakdown:** Create 4 stories (Master, Slave, Failover, Testing)
2. **Set Up locals/:** Prepare test configurations
3. **Document Epic 5 Baseline:** Current HA sensor architecture
4. **Implement Story 9.1:** Begin with master REST server
5. **Validate with Browser:** Test endpoints before slave integration

---

**Document Status:** Planning - Ready for Story Breakdown  
**Created:** November 5, 2025  
**Author:** Mary (Business Analyst)
