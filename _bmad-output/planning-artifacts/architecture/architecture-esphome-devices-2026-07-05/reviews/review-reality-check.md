# Review — Verification Against Reality

- **Target:** `ARCHITECTURE-SPINE.md` (+ companion `MIGRATION-MAP.md`), architecture-esphome-devices-2026-07-05
- **Lens:** every committed decision and factual claim checked against the actual repo at `/Users/alberto/src/esphome-devices` (commit tip `59121ec`)
- **Reviewer:** reality-check agent, 2026-07-05
- **Verdict:** **pass-with-fixes** — the spine is unusually well-grounded (most path, tooling, and contract claims check out against the code), but one Stack row contradicts the deployed config and the structural seed asserts a target state no migration phase actually produces.

---

## 1. Findings requiring fixes

### F-1 (HIGH) — Stack row "Modbus RTU (hvac boards, current transport) | 9600 8N1" contradicts the deployed master config

The spine copies the 9600 8N1 value from root `CLAUDE.md`, but the config that actually ships is different:

- `boards/waveshare-s3.yaml:66-72` (the block commented `# RS485 / Modbus`) defines `modbus_uart` with **`baud_rate: 38400`, `parity: EVEN`** (comments in-file say "default to 8E1").
- `devices/climate-control.yaml:70-72` wires `modbus: uart_id: modbus_uart` — so the main HVAC entry point's Modbus transport is **38400 8E1**, not 9600 8N1.
- Meanwhile `boards/a6.yaml:14` and `boards/a16.yaml:14` use `baud_rate: 9600` (no parity → ESPHome default 8N1), and `components/mev_modbus.yaml:33` documents its device as "9600 baud, 8N1".

So "9600 8N1" is true of the A6/A16 board files and the MEV comment, false of the current master (`waveshare-s3` + `climate-control`). The Stack table claims to describe "existing reality, unchanged by this spine" — this row was asserted from docs, not reality-checked.

**Fix:** either state both configurations (A6/A16 legacy at 9600 8N1; waveshare-s3 master bus at 38400 8E1) or drop the row's precision. Note in passing: the repo itself is internally inconsistent here — `mev_modbus.yaml` attaches an allegedly-9600-8N1 device to the same `rs485_bus` that `waveshare-s3.yaml` runs at 38400 8E1; one of the two is stale or wrong. That is outside this review's scope but worth a separate look, since it means either the MEV comment or the bus config cannot work as written.

### F-2 (MEDIUM) — Structural seed & deployment envelope place `locals/` and `remotes/` inside `devices/`, but no migration phase moves them

- Spine Structural Seed: `devices/ # ENTRY POINTS (AD-4): climate-control, gateway (+secrets), bridge, room sensors; locals/, remotes/` — i.e. `devices/locals/`, `devices/remotes/`.
- Deployment envelope: "locally from `devices/locals/`, in production via `devices/remotes/`".
- AD-4 rule: entry points "(climate-control, gateway, bridge, room sensors, plus their `locals/` and `remotes/` variants) live in `devices/`".
- Reality: `locals/` and `remotes/` are **top-level directories** today (`/Users/alberto/src/esphome-devices/locals/`, `/Users/alberto/src/esphome-devices/remotes/`), and the Migration Map's six phases contain no `git mv locals devices/locals` (or equivalent). Phase 4 even relies on `remotes/*.yaml` at its current path, and the standing battery invokes `esphome config locals/climate-control.yaml` unchanged through Phase 6.

As written, the spine's cold-start tree is unreachable by the companion plan. **Fix:** either add the move to a phase (with `!secret`/relative-include impact checked — `locals/climate-control.yaml` includes `../devices/...` style paths that would change), or correct the seed/envelope/AD-4 to keep `locals/` and `remotes/` at root.

### F-3 (LOW/MEDIUM) — Migration Map Phase 1 misstates `bindings.py` as a `Path(__file__)`-anchored tool

Phase 1: "Update the registry-relative path anchor in every tool (`generate_nodes.py`, `bindings.py`, `allocate_node.py`, `commission.py`, `check_registry_pushed.py`) ... — all anchor on `Path(__file__)`, so this is one constant per file."

Verified anchors:

- `generate_nodes.py:47` — `ROOT = Path(__file__).resolve().parent.parent  # firmware/` ✓
- `allocate_node.py:21-22` — `HERE = Path(__file__).parent`; `REGISTRY = HERE.parent / "registry"` ✓
- `commission.py:24-25` — `HERE`; `CSV_PATH = HERE.parent / "registry" / "nodes.csv"` ✓
- `check_registry_pushed.py:33` — `FIRMWARE = Path(__file__).resolve().parent.parent`, plus `GUARDED_PATHS` containing `"registry"` ✓
- All three Python tests anchor via `Path(__file__)` ✓
- **`bindings.py` — no `Path(__file__)`, no path constant at all.** It is a pure library; every function takes paths as parameters (`registry/` appears only in docstrings). Nothing in it needs a Phase 1 edit.

