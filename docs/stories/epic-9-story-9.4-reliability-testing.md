# Story 9.4: Reliability Testing & Production Validation

**Epic:** 9 - REST API-Based Board Communication  
**Story Type:** Testing & Validation  
**Estimated Effort:** 5-8 hours (2 weeks calendar time)  
**Priority:** Critical (Production Readiness)  
**Date:** November 5, 2025

## Status
Draft

---

## User Story

As a **system owner**,  
I want **comprehensive 2-week reliability testing of the REST API architecture with Home Assistant offline validation**,  
So that **I can confidently decide whether to keep REST API or revert to Epic 5 architecture based on measured performance data**.

---

## Story Context

**System Integration:**

- **Tests:** All Epic 9 components (Master, Slave, Failover)
- **Validates:** Full autonomous operation without Home Assistant
- **Measures:** Error rates, latency, temperature accuracy, uptime
- **Compares:** Against Epic 5 baseline metrics
- **Documents:** Completion report with go/no-go recommendation
- **Preserves:** Modbus 0-10V adapters for fancoil control (unchanged)

**Architecture Pattern:**

- Deploy REST API to all boards (gruppo-miscelazione + 2 distribuzione boards)
- Run 2-week soak test with continuous monitoring
- Test Home Assistant offline for 24+ hours
- Measure against MVP success criteria
- Make decision: Keep REST API or revert to Epic 5

---

## Acceptance Criteria

### Deployment Requirements

1. **All Boards Deployed:**
   - gruppo-miscelazione with REST API master (Story 9.1)
   - distribuzione-piano-terra with REST client + failover (Stories 9.2 + 9.3)
   - distribuzione-primo-piano with REST client + failover (Stories 9.2 + 9.3)
   - All firmware compiled and flashed successfully
   - All boards operational and communicating via REST

2. **Monitoring Setup:**
   - Home Assistant dashboard with REST diagnostics
   - Grafana/InfluxDB for time-series metrics (if available)
   - ESPHome log collection (syslog or file-based)
   - Manual checklist for daily observations
   - Baseline metrics documented from Epic 5

3. **Test Environment Validation:**
   - All boards have stable Ethernet/WiFi
   - mDNS working for .local hostnames
   - Network switch/router operational
   - Dallas sensors functional
   - PIDs operational with correct setpoints

### Reliability Metrics (2-Week Soak Test)

4. **REST API Error Rate:**
   - **Target:** <1% error rate over 2 weeks
   - **Measurement:** REST API error count sensors
   - **Calculation:** (Total errors / Total polls) × 100
   - **Pass criteria:** Error rate ≤ 1%
   - **Data source:** ESPHome error count sensors

5. **REST API Latency:**
   - **Target:** Average <2s, P95 <5s
   - **Measurement:** REST response time sensors (if available)
   - **Alternative:** Manual curl timing tests (daily)
   - **Pass criteria:** 95% of requests complete within 5s
   - **Data source:** Response time sensors or manual logs

6. **Temperature Control Accuracy:**
   - **Target:** ±0.5°C maintained across all zones
   - **Measurement:** Compare room temps to setpoints
   - **Calculation:** |room_temp - setpoint| ≤ 0.5°C
   - **Pass criteria:** 95% of time within tolerance
   - **Data source:** HA historical data or ESPHome logs

7. **System Uptime:**
   - **Target:** No unexpected reboots or crashes
   - **Measurement:** ESPHome uptime sensors
   - **Pass criteria:** All boards maintain uptime for full 2 weeks (except planned restarts)
   - **Data source:** Uptime sensors, boot count logs

### Autonomous Operation Validation

8. **Home Assistant Offline Test:**
   - **Duration:** 24+ hours with HA shut down
   - **Validation:** All sensors continue updating via REST
   - **Validation:** All PIDs continue operating
   - **Validation:** Temperature control maintained
   - **Validation:** No emergency shutdowns triggered (unless warranted)
   - **Pass criteria:** System fully autonomous during HA outage

