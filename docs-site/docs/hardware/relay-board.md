# Relay Board Died

The relay board (a Waveshare Modbus RTU Relay 32CH) switches pumps, mixing valves,
radiant floor circuits, and lighting circuits — 32 channels on one board. It's
addressed at `0x2` on the RS485 bus, and this address is deliberately **mirrored on
both the climate bus and the lighting bus**, so a spare board pre-addressed to `0x2`
works in either system without any extra configuration.

## Commissioning a fresh/spare board

A brand-new board ships at the factory-default address `0x1`. You need to change it
to `0x2` before wiring it into either system.

!!! danger "Only one board on the bus while doing this"
    The commissioning procedure writes to the *broadcast* address, which every
    listening Modbus device accepts. If more than one board is connected while you do
    this, you'll re-address all of them at once. Disconnect everything except the
    board you're commissioning first.

1. Wire the target board **alone** to a spare T-Connect Pro's RS485 terminal (A→A,
   B→B).
2. Take the ready-made commissioning tool at `docs/change_waveshare_relay_address.yaml`
   in this repository, edit its WiFi placeholders, and flash it to the spare
   T-Connect Pro: `esphome run docs/change_waveshare_relay_address.yaml`.
3. In its web UI (or Home Assistant, once connected), watch the "Address Register"
   sensor — it should read back `1` (the factory default), confirming the board is
   responding.
4. Press the "Write Address" button. This sends the address change.
5. Power-cycle the relay board (the address change only takes effect after a
   restart).
6. To verify, edit the tool's `current_address` substitution to `0x02` and reflash —
   the Address Register sensor should now read back `2`.
7. Wire the board into place. The house's controllers already expect a relay board at
   `0x2`, so once wired in and powered, it should be picked up automatically — no
   controller-side configuration change needed.

⚠️ **Serial-parameter caveat**: this commissioning tool talks at the board's factory
default (9600 8N1). The live buses in this house target **38400 8E1** — a different
baud rate and parity. Changing a board's baud/parity away from its factory default is
a *separate* register write that this tool does not automate (as of this writing, that
procedure hasn't been confirmed/bring-up-tested). If your live bus genuinely runs at
38400 8E1, a freshly-addressed spare board may still need its serial parameters
reconfigured separately before it will talk correctly — don't assume addressing alone
is sufficient; confirm against the board's manual or by testing communication after
wiring it in.

## If the board just needs a straight swap (already correctly addressed)

If you have a pre-addressed spare (already set to `0x2` and, ideally, already
bench-tested at the live serial parameters), you can skip the commissioning steps
above — just power down, swap the physical board, rewire, and power back up. No
config change is needed on the controller side; it polls address `0x2` regardless of
which physical board answers.

## Related

- [Relay assignment table](../reference/hardware-table.md) — which relay number
  controls which circuit.
- [RS485/Modbus troubleshooting](../troubleshooting/rs485-modbus.md) — if you're not
  sure the board itself is dead versus a wiring/bus issue.
- [Analog Output Board](analog-board.md) — the *other* Modbus I/O board; its
  commissioning procedure is less well documented, don't assume it's identical.
