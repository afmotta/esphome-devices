# Epic 15: Air Quality Sensor Broadcasting

**Date:** January 14, 2026  
**Status:** Complete  
**Priority:** High (Prerequisite for Epic 16)  
**Estimated Story Points:** 5  
**Actual Story Points:** 5

---

## Executive Summary

Extend the existing UDP packet transport infrastructure to broadcast CO₂ and VOC/IAQ sensor data from room sensor ESP32 devices to the central climate-control board. This enables floor-wide air quality aggregation required for intelligent MEV (Mechanical Extract Ventilation) control in Epic 16.

---

## Problem Statement

### Current State
- Room sensor ESP32 devices (S1-Pro-Multi-Sense) have SCD40 CO₂ sensors and BME688 VOC/IAQ sensors
- These sensors are exposed to Home Assistant but **not broadcast via UDP** to the climate-control board
- The `packet_transport` infrastructure already broadcasts temperature and humidity successfully
- MEV control logic (Epic 16) requires CO₂ and VOC data on the climate-control board for real-time decisions

### Why This Matters
- **Epic 16 Blocker:** MEV intelligent control needs air quality inputs directly on ESPHome, not just HA
- **Latency:** HA round-trip adds delay; direct UDP provides sub-second response
- **Resilience:** UDP path works even if HA is temporarily unavailable
- **Consistency:** Follow established patterns from Epic 9/10 for sensor data transport

---

## Proposed Solution

### Core Changes

1. **Modify `s1-pro-multi-sense.yaml`** to broadcast additional sensors:
   - `scd_co2` → `${room_slug}_co2`
   - `iaq` (BME688 IAQ index) → `${room_slug}_iaq`

2. **Add receivers in `climate-control.yaml`**:
   - `packet_transport` sensors for each first floor room's CO₂ and IAQ

3. **Create aggregation sensors**:
   - `first_floor_max_co2` - Maximum CO₂ across all first floor rooms
   - `first_floor_max_iaq` - Maximum IAQ (worst air quality) across all first floor rooms

---

## User Stories

| Story | Title                                    | Points | Priority |
| ----- | ---------------------------------------- | ------ | -------- |
| 15.1  | Broadcast CO₂/IAQ from Room Sensors      | 2      | High     |
| 15.2  | Receive CO₂/IAQ on Climate Control Board | 2      | High     |
| 15.3  | First Floor Air Quality Aggregation      | 1      | High     |

---

## Technical Implementation

### Story 15.1: Broadcast CO₂/IAQ from Room Sensors

**File:** `boards/s1-pro-multi-sense.yaml`

**Current packet_transport section:**
```yaml
packet_transport:
  - platform: udp
    udp_id: udp_packet_transport
    update_interval: 10s
    sensors:
      - id: scd40_temp
        broadcast_id: "${room_slug}_room_temp"
      - id: scd40_rh
        broadcast_id: "${room_slug}_room_humidity"
```

**Modified to add CO₂ and IAQ:**
```yaml
packet_transport:
  - platform: udp
    udp_id: udp_packet_transport
    update_interval: 10s
    sensors:
      - id: scd40_temp
        broadcast_id: "${room_slug}_room_temp"
      - id: scd40_rh
        broadcast_id: "${room_slug}_room_humidity"
      - id: scd_co2
        broadcast_id: "${room_slug}_co2"
      - id: iaq
        broadcast_id: "${room_slug}_iaq"
```

### Story 15.2: Receive CO₂/IAQ on Climate Control Board

**File:** `components/rooms/first_floor/first-floor.yaml` (add to existing sensor section)

**Add packet_transport receivers for all 8 first floor rooms:**

