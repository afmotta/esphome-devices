# Epic 3: HA-Coordinated Independent Boards - Architecture Simplification

## Document Information

| Field             | Value                                     |
| ----------------- | ----------------------------------------- |
| **Epic**          | Epic 3: HA-Coordinated Independent Boards |
| **Version**       | 1.2                                       |
| **Date**          | October 21, 2025                          |
| **Status**        | Draft                                     |
| **Story Manager** | Bob (Scrum Master)                        |
| **Product Owner** | Sarah (Product Owner)                     |

---

## Epic Title

**HA-Coordinated Independent Boards** - Architecture Simplification

---

## Epic Goal

Simplify system architecture by eliminating board-to-board Modbus master/slave communication while preserving Modbus for sensor/adapter connectivity, making each board independently coordinated through Home Assistant for improved maintainability and deployment flexibility.

---

## Epic Description

### Current Architecture (Epic 1)

**Board-to-Board Modbus Coordination:**
- `gruppo-miscelazione` (A6) = Modbus **master**
- `distribuzione-piano-terra` (A16) = Modbus **slave** (address 2)
- `distribuzione-primo-piano` (A16) = Modbus **slave** (address 3)
- Master exposes: Dallas temperature sensors, climate mode
- Slaves read: Temperature data, climate mode, heartbeat from master
- Three-tier failover: Modbus → HA → Emergency shutdown

**Modbus Usage:**
- **Board-to-Board**: Master/slave registers for coordination data
- **Board-to-Sensors**: Temperature/humidity sensors via Modbus
- **Board-to-Adapters**: 0-10V adapters for fancoil control

**Problems with Current Approach:**

1. **Single Point of Failure**: Master board (gruppo-miscelazione) failure breaks entire system
2. **Complex Deployment**: Must deploy master first, then slaves in sequence
3. **Tight Coupling**: Slave boards cannot operate independently during master maintenance
4. **Register Mapping Overhead**: Maintaining register map for board coordination
5. **Failover Complexity**: Three-tier failover logic adds code complexity
6. **Testing Difficulty**: Cannot test individual boards in isolation
7. **Debugging Challenge**: Modbus communication failures hard to diagnose

### Proposed Architecture (Epic 3)

**HA-Coordinated Independent Boards:**
- Each board operates **independently**
- All boards read climate mode from **Home Assistant** (single source of truth)
- All boards expose their sensors/outputs to **Home Assistant**
- No board-to-board Modbus communication
- Each board still uses Modbus for:
  - ✅ **Temperature/humidity sensors** (Modbus sensors - primary source)
  - ✅ **0-10V adapters** (fancoil control)
  - ❌ **Board-to-board coordination** (removed)

**Benefits:**

1. **Independent Operation**: Each board works standalone (even with HA outages)
2. **Simplified Deployment**: Deploy boards in any order, no dependencies
3. **Easier Testing**: Test each board individually without full system
4. **No Master/Slave Complexity**: All boards are equal peers
5. **HA as Coordinator**: Leverage existing HA infrastructure for coordination
6. **Resilient Failover**: Smart failover per data type:
   - **Climate mode**: HA → Local cache (persistent across reboots)
   - **Temperature sensors**: Modbus (primary) → HA (backup) → Emergency
7. **Better Debugging**: Clear separation: board issues vs HA issues
8. **Flexible Topology**: Add/remove boards without reconfiguring others
9. **HA Outage Tolerance**: System continues normal operation during HA downtime using cached climate mode

**Trade-offs:**

- **HA Dependency**: System requires Home Assistant for climate mode changes (but cached locally)
- **Network Dependency**: Requires WiFi/network connectivity for initial setup and mode changes
- **Response Time**: Slightly slower for mode changes (HA API vs direct Modbus), but mode changes are rare

**Home Assistant as Coordinator:**
```yaml
# HA provides coordination data to ALL boards
sensor.thermostat_mode          → All boards read this (climate mode coordination)
                                → Cached locally in flash (persistent)
sensor.modbus_temp_room_*       → Backup temperature sensors (if Modbus fails)
sensor.dallas_piano_terra       → Exposed by gruppo-miscelazione
sensor.dallas_primo_piano       → Exposed by gruppo-miscelazione
input_number.setpoint_*         → All boards read their setpoints
```