9. **Network Failure Recovery:**
   - **Test:** Power cycle network switch (simulated outage)
   - **Validation:** Boards reconnect automatically
   - **Validation:** REST polling resumes within 30s
   - **Validation:** Emergency conditions trigger if outage >180s
   - **Validation:** Recovery completes after network restored
   - **Pass criteria:** Automatic recovery without manual intervention

10. **Modbus 0-10V Fancoil Validation:**
    - **Validation:** Fancoil control via Modbus 0-10V adapters still functional
    - **Validation:** No interference from REST API implementation
    - **Validation:** MEV coordination works correctly
    - **Pass criteria:** Fancoils operate as before Epic 9

### Failure Scenario Testing

11. **Master Board Failure:**
    - **Test:** Power off gruppo-miscelazione for 5 minutes
    - **Validation:** Slave boards detect REST failure
    - **Validation:** Emergency conditions trigger after 180s
    - **Validation:** PIDs forced OFF
    - **Validation:** Recovery when master restored
    - **Pass criteria:** Safe shutdown and automatic recovery

12. **Single Room Sensor Failure:**
    - **Test:** Power off one room sensor device for 5 minutes
    - **Validation:** Affected zone enters emergency
    - **Validation:** Other zones remain operational
    - **Validation:** REST API health shows "Degraded"
    - **Validation:** Recovery when sensor restored
    - **Pass criteria:** Failure isolation, no cascade

13. **Network Congestion Simulation:**
    - **Test:** Generate network traffic (large file transfer, video stream)
    - **Validation:** REST polls continue successfully
    - **Validation:** Latency may increase but stays <5s
    - **Validation:** No timeout failures
    - **Pass criteria:** REST API resilient to network load

### Decision Criteria

14. **Go/No-Go Decision:**
    - **GO (Keep REST API):** All pass criteria met
      - Error rate <1%
      - Latency P95 <5s
      - Temperature accuracy ±0.5°C
      - 24+ hour HA offline success
      - No unexpected failures
    - **NO-GO (Revert Epic 5):** Any critical failure
      - Error rate >5%
      - Latency consistently >5s
      - Temperature accuracy degraded
      - System instability
      - Cascade failures

### Documentation Requirements

15. **Completion Report:**
    - Executive summary with go/no-go recommendation
    - Detailed metrics for all acceptance criteria
    - Failure logs and root cause analysis (if any)
    - Comparison to Epic 5 baseline
    - Lessons learned and future improvements
    - Rollback procedure if reverting to Epic 5

16. **Epic 9 Documentation Updates:**
    - Update epic brief with final results
    - Update architecture.md with REST API details
    - Update deployment-guide.md with REST API setup
    - Create rest-api-troubleshooting-guide.md
    - Archive Epic 5 components in deprecated/ folder (if keeping REST)

---

## Tasks / Subtasks

- [ ] **Task 1: Deploy REST API to All Boards** (AC: 1)
  - [ ] Flash gruppo-miscelazione with Story 9.1 components
  - [ ] Flash distribuzione-piano-terra with Stories 9.2 + 9.3
  - [ ] Flash distribuzione-primo-piano with Stories 9.2 + 9.3
  - [ ] Verify all boards boot successfully
  - [ ] Verify REST endpoints accessible from each board

- [ ] **Task 2: Setup Monitoring Infrastructure** (AC: 2)
  - [ ] Create HA dashboard with all REST diagnostic sensors
  - [ ] Setup Grafana/InfluxDB (if available)
  - [ ] Configure ESPHome log collection (syslog)
  - [ ] Document Epic 5 baseline metrics for comparison
  - [ ] Create manual observation checklist template

- [ ] **Task 3: Validate Test Environment** (AC: 3)
  - [ ] Verify all boards have stable network
  - [ ] Test mDNS hostname resolution from each board
  - [ ] Verify Dallas sensors operational
  - [ ] Verify PIDs controlling zones correctly
  - [ ] Verify Modbus 0-10V fancoils operational