Harmless to an attentive executor, but the claim is factually wrong for one of the five named files. **Fix:** drop `bindings.py` from the Phase 1 list (or note it needs only docstring touch-ups).

### F-4 (LOW) — ESPHome Stack row "2026.3.0+ (as pinned by installation)" is only half-pinned

`min_version: 2026.3.0` exists in `boards/base.yaml:3`, `boards/waveshare-s3.yaml:12`, and `devices/wall-sensor.yaml:3` — HVAC side only. No canbus YAML (gateway, bridge, packages, compile test) pins any `min_version`. Additionally `vesta/tests/pyproject.toml:9` pins `esphome==2026.5.3` for the vesta test harness, and the gateway's `.esphome` build cache shows it was last validated with 2026.5.x. The 2026.3.0 floor is therefore a claim about one subsystem's configs, not the repo. **Fix:** reword to "2026.3.0 floor pinned in hvac board configs; canbus configs unpinned; vesta test harness pins 2026.5.3" or similar.

### F-5 (LOW) — Two small Migration Map assertions that a repo check softens

1. **Phase 4:** "any vesta example that cites `components/`" — no vesta example cites the repo's `components/`; the only matches (`vesta/examples/two_zone_radiant_fancoil.yaml`, `mev_two_demand.yaml`) reference vesta-internal `../packages/components/`. The "any" hedge saves it, but as written it invites a pointless hunt.
2. **Phase 3:** "Delete the now-empty top-level `home-assistant/`; port its README content" — there is no `home-assistant/README.md`; the READMEs live at `home-assistant/canbus/README.md` and inside `home-assistant/dashboards/`, and both travel with their folders in Phases 2–3. The step as worded has nothing to port.

---

## 2. Claims verified as accurate (checked against the repo)

### Stack table

| Claim | Verdict |
| --- | --- |
| Python registry tooling stdlib-only | ✓ — imports across `canbus/firmware/tools/*.py` are `argparse, csv, hashlib, json, re, subprocess, sys, pathlib` only; `bindings.py` explicitly hand-rolls a YAML-subset reader to avoid PyYAML ("stdlib-only by project rule") |
| C++17 native tests | ✓ — matches `canbus/CLAUDE.md` battery (`g++ -std=c++17 -Wall -Wextra` on 4 test files, all present in `canbus/firmware/tests/`) |
| CAN 125 kbps, 29-bit extended IDs (ADR-0001) | ✓ — `bit_rate: 125KBPS` + `use_extended_id: true` in `canbus/firmware/packages/base_node.yaml:66-72` and `gateway.yaml:284-290`; `canbus/docs/canbus-smart-home-reference.md` (125 kbps, 29-bit Extended CAN ID); `adrs/0001-can-extended-id-location-as-address.md` exists |
| Home Assistant 2024.x+ | ~ — matches root `CLAUDE.md`; not independently verifiable from the repo, acceptable as a doc-sourced row |

### Path / structure claims