**Climate Mode Caching:**
- **Primary Source**: Home Assistant sensor (sensor.thermostat_mode)
- **Local Cache**: ESPHome `globals` with `restore_value: true` (persists across reboots)
- **Update Frequency**: Only when HA value changes (typically once per season)
- **HA Outage Behavior**: Continue using last known climate mode from cache
- **Cache Validity**: Indefinite (mode changes are manual/seasonal)

**Sensor Architecture (Redundancy):**
- **Primary**: Modbus temperature/humidity sensors (direct to each board)
- **Backup**: Home Assistant sensors (HA-connected sensors as fallback)
- **Failover**: Modbus → HA → Emergency shutdown
- Each room has **two physical sensors** for redundancy

### Scope

**Epic 1 Components to Remove:**
- `components/modbus_master.yaml` - No more master board
- `components/modbus_slave.yaml` - No more slave boards
- `components/modbus_master_registers.yaml` - No register coordination (board-to-board)
- `components/modbus_slave_registers.yaml` - No register coordination (board-to-board)
- `components/modbus_test.yaml` - No board-to-board testing needed

**Epic 1 Components to Modify:**
- `components/sensor_failover.yaml` - Remove board-to-board Modbus tier, keep Modbus sensor → HA → Emergency

**Epic 1 Components to Keep:**
- ✅ `components/modbus_0_10v_output.yaml` - Still needed for fancoil adapters
- ✅ Any sensor components using Modbus for temperature/humidity sensors
- ✅ Sensor failover logic - Modified to remove board-to-board tier, keep Modbus sensor → HA → Emergency

**Device Files to Modify:**
- `devices/gruppo-miscelazione.yaml` - Remove master packages, keep sensor Modbus
- `devices/distribuzione-piano-terra.yaml` - Remove slave packages, keep adapter Modbus
- `devices/distribuzione-primo-piano.yaml` - Remove slave packages, keep adapter Modbus

**New Components to Create:**
- `components/ha_climate_mode_cached.yaml` - Read climate mode from HA with local flash caching
  - Uses ESPHome `globals` with `restore_value: true`
  - Caches last known mode persistently
  - Updates cache when HA value changes
  - Falls back to cache during HA outages
- `components/ha_temperature_failover.yaml` - Simple HA → Emergency failover (if needed)
- Or inline these directly in device files for clarity

**Documentation to Update:**
- `docs/architecture.md` - Update coordination model
- `docs/epic-1-modbus-coordination.md` - Mark board-to-board stories as superseded
- `docs/modbus-register-map.md` - Remove board coordination registers, keep sensor/adapter registers
- `.github/copilot-instructions.md` - Update architecture patterns

---

## Stories

This epic consists of **4 focused stories** for architecture migration:

### 1. **Story 3.1: Remove Board-to-Board Modbus from gruppo-miscelazione**
   - Remove modbus_master package
   - Remove modbus_master_registers package
   - Keep Dallas sensors exposed to Home Assistant via ESPHome API
   - Remove master-specific automation and scripts
   - Verify mixing valve control still works via HA coordination
   - **Status**: ⏳ Not Started

### 2. **Story 3.2: Remove Board-to-Board Modbus from Distribution Boards**
   - Update distribuzione-piano-terra.yaml to remove slave packages
   - Update distribuzione-primo-piano.yaml to remove slave packages
   - Keep 0-10V adapter Modbus (address 4, 5)
   - Add HA climate mode reading with local caching
   - Implement climate mode cache using ESPHome globals (restore_value: true)
   - Remove board-to-board failover logic
   - **Status**: ⏳ Not Started

### 3. **Story 3.3: Simplify Sensor Failover (Remove Board-to-Board Tier)**
   - Keep Modbus temperature/humidity sensors as **primary** source (each board reads its own sensors)
   - Keep HA sensors as **backup** source (redundant physical sensors)
   - Remove board-to-board Modbus tier from failover logic
   - Update failover: Modbus sensor (primary) → HA sensor (backup) → Emergency shutdown
   - Each room has two physical sensors: one on Modbus, one visible to HA
   - **Status**: ⏳ Not Started

### 4. **Story 3.4: Documentation and Register Map Cleanup**
   - Update architecture documentation to reflect HA coordination
   - Update modbus-register-map.md (remove board coordination section)
   - Update Epic 1 documentation to show superseded stories
   - Create HA automation examples for climate mode coordination
   - Document new deployment process (boards independent)
   - **Status**: ⏳ Not Started

---

