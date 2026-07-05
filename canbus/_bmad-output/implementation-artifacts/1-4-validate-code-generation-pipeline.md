---
status: done
epic: 1
story: 4
story_key: 1-4-validate-code-generation-pipeline
baseline_commit: 96d369d32b727bf9fee9faf4145af1954c6905dc
---

# Story 1.4: Validate code generation pipeline and populate `nodes.csv`

Status: done

## Story

As a developer,
I want `generate_nodes.py` validated and `nodes.csv` populated with the 2 PoC node entries,
so that the generated node YAML files are ready to compile and the pipeline is proven end-to-end.

## Acceptance Criteria

1. `firmware/nodes.csv` contains exactly 2 entries: `node_id=100` and `node_id=101`, both in the ground floor range (100–199), with distinct `room` values, and `gpio_list` populated with the confirmed button GPIO numbers from Story 1.2 (OQ-1)
2. `python3 generate_nodes.py` (run from `firmware/`) exits successfully and prints a CAN ID map listing node 100 and node 101 with no duplicate CAN IDs
3. `firmware/nodes/node100.yaml` and `firmware/nodes/node101.yaml` are generated
4. Each generated YAML includes the correct `!include` path to `firmware/common/canbus_protocol.h` (via the `base: !include ../common/base_node.yaml` package, which in turn includes the header)
5. `generate_nodes.py` rejects any `node_id` outside 0–399 with a clear error message and non-zero exit code
6. `generate_nodes.py` rejects duplicate `node_id` values with a clear error message and non-zero exit code
7. The generated YAML files are committed to the repository; old generated files (`node000.yaml`, `node001.yaml`, etc.) are removed

## Tasks / Subtasks

- [x] Task 1: Update `firmware/generate_nodes.py` — tighten ID validation (AC: 5, 6)
  - [x] Change node_id upper bound from 511 to 399 (IDs 400–511 are reserved per architecture)
  - [x] Change from `assert` to `sys.exit(1)` with printed error message for all validation failures (assert does not guarantee non-zero exit in all Python environments)
  - [x] Confirm duplicate node_id check uses non-zero exit (converted raise ValueError → explicit print + sys.exit(1) for consistency)
- [x] Task 2: Replace `firmware/nodes.csv` with PoC entries (AC: 1)
  - [x] Remove all existing entries (IDs 0, 1, 2, 10, 11, 12, 20)
  - [x] Add node 100: ground floor, room=7, board=0, location="Ground floor hallway", gpio_list="20,21" (OQ-1 confirmed GPIO20–GPIO27)
  - [x] Add node 101: ground floor, room=8, board=0, location="Ground floor living room", gpio_list="20,21"
  - [x] Both entries have node_id in range 100–199 (ground floor)
- [x] Task 3: Run generator and verify output (AC: 2, 3, 4)
  - [x] Run `python3 generate_nodes.py` from `firmware/` — exits 0
  - [x] CAN ID map printed: node 100 = 0x264, node 101 = 0x265, no duplicate IDs
  - [x] `firmware/nodes/node100.yaml` and `firmware/nodes/node101.yaml` created
  - [x] Generated YAMLs contain `packages: base: !include ../common/base_node.yaml`
- [x] Task 4: Clean up old generated files (AC: 7)
  - [x] Deleted `firmware/nodes/node000.yaml`, `node001.yaml`, `node002.yaml`, `node010.yaml`, `node011.yaml`, `node012.yaml`, `node020.yaml`
  - [x] `firmware/nodes/node100.yaml` and `firmware/nodes/node101.yaml` committed

### Review Findings

- [x] [Review][Decision] Distinct board ID requirement resolved — user confirmed that distinct room IDs are sufficient for the PoC; the story and planning requirement text were updated to match the implemented `board=0` / `board=0` registry.
- [x] [Review][Patch] Generated node YAMLs now compile from `firmware/nodes/*.yaml` after correcting the shared include path and replacing node-side CAN ID lambdas with generated static CAN IDs [firmware/common/base_node.yaml:12]
- [x] [Review][Patch] Non-integer CSV fields now exit with a clear validation error instead of a raw `ValueError` traceback [firmware/generate_nodes.py:66]
- [x] [Review][Patch] Duplicate GPIOs inside a single CSV row now fail validation with an explicit error. [`firmware/generate_nodes.py`]
- [x] [Review][Patch] Missing-CSV bootstrap now seeds current PoC rows (100/101, GPIO20/21) and exits before generating stale node YAMLs. [`firmware/generate_nodes.py`]

## Dev Notes

### Prerequisites

This story depends on:

- **Story 1.1 complete:** firmware files are under `firmware/`, not `docs/esphome_canbus/`
- **Story 1.2 complete:** `firmware/README.md` has confirmed GPIO values for OQ-1 (button GPIOs), OQ-2 (INT pin), OQ-3 (oscillator frequency)
- **Story 1.3 complete:** `firmware/common/canbus_protocol.h` is rewritten with the correct EVT_* constant names

