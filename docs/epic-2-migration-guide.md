# Epic 2: PID Architecture Simplification - Migration Guide

**Document Version:** 1.0  
**Epic Completion Date:** October 22, 2025  
**Authors:** Development Team (Stories 2.1, 2.2, 2.3)

---

## Overview

Epic 2 simplified the ESPHome PID climate control architecture by eliminating the `dual_pid.yaml` pattern that created two separate climate entities (heat/cool) per zone. The new pattern uses ESPHome's native PID platform with both `heat_output` and `cool_output` configured on a single climate entity.

**Impact:**
- Climate entities reduced: 16 → 8 (50% reduction)
- Components removed: 3 files (`dual_pid.yaml`, `valve_trigger.yaml`, `mixing_valve.yaml`)
- Code complexity: Significantly reduced
- Functionality: Unchanged - all PID tuning and behavior preserved

---

## Rationale for Simplification

### The Problem with Dual PID Pattern

The original architecture created **two separate PID climate entities** per control zone which introduced unnecessary complexity:

1. **Redundant Entities**: Two climate entities when one could handle both modes
2. **Complex Coordination**: Required external automation for mode switching
3. **Same Physical Output**: Both PIDs controlled the same DAC/relay
4. **HA Dashboard Bloat**: Double the entities to manage

### Why ESPHome Native PID is Better

ESPHome's `climate: platform: pid` supports **both heating and cooling natively**:

```yaml
climate:
  - platform: pid
    id: pid_piano_terra
    name: "PID Piano Terra"
    sensor: dallas_0x81000000b3e6f628
    heat_output: dac_1
    cool_output: dac_1  # Same output, different action ranges
```

---

## Before and After Architecture

### Before Epic 2

```yaml
packages:
  mixing_valve_piano_terra: !include
    file: ../components/mixing_valve.yaml
    vars:
      circuit_name: "Piano Terra"
      # ... many vars required
```

**Result:** Creates 2 entities: `climate.pid_piano_terra_heat`, `climate.pid_piano_terra_cool`

### After Epic 2

```yaml
climate:
  - platform: pid
    id: pid_piano_terra
    name: "PID Piano Terra"
    sensor: dallas_0x81000000b3e6f628
    heat_output: dac_1
    cool_output: dac_1
```

**Result:** Creates 1 entity: `climate.pid_piano_terra`

---

## Component Pattern Changes

| Old Component | Status | Replacement |
|--------------|--------|-------------|
| `dual_pid.yaml` | **DEPRECATED** | Direct `climate: platform: pid` with both outputs |
| `valve_trigger.yaml` | **DEPRECATED** | Lambda automation based on `climate_mode` sensor |
| `mixing_valve.yaml` | **DEPRECATED** | Direct PID configuration in device file |

**Location of deprecated components:** `components/deprecated/` (for reference only)

---

## Entity ID Migration for Home Assistant

### Mixing Valves

- **Piano Terra**: `climate.pid_piano_terra_heat/cool` → `climate.pid_piano_terra`
- **Primo Piano**: `climate.pid_primo_piano_heat/cool` → `climate.pid_primo_piano`

### Distribution Zones - Ground Floor

- **Soggiorno**: `climate.pid_soggiorno_heat/cool` → `climate.pid_soggiorno`
- **Cucina**: `climate.pid_cucina_heat/cool` → `climate.pid_cucina`
- **Bagno**: `climate.pid_bagno_heat/cool` → `climate.pid_bagno`
- **Anticamera**: `climate.pid_anticamera_heat/cool` → `climate.pid_anticamera`

### Distribution Zones - First Floor

- **Zona 1**: `climate.pid_primo_piano_zona_1_heat/cool` → `climate.pid_primo_piano_zona_1`
- **Zona 2**: `climate.pid_primo_piano_zona_2_heat/cool` → `climate.pid_primo_piano_zona_2`

---

## Step-by-Step Migration Example

### Example: Converting a Single Zone

#### 1. Old Configuration (dual_pid)

```yaml
packages:
  dual_pid_soggiorno: !include
    file: ../components/dual_pid.yaml
    vars:
      circuit_slug: "soggiorno"
      sensor: temperature_failover
      output: slow_pwm_soggiorno
      heat_kp: 0.8
      heat_ki: 0.005
      heat_kd: 0.05
```

