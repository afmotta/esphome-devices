# Epic 9: User Stories Index

**Epic:** 9 - REST API-Based Board Communication (Experimental)  
**Date:** November 5, 2025  
**Total Stories:** 4  
**Estimated Total Effort:** 15-21 hours (2-3 weeks calendar time including testing)

---

## Story Overview

### Foundation Stories (Critical Path)

**Story 9.1: Master REST API Server**  
- **File:** `epic-9-story-9.1-master-rest-server.md`
- **Effort:** 3-4 hours
- **Summary:** Enable web_server on gruppo-miscelazione to expose supply temps and climate mode via REST API
- **Deliverable:** `components/rest_api_master.yaml`
- **Status:** Draft

**Story 9.2: Slave REST Client**  
- **File:** `epic-9-story-9.2-slave-rest-client.md`
- **Effort:** 4-5 hours
- **Summary:** Implement http_request polling on distribuzione boards to consume master and room sensor REST endpoints
- **Deliverable:** `components/rest_api_slave.yaml`
- **Status:** Draft

**Story 9.3: Two-Tier Failover & Diagnostics**  
- **File:** `epic-9-story-9.3-failover-diagnostics.md`
- **Effort:** 3-4 hours
- **Summary:** Implement REST → Emergency failover with comprehensive REST API health diagnostics
- **Deliverable:** `components/rest_api_failover.yaml`
- **Status:** Draft

### Validation Story

**Story 9.4: Reliability Testing**  
- **File:** `epic-9-story-9.4-reliability-testing.md`
- **Effort:** 5-8 hours (2 weeks calendar time)
- **Summary:** 2-week soak test with HA offline validation, go/no-go decision on REST API vs. Epic 5 revert
- **Deliverable:** Completion report, updated documentation, production decision
- **Status:** Draft

---

## Story Dependencies

```
9.1 (Master REST Server) ──> 9.2 (Slave REST Client) ──> 9.3 (Failover) ──> 9.4 (Reliability Testing)
```

**Critical Path:** 9.1 → 9.2 → 9.3 → 9.4 (fully sequential)  
**No Parallel Work:** Each story builds on previous

---

## Acceptance Criteria Summary

### Story 9.1: Master REST Server
- [ ] web_server component enabled (port 80, version 2)
- [ ] Supply temperature endpoints exposed (piano terra, primo piano)
- [ ] Climate mode endpoint exposed
- [ ] JSON responses validated with browser/curl
- [ ] Firmware size within limits
- [ ] mDNS hostname resolution working

### Story 9.2: Slave REST Client
- [ ] http_request component configured
- [ ] Supply temp sensors poll master (10s interval)
- [ ] Room temp sensors poll ESPHome devices (10s interval)
- [ ] JSON path extraction working
- [ ] Sensor values match master logs (±0.1°C)
- [ ] Error handling for network failures
- [ ] Automatic recovery after outages

### Story 9.3: Failover & Diagnostics
- [ ] 2-tier template sensors (REST → Emergency, no HA)
- [ ] REST API health sensor (Healthy/Degraded/Failed)
- [ ] REST error count sensor
- [ ] Last success timestamp sensor
- [ ] Emergency triggers after 180s REST failure
- [ ] Recovery completes after 60s REST restoration
- [ ] HA dashboard with diagnostics

### Story 9.4: Reliability Testing
- [ ] All boards deployed with REST API
- [ ] 2-week soak test completed
- [ ] <1% REST API error rate achieved
- [ ] Latency P95 <5s achieved
- [ ] ±0.5°C temperature accuracy maintained
- [ ] 24+ hour HA offline test passed
- [ ] Failure scenarios tested (master, room sensor, network)
- [ ] Modbus 0-10V fancoils still functional
- [ ] Go/no-go decision made
- [ ] Completion report created

---

## Risk Summary

| Story | Primary Risk                                     | Mitigation                                     |
| ----- | ------------------------------------------------ | ---------------------------------------------- |
| 9.1   | Firmware size exceeds flash limits               | Disable web UI, reduce components              |
| 9.2   | mDNS hostname resolution fails                   | Use static IPs, document alternative           |
| 9.3   | Emergency doesn't trigger on REST failure        | Extensive testing, validate Epic 8 integration |
| 9.4   | High error rate or latency makes REST unfeasible | Clear rollback procedure to Epic 5             |

---

## Success Metrics

**Technical Goals:**
- <1% REST API error rate
- Average latency <2s, P95 <5s
- ±0.5°C temperature accuracy
- 24+ hour autonomous operation without Home Assistant

**Architecture Goals:**
- Eliminate HA as sensor data intermediary
- Simplify from Epic 5 (no HA dependency)
- Better observability (web browser debugging)
- Preserve Modbus 0-10V for fancoils

**Business Goals:**
- Improved system resilience
- Faster sensor updates (direct vs. via HA)
- Easier debugging (JSON, curl, browser)
- Foundation for future enhancements

---

## Timeline

