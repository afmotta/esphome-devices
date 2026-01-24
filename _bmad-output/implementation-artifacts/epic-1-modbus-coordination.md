# Epic 1: Autonomous Multi-Board Climate Control via RS485 Modbus - Brownfield Enhancement

## Document Information

| Field             | Value                                          |
| ----------------- | ---------------------------------------------- |
| **Epic**          | Epic 1: Autonomous Multi-Board Climate Control |
| **Version**       | 1.2                                            |
| **Date**          | October 17, 2025                               |
| **Status**        | In Progress                                    |
| **Story Manager** | Bob (Scrum Master)                             |
| **Product Owner** | Sarah (Product Owner)                          |

---

## Epic Title

**Autonomous Multi-Board Climate Control via RS485 Modbus** - Brownfield Enhancement

---

## Epic Goal

Transform the ESPHome climate control system from Home Assistant-dependent to autonomous by implementing master/slave RS485 Modbus communication, eliminating single-point-of-failure while maintaining full HA integration and completing three-floor coverage.

---

## Epic Description

### Existing System Context

**Current Relevant Functionality:**
- Active production ESPHome-based home climate control system managing three-floor residential HVAC
- **Ground Floor**: 1 mixing valve (gruppo-miscelazione A6 board) + 4 zone fancoils + floor cooling (distribuzione-piano-terra A16 board)
- Dual PID controllers (heat/cool modes) for precise temperature control
- Heavy dependency on Home Assistant for temperature sensor data and climate mode coordination
- **Single Point of Failure**: Home Assistant downtime = complete system failure

**Technology Stack:**
- **ESPHome**: Device firmware platform
- **Kincony KC868-A6**: Mixing valve controller with RS485 UART (unused)
- **Kincony KC868-A16**: Zone distribution controller with RS485 UART (unused)
- **ESP32**: Microcontroller platform
- **RS485 Hardware**: UART pins configured but not actively used
- **Dallas Sensors**: Temperature monitoring on supply lines
- **Package-based Architecture**: Modular YAML composition (`boards/`, `components/`, `devices/`)

**Integration Points:**
- RS485 UART hardware already present and configured on both boards
- Home Assistant sensor platform integration (`platform: homeassistant`)
- ESPHome API for entity exposure to Home Assistant
- Existing PID control algorithms with tuned parameters
- Relay control patterns for mixing valves and zone distribution

### Enhancement Details

**What's Being Added/Changed:**

1. **Modbus RTU Master/Slave Protocol** (Stories 1.1-1.4):
   - Transform `gruppo-miscelazione` (A6 board) into Modbus **master** controller
   - Configure `distribuzione-piano-terra` (A16 board) as Modbus **slave** device
   - Implement data exchange: temperature sensors, climate mode, heartbeat monitoring
   - Add automatic failover logic: Modbus (primary) → Home Assistant (fallback) → Safe shutdown (emergency)

2. **Three-Floor System Completion** (Story 1.5):
   - Add new A16 board for first floor distribution (Modbus slave address 3)
   - Configure 0-10V Modbus adapter on ground floor A16 for second floor fancoil control
   - Complete RS485 Modbus network with proper bus termination

3. **Room Sensor Integration** (Story 1.6):
   - Add room-level temperature/humidity sensors for all zones
   - Technology selection: Modbus sensors OR 1-Wire/I2C sensors
   - Integrate room sensors into PID control logic for improved accuracy

4. **Documentation & Production Deployment** (Story 1.7):
   - Modbus register map documentation
   - Sensor technology selection documentation
   - RS485 wiring and troubleshooting guides
   - Production deployment via `remotes/` configuration

**How It Integrates:**

- **Additive and Parallel Approach**: Modbus communication layer added without removing existing Home Assistant integration
- **Feature Flag Control**: `use_modbus: true/false` substitution enables gradual rollout
- **Failover Architecture**: Three-tier sensor selection (Modbus → HA → Emergency)
- **Backward Compatibility**: All existing entity IDs, PID tuning, and control patterns preserved
- **Reusable Components**: `components/modbus_master.yaml`, `components/modbus_slave.yaml`, `components/room_sensors.yaml`

**Success Criteria:**

