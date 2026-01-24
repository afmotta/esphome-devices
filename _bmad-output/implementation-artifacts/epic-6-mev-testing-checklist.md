# Epic 6: MEV Testing Checklist

**Board:** KC868-A6 ESPHome  
**Device:** MEV Primo Piano  
**Version:** 1.0  
**Date:** October 30, 2025

---

## Overview

This checklist provides a systematic approach to testing the MEV board before, during, and after installation. Follow all steps in order to ensure reliable operation.

---

## Pre-Installation Testing (Bench Test)

Complete these tests BEFORE connecting to the MEV unit.

### Setup Required
- [ ] KC868-A6 board
- [ ] 12V DC power supply (min 1A)
- [ ] Multimeter (with voltage and continuity modes)
- [ ] Home Assistant instance accessible
- [ ] WiFi network available

---

### Test 1: Power and Connectivity

**Objective:** Verify board powers on and connects to network

**Steps:**
1. [ ] Connect 12V power supply to KC868-A6 (verify polarity!)
2. [ ] Observe board LED (should illuminate)
3. [ ] Wait 30 seconds for boot sequence
4. [ ] Check WiFi router for device: `mev-primo-piano`
5. [ ] Open Home Assistant → Settings → Devices → ESPHome
6. [ ] Verify device "MEV Primo Piano" appears
7. [ ] Check device shows "Online" status

**Pass Criteria:**
- ✅ Board LED on
- ✅ Device visible on network
- ✅ Home Assistant shows online

**Troubleshooting:**
- LED off → Check power supply polarity and voltage
- Not on network → Verify WiFi credentials in `locals/secrets.yaml`
- Not in HA → Try adding integration manually

---

### Test 2: Entity Visibility

**Objective:** Confirm all 6 MEV entities are exposed

**Steps:**
1. [ ] Open Home Assistant → Settings → Devices → MEV Primo Piano
2. [ ] Verify the following entities exist:
   - [ ] `switch.mev_primo_piano_power`
   - [ ] `switch.mev_primo_piano_mode`
   - [ ] `switch.mev_primo_piano_dehumidifier`
   - [ ] `switch.mev_primo_piano_cooling`
   - [ ] `number.mev_primo_piano_fan_speed`
   - [ ] `binary_sensor.mev_primo_piano_alarm`
3. [ ] Verify all entities show current states (not "unavailable")

**Pass Criteria:**
- ✅ All 6 entities present
- ✅ No "unavailable" states

**Troubleshooting:**
- Missing entities → Check ESPHome compilation logs
- Unavailable → Restart Home Assistant, check ESPHome device logs

---

### Test 3: Relay Operation

**Objective:** Verify all 4 relays toggle correctly

**Equipment:** Multimeter in continuity mode

**For Each Relay (1-4):**

#### Relay 1 (Power)
1. [ ] Set multimeter to continuity mode
2. [ ] Connect probes to RELAY1 COM and NO terminals
3. [ ] Verify open circuit (no continuity) when relay OFF
4. [ ] Turn on switch in HA: `switch.mev_primo_piano_power`
5. [ ] Verify closed circuit (continuity beep) when relay ON
6. [ ] Turn off switch in HA
7. [ ] Verify returns to open circuit
8. [ ] **Result:** PASS / FAIL

#### Relay 2 (Mode)
1. [ ] Connect probes to RELAY2 COM and NO terminals
2. [ ] Verify open circuit when relay OFF
3. [ ] Turn on switch in HA: `switch.mev_primo_piano_mode`
4. [ ] Verify closed circuit when relay ON
5. [ ] Turn off switch in HA
6. [ ] Verify returns to open circuit
7. [ ] **Result:** PASS / FAIL

#### Relay 3 (Dehumidifier)
1. [ ] Connect probes to RELAY3 COM and NO terminals
2. [ ] Verify open circuit when relay OFF
3. [ ] Turn on switch in HA: `switch.mev_primo_piano_dehumidifier`
4. [ ] Verify closed circuit when relay ON
5. [ ] Turn off switch in HA
6. [ ] Verify returns to open circuit
7. [ ] **Result:** PASS / FAIL

#### Relay 4 (Cooling)
1. [ ] Connect probes to RELAY4 COM and NO terminals
2. [ ] Verify open circuit when relay OFF
3. [ ] Turn on switch in HA: `switch.mev_primo_piano_cooling`
4. [ ] Verify closed circuit when relay ON
5. [ ] Turn off switch in HA
6. [ ] Verify returns to open circuit
7. [ ] **Result:** PASS / FAIL