If Story 1.2 is not complete, use the existing assumed values (GPIOs 2, 3, 4, 5 for buttons; GPIO20 for INT; 16 MHz oscillator) and note the assumption in the story completion notes.

### Critical Change: `generate_nodes.py` Validation

The existing script uses Python `assert` for validation:

```python
assert 0 <= node_id <= 511, f"Node ID {node_id} out of range (0-511)"
```

**Two problems:**

1. Upper bound must be 399, not 511 (architecture: IDs 400–511 are reserved)
2. Python `assert` can be disabled with `-O` flag and doesn't guarantee a clear error message on exit

**Required validation approach:**

```python
import sys

if not (0 <= node_id <= 399):
    print(f"ERROR: Node ID {node_id} out of range (valid: 0–399)", file=sys.stderr)
    sys.exit(1)
if not (0 <= room <= 255):
    print(f"ERROR: Room {room} out of range (valid: 0–255)", file=sys.stderr)
    sys.exit(1)
if not (0 <= board <= 255):
    print(f"ERROR: Board {board} out of range (valid: 0–255)", file=sys.stderr)
    sys.exit(1)
if len(gpios) > 6:
    print(f"ERROR: Too many GPIOs for node {node_id}: max 6, got {len(gpios)}", file=sys.stderr)
    sys.exit(1)
```

The duplicate node_id check already uses `raise ValueError` (which propagates as a non-zero exit via the uncaught exception). **Confirm this exits non-zero** — Python unhandled exceptions exit with code 1 on CPython. If the project wants a cleaner error, convert it to an explicit `print` + `sys.exit(1)`.

### `nodes.csv` Content for PoC

The PoC uses 2 nodes on the ground floor. Use `node_id=100` and `node_id=101`.

The `gpio_list` values must come from Story 1.2 (OQ-1). If Story 1.2 is not yet complete, use the existing script defaults as a placeholder: `"2,3"` (2 buttons, minimal). Do not use the old entries with 4–6 buttons unless OQ-1 has confirmed those pins.

**Proposed `nodes.csv`** (adjust room/location as appropriate for the physical bench setup):

```csv
node_id,floor,room,board,location,gpio_list
100,0,7,0,Ground floor hallway,<OQ-1 GPIOs from README>
101,0,8,0,Ground floor living room,<OQ-1 GPIOs from README>
```

The `room` values are arbitrary for the PoC bench — they just need to be distinct between node 100 and node 101 so that HA events are distinguishable. The `board` values may match for this PoC.

### Generated YAML Structure

After running `generate_nodes.py`, the generated `firmware/nodes/node100.yaml` will look like:

```yaml
substitutions:
  node_name: "node100"
  node_id: "100"
  room_id: "7"
  board_id: "0"
  debounce_ms: "50"
  can_cs_pin: "GPIO9"
  can_clk_pin: "GPIO18"
  can_mosi_pin: "GPIO19"
  can_miso_pin: "GPIO16"
  can_int_pin: "GPIO20"       # ← verify against OQ-2 from README
  can_clock: "16MHZ"          # ← verify against OQ-3 from README

esphome:
  name: ${node_name}
  friendly_name: "Ground floor hallway"

rp2040:
  board: rpipico

logger:
  level: DEBUG

packages:
  base: !include ../common/base_node.yaml
  btn0: !include { file: ../common/button.yaml, vars: { button_index: "0", button_gpio: "<GPIO>" } }
  # ... one line per button
```

**⚠️ If Story 1.3 renamed EVT_* constants:**
The generated YAML itself does NOT reference EVT_* — those are used in `button.yaml`. The generator template does not need to change. However, `base_node.yaml` and `button.yaml` (updated in Stories 2.1 and 2.2) must use the new names.

### Updating the Generator Template for OQ-2 and OQ-3

The `generate_nodes.py` template hardcodes the MCP2515 pin assumptions. If Story 1.2 confirmed different values, update the template defaults:

```python
TEMPLATE = """\
...
  can_int_pin: "GPIO<OQ-2 value>"
  can_clock: "<OQ-3 value>MHZ"
...
"""
```

These defaults in the template are used for ALL generated nodes. Since this is the PoC, updating the template is the right fix — not per-node overrides.

### Node ID Range Enforcement — Architecture Reference

From architecture doc:

| Range   | Floor                          |
| ------- | ------------------------------ |
| 0–99    | Infrastructure (gateway, etc.) |
| 100–199 | Ground floor                   |
| 200–299 | First floor                    |
| 300–399 | Second floor                   |
| 400–511 | **Reserved — reject**          |

The updated validation must reject IDs ≥ 400.

### Old Generated Files to Remove

These files exist at `firmware/nodes/` after Story 1.1 (moved from `docs/esphome_canbus/nodes/`):

