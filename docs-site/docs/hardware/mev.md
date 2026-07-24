# MEV Unit Died

!!! danger "Known gap — no replacement procedure exists"
    There is no documented hardware-replacement procedure for the MEV (Mechanical
    Extract Ventilation) unit anywhere in this project. This page tells you what *is*
    known so you're not starting from zero, but it does not walk you through a swap
    the way the other hardware pages do — because nobody has written that procedure
    yet.

## What this device is

The MEV unit (a Cappellotto Air Fresh I) handles whole-house ventilation and
dehumidification. It talks Modbus at address `0x10` on the climate RS485 bus. It's
described elsewhere in this project's documentation as **"the least flexible bus
member"** — meaning if the RS485 bus's serial settings ever need reconciling (baud
rate, parity), this unit's supported settings are the binding constraint the rest of
the bus has to work around, more so than the relay or analog boards.

Its full register map — mode/on-off/dehumidify controls, five temperature sensors,
39 distinct alarm types, filter-hours tracking — lives in `climate/mev_modbus.yaml` in
the repository. That file is the source of truth if you need the exact register
numbers for diagnosis; it's not duplicated here.

## If it's not responding

Before assuming the unit itself has failed, rule out the shared bus:
[RS485/Modbus troubleshooting](../troubleshooting/rs485-modbus.md) covers wiring,
termination, and address conflicts that could make a perfectly good unit look dead.

## If it has actually failed

This is genuinely uncharted territory for this project. Reasonable starting points,
not a validated procedure:

- Contact the manufacturer or your installer for hardware diagnosis/replacement —
  this is a purpose-built ventilation unit, not a generic Modbus I/O board with a
  spares story like the relay/analog boards.
- Re-integrating a replacement unit (wiring, confirming the Modbus register map still
  matches, address configuration) should be treated as new integration work, not a
  documented swap — verify each register against the unit's own manual rather than
  assuming compatibility.
- If you do work through this, please write down what you did — see the
  [Confidence Ledger](../reference/confidence-ledger.md) for where to record it so the
  next person isn't starting from zero either.

## Related

- [Climate troubleshooting](../troubleshooting/climate.md) — for ventilation
  behavior issues that might not be a hardware failure at all.
