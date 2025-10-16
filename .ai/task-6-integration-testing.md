# Task 6: Integration Verification Testing Guide

## Overview
This document provides step-by-step instructions for verifying that the Modbus infrastructure additions do not affect existing system functionality.

## Prerequisites
- Both devices online and accessible via Home Assistant
- USB serial cable available for emergency recovery
- Access to Home Assistant dashboard

## Phase 1: Pre-Deployment Validation (use_modbus: "false")

### ✅ Test 1.1: Firmware Compilation - COMPLETED
- Master (gruppo-miscelazione): RAM 10.8%, Flash 50.3%
- Slave (distribuzione-piano-terra): RAM 11.0%, Flash 50.3%

### ⏳ Test 1.2: OTA Update with Modbus Disabled - REQUIRES HARDWARE
**Steps:**
1. Ensure `use_modbus: "false"` in both configs
2. OTA update master: `esphome run locals/gruppo-miscelazione.yaml`
3. OTA update slave: `esphome run locals/gruppo-distribuzione.yaml`

**Expected:** Both devices update successfully and reconnect to HA

### ⏳ Test 1.3: PID Controls - REQUIRES HARDWARE
Verify climate entities respond correctly:
- `climate.pid_piano_terra_heat/cool`
- `climate.pid_primo_piano_heat/cool`

### ⏳ Test 1.4: Dallas Sensors - REQUIRES HARDWARE
Check both sensors report temperature:
- `dallas_0x81000000b3e6f628`
- `dallas_0xe9000000b366ed28`

### ⏳ Test 1.5-1.8: Relay, Inputs, WiFi, I2C - REQUIRES HARDWARE
Verify all peripheral functions unchanged

## Phase 2: Modbus Activation (use_modbus: "true")

### ⏳ Test 2.1: Enable Modbus - REQUIRES HARDWARE
1. Set `use_modbus: "true"` in both device files
2. OTA update both devices
3. Verify new diagnostic sensors appear in HA:
   - `sensor.modbus_master_status`
   - `sensor.modbus_communication_errors`
   - `sensor.slave_test_register_value`

### ⏳ Test 2.2: Modbus Communication - REQUIRES HARDWARE
Monitor logs: `esphome logs locals/gruppo-miscelazione.yaml`
Verify master reads test register from slave

## Rollback Procedure
If issues occur:
1. Set `use_modbus: "false"`
2. OTA update devices
3. Or flash via USB if needed

## Current Status
**Tasks 1-5:** ✅ COMPLETED (configuration, compilation, sizing)
**Task 6:** ⏳ READY FOR HARDWARE TESTING

