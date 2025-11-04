# Deprecated Components

This directory contains ESPHome component packages that have been deprecated and should not be used in new device configurations.

## Epic 2: PID Architecture Simplification (October 2025)

The following components were deprecated as part of Epic 2, which simplified the PID climate control architecture:

### dual_pid.yaml
**Deprecated:** October 22, 2025  
**Replaced by:** Direct `climate: - platform: pid` with both `heat_output` and `cool_output`  
**Reason:** Unnecessary complexity - ESPHome PID supports both modes natively

### valve_trigger.yaml
**Deprecated:** October 22, 2025  
**Replaced by:** Simple lambda automation based on `climate_mode` sensor  
**Reason:** Physical trigger pattern no longer needed for mode coordination

### mixing_valve.yaml
**Deprecated:** October 22, 2025  
**Replaced by:** Direct PID configuration in device files  
**Reason:** High-level wrapper around deprecated dual_pid pattern

## Epic 5: HA-Only Sensors with Emergency Shutdown (October 2025)

The following components were deprecated as part of Epic 5, which eliminated expensive Modbus sensors in favor of HA-only sensors:

### room_sensors_v4.yaml
**Deprecated:** October 29, 2025  
**Replaced by:** New `components/room_sensors.yaml` (v5)  
**Reason:** Cost reduction - eliminates Modbus RS485 sensors ($640+ hardware savings)

**Key Changes:**
- 3-tier failover (Modbus → HA → Emergency) simplified to 2-tier (HA → Emergency)
- Removed per-room `modbus_controller` definitions
- Removed humidity sensors (not needed for PID control)
- Emergency timeout: 5 min → 3 min (more responsive)
- Added recovery stability check (60s, prevents flapping)
- Code reduction: 220 lines → 211 lines (4% reduction)
- Entity reduction: 7 entities/room → 3 entities/room (57% reduction)

**Migration:**
- See `docs/epic-5-migration-guide.md` for step-by-step migration procedures
- Remove `modbus_controller_address` and `ha_humidity_sensor_id` vars from room component calls
- Update HA dashboards to use `text_sensor.{zone}_sensor_state` instead of `binary_sensor.{zone}_room_sensor_online`

## Epic 8: Unified State Machine Architecture (November 2025)

The following components were deprecated as part of Epic 8, which unified emergency and window detection into a coordinator pattern:

### room_sensors_v5.yaml
**Deprecated:** November 1, 2025  
**Replaced by:** `components/room_emergency_condition.yaml` + temperature sensor abstraction  
**Reason:** Separation of concerns - condition detection vs coordinator control

### room_emergency_shutdown_v5.yaml
**Deprecated:** November 1, 2025  
**Replaced by:** `components/room_emergency_condition.yaml` + `components/room_control_coordinator.yaml`  
**Reason:** Stateless coordinator pattern enables extensibility and eliminates PID control logic duplication

### room_window_detection_v7.yaml
**Deprecated:** November 1, 2025  
**Replaced by:** `components/room_window_condition.yaml` + `components/room_control_coordinator.yaml`  
**Reason:** Unified condition interface contract with priority-based coordination

### emergency_shutdown_v5.yaml
**Deprecated:** November 1, 2025  
**Replaced by:** Epic 8 architecture (condition components + coordinator)  
**Reason:** Old standalone pattern superseded by unified architecture

**Key Changes:**
- Condition components expose state (0/1/2) and priority (1-99) globals
- Coordinator reads all conditions, applies priority hierarchy, forces PID OFF
- Emergency priority: 1 (highest), Window priority: 2
- 40% code reduction through single coordinator vs per-room PID control
- Extensible: Add new conditions (occupancy, schedule) without touching existing code

**Room Files Deprecated:**
All old room configuration files moved to `deprecated/rooms/`:
- Ground floor: soggiorno, cucina, bagno, anticamera, sala_pranzo, locale_tecnico (v5/v7)
- First floor: bagno_grande, bagno_ospiti, bagno_padronale, camera_nord, camera_sud, camera_ospiti, camera_padronale, lavanderia (v5)

**Migration:**
- See `docs/epic-8-migration-strategy.md` for rollout procedures
- Replace Epic 5/7 components with: emergency_condition + window_condition (if fancoil) + coordinator
- Radiant-only rooms: Include `room_window_condition_stub.yaml` for coordinator compatibility
- Update HA automations to monitor `text_sensor.{zone}_coordinator_status` for PID resume logic

## Migration Guides

- **Epic 2:** See `docs/epic-2-migration-guide.md` for PID simplification
- **Epic 5:** See `docs/epic-5-migration-guide.md` for HA-only sensor migration
- **Epic 8:** See `docs/epic-8-migration-strategy.md` for unified state machine architecture

## Reference Purposes Only

These components are retained for:
- Historical reference
- Understanding old device configurations
- Rollback scenarios (if needed)

**Do not use these components in new configurations.**