**Pass Criteria:**
- ✅ All 4 relays toggle correctly
- ✅ HA switch state matches physical relay state
- ✅ No stuck or inverted relays

**Troubleshooting:**
- Relay always open → Check PCF8574 connections, verify I2C communication
- Relay always closed → May be stuck, check relay module
- Inverted behavior → Software expects active-low, may need adjustment

---

### Test 4: DAC Output (0-10V Fan Speed)

**Objective:** Verify 0-10V output scales linearly with fan speed percentage

**Equipment:** Multimeter in DC voltage mode

**Steps:**
1. [ ] Set multimeter to DC voltage mode (20V range)
2. [ ] Connect RED probe to DAC1(+) terminal
3. [ ] Connect BLACK probe to GND(-) terminal

**Test Points:**

| Fan Speed % | Expected Voltage | Measured Voltage | Pass/Fail |
|-------------|------------------|------------------|-----------|
| 0%          | ~0.0V            | ________V        | [ ]       |
| 10%         | ~1.0V            | ________V        | [ ]       |
| 25%         | ~2.5V            | ________V        | [ ]       |
| 50%         | ~5.0V            | ________V        | [ ]       |
| 75%         | ~7.5V            | ________V        | [ ]       |
| 100%        | ~10.0V           | ________V        | [ ]       |

**Procedure for each test point:**
1. [ ] Set fan speed in HA: `number.mev_primo_piano_fan_speed` → [value]
2. [ ] Wait 2 seconds for DAC to stabilize
3. [ ] Read voltage on multimeter
4. [ ] Record in table above
5. [ ] Verify voltage is within ±0.3V of expected

**Pass Criteria:**
- ✅ All measurements within ±0.3V of expected
- ✅ Linear relationship (no sudden jumps)
- ✅ Voltage adjusts within 1 second of command

**Troubleshooting:**
- No voltage change → Check DAC pin configuration (GPIO26)
- Voltage stuck at 3.3V → DAC not configured for 0-10V mode
- Non-linear response → Software calibration issue
- Noisy/fluctuating → Add capacitor across DAC output (10µF recommended)

---

### Test 5: Alarm Input

**Objective:** Verify alarm binary sensor responds to input state

**Equipment:** Jumper wire

**Steps:**
1. [ ] Monitor alarm sensor in HA: `binary_sensor.mev_primo_piano_alarm`
2. [ ] Verify initial state is "Clear" (OFF) with input open
3. [ ] Use jumper wire to short INPUT1(+) to GND(-)
4. [ ] Verify HA sensor changes to "Problem" (ON) within 2 seconds
5. [ ] Remove jumper wire (open circuit)
6. [ ] Verify HA sensor returns to "Clear" (OFF) within 2 seconds

**Test Results:**

| Condition         | Expected State | Actual State | Pass/Fail |
|-------------------|----------------|--------------|-----------|
| Input OPEN        | Clear (OFF)    | _________    | [ ]       |
| Input CLOSED (shorted) | Problem (ON) | _________ | [ ]       |
| Input OPEN again  | Clear (OFF)    | _________    | [ ]       |

**Pass Criteria:**
- ✅ Sensor responds to input state changes
- ✅ State updates within 2 seconds
- ✅ Logic is correct (closed = problem)

**Troubleshooting:**
- Always "Problem" → Input may be shorted, check wiring
- Always "Clear" → Check INPUT1 pull-up configuration
- Inverted logic → May need software adjustment for MEV alarm type

---

### Test 6: State Persistence (Autonomous Operation)

**Objective:** Verify board maintains last settings when HA disconnects

**Steps:**
1. [ ] Set specific states in HA:
   - Power: ON
   - Mode: Summer (ON)
   - Dehumidifier: OFF
   - Cooling: OFF
   - Fan Speed: 60%
2. [ ] Verify all relays and DAC match expected states (use multimeter)
3. [ ] Record current states
4. [ ] Disconnect Home Assistant (stop HA or unplug network)
5. [ ] Wait 5 minutes
6. [ ] Verify board relays remain in last states (use multimeter):
   - [ ] Relay 1 (Power) still CLOSED
   - [ ] Relay 2 (Mode) still CLOSED
   - [ ] Relay 3 (Dehumidifier) still OPEN
   - [ ] Relay 4 (Cooling) still OPEN
   - [ ] DAC voltage still ~6.0V