- [ ] **Task 4: 2-Week Soak Test - Week 1** (AC: 4-7)
  - [ ] Start monitoring on Day 1
  - [ ] Daily checklist:
    - [ ] Check REST API health sensors
    - [ ] Check error count sensors
    - [ ] Check PID operation (all zones)
    - [ ] Check temperature accuracy (sample rooms)
    - [ ] Check board uptime sensors
    - [ ] Log any anomalies or failures
  - [ ] End of Week 1: Calculate preliminary metrics

- [ ] **Task 5: Home Assistant Offline Test** (AC: 8)
  - [ ] Schedule 24-hour HA shutdown window
  - [ ] Shut down Home Assistant
  - [ ] Verify REST polling continues (check logs)
  - [ ] Verify PIDs continue operating
  - [ ] Verify temperature control maintained
  - [ ] Monitor for 24+ hours
  - [ ] Restart Home Assistant
  - [ ] Verify HA diagnostics reconnect
  - [ ] Document results

- [ ] **Task 6: Network Failure Recovery Test** (AC: 9)
  - [ ] Power cycle network switch (5 minutes)
  - [ ] Monitor board reconnection behavior
  - [ ] Verify REST polling resumes automatically
  - [ ] Check if emergency triggered (expected if >180s)
  - [ ] Verify recovery after network restored
  - [ ] Document recovery times and behavior

- [ ] **Task 7: Master Board Failure Test** (AC: 11)
  - [ ] Power off gruppo-miscelazione
  - [ ] Monitor slave boards for REST failures
  - [ ] Wait 180s, verify emergency triggers
  - [ ] Verify PIDs forced OFF
  - [ ] Power on master board
  - [ ] Verify automatic recovery
  - [ ] Document transition times

- [ ] **Task 8: Single Room Sensor Failure Test** (AC: 12)
  - [ ] Power off one room sensor device
  - [ ] Verify affected zone emergency
  - [ ] Verify other zones remain operational
  - [ ] Verify REST API health shows "Degraded"
  - [ ] Power on sensor device
  - [ ] Verify recovery
  - [ ] Document failure isolation

- [ ] **Task 9: Network Congestion Test** (AC: 13)
  - [ ] Generate network traffic (file transfer or video)
  - [ ] Monitor REST response times
  - [ ] Verify no timeout failures
  - [ ] Verify PIDs continue operating
  - [ ] Stop traffic, verify return to normal
  - [ ] Document latency impact

- [ ] **Task 10: Modbus 0-10V Fancoil Validation** (AC: 10)
  - [ ] Test all fancoil zones
  - [ ] Verify 0-10V output control working
  - [ ] Verify MEV coordination correct
  - [ ] Verify no interference from REST API
  - [ ] Document fancoil operation status

- [ ] **Task 11: 2-Week Soak Test - Week 2** (AC: 4-7)
  - [ ] Continue daily monitoring
  - [ ] Daily checklist (same as Week 1)
  - [ ] Address any issues discovered in Week 1
  - [ ] End of Week 2: Calculate final metrics
  - [ ] Compare to Epic 5 baseline

- [ ] **Task 12: Metrics Analysis & Go/No-Go Decision** (AC: 14)
  - [ ] Calculate REST API error rate
  - [ ] Calculate REST API latency (average, P95)
  - [ ] Calculate temperature accuracy
  - [ ] Review uptime and stability
  - [ ] Review HA offline test results
  - [ ] Review failure scenario results
  - [ ] Make go/no-go decision with rationale

- [ ] **Task 13: Create Completion Report** (AC: 15)
  - [ ] Write executive summary with recommendation
  - [ ] Document all metrics with charts/graphs
  - [ ] Document failures and root causes
  - [ ] Compare to Epic 5 baseline
  - [ ] Document lessons learned
  - [ ] Create rollback procedure (if no-go)

- [ ] **Task 14: Update Epic 9 Documentation** (AC: 16)
  - [ ] Update epic-9-brief.md with results
  - [ ] Update architecture.md with REST API
  - [ ] Update deployment-guide.md
  - [ ] Create rest-api-troubleshooting-guide.md
  - [ ] Archive Epic 5 components if keeping REST
  - [ ] Update PRD with Epic 9 completion

