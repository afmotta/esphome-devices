# MEV Unit Died

!!! danger "Known gap — no replacement procedure exists"
    There is no documented hardware-replacement procedure for the MEV (Mechanical
    Extract Ventilation) unit anywhere in this project. This page tells you what *is*
    known so you're not starting from zero, but it does not walk you through a swap
    the way the other hardware pages do — because nobody has written that procedure
    yet.

## What these devices are

There are **two** MEV units, of **different models**, one per floor with ventilation:

- **First floor — Cappellotto Air Fresh I**, Modbus address `0x10`. Handles ventilation
  *and* dehumidification. It's described elsewhere in this project's documentation as
  **"the least flexible bus member"** — meaning if the RS485 bus's serial settings ever
  need reconciling (baud rate, parity), this unit's supported settings are the binding
  constraint the rest of the bus has to work around, more so than the relay or analog
  boards. Its full register map — mode/on-off/dehumidify controls, five temperature
  sensors, 39 distinct alarm types, filter-hours tracking — lives in
  `climate/mev_modbus.yaml`.
- **Ground floor — Innova HRP DOMO 60 HX**, Modbus address `0x11`. A passive **enthalpic**
  heat-recovery unit: it renews air in response to **air quality and humidity** (raising
  ventilation when humidity is high; the enthalpic core passively manages moisture). It has
  **no active dehumidifier** — its only actuator is fan speed. On the ground floor the fancoils
  also dehumidify, but only in summer, so this unit covers humidity year-round through
  ventilation. Its driver lives in `climate/mev_innova_modbus.yaml`.

Both drive fan speed via a 0-10V analog output (first floor `analog_output_7`, ground floor
`analog_output_8`) and use Modbus for everything else. Those two files are the source of
truth for the exact register numbers if you need them for diagnosis; they're not duplicated
here.

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