#### 2. New Configuration (single PID)

```yaml
climate:
  - platform: pid
    id: pid_soggiorno
    name: "PID Soggiorno"
    sensor: temperature_failover
    default_target_temperature: 20°C
    heat_output: slow_pwm_soggiorno
    cool_output: slow_pwm_soggiorno
    control_parameters:
      kp: 0.8
      ki: 0.005
      kd: 0.05
```

#### 3. Add Mode Coordination

```yaml
sensor:
  - platform: homeassistant
    id: climate_mode
    entity_id: sensor.thermostat_mode
    on_value:
      - lambda: |-
          if (id(climate_mode).state == "heat") {
            auto call = id(pid_soggiorno).make_call();
            call.set_mode(CLIMATE_MODE_HEAT);
            call.perform();
          } else if (id(climate_mode).state == "cool") {
            auto call = id(pid_soggiorno).make_call();
            call.set_mode(CLIMATE_MODE_COOL);
            call.perform();
          }
```

#### 4. Update Home Assistant

1. Flash updated configuration to device
2. Restart Home Assistant to clear old entities
3. Update dashboards to use new single entity ID
4. Update automations to reference new entity ID
5. Test heating and cooling modes

---

## Lessons Learned

### What Went Well

1. **ESPHome Native Features Sufficient**: Native PID supported everything needed
2. **Incremental Migration**: Story-by-story approach minimized risk
3. **PID Tuning Preserved**: All tuning parameters successfully transferred
4. **Entity Count Reduction**: Cleaner HA dashboards

### Key Takeaways

1. **Question Complexity Early**: If pattern seems complex, investigate simpler alternatives
2. **Use Platform Features**: Prefer native ESPHome features over custom components
3. **Document Deprecation**: Move old components to `deprecated/` with clear explanations
4. **Migration Guide Essential**: Future developers need clear migration path

---

## Future Guidance

### When Creating New Climate Control Components

**DO:**
- ✅ Use native ESPHome `climate: platform: pid` with both outputs
- ✅ Keep component structure simple and reusable
- ✅ Test both heating and cooling modes thoroughly
- ✅ Use standard climate.control actions for automation

**DON'T:**
- ❌ Create separate entities for heat/cool modes
- ❌ Build custom coordination logic when native features exist
- ❌ Duplicate PID entities controlling same output
- ❌ Skip documentation of component behavior

---

## Rollback Procedures

### Emergency Rollback (Per Device)

1. **Restore Old Configuration:**
   ```bash
   git checkout <commit-before-epic-2> devices/gruppo-miscelazione.yaml
   ```

2. **Restore Deprecated Components:**
   ```bash
   cp components/deprecated/*.yaml components/
   ```

3. **Recompile and Flash:**
   ```bash
   esphome compile devices/gruppo-miscelazione.yaml
   esphome upload devices/gruppo-miscelazione.yaml
   ```

4. **Restart Home Assistant** to detect old entities

---

## Troubleshooting

### Climate Entity Not Responding to Mode Changes

**Solution:**
```yaml
# Verify climate_mode sensor is updating
sensor:
  - platform: homeassistant
    id: climate_mode
    entity_id: sensor.thermostat_mode
    on_value:
      - logger.log:
          format: "Climate mode changed to: %s"
          args: [ 'id(climate_mode).state.c_str()' ]
```

### Old Entities Still Showing in Home Assistant

**Solution:**
1. Ensure old configuration is removed from device
2. Flash updated config to device
3. Restart Home Assistant completely
4. Check Configuration → Entities for orphaned entities
5. Remove unavailable entities manually

### PID Not Controlling Output

**Solution:**
```yaml
# Verify output IDs match
climate:
  - platform: pid
    heat_output: slow_pwm_soggiorno  # Must match output: id below

output:
  - platform: slow_pwm
    id: slow_pwm_soggiorno  # Must match climate heat_output/cool_output
```

---

## Document History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | Oct 22, 2025 | Initial migration guide | James (Dev Agent) |

---

**For complete technical details, see:**
- `docs/epic-2-pid-architecture-simplification.md` - Epic overview
- `components/deprecated/README.md` - Deprecation rationale
- `docs/architecture.md` - Current architecture patterns
