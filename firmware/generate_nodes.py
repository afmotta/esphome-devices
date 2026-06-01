#!/usr/bin/env python3
"""
generate_nodes.py — Generate ESPHome node configs from a registry CSV.

Usage:
    1. Fill in nodes.csv with your physical layout
    2. Run: python generate_nodes.py
    3. Generated configs appear in nodes/

CSV format:
    node_id,floor,room,board,location,gpio_list
    0,0,0,0,"Ground floor hallway entrance","2,3,4,5"

node_id is the flat CAN bus address (0-511).
floor/room/board are metadata carried in the payload for HA.
"""

import csv
from pathlib import Path

TEMPLATE = """\
# =============================================================================
# Node: {name} — ID {node_id}
# =============================================================================
# Floor:    {floor_label}
# Location: {location}
# Room:     {room}, Board: {board}
# Buttons:  {num_buttons} (GPIO {gpio_summary})
# CAN ID:   Input  = 0x{input_id:03X}
#            Status = 0x{status_id:03X}
# =============================================================================

substitutions:
  node_name: "{name}"
  node_id: "{node_id}"
  room_id: "{room}"
  board_id: "{board}"
  debounce_ms: "50"
  can_cs_pin: "GPIO9"
  can_clk_pin: "GPIO18"
  can_mosi_pin: "GPIO19"
  can_miso_pin: "GPIO16"
  can_int_pin: "GPIO20"
  can_clock: "16MHZ"

esphome:
  name: ${{node_name}}
  friendly_name: "{location}"

rp2040:
  board: rpipico

logger:
  level: DEBUG

packages:
  base: !include ../common/base_node.yaml
{button_packages}\
"""

BUTTON_PKG = '  btn{idx}: !include {{ file: ../common/button.yaml, vars: {{ button_index: "{idx}", button_gpio: "{gpio}" }} }}'

FLOOR_LABELS = {0: "Ground", 1: "First", 2: "Second", 3: "Third"}


def can_id(category: int, node_id: int) -> int:
    return ((category & 0x03) << 9) | (node_id & 0x1FF)


def main():
    csv_path = Path(__file__).parent / "nodes.csv"
    out_dir = Path(__file__).parent / "nodes"
    out_dir.mkdir(exist_ok=True)

    if not csv_path.exists():
        print(f"Creating example {csv_path} ...")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["node_id", "floor", "room", "board", "location", "gpio_list"])
            w.writerow([0, 0, 0, 0, "Hallway entrance", "2,3,4,5"])
            w.writerow([1, 0, 1, 0, "Kitchen left", "2,3,4,5,6,7"])
            w.writerow([2, 0, 1, 1, "Kitchen island", "2,3"])
            w.writerow([10, 1, 9, 0, "Master bedroom door", "2,3,4,5"])
            w.writerow([11, 1, 9, 1, "Master bedroom bed left", "2,3"])
            w.writerow([12, 1, 9, 2, "Master bedroom bed right", "2,3"])
            w.writerow([20, 2, 17, 0, "Attic studio", "2,3,4,5"])
        print(f"  Edit {csv_path} with your actual layout, then re-run.\n")

    seen_node_ids = {}
    count = 0
    floor_groups = {}

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            node_id = int(row["node_id"])
            floor = int(row["floor"])
            room = int(row["room"])
            board = int(row["board"])
            location = row["location"]
            gpios = [int(g.strip()) for g in row["gpio_list"].split(",")]

            assert 0 <= node_id <= 511, f"Node ID {node_id} out of range (0-511)"
            assert 0 <= room <= 255, f"Room {room} out of range (0-255)"
            assert 0 <= board <= 255, f"Board {board} out of range (0-255)"
            assert len(gpios) <= 6, f"Max 6 buttons, got {len(gpios)}"

            if node_id in seen_node_ids:
                raise ValueError(f"Duplicate node_id {node_id}: '{location}' vs '{seen_node_ids[node_id]}'")
            seen_node_ids[node_id] = location

            name = f"node{node_id:03d}"
            input_id = can_id(1, node_id)
            status_id = can_id(3, node_id)

            button_lines = [BUTTON_PKG.format(idx=idx, gpio=gpio) for idx, gpio in enumerate(gpios)]

            yaml_content = TEMPLATE.format(
                name=name,
                node_id=node_id,
                floor_label=FLOOR_LABELS.get(floor, f"Floor {floor}"),
                room=room,
                board=board,
                location=location,
                num_buttons=len(gpios),
                gpio_summary=",".join(str(g) for g in gpios),
                input_id=input_id,
                status_id=status_id,
                button_packages="\n".join(button_lines) + "\n",
            )

            out_path = out_dir / f"{name}.yaml"
            with open(out_path, "w") as yf:
                yf.write(yaml_content)

            floor_groups.setdefault(floor, []).append((node_id, room, board, location, len(gpios)))
            print(f"  ✓ {name}.yaml  CAN=0x{input_id:03X}  R{room}B{board}  {len(gpios)} btn  [{location}]")
            count += 1

    print(f"\nGenerated {count} node configs in {out_dir}/")
    print("\n── CAN ID Map ──")
    for floor in sorted(floor_groups):
        label = FLOOR_LABELS.get(floor, f"Floor {floor}")
        print(f"\n  {label} floor:")
        for nid, rm, bd, loc, nb in sorted(floor_groups[floor]):
            cid = can_id(1, nid)
            print(f"    #{nid:3d}  0x{cid:03X}  R{rm}B{bd}  {nb} btn  {loc}")


if __name__ == "__main__":
    main()