## Compatibility Requirements

- [x] **Functionality preserved**: Temperature control behavior identical
- [x] **Modbus kept for sensors/adapters**: 0-10V adapters and Modbus sensors unchanged
- [x] **Entity IDs unchanged**: All HA entity IDs remain the same
- [x] **PID tuning unchanged**: Control parameters identical
- [x] **Autonomy trade-off**: System now requires HA for mode changes only
  - **Mitigation**: Climate mode cached locally in flash (persistent across reboots)
  - **Result**: System continues normal operation during HA outages using cached mode

---

## Risk Mitigation

### Primary Risk
**Increased dependency on Home Assistant** for climate mode coordination vs. autonomous Modbus coordination in Epic 1.

### Mitigation Strategy

1. **Climate Mode Caching** (NEW - Primary Mitigation):
   - Climate mode cached in ESP32 flash memory using ESPHome `globals`
   - `restore_value: true` ensures cache persists across reboots/power loss
   - System continues normal operation during HA outages using cached mode
   - Only requires HA connectivity when changing climate mode (seasonal change)
   - Example: Switch from "heat" to "cool" mode requires HA, but daily operation does not

2. **Home Assistant Reliability**:
   - HA is production-grade, mature platform
   - Run HA on reliable hardware (not Raspberry Pi - use mini PC or VM)
   - Implement HA backups and monitoring
   - Consider HA Core in Docker for stability

3. **Graceful Degradation**:
   - Each board monitors HA sensor availability for temperature sensors
   - Climate mode: Uses cached value during HA outages (no timeout)
   - Temperature sensors: Failover Modbus → HA → Emergency
   - Visual indication of HA connection status (optional: LED/status sensor)

3. **Network Redundancy**:
   - WiFi boards on reliable network infrastructure
   - Consider static IP reservations for boards
   - Monitor WiFi signal strength sensors in ESPHome

4. **Rollback Plan**:
   - Keep Epic 1 board-to-board Modbus as alternative architecture
   - Can revert to Epic 1 if HA coordination proves unreliable
   - Components stored in `components/deprecated-epic1/` for reference

### Comparison: Epic 1 vs Epic 3

| Aspect                      | Epic 1 (Board-to-Board Modbus)  | Epic 3 (HA Coordination + Caching)         |
| --------------------------- | ------------------------------- | ------------------------------------------ |
| **Autonomy**                | ✅ Autonomous (no HA needed)     | ✅ Autonomous (cached mode, HA for changes) |
| **Complexity**              | ❌ High (master/slave, failover) | ✅ Low (simple HA reading + cache)          |
| **Single Point of Failure** | ❌ Master board failure          | ✅ HA (but cached, more reliable)           |
| **Deployment**              | ❌ Sequential (master first)     | ✅ Independent (any order)                  |
| **Testing**                 | ❌ Need full system              | ✅ Test boards individually                 |
| **Debugging**               | ❌ Complex (Modbus traces)       | ✅ Simple (HA API logs)                     |
| **Code Maintenance**        | ❌ More code, more bugs          | ✅ Less code, simpler                       |
| **Response Time**           | ✅ Fast (direct Modbus)          | ✅ Fast (local cache, rare HA calls)        |
| **HA Outage Impact**        | ✅ No impact                     | ✅ Minimal (mode cached, sensors on Modbus) |

---

## Definition of Done

This epic is complete when:

- [ ] **All 4 stories completed** with acceptance criteria met
- [ ] **Board-to-board Modbus removed**:
  - No master/slave Modbus packages in device configs
  - No board coordination registers
  - No modbus_master or modbus_slave components
- [ ] **Sensor/adapter Modbus preserved**:
  - 0-10V adapters still work via Modbus
  - Modbus temperature/humidity sensors work as primary source
  - Sensor failover works: Modbus sensor → HA sensor → Emergency
- [ ] **HA coordination working**:
  - All boards read climate mode from HA (with local caching)
  - Climate mode persists across reboots and HA outages
  - All boards read temperature sensors from Modbus (primary)
  - All boards can failover to HA sensors (backup)
  - Climate control responds correctly to mode changes
- [ ] **Existing functionality preserved**:
  - Temperature control accuracy maintained (±0.5°C)
  - PID tuning unchanged and effective
  - Relay/output control identical to before
- [ ] **Documentation updated**:
  - Architecture reflects HA coordination model
  - Register map shows only sensor/adapter registers
  - Deployment guide updated for independent boards
