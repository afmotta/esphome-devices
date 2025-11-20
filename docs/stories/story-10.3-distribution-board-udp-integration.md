# Story 10.3: Distribution Board UDP Integration - Brownfield Addition

**Epic:** 10 - ESP32 Room Sensors & Zone Activity Tracking via UDP  
**Date:** November 20, 2025  
**Status:** Ready  
**Story Points:** 3  
**Version:** 1.0

---

## User Story

As a **distribution board operator**,  
I want **to broadcast zone activity demand signals via UDP and optionally receive room temperatures from ESP32 sensors**,  
So that **mixing groups can respond to actual demand and PIDs can operate independently from Home Assistant**.

---

## Story Context

**Existing System Integration:**

- **Integrates with:** Distribution board device files (`devices/distribuzione-piano-terra.yaml`, `devices/distribuzione-primo-piano.yaml`), Epic 9 packet_transport infrastructure, Story 10.2 zone_activity_aggregator component, mixing group receivers
- **Technology:** ESPHome packet_transport platform (UDP), binary_sensor broadcasting, optional sensor receiving for room temps
- **Follows pattern:** Epic 9 gruppo-miscelazione UDP broadcasting (Story 9.1), Epic 9 packet_transport sensor platform
- **Touch points:**
  - Distribution board device files - Will add UDP configuration (sender + optional receiver)
  - Zone activity aggregator (Story 10.2) - Binary sensor to be broadcast
  - Mixing group (Story 10.4) - Will receive broadcasted demand signals
  - Room components (Story 10.1) - Can optionally use UDP room sensors when available

**Current State:**

- Distribution boards have no UDP configuration (Epic 9 was mixing group only)
- Zone activity aggregator binary sensor exists (Story 10.2) but not broadcast
- No UDP receiver configured for ESP32 room sensor broadcasts
- Mixing groups have no visibility into zone demand

**Desired State:**

- Distribution boards broadcast `binary_sensor.{board_slug}_any_zone_open` via UDP every 5 seconds
- Optional: Distribution boards receive room temperature broadcasts from ESP32 sensors (for Epic 10.1 UDP tier)
- UDP configuration inline in device files (no separate component, following Epic 9 pattern)
- Mixing groups can subscribe to demand signals for relay control (Story 10.4)
- Backward compatible with Epic 5 (HA-only room sensors still work)

---

## Acceptance Criteria

### Functional Requirements

1. **UDP Binary Sensor Broadcasting:**
   - Add `udp:` and `packet_transport:` sections to both distribution board device files
   - Configure packet_transport to broadcast binary_sensor state (any_zone_open)
   - Broadcast ID: `{board_slug}_any_zone_open` (e.g., "piano_terra_any_zone_open")
   - Update interval: 5s (responsive relay control)
   - Port: 6053 (Epic 9 standard)

2. **Optional UDP Room Sensor Receiver:**
   - Add receiver configuration for ESP32 room sensor broadcasts (optional, for future Story 10.1 integration)
   - Receiver listens for `broadcast_id: "room_{zone_slug}_temperature"` pattern
   - Creates internal sensors: `{zone_slug}_temperature_udp` for each room
   - Not mandatory for Story 10.3 (can defer to Story 10.1 if preferred)

3. **Device File Integration:**
   - Piano terra device file: broadcasts piano_terra_any_zone_open
   - Primo piano device file: broadcasts primo_piano_any_zone_open
   - Configuration follows Epic 9 inline pattern (not separate component)
   - UDP config can be disabled via commenting out sections (feature flag pattern)

### Integration Requirements

4. **Binary Sensor Preparation:**
   - Story 10.2 zone_activity_aggregator must be included and functional
   - Binary sensor IDs match packet_transport broadcast_id references
   - Binary sensor must be `internal: false` (exposed for UDP broadcasting)

5. **Network Configuration:**
   - UDP port 6053 (consistent with Epic 9)
   - Broadcast/multicast to local subnet (all boards on same network)
   - No firewall rules needed (local network trust model)

6. **Compilation Validation:**
   - Both distribution board device files compile successfully
   - Firmware size within ESP32 flash limits (currently ~60%, Epic 10 adds ~5%)
   - No conflicts with existing packages or components

### Quality Requirements

7. **No Impact on Existing Functionality:**
   - Room components continue using HA sensors (Story 10.1 adds UDP tier)
   - PID controllers operate normally
   - Existing pump management scripts unaffected
   - HA integration remains functional

8. **Diagnostic Logging:**
   - Log UDP broadcasting start/stop at INFO level
   - Log binary sensor value on state change
   - Example: "Broadcasting piano_terra_any_zone_open: TRUE (3 zones active)"

9. **Documentation:**
   - Inline comments explain UDP configuration purpose (Epic 10 context)
   - Document broadcast_id naming conventions
   - Note dependencies on Story 10.2 (zone_activity_aggregator)