1. **Autonomy**: System continues full operation during Home Assistant outages using Modbus coordination
2. **Performance**: Modbus communication completes within 500ms; failover transitions within 30s
3. **Compatibility**: All existing Home Assistant entities and automations continue to work unchanged
4. **Reliability**: Automatic recovery when Modbus or HA communication restored; no manual intervention required
5. **Completeness**: All three floors operational with Modbus coordination
6. **Documentation**: Comprehensive guides for maintenance, troubleshooting, and future expansion

---

## Stories

This epic consists of **8 focused stories** that build the system incrementally:

### 1. **Story 1.1: Modbus Master/Slave Infrastructure Foundation**
   - Configure A6 board as Modbus master (address 1)
   - Configure A16 board as Modbus slave (address 2)
   - Implement diagnostic sensors and master→slave test communication
   - **Status**: ✅ Complete

### 2. **Story 1.2: Modbus Master - Temperature Sensor and Coordination Data Exposure**
   - Master exposes Dallas sensors and climate mode via Modbus registers
   - Create reusable `components/modbus_master.yaml`
   - Document register map
   - **Status**: ✅ Complete

### 3. **Story 1.3: Modbus Slave - Master Data Reading and Response**
   - Slave reads climate mode and heartbeat from master
   - Create reusable `components/modbus_slave.yaml`
   - Implement timeout handling and error tracking
   - Slave exposes health status registers for master polling
   - **Status**: ✅ Complete

### 4. **Story 1.4: Sensor Failover Logic Implementation**
   - Implement three-tier failover: Modbus → HA → Emergency
   - Add `template` sensor wrappers for source selection
   - Test all failover scenarios and recovery paths
   - **Status**: ✅ Complete

### 5. **Story 1.5: First Floor A16 Board + Ground Floor 0-10V Fancoil + Second Floor 0-10V Fancoil**
   - Add new A16 board for first floor (slave address 3)
   - Configure 0-10V Modbus adapter for second floor fancoil
   - Complete three-floor system integration
   - Control 4 ground floor fancoils via 4-channel Modbus 0-10V adapter
   - **Status**: 🔄 In Progress (Current Story)

### 6. **Story 1.6: Room Temperature and Humidity Sensor Integration**
   - Select sensor technology (Modbus vs 1-Wire/I2C)
   - Implement room sensors for all ground floor zones
   - Update PID controllers to use room temperature
   - **Status**: ⏳ Not Started

### 7. **Story 1.7: Documentation, Deployment, and Production Readiness**
   - Complete Modbus register map documentation
   - Create RS485 wiring and troubleshooting guides
   - Update `remotes/` configuration for production
   - Create monitoring dashboard in Home Assistant
   - **Status**: ⏳ Not Started

---

## Compatibility Requirements

- [x] **Existing APIs remain unchanged**: All Home Assistant entity IDs preserved; ESPHome API connections maintained
- [x] **Database schema changes are backward compatible**: N/A - No database changes (YAML configuration only)
- [x] **UI changes follow existing patterns**: All new sensors/controls follow ESPHome entity naming conventions
- [x] **Performance impact is minimal**: 
  - Modbus communication: ≤500ms per operation
  - CPU usage increase: ≤5%
  - Failover transition: ≤30s
  - No degradation in PID control loop timing

---

## Risk Mitigation

### Primary Risk
**Loss of heating/cooling control during Modbus implementation or communication failures**, potentially leading to uncomfortable conditions or system damage.

### Mitigation Strategy

1. **Incremental Rollout with Feature Flags**:
   - `use_modbus: false` by default - system works exactly as before
   - Enable Modbus per-board after infrastructure validation
   - Test each story independently before moving to next

2. **Three-Tier Failover Architecture**:
   - Primary: Modbus sensors (fast, autonomous)
   - Fallback: Home Assistant sensors (proven, reliable)
   - Emergency: Safe shutdown after 5 minutes of no data

3. **Parallel Operation Period**:
   - Stories 1.1-1.3: Modbus communication active but NOT used for control
   - Both Modbus and HA sensors visible in Home Assistant for comparison
   - Story 1.4 implements actual failover only after validation

