# Modbus Register Map

> **Historical document (Gen-1 hardware).** This register map describes the retired
> KC868-A6/A16 master/slave Modbus topology (`gruppo-miscelazione` / `distribuzione-piano-terra`),
> superseded by ADR-0014's single-master T-Connect Pro + Waveshare RTU I/O family. For
> current Modbus addressing/registers see `climate/CLAUDE.md` Appendices A–C; for
> troubleshooting and hardware-replacement procedures see the
> [Maintenance Guide](https://afmotta.github.io/esphome-devices/). Kept as historical
> record.

This document defines the Modbus register layout for the ESPHome climate control system implementing RS485 Modbus RTU communication between master and slave controllers.

## Master Device: gruppo-miscelazione (Modbus Address 0x01)

**Board:** KC868-A6  
**Role:** Modbus Master  
**RS485:** TX=GPIO27, RX=GPIO14, 9600 baud, 8N1

### Holding Registers (Function Code 0x03 - Read by Slaves)

| Address (Hex) | Address (Dec) | Name                    | Type   | Description                     | Units | Scaling                 | Update Rate | Access |
| ------------- | ------------- | ----------------------- | ------ | ------------------------------- | ----- | ----------------------- | ----------- | ------ |
| 0x0064        | 100           | dallas_piano_terra_temp | INT16  | Ground floor supply temperature | °C    | ×100 (0.01°C precision) | 10s         | Read   |
| 0x00C8        | 200           | climate_mode            | UINT16 | System operation mode           | enum  | 0=off, 1=heat, 2=cool   | 10s         | Read   |
| 0x012C        | 300           | master_heartbeat        | UINT16 | Master liveness counter         | count | Increments from 0       | 10s         | Read   |
| 0x0190        | 400           | soggiorno_temp          | INT16  | Soggiorno room temperature      | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0191        | 401           | soggiorno_humidity      | UINT16 | Soggiorno room humidity         | %RH   | ×10 (0.1% precision)    | 30s         | Read   |
| 0x0192        | 402           | cucina_temp             | INT16  | Cucina room temperature         | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0193        | 403           | cucina_humidity         | UINT16 | Cucina room humidity            | %RH   | ×10 (0.1% precision)    | 30s         | Read   |
| 0x0194        | 404           | bagno_temp              | INT16  | Bagno room temperature          | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0195        | 405           | bagno_humidity          | UINT16 | Bagno room humidity             | %RH   | ×10 (0.1% precision)    | 30s         | Read   |
| 0x0196        | 406           | anticamera_temp         | INT16  | Anticamera room temperature     | °C    | ×100 (0.01°C precision) | 30s         | Read   |
| 0x0197        | 407           | anticamera_humidity     | UINT16 | Anticamera room humidity        | %RH   | ×10 (0.1% precision)    | 30s         | Read   |

### Register Details

#### Register 100: Ground Floor Supply Temperature
- **Purpose:** Exposes the Dallas DS18B20 sensor reading for the ground floor (Piano Terra) mixing valve supply line
- **Source Sensor:** `dallas_0x81000000b3e6f628` (1-Wire bus on GPIO32)
- **Data Type:** Signed 16-bit integer (range: -327.68°C to +327.67°C)
- **Scaling:** Temperature in °C × 100
  - Example: 23.45°C → register value 2345
  - Example: -5.20°C → register value -520
- **Usage:** Slaves can read this to coordinate their heating/cooling based on master supply temperature
- **Update Frequency:** Every 10 seconds (faster than Dallas sensor's native 60s update)

#### Register 200: Climate Mode
- **Purpose:** Broadcast system-wide operating mode to all slaves
- **Source:** Home Assistant text sensor `sensor.thermostat_mode`
- **Data Type:** Unsigned 16-bit integer (enum)
- **Values:**
  - `0` = System off / idle
  - `1` = Heating mode active
  - `2` = Cooling mode active
- **Usage:** Slaves use this to switch their control logic without HA connectivity
- **Update Frequency:** Every 10 seconds

#### Register 300: Master Heartbeat
- **Purpose:** Liveness indicator for master controller
- **Data Type:** Unsigned 16-bit integer (0-65535)
- **Behavior:** Increments by 1 every 10 seconds, wraps to 0 at 65535
- **Usage:** Slaves monitor this register; if unchanged for >30s, master may be offline
- **Update Frequency:** Every 10 seconds

#### Registers 400-407: Room Temperature and Humidity (Story 1.6)
- **Purpose:** Expose Modbus RS485 room sensor data from ground floor zones
- **Source:** XY-MD02 or AM2301-MB Modbus temp/humidity sensors (addresses 10-13)
- **Master Polling:** Master polls sensors every 30 seconds, writes to these registers
- **Slave Reading:** Ground floor slave (Address 0x02) reads these registers for PID control

**Register 400: Soggiorno (Living Room) Temperature**
- **Data Type:** Signed 16-bit integer
- **Scaling:** Temperature in °C × 100
- **Modbus Sensor Address:** 10 (0x0A)
- **Usage:** PID controller uses this instead of supply temperature for precise room control

**Register 401: Soggiorno Humidity**
- **Data Type:** Unsigned 16-bit integer
- **Scaling:** Humidity in %RH × 10
- **Example:** 65.3% RH → register value 653

**Registers 402-403: Cucina (Kitchen) Temperature/Humidity**
- **Modbus Sensor Address:** 11 (0x0B)
- **Usage:** Same as Soggiorno (temperature control + humidity monitoring)

**Registers 404-405: Bagno (Bathroom) Temperature/Humidity**
- **Modbus Sensor Address:** 12 (0x0C)
- **Usage:** Critical for humidity monitoring (bathroom = highest humidity zone)

**Registers 406-407: Anticamera (Entryway) Temperature/Humidity**
- **Modbus Sensor Address:** 13 (0x0D)
- **Usage:** Buffer zone between indoor and outdoor conditions

### Reserved Register Ranges

| Address Range (Hex) | Address Range (Dec) | Purpose                                   | Notes                                  |
| ------------------- | ------------------- | ----------------------------------------- | -------------------------------------- |
| 0x0065 - 0x00C7     | 101 - 199           | Future temperature sensors                | Reserved for additional Dallas sensors |
| 0x00C9 - 0x012B     | 201 - 299           | Future coordination data                  | Reserved for setpoints, overrides      |
| 0x012D - 0x018F     | 301 - 399           | Master expansion                          | Reserved for future features           |
| 0x0198 - 0x01FF     | 408 - 511           | Future room sensors (first/second floor)  | Addresses 414-427 for expansion        |
| 0x0200 - 0x03FF     | 512 - 1023          | Reserved for slave device status readback | Not yet implemented                    |

## Slave Devices

### Room Temperature/Humidity Sensors (Modbus Addresses 10-13)

**Sensor Model:** XY-MD02 or AM2301-MB Modbus RS485 Temperature/Humidity Sensor  
**Protocol:** Modbus RTU Slave, 9600 baud, 8N1  
**Power:** 12-24V DC  
**Role:** Provide room-level temperature and humidity data for precise zone control

#### Sensor Addresses (Ground Floor)

| Modbus Address | Location   | Zone Name   | Purpose                          |
| -------------- | ---------- | ----------- | -------------------------------- |
| 10 (0x0A)      | Soggiorno  | Living Room | Primary living space control     |
| 11 (0x0B)      | Cucina     | Kitchen     | High-activity zone with humidity |
| 12 (0x0C)      | Bagno      | Bathroom    | Highest humidity monitoring      |
| 13 (0x0D)      | Anticamera | Entryway    | Buffer zone (indoor/outdoor)     |

#### Sensor Registers (Standard for XY-MD02/AM2301-MB)

Sensors typically expose their data at the following addresses (check sensor manual):

| Register Address | Name        | Type   | Description               | Scaling       |
| ---------------- | ----------- | ------ | ------------------------- | ------------- |
| 0x0001           | temperature | INT16  | Current temperature       | ×100 (0.01°C) |
| 0x0002           | humidity    | UINT16 | Current relative humidity | ×10 (0.1% RH) |

**Master Polling Sequence (Story 1.6):**
1. Master polls sensor address 10 → Read registers 0x0001-0x0002
2. Master polls sensor address 11 → Read registers 0x0001-0x0002
3. Master polls sensor address 12 → Read registers 0x0001-0x0002
4. Master polls sensor address 13 → Read registers 0x0001-0x0002
5. Master writes sensor data to master registers 400-407
6. Slaves read master registers 400-407 for local PID control
7. Repeat every 30 seconds

### Ground Floor Slave: distribuzione-piano-terra (Modbus Address 0x02)

**Board:** KC868-A16  
**Role:** Modbus Slave  
**RS485:** TX=GPIO13, RX=GPIO16, 9600 baud, 8N1

#### Holding Registers (Read by Master)

| Address (Hex) | Address (Dec) | Name                              | Type   | Description                       | Units | Scaling | Update Rate | Access |
| ------------- | ------------- | --------------------------------- | ------ | --------------------------------- | ----- | ------- | ----------- | ------ |
| 0x0001        | 1             | test_register                     | UINT16 | Test register for communication   | -     | Direct  | On-demand   | R/W    |
| 0x0400        | 1024          | slave_heartbeat                   | UINT16 | Slave liveness counter (reserved) | count | -       | 10s         | Read   |
| 0x0401-0x04FF | 1025-1279     | Reserved for zone status (future) | -      | -                                 | -     | -       |

*Note: Detailed slave register map will be defined in Story 1.3 (Slave Data Reading)*

## Example Modbus Commands

### Reading Master Registers from Slave

**Read Ground Floor Temperature (Register 100):**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x0064 (100 decimal)
Quantity: 1 register (2 bytes)

Request (RTU): 01 03 00 64 00 01 [CRC]
Response: 01 03 02 09 29 [CRC]
  → 0x0929 = 2345 decimal = 23.45°C
```

**Read Climate Mode (Register 200):**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x00C8 (200 decimal)
Quantity: 1 register

Request (RTU): 01 03 00 C8 00 01 [CRC]
Response: 01 03 02 00 01 [CRC]
  → 0x0001 = 1 = Heating mode
```

**Read Master Heartbeat (Register 300):**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x012C (300 decimal)
Quantity: 1 register

Request (RTU): 01 03 01 2C 00 01 [CRC]
Response: 01 03 02 00 7B [CRC]
  → 0x007B = 123 decimal (heartbeat count)
```

### Reading All Master Coordination Data (Burst Read)

**Read Registers 100-300 in one transaction:**
```
Function Code: 0x03 (Read Holding Registers)
Slave Address: 0x01 (Master)
Starting Address: 0x0064 (100 decimal)
Quantity: 3 registers (temperature, mode, heartbeat)

Request (RTU): 01 03 00 64 00 03 [CRC]
Response: 01 03 06 09 29 00 01 00 7B [CRC]
  → Reg 100: 0x0929 = 2345 = 23.45°C
  → Reg 200: 0x0001 = 1 = Heating
  → Reg 300: 0x007B = 123 = Heartbeat
```

*Note: Burst reads may not work correctly depending on register spacing; test individually first.*

## Error Handling

### Modbus Exception Codes

| Code | Name                  | Description                                      |
| ---- | --------------------- | ------------------------------------------------ |
| 0x01 | Illegal Function      | Unsupported function code                        |
| 0x02 | Illegal Data Address  | Register address not implemented                 |
| 0x03 | Illegal Data Value    | Invalid value for write operation                |
| 0x04 | Slave Device Failure  | Device error (e.g., sensor unavailable)          |
| 0x0B | Gateway Target Failed | Slave not responding (for master querying slave) |

### Testing Invalid Register Reads

**Read Unimplemented Register 500:**
```
Request: 01 03 01 F4 00 01 [CRC]
Expected Response: 01 83 02 [CRC]
  → 0x83 = Function code 0x03 | 0x80 (exception flag)
  → 0x02 = Exception code (Illegal Data Address)
```

## Data Precision and Update Rates

| Data Type    | Source Update Rate  | Modbus Update Rate  | Precision       | Notes                                   |
| ------------ | ------------------- | ------------------- | --------------- | --------------------------------------- |
| Temperature  | 60s (Dallas native) | 10s (register sync) | 0.01°C (×100)   | Faster Modbus updates than sensor polls |
| Climate Mode | On-change (HA)      | 10s (register sync) | Enum (discrete) | Polling ensures slaves see changes      |
| Heartbeat    | N/A                 | 10s (increment)     | 1 count         | Monotonic counter with wraparound       |

## Implementation Notes

### Temperature Scaling Rationale

**Why ×100 scaling?**
- Dallas DS18B20 sensors provide 0.0625°C resolution (12-bit)
- ESPHome reports as float (e.g., 23.45°C)
- Modbus registers are 16-bit integers (no float support)
- Multiply by 100 preserves 0.01°C precision, sufficient for HVAC
- Range: -327.68°C to +327.67°C (adequate for climate control)

**Alternative Considered (×10):**
- 0.1°C precision (e.g., 23.5°C → 235)
- Deemed insufficient; temperature control benefits from 0.01°C precision
- Larger range (-3276.8°C to +3276.7°C) not needed

### Register Address Spacing

Registers are spaced at intervals of 100 decimal (0x64 hex) to allow future expansion within each category:
- **100-199:** Temperature sensors
- **200-299:** Coordination/control data
- **300-399:** Status/diagnostic data

This prevents conflicts when adding new registers in future stories.

### Feature Flag Integration

All register updates respect the `use_modbus` substitution flag:
- When `use_modbus: "false"` → No register updates, saves CPU
- When `use_modbus: "true"` → Registers update every 10 seconds

This allows safe deployment with Modbus infrastructure present but inactive.

## Example Modbus Commands for Testing and Troubleshooting

This section provides practical examples for reading and writing Modbus registers using various tools.

### Reading Registers with ESPHome Logs

**Enable Modbus debugging in your device YAML:**
```yaml
logger:
  level: DEBUG
  logs:
    modbus_controller: DEBUG
    modbus.master: DEBUG
```

**Watch logs during operation:**
```bash
esphome logs locals/gruppo-miscelazione.yaml
```

**Expected output for successful register reads:**
```
[D][modbus_controller:189]: Read from register 100: value=2345 (23.45°C)
[D][modbus_controller:189]: Read from register 200: value=1 (heat mode)
[D][modbus_controller:189]: Read from register 300: value=42 (heartbeat)
```

### Reading Registers with mbpoll (Command Line)

**Install mbpoll:**
```bash
brew install mbpoll          # macOS
sudo apt install mbpoll      # Ubuntu/Debian
```

**Single register read (Master supply temperature):**
```bash
mbpoll -a 1 -r 100 -t 3 /dev/ttyUSB0 -b 9600 -P none
```
**Output:**
```
mbpoll 1.4-12 - FieldTalk(tm) Modbus(R) Polling Utility
Protocol configuration: Modbus RTU
Slave configuration: address = [1], start reference = 100, count = 1
Communication: /dev/ttyUSB0, 9600, 8, 1, none, t/o 1.00 s
Data type: 16-bit register, input register table
[100]: 2345
```

**Multiple register read (burst read of all master registers):**
```bash
mbpoll -a 1 -r 100 -c 11 -t 3 /dev/ttyUSB0 -b 9600 -P none
```
**Output:**
```
[100]: 2345    (Supply temp: 23.45°C)
[101]: 0       (Reserved)
[200]: 1       (Climate mode: heat)
[300]: 42      (Master heartbeat)
[400]: 2245    (Soggiorno temp: 22.45°C)
[401]: 653     (Soggiorno humidity: 65.3%)
[402]: 2310    (Cucina temp: 23.10°C)
[403]: 582     (Cucina humidity: 58.2%)
```

**Continuous monitoring (watch heartbeat increment):**
```bash
mbpoll -a 1 -r 300 -t 3 /dev/ttyUSB0 -b 9600 -P none -1
```
**Output (updates every 10 seconds):**
```
[300]: 42
[300]: 43
[300]: 44
[300]: 45
```

### Reading Room Sensor Registers Directly

**Read temperature from room sensor (address 10):**
```bash
mbpoll -a 10 -r 1 -t 3 /dev/ttyUSB0 -b 9600 -P none
```
**Output:**
```
[1]: 2245      (22.45°C)
```

**Read humidity from room sensor (address 10):**
```bash
mbpoll -a 10 -r 2 -t 3 /dev/ttyUSB0 -b 9600 -P none
```
**Output:**
```
[2]: 653       (65.3% RH)
```

**Read both temperature and humidity (burst):**
```bash
mbpoll -a 10 -r 1 -c 2 -t 3 /dev/ttyUSB0 -b 9600 -P none
```

### Scanning for Modbus Devices

**Scan all addresses 1-30 to detect connected devices:**
```bash
#!/bin/bash
for addr in {1..30}; do
  echo "Testing address $addr..."
  timeout 2 mbpoll -a $addr -r 1 -t 3 /dev/ttyUSB0 -b 9600 -P none -0 2>&1 | grep -q "Read" && echo "  ✓ Device found at address $addr"
done
```

**Expected output:**
```
Testing address 1...
  ✓ Device found at address 1    (Master)
Testing address 2...
  ✓ Device found at address 2    (Ground floor slave)
Testing address 3...
  ✓ Device found at address 3    (First floor slave)
Testing address 10...
  ✓ Device found at address 10   (Soggiorno sensor)
Testing address 11...
  ✓ Device found at address 11   (Cucina sensor)
```

### Using QModMaster (GUI Tool)

**Setup:**
1. Download QModMaster from https://sourceforge.net/projects/qmodmaster/
2. Configure serial port:
   - Port: COM3 (Windows) or /dev/ttyUSB0 (Linux)
   - Baud rate: 9600
   - Data bits: 8
   - Parity: None
   - Stop bits: 1
3. Set Modbus mode: RTU
4. Set slave address: 1 (for master)

**Read holding registers:**
1. Function code: 03 (Read Holding Registers)
2. Start address: 100
3. Number of registers: 11
4. Click "Read"

**Monitor continuously:**
1. Enable "Scan" mode
2. Set scan interval: 10 seconds
3. Watch registers update in real-time

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Slave Reading All Zeros from Master Registers

**Symptoms:**
- Slave successfully connects to master (no Modbus errors)
- All register values read as 0x0000
- ESPHome logs show successful reads but invalid data

**Possible Causes:**
1. Master not writing to registers (`use_modbus: "false"`)
2. Register address mismatch (slave reading wrong registers)
3. Master sensors not providing data (Dallas sensor offline)
4. Timing issue (slave reading before master writes)

**Debugging Steps:**
```yaml
# Add to master device for debugging
logger:
  level: DEBUG
  
# Check master logs for register write operations
# Should see: "Writing to register 100: value 2345"

# Add to slave device for debugging
sensor:
  - platform: modbus_controller
    name: "Debug Master Reg 100"
    address: 100
    register_type: holding
    value_type: S_WORD
    lambda: |-
      ESP_LOGD("modbus_debug", "Raw register 100 value: %d", x);
      return x / 100.0;
```

**Solution:**
- Verify `use_modbus: "true"` on both devices
- Check ESPHome logs for "Modbus write" messages from master
- Verify Dallas sensors are online and reporting values
- Add 5-10 second delay on slave startup before reading registers

#### Issue 2: CRC Errors on Modbus Bus

**Symptoms:**
- ESPHome logs show "Modbus CRC check failed"
- Communication intermittent or completely failing
- Error rate >5%

**Possible Causes:**
1. Loose RS485 wiring connections
2. Missing or incorrect termination resistors
3. Electromagnetic interference (EMI)
4. Cable too long or poor quality
5. Incorrect baud rate configuration

**Debugging Steps:**
```bash
# Check RS485 wiring with multimeter
# Measure resistance between A and B terminals:
# - No termination: >1kΩ (open circuit)
# - One termination: ~120Ω
# - Both terminations: ~60Ω (120Ω || 120Ω)

# Test with minimal cable length
# If errors disappear, cable quality or length is issue

# Check for EMI sources
# Power cables, motors, fluorescent lights near RS485 cable
```

**Solution:**
- Install 120Ω termination resistors at BOTH bus ends (master + last slave)
- Use twisted-pair cable (Cat5e or better)
- Shield cable and ground shield at ONE end only
- Keep RS485 cable away from power cables (>30cm separation)
- Verify baud rate matches on all devices (9600 baud default)

#### Issue 3: Room Sensor Not Responding (Addresses 10-13)

**Symptoms:**
- Master logs show "Modbus read failed" for sensor address 10-13
- Room temperature/humidity registers (400-407) remain at 0
- PID controllers not using room temperature

**Possible Causes:**
1. Sensor not powered or powered incorrectly
2. Sensor address not configured correctly (DIP switches or software)
3. Sensor not on RS485 bus (wiring disconnected)
4. Sensor model doesn't match expected register layout

**Debugging Steps:**
```yaml
# Add individual sensor test to master
sensor:
  - platform: modbus_controller
    modbus_controller_id: room_sensor_soggiorno
    name: "Debug Soggiorno Sensor"
    address: 0x0001  # Temperature register on sensor
    register_type: holding
    value_type: S_WORD
    on_value:
      - logger.log:
          format: "Sensor 10 temperature raw: %d (%.2f°C)"
          args: [ 'x', 'x / 100.0' ]
```

**Solution:**
- Verify sensor power: 12-24V DC applied correctly
- Check sensor address configuration (consult sensor manual)
- Use Modbus scanner tool to detect sensors on bus
- Verify sensor wiring: A to A, B to B (not crossed)
- Test sensor individually on bench before installation

#### Issue 4: Heartbeat Not Incrementing

**Symptoms:**
- Master heartbeat register (300) stays at constant value
- Slaves detect master as offline

**Possible Causes:**
1. Master not updating heartbeat template sensor
2. `use_modbus: "false"` on master
3. Master crashed or not running

**Debugging Steps:**
```yaml
# Add heartbeat debug logging to master
sensor:
  - platform: template
    id: master_heartbeat_sensor
    lambda: |-
      static uint16_t count = 0;
      ESP_LOGD("heartbeat", "Incrementing heartbeat to %d", count);
      return count++;
    update_interval: 10s
```

**Solution:**
- Verify master is online and responding
- Check master logs for heartbeat increment messages
- Enable `use_modbus: "true"` on master
- Restart master device if heartbeat stuck

### Using ESPHome Logs for Debugging

**Enable Modbus Debugging:**
```yaml
logger:
  level: DEBUG
  logs:
    modbus_controller: DEBUG
    modbus.master: DEBUG
    modbus.slave: DEBUG
```

**Key Log Messages to Monitor:**

Master logs:
```
[D][modbus.master:123]: Sending read request to 0x02 register 0x0001
[D][modbus.master:145]: Response received: 2 bytes
[D][modbus_controller:234]: Writing to holding register 100: 2345
```

Slave logs:
```
[D][modbus.slave:089]: Received read request: register 100
[D][modbus.slave:112]: Sending response: 2 bytes [0x09, 0x29]
[D][modbus_controller:189]: Read from master register 100: 2345 (23.45°C)
```

### Manual Testing with Modbus Tools

**Using mbpoll (Linux/Mac):**
```bash
# Install mbpoll
brew install mbpoll  # macOS
sudo apt install mbpoll  # Linux

# Read single register from master
mbpoll -a 1 -r 100 -t 3 /dev/ttyUSB0 -b 9600 -P none
# Output: [100]: 2345

# Read multiple registers (burst read)
mbpoll -a 1 -r 100 -c 3 -t 3 /dev/ttyUSB0 -b 9600 -P none
# Output:
# [100]: 2345
# [200]: 1
# [300]: 123

# Monitor register continuously
mbpoll -a 1 -r 300 -t 3 /dev/ttyUSB0 -b 9600 -P none -1
# Heartbeat should increment every 10 seconds
```

**Using QModMaster (Windows GUI):**
1. Download from https://sourceforge.net/projects/qmodmaster/
2. Configure serial port: 9600 baud, 8N1, no flow control
3. Set device address (1 for master, 2/3 for slaves)
4. Read holding registers starting at address 100
5. Monitor register values in real-time

## Register Allocation Strategy for Future Expansion

### Ground Floor Room Sensors (Implemented - Story 1.6)
- **Registers 400-407:** Soggiorno, Cucina, Bagno, Anticamera (4 zones × 2 registers)

### First Floor Room Sensors (Future - Story 2.x)
- **Registers 408-415:** Reserved for first floor zones (4 zones × 2 registers)
- Suggested allocation:
  - 408-409: Camera matrimoniale (Master bedroom)
  - 410-411: Camera singola (Single bedroom)
  - 412-413: Studio (Office)
  - 414-415: Bagno primo piano (First floor bathroom)

### Second Floor Room Sensors (Future - Story 2.x)
- **Registers 416-423:** Reserved for second floor zones (4 zones × 2 registers)
- Suggested allocation:
  - 416-417: Mansarda zona 1 (Attic zone 1)
  - 418-419: Mansarda zona 2 (Attic zone 2)
  - 420-421: Bagno secondo piano (Second floor bathroom)
  - 422-423: Reserved for future expansion

### Modbus Sensor Address Assignment

| Address Range | Purpose                          | Notes                              |
| ------------- | -------------------------------- | ---------------------------------- |
| 1             | Master (gruppo-miscelazione)     | Implemented - Story 1.1            |
| 2             | Ground floor slave (A16)         | Implemented - Story 1.3            |
| 3             | First floor slave (A16)          | Implemented - Story 1.5            |
| 4-9           | Future slave boards              | Reserved for expansion             |
| 10-13         | Ground floor room sensors        | Implemented - Story 1.6            |
| 14-17         | First floor room sensors         | Reserved for future implementation |
| 18-21         | Second floor room sensors        | Reserved for future implementation |
| 22-29         | Additional room sensors          | Reserved for expansion             |
| 30-39         | 0-10V Modbus adapters            | Address 30 used - Story 1.5        |
| 40-99         | Future external devices          | Reserved                           |
| 100-247       | Available for custom integration | User-definable                     |

### Expansion Planning

**Adding a New Slave Board:**
1. Assign next available slave address (4, 5, 6, etc.)
2. Allocate register range for slave status (e.g., 1280-1535 for address 4)
3. Update master to poll new slave (add to modbus_master component)
4. Document new registers in this map

**Adding a New Room Sensor:**
1. Assign next available sensor address (14-29 range)
2. Allocate 2 consecutive master registers (temperature + humidity)
3. Update master room sensor poller component
4. Wire sensor to RS485 bus with proper termination

**Best Practices:**
- Always use even register addresses for temperature (odd for humidity)
- Maintain consistent spacing (2 registers per zone)
- Document register purpose immediately upon allocation
- Test new devices individually before adding to production bus

## Version History

| Date       | Version | Changes                                              | Author            |
| ---------- | ------- | ---------------------------------------------------- | ----------------- |
| 2025-10-16 | 1.0     | Initial register map for master (Story 1.2)          | James (Dev Agent) |
| 2025-10-22 | 1.1     | Added room sensor registers 400-407 (Story 1.6)      | James (Dev Agent) |
| 2025-10-22 | 2.0     | Added troubleshooting guide and examples (Story 1.7) | James (Dev Agent) |

## References

- Architecture Document: `docs/architecture.md`
- RS485 Wiring Guide: `docs/rs485-wiring-guide.md`
- Deployment Guide: `docs/deployment-guide.md`
- Story 1.1: Modbus Infrastructure Foundation
- Story 1.2: Master Data Exposure (this implementation)
- Story 1.3: Slave Data Reading
- Story 1.6: Room Sensor Integration

---

**Maintenance Note:** Update this document whenever new registers are allocated or Modbus devices are added to the system.
