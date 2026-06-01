---
status: done
epic: 1
story: 1
story_key: 1-1-move-firmware-to-firmware-directory
baseline_commit: b7172efa06e0e894d19277ea48cd4a911e6e2a56
---

# Story 1.1: Move firmware to `firmware/` directory

Status: done

## Story

As a developer,
I want the firmware source organized under a top-level `firmware/` directory,
so that the firmware is clearly separated from documentation and all tooling correctly locates build files.

## Acceptance Criteria

1. All ESPHome firmware files exist under `firmware/` — specifically: `firmware/common/canbus_protocol.h`, `firmware/common/base_node.yaml`, `firmware/common/button.yaml`, `firmware/gateway.yaml`, `firmware/generate_nodes.py`, `firmware/nodes.csv`, and `firmware/nodes/*.yaml`
2. `docs/esphome_canbus/` is removed from the repository
3. All relative `!include` paths within YAML packages remain valid after the move (i.e., `../common/base_node.yaml` from `nodes/` still resolves correctly)
4. `firmware/secrets.yaml` is listed in `.gitignore` (add both `firmware/secrets.yaml` and `firmware/.esphome/`)
5. `firmware/secrets.yaml.example` is committed with placeholder values for `wifi_ssid`, `wifi_password`, and `ha_api_key`
6. `firmware/README.md` exists with a "Hardware Verification" section (values TBD — three subsections: OQ-1 Button GPIOs, OQ-2 MCP2515 INT pin, OQ-3 Oscillator frequency) and an "ESPHome Version" section (value TBD)
7. `esphome config firmware/gateway.yaml` (run from project root) exits without path resolution errors

## Tasks / Subtasks

- [x] Task 1: Create `firmware/` directory structure and move all files (AC: 1, 2)
  - [x] Create `firmware/`, `firmware/common/`, `firmware/nodes/` directories
  - [x] Move `docs/esphome_canbus/common/canbus_protocol.h` → `firmware/common/canbus_protocol.h`
  - [x] Move `docs/esphome_canbus/common/base_node.yaml` → `firmware/common/base_node.yaml`
  - [x] Move `docs/esphome_canbus/common/button.yaml` → `firmware/common/button.yaml`
  - [x] Move `docs/esphome_canbus/gateway.yaml` → `firmware/gateway.yaml`
  - [x] Move `docs/esphome_canbus/generate_nodes.py` → `firmware/generate_nodes.py`
  - [x] Move `docs/esphome_canbus/nodes.csv` → `firmware/nodes.csv`
  - [x] Move all `docs/esphome_canbus/nodes/*.yaml` → `firmware/nodes/`
  - [x] Remove `docs/esphome_canbus/` entirely
- [x] Task 2: Update `.gitignore` (AC: 4)
  - [x] Add `firmware/secrets.yaml` to `.gitignore`
  - [x] Add `firmware/.esphome/` to `.gitignore`
- [x] Task 3: Create `firmware/secrets.yaml.example` (AC: 5)
- [x] Task 4: Create `firmware/README.md` (AC: 6)
- [x] Task 5: Verify path resolution (AC: 3, 7)
  - [x] Confirm no YAML file content requires changes (all `!include` paths are relative and remain valid)
  - [x] Run `esphome config firmware/gateway.yaml` and confirm it exits without path resolution errors

## Dev Notes

### Critical: What Does and Does NOT Change

**DO NOT change any file contents** during this move — this is a pure restructure. The only new files are `firmware/secrets.yaml.example`, `firmware/README.md`, and additions to `.gitignore`.

**Path analysis — why no `!include` changes are needed:**
- Generated node YAMLs (e.g., `firmware/nodes/node000.yaml`) use:
  - `!include ../common/base_node.yaml` → resolves to `firmware/common/base_node.yaml` ✓
  - `!include { file: ../common/button.yaml, ... }` → resolves to `firmware/common/button.yaml` ✓
