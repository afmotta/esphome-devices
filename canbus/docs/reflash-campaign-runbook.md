# Reflash-Campaign Runbook

> **⚠ STUB — pending bench-timing.** This realizes ADR-0008 open item 2. The *procedure* is
> drafted from ADR-0008 §2; the **time budget numbers below are unvalidated estimates** and
> must be measured on the bench before this runbook gates LIVE
> (`docs/live-freeze-checklist.md`).

## When to run this

Only when a fielded node or bridge **genuinely must change** — i.e. a change that alters what
fielded boards must *transmit* or *receive*. Per ADR-0008 §1, the controller is the sole
compatibility layer: **exhaust controller-side translation first** (new HA event fields,
re-mapping, new derived semantics, decoding a new payload version). If the change is
expressible centrally, it is **not** a node change and this runbook does not apply.

A breaking payload change after LIVE also requires bumping `PROTO_V1` (see `project-context.md`
versioning policy).

## Before any path

Make the source change correct first — committed and compiling, **including any required
`PROTO_V1` bump** for a breaking payload change. The campaign only reflashes boards with
whatever is in source.

## Path A — in-place USB reflash (primary)

The board stays mounted and wired; a laptop reaches its USB port (USB reachability is
*required* by the ADR-0008 §3 install rule and verified at commissioning per
`docs/live-freeze-checklist.md`). **Identity is preserved** — `node_id` is a flash-time
substitution, so recompiling from the registry keeps the board's id and its central-map
entry. No re-commissioning.

1. Confirm the registry row for the board in `registry/nodes.csv` is current.
2. Regenerate: `python3 canbus/firmware/tools/generate_nodes.py` (review the printed CAN-ID map).
3. Compile: `esphome compile canbus/firmware/nodes/node<id>.yaml` (generated filenames are
   zero-padded to 3 digits, e.g. `node007.yaml`).
4. Reach the board's USB port through the wall-box / enclosure opening.
5. Flash: `esphome upload canbus/firmware/nodes/node<id>.yaml`.
6. Verify the board re-joins the bus (heartbeat seen at the controller) before moving on.

> **Bridges:** skip the regenerate step (`bridge.yaml` is hand-maintained, not generated).
> Compile and flash `canbus/firmware/bridge/bridge.yaml` directly over USB-serial (radios off per
> ADR-0005). Ignore any `canbus/firmware/nodes/node<bridge_id>.yaml` that `generate_nodes.py` emits
> for the bridge's registry row — it is a decoy RP2040 node config and must never be flashed to
> the ESP32-S3 bridge. Confirm the bridge resumes forwarding + heartbeating after reflash.

## Path B — board swap (secondary)

Used when the board is damaged or in-place USB access is awkward. Optimised by ADR-0007's
stateless nodes.

1. On the bench, allocate a **fresh** `node_id` (`canbus/firmware/tools/allocate_node.py`), then
   regenerate and build the spare: `python3 canbus/firmware/tools/generate_nodes.py`,
   `esphome compile canbus/firmware/nodes/node<newid>.yaml`, `esphome upload …`. (`allocate_node.py`
   only seeds the registry row; the node YAML doesn't exist until you regenerate.)
2. **Retire the swapped-out board's registry row first** — reset its `(room, board)` to the
   `(0, 0)` placeholder (or delete the row). `node_id`s are never reused, so leaving the old
   row makes two rows share one `(room, board)`, which `generate_nodes.py` rejects.
3. Swap the spare in for the fielded board.
4. Press-to-identify and assign the new `node_id` its `(room, board)` / central-map entry
   (`canbus/firmware/tools/commission.py`).
5. Verify the new board reports correctly end-to-end.

## Time budget (ESTIMATES — TBD by bench)

ADR-0008 §2 estimates the following; **replace with measured values before LIVE.**

| Quantity | ADR-0008 estimate | Bench-measured |
|----------|-------------------|----------------|
| Per board, in-place reflash (incl. ladder time) | ~5–10 min | _TBD_ |
| Per board, board swap | "minutes per node" | _TBD_ |
| Fleet-wide campaign (~100-node house) | ~2–3 working days | _TBD_ |

## Pre-requisites checked elsewhere

- **USB reachability at every mount** — ADR-0008 §3 install rule; verified at commissioning.
- **Archived per-release firmware + pinned ESPHome version** — ADR-0008 open item 3; without
  it a years-later campaign cannot rebuild the exact image.

## Bench-timing TODO (closes open item 2)

- [ ] Time Path A on a representative wall mount (include ladder/access time).
- [ ] Time Path B end-to-end (allocate → flash → swap → commission → verify).
- [ ] Extrapolate a fleet campaign for the real node count and record it above.
- [ ] Remove the STUB banner once the table holds measured values.
