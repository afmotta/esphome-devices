````markdown
# Epic 4: Room-Based Component Architecture - Code Organization Refactoring

## Document Information

| Field             | Value                                     |
| ----------------- | ----------------------------------------- |
| **Epic**          | Epic 4: Room-Based Component Architecture |
| **Version**       | 1.0                                       |
| **Date**          | October 23, 2025                          |
| **Status**        | Draft                                     |
| **Story Manager** | Bob (Scrum Master)                        |
| **Product Owner** | Sarah (Product Owner)                     |

---

## Epic Title

**Room-Based Component Architecture** - Code Organization Refactoring

---

## Epic Goal

Reorganize ESPHome components from functionality-based structure (PIDs, sensors, outputs) to room-based structure (Soggiorno, Cucina, Bagno, etc.) for improved maintainability, clarity, and easier per-room configuration management.

---

## Epic Description

### Current Architecture (Functionality-Based)

**Current Organization Pattern:**

The system currently organizes code by **functionality type** across device files:

```yaml
# devices/distribuzione-piano-terra.yaml (Current)
packages:
  pid_sensors_soggiorno: !include pid_sensors.yaml
  pid_sensors_cucina: !include pid_sensors.yaml
  pid_sensors_bagno: !include pid_sensors.yaml
  pid_sensors_anticamera: !include pid_sensors.yaml

sensor:
  - platform: homeassistant
    id: ha_soggiorno_temperature
  - platform: homeassistant
    id: ha_cucina_temperature
  - platform: homeassistant
    id: ha_bagno_temperature
  - platform: homeassistant
    id: ha_anticamera_temperature

climate:
  - platform: pid
    id: pid_soggiorno
  - platform: pid
    id: pid_cucina
  - platform: pid
    id: pid_bagno
  - platform: pid
    id: pid_anticamera

output:
  - platform: slow_pwm
    id: slow_pwm_soggiorno
  - platform: slow_pwm
    id: slow_pwm_cucina
  - platform: slow_pwm
    id: slow_pwm_bagno
  - platform: slow_pwm
    id: slow_pwm_anticamera
```

**Problems with Current Approach:**

1. **Scattered Room Logic**: Each room's configuration scattered across multiple sections (sensors, climate, outputs, scripts)
2. **Difficult to Understand**: Hard to see complete picture of what controls a specific room
3. **Copy-Paste Errors**: Repeated patterns for each room increase risk of mistakes (wrong ID references)
4. **Maintenance Burden**: Changing room configuration requires editing multiple sections
5. **No Room Encapsulation**: Can't easily add/remove/modify a room as a unit
6. **Testing Difficulty**: Can't isolate or test a single room's configuration
7. **Configuration Drift**: Room-specific parameters (setpoints, PID tuning) not co-located with room definition

### Proposed Architecture (Room-Based)

**New Organization Pattern:**

Organize code by **rooms** with each room as a self-contained component:

```yaml
# devices/distribuzione-piano-terra.yaml (Proposed)
packages:
  board: !include ../boards/a16.yaml
  wifi: !include ../boards/wifi.yaml
  
  # Room-based components - each contains ALL room logic
  room_soggiorno: !include
    file: ../components/rooms/ground_floor/soggiorno.yaml
    vars:
      room_name: "Soggiorno"
      room_slug: soggiorno
      ha_temperature: sensor.room_soggiorno_temperature
      default_target: 22.0
      relay_ids: [relay_05, relay_06, relay_07]
      pid_tuning: {kp: 0.8, ki: 0.005, kd: 0.05}
  
  room_cucina: !include
    file: ../components/rooms/ground_floor/cucina.yaml
    vars:
      room_name: "Cucina"
      room_slug: cucina
      ha_temperature: sensor.room_cucina_temperature
      default_target: 22.0
      relay_ids: [relay_01, relay_02]
      pid_tuning: {kp: 0.8, ki: 0.005, kd: 0.05}
  
  room_bagno: !include
    file: ../components/rooms/ground_floor/bagno.yaml
    vars:
      room_name: "Bagno"
      room_slug: bagno
      ha_temperature: sensor.room_bagno_temperature
      default_target: 23.0
      relay_ids: [relay_03]
      pid_tuning: {kp: 0.8, ki: 0.005, kd: 0.05}
  
  room_anticamera: !include
    file: ../components/rooms/ground_floor/anticamera.yaml
    vars:
      room_name: "Anticamera"
      room_slug: anticamera
      ha_temperature: sensor.room_anticamera_temperature
      default_target: 20.0
      relay_ids: [relay_04]
      pid_tuning: {kp: 0.8, ki: 0.005, kd: 0.05}

# Global mode coordination (stays at device level)
text_sensor:
  - platform: homeassistant
    id: climate_mode
    entity_id: sensor.thermostat_mode
    on_value:
      - lambda: |-
          auto mode = CLIMATE_MODE_OFF;
          if (id(climate_mode).state == "HEAT") {
            mode = CLIMATE_MODE_HEAT;
          }
          
          id(pid_soggiorno).make_call().set_mode(mode).perform();
          id(pid_cucina).make_call().set_mode(mode).perform();
          id(pid_bagno).make_call().set_mode(mode).perform();
          id(pid_anticamera).make_call().set_mode(mode).perform();
```

**Room Component Structure:**

```yaml
# components/rooms/ground_floor/soggiorno.yaml (New)
substitutions:
  room_name: ${room_name}
  room_slug: ${room_slug}

sensor:
  # Temperature sensor from Home Assistant
  - platform: homeassistant
    name: "${room_name} Temperature"
    entity_id: ${ha_temperature}
    id: ha_${room_slug}_temperature
    internal: true
  
  # PID output sensor
  - platform: pid
    climate_id: pid_${room_slug}
    name: "${room_name} PID Output"
    type: HEAT

climate:
  # PID controller
  - platform: pid
    id: pid_${room_slug}
    name: "PID ${room_name}"
    sensor: ha_${room_slug}_temperature
    default_target_temperature: ${default_target}
    heat_output: slow_pwm_${room_slug}
    control_parameters:
      kp: ${pid_tuning.kp}
      ki: ${pid_tuning.ki}
      kd: ${pid_tuning.kd}
    visual:
      min_temperature: 15
      max_temperature: 30
      temperature_step: 0.5

output:
  # Slow PWM output controlling room relays
  - platform: slow_pwm
    id: slow_pwm_${room_slug}
    period: 30s
    turn_on_action:
      # Dynamically generated from relay_ids var
      %for relay_id in ${relay_ids}%
      - switch.turn_on: ${relay_id}
      %endfor%
    turn_off_action:
      %for relay_id in ${relay_ids}%
      - switch.turn_off: ${relay_id}
      %endfor%
```

**Benefits:**

1. **Room Encapsulation**: Each room is a single, cohesive component
2. **Clarity**: Complete room configuration visible in one file
3. **Maintainability**: Change room parameters in one place
4. **Reusability**: Room templates can be instantiated with different vars
5. **Testing**: Easy to test individual rooms in isolation
6. **Documentation**: Room component serves as documentation of room capabilities
7. **Scalability**: Add new rooms by instantiating template with new vars
8. **Reduced Errors**: No ID cross-references between distant file sections
9. **Co-Location**: Room-specific PID tuning, setpoints, relay mappings all together
10. **Flexible Configuration**: Easy to create room variants (e.g., bathroom with higher default temp)

### Scope

**New Directory Structure:**
```
components/
  rooms/
    ground_floor/
      soggiorno.yaml
      cucina.yaml
      bagno.yaml
      anticamera.yaml
    first_floor/
      zona_1.yaml
      zona_2.yaml
    _templates/
      room_with_pid.yaml        # Generic room template
      room_with_fancoil.yaml    # Room with fancoil control
      room_ground_floor.yaml    # Ground floor room base (existing, might refactor)
```