7. [ ] Reconnect Home Assistant
8. [ ] Verify HA entities sync to current board states

**Pass Criteria:**
- ✅ Board maintains relay states during HA disconnect
- ✅ DAC voltage stable during disconnect
- ✅ HA re-syncs to board state on reconnect

**Troubleshooting:**
- Relays reset → Check `restore_mode` in component configuration
- DAC resets to 0V → Check `restore_value: true` in number entity
- HA out of sync → May need manual refresh of entities

---

## Installation Testing

Complete these tests DURING physical installation.

### Test 7: Pre-Connection Verification

**Before connecting to MEV unit:**

1. [ ] All bench tests passed
2. [ ] Wiring diagram reviewed and understood
3. [ ] MEV unit documentation reviewed
4. [ ] MEV terminal functions verified
5. [ ] Wire gauge appropriate for MEV requirements
6. [ ] Shielded cable available for 0-10V signal
7. [ ] Ferrule crimps or terminal blocks ready
8. [ ] MEV unit power is OFF at breaker

**⚠️ DO NOT PROCEED until all items checked**

---

### Test 8: Wiring Continuity

**After wiring but before power-on:**

For each connection:

#### Power Relay Wire
1. [ ] Measure continuity from RELAY1 COM → MEV Power terminal
2. [ ] Measure continuity from RELAY1 NO → MEV Power return
3. [ ] Verify no shorts to ground or other wires

#### Mode Relay Wire
1. [ ] Measure continuity from RELAY2 COM → MEV Mode terminal
2. [ ] Measure continuity from RELAY2 NO → MEV Mode return
3. [ ] Verify no shorts

#### Dehumidifier Relay Wire
1. [ ] Measure continuity from RELAY3 COM → MEV Dehumid terminal
2. [ ] Measure continuity from RELAY3 NO → MEV Dehumid return
3. [ ] Verify no shorts

#### Cooling Relay Wire
1. [ ] Measure continuity from RELAY4 COM → MEV Cooling terminal
2. [ ] Measure continuity from RELAY4 NO → MEV Cooling return
3. [ ] Verify no shorts

#### 0-10V Fan Speed Wire
1. [ ] Measure continuity from DAC1(+) → MEV 0-10V (+)
2. [ ] Measure continuity from GND(-) → MEV 0-10V (-)
3. [ ] Verify no shorts between (+) and (-)
4. [ ] Verify shield connected at KC868-A6 end only

#### Alarm Input Wire
1. [ ] Measure continuity from INPUT1(+) → MEV Alarm (+)
2. [ ] Measure continuity from GND(-) → MEV Alarm (-)
3. [ ] Verify no shorts

**Pass Criteria:**
- ✅ All wires have continuity end-to-end
- ✅ No shorts between wires or to ground
- ✅ Shield properly connected (one end only)

---

## Post-Installation Testing

Complete these tests AFTER connecting to MEV unit.

### Test 9: Controlled Power-On

**Objective:** Safely power on integrated system

**Steps:**
1. [ ] Verify all wiring tests passed
2. [ ] Verify MEV unit main power still OFF
3. [ ] Apply power to KC868-A6 board
4. [ ] Wait for board to boot and connect to HA
5. [ ] Set all switches to OFF in HA:
   - [ ] Power: OFF
   - [ ] Mode: OFF
   - [ ] Dehumidifier: OFF
   - [ ] Cooling: OFF
6. [ ] Set fan speed to 0%
7. [ ] Verify all relays OPEN (use multimeter at KC868-A6)
8. [ ] Verify DAC output ~0V
9. [ ] Restore power to MEV unit at breaker
10. [ ] Wait 30 seconds
11. [ ] Verify MEV unit does NOT start (all controls off)

**Pass Criteria:**
- ✅ Board boots successfully
- ✅ All relays in safe OFF state
- ✅ MEV remains off until commanded

---

### Test 10: Individual Relay Function

**Objective:** Test each relay controls correct MEV function

#### Power Control Test
1. [ ] Ensure all other switches OFF, fan speed 0%
2. [ ] Turn on: `switch.mev_primo_piano_power`
3. [ ] Verify MEV unit powers on (check LEDs, listen for fans)
4. [ ] Turn off: `switch.mev_primo_piano_power`
5. [ ] Verify MEV unit powers off
6. [ ] **Result:** PASS / FAIL