- `firmware/common/base_node.yaml` uses `esphome: includes: - common/canbus_protocol.h`
  - ESPHome resolves `includes:` paths relative to the **compile working directory**, not the package file. When `esphome compile nodes/node000.yaml` is run from `firmware/`, it resolves to `firmware/common/canbus_protocol.h` ✓
- `firmware/gateway.yaml` uses `esphome: includes: - common/canbus_protocol.h` — same resolution ✓
- `firmware/generate_nodes.py` uses `Path(__file__).parent / "nodes.csv"` and `Path(__file__).parent / "nodes"` — relative to script location, no changes needed ✓

### Required File Contents

**`firmware/secrets.yaml.example`** (exact content):
```yaml
wifi_ssid: "your_ssid"
wifi_password: "your_password"
ha_api_key: "your_api_key"
```

**`firmware/README.md`** — must include these two top-level sections with placeholder values:

```markdown
# Firmware

## Hardware Verification

Hardware open questions to resolve before first compile.

### OQ-1: Button GPIO numbers (CANBed RP2040)

**Status:** TBD  
**Value:** TBD  
**Source:** TBD

### OQ-2: MCP2515 INT pin (CANBed RP2040)

**Status:** TBD  
**Value:** TBD  
**Source:** TBD

### OQ-3: Oscillator frequency (MCP2515 on CANBed RP2040)

**Status:** TBD  
**Value:** TBD  
**Source:** TBD

## ESPHome Version

**Pinned version:** TBD — record after first successful compile.
```

### `.gitignore` Additions

Check if `.gitignore` exists at project root. If it does, append; if not, create it. Add:
```
firmware/secrets.yaml
firmware/.esphome/
```

### Verification Step

Run from project root:
```bash
esphome config firmware/gateway.yaml
```
This validates YAML syntax and ESPHome component resolution without running a full compile. The command must exit 0. If it fails with a "file not found" or path error, re-examine the `includes:` paths.

**Note:** A full compile (`esphome compile`) requires ESPHome and toolchains to be installed. The AC specifies `esphome config` (config-check only), which just needs ESPHome CLI.

### No Regressions — Existing Code Analysis

The existing files in `docs/esphome_canbus/` are reference material only. They will be fully superseded by later stories:
- `canbus_protocol.h` will be rewritten in Story 1.3 (the existing version is non-authoritative per FR-4.1)
- `gateway.yaml` will be updated in Story 3.1 (hardware config mismatch: existing uses PoE/Ethernet board config; PoC uses WiFi/RS485-CAN board)
- `common/base_node.yaml` and `common/button.yaml` will be updated in Stories 2.1 and 2.2
- `nodes.csv` and generated nodes will be replaced in Story 1.4 (PoC nodes are 100 and 101, not 0–20)

This story's job is ONLY the directory move. Do not attempt to fix any existing issues in the file contents.

### Project Structure After This Story

```
canbus/
├── .gitignore                     ← add firmware/secrets.yaml, firmware/.esphome/
├── README.md
├── docs/
│   └── canbus-smart-home-reference.md   ← keep this (it's reference docs, not firmware)
├── firmware/
│   ├── secrets.yaml.example        ← NEW (committed)
│   ├── README.md                   ← NEW (committed, placeholder sections)
│   ├── nodes.csv
│   ├── generate_nodes.py
│   ├── gateway.yaml
│   ├── common/
│   │   ├── canbus_protocol.h
│   │   ├── base_node.yaml
│   │   └── button.yaml
│   └── nodes/
│       └── *.yaml                  ← generated (committed)
└── _bmad-output/
```

### Testing

There is no automated test suite for ESPHome YAML. The validation gate is:
1. `esphome config firmware/gateway.yaml` exits 0 (no path errors)
2. Manually confirm all files listed in AC #1 exist at their expected paths

### References