---

## Technical Notes

### Integration Approach

**UDP Broadcasting Configuration Pattern (Epic 9 style):**

```yaml
# In devices/distribuzione-piano-terra.yaml

# Epic 10: UDP broadcasting for zone demand signaling to mixing groups
udp:
  id: udp_packet_transport

packet_transport:
  - platform: udp
    udp_id: udp_packet_transport
    update_interval: 5s  # Fast response for relay control
    binary_sensors:
      - id: piano_terra_any_zone_open  # From Story 10.2
        broadcast_id: piano_terra_any_zone_open
```

**Optional UDP Receiver for ESP32 Room Sensors:**

```yaml
# Optional (for Story 10.1 integration)
# Receive room temperature broadcasts from external ESP32 sensors

packet_transport:
  - platform: udp
    udp_id: udp_packet_transport
    sensors:
      - broadcast_id: room_soggiorno_temperature
        id: soggiorno_temperature_udp
      - broadcast_id: room_cucina_temperature
        id: cucina_temperature_udp
      # ... repeat for all zones
```

**Challenge:** ESPHome packet_transport supports both sensors and binary_sensors in same configuration, but must verify both can coexist (sender + receiver on same port).

**Solution:** Epic 9 established pattern of sender-only on mixing group. Distribution boards will be sender+receiver hybrid, which should work as long as UDP IDs are shared.

### Existing Pattern Reference

- **Epic 9 Story 9.1:** gruppo-miscelazione broadcasts supply temperatures via packet_transport
- **Epic 9 configuration:** Inline UDP config in device file (no separate component)
- **Port 6053:** Established in Epic 9 as standard UDP port
- **Update intervals:** 10s for slow sensors (supply temps), 5s for fast control (demand signals)

### Key Constraints