**Device Files to Refactor:**
- `devices/distribuzione-piano-terra.yaml` - Convert 4 rooms to room-based components
- `devices/distribuzione-primo-piano.yaml` - Convert 2 rooms to room-based components

**Components to Create:**
- `components/rooms/ground_floor/*.yaml` - One file per ground floor room
- `components/rooms/first_floor/*.yaml` - One file per first floor room
- `components/rooms/_templates/room_with_pid.yaml` - Generic reusable template (optional)

**Components to Keep (Unchanged):**
- `boards/*.yaml` - No changes (board definitions stay)
- `components/dallas.yaml` - No changes (sensor definitions stay)
- `components/fancoil.yaml` - No changes (fancoil logic stays)
- `components/pid_sensors.yaml` - Might deprecate or absorb into room components

**Documentation to Update:**
- `docs/architecture.md` - Update component organization section
- `.github/copilot-instructions.md` - Update file organization patterns
- Add new doc: `docs/room-component-guide.md` - How to create/modify room components

---

## Stories

This epic consists of **4 focused stories** for incremental refactoring:

### 1. **Story 4.1: Create Room Component Template and Ground Floor Prototype**
   - Design room component interface (vars contract)
   - Create `components/rooms/_templates/room_with_pid.yaml` template
   - Refactor Soggiorno (ground floor) as prototype
   - Test prototype compiles and works identically to current
   - Document room component pattern
   - **Status**: ⏳ Not Started

### 2. **Story 4.2: Refactor Ground Floor Rooms (Cucina, Bagno, Anticamera)**
   - Convert Cucina to room component
   - Convert Bagno to room component
   - Convert Anticamera to room component
   - Update `devices/distribuzione-piano-terra.yaml` to use all room components
   - Verify all 4 rooms work identically to before
   - **Status**: ⏳ Not Started

### 3. **Story 4.3: Refactor First Floor Rooms**
   - Create `components/rooms/first_floor/zona_1.yaml`
   - Create `components/rooms/first_floor/zona_2.yaml`
   - Update `devices/distribuzione-primo-piano.yaml` to use room components
   - Test both zones work identically to before
   - **Status**: ⏳ Not Started

### 4. **Story 4.4: Documentation, Cleanup, and Template Refinement**
   - Refine room component template based on learnings
   - Create `docs/room-component-guide.md` (how to add new rooms)
   - Update architecture documentation
   - Update copilot instructions
   - Consider deprecating `pid_sensors.yaml` if absorbed into room components
   - **Status**: ⏳ Not Started

---

## Compatibility Requirements

- [x] **Existing functionality preserved**: All temperature control behavior remains identical
- [x] **Entity IDs unchanged**: All Home Assistant entity IDs remain the same (no HA breakage)
- [x] **PID tuning unchanged**: All control parameters remain identical
- [x] **Output control identical**: Same physical relay control patterns
- [x] **Performance impact**: None (purely organizational refactoring)
- [x] **Firmware size**: Negligible impact (might reduce slightly due to better code reuse)

---

## Risk Mitigation

### Primary Risk
**Introduction of errors during refactoring** that break room-specific temperature control.

### Mitigation Strategy

1. **Incremental Refactoring**:
   - Start with single room prototype (Soggiorno)
   - Validate prototype works before proceeding
   - Refactor remaining rooms one at a time
   - Test each room after conversion

2. **Validation Testing**:
   - Compile check after each room conversion
   - Compare generated entity IDs before/after
   - Deploy to test environment before production
   - Monitor each room's temperature control for 24 hours

3. **Preserve Existing Code**:
   - Keep backup of original device files
   - Use git branches for epic work
   - Easy rollback if issues found

4. **Documentation First**:
   - Document room component pattern before implementation
   - Clear vars contract defined upfront
   - Examples provided for team

### Rollback Plan

**Per-Story Rollback:**
- Revert device file changes via git
- Remove new room components
- System returns to functionality-based organization

**Full Epic Rollback:**
- Delete `components/rooms/` directory
- Restore original device files
- System operates exactly as before Epic 4

---

## Definition of Done

This epic is complete when:

- [x] **All 4 stories completed** with acceptance criteria met
- [x] **All rooms converted to room-based components**:
  - Ground floor: Soggiorno, Cucina, Bagno, Anticamera
  - First floor: Zona 1, Zona 2
- [x] **New directory structure created**:
  - `components/rooms/ground_floor/*.yaml`
  - `components/rooms/first_floor/*.yaml`
- [x] **Device files refactored**:
  - `devices/distribuzione-piano-terra.yaml` uses room components
  - `devices/distribuzione-primo-piano.yaml` uses room components
- [x] **Existing functionality verified**:
  - Temperature control accuracy maintained (±0.5°C)
  - PID tuning unchanged and effective
  - Relay control identical to before
  - All entity IDs unchanged in Home Assistant
- [x] **Documentation updated**:
  - Architecture docs reflect room-based organization
  - Room component guide created
  - Copilot instructions updated
- [x] **Production deployment successful**:
  - All boards deployed with room components
  - 7-day monitoring shows stable operation
  - No temperature control regressions

---

## Dependencies and Sequencing

### Epic Dependencies

```
Epic 2 (PID Simplification) ──> COMPLETE ✅
                                    │
                                    └──> Epic 4 (Room Components)
                                              │
                                              └──> Builds on simplified PID pattern

Epic 3 (HA Coordination) ──> Can run in parallel or after Epic 4
```

**Note**: Epic 4 is **independent** from Epic 3. Can proceed in any order or parallel.

### Story Dependencies

```
Story 4.1 (Template + Prototype) ──────────┬──> Story 4.4 (Documentation)
                                            │
Story 4.2 (Ground Floor Rooms) ─────────────┤
                                            │
Story 4.3 (First Floor Rooms) ──────────────┘
```

**Critical Path**: 
- Story 4.1 must complete first (establishes pattern)
- Stories 4.2 and 4.3 can proceed in parallel
- Story 4.4 runs after all implementation complete

---

## Technical Constraints

### ESPHome Constraints

- **Package System**: ESPHome `!include` with `vars` must support room component pattern
- **Substitution Limitations**: Cannot use complex logic in substitutions (keep vars simple)
- **ID Uniqueness**: Room component IDs must be unique per device (handled by `${room_slug}`)
- **YAML Syntax**: Must use valid YAML syntax in templates

### Component Design Constraints

- **Vars Contract**: Room components must define clear, stable vars interface
- **Self-Contained**: Each room component should be independent (no cross-room dependencies)
- **Board Agnostic**: Room components shouldn't assume specific board hardware details
- **Relay Abstraction**: Room component references relay IDs passed as vars (not hardcoded pin numbers)

### Testing Constraints

- **Compilation**: Each refactored device must compile successfully
- **Entity Preservation**: Entity IDs must remain unchanged (validate via generated YAML inspection)
- **Behavioral Equivalence**: Temperature control behavior must be identical before/after

---

## Success Metrics

- **Code Organization**: 6 rooms converted to room-based components
- **File Count**: 6 new room component files created
- **Code Clarity**: Room configuration co-located (single file per room)
- **Maintainability**: Room changes require editing single file (not multiple sections)
- **Reusability**: Room template can instantiate new rooms with vars
- **Documentation**: Clear guide for adding new rooms in future
- **No Regressions**: Zero temperature control issues post-refactoring

---

## Rationale and Benefits

### Why Room-Based Organization?

**Current Pain Points:**
- Adding new room requires editing multiple sections across device file
- Room-specific parameters (PID tuning, setpoints) scattered
- Hard to understand complete room configuration
- Copy-paste errors when adding similar rooms
- Testing individual rooms difficult

**Room-Based Benefits:**
- **Single Source of Truth**: All room config in one file
- **Easy to Add Rooms**: Instantiate template with room-specific vars
- **Easy to Modify Rooms**: Change room behavior in one place
- **Easy to Test Rooms**: Isolate room component for testing
- **Easy to Understand**: Complete room picture visible at once
- **Reduced Errors**: No ID cross-references across distant sections

