#!/usr/bin/env python3
"""commission.py — Phase-1 node commissioning (ADR-0007, static map).

After a node is allocated (allocate_node.py), flashed, mounted, and identified — press its
button and the gateway fires an HA event carrying its node_id; an uncommissioned node also
appears via esphome.canbus_node_unknown — assign its room/board here. This edits the registry
(nodes.csv = the map seed) and regenerates the gateway's compiled node_map.h. Reflash the
gateway to apply (Phase 1 is static; runtime push is a later, pre-go-live phase).

Run with no arguments for an interactive menu (commission nodes one prompt at a time), or use
the subcommands directly for scripting:

    python commission.py                # interactive menu
    python commission.py list
    python commission.py assign --node-id 102 --room 5 --board 0 [--location "Kitchen"] [--floor 0] [--room-slug cucina]
"""

import argparse
import csv
from pathlib import Path

import generate_nodes  # regenerate node_map.h after an edit

HERE = Path(__file__).parent
# HERE is canbus/tools/ — two levels below repo root (flattened out of
# firmware/, Phase 6a), where registry/ was elevated to (Phase 1).
CSV_PATH = HERE.parent.parent / "registry" / "nodes.csv"
FIELDS = generate_nodes.CSV_HEADER  # single source of the registry schema
MAX_RB = 255  # room/board are uint8 in node_map.h


def read_rows():
    with open(CSV_PATH, newline="") as f:
        return list(csv.DictReader(f))


def write_rows(rows):
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            # Rows read from a pre-ADR-0006 CSV have no sensors key — default to 0.
            # Explicit None check: values may be falsy-but-valid (int 0 from
            # apply_assignment, "0" placeholders) and must round-trip untouched.
            w.writerow({k: ("0" if k == "sensors" else "") if r.get(k) is None else r[k]
                        for k in FIELDS})


def apply_assignment(rows, node_id, *, room=None, board=None, floor=None, location=None,
                     room_slug=None):
    """Apply room/board/floor/location/room_slug to the node_id row, persist, and regenerate
    node_map.h.

    Fields left as None keep their existing value. Shared by the `assign` subcommand and the
    interactive flow so the write/regenerate logic lives in exactly one place. Raises SystemExit
    on out-of-range input, an invalid climate join, or unknown node_id.
    """
    if room is not None and not (0 <= room <= MAX_RB):
        raise SystemExit(f"room out of range (0-{MAX_RB})")
    if board is not None and not (0 <= board <= MAX_RB):
        raise SystemExit(f"board out of range (0-{MAX_RB})")

    match = next((r for r in rows if int(r["node_id"]) == node_id), None)
    if match is None:
        raise SystemExit(f"node_id {node_id} not in nodes.csv — allocate it first (allocate_node.py).")

    if room is not None:
        match["room"] = str(room)
    if board is not None:
        match["board"] = str(board)
    if floor is not None:
        match["floor"] = str(floor)
    if location is not None:
        match["location"] = location
    if room_slug is not None:
        match["room_slug"] = room_slug.strip()

    # Validate the climate-zone join on the row's FINAL state before persisting, so an
    # unknown slug / floor mismatch doesn't land in nodes.csv and wedge the generator
    # (spec-map-json-contract; same pre-write stance as the room/board range checks).
    final_slug = (match.get("room_slug") or "").strip()
    final_sensors = (match.get("sensors") or "0").strip() == "1"
    if final_slug or final_sensors:
        err = generate_nodes.validate_room_slug(
            final_slug, int(match["floor"]), final_sensors, generate_nodes.load_climate_zones())
        if err:
            raise SystemExit(err)

    write_rows(rows)
    print(f"Assigned node_id {node_id}: room={match['room']} board={match['board']} "
          f"floor={match['floor']} location={match['location']!r} "
          f"room_slug={final_slug or '-'}")
    generate_nodes.main()
    print("Regenerated node_map.h — reflash the gateway to apply.")


def cmd_list(_args):
    rows = read_rows()
    print(f"{'node_id':>8} {'room':>5} {'board':>6} {'floor':>6} {'room_slug':<16}  location")
    for r in rows:
        flag = "  (unassigned)" if r["room"] == "0" and r["board"] == "0" else ""
        slug = r.get("room_slug") or "-"
        print(f"{r['node_id']:>8} {r['room']:>5} {r['board']:>6} {r['floor']:>6} "
              f"{slug:<16}  {r['location']}{flag}")


