# Analog Output Board Died

The analog output board (a Waveshare Modbus RTU Analog Output **8CH (B)** — the
voltage variant, not the similar-looking 0-20mA current variant) drives the 0-10V
signals that modulate mixing valves and fancoil fans. It's addressed at `0x1` on the
climate RS485 bus. Unlike the relay board, this address is **not** mirrored on the
lighting bus — this board is climate-only.

## Channel assignments

| Channel | Circuit |
|---|---|
| `analog_output_1` | Ground floor radiant mixing valve |
| `analog_output_2` | First floor radiant mixing valve |
| `analog_output_3` | Soggiorno (living room) fancoil |
| `analog_output_4` | Cucina (kitchen) fancoil |
| `analog_output_5` | Locale Tecnico (technical room) fancoil |
| `analog_output_6` | Sottotetto (attic) fancoil |
| `analog_output_7` | First floor MEV (ventilation) fan speed |
| `analog_output_8` | Unallocated |

## If you're replacing this board with a spare

!!! warning "Known gap — addressing procedure not confirmed"
    Unlike the relay board, this board's own address-configuration register was
    **never independently verified** when this house's hardware was standardized —
    only the relay board's address register (`0x4000`) was confirmed to work as
    documented. The commissioning tool at `docs/change_waveshare_relay_address.yaml`
    is written specifically for the relay board; its register numbers and write
    values may not directly apply to this board. **Before attempting to re-address a
    spare analog board, check the procedure against the board's own physical manual**
    rather than assuming the relay-board tool works unmodified.

What IS confirmed about this board: its 8 output channels live on Modbus holding
registers `0x0000`–`0x0007` (channel 1 = register 0, etc.), each holding a value in
millivolts from `0` to `10000` (representing `0`–`10.00V`), read/written with the
standard Modbus function codes `0x03`/`0x06`/`0x10`.

## If you have a pre-addressed spare

If the replacement board is already correctly addressed to `0x1` (confirmed some
other way — e.g. it came pre-configured, or you verified it against its manual), a
straight physical swap works the same as for the relay board: power down, swap,
rewire, power up. The controller polls address `0x1` regardless of which physical
board answers.

## Related

- [Relay Board](relay-board.md) — the sibling I/O board, with a confirmed
  commissioning procedure you can use as a starting point for adapting to this board.
- [Climate troubleshooting](../troubleshooting/climate.md) — for PID/fancoil
  behavior issues that might not actually be a dead board.