### Alignment with Epic 2 Simplification

Epic 2 simplified PID architecture by eliminating dual_pid pattern. Epic 4 builds on that simplification by organizing code around **domain concepts (rooms)** rather than **implementation details (PIDs, sensors, outputs)**.

This is a classic **Domain-Driven Design** refactoring:
- **Before**: Implementation-oriented (grouped by technical component type)
- **After**: Domain-oriented (grouped by business concept - rooms)

### Future Extensions Enabled

Room-based architecture enables future enhancements:

1. **Room Profiles**: Different room types (bedroom, bathroom, kitchen) with preset configurations
2. **Room-Specific Features**: Easy to add room-specific sensors, controls, automations
3. **Dynamic Room Addition**: Add rooms via configuration without code changes
4. **Room Testing**: Test rooms in isolation without full system
5. **Multi-Building Support**: Reuse room components across different buildings/floors

---

## Alternative Approaches Considered

### Alternative 1: Keep Functionality-Based (Status Quo)

**Pros:**
- No refactoring effort
- Familiar structure

**Cons:**
- Scaling issues as rooms increase
- Maintenance burden grows
- Code duplication continues

**Decision**: Rejected - pain points will worsen as system grows

### Alternative 2: Hybrid Approach (Partial Room Components)

**Pros:**
- Less disruptive
- Gradual migration

**Cons:**
- Inconsistent architecture
- Confusion about which pattern to use
- Migration never completes

**Decision**: Rejected - clean break is clearer

### Alternative 3: Generic Room Template Only (No Per-Room Files)

```yaml
# All rooms use same template with different vars
packages:
  room_1: !include { file: room_template.yaml, vars: {...} }
  room_2: !include { file: room_template.yaml, vars: {...} }
```

**Pros:**
- Maximum code reuse
- Single template to maintain

**Cons:**
- Room-specific customizations harder
- Less clear what each room does
- All rooms must fit same template

**Decision**: Start with per-room files for flexibility, create template if pattern emerges

---

## Change Log

| Date       | Version | Description  | Author                  |
| ---------- | ------- | ------------ | ----------------------- |
| 2025-10-23 | 1.0     | Epic created | Mary (Business Analyst) |

---

## Notes

### Relationship to Existing Room Components

There are already some room-related components:
- `components/room_ground_floor.yaml`
- `components/room_first_floor.yaml`
- `components/room_sensors.yaml`

**Investigation Needed (Story 4.1):**
- Review existing room components
- Determine if they should be refactored, reused, or replaced
- Maintain backward compatibility if they're actively used

### Room Naming Conventions

**Current Room Names:**
- Ground Floor: Soggiorno, Cucina, Bagno, Anticamera (Italian names)
- First Floor: Zona 1, Zona 2 (Generic zone names)

**Decision**: Preserve existing room names in Epic 4. Room naming standardization is out of scope.

### Fancoil Rooms

Some rooms have fancoil control (not just PID heating). Epic 4 should account for this:
- Create `room_with_fancoil.yaml` template if needed
- Or make fancoil optional in room template via conditional inclusion

**Investigation Needed (Story 4.1):**
- Review fancoil integration requirements
- Design room template that supports both heating-only and heating+cooling rooms

---

## Story Manager Handoff

**This epic is a code organization refactoring that builds on Epic 2 simplification.**

Epic 4 makes the codebase more maintainable by organizing around domain concepts (rooms) rather than implementation details (PIDs, sensors, outputs).

**Key Architectural Decision**: Room components as self-contained units with clear vars contract.

**Risk Level**: Low (purely organizational, no logic changes)  
**Effort**: Small to Medium (mostly moving code, minimal new logic)  
**Value**: High (long-term maintainability, clarity, scalability)

**Recommendation**: 
1. Start Story 4.1 to prototype pattern
2. Validate prototype with stakeholders
3. Proceed with Stories 4.2-4.4 after prototype approval

**Critical Success Factor**: Room component vars interface must be well-designed upfront to avoid rework.

````