- Registry contents: `canbus/firmware/registry/` holds exactly `nodes.csv`, `node_id_hwm`, `bindings.yaml`, `map.json` ✓ (no README yet — consistent with Phase 1 *adding* one).
- HA artifacts: `home-assistant/canbus/` holds `ha_hold_automations.yaml`, `ha_arbitration_automations.yaml`, `ha_manifest_package.yaml` (+ `README.md`); `home-assistant/dashboards/` holds the HVAC dashboards + installer scripts ✓ — AD-5's split and Phases 2–3 moves are all real files.
- Frozen contract: `_bmad-output/specs/spec-map-json-contract/SPEC.md` exists ✓; it names `components/rooms/**` as the room_slug source (SPEC lines 39, 61), so Phase 4's "update the same path in spec + test" is a real, necessary edit.
- `generate_nodes.py` validates `room_slug` against `components/rooms/**` ✓ (`rooms_dir = ROOT.parent.parent / "components" / "rooms"`, line 124) and **does** write the generated HA manifest to `home-assistant/canbus/ha_manifest_package.yaml` ✓ (line 383: `root.parent.parent / "home-assistant" / "canbus" / ...`) — Phase 3's "teach the generator the new manifest output path" is accurate and required.
- `gateway.yaml` includes protocol headers **by relative path** (`../protocol/canbus_protocol.h`, `node_map.h`, `ha_arbitration.h`, `node_health.h`, `bindings.h`, lines 46-51); `bridge.yaml` likewise (lines 58-60). These would break on the Phase 5 move exactly as the map says; "fix its includes" is a real step ✓.
- Gateway dir carries `secrets.yaml` (untracked), `secrets.yaml.example` (tracked), and its own `.gitignore` ✓ — Phase 5's "+ secrets.yaml, secrets.yaml.example; update .gitignore paths" matches reality (the .gitignore in question is `canbus/firmware/gateway/.gitignore`; root `.gitignore`'s unanchored `secrets.yaml` pattern would also cover the new location).
- `compile_sensor_node.yaml` includes `../packages/base_node.yaml` / `sensor_kit.yaml` relatively ✓ — Phase 6's "update compile_sensor_node.yaml includes" is real.
- Push gate: `check_registry_pushed.py` `GUARDED_PATHS = ["registry", "protocol/node_map.h", "protocol/bindings.h", "../../home-assistant/canbus/ha_manifest_package.yaml"]` ✓ — AD-3's "one push gate covers the whole registry" (plus flashed generated artifacts) is exactly how the code works.
- Gateway relays: gateway is "input-only for now ... actions only LOG (no relays yet)" (gateway.yaml:10,15) ✓ — consistent with the spine's "as ADR-0013 lands" and Phase 5's "when relay outputs become real"; ADR-0013 file exists.
- `remotes/climate-control.yaml` fetches `devices/climate-control.yaml` from GitHub `@main` ✓ — AD-9's atomicity rationale and Phase 4's remote-path note are grounded.
- Spine `sources:` all exist: merge proposal, ADR-0009, ADR-0013, SPEC.md ✓. Phase 1 doc list all exist: `canbus/docs/live-freeze-checklist.md`, `reflash-campaign-runbook.md` ✓.
- Risk register artifacts exist: `.claude/worktrees/` and `canbus/firmware/tools/__pycache__/` ✓.
- AD-6 "map.json → hvac (spec + tests exist)": `test_generate_exports.py` explicitly exercises the frozen contract (FLOOR_SLUGS table, room_slug join key, frozen-additive struct — lines 12, 40, 106, 167-168) ✓.
- AD-10: hvac entity convention matches root `CLAUDE.md`; CAN-/HVAC- prefixes documented there and in `canbus/CLAUDE.md` (LIGHT- is a new decision, correctly presented as such) ✓.
- Current tree matches the "before" state the map assumes: `canbus/firmware/{bridge,gateway,nodes,packages,protocol,registry,tests,tools}`, `devices/{climate-control,room-sensor-soggiorno,wall-sensor}.yaml`, `libs/`, `scripts/` ✓.

### Migration Map battery vs `canbus/CLAUDE.md`

The battery is a verbatim match for all seven test commands (same files, same `g++ -std=c++17 -Wall -Wextra` flags, same output names) plus `compile_sensor_node.yaml` ✓. Two deliberate additions are sound: `esphome config locals/climate-control.yaml` (root CLAUDE.md's validation command) and the push-gate run. One nuance, not a defect: `canbus/CLAUDE.md` scopes idempotence as `git diff --exit-code canbus/firmware`, the map uses unscoped `git diff --exit-code` — the unscoped form is *required* once the manifest lives outside `firmware/` (it already does) and after Phase 1 moves the registry, so the map is actually the more correct of the two.

---

## 3. Observations (no action required)

- **Phase 6 flatten leaves `canbus/firmware/README.md` behind** — the mv list is `{protocol,packages,nodes,tools,tests}`; `firmware/README.md` (cited by `canbus/CLAUDE.md` as "operational detail") and `firmware/.gitignore` need a home too. "Update ... all docs" arguably covers it, but naming it would prevent an orphaned `firmware/` stub.
- **AD-4's "the gateway hosts infra + lighting today"** is defensible-but-generous: the gateway compiles the binding manifest hash and fallback gate but actuates nothing (log-only). The spine's own Phase 5 wording is more precise.
- The intra-repo Modbus mismatch surfaced under F-1 (MEV documented 9600 8N1 on a bus configured 38400 8E1) predates this spine and is worth an independent check before the master-controller swap decision.

---

## 4. Verdict

**pass-with-fixes.** The document's central claims — registry mechanics, generator behavior, contract spec, test battery, relative-include breakage, push-gate scope, CAN parameters, stdlib/C++17 tooling — were all verified against the code and hold. Fix F-1 (Modbus row) and F-2 (locals/remotes placement vs migration plan) before treating the spine as binding; F-3–F-5 are wording corrections.
