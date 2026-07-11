# Modbus RS485 0-10V Adapter Setup Guide

> **Historical document (retired hardware).** The generic AliExpress 0-10V adapter this
> guide commissions was replaced by the Waveshare Modbus RTU Analog Output 8CH (B)
> (ADR-0014); its companion re-addressing utilities were retired in the same sweep (see
> `docs/change_waveshare_relay_address.yaml` for the current commissioning tool). Kept
> as historical record.

## Device Information

**Product**: 2/4 Channel RS485 Modbus RTU to 0-10V/0-20mA Analog Output Module  
**Source**: AliExpress (YJ Electronic Store)  
**Link**: https://it.aliexpress.com/item/1005004930063367.html

## Default Factory Settings

These adapters typically ship with the following defaults:

- **Modbus Address**: `0x01` (will need reconfiguration)
- **Baud Rate**: `9600` (matches our system ✅)
- **Data Format**: `8N1` (8 data bits, No parity, 1 stop bit) ✅
- **Protocol**: Modbus RTU
- **Register Map** (per channel):
  - Channel 1: `0x0001`
  - Channel 2: `0x0002`
  - Channel 3: `0x0003`
  - Channel 4: `0x0004`

## ESPHome Configuration Compatibility

✅ **Our implementation is fully compatible!**

The existing `components/modbus_0_10v.yaml` component is designed for these adapters:

```yaml
# Register value range: 0-10000
# Maps to 0.0V - 10.0V output
# Resolution: 0.001V (1mV)

# Example: Register value 5000 = 5.0V output
# Example: Register value 10000 = 10.0V output
# Example: Register value 0 = 0.0V output (fancoil off)
```

## Required Device Configuration

### Step 1: Set Modbus Address

**IMPORTANT**: Each adapter must have a unique address on the RS485 bus.

Current address assignments in our system:
- `0x01` - Master (gruppo-miscelazione A6)
- `0x02` - Ground floor slave (distribuzione-piano-terra A16)
- `0x03` - First floor slave (distribuzione-primo-piano A16)
- `0x04` - **Second floor fancoil 0-10V adapter** ← Configure device to this
- `0x05` - **Ground floor fancoil 0-10V adapter** ← Configure device to this

### Step 2: Configure Device Address (Methods)

Most adapters support address configuration via:

#### Option A: DIP Switches (if present on device)
- Check device for DIP switch bank (usually 8-position)
- Set switches to binary representation of desired address
- Example for address 4: `00000100` (binary)
- Example for address 5: `00000101` (binary)

#### Option B: Configuration Software (USB-RS485 adapter required)
1. Connect device to PC via USB-RS485 adapter
2. Use Modbus configuration tool (Modbus Poll, QModMaster, or vendor software)
3. Read current configuration registers
4. Write new address to configuration register
5. Save and reboot device

#### Option C: Modbus Command (via ESPHome testing)
Some devices allow address change via Modbus command:
```yaml
# Temporary test configuration to change device address
# Function code 0x06: Write Single Register
# Address 0x0000 (configuration register): New address value
```

### Step 3: Verify Configuration

After setting the address, test with ESPHome:

```yaml
# Test in devices/distribuzione-piano-terra.yaml
packages:
  test_0_10v: !include
    file: ../components/modbus_0_10v.yaml
    vars:
      adapter_address: 0x4  # or 0x5 for ground floor
      output_id: "test_fancoil"
```

Watch ESPHome logs for successful communication:
```
[D][modbus_controller:xxx] Modbus device 0x04 responded
[D][modbus_0_10v:xxx] PID output 0.50 → register 5000
```

## Multi-Channel Adapter Notes

For the **4-channel adapter** (ground floor fancoils):

### Register Map (Sequential)
| Channel | Register Address | Use Case                 |
| ------- | ---------------- | ------------------------ |
| 1       | `0x0001`         | Soggiorno Fancoil 1      |
| 2       | `0x0002`         | Soggiorno Fancoil 2      |
| 3       | `0x0003`         | Cucina Fancoil           |
| 4       | `0x0004`         | Technical Closet Fancoil |

### ESPHome Implementation
Use `components/modbus_0_10v.yaml` multiple times with different `register_address` vars:

```yaml
packages:
  soggiorno_fc1: !include
    file: ../components/modbus_0_10v.yaml
    vars:
      adapter_address: 0x5
      output_id: "soggiorno_fc1"
      register_address: 0x0001

  soggiorno_fc2: !include
    file: ../components/modbus_0_10v.yaml
    vars:
      adapter_address: 0x5
      output_id: "soggiorno_fc2"
      register_address: 0x0002

  cucina_fc: !include
    file: ../components/modbus_0_10v.yaml
    vars:
      adapter_address: 0x5
      output_id: "cucina_fc"
      register_address: 0x0003

  tech_closet_fc: !include
    file: ../components/modbus_0_10v.yaml
    vars:
      adapter_address: 0x5
      output_id: "tech_closet_fc"
      register_address: 0x0004
```

## Hardware Connection

### RS485 Wiring
```
ESPHome Board (A16)     0-10V Adapter
───────────────────     ──────────────
GPIO13 (TX)    ──────── A (RS485+)
GPIO16 (RX)    ──────── B (RS485-)
GND            ──────── GND (Common ground)
```

### Termination Resistor
- If adapter is the **last device** on RS485 bus, enable 120Ω termination resistor
- If adapter is in middle of bus, leave termination disabled
- Check device jumper or DIP switch for termination control

### Power Supply
- Adapter requires external power (typically 9-30V DC)
- Do **NOT** power from ESP32 (insufficient current)
- Use dedicated 12V/24V power supply
- Ensure ground is common with ESP32 ground

## Troubleshooting

### No Communication
1. ✅ Check wiring: A/B not reversed
2. ✅ Verify baud rate: Should be 9600 on both sides
3. ✅ Check device address: Must be unique on bus
4. ✅ Test with simple Modbus tool first (Modbus Poll)
5. ✅ Check termination resistor if at end of bus

### Erratic Output
1. ✅ Check register value range (0-10000, not 0-100)
2. ✅ Verify ground connection between devices
3. ✅ Check for electrical noise on RS485 lines (use shielded cable)
4. ✅ Verify power supply is stable

### ESPHome Logs Show Errors
```
[W][modbus_controller:xxx] Modbus device 0x04 not responding
```
- Device address mismatch
- Wiring issue (A/B reversed or disconnected)
- Baud rate mismatch

```
[E][modbus_controller:xxx] CRC check failed
```
- Electrical noise on RS485 lines
- Use shielded twisted pair cable
- Check grounding

## Verification Checklist

Before integrating with PID controllers:

- [ ] Device address configured to `0x04` (second floor) or `0x05` (ground floor)
- [ ] Baud rate verified at 9600
- [ ] RS485 wiring correct (A to A, B to B)
- [ ] Common ground established
- [ ] Termination resistor configured (if end of bus)
- [ ] ESPHome logs show successful communication
- [ ] Test register write: `number.set` from Home Assistant changes output voltage
- [ ] Measure output with multimeter: 0-10V range verified

## References

- ESPHome Modbus Controller: https://esphome.io/components/modbus_controller.html
- Modbus RTU Protocol: https://en.wikipedia.org/wiki/Modbus
- Component Implementation: `components/modbus_0_10v.yaml`
- Architecture: `docs/architecture.md` (Section 6.3)
- Story 1.6: `docs/stories/1.6.ground-floor-fancoil-control.md`
