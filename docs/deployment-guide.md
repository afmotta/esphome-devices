# ESPHome Climate Control - Deployment Guide

> **Historical document (Gen-1 hardware).** This guide describes deploying the retired
> Gen-1 A6/A16 master/slave topology with Modbus room sensors — hardware replaced by
> ADR-0014 (LilyGO T-Connect Pro + Waveshare Modbus RTU I/O boards, single master, room
> sensors over HA/UDP). Kept as historical record; for the live system see root
> `CLAUDE.md`, `hvac/CLAUDE.md`, and `docs/rs485-wiring-guide.md`.

**Project:** ESPHome Multi-Floor Climate Control - Modbus RTU Enhancement  
**Version:** 1.0  
**Date:** October 22, 2025

This guide provides step-by-step instructions for deploying the Modbus-enhanced ESPHome climate control system from development to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Strategy](#deployment-strategy)
3. [Phase 1: Validation Deployment](#phase-1-validation-deployment-use_modbus-false)
4. [Phase 2: Master Modbus Enabled](#phase-2-master-modbus-enabled)
5. [Phase 3: Full System Modbus](#phase-3-full-system-modbus-enabled)
6. [Phase 4: Room Sensor Hardware](#phase-4-room-sensor-hardware-installation)
7. [Rollback Procedures](#rollback-procedures)
8. [Troubleshooting](#troubleshooting)
9. [Post-Deployment Validation](#post-deployment-validation)

---

## Pre-Deployment Checklist

### Code Readiness

- [ ] All Stories 1.1-1.6 marked complete (software tasks)
- [ ] All firmware compiles without errors or warnings
- [ ] ESPHome validation passes: `esphome config *.yaml`
- [ ] Git repository clean (no uncommitted changes)
- [ ] Documentation reviewed and up-to-date

### Environment Readiness

- [ ] Home Assistant accessible and online
- [ ] ESPHome addon installed in Home Assistant
- [ ] Network connectivity verified (Ethernet/WiFi to all boards)
- [ ] Backup of current firmware for all devices
- [ ] Backup of Home Assistant configuration

### Hardware Readiness

- [ ] All three boards powered and accessible
- [ ] RS485 wiring installed and terminated (120Ω resistors at both ends)
- [ ] Continuity test passed on RS485 A/B lines
- [ ] Modbus room sensors procured (if deploying Story 1.6 hardware)

### Team Readiness

- [ ] Deployment window scheduled (recommend 2-4 hour window)
- [ ] Rollback plan reviewed
- [ ] Monitoring dashboard prepared
- [ ] Emergency contact available if issues arise

---

## Deployment Strategy

**Philosophy:** Gradual rollout with validation at each phase

| Phase | Description                 | Duration   | Risk Level | Rollback Ease |
| ----- | --------------------------- | ---------- | ---------- | ------------- |
| 1     | Validation (use_modbus=off) | 24 hours   | Low        | Easy          |
| 2     | Master Modbus enabled       | 24 hours   | Medium     | Easy          |
| 3     | Full system Modbus          | 24-48 hrs  | Medium     | Moderate      |
| 4     | Room sensor hardware        | As needed  | Low        | Easy          |

**Feature Flag Control:**

All phases use the `use_modbus` substitution to control Modbus functionality:

```yaml
substitutions:
  use_modbus: "false"  # Phase 1
  use_modbus: "true"   # Phases 2-4
```

**Benefits:**
- Infrastructure deployed but inactive initially
- Easy to enable/disable without code changes
- Safe testing of new firmware before Modbus activation

---

## Phase 1: Validation Deployment (use_modbus: false)

**Goal:** Deploy new firmware with Modbus infrastructure present but disabled, verify no regressions

**Duration:** 24 hours monitoring

**Risk Level:** Low (Modbus inactive, system operates exactly as before)

### Step 1.1: Prepare Configuration Files

```bash
# Navigate to project directory
cd ~/esphome-devices

# Ensure all devices have use_modbus: "false"
grep -r "use_modbus" locals/*.yaml

# Expected output:
# locals/gruppo-miscelazione.yaml:  use_modbus: "false"
# locals/distribuzione-piano-terra.yaml:  use_modbus: "false"
# locals/distribuzione-primo-piano.yaml:  use_modbus: "false"
```

### Step 1.2: Compile Firmware

```bash
# Validate all configurations
esphome config locals/gruppo-miscelazione.yaml
esphome config locals/distribuzione-piano-terra.yaml
esphome config locals/distribuzione-primo-piano.yaml

# Compile firmware (without uploading)
esphome compile locals/gruppo-miscelazione.yaml
esphome compile locals/distribuzione-piano-terra.yaml
esphome compile locals/distribuzione-primo-piano.yaml
```

**Check for warnings/errors:**
- No compilation errors
- Firmware size < 1.5 MB (ESP32 partition limit)
- No deprecated component warnings

### Step 1.3: Deploy via OTA (Master First)

```bash
# Deploy to master controller
esphome upload locals/gruppo-miscelazione.yaml

# Monitor logs during deployment
esphome logs locals/gruppo-miscelazione.yaml
```

**Expected log output:**
```
INFO Successfully uploaded program.
INFO Starting log output from gruppo-miscelazione.local
INFO OTA in progress
INFO OTA completed successfully
INFO Rebooting...
INFO Successfully connected to gruppo-miscelazione.local
[I][app:102]: ESPHome version 2024.10.0 compiled on Oct 22 2025, 14:35:42
[I][app:104]: Project esphome-devices version 2.0.0
```

**Verify master functionality:**
- [ ] Master reboots successfully
- [ ] ESPHome API connection to HA established
- [ ] All sensors reporting (Dallas temperature sensors)
- [ ] Mixing valve PIDs operational
- [ ] Climate entities visible in Home Assistant

### Step 1.4: Deploy Slaves

```bash
# Deploy to ground floor slave
esphome upload locals/distribuzione-piano-terra.yaml

# Deploy to first floor slave
esphome upload locals/distribuzione-primo-piano.yaml
```

**Verify slave functionality (both boards):**
- [ ] Slaves reboot successfully
- [ ] ESPHome API connections established
- [ ] Zone relays controllable
- [ ] PID controllers operational
- [ ] Climate entities visible in Home Assistant

### Step 1.5: 24-Hour Monitoring

**Monitor for:**
- Temperature control accuracy (±0.5°C from setpoints)
- No unexpected restarts or crashes
- Memory usage stable (check ESPHome debug sensor)
- No increase in network traffic
- All Home Assistant automations work as before

**Log collection:**
```bash
# Save logs from all devices
esphome logs locals/gruppo-miscelazione.yaml > phase1-master.log &
esphome logs locals/distribuzione-piano-terra.yaml > phase1-slave1.log &
esphome logs locals/distribuzione-primo-piano.yaml > phase1-slave2.log &

# Let run for 24 hours, then analyze logs for errors
```

**Success Criteria:**
- No regressions in existing functionality
- Temperature control maintains ±0.5°C accuracy
- System stable for 24 hours
- Ready to proceed to Phase 2

**If Issues Found:**
- Analyze logs for root cause
- Roll back using [Rollback Procedures](#rollback-procedures)
- Fix issues and restart Phase 1

---

## Phase 2: Master Modbus Enabled

**Goal:** Enable Modbus on master only, verify register updates and slave polling

**Duration:** 24 hours monitoring

**Risk Level:** Medium (Modbus active but not used for control)

### Step 2.1: Enable use_modbus on Master

```yaml
# Edit locals/gruppo-miscelazione.yaml
substitutions:
  use_modbus: "true"  # ← Change from "false"
```

### Step 2.2: Compile and Deploy Master

```bash
esphome compile locals/gruppo-miscelazione.yaml
esphome upload locals/gruppo-miscelazione.yaml
esphome logs locals/gruppo-miscelazione.yaml
```

**Expected log output:**
```
[I][modbus_master:123]: Modbus RTU enabled on UART1
[I][modbus_master:145]: Starting polling cycle
[D][modbus_master:201]: Polling slave address 0x02
[D][modbus_master:234]: Writing to holding register 100: 2345 (23.45°C)
[D][modbus_master:234]: Writing to holding register 200: 1 (heat mode)
[D][modbus_master:234]: Writing to holding register 300: 42 (heartbeat)
```

### Step 2.3: Verify Master Register Updates

**Check Home Assistant Entities:**

The master should expose diagnostic sensors for register values:

- `sensor.gruppo_miscelazione_register_100` → Supply temperature (scaled ×100)
- `sensor.gruppo_miscelazione_register_200` → Climate mode (0=off, 1=heat, 2=cool)
- `sensor.gruppo_miscelazione_register_300` → Heartbeat counter

**Verify in Home Assistant Developer Tools:**
1. Go to Developer Tools → States
2. Find entities starting with `sensor.gruppo_miscelazione_register_`
3. Verify values update every 10 seconds
4. Heartbeat should increment: 0 → 1 → 2 → ...

### Step 2.4: Verify Slave Can Read Master Registers

**Note:** Slaves still have `use_modbus: "false"` but can still poll master

Check slave logs for Modbus communication (even if not using data):

```bash
esphome logs locals/distribuzione-piano-terra.yaml
```

Expected slave log output:
```
[D][modbus_controller:189]: Read from master register 100: 2345 (23.45°C)
[D][modbus_controller:189]: Read from master register 200: 1 (heat)
[D][modbus_controller:189]: Read from master register 300: 42
```

**If slaves show Modbus errors:**
- Check RS485 wiring (A/B not reversed)
- Verify termination resistors installed
- Check baud rate matches (9600 baud on all devices)

### Step 2.5: 24-Hour Monitoring

**Monitor for:**
- Master heartbeat increments correctly
- Register values update every 10 seconds
- Slaves can read master registers (check logs)
- No Modbus communication errors (CRC failures)
- Existing temperature control unaffected

**Success Criteria:**
- Master writes registers successfully
- Slaves read registers successfully
- Modbus error rate < 1%
- System stable for 24 hours
- Ready to proceed to Phase 3

---

## Phase 3: Full System Modbus Enabled

**Goal:** Enable Modbus on slaves, PIDs use Modbus sensor data for control

**Duration:** 24-48 hours monitoring

**Risk Level:** Medium (Control now uses Modbus data)

### Step 3.1: Enable use_modbus on Slaves

```yaml
# Edit locals/distribuzione-piano-terra.yaml
substitutions:
  use_modbus: "true"  # ← Change from "false"

# Edit locals/distribuzione-primo-piano.yaml
substitutions:
  use_modbus: "true"  # ← Change from "false"
```

### Step 3.2: Deploy Slaves

```bash
# Deploy ground floor slave
esphome upload locals/distribuzione-piano-terra.yaml

# Deploy first floor slave
esphome upload locals/distribuzione-primo-piano.yaml
```

### Step 3.3: Verify PID Controllers Use Modbus Data

**Check Home Assistant Climate Entities:**

Each zone climate entity should show:
- Current temperature from Modbus sensor (not HA sensor)
- Temperature updates every 10 seconds (aligned with Modbus polling)

**Verify in Logs:**
```bash
esphome logs locals/distribuzione-piano-terra.yaml
```

Expected output:
```
[D][climate:234]: Soggiorno Floor Heat PID:
[D][climate:237]:   Current Temperature: 22.45°C (from Modbus)
[D][climate:240]:   Target Temperature: 23.00°C
[D][climate:243]:   Action: HEATING
[D][pid:123]: PID Control Output: 45.2% (kp=0.8, ki=0.005, kd=0.05)
```

### Step 3.4: Test Failover Logic

**Test 1: Simulate Modbus Failure**

1. Temporarily disconnect RS485 cable (A or B line)
2. Wait 30 seconds (Modbus timeout)
3. Check Home Assistant: Climate entities should show temperature from HA sensor fallback
4. Reconnect RS485 cable
5. Verify automatic recovery to Modbus sensor

**Expected failover logs:**
```
[W][sensor_failover:234]: Modbus sensor timeout, switching to HA sensor
[I][text_sensor:089]: Temperature Source: Home Assistant Fallback
[I][sensor_failover:256]: Modbus sensor recovered, switching back
[I][text_sensor:089]: Temperature Source: Local Modbus Sensor
```

**Test 2: Simulate Home Assistant Offline**

1. Stop Home Assistant (or disconnect network)
2. Verify climate control continues using Modbus sensors
3. Verify no emergency shutdown (system autonomous)
4. Restart Home Assistant
5. Verify ESPHome API reconnects

### Step 3.5: 24-48 Hour Stability Test

**Monitoring Metrics:**

| Metric                       | Target      | How to Measure                        |
| ---------------------------- | ----------- | ------------------------------------- |
| Temperature Control Accuracy | ±0.5°C      | Home Assistant history graphs         |
| Modbus Communication Errors  | <1%         | Check error counters in HA            |
| PID Stability                | No oscill.  | Monitor climate entity history        |
| Failover Events              | 0 (stable)  | Check failover status text sensors    |
| CPU Usage                    | <15%        | ESPHome debug sensor                  |
| Memory Free                  | >100 KB     | ESPHome debug sensor                  |

**Data Collection:**
```bash
# Export Home Assistant data for analysis
# Developer Tools → Statistics → Export to CSV
# Entities: temperature sensors, climate entities, diagnostic sensors
```

**Success Criteria:**
- All zones maintain temperature ±0.5°C
- No unexpected failover events
- Modbus error rate < 1%
- System stable for 24-48 hours
- Ready to proceed to Phase 4 (optional)

---

## Phase 4: Room Sensor Hardware Installation

**Goal:** Install Modbus room sensors for ground floor zones

**Duration:** Depends on installation complexity

**Risk Level:** Low (Room sensors additive, supply temp fallback available)

**Note:** This phase requires physical hardware (XY-MD02 or AM2301-MB sensors). Can be skipped if room sensors not yet procured.

### Step 4.1: Configure Sensor Addresses (Bench Test)

Before installation, configure each sensor's Modbus address:

| Sensor | Location   | Modbus Address | DIP Switch Config   |
| ------ | ---------- | -------------- | ------------------- |
| 1      | Soggiorno  | 10 (0x0A)      | Consult sensor manual |
| 2      | Cucina     | 11 (0x0B)      | Consult sensor manual |
| 3      | Bagno      | 12 (0x0C)      | Consult sensor manual |
| 4      | Anticamera | 13 (0x0D)      | Consult sensor manual |

**Bench Test Procedure:**
1. Connect sensor to RS485 bus (master only, no slaves)
2. Power sensor (12-24V DC)
3. Verify master can poll sensor:
   ```
   [D][modbus_master:234]: Polling sensor address 10
   [D][modbus_master:267]: Temperature: 2245 (22.45°C)
   [D][modbus_master:270]: Humidity: 653 (65.3% RH)
   ```
4. Repeat for all 4 sensors
5. Label sensors with location and address

### Step 4.2: Install Sensors in Rooms

**Installation Guidelines:**

- **Location:** Center of room, 1.5m height, away from heat sources
- **Avoid:** Direct sunlight, near windows, near HVAC vents, behind furniture
- **Wiring:** Run RS485 cable from sensor to nearest junction point
- **Daisy-chain:** All sensors share common A/B bus (no star topology)

**Wiring Diagram:**
```
Master --> Slave 1 --> Slave 2 --> Sensor 1 --> Sensor 2 --> Sensor 3 --> Sensor 4 --> [120Ω Term]
[120Ω Term]                                                                              
```

### Step 4.3: Enable Room Sensor Polling

Enable room sensor polling in master configuration:

```yaml
# In locals/gruppo-miscelazione.yaml
# Ensure modbus_room_sensor_poller package is included
packages:
  modbus_room_sensor_poller: !include
    file: ../components/modbus_room_sensor_poller.yaml
```

Deploy updated master firmware:
```bash
esphome upload locals/gruppo-miscelazione.yaml
```

**Verify master polls all 4 sensors:**
```bash
esphome logs locals/gruppo-miscelazione.yaml
```

Expected output:
```
[D][modbus_master:234]: Polling sensor address 10 (Soggiorno)
[D][modbus_master:267]: Temperature: 2245, Humidity: 653
[D][modbus_master:234]: Polling sensor address 11 (Cucina)
[D][modbus_master:267]: Temperature: 2310, Humidity: 582
[D][modbus_master:234]: Polling sensor address 12 (Bagno)
[D][modbus_master:267]: Temperature: 2420, Humidity: 725
[D][modbus_master:234]: Polling sensor address 13 (Anticamera)
[D][modbus_master:267]: Temperature: 2180, Humidity: 601
[I][modbus_master:289]: Room sensors online: 4/4
```

### Step 4.4: Update Slaves to Use Room Sensors

Slaves automatically read room sensor data from master registers 400-407. Verify PIDs now use room temperature:

```bash
esphome logs locals/distribuzione-piano-terra.yaml
```

Expected output:
```
[D][climate:234]: Soggiorno Floor Heat PID:
[D][climate:237]:   Current Temperature: 22.45°C (from Room Sensor via Modbus)
[I][text_sensor:089]: Temperature Source: Local Room Sensor (Modbus)
```

### Step 4.5: Calibration and Tuning

**Temperature Calibration:**
1. Compare room sensors to reference thermometer (±0.1°C accuracy)
2. If offset needed, add filter to sensor configuration:
   ```yaml
   filters:
     - offset: -0.3  # Subtract 0.3°C if sensor reads high
   ```

**PID Retuning:**

Room temperature responds slower than supply temperature. Monitor PID behavior:

- **Oscillation:** Reduce `kp` (proportional gain)
- **Slow Response:** Increase `kp` or `ki` (integral gain)
- **Overshoot:** Increase `kd` (derivative gain)

Starting PID parameters (from Story 1.6):
```yaml
control_parameters:
  kp: 0.8
  ki: 0.005
  kd: 0.05
```

Tune incrementally and monitor for 24 hours after each change.

**Success Criteria:**
- All 4 room sensors online and reporting
- PID controllers use room temperature
- Temperature control accuracy maintained (±0.5°C)
- No oscillation or instability
- 24-hour stability test passes

---

## Rollback Procedures

### Scenario 1: Phase 1 Issues (Firmware Regression)

**Symptoms:** New firmware causes crashes, sensor failures, or control issues

**Rollback Procedure:**
1. Flash previous firmware via OTA:
   ```bash
   esphome upload --device [device-ip] previous-backup/device.yaml
   ```
2. Monitor logs to verify rollback successful
3. Investigate root cause before re-attempting deployment

**Alternative:** Use Home Assistant ESPHome addon:
1. Go to ESPHome addon
2. Select device
3. Click "Install" → "Install from Backup"
4. Select previous firmware version

### Scenario 2: Phase 2/3 Issues (Modbus Communication Failure)

**Symptoms:** Modbus errors, slaves not reading master, temperature control degraded

**Quick Fix:** Disable Modbus without reflashing
1. Edit `locals/secrets.yaml`:
   ```yaml
   use_modbus: "false"
   ```
2. OTA update all devices:
   ```bash
   esphome upload locals/*.yaml
   ```
3. System reverts to Home Assistant-dependent mode (proven stable)

**Root Cause Investigation:**
- Check RS485 wiring (A/B not reversed, termination resistors)
- Review Modbus logs for CRC errors or timeouts
- Verify baud rate matches on all devices
- Test RS485 bus with multimeter (resistance check)

### Scenario 3: Phase 4 Issues (Room Sensor Installation)

**Symptoms:** Room sensors not responding, incorrect readings, PID instability

**Quick Fix:** Disable room sensor usage
1. In slave configuration, revert PID sensor to supply temperature:
   ```yaml
   # Change from:
   sensor: soggiorno_room_temp_abstracted
   # Back to:
   sensor: dallas_supply_temp_soggiorno
   ```
2. OTA update affected slave
3. System reverts to supply temperature control (Story 1.5 state)

**Hardware Debugging:**
- Test sensors individually on bench
- Verify sensor addresses configured correctly
- Check RS485 wiring to sensors
- Verify sensor power supply (12-24V DC)

### Emergency Rollback (Complete System Failure)

**If OTA not possible (device offline):**

1. **Physical Access Required:** Connect USB cable to ESP32 board
2. Flash previous firmware via USB:
   ```bash
   esphome upload --device /dev/ttyUSB0 previous-backup/device.yaml
   ```
3. Verify device boots and connects to network
4. Investigate root cause before re-attempting OTA deployment

**Prevention:**
- Always maintain working backup firmware files
- Test firmware compilation before deployment
- Deploy during low-criticality hours (spring/fall when heating/cooling less critical)
- Have physical access available during initial deployment

---

## Troubleshooting

### Issue: OTA Upload Fails

**Symptoms:**
```
ERROR Cannot connect to device-name.local
ERROR OTA upload failed
```

**Solutions:**
1. Verify device is powered and online
2. Check network connectivity (ping device IP)
3. Try uploading via IP address instead of mDNS:
   ```bash
   esphome upload --device 192.168.1.100 locals/device.yaml
   ```
4. If persistent, use USB upload as fallback

### Issue: Home Assistant Can't Discover Devices

**Symptoms:** ESPHome devices missing from Home Assistant integrations

**Solutions:**
1. Check ESPHome API connection in device logs:
   ```
   [I][api:102]: Successfully connected to Home Assistant API
   ```
2. Verify ESPHome integration installed in HA
3. Manually add device: Settings → Devices & Services → Add Integration → ESPHome → Enter device IP
4. Restart Home Assistant if devices still missing

### Issue: High Modbus Error Rate (>5%)

**Symptoms:** Logs show frequent CRC check failures or read timeouts

**Solutions:**
1. Check RS485 wiring quality (twisted pair, shielded)
2. Verify termination resistors installed at both bus ends
3. Reduce cable length if possible (test with short cable)
4. Add delay between Modbus operations (increase `send_wait_time`)
5. Check for electromagnetic interference sources

### Issue: PID Controllers Oscillating After Room Sensor Installation

**Symptoms:** Temperature swings ±1-2°C around setpoint

**Solutions:**
1. Reduce `kp` (proportional gain) by 50%: 0.8 → 0.4
2. Reduce `ki` (integral gain) by 50%: 0.005 → 0.0025
3. Monitor for 2-4 hours, adjust incrementally
4. Consider increasing `kd` (derivative gain) for damping: 0.05 → 0.1
5. Document final PID parameters in Story 1.6 completion notes

---

## Post-Deployment Validation

### Final Checklist

- [ ] All three devices online and reporting to Home Assistant
- [ ] All climate entities controllable from HA dashboard
- [ ] Temperature control accuracy ±0.5°C (24-hour average)
- [ ] Modbus communication error rate <1%
- [ ] No unexpected failover events during stable operation
- [ ] PID controllers stable (no oscillation)
- [ ] Room sensors online and reporting (if installed)
- [ ] System autonomous (test by stopping Home Assistant briefly)

### Performance Metrics Documentation

Record final metrics for Story 1.7 completion:

| Metric                       | Target      | Actual      | Status |
| ---------------------------- | ----------- | ----------- | ------ |
| Firmware Size (A6)           | <1.5 MB     | _____ MB    | ☐      |
| Firmware Size (A16)          | <1.5 MB     | _____ MB    | ☐      |
| CPU Usage (idle)             | <10%        | _____%      | ☐      |
| CPU Usage (polling)          | <15%        | _____%      | ☐      |
| Memory Free                  | >100 KB     | _____ KB    | ☐      |
| Modbus Polling Cycle         | <500ms      | _____ ms    | ☐      |
| Temperature Control Accuracy | ±0.5°C      | ±____ °C    | ☐      |
| Modbus Error Rate            | <1%         | _____%      | ☐      |
| Failover Transition Time     | <30s        | _____ s     | ☐      |

### Long-Term Monitoring Plan

**Weekly Checks:**
- Review Home Assistant history graphs for temperature stability
- Check Modbus error counters (should remain low)
- Verify no unexpected restarts or crashes

**Monthly Checks:**
- Review ESPHome logs for warnings or errors
- Verify room sensor calibration still accurate
- Check PID performance (adjust tuning if needed)

**Quarterly Maintenance:**
- Backup all device configurations
- Update ESPHome to latest stable version (test in dev first)
- Review and update documentation as needed

---

## Success Metrics

**Deployment considered successful when:**

1. ✅ All phases completed without requiring rollback
2. ✅ System runs autonomously (Home Assistant optional)
3. ✅ Temperature control accuracy maintained (±0.5°C)
4. ✅ Modbus communication reliable (<1% error rate)
5. ✅ Failover tested and functional
6. ✅ 24-hour stability test passed (all phases)
7. ✅ Documentation complete and accurate
8. ✅ Team trained on monitoring and maintenance

---

## References

- **Architecture Documentation:** `docs/architecture.md`
- **Architecture Diagrams:** `docs/architecture-diagram.md`
- **Modbus Register Map:** `docs/modbus-register-map.md`
- **RS485 Wiring Guide:** `docs/rs485-wiring-guide.md`
- **Sensor Technology Selection:** `docs/sensor-technology-selection.md`

---

**Version History:**

| Date       | Version | Changes                           | Author            |
| ---------- | ------- | --------------------------------- | ----------------- |
| 2025-10-22 | 1.0     | Initial deployment guide (Story 1.7) | James (Dev Agent) |