4. **Comprehensive Testing**:
   - Test each story with `locals/` configuration before production
   - Simulate failures: RS485 disconnect, HA offline, both offline
   - Verify recovery paths and automatic restoration

5. **Preserve Existing Tuning**:
   - All PID control parameters remain unchanged
   - Relay control patterns identical
   - Mixing valve positioning logic preserved

### Rollback Plan

**Per-Story Rollback:**
- Revert to previous firmware version via OTA update
- Change `use_modbus: false` in configuration
- Recompile and deploy previous working configuration
- System immediately returns to HA-dependent operation

**Full Epic Rollback:**
1. Set `use_modbus: false` on all boards
2. Remove `modbus_master` and `modbus_slave` packages from device configurations
3. Recompile firmware without Modbus components
4. OTA update all boards to pre-Modbus firmware
5. System operates exactly as before Epic 1 started

**Emergency Manual Rollback:**
- Physical access to boards: Flash backup firmware via USB
- Backup configurations stored in `locals/backup-pre-modbus/`
- RS485 bus can be physically disconnected if needed

---

## Definition of Done

This epic is complete when:

- [x] **All 8 stories completed** with acceptance criteria met and integration verification passed
- [ ] **Existing functionality verified through testing**:
  - All PID controllers operate with identical behavior
  - All relay outputs function correctly
  - All temperature sensors report accurately
  - Home Assistant integration fully functional
- [ ] **Integration points working correctly**:
  - Modbus master polls all slaves successfully (addresses 2 and 3)
  - Slaves read coordination data from master every 10 seconds
  - Failover logic transitions smoothly between sources
  - Three floors respond correctly to climate mode changes
- [ ] **Documentation updated appropriately**:
  - Modbus register map complete and accurate
  - RS485 wiring guide with troubleshooting section
  - Sensor technology selection documented with rationale
  - Architecture diagram showing all boards and data flow
  - Deployment guide with step-by-step upgrade procedure
- [ ] **No regression in existing features**:
  - Temperature control accuracy maintained (±0.5°C)
  - PID tuning parameters unchanged and effective
  - Relay control timing preserved
  - Home Assistant automations continue to work
  - OTA updates function correctly
- [ ] **Production deployment successful**:
  - `remotes/` configuration updated and tested
  - All boards successfully deployed via Home Assistant ESPHome Builder
  - Monitoring dashboard operational in Home Assistant
  - System operates autonomously during simulated HA outage

---

## Dependencies and Sequencing

### Story Dependencies

```
1.1 (Infrastructure) ─────────────────────┐
                                           │
                                           v
1.2 (Master Data Exposure) ────────┬──> 1.4 (Failover Logic)
                                    │
                                    v
1.3 (Slave Data Reading) ──────────┘


1.4 (Failover Logic) ──────────────────> 1.5 (Three-Floor Completion)


1.5 (Three-Floor) ─────────────────────┬──> 1.6 (Ground Floor Fancoils)
                                        │
                                        └──> 1.7 (Room Sensors)


1.6 (Ground Floor Fancoils) ────────────┐
                                         ├──> 1.8 (Documentation & Production)
1.7 (Room Sensors) ─────────────────────┘
```

### Critical Path

1. **Foundation** (Stories 1.1 → 1.2 → 1.3): Must be completed sequentially
2. **Failover** (Story 1.4): Depends on 1.2 and 1.3; enables actual Modbus usage
3. **Three-Floor Expansion** (Story 1.5): Depends on 1.4; adds first floor and second floor control
4. **Ground Floor Fancoils** (Story 1.6): Depends on 1.5; adds precise 0-10V cooling control
5. **Room Sensors** (Story 1.7): Depends on 1.5; can proceed in parallel with 1.6
6. **Finalization** (Story 1.8): Depends on all previous stories

---

## Technical Constraints

### Hardware Constraints

- **RS485 Bus Termination**: Required at both physical ends (master and last slave)
- **RS485 Cable Length**: Maximum 1200m (typical residential: <50m)
- **Modbus Device Limit**: Maximum 247 devices (current: 3 devices - ample headroom)
- **UART Pins**: Fixed on Kincony boards - cannot be changed without hardware modification
- **ESP32 Flash Memory**: ~1.5MB available for firmware (current usage: ~800KB, post-Modbus: ~850KB)