**Week 1: Implementation**
- Day 1: Story 9.1 (Master REST server)
- Day 2: Story 9.2 (Slave REST client)
- Day 3: Story 9.3 (Failover & diagnostics)
- Day 4-5: Integration testing, bug fixes

**Week 2-3: Testing**
- Day 6: Deploy to all boards
- Day 7-20: 2-week reliability testing (Story 9.4)
- Day 21: Metrics analysis, go/no-go decision

**Week 4: Documentation**
- Day 22-23: Completion report
- Day 24: Documentation updates
- Day 25: Epic 9 completion or Epic 5 revert

---

## Comparison: Epic 5 vs. Epic 9

| Aspect        | Epic 5 (HA Sensors)       | Epic 9 (REST API)             |
| ------------- | ------------------------- | ----------------------------- |
| Sensor Source | Home Assistant            | ESPHome REST API              |
| Latency       | ~1-5s (via HA)            | ~1-2s (direct)                |
| HA Dependency | Required                  | Optional (monitoring only)    |
| Autonomy      | HA restart breaks sensors | Full autonomous operation     |
| Debugging     | HA logs                   | Web browser, curl, JSON       |
| Complexity    | Medium                    | Low                           |
| Observability | HA entities               | Web browser, REST diagnostics |

**Key Improvement:** Epic 9 eliminates HA as single point of failure for sensor data while maintaining simplicity.

---

## Epic 9 Architecture

### Communication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 Master Board (gruppo-miscelazione)               │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Dallas Sensors                                             │ │
│  │  • supply_temp_piano_terra                                 │ │
│  │  • supply_temp_primo_piano                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ REST API Master (Story 9.1)                                │ │
│  │  web_server: port 80, version 2                            │ │
│  │  Endpoints:                                                │ │
│  │   • GET /sensor/supply_temp_piano_terra → JSON            │ │
│  │   • GET /sensor/supply_temp_primo_piano → JSON            │ │
│  │   • GET /text_sensor/climate_mode → JSON                  │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────────┬──────────────────────────────────┘
                               │ REST API (HTTP/JSON)
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ Room Sensor 1   │   │ Room Sensor 2   │   │ Room Sensor N   │
│ (ESPHome)       │   │ (ESPHome)       │   │ (ESPHome)       │
│  web_server     │   │  web_server     │   │  web_server     │
│  /sensor/temp   │   │  /sensor/temp   │   │  /sensor/temp   │
└────────┬────────┘   └────────┬────────┘   └────────┬────────┘
         │                     │                     │
         │ REST API            │                     │
         └─────────────────────┼─────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│           Slave Board (distribuzione-piano-terra)                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ REST API Slave (Story 9.2)                                 │ │
│  │  http_request: polling every 10s                           │ │
│  │  Sensors:                                                  │ │
│  │   • supply_temp_piano_terra_rest ← master                 │ │
│  │   • soggiorno_room_temp_rest ← room sensor                │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ REST API Failover (Story 9.3)                              │ │
│  │  Template sensors: REST → Emergency (no HA)                │ │
│  │  Diagnostics: health, error count, last success            │ │
│  └────────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ PID Controllers                                            │ │
│  │  Input: {zone}_room_temp_abstracted (from failover)       │ │
│  │  Output: slow_pwm → relays                                │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Home Assistant                              │
│  Role: Monitoring & Manual Overrides ONLY                       │
│   • REST API diagnostics visibility                             │
│   • PID manual control (optional)                               │
│   • NOT required for autonomous operation                       │
└─────────────────────────────────────────────────────────────────┘
```

### Failover Logic (Story 9.3)

```
REST Sensor Available?
        │
        ├─ YES → Return REST value (Tier 1)
        │
        └─ NO  → Return NaN (Tier 2: Emergency)
                 │
                 └─> Epic 8 Emergency Condition (180s)
                     │
                     └─> Coordinator forces PID OFF
```

---

## References

- **Epic Brief:** `docs/epic-9-brief.md`
- **Epic 5 Baseline:** `docs/epic-5-ha-only-sensors.md` (for comparison)
- **Epic 8 Foundation:** `docs/epic-8-coordinator-design.md` (emergency/recovery state machine)
- **Architecture:** `docs/architecture.md`

---

## Next Steps After Epic 9

**If GO (Keep REST API):**
1. Deprecate Epic 5 `room_sensors.yaml` component
2. Move Epic 5 components to `components/deprecated/`
3. Update all documentation with REST API as standard
4. Roll out to third board (mev-primo-piano)
5. Consider future enhancements:
   - WebSocket push (reduce polling)
   - Authentication/SSL
   - Batch endpoints (reduce requests)

**If NO-GO (Revert to Epic 5):**
1. Execute rollback procedure (restore HA sensors)
2. Archive Epic 9 components in `components/deprecated/`
3. Update epic-9-brief.md with "REVERTED" status
4. Create post-mortem document
5. Maintain Epic 5 as stable baseline
6. Consider alternative improvements (optimize HA integration)

---

**Status:** All stories created, ready for sequential implementation  
**Next Action:** Begin Story 9.1 (Master REST API Server)

---

*Epic 9 stories index - REST API-Based Board Communication*