- [ ] **Production deployment successful**:
  - All boards deployed and operational
  - 7-day monitoring shows stable operation
  - HA coordination responsive (<2s for mode changes)

---

## Dependencies and Sequencing

### Epic Dependencies

```
Epic 1 (Board-to-Board Modbus) ──> Stories 1.1-1.4 COMPLETE
                                         │
                                         └──> Epic 3 (Remove Board-to-Board)
                                                   │
                                                   ├──> Keep: 0-10V Modbus
                                                   └──> Remove: Master/Slave

Epic 2 (PID Simplification) ──> Can run in parallel with Epic 3
```

**Note**: Epic 3 **supersedes** Epic 1 Stories 1.5-1.8 (those stories assume board-to-board Modbus)

### Story Dependencies

```
Story 3.1 (Remove Master) ──────────┬──> Story 3.3 (Simplify Sensors)
                                    │           │
Story 3.2 (Remove Slaves) ──────────┘           │
                                                 v
                                        Story 3.4 (Documentation)
```

**Critical Path**: Stories 3.1 and 3.2 must complete before 3.3. Story 3.4 runs after all implementation complete.

---

## Technical Constraints

### Home Assistant Constraints

- **API Response Time**: Typical 50-200ms for sensor reads (vs <10ms Modbus)
- **ESPHome API**: Native integration via ESPHome API (no custom code)
- **Entity Availability**: Sensors must be marked `internal: false` to expose to HA
- **Update Frequency**: HA sensors updated at ESPHome `update_interval` rate

### Network Constraints

- **WiFi Reliability**: All boards must have stable WiFi connection
- **API Connection**: ESPHome native API must be connected to HA
- **Latency**: Typical home network latency acceptable (<100ms)

### Backward Compatibility Constraints

- **Entity IDs**: Must preserve existing entity IDs (no HA automation breakage)
- **Sensor Names**: Temperature sensor names must remain unchanged
- **PID References**: PID controllers reference sensors by ID (no changes)

---

## Success Metrics

- **Code Reduction**: Remove ~400 lines of YAML (master/slave/failover components)
- **Component Count**: Remove 6 components (master, slave, registers, test, complex failover)
- **Firmware Size**: Reduce by ~30KB (no Modbus master/slave overhead)
- **Deployment Time**: Independent board deployment (any order, parallel possible)
- **Debugging Time**: Faster issue resolution (simpler architecture)
- **Response Time**: Climate mode changes propagate within 2 seconds

---

## Migration Strategy

### Phase 1: Preparation (Before Epic 3)
1. Ensure all HA automations reference correct entity IDs
2. Verify HA is stable and reliable (uptime, backups)
3. Document current board-to-board Modbus behavior for comparison
4. Create test plan for post-migration validation

### Phase 2: Implementation (Epic 3 Stories)
1. Story 3.1: Remove master from gruppo-miscelazione
2. Story 3.2: Remove slaves from distribution boards
3. Story 3.3: Simplify temperature sensor reading
4. Story 3.4: Update documentation

### Phase 3: Validation (After Epic 3)
1. Monitor temperature control accuracy for 7 days
2. Verify climate mode changes propagate correctly and cache updates
3. Test HA restart scenario (boards reconnect gracefully, Modbus sensors continue working)
4. Test climate mode caching:
   - Change mode in HA, verify cache updates
   - Reboot board, verify cached mode persists
   - Disconnect HA, verify board continues with cached mode
5. Simulate Modbus sensor failure (boards failover to HA backup sensors)
6. Simulate extended HA outage (boards continue with Modbus sensors + cached climate mode)
7. Measure response times for typical operations

### Rollback Option

If Epic 3 proves problematic, can revert to Epic 1 architecture:
1. Restore master/slave packages from `components/deprecated-epic1/`
2. Re-deploy Epic 1 firmware via OTA
3. System returns to autonomous board-to-board Modbus

---

## Change Log

| Date       | Version | Description                                                                         | Author                  |
| ---------- | ------- | ----------------------------------------------------------------------------------- | ----------------------- |
| 2025-10-21 | 1.0     | Epic created from architecture review                                               | Mary (Business Analyst) |
| 2025-10-21 | 1.1     | Clarified sensor architecture: Modbus sensors remain primary, HA sensors are backup | Mary (Business Analyst) |
| 2025-10-21 | 1.2     | Added climate mode local caching for HA outage resilience                           | Mary (Business Analyst) |