### Software Constraints

- **ESPHome Platform**: Must use ESPHome-compatible Modbus implementation
- **Modbus RTU Protocol**: Function codes limited to 0x03 (Read Holding Registers), 0x10 (Write Multiple Registers)
- **Register Count**: 16-bit registers only (no 32-bit float support - must scale)
- **Polling Frequency**: Master polling limited by bus speed (9600 baud = ~10 registers/second)
- **YAML Composition**: Must follow existing package structure (`boards/`, `components/`, `devices/`)

### Integration Constraints

- **Home Assistant Compatibility**: Must maintain ESPHome API v1.x compatibility
- **OTA Update Size**: Firmware must fit within OTA partition (~1.3MB compressed)
- **Entity ID Preservation**: Cannot change existing entity IDs without breaking HA automations
- **PID Tuning**: Cannot modify tuning parameters without extensive re-testing

---

## Change Log

| Date       | Version | Description                                                                                                                                      | Author                  |
| ---------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- |
| 2025-10-15 | 1.0     | Epic documentation created from PRD                                                                                                              | Sarah (Product Owner)   |
| 2025-10-17 | 1.1     | Removed Story 1.5 (Ground Floor Cooling) - deferred to future phase; renumbered                                                                  | Sarah (Product Owner)   |
| 2025-10-17 | 1.2     | Added Story 1.6 (Ground Floor Fancoil Control); updated Story 1.5 status to Draft; renumbered room sensors (1.6→1.7) and documentation (1.7→1.8) | Mary (Business Analyst) |

---

## Notes

### Integration Approach

This epic follows a **safe, incremental brownfield enhancement pattern**:

1. **Additive**: New Modbus layer added without removing existing HA integration
2. **Parallel**: Both communication paths active during transition
3. **Feature-Flagged**: `use_modbus` substitution enables controlled rollout
4. **Validated**: Each story includes integration verification before next story starts
5. **Reversible**: Clear rollback path at every stage

### Future Expansion Considerations

After Epic 1 completion, the system will support:

- **Ground Floor Cooling Automation**: Intelligent coordination between fancoils and floor cooling with humidity-aware logic (deferred from Epic 1)
- **Additional Floors**: Add more A16 slaves (up to address 247)
- **Additional Sensors**: Expand Modbus register map for more room sensors
- **Advanced Coordination**: Master can coordinate supply temperatures across multiple mixing valves
- **Energy Monitoring**: Add power meters on Modbus bus for energy tracking
- **Remote Monitoring**: Master can expose aggregated data to external systems via Home Assistant

### Reference Documentation

- **PRD**: `docs/prd.md` - Complete functional requirements
- **Architecture**: `docs/architecture.md` - Detailed technical design
- **Story Files**: `docs/stories/1.*.md` - Individual story documentation
- **Copilot Instructions**: `.github/copilot-instructions.md` - Development patterns and conventions

---

## Story Manager Handoff

**This epic has been decomposed into 8 detailed user stories by Bob (Scrum Master).**

All stories follow the brownfield enhancement pattern with:
- Clear acceptance criteria
- Integration verification requirements (IV1-IV3)
- Comprehensive dev notes with architecture context
- Testing strategies and scenarios
- File location guidance
- Critical success factors

**Current Status**: Story 1.3 is **In Progress**. Stories 1.5 and 1.6 are **Draft** (awaiting implementation).

**Recent Changes (October 17, 2025)**:
1. **v1.1**: Ground Floor Cooling Automation removed from Epic 1 scope and deferred to future phase
2. **v1.2**: Added Story 1.6 (Ground Floor Fancoil 0-10V Control) to address missing requirement for 4 ground floor fancoils. Story 1.5 status updated to Draft. Room sensors renumbered 1.6→1.7, Documentation renumbered 1.7→1.8.

**Next Actions**:
1. Complete Story 1.3 implementation and validation
2. Run PO checklist validation before moving to Story 1.4
3. Ensure integration verification passes before starting failover logic
4. After Story 1.4, implement Stories 1.5-1.6 (three-floor completion + ground floor fancoils)
5. Maintain documentation updates as implementation proceeds