---

## Dev Notes

### Relevant Source Tree

**Epic 9 Components (Testing):**
- `components/rest_api_master.yaml` (Story 9.1)
- `components/rest_api_slave.yaml` (Story 9.2)
- `components/rest_api_failover.yaml` (Story 9.3)

**Device Configurations:**
- `devices/gruppo-miscelazione.yaml` - Master board
- `devices/distribuzione-piano-terra.yaml` - Slave board 1
- `devices/distribuzione-primo-piano.yaml` - Slave board 2

**Documentation:**
- `docs/epic-9-brief.md` - Epic overview
- `docs/architecture.md` - System architecture
- `docs/deployment-guide.md` - Deployment procedures
- `docs/epic-5-ha-only-sensors.md` - Epic 5 baseline for comparison

**Preserved Components (Epic 6):**
- `components/modbus_0_10v_output.yaml` - Fancoil control (unchanged)
- `components/fancoil.yaml` - Fancoil coordination (unchanged)

### Testing Timeline

**Week 0 (Preparation):**
- Day -2: Deploy REST API to all boards
- Day -1: Setup monitoring, validate environment
- Day 0: Start 2-week soak test

**Week 1 (Initial Testing):**
- Day 1-7: Daily monitoring, collect baseline data
- Day 3: Home Assistant offline test (24 hours)
- Day 5: Network failure recovery test
- Day 7: Week 1 metrics review

**Week 2 (Validation):**
- Day 8-14: Continue monitoring
- Day 10: Master board failure test
- Day 11: Room sensor failure test
- Day 12: Network congestion test
- Day 14: Final metrics, go/no-go decision

**Week 3 (Documentation):**
- Day 15-16: Completion report
- Day 17: Documentation updates
- Day 18: Epic 9 completion or Epic 5 revert

### Monitoring Tools

**Home Assistant Dashboard:**
- REST API health sensors (all boards)
- REST API error count sensors
- REST API last success timestamps
- Board uptime sensors
- Temperature sensors (room temps, supply temps)
- PID climate entities (mode, target, current)

**ESPHome Logs:**
- HTTP request logs (success/failure)
- JSON parsing logs
- Template sensor lambda logs
- Emergency condition state transitions
- Coordinator PID control actions

**Optional: Grafana + InfluxDB:**
- Time-series graphs for error rates
- Latency histograms
- Temperature accuracy over time
- Uptime tracking

**Manual Tools:**
- curl for spot-checking REST endpoints
- ping for network latency baseline
- speedtest for network bandwidth

### Epic 5 Baseline Metrics (For Comparison)

**Need to Document:**
- HA sensor update frequency
- HA sensor error rate (if any)
- Temperature accuracy during Epic 5
- System behavior during HA restarts (Epic 5)
- Typical HA sensor latency (~1-5s)

**Comparison Goals:**
- REST API should be ≤ Epic 5 error rate
- REST API latency should be ≤ Epic 5 latency
- Temperature accuracy should match Epic 5
- Autonomy should be better (HA offline resilience)

### Success Metrics (MVP)

From Epic 9 brief, must achieve:
1. ✅ Master exposes REST API endpoints with JSON responses
2. ✅ Slave polls master endpoints successfully (10s interval)
3. ✅ Room sensors accessed via REST (ESPHome-to-ESPHome)
4. ✅ Two-tier failover works (REST → Emergency)
5. ✅ **24+ hour autonomous operation without Home Assistant**
6. ✅ **<1% REST API error rate**
7. ✅ **±0.5°C temperature accuracy maintained**
8. ✅ Web browser inspection works (human-readable JSON)
9. ✅ Modbus 0-10V outputs continue to function (fancoil control)
10. ✅ **2-week reliability testing completes successfully**

### Common Issues & Mitigation