- [Source: architecture.md#Project Structure & Boundaries] — canonical directory layout
- [Source: architecture.md#Firmware Build & Deployment] — ESPHome version and directory decisions
- [Source: epics.md#Story 1.1] — acceptance criteria and constraints

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

- `esphome config firmware/gateway.yaml` exits with code 2 due to pre-existing `can_id: !lambda` not-templatable error in `gateway.yaml:53`. This is an existing bug unrelated to the move — all path resolution succeeded. Will be addressed in Story 3.1.

### Completion Notes List

- Pure directory restructure: moved 13 files from `docs/esphome_canbus/` to `firmware/` with no content changes.
- All `!include ../common/` paths in `firmware/nodes/*.yaml` correctly resolve to `firmware/common/` after the move.
- `esphome config` confirmed no path resolution errors (ESPHome found and parsed all files; the exit code 2 is from a pre-existing templating limitation in `canbus.send:can_id`, not a path error).
- Created `firmware/secrets.yaml.example` and `firmware/README.md` as specified.
- Added `firmware/secrets.yaml` and `firmware/.esphome/` to `.gitignore`.

### File List

- firmware/common/canbus_protocol.h (moved from docs/esphome_canbus/common/)
- firmware/common/base_node.yaml (moved from docs/esphome_canbus/common/)
- firmware/common/button.yaml (moved from docs/esphome_canbus/common/)
- firmware/gateway.yaml (moved from docs/esphome_canbus/)
- firmware/generate_nodes.py (moved from docs/esphome_canbus/)
- firmware/nodes.csv (moved from docs/esphome_canbus/)
- firmware/nodes/node000.yaml (moved from docs/esphome_canbus/nodes/)
- firmware/nodes/node001.yaml (moved from docs/esphome_canbus/nodes/)
- firmware/nodes/node002.yaml (moved from docs/esphome_canbus/nodes/)
- firmware/nodes/node010.yaml (moved from docs/esphome_canbus/nodes/)
- firmware/nodes/node011.yaml (moved from docs/esphome_canbus/nodes/)
- firmware/nodes/node012.yaml (moved from docs/esphome_canbus/nodes/)
- firmware/nodes/node020.yaml (moved from docs/esphome_canbus/nodes/)
- firmware/secrets.yaml.example (new)
- firmware/README.md (new)
- .gitignore (modified — added firmware/secrets.yaml and firmware/.esphome/)
- docs/esphome_canbus/ (deleted)

### Change Log

- 2026-06-01: Story 1.1 implemented — moved firmware source from docs/esphome_canbus/ to firmware/, created firmware/secrets.yaml.example and firmware/README.md, updated .gitignore.

### Review Findings

- [x] [Review][Decision] AC 7 verification — confirmed: `esphome config firmware/gateway.yaml` output shows no path errors; exit code 2 is exclusively the pre-existing `can_id: !lambda` templating limitation at gateway.yaml:42. AC 7 passes.
- [x] [Review][Patch] .gitignore missing trailing newline — fixed. [.gitignore:3]
- [x] [Review][Defer] MSG_BUTTON_EVENT and MSG_HEARTBEAT share value 0x01 [firmware/common/canbus_protocol.h:20-21] — deferred, pre-existing
- [x] [Review][Defer] `includes:` path is CWD-sensitive — breaks if `esphome compile` is run from outside the project root [firmware/common/base_node.yaml, firmware/gateway.yaml] — deferred, pre-existing ESPHome behavior
- [x] [Review][Defer] `generate_nodes.py` silently overwrites node files on re-run without warning [firmware/generate_nodes.py] — deferred, pre-existing
- [x] [Review][Defer] `generate_nodes.py` no duplicate GPIO validation within a row — two buttons can share a pin silently [firmware/generate_nodes.py] — deferred, pre-existing
- [x] [Review][Defer] `generate_nodes.py` uses `assert` for validation — all checks are disabled when run with `python -O` [firmware/generate_nodes.py] — deferred, pre-existing