---

## Notes

### Relationship to Epic 1

Epic 3 **supersedes** the following Epic 1 stories:
- ❌ Story 1.1: Master/Slave Infrastructure (remove board-to-board Modbus)
- ❌ Story 1.2: Master Data Exposure (remove board coordination registers)
- ❌ Story 1.3: Slave Data Reading (remove board coordination)
- ⚠️ Story 1.4: Sensor Failover Logic (modify - remove board-to-board tier, keep Modbus sensor → HA → Emergency)
- ✅ Story 1.5: Three-Floor Completion (still valid - boards use Modbus for sensors/adapters)
- ✅ Story 1.6: Room Sensors (still valid - Modbus sensors are primary, HA sensors are backup)
- ✅ Story 1.7: Documentation (still needed, update for Epic 3)

**Work Completed in Epic 1 (Stories 1.1-1.4):**
- Board-to-board Modbus code will be **archived** in `components/deprecated-epic1/`
- Sensor failover logic will be **modified** (remove board-to-board tier only)
- Learning and testing from Epic 1 still valuable (validated Modbus hardware works)
- Register map knowledge still useful for sensor/adapter Modbus
- **Modbus sensor infrastructure remains** (primary temperature source)

### Why Change from Epic 1?

**Original Epic 1 Goal**: Autonomous system that works without Home Assistant

**Reality Check**:
1. **HA is Production-Grade**: Modern Home Assistant is very reliable
2. **Complexity Cost**: Board-to-board Modbus adds significant complexity for limited benefit
3. **Deployment Friction**: Master/slave dependencies make deployment harder
4. **Debugging Overhead**: Modbus communication failures hard to diagnose
5. **Testing Burden**: Cannot test boards independently

**Epic 3 Philosophy**: 
- **Leverage HA strengths**: It's already there, stable, and powerful for coordination
- **Simplify where possible**: Remove complexity that doesn't add significant value
- **Keep Modbus where useful**: Sensors and 0-10V adapters benefit from Modbus (low latency, reliable)
- **Cache infrequent data**: Climate mode cached locally (changes rarely, critical for operation)
- **Redundant Sensors**: Each room has two physical sensors (Modbus primary, HA backup)
- **Independent boards**: Easier to develop, test, and maintain
- **Resilient to HA outages**: System continues normal operation with cached mode + Modbus sensors

### Future Enhancements (Post-Epic 3)

Climate mode caching (v1.2) already provides resilience to HA outages. Additional enhancements if needed:

1. **Local Temperature Sensor Caching**: Cache last known temperature from HA backup sensors
   - Useful if both Modbus sensor AND HA fail
   - Probably not needed (redundant physical sensors already in place)
2. **Manual Mode Override**: Physical button/switch to change climate mode without HA
   - Useful for emergency mode changes if HA down and mode change needed
   - Low priority (seasonal changes can wait for HA restoration)
3. **WiFi Fallback**: Automatic AP mode if WiFi fails for manual configuration
   - Allows direct access to ESP32 web interface without network
4. **Status LED**: Visual indication of HA connection, sensor status, mode cache age
   - Helpful for debugging and system health monitoring

But start with climate mode caching (v1.2) and only add complexity if actually needed.

---

## Story Manager Handoff

**This epic represents a strategic architecture pivot from Epic 1.**

After implementing Epic 1 Stories 1.1-1.4, the team has learned that:
- Board-to-board Modbus coordination adds significant complexity
- The autonomous benefit doesn't outweigh the maintenance cost
- Home Assistant is reliable enough to serve as coordinator
- Simpler architectures are easier to maintain and debug

**Recommendation**: 
1. Complete Epic 2 (PID simplification) first - lower risk, high value
2. Implement Epic 3 to simplify board coordination
3. Keep Epic 1 master/slave code as reference in deprecated folder

**Risk Level**: Medium (architecture change, but simpler than Epic 1)  
**Effort**: Medium (need to carefully remove master/slave code)  
**Value**: Very High (dramatic simplification, easier maintenance)

**Decision Point**: Product Owner should decide between:
- **Option A**: Continue with Epic 1 (autonomous board-to-board Modbus)
- **Option B**: Pivot to Epic 3 (HA-coordinated independent boards)

This epic document supports Option B with clear rationale and migration path.