**Issue: High error rate (>5%)**
- Root cause: Network instability, mDNS failures
- Mitigation: Switch to static IPs, improve network infrastructure
- Decision: No-go if cannot resolve

**Issue: High latency (>5s consistently)**
- Root cause: Network congestion, underpowered boards
- Mitigation: Optimize network, increase update_interval
- Decision: No-go if temperature control degraded

**Issue: Temperature accuracy degraded**
- Root cause: REST latency or sensor polling issues
- Mitigation: Reduce update_interval, improve network
- Decision: No-go if >±1°C consistently

**Issue: Cascade failures**
- Root cause: Single failure affects multiple zones
- Mitigation: Review failure isolation logic
- Decision: No-go if not isolated properly

**Issue: HA offline test fails**
- Root cause: Hidden HA dependencies not eliminated
- Mitigation: Review all sensor sources, eliminate HA deps
- Decision: No-go if cannot achieve autonomy

### Rollback Procedure (No-Go Decision)

**If reverting to Epic 5:**

1. **Prepare Epic 5 Configurations:**
   - Restore `platform: homeassistant` sensors
   - Restore Epic 5 room_sensors.yaml component
   - Remove Epic 9 REST components

2. **Flash Boards:**
   - Recompile firmware with Epic 5 config
   - Flash all boards with Epic 5 firmware
   - Verify Epic 5 operation restored

3. **Validation:**
   - Verify HA sensors working
   - Verify PIDs operating normally
   - Verify temperature control restored
   - Monitor for 24 hours

4. **Documentation:**
   - Document rollback reason
   - Archive Epic 9 components in deprecated/
   - Update epic-9-brief.md with "REVERTED" status
   - Create lessons learned document

5. **Post-Mortem:**
   - Analyze root causes of failure
   - Identify improvements for future attempts
   - Document Epic 5 as stable baseline

### Decision Authority

**Go/No-Go Decision Maker:**
- Alberto (System Owner)

**Consultation:**
- Sarah (Product Owner) - Business impact
- Dev Agent - Technical feasibility
- Mary (Business Analyst) - Requirements met

**Decision Factors:**
- Safety: No compromise on climate control safety
- Reliability: Must match or exceed Epic 5
- Autonomy: HA independence is key benefit
- Complexity: Simpler is better if equivalent reliability

---

## Change Log

| Date       | Version | Description            | Author     |
| ---------- | ------- | ---------------------- | ---------- |
| 2025-11-05 | 1.0     | Initial story creation | Sarah (PO) |

---

## Dev Agent Record

### Agent Model Used
*To be populated during implementation*

### Debug Log References
*To be populated during implementation*

### Completion Notes List
*To be populated during implementation*

### File List
*To be populated during implementation*

---

## QA Results

*To be populated after QA review*

---

**Story Status:** Draft - Ready for Testing (Depends on Stories 9.1, 9.2, 9.3)  
**Epic Completion:** This story completes Epic 9 with go/no-go decision

---

## Testing Checklist Template

**Daily Observation Checklist (Copy for each day):**

```
Date: ___________
Observer: ___________

[ ] All boards online (gruppo, piano-terra, primo-piano)
[ ] REST API health: Healthy / Degraded / Failed
[ ] Error counts: gruppo=___ terra=___ primo=___
[ ] Board uptimes: gruppo=___ terra=___ primo=___
[ ] Temperature accuracy spot check: Zone=___ Setpoint=___ Actual=___ Delta=___
[ ] PID modes correct: ___
[ ] Fancoils operational: Yes / No / Issues: ___
[ ] Any anomalies or failures: ___________

Notes:
___________________________________________
```

**Week 1 Summary:**
- Total polls: ___________
- Total errors: ___________
- Error rate: _________%
- Average latency: ___________ms
- Temperature accuracy: ___________

**Week 2 Summary:**
- Total polls: ___________
- Total errors: ___________
- Error rate: _________%
- Average latency: ___________ms
- Temperature accuracy: ___________

**Final Decision: GO / NO-GO**
**Rationale:** ___________________________________________
