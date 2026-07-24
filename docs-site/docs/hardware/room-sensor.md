# Room Sensor Board Died

!!! warning "Speculative page — no confirmed procedure"
    Nothing in this project documents a swap procedure for a room-sensor board. This
    page sketches a plausible approach **by analogy** to the CAN node procedure,
    because room sensors appear to register through the same house-wide registry
    (`registry/nodes.csv` records a `sensors` flag and a `room_slug` per node — the
    living-room sensor is registered there as node 101). But this has not been
    confirmed end-to-end, and the physical process of removing/replacing a sensor
    board that may be built into a wall-mounted enclosure isn't documented anywhere.
    Treat everything below as a starting point, not a trusted procedure — and please
    update this page (and the [Confidence Ledger](../reference/confidence-ledger.md))
    once someone actually does this.

## What this device is

There are two different room-sensor board families in this house:

- **S1-Pro Multi-Sense** (`boards/s1-pro-multi-sense.yaml`) — most rooms; includes an
  LD2450 presence radar, air-quality sensing, and more.
- **wall-sensor** (`devices/wall-sensor.yaml`) — a simpler board (temperature/humidity
  + basic air quality, no radar), used in a smaller number of rooms.

Each room gets its own thin wrapper config (e.g. `devices/room-sensor-soggiorno.yaml`)
that sets the room's slug/name and includes the shared board template.

## Sketch of a by-analogy procedure

1. Confirm which board family the dead sensor is (S1-Pro Multi-Sense vs. wall-sensor)
   — check the existing per-room wrapper file for that room under `devices/` or
   `devices/locals/`.
2. If the board itself is fine and you just need to reflash it, treat it like
   [Path A for a CAN node](can-node.md#path-a-in-place-usb-reflash-use-this-first):
   compile and flash the room's existing wrapper config over USB.
3. If the physical board needs replacing, treat it like
   [Path B for a CAN node](can-node.md#path-b-board-swap-use-this-when-the-board-is-damaged):
   this likely means retiring the old registry row for that room and re-commissioning
   the replacement — but confirm this is actually how these boards get their identity
   before relying on it; it has not been verified against the real firmware/tooling
   for this specific board family.
4. Follow the same [golden rule](index.md) as everywhere else: push the registry
   before reflashing anything.

## Related

- [CAN Node](can-node.md) — the procedure this page is modeled on.
- [Everyday Monitoring](../monitoring.md) — how to tell a room's sensor data has gone
  stale in the first place.