#### Mode Control Test (Winter/Summer)
1. [ ] Turn power ON
2. [ ] Turn on: `switch.mev_primo_piano_mode` (Summer)
3. [ ] Verify MEV changes to summer mode (check MEV indicators)
4. [ ] Turn off: `switch.mev_primo_piano_mode` (Winter)
5. [ ] Verify MEV changes to winter mode
6. [ ] **Result:** PASS / FAIL

#### Dehumidifier Test
1. [ ] Ensure power ON, normal mode
2. [ ] Turn on: `switch.mev_primo_piano_dehumidifier`
3. [ ] Verify MEV activates dehumidifier (check MEV indicators)
4. [ ] Turn off: `switch.mev_primo_piano_dehumidifier`
5. [ ] Verify MEV returns to normal ventilation
6. [ ] **Result:** PASS / FAIL

#### Cooling Integration Test
1. [ ] Ensure power ON
2. [ ] Turn on: `switch.mev_primo_piano_cooling`
3. [ ] Verify MEV enables cooling coordination (check MEV indicators)
4. [ ] Turn off: `switch.mev_primo_piano_cooling`
5. [ ] Verify MEV returns to independent operation
6. [ ] **Result:** PASS / FAIL

**Pass Criteria:**
- ✅ Each relay controls expected MEV function
- ✅ MEV responds to commands within 2 seconds
- ✅ No unexpected behavior or alarms

---

### Test 11: Fan Speed Control

**Objective:** Verify 0-10V output correctly controls MEV fan speed

**Steps:**
1. [ ] Ensure MEV power ON
2. [ ] Set fan speed to 0%
3. [ ] Listen/feel for fan stopped or minimum speed
4. [ ] Set fan speed to 25%
5. [ ] Verify fan runs at low speed
6. [ ] Set fan speed to 50%
7. [ ] Verify fan runs at medium speed
8. [ ] Set fan speed to 75%
9. [ ] Verify fan runs at high speed
10. [ ] Set fan speed to 100%
11. [ ] Verify fan runs at maximum speed
12. [ ] Slowly decrease from 100% → 0%
13. [ ] Verify smooth, continuous decrease (no jumps)

**Test Results:**

| Fan Speed % | MEV Response | Fan Audible/Measurable | Pass/Fail |
|-------------|--------------|------------------------|-----------|
| 0%          | Min/Stop     | ___________            | [ ]       |
| 25%         | Low          | ___________            | [ ]       |
| 50%         | Medium       | ___________            | [ ]       |
| 75%         | High         | ___________            | [ ]       |
| 100%        | Maximum      | ___________            | [ ]       |

**Pass Criteria:**
- ✅ Fan speed changes proportionally to percentage
- ✅ Smooth transitions (no sudden jumps)
- ✅ Responds within 3 seconds of command

**Troubleshooting:**
- No fan response → Check 0-10V wiring polarity
- Partial range only → Verify DAC voltage at MEV terminals
- Jumpy response → Check for noise on 0-10V line, verify shielding

---

### Test 12: Alarm Input Monitoring

**Objective:** Verify alarm sensor correctly monitors MEV fault condition

**Steps:**
1. [ ] Ensure MEV power ON, normal operation
2. [ ] Monitor: `binary_sensor.mev_primo_piano_alarm` in HA
3. [ ] Verify sensor shows "Clear" (OFF) during normal operation
4. [ ] Trigger MEV alarm (consult MEV manual for test procedure)
   - Options: Block air intake, simulate filter clog, use MEV test mode
5. [ ] Verify HA sensor changes to "Problem" (ON) within 5 seconds
6. [ ] Clear MEV alarm condition
7. [ ] Verify HA sensor returns to "Clear" (OFF)

**Test Results:**

| MEV Condition | Expected Sensor | Actual Sensor | Pass/Fail |
|---------------|-----------------|---------------|-----------|
| Normal        | Clear (OFF)     | _________     | [ ]       |
| Alarm Active  | Problem (ON)    | _________     | [ ]       |
| Alarm Cleared | Clear (OFF)     | _________     | [ ]       |

**Pass Criteria:**
- ✅ Sensor accurately reflects MEV alarm state
- ✅ Updates within 5 seconds
- ✅ Logic is correct