def cmd_assign(args):
    rows = read_rows()
    apply_assignment(rows, args.node_id, room=args.room, board=args.board,
                     floor=args.floor, location=args.location, room_slug=args.room_slug)


# --- Interactive prompts ---------------------------------------------------

def prompt_int(label, lo, hi, current):
    """Prompt for an int in [lo, hi]. Blank keeps `current`. Re-prompts on bad input."""
    hint = f" [{lo}-{hi}]" if hi is not None else f" [>= {lo}]"
    while True:
        raw = input(f"{label}{hint} [{current}]: ").strip()
        if not raw:
            return int(current)
        try:
            value = int(raw)
        except ValueError:
            print(f"  not an integer — enter a number{hint}.")
            continue
        if value < lo or (hi is not None and value > hi):
            print(f"  out of range — valid{hint}.")
            continue
        return value


def prompt_str(label, current):
    """Prompt for a string. Blank keeps `current`."""
    raw = input(f"{label} [{current}]: ").strip()
    return raw if raw else current


def prompt_yes(label, default=True):
    """Yes/no prompt. Blank takes `default`."""
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input(f"{label} {suffix}: ").strip().lower()
    if not raw:
        return default
    return raw[0] == "y"


def commission_interactive():
    """Commission nodes one prompt at a time, looping until the user declines another."""
    while True:
        rows = read_rows()
        # node_id must already exist (allocated by allocate_node.py) — re-prompt otherwise.
        match = None
        while match is None:
            raw = input("node_id to commission: ").strip()
            if not raw:
                print("  enter a node_id (allocate one first with allocate_node.py).")
                continue
            try:
                node_id = int(raw)
            except ValueError:
                print("  not an integer.")
                continue
            match = next((r for r in rows if int(r["node_id"]) == node_id), None)
            if match is None:
                print(f"  node_id {node_id} not in nodes.csv — allocate it first (allocate_node.py).")

        room = prompt_int("room", 0, MAX_RB, match["room"])
        board = prompt_int("board", 0, MAX_RB, match["board"])
        floor = prompt_int("floor", 0, None, match["floor"])
        location = prompt_str("location", match["location"])
        room_slug = prompt_str("room_slug (climate zone, blank = none)",
                               match.get("room_slug") or "")

        try:
            apply_assignment(rows, node_id, room=room, board=board, floor=floor,
                             location=location, room_slug=room_slug)
        except SystemExit as exc:  # generate_nodes.main() sys.exit()s on a bad registry row (e.g. another row's value)
            print(f"  assignment failed: {exc}")

        if not prompt_yes("Commission another node?", default=True):
            return


def main_menu():
    """Top-level interactive menu: ask what the user wants to do."""
    while True:
        print("\nWhat do you want to do?")
        print("  [1] List nodes")
        print("  [2] Commission a node")
        print("  [q] Quit")
        choice = input("> ").strip().lower()
        if choice == "1":
            cmd_list(None)
        elif choice == "2":
            commission_interactive()
        elif choice in ("q", "quit", "exit"):
            return
        else:
            print("  unknown choice.")


def main():
    ap = argparse.ArgumentParser(description="Phase-1 node commissioning: assign room/board and regenerate the gateway map.")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="show the registry / current assignments")
    a = sub.add_parser("assign", help="assign room/board (and optional location/floor/room_slug) to a node_id")
    a.add_argument("--node-id", type=int, required=True)
    a.add_argument("--floor", type=int)
    a.add_argument("--room", type=int)
    a.add_argument("--board", type=int)
    a.add_argument("--location")
    a.add_argument("--room-slug", dest="room_slug",
                   help="climate zone join (validated against climate/rooms/**; '' clears)")
    args = ap.parse_args()

    if args.cmd is None:
        try:
            main_menu()
        except (EOFError, KeyboardInterrupt):
            print()  # clean newline, no traceback
        return

    {"list": cmd_list, "assign": cmd_assign}[args.cmd](args)


if __name__ == "__main__":
    main()
