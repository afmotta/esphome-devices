# CAN Node Died (Wall Button / Room Sensor)

A "CAN node" is one of the small boards behind a wall button or built into a room
sensor. They run frozen firmware (no WiFi), talk to the rest of the house over the
CAN bus, and each has a unique `node_id` recorded in `registry/nodes.csv`.

!!! danger "Push before you reflash"
    If you've edited `registry/nodes.csv` (or used the commissioning tool below),
    run `python3 canbus/tools/check_registry_pushed.py` and confirm it succeeds
    **before** flashing anything. See [Hardware Died: overview](index.md) for why.

There are two paths, depending on whether the board itself is still good.

## Path A — In-place USB reflash (use this first)

Use this when the board is physically fine and you just need to change what it's
running (e.g. a firmware update, or the registry entry changed but the board itself
didn't move). The board stays mounted and wired — you only need to reach its USB
port. Its identity (`node_id`) is preserved automatically; nothing needs
re-registering.

1. Confirm the row for this board in `registry/nodes.csv` is correct and pushed.
2. Regenerate the node firmware definitions: `python3 canbus/tools/generate_nodes.py`
   (check the printed CAN-ID map for sanity).
3. Compile: `esphome compile canbus/nodes/node<id>.yaml` (the filename is your
   node's id, zero-padded to 3 digits — e.g. `node007.yaml`).
4. Reach the board's USB port (every fielded node is supposed to have one
   reachable without rewiring — 🔵 designed-in, verified at installation time).
5. Flash it: `esphome upload canbus/nodes/node<id>.yaml`.
6. Confirm it rejoins the bus — check its heartbeat is visible again (see
   [Everyday Monitoring](../monitoring.md) for what to look at).

## Path B — Board swap (use this when the board is damaged)

Use this when the physical board itself needs replacing.

1. On the bench, allocate a **fresh** `node_id` for the replacement:
   `python3 canbus/tools/allocate_node.py`. This only creates the registry row —
   the node's firmware config doesn't exist yet.
2. Regenerate and build the replacement: `python3 canbus/tools/generate_nodes.py`,
   then `esphome compile canbus/nodes/node<newid>.yaml`, then
   `esphome upload canbus/nodes/node<newid>.yaml` (over USB, on the bench, before
   it goes in the wall).
3. **Retire the dead board's old registry row first** — set its room/board back to
   the empty placeholder, or delete the row entirely. `node_id`s are never reused,
   so if you skip this step the old row will conflict with the new one.
4. Physically swap the new board in for the dead one.
5. Assign the new board its room/location using the commissioning tool:
   `python3 canbus/tools/commission.py` (it supports a "press a button to identify
   yourself" flow, or a direct `commission.py assign --node-id N --room R --board B`
   form).
6. Confirm the new board reports correctly end-to-end (its expected events/sensor
   readings show up).

## Time estimates

!!! warning "Unvalidated — do not plan around these numbers"
    These are the project's own *design-time* estimates, explicitly marked
    unmeasured in the source runbook. Treat them as a rough order of magnitude only,
    and if you measure a real one, please update this page.

| Task | Estimate | Status |
|---|---|---|
| Per-board in-place reflash (including reaching it) | ~5–10 minutes | 🔵 estimate only |
| Per-board swap (bench + install + commission) | "minutes per node" | 🔵 estimate only |
| Whole-house campaign (~100 nodes) | ~2–3 working days | 🔵 estimate only |

## Before you start a bulk campaign

- Every fielded node is supposed to have USB access without rewiring — if you find
  one that doesn't, that's worth fixing independently of any specific failure.
- Rebuilding an *exact* historical firmware image years later depends on archived
  per-release builds and knowing the exact ESPHome version used at the time — if
  those aren't archived, you may only be able to build the *current* firmware, not
  reproduce an old one bit-for-bit.

## Related

- [CAN bus troubleshooting](../troubleshooting/canbus.md) — if you're not sure the
  board is actually dead versus a bus-wide issue.
- [Environment setup](../setup.md) — if this is a fresh machine and you don't have
  the tools installed yet.
