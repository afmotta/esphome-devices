#!/usr/bin/env python3
"""allocate_node.py — allocate the next node_id (persistent monotonic counter) and register it.

A node_id is permanent and never reused (ADR-0007: it is the bus address; a duplicate is a
collision). A high-water mark in firmware/node_id_hwm guarantees monotonic allocation even if
rows are later deleted from nodes.csv. Allocation is identity-only: the row is written with
ALL positioning fields (floor/room/board/location) as placeholders, because none of them are
known until the node is physically mounted. commission.py fills them in later. After allocating,
run generate_nodes.py and flash the board.

Usage:
    python allocate_node.py
"""

import argparse
import csv
from pathlib import Path

from generate_nodes import CSV_HEADER as HEADER  # single source of the registry schema

HERE = Path(__file__).parent
# HERE is canbus/firmware/tools/ — three levels below repo root, where registry/ was
# elevated to (migration Phase 1).
REGISTRY = HERE.parent.parent.parent / "registry"
CSV_PATH = REGISTRY / "nodes.csv"
HWM_PATH = REGISTRY / "node_id_hwm"
NODE_ID_MAX = 8191  # 13 bits, must match canbus_protocol.h / generate_nodes.py


def existing_max() -> int:
    if not CSV_PATH.exists():
        return -1
    with open(CSV_PATH, newline="") as f:
        ids = [int(r["node_id"]) for r in csv.DictReader(f) if r.get("node_id")]
    return max(ids, default=-1)


def main():
    argparse.ArgumentParser(description="Allocate the next node_id and register it in nodes.csv.").parse_args()

    hwm = int(HWM_PATH.read_text().strip()) if HWM_PATH.exists() else -1
    next_id = max(hwm, existing_max()) + 1
    if next_id > NODE_ID_MAX:
        raise SystemExit(f"node_id space exhausted (max {NODE_ID_MAX})")

    new_csv = not CSV_PATH.exists()
    # "a+" (not "a"): the header check below needs a readable handle; writes still append.
    with open(CSV_PATH, "a+", newline="") as f:
        w = csv.writer(f)
        if new_csv:
            w.writerow(HEADER)
        else:
            # Pre-live there is exactly one nodes.csv — the committed one — and a new column is
            # added by editing HEADER and the CSV together, in place (no migration shims, same
            # doctrine as the no-PROTO-bump rule). Fail loudly on a header mismatch instead of
            # appending a row that DictReader would misalign.
            f.seek(0)
            existing = next(csv.reader(f), [])
            if existing != HEADER:
                raise SystemExit(f"nodes.csv header {existing} does not match the expected "
                                 f"{HEADER} — pre-live, update the CSV in place.")
            f.seek(0, 2)  # back to the end before appending
        # Identity-only: floor/room/board/location are placeholders until commissioning;
        # sensors defaults to 0 (set it in nodes.csv when fitting the ADR-0006 kit);
        # room_slug is assigned at commissioning (climate-zone join, spec-map-json-contract).
        w.writerow([next_id, 0, 0, 0, f"node {next_id} (unassigned)", 0, ""])

    HWM_PATH.write_text(f"{next_id}\n")
    print(f"Allocated node_id {next_id} (floor/room/board/location unassigned — set at commissioning).")
    print("Next: python tools/generate_nodes.py  then flash the board.")


if __name__ == "__main__":
    main()