- `node000.yaml` (node_id=0)
- `node001.yaml` (node_id=1)
- `node002.yaml` (node_id=2)
- `node010.yaml` (node_id=10)
- `node011.yaml` (node_id=11)
- `node012.yaml` (node_id=12)
- `node020.yaml` (node_id=20)

All must be deleted. The PoC only uses nodes 100 and 101.

### Testing

The primary verification is running `python3 generate_nodes.py` from `firmware/` and checking:

1. Exit code 0
2. CAN ID map printed showing node 100 and node 101 with IDs `0x264` (node 100, CAT_INPUT=1) and `0x265` (node 101)
   - `can_id(1, 100)` = `(1 << 9) | 100` = `512 + 100` = `612` = `0x264`
   - `can_id(1, 101)` = `(1 << 9) | 101` = `512 + 101` = `613` = `0x265`
3. Rejection tests:
   - Create a temporary `nodes.csv` with `node_id=400` → expect non-zero exit
   - Create a temporary `nodes.csv` with two entries both `node_id=100` → expect non-zero exit

No ESPHome compile is required in this story — node firmware compile gates are in Stories 2.1 and 2.2.

### References

- [Source: epics.md#Story 1.4] — acceptance criteria
- [Source: architecture.md#Node ID Assignment Rule] — 0–399 valid range, floor-to-range mapping
- [Source: architecture.md#Code Generation Discipline] — never edit files in nodes/, all changes via nodes.csv
- [Source: architecture.md#File Organisation Patterns] — `nodes.csv` schema definition
- [Source: docs/esphome_canbus/generate_nodes.py] — existing generator (now at firmware/generate_nodes.py after Story 1.1)

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

_None — no blockers encountered._

### Completion Notes List

- Task 1: Replaced all `assert` statements with explicit `if not (...): print(...); sys.exit(1)` checks. Node ID upper bound changed 511 → 399 per architecture. Duplicate node_id check also converted from `raise ValueError` to explicit `print + sys.exit(1)` for consistency. Rejection tests confirmed: node_id=400 → exit 1 + "ERROR: Node ID 400 out of range (valid: 0–399)"; duplicate node_id=100 → exit 1 + "ERROR: Duplicate node_id...". Both tests passed.
- Task 1 (template): Also corrected hardware pin defaults per Story 1.2 (README): `can_clk_pin` GPIO18→GPIO2, `can_mosi_pin` GPIO19→GPIO3, `can_miso_pin` GPIO16→GPIO4, `can_int_pin` GPIO20→GPIO11. These corrections are required by OQ-2 (INT) and the SPI pin map confirmed from the CANBed RP2040 V1.1 Eagle schematic.
- Task 2: `nodes.csv` replaced with 2 PoC entries. Button GPIOs set to `"20,21"` per OQ-1 (GPIO20–GPIO27 confirmed as expansion header pins). Rooms 7 and 8 used for node 100 and 101 respectively (distinct, PoC bench assignment).
- Task 3: Generator runs successfully. CAN ID map output: node 100 = 0x264, node 101 = 0x265. Both YAMLs contain `packages: base: !include ../common/base_node.yaml` (satisfies AC 4). Exit code 0.
- Task 4: Seven old node YAMLs (node000–node020) deleted. Only node100.yaml and node101.yaml remain in `firmware/nodes/`.
- Deferred-work follow-up: the generator now rejects duplicate GPIOs within one node row and, when `nodes.csv` is missing, seeds current PoC example rows then exits without generating stale YAML output.
- Existing regression test (`_bmad/scripts/tests/test_resolve_customization.py`) passes — no regressions.

### File List

- `firmware/generate_nodes.py` — modified (validation overhaul, hardware pin template corrections)
- `firmware/nodes.csv` — modified (replaced with 2 PoC entries: node 100 and 101)
- `firmware/nodes/node100.yaml` — generated (new)
- `firmware/nodes/node101.yaml` — generated (new)
- `firmware/nodes/node000.yaml` — deleted
- `firmware/nodes/node001.yaml` — deleted
- `firmware/nodes/node002.yaml` — deleted
- `firmware/nodes/node010.yaml` — deleted
- `firmware/nodes/node011.yaml` — deleted
- `firmware/nodes/node012.yaml` — deleted
- `firmware/nodes/node020.yaml` — deleted

### Change Log

- 2026-06-01: Story 1.4 implemented — validated code generation pipeline, populated `nodes.csv` with PoC entries (node 100 and 101), fixed generator validation (assert→sys.exit, bound 399, duplicate check), corrected hardware pin template (SPI + INT), generated node100.yaml and node101.yaml, and removed 7 old placeholder node YAMLs.
- 2026-06-01: Deferred-work follow-up added duplicate-GPIO validation and made the missing-CSV bootstrap seed current PoC rows without generating stale node files.