```yaml
sensor:
  # ============================================================================
  # CO₂ Receivers (from room sensor ESP32s via UDP)
  # ============================================================================
  - platform: packet_transport
    id: bagno_grande_co2
    provider: room-sensor-bagno-grande
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: bagno_ospiti_co2
    provider: room-sensor-bagno-ospiti
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: bagno_padronale_co2
    provider: room-sensor-bagno-padronale
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_nord_co2
    provider: room-sensor-camera-nord
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_sud_co2
    provider: room-sensor-camera-sud
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_ospiti_co2
    provider: room-sensor-camera-ospiti
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_padronale_co2
    provider: room-sensor-camera-padronale
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: lavanderia_co2
    provider: room-sensor-lavanderia
    internal: true
    filters:
      - filter_out: nan

  # ============================================================================
  # IAQ Receivers (from room sensor ESP32s via UDP)
  # ============================================================================
  - platform: packet_transport
    id: bagno_grande_iaq
    provider: room-sensor-bagno-grande
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: bagno_ospiti_iaq
    provider: room-sensor-bagno-ospiti
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: bagno_padronale_iaq
    provider: room-sensor-bagno-padronale
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_nord_iaq
    provider: room-sensor-camera-nord
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_sud_iaq
    provider: room-sensor-camera-sud
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_ospiti_iaq
    provider: room-sensor-camera-ospiti
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: camera_padronale_iaq
    provider: room-sensor-camera-padronale
    internal: true
    filters:
      - filter_out: nan

  - platform: packet_transport
    id: lavanderia_iaq
    provider: room-sensor-lavanderia
    internal: true
    filters:
      - filter_out: nan
```

**Note:** The `filter_out: nan` ensures the combination sensor handles missing data gracefully.

### Story 15.3: First Floor Air Quality Aggregation

**File:** `components/rooms/first_floor/first-floor.yaml`

```yaml
sensor:
  # Maximum CO₂ across first floor
  - platform: combination
    id: first_floor_max_co2
    name: "First Floor Max CO₂"
    type: max
    unit_of_measurement: "ppm"
    icon: "mdi:molecule-co2"
    sources:
      - source: bagno_grande_co2
      - source: bagno_ospiti_co2
      - source: bagno_padronale_co2
      - source: camera_nord_co2
      - source: camera_sud_co2
      - source: camera_ospiti_co2
      - source: camera_padronale_co2
      - source: lavanderia_co2

  # Maximum IAQ (worst air quality) across first floor
  - platform: combination
    id: first_floor_max_iaq
    name: "First Floor Max IAQ"
    type: max
    unit_of_measurement: ""
    icon: "mdi:air-filter"
    sources:
      - source: bagno_grande_iaq
      - source: bagno_ospiti_iaq
      - source: bagno_padronale_iaq
      - source: camera_nord_iaq
      - source: camera_sud_iaq
      - source: camera_ospiti_iaq
      - source: camera_padronale_iaq
      - source: lavanderia_iaq
```

---

## Dependencies

| Dependency           | Status     | Notes                              |
| -------------------- | ---------- | ---------------------------------- |
| UDP packet_transport | ✅ Working  | Epic 9/10 established pattern      |
| SCD40 CO₂ sensor     | ✅ Working  | Already in s1-pro-multi-sense.yaml |
| BME688 IAQ sensor    | ✅ Working  | Already in s1-pro-multi-sense.yaml |
| Room sensor devices  | ✅ Deployed | 8 first floor sensors active       |

---

## Acceptance Criteria

### Functional
- [ ] All first floor room sensors broadcast CO₂ and IAQ via UDP
- [ ] Climate-control board receives CO₂/IAQ from all 8 first floor rooms
- [ ] `first_floor_max_co2` shows highest CO₂ across floor
- [ ] `first_floor_max_iaq` shows worst air quality across floor

### Technical
- [ ] `esphome compile` succeeds for all affected devices
- [ ] No UDP packet loss or latency issues
- [ ] Sensors update within 10 seconds of room sensor change

### Integration
- [ ] Aggregation sensors visible in Home Assistant
- [ ] Ready for Epic 16 MEV control logic consumption

---

## Risks & Mitigations

| Risk                   | Likelihood | Impact | Mitigation                                  |
| ---------------------- | ---------- | ------ | ------------------------------------------- |
| UDP bandwidth increase | Low        | Low    | Only 2 additional values per room           |
| Sensor unavailability  | Low        | Medium | `combination` sensor handles NaN gracefully |
| IAQ sensor calibration | Medium     | Low    | BME688 auto-calibrates; values relative     |

---

## Definition of Done

- [ ] Room sensors broadcasting CO₂ and IAQ
- [ ] Climate-control receiving all first floor air quality data
- [ ] Aggregation sensors working and exposed to HA
- [ ] Documentation updated
- [ ] Ready for Epic 16 consumption

---

## Notes

- IAQ from BME688 is an index (0-500+), not ppm—higher = worse air quality
- CO₂ from SCD40 is accurate to ±50 ppm
- This epic is a pure infrastructure prerequisite; no behavior changes
- Epic 16 will implement the actual MEV control logic using these sensors
