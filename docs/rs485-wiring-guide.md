# RS485 Wiring Guide for ESPHome Climate Control

**Project:** ESPHome Multi-Floor Climate Control - Modbus RTU Enhancement  
**Version:** 1.0  
**Date:** October 22, 2025

This guide provides comprehensive instructions for proper RS485 wiring, termination, troubleshooting, and signal quality testing.

## Table of Contents

1. [RS485 Basics](#rs485-basics)
2. [Cable Requirements](#cable-requirements)
3. [Termination Resistors](#termination-resistors)
4. [Wiring Topology](#wiring-topology)
5. [Installation Procedure](#installation-procedure)
6. [Signal Quality Testing](#signal-quality-testing)
7. [Troubleshooting](#troubleshooting)
8. [Maximum Cable Length](#maximum-cable-length)

---

## RS485 Basics

### What is RS485?

RS485 is a differential signaling standard for serial communication:
- **Differential signaling:** Uses two wires (A and B) with opposite polarity
- **Noise immunity:** Differential mode rejects common-mode noise
- **Long distance:** Supports cables up to 1200m at 9600 baud
- **Multi-drop:** Multiple devices on same bus (up to 32 nodes standard)

### RS485 Signal Characteristics

```
       +5V ┐           ┌─────┐           ┌─────
A Line     │           │     │           │
           └───────────┘     └───────────┘
           ┌───────────┐     ┌───────────┐
B Line     │           │     │           │
       -5V └─────┘           └─────┘
           
           Idle    1    0    1    0    Idle
           
Differential Voltage = A - B
  Logic 1 (Mark):  A > B  (+2V to +6V typical)
  Logic 0 (Space): A < B  (-2V to -6V typical)
```

### Why Differential Signaling?

**Advantages:**
- **EMI rejection:** Interference affects both wires equally, cancelled by differential measurement
- **Ground offset tolerance:** No shared ground needed between devices
- **Long cable runs:** Signal integrity maintained over 1000m+ distances
- **Reliable:** Proven industrial standard for decades

**Common Applications:**
- Industrial automation (PLCs, sensors, actuators)
- Building management systems (HVAC, lighting)
- Security systems (access control, cameras)
- This project: Climate control coordination

---

## Cable Requirements

### Cable Type: Twisted Pair, Shielded

**Minimum Specification:**
- **Type:** Cat5e or Cat6 Ethernet cable
- **Conductors:** Use one twisted pair (e.g., blue/blue-white)
- **Twist rate:** Minimum 2-3 twists per inch
- **Wire gauge:** 24 AWG minimum (22-24 AWG recommended)
- **Shielding:** Overall foil or braid shield required

### Why Twisted Pair?

Twisting the wires provides:
1. **Balanced capacitance:** Equal coupling to ground/noise sources
2. **Inductance cancellation:** Magnetic fields from each wire cancel
3. **Crosstalk reduction:** Minimizes interference from adjacent pairs
4. **Signal integrity:** Maintains impedance consistency

```
Non-Twisted Pair (BAD):
━━━━━━━━━━━━━━━━━━━  A wire
━━━━━━━━━━━━━━━━━━━  B wire
Problem: Different noise pickup on each wire

Twisted Pair (GOOD):
    ╱╲  ╱╲  ╱╲  ╱╲   A wire
   ╱  ╲╱  ╲╱  ╲╱  ╲
  ╱            B wire
Benefit: Equal noise pickup, cancelled by differential
```

### Recommended Cable Types

| Cable Type              | Pros                                | Cons                      | Cost    |
| ----------------------- | ----------------------------------- | ------------------------- | ------- |
| **Cat5e/Cat6 Ethernet** | Readily available, cheap, 4 pairs   | Overkill for 1 pair       | $0.20/m |
| **Belden 9841**         | Purpose-built RS485, 120Ω impedance | Expensive, harder to find | $1.50/m |
| **Alpha Wire 6712**     | Flexible, industrial-rated          | More expensive            | $1.20/m |
| **Generic 2-wire**      | Cheap                               | May lack proper twist     | $0.10/m |

**Recommendation for this project:** Cat5e/Cat6 Ethernet cable
- Widely available
- 4 pairs available (only need 1 for RS485)
- Good quality twisted pairs
- Often includes shielding (STP versions)
- Cost-effective

### Shield Grounding

**CRITICAL: Ground shield at ONE end only**

```
Master Device         Cable Shield              Slave Device
┌──────────┐         ╔══════════════╗          ┌──────────┐
│          │─── A ───║───────────────║─── A ───│          │
│  RS485   │─── B ───║───────────────║─── B ───│  RS485   │
│          │         ║───────────────║          │          │
│  Ground ─┼─────────║───────────────║          │ Ground   │
└──────────┘         ╚══════════════╝          └──────────┘
     ↑                     ↑                         ↑
   Earth              Shield                    Floating
   Ground             Drain Wire                (not connected)
   
✓ Ground shield at master ONLY
✗ Do NOT ground shield at both ends (creates ground loop)
```

**Why Ground at One End Only?**
- Prevents ground loops (different ground potentials create circulating currents)
- Provides EMI shielding without introducing noise
- Shield drains interference to ground at one point

---

## Termination Resistors

### What is Termination?

Termination resistors absorb signal reflections at cable ends, preventing:
- Signal distortion
- Data errors
- Communication failures

**The Rule:** Install 120Ω resistors at **BOTH** ends of the RS485 bus

### Why 120Ω?

RS485 cables have characteristic impedance of ~120Ω:
- Termination matches cable impedance
- Absorbs reflections instead of bouncing back
- Prevents standing waves on long cables

### Termination Resistor Placement

```
Master (End 1)         Slaves (Middle)            Last Device (End 2)
┌──────────┐          ┌──────────┐               ┌──────────┐
│          │          │          │               │          │
│  ┌──┐   │          │          │               │  ┌──┐   │
│  │120Ω  │          │  (No     │               │  │120Ω  │
│  │ Ω │  │          │   Term)  │               │  │ Ω │  │
│  └──┘   │          │          │               │  └──┘   │
│  A ─────┼──────────┼─── A ────┼───────────────┼─── A    │
│  B ─────┼──────────┼─── B ────┼───────────────┼─── B    │
└──────────┘          └──────────┘               └──────────┘
   ↑                                                 ↑
  Term 1                                           Term 2
```

**For this project:**
- **Termination 1:** Master (gruppo-miscelazione) - Always at one end
- **Termination 2:** Last device on bus (0-10V adapter or furthest room sensor)

### Installing Termination Resistors

**Option 1: Internal Jumper/DIP Switch**
Many RS485 devices have built-in termination:
- Check device manual for termination jumper
- Enable termination on end devices only
- Disable termination on middle devices

**Option 2: External Resistor**
If no built-in termination:
```
Terminal Block:
  A ───┬─── (to next device)
       │
      120Ω
       │
  B ───┴─── (to next device)
```

**Option 3: Resistor in Cable**
Add resistor inside cable connector:
- Solder 120Ω resistor between A and B wires
- Heatshrink wrap for insulation
- Only at cable ends

### Verifying Termination with Multimeter

**Resistance Measurement Between A and B:**

| Configuration     | Expected Resistance | Interpretation              |
| ----------------- | ------------------- | --------------------------- |
| No termination    | >1 kΩ (open)        | Missing terminators         |
| One termination   | ~120Ω               | One end terminated          |
| Both terminations | ~60Ω                | Both ends terminated (good) |
| Short circuit     | <10Ω                | Wiring error                |

**How to Measure:**
1. Power OFF all devices on bus
2. Disconnect A and B from master
3. Set multimeter to resistance (Ω) mode
4. Measure between A and B wires
5. Should read ~60Ω with both terminators installed

```
Expected: 120Ω || 120Ω = 60Ω

     Master Term        Last Device Term
        120Ω                 120Ω
         │                     │
    A ───┴─────────────────────┴─── A
                  │
         Multimeter reads 60Ω
```

---

## Wiring Topology

### Daisy-Chain Topology (CORRECT)

**This is the ONLY correct topology for RS485:**

```
Master ────→ Slave 1 ────→ Slave 2 ────→ Room Sensor 1 ────→ ... ────→ Last Device
  (Term)                                                                    (Term)
  
Single cable runs from device to device in series
```

**Benefits:**
- Minimizes reflections
- Easy to terminate (only 2 points)
- Reliable signal quality
- Industry standard

### Star Topology (INCORRECT - Don't Use!)

```
           ┌─── Slave 1
           │
Master ────┼─── Slave 2
           │
           └─── Slave 3
           
Multiple cable branches from central point
```

**Problems:**
- Signal reflections at each branch point
- Difficult to terminate properly
- Unreliable communication
- Data errors and CRC failures

### This Project's Topology

```
Master Controller                Ground Floor            First Floor
gruppo-miscelazione             distribuzione-          distribuzione-
(KC868-A6)                      piano-terra             primo-piano
Address: 0x01                   (KC868-A16)             (KC868-A16)
[120Ω Term]                     Address: 0x02           Address: 0x03
     │                               │                       │
     ├───────────────────────────────┤                       │
     │                               RS485 Bus               │
     └───────────────────────────────────────────────────────┤
                                                             │
     ┌───────────────────────────────────────────────────────┘
     │
     ├─── Room Sensor 1 (Soggiorno, Address: 0x0A)
     │
     ├─── Room Sensor 2 (Cucina, Address: 0x0B)
     │
     ├─── Room Sensor 3 (Bagno, Address: 0x0C)
     │
     ├─── Room Sensor 4 (Anticamera, Address: 0x0D)
     │
     └─── 0-10V Adapter (Address: 0x1E)
          [120Ω Term]
```

**Cable Lengths (Approximate):**
- Master to Ground Floor Slave: 15m
- Ground Floor to First Floor Slave: 20m
- First Floor to Room Sensors: 10-25m per sensor
- Last Sensor to 0-10V Adapter: 15m
- **Total Bus Length:** ~100-120m (well within 1200m limit)

---

## Installation Procedure

### Step 1: Cable Preparation

**Tools Needed:**
- Wire strippers
- Screwdriver (for terminal blocks)
- Multimeter
- Cable ties
- Heat shrink tubing (optional)

**Procedure:**
1. Measure cable runs between devices (add 10% slack)
2. Cut Cat5e/Cat6 cable to length
3. Strip outer jacket 5cm from each end
4. Select one twisted pair (e.g., blue/blue-white)
5. Strip individual wires 5mm
6. Tin wire ends with solder (optional, improves connection)

**Color Convention:**
- **Blue:** A wire (positive, D+, non-inverting)
- **Blue-White:** B wire (negative, D-, inverting)
- **Shield/Drain:** Connect to ground at master only

### Step 2: Wiring Each Device

**KC868-A6 (Master) Terminal Block:**
```
Terminal:  TX+   TX-   RX+   RX-   GND
Wire:       A     B     A     B   Shield
```

**Note:** Some RS485 transceivers tie TX and RX together internally. Check your board schematic.

**KC868-A16 (Slaves) Terminal Block:**
```
Terminal:  A    B    GND
Wire:      A    B   (none)
```

**Room Sensors (XY-MD02) Terminal Block:**
```
Terminal:  A    B    +12V  GND
Wire:      A    B   Power Ground
```

### Step 3: Install Termination Resistors

**At Master (gruppo-miscelazione):**
1. Locate RS485 terminal block
2. Install 120Ω resistor between A and B terminals
3. Verify with multimeter: should read ~120Ω

**At Last Device (0-10V adapter or last room sensor):**
1. Locate RS485 terminal block
2. Install 120Ω resistor between A and B terminals
3. Verify with multimeter: should read ~120Ω

**All Middle Devices:**
- Do NOT install termination
- Wire passes straight through (A to A, B to B)

### Step 4: Cable Management

**Best Practices:**
1. **Separate from power cables:** Minimum 30cm separation
2. **Avoid parallel runs:** If crossing power cables, do so at 90° angle
3. **Secure cables:** Use cable ties every 50cm
4. **Label cables:** Mark A, B, and device addresses
5. **Document routing:** Take photos for future reference

**Bad:**
```
RS485 Cable ═════════════════════ (parallel to power)
Power Cable ─────────────────────
           ↑
     High EMI coupling
```

**Good:**
```
RS485 Cable ═════════════════════
                                 (30cm+ separation)
Power Cable ─────────────────────
```

### Step 5: Continuity Testing

**Before Powering On:**

1. **A-to-A continuity:** Should be continuous through entire bus
2. **B-to-B continuity:** Should be continuous through entire bus
3. **A-to-B resistance:** Should be ~60Ω with both terminators
4. **A-to-Ground:** Should be high resistance (>10kΩ)
5. **B-to-Ground:** Should be high resistance (>10kΩ)

**Test Procedure:**
```bash
# Disconnect power from all devices
# Set multimeter to continuity mode

# Test A wire continuity
Multimeter Probe 1: Master A terminal
Multimeter Probe 2: Last device A terminal
Expected: Beep (continuity)

# Test B wire continuity
Multimeter Probe 1: Master B terminal
Multimeter Probe 2: Last device B terminal
Expected: Beep (continuity)

# Test termination resistance
Multimeter Probe 1: Master A terminal
Multimeter Probe 2: Master B terminal
Expected: ~60Ω (with both terminators installed)
```

### Step 6: Initial Power-On

**Power Up Sequence:**
1. Power ON master controller first
2. Wait 10 seconds for master to boot
3. Power ON slave devices one at a time
4. Power ON room sensors
5. Monitor ESPHome logs for Modbus communication

**Check Logs:**
```bash
esphome logs locals/gruppo-miscelazione.yaml
```

**Expected Output:**
```
[I][modbus_master:123]: Modbus RTU enabled
[D][modbus_master:201]: Polling slave address 0x02
[D][modbus_master:234]: Response received from 0x02
[D][modbus_master:201]: Polling slave address 0x03
[D][modbus_master:234]: Response received from 0x03
```

---

## Signal Quality Testing

### Visual Inspection

**Check for:**
- [ ] Termination resistors installed at both ends
- [ ] No termination at middle devices
- [ ] A-to-A and B-to-B connections correct (not swapped)
- [ ] Shield grounded at master only
- [ ] No damaged cable insulation
- [ ] Cable secured every 50cm
- [ ] Separation from power cables maintained

### Multimeter Testing (Static)

**DC Voltage Test (Idle Bus):**
1. Power ON all devices
2. Set multimeter to DC voltage mode
3. Measure A-to-Ground: should be +5V to +12V (idle mark state)
4. Measure B-to-Ground: should be -5V to -12V (idle mark state)
5. Measure A-to-B: should be +2V to +12V (differential idle voltage)

**Expected Idle State:**
```
        +5V to +12V
A ───────────────────
                      
                      } Differential: +2V to +12V
B ───────────────────
        -5V to -12V
```

### Communication Error Rate Testing

**Monitor Modbus Errors:**
```bash
# Enable debug logging
esphome logs locals/gruppo-miscelazione.yaml | grep -i error
```

**Calculate Error Rate:**
```
Error Rate = (Failed Polls / Total Polls) × 100%

Acceptable: <1% error rate
Investigate: >1% error rate
Critical: >5% error rate (likely wiring issue)
```

**24-Hour Test:**
- Let system run for 24 hours
- Count Modbus errors in logs
- Calculate error rate
- Investigate if >1%

### Oscilloscope Testing (Advanced)

**For signal quality diagnosis:**

1. **Setup:** Connect oscilloscope probe to A wire (referenced to ground)
2. **Trigger:** Set to edge trigger on falling edge
3. **Timebase:** 100μs/div (to see bit transitions)
4. **Voltage:** 5V/div

**Expected Waveform:**
```
       +5V ┐     ┌─────┐     ┌─────
A Signal   │     │     │     │
        0V └─────┘     └─────┘
           
           Clean square edges (good)
```

**Bad Waveform (Problems):**
```
       +5V ┐   ╱─┐   ╱─┐
A Signal   │  ╱  │  ╱  │
        0V └─╱   └─╱   └──
           
           Rounded edges (reflections/termination issue)
```

**Differential Measurement:**
- Use two probes: A and B
- Set scope to MATH mode: CH1 - CH2
- Differential signal should be clean ±2V to ±6V square wave

---

## Troubleshooting

### Problem: No Communication

**Symptoms:**
- Slaves show "Modbus connection failed" in logs
- No response from any device
- Complete silence on bus

**Troubleshooting Steps:**

1. **Check Power:**
   - [ ] All devices powered ON
   - [ ] Power LEDs lit on all devices
   - [ ] Correct voltage (5V or 12V depending on device)

2. **Check Wiring:**
   - [ ] A-to-A connections continuous
   - [ ] B-to-B connections continuous
   - [ ] No A-to-B short circuit (check with multimeter)
   - [ ] Shield not shorting to A or B

3. **Check Configuration:**
   - [ ] Baud rate matches on all devices (9600)
   - [ ] Data bits = 8, Parity = None, Stop bits = 1
   - [ ] UART pins correct in YAML (GPIO27/14 for A6, GPIO13/16 for A16)
   - [ ] `use_modbus: "true"` on all devices

4. **Check Termination:**
   - [ ] Measure A-to-B resistance: should be ~60Ω
   - [ ] If >100Ω: missing terminator
   - [ ] If <20Ω: short circuit

**Quick Test:**
```bash
# Disconnect all devices except master
# Master should show "No response" errors (expected, no slaves)
# Reconnect one slave at a time
# Communication should work with just master + 1 slave
```

### Problem: Intermittent Communication

**Symptoms:**
- Communication works sometimes, fails others
- CRC errors in logs
- Error rate 1-10%

**Troubleshooting Steps:**

1. **Check Termination:**
   - Missing terminators → reflections → intermittent errors
   - Verify ~60Ω resistance between A and B

2. **Check Cable Quality:**
   - Loose connections in terminal blocks → intermittent contact
   - Damaged cable → intermittent short/open
   - Re-seat all wires in terminal blocks, tighten screws

3. **Check EMI Sources:**
   - Fluorescent lights → high-frequency noise
   - Variable frequency drives (VFDs) → switching noise
   - Power cables too close → inductive coupling
   - Move RS485 cable away from noise sources

4. **Check Cable Length:**
   - Total bus length >1200m → signal attenuation
   - Measure actual cable length
   - If too long, add RS485 repeater

**EMI Test:**
```bash
# Turn off suspected EMI sources one at a time
# Monitor error rate with each source off
# If error rate drops, EMI source identified
```

### Problem: Some Devices Work, Others Don't

**Symptoms:**
- Master communicates with Slave 1, but not Slave 2
- Room sensor 1 responds, sensors 2-4 don't
- Last device on bus never responds

**Troubleshooting Steps:**

1. **Check Device Addresses:**
   - [ ] Each device has unique address (1, 2, 3, 10, 11, ...)
   - [ ] No duplicate addresses on bus
   - [ ] Addresses configured correctly in device firmware

2. **Check Wiring to Non-Working Devices:**
   - [ ] A and B connected (not swapped)
   - [ ] Continuity from previous device
   - [ ] No breaks in cable

3. **Isolate Non-Working Device:**
   - Disconnect non-working device from bus
   - Bridge wires to bypass device
   - If bus works without device, device is faulty

4. **Check Device-Specific Configuration:**
   - Room sensors: DIP switches or software address config
   - Slaves: Correct UART pins in YAML
   - Power: Device getting correct voltage

**Bypass Test:**
```
Before:
Master ─── Slave 1 ─── Slave 2 ─── Room Sensor 1
                       (fails)

After (bypass Slave 2):
Master ─── Slave 1 ──┐         ┌── Room Sensor 1
                      └─────────┘
                      
If Room Sensor 1 now works, Slave 2 is the problem
```

### Problem: High Error Rate (>5%)

**Symptoms:**
- Communication works but frequent CRC errors
- Data corruption
- Unreliable operation

**Troubleshooting Steps:**

1. **Check Signal Quality (Oscilloscope):**
   - Rounded edges → reflections (termination issue)
   - Noise spikes → EMI (shielding/separation issue)
   - Excessive ringing → impedance mismatch

2. **Check Cable:**
   - Non-twisted pair → replace with Cat5e/Cat6
   - Unshielded → add shielding
   - Poor quality → replace with better cable

3. **Reduce Baud Rate (Temporary Workaround):**
   ```yaml
   # In all device YAMLs
   uart:
     baud_rate: 4800  # Reduce from 9600
   ```
   - Lower baud rate = more noise margin
   - Confirms signal quality issue
   - Not a permanent solution (fix wiring instead)

4. **Check Ground Loops:**
   - Shield grounded at both ends → ground loop
   - Different ground potentials → circulating current
   - Ground shield at master only

---

## Maximum Cable Length Calculations

### RS485 Standard Limits

**At 9600 baud (this project):**
- **Maximum cable length:** 1200m (4000 feet)
- **Maximum stub length:** 1m (from main bus to device)
- **Maximum nodes:** 32 (without repeaters)

### Cable Length vs Baud Rate

| Baud Rate | Maximum Length | Notes                      |
| --------- | -------------- | -------------------------- |
| 9600      | 1200m          | This project (good margin) |
| 19200     | 1000m          | -                          |
| 38400     | 500m           | -                          |
| 115200    | 100m           | Not recommended for RS485  |

### This Project's Cable Lengths

| Segment                       | Approximate Length | Cumulative |
| ----------------------------- | ------------------ | ---------- |
| Master → Ground Floor Slave   | 15m                | 15m        |
| Ground Floor → First Floor    | 20m                | 35m        |
| First Floor → Room Sensor 1   | 10m                | 45m        |
| Room Sensor 1 → 2             | 15m                | 60m        |
| Room Sensor 2 → 3             | 10m                | 70m        |
| Room Sensor 3 → 4             | 15m                | 85m        |
| Room Sensor 4 → 0-10V Adapter | 15m                | 100m       |

**Total Bus Length:** ~100-120m
**Margin:** 1200m limit - 120m used = **1080m safety margin**

✓ Well within RS485 specifications

### When to Use Repeaters

**Consider RS485 repeaters if:**
- Total cable length >1000m
- Error rate >5% despite good wiring
- More than 32 devices on bus
- Splitting into multiple segments desired

**Repeater Placement:**
```
Segment 1 (1000m)    Repeater    Segment 2 (1000m)
Master ─── Slaves ──── [REP] ──── Slaves ─── Sensors
```

Repeater regenerates signal, effectively creating two separate 1200m buses.

---

## Checklist: RS485 Installation

Use this checklist for every RS485 installation:

### Pre-Installation

- [ ] Cat5e/Cat6 cable procured
- [ ] Two 120Ω termination resistors available
- [ ] Tools ready (wire stripper, screwdriver, multimeter)
- [ ] Cable routes planned and measured
- [ ] Wiring diagram reviewed

### Installation

- [ ] Cable cut to length (with 10% slack)
- [ ] Twisted pair selected (e.g., blue/blue-white)
- [ ] Wires stripped and tinned
- [ ] A-to-A and B-to-B wired correctly
- [ ] Shield connected at master only
- [ ] 120Ω terminator installed at master
- [ ] 120Ω terminator installed at last device
- [ ] No terminators at middle devices
- [ ] Cable secured with ties every 50cm
- [ ] Minimum 30cm separation from power cables

### Testing

- [ ] Continuity test: A-to-A continuous
- [ ] Continuity test: B-to-B continuous
- [ ] Resistance test: A-to-B = 60Ω (with both terminators)
- [ ] Isolation test: A-to-Ground >10kΩ
- [ ] Isolation test: B-to-Ground >10kΩ
- [ ] Power on devices in sequence
- [ ] Check ESPHome logs for Modbus communication
- [ ] Monitor for errors over 24 hours
- [ ] Error rate <1%

### Documentation

- [ ] Cable routing documented (photos/diagram)
- [ ] Device addresses recorded
- [ ] Termination locations marked on diagram
- [ ] Test results recorded
- [ ] Maintenance notes added

---

## References

- **RS485 Standard:** TIA/EIA-485-A
- **Modbus Protocol:** Modbus RTU Specification
- **ESPHome Modbus Documentation:** https://esphome.io/components/modbus.html
- **Related Documents:**
  - `docs/modbus-register-map.md` - Register definitions
  - `docs/deployment-guide.md` - Deployment procedures
  - `docs/architecture-diagram.md` - System topology diagrams

---

## Version History

| Date       | Version | Changes                    | Author            |
| ---------- | ------- | -------------------------- | ----------------- |
| 2025-10-22 | 1.0     | Initial RS485 wiring guide | James (Dev Agent) |

---

**Note:** This guide follows RS485 industry best practices. For project-specific questions, refer to the deployment guide and architecture documentation.
