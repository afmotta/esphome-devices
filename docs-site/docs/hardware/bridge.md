# CAN Bridge Died

The bridge is a small board (LilyGO T-2CAN) that joins two sections of the CAN bus
together — a "backbone" segment and a "zone" segment — so a fault or a lot of traffic
on one section doesn't necessarily spread to the other. It's deliberately simple: no
WiFi, no Home Assistant connection, no over-the-air updates. You flash it and read its
logs only by plugging a USB cable directly into it.

## How to tell it's the bridge and not something else

If an entire section of the house stops hearing CAN traffic while the rest of the bus
is fine, the bridge joining that section is the first suspect. The bridge is designed
to **fail safe**: if its firmware gets stuck, a watchdog timer forces it to reboot
rather than let it limp along, and if it can't keep up or something goes wrong, it
simply stops forwarding traffic ("degrades to silent") — it's built to never jam the
bus or hold it busy. So a dead/stuck bridge looks like "that whole section went quiet,"
not like general chaos on the bus. 🔵 This behavior is built and code-reviewed, not
yet exercised against a real hardware fault.

There's also a self-reporting signal: if the bridge has ever dropped frames because
its internal buffer filled up, it latches an error flag (`ERR_BRIDGE_QUEUE_OVERFLOW`)
into its own heartbeat that stays set until the bridge is power-cycled — so a
struggling-but-not-fully-dead bridge should be visible in its diagnostics rather than
silently degrading.

!!! danger "Push before you reflash"
    Same rule as every registry-derived device — see [Hardware Died: overview](index.md).

## Path A — In-place USB reflash

Unlike a regular node, the bridge's config (`devices/bridge.yaml`) is **hand-written**,
not generated from the registry — skip the registry-regenerate step.

1. Compile it directly: `esphome compile devices/bridge.yaml`.
2. Flash it over USB-serial (the bridge has no OTA/WiFi by design — radios are
   deliberately off on this device).
3. Confirm it resumes forwarding and heartbeating (check the controller sees its
   heartbeat again).

!!! warning "Ignore the decoy file"
    The registry generator (`canbus/tools/generate_nodes.py`) still emits a
    `canbus/nodes/node<id>.yaml` file for the bridge's registry row, because the
    bridge shares the same `node_id` numbering space as regular nodes. **Never flash
    that file to the bridge** — it's a generic node config, not the bridge's actual
    firmware. Always flash `devices/bridge.yaml` directly.

## Path B — Board swap (the bridge itself is damaged)

1. On the bench, allocate the replacement bridge a fresh `node_id` with
   `python3 canbus/tools/allocate_node.py` (bridges share the flat node_id space with
   regular CAN nodes — name the registry row something identifiable, e.g. "bridge -
   floor 1").
2. In `devices/bridge.yaml`, set the `node_id` substitution to the newly allocated
   id (the file ships with a placeholder value — check the current file, it should
   *not* still say `"200"` when you flash a real bridge with it).
3. Retire the old bridge's registry row (same reasoning as CAN nodes — `node_id`s are
   never reused).
4. Compile and flash the replacement over USB, as in Path A.
5. Physically install it in place of the dead one and confirm it resumes forwarding
   and heartbeating.

## Related

- [CAN bus troubleshooting](../troubleshooting/canbus.md)
- [CAN Node](can-node.md) — the more common case; a bridge failure is rarer than a
  regular node failure.