**Troubleshooting:**
- Never triggers → Check alarm wire connections, verify MEV alarm output
- Always triggered → Wire may be shorted, check polarity
- Delayed response → Increase ESPHome update interval if needed

---

### Test 13: HA Automation Integration

**Objective:** Verify entities work correctly in HA automations

**Steps:**
1. [ ] Create test automation (see example below)
2. [ ] Trigger automation manually or via condition
3. [ ] Verify all MEV entities respond as programmed
4. [ ] Verify automation completes without errors
5. [ ] Check HA automation traces for any issues

**Example Test Automation:**
```yaml
automation:
  - alias: "MEV Test Automation"
    trigger:
      - platform: state
        entity_id: input_boolean.test_mev
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_power
      - delay:
          seconds: 5
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 60
      - delay:
          seconds: 10
      - service: switch.turn_on
        target:
          entity_id: switch.mev_primo_piano_dehumidifier
      - delay:
          seconds: 5
      - service: switch.turn_off
        target:
          entity_id: switch.mev_primo_piano_dehumidifier
      - service: number.set_value
        target:
          entity_id: number.mev_primo_piano_fan_speed
        data:
          value: 30
```

**Pass Criteria:**
- ✅ Automation executes without errors
- ✅ All commands reach board and MEV unit
- ✅ Timing is correct
- ✅ Entities update in HA

---

### Test 14: Autonomous Operation (Field Test)

**Objective:** Verify system continues operating if HA fails

**Steps:**
1. [ ] Set MEV to specific operating state:
   - Power: ON
   - Mode: Winter (OFF)
   - Dehumidifier: OFF
   - Cooling: OFF
   - Fan Speed: 50%
2. [ ] Verify MEV operating at expected state
3. [ ] Disconnect Home Assistant:
   - Option A: Stop HA service
   - Option B: Disconnect HA from network
   - Option C: Power off HA server
4. [ ] Wait 10 minutes
5. [ ] Verify MEV continues operating at last settings:
   - [ ] Still powered
   - [ ] Fan speed unchanged (~5V on DAC)
   - [ ] Mode unchanged
6. [ ] Reconnect/restart Home Assistant
7. [ ] Verify HA entities re-sync to current board state
8. [ ] Verify you can send new commands after reconnect

**Pass Criteria:**
- ✅ MEV continues operating during HA disconnect
- ✅ No state changes during disconnect
- ✅ HA re-syncs correctly after reconnect
- ✅ Control restored after HA returns

**Troubleshooting:**
- Board resets → Check power supply stability
- Settings lost → Verify `restore_value: true` in entities
- Can't reconnect → Check network/WiFi credentials

---

## Acceptance Criteria Validation

### Final Checklist

All pre-installation tests passed:
- [ ] Power and connectivity ✅
- [ ] Entity visibility ✅
- [ ] Relay operation (all 4) ✅
- [ ] DAC output (0-10V linear) ✅
- [ ] Alarm input ✅
- [ ] State persistence ✅

All installation tests passed:
- [ ] Pre-connection verification ✅
- [ ] Wiring continuity ✅

All post-installation tests passed:
- [ ] Controlled power-on ✅
- [ ] Individual relay functions (all 4) ✅
- [ ] Fan speed control ✅
- [ ] Alarm monitoring ✅
- [ ] HA automation integration ✅
- [ ] Autonomous operation ✅

Documentation complete:
- [ ] All test results recorded
- [ ] Any issues documented
- [ ] Wiring diagram matches installation
- [ ] HA integration guide reviewed

**Overall Result:** PASS / FAIL

---

## Troubleshooting Reference

### Quick Diagnostics

| Issue | Check | Solution |
|-------|-------|----------|
| Board offline | Power, WiFi | Verify 12V power, check WiFi credentials |
| Relay doesn't toggle | Wiring, multimeter | Check PCF8574, verify relay module |
| Fan speed no effect | DAC voltage, wiring | Measure 0-10V, check polarity |
| Alarm always on | Input short | Check wire not grounded |
| Settings lost on HA disconnect | Restore config | Add `restore_value: true` |

---

## Sign-Off

**Tested By:** ______________________  
**Date:** ______________________  
**Result:** PASS / FAIL  

**Notes:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

**Approver:** ______________________  
**Date:** ______________________  

---

## Revision History

| Version | Date         | Changes                          |
|---------|--------------|----------------------------------|
| 1.0     | Oct 30, 2025 | Initial testing checklist created |