- **Single UDP Port:** All boards use port 6053 (broadcast/multicast pattern)
- **Firmware Size:** Distribution boards are KC868-A16 (larger than mixing group's A6), so more headroom
- **Network Topology:** All boards must be on same subnet for UDP broadcast visibility
- **Binary Sensor Support:** ESPHome packet_transport must support broadcasting binary_sensor (not just sensor)

### Implementation Notes

**Two-Phase Approach (Recommended):**

1. **Phase A (This Story):** Add UDP broadcasting of zone activity binary sensor only
   - Simpler to test
   - Unblocks Story 10.4 (mixing group relay control)
   - Validates packet_transport binary_sensor support

2. **Phase B (Story 10.1 or deferred):** Add UDP receiver for ESP32 room sensors
   - More complex (multiple sensors per board)
   - Requires ESP32 room sensors to exist and broadcast
   - Can be added later without breaking existing functionality

**Recommendation for Story 10.3:** Focus on Phase A (broadcasting only). Defer receiver configuration to Story 10.1 when room_sensors.yaml v6 is updated to consume UDP tier.

### Existing Device File Structure

**Piano Terra (6 zones):**
- Includes: a16.yaml (board), wifi.yaml, 6 room packages (soggiorno, cucina, bagno, anticamera, sala_pranzo, locale_tecnico)
- Has pump management scripts (ground_floor_radiant_pump_management, ground_floor_fancoils_pump_management)
- Story 10.2 adds zone_activity_aggregator package

**Primo Piano (8 zones):**
- Includes: a16.yaml, wifi.yaml, 8 room packages (various cameras and bagnos)
- Similar pump management scripts
- Story 10.2 adds zone_activity_aggregator package

**UDP Configuration Location:** Add UDP sections after packages and before scripts (follows Epic 9 mixing group pattern)

### Network Validation

**Testing UDP Broadcasting:**

```bash
# On any machine on same subnet
sudo tcpdump -i eth0 -n udp port 6053 -A

# Expected output:
# Binary sensor broadcasts every 5s:
# {"piano_terra_any_zone_open": true}
# {"primo_piano_any_zone_open": false}
```

**Wireshark Filter:**
```
udp.port == 6053
```

---

## Definition of Done

- [x] **Functional requirements met:**
  - [ ] UDP configuration added to distribuzione-piano-terra.yaml
  - [ ] UDP configuration added to distribuzione-primo-piano.yaml
  - [ ] Binary sensor broadcasts configured (5s interval, port 6053)
  - [ ] Broadcast IDs follow naming convention (board_slug_any_zone_open)

- [x] **Integration requirements verified:**
  - [ ] Zone_activity_aggregator component included (Story 10.2 dependency)
  - [ ] Binary sensor IDs match broadcast_id references
  - [ ] Broadcast_id values align with mixing group receivers (Story 10.4)

- [x] **Existing functionality regression tested:**
  - [ ] Both distribution boards compile successfully
  - [ ] Firmware size within limits (check build output)
  - [ ] Room components operate normally with HA sensors
  - [ ] PID controllers and pump scripts unaffected

- [x] **Code follows existing patterns:**
  - [ ] Inline UDP config (Epic 9 pattern, not separate component)
  - [ ] Port 6053 and update_interval conventions followed
  - [ ] Broadcast_id naming matches Epic 10 conventions

- [x] **Network validation:**
  - [ ] UDP packets visible via tcpdump/Wireshark
  - [ ] Binary sensor values broadcast correctly (TRUE/FALSE)
  - [ ] Update interval is ~5 seconds (measured via packet capture)

- [x] **Documentation updated:**
  - [ ] Inline comments explain Epic 10 context
  - [ ] Broadcast_id naming conventions documented
  - [ ] Dependencies on Story 10.2 noted

---

## Risk and Compatibility Check

### Minimal Risk Assessment

**Primary Risk:** ESPHome packet_transport doesn't support binary_sensor broadcasting (only sensor)

- **Impact:** HIGH - Cannot broadcast zone demand signals, blocks Story 10.4
- **Likelihood:** MEDIUM - Documentation mentions sensors, unclear if binary_sensors supported
- **Mitigation:**
  - Research ESPHome packet_transport API documentation
  - Test with simple binary_sensor example before full integration
  - Fallback: Convert binary_sensor to numeric sensor (0/1) if needed
  - Alternative: Broadcast text_sensor with "true"/"false" strings

**Secondary Risk:** UDP sender + receiver conflict on same board/port

- **Impact:** MEDIUM - Receiver interferes with sender, packets lost
- **Likelihood:** LOW - UDP broadcast pattern should allow hybrid sender/receiver
- **Mitigation:**
  - Start with sender-only (Phase A) to validate independently
  - Add receiver in separate story (10.1) after sender proven
  - Monitor network traffic to detect conflicts

**Tertiary Risk:** Firmware size overflow on distribution boards

- **Impact:** HIGH - Cannot compile, blocks deployment
- **Likelihood:** LOW - KC868-A16 boards have more flash than A6 mixing group
- **Mitigation:**
  - Compile early in story to detect size issues
  - Optimize logging verbosity if needed
  - Remove unused platforms if necessary

**Quaternary Risk:** 5-second update interval too aggressive for ESP32 UDP

- **Impact:** LOW - Slight delay acceptable (30s response target)
- **Likelihood:** LOW - ESP32 handles UDP easily, 5s is conservative
- **Mitigation:**
  - Configurable update_interval (can increase to 10s if issues)
  - Monitor ESP32 CPU/memory during testing

### Compatibility Verification

- [x] **No breaking changes to existing APIs:**
  - UDP configuration is additive, doesn't modify room components
  - Distribution boards opt-in by adding UDP sections
  - Can be disabled by commenting out UDP config

- [x] **Database changes:** N/A (ESPHome firmware only)

- [x] **UI changes:** Zone demand binary sensors already exposed in HA (Story 10.2), no new UI

- [x] **Performance impact:** 
  - UDP broadcasting adds ~100 bytes/5s per board (negligible network bandwidth)
  - Binary sensor polling already exists (Story 10.2), no additional CPU load
  - Firmware size increase estimated ~1-2KB (within headroom)

---

## Validation Checklist

### Scope Validation

- [x] **Story can be completed in one development session:** Mostly yes (estimated 2-3 hours: UDP config 60min, compile/test 60min, network validation 30min, documentation 30min)
- [x] **Integration approach is straightforward:** Yes (Epic 9 established pattern, Story 10.2 provides binary sensor)
- [x] **Follows existing patterns exactly:** Yes (Epic 9 inline UDP config pattern)
- [x] **No design or architecture work required:** Yes (architecture defined in Epic 10 brief, Epic 9 pattern established)

### Clarity Check

- [x] **Story requirements are unambiguous:** Mostly clear (binary_sensor broadcasting support needs validation)
- [x] **Integration points are clearly specified:** Yes (Story 10.2 aggregator, Story 10.4 mixing group receivers)
- [x] **Success criteria are testable:** Yes (compilation + network capture validation)
- [x] **Rollback approach is simple:** Yes (comment out UDP sections)

---

## Notes and Open Questions

### Implementation Decision Required

**Question:** Should Story 10.3 include UDP receiver for ESP32 room sensors, or defer to Story 10.1?

**Options:**

1. **Include Receiver (Full Integration):**
   - Distribution boards ready to receive room temps immediately
   - **Pros:** Complete Epic 10 communication architecture in one story
   - **Cons:** More complex testing, depends on ESP32 sensors existing, increases story scope

2. **Defer Receiver to Story 10.1 (Recommended):**
   - Focus Story 10.3 on broadcasting only (simpler, unblocks Story 10.4)
   - Story 10.1 adds receiver when updating room_sensors.yaml to v6
   - **Pros:** Smaller story scope, validates broadcasting first, incremental complexity
   - **Cons:** Two-touch approach (add receiver later)

**Recommendation:** **Option 2 (Defer Receiver).** Story 10.3 should focus on broadcasting zone demand to unblock mixing group relay control (Story 10.4). Room sensor UDP receiving can be added in Story 10.1 when room_sensors.yaml v6 is implemented, as that's the natural integration point.

### Binary Sensor Broadcasting Research

**Question:** Does ESPHome packet_transport support broadcasting binary_sensor states?

**Research Required:**
- Review ESPHome packet_transport documentation
- Check if binary_sensors can be mapped to broadcast_ids
- Test with simple binary_sensor example before full integration

**Fallback Options if Not Supported:**
1. Convert binary_sensor to numeric sensor (0.0 = false, 1.0 = true)
2. Use text_sensor with "true"/"false" strings
3. Create lambda sensor that reads binary_sensor state and publishes number

**Impact on Story:** If binary_sensor not directly supported, requires minor refactoring of broadcast configuration but doesn't block core functionality.

### Testing Strategy

**Compilation Test:**
```bash
esphome compile devices/distribuzione-piano-terra.yaml
esphome compile devices/distribuzione-primo-piano.yaml

# Verify firmware size in build output
# Target: < 80% flash usage (currently ~60%, expect ~65% after Epic 10)
```

**Network Capture Test:**
```bash
# On development machine (same subnet as boards)
sudo tcpdump -i eth0 -n udp port 6053 -A

# Or with Wireshark: filter 'udp.port == 6053'
# Expected: Packets every 5 seconds with binary sensor state
```

**State Validation Test (Manual):**
1. Deploy firmware to one distribution board
2. Trigger PID heating/cooling via HA (turn ON setpoint)
3. Verify binary sensor transitions TRUE in HA dashboard
4. Verify UDP packet contains "true" in network capture
5. Stop all PIDs, verify binary sensor FALSE and UDP packet "false"

### Dependencies

- **Prerequisite:** Story 10.2 zone_activity_aggregator complete (binary sensor exists)
- **Prerequisite:** Distribution board device files compile (✅ existing)
- **Prerequisite:** Epic 9 UDP infrastructure validated (packet_transport works)
- **Blocks:** Story 10.4 (mixing group relay control) depends on these broadcasts
- **Optional Integration:** Story 10.1 (room_sensors v6) can add receiver config later

### Open Questions for Mixing Group Integration (Story 10.4)

- How does mixing group subscribe to binary sensor broadcasts? (Provider mechanism)
- Does mixing group need both piano_terra AND primo_piano broadcasts? (Yes, 2 relays)
- What happens if one distribution board is offline? (Mixing group relay stays in last-known state or fails-safe OFF?)

**Recommendation for Story 10.4:** Mixing groups should fail-safe to relay OFF if UDP packets stop (timeout mechanism) to prevent wasting energy when distribution boards offline.

---

## Success Criteria Summary

This story is **successful** when:

1. ✅ Distribution board device files have UDP broadcasting configuration
2. ✅ Zone activity binary sensors broadcast via UDP every 5 seconds
3. ✅ UDP packets visible in network capture with correct broadcast_id and state values
4. ✅ Both distribution boards compile and firmware fits within flash limits
5. ✅ Existing room components and PID controllers operate normally
6. ✅ No regression in pump management scripts or other existing functionality
7. ✅ Story 10.4 can proceed (mixing groups can receive broadcasts)

**Estimated Effort:** 2-3 hours focused development work

**Story Priority:** HIGH - Blocks Story 10.4 (mixing group relay control, core Epic 10 energy savings feature)

---

**Ready for Implementation** ✅

---

## Additional Notes

### Epic 9 vs Epic 10 UDP Patterns

**Epic 9 (Mixing Group Broadcasting):**
- Broadcasts sensor values (Dallas temperatures)
- Update interval: 10s (slow sensors)
- Receivers: Distribution boards (deferred to Epic 10)

**Epic 10 (Distribution Board Broadcasting):**
- Broadcasts binary_sensor values (zone demand)
- Update interval: 5s (fast control signals)
- Receivers: Mixing group (Story 10.4)

**Pattern Consistency:** Both epics use inline UDP config, port 6053, packet_transport platform. Epic 10 adds binary_sensor support (pending validation).

### Future Enhancements (Post-MVP)

- **Per-Zone Demand Broadcasting:** Individual zone status (not just "any zone")
- **UDP Receiver for Humidity:** If ESP32 sensors have DHT22/BME280
- **Diagnostic Counters:** udp_packets_sent, udp_last_broadcast_timestamp
- **Multicast Optimization:** Use multicast address instead of broadcast for efficiency
- **UDP Packet Compression:** Reduce payload size if bandwidth becomes concern

