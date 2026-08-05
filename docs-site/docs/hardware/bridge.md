# CAN Bridge Died

The bridge is a small board that joins two sections of the CAN bus together — a
"backbone" segment and a "zone" segment — so a fault or a lot of traffic on one section
doesn't necessarily spread to the other. It's deliberately simple: no WiFi, no Home
Assistant connection, no over-the-air updates. You flash it and read its logs only by
plugging a USB cable directly into it.

There are **two kinds of bridge board**, and which one you have is recorded in the
registry's `profile` column:

| Profile | Board | Where it's used |
| --- | --- | --- |
| `bridge-t2can` | **LilyGO T-2CAN** — one board, two CAN ports | the normal case |
| `bridge` | CANBed RP2040 + a small add-on CAN module | second source |
| `buttons+bridge` | CANBed RP2040 + add-on, **plus wall buttons** | where the cabling splits at a button box |

🔵 No bridge has been built or flashed on real hardware yet.

If the buttons on a `buttons+bridge` box stop working, check whether the whole downstream
section went quiet too: that points at the board itself rather than at the switch.

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
into its heartbeat that stays set until the bridge is power-cycled — so a
struggling-but-not-fully-dead bridge should be visible in its diagnostics rather than
silently degrading. Because a bridge is a normal registry row, it also appears in Home
Assistant's per-node health entities exactly like a node: if it stops heartbeating, you
get the same "node offline" signal you'd get for a wall switch.

!!! danger "Push before you reflash"
    Same rule as every registry-derived device — see [Hardware Died: overview](index.md).

## Path A — In-place USB reflash

The bridge's config is **generated from the registry**, same as any node — its registry
row just carries the `bridge` profile instead of `buttons` (or `buttons+bridge`, if this
one is also a wall switch).

1. Regenerate: `python3 canbus/tools/generate_nodes.py`.
2. Compile its generated config: `esphome compile canbus/nodes/bridge<id>.yaml`
   (note the `bridge` prefix — that's how you spot bridges in `canbus/nodes/`). The
   profile in the registry decides which board it builds for; you don't choose here.
3. Flash it over USB-serial (the bridge has no OTA/WiFi by design — the board has no
   radio at all).
4. Confirm it resumes forwarding and heartbeating (check the health monitor sees its
   heartbeat again).

## Path B — Board swap (the bridge itself is damaged)

1. On the bench, allocate the replacement bridge a fresh `node_id` with
   `python3 canbus/tools/allocate_node.py` (bridges share the flat node_id space with
   regular CAN nodes).
2. In `registry/nodes.csv`, set that new row's `profile` column to `bridge` — or
   `buttons+bridge` if the box also has a wall switch on it — and give its `location`
   something identifiable, e.g. "bridge - floor 1". The allocator seeds new rows as
   `buttons`, so this step is what makes it a bridge. Copy the profile from the row
   you're replacing so you don't accidentally drop its buttons.
3. Retire the old bridge's registry row (same reasoning as CAN nodes — `node_id`s are
   never reused).
4. Regenerate, compile and flash the replacement over USB, as in Path A.
5. Physically install it in place of the dead one and confirm it resumes forwarding
   and heartbeating.

!!! note "Only for the CANBed bridges: the add-on module is fussy"
    A T-2CAN needs no add-on — both CAN ports are on the board, so a spare is just a
    spare. The CANBed bridges are the fiddly ones. Their add-on MCP2515 module must be
    a **3.3 V** model (paired with an SN65HVD230, MCP2562FD or TJA1042T,3 transceiver):
    the very common red "MCP2515 + TJA1050" module is 5 V and will **destroy** the
    board, because the RP2040 is not 5 V tolerant. Its crystal must also be 8, 12, 16
    or 20 MHz, and the firmware's `clock:` setting must match it — a mismatch gives you
    a board that looks fine and moves no traffic. This awkwardness is exactly why the
    T-2CAN is preferred.

## Related

- [CAN bus troubleshooting](../troubleshooting/canbus.md)
- [CAN Node](can-node.md) — the more common case; a bridge failure is rarer than a
  regular node failure. Same board, so the spare is interchangeable.
