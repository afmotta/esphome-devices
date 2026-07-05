# Proposal: merge `canbus` into `esphome-devices`

**Status:** Implemented 2026-07-05 (merge commit 1dc807f; afmotta/canbus archived)
**Decision:** merge as a history-preserving subtree under `canbus/`, then archive `afmotta/canbus`.

---

## 1. Evaluation — does merging make sense?

**Yes.** These are not two adjacent projects that happen to share a stack; they are two
subsystems of the same house with an explicit integration contract between them.

### Arguments for

1. **Same house, same HA instance, same toolchain.** Both projects target Alberto's
   fienile build (3 floors), deploy via ESPHome, integrate with the same Home Assistant,
   and use the same BMAD development workflow. `esphome-devices` is already the
   umbrella-named repo hosting multiple device families (climate boards, room sensors,
   wall sensor).

2. **A cross-repo contract already exists — and it's the risky kind.**
   - `registry/map.json` is explicitly designed as "the read-only export for non-C
     consumers (HVAC controller, dashboards)", and ADR-0009 open item 5 says its field
     shape must be confirmed *with the HVAC firmware* before freezing. That HVAC firmware
     is `esphome-devices`.
   - The sensor-kit CAN frames (ADR-0006) name "the dedicated HVAC controller, external
     firmware" as their consumer.
   - Today that contract evolves across two repos with no atomic change possible. In one
     repo, a schema change and its consumer update land in the same commit.

3. **The HA-side artifacts want to live together.** `esphome-devices` has a
   `home-assistant/` directory for dashboards and HA config; canbus produces HA-side YAML
   (`ha_hold_automations.yaml`, `ha_arbitration_automations.yaml`, the generated
   `ha_manifest_package.yaml`). One repo = one place to look for "what does my HA import".

4. **The project was born there.** The stale draft `canbus-smart-home-reference.md`
   sitting untracked at the root of `esphome-devices` is the original ideation doc
   (pre-CANBed, "up to 6 buttons" era). The split was an accident of bootstrapping, not a
   design decision.

5. **The push-discipline gate (ADR-0009 §6) survives and gets slightly stronger.**
   `check_registry_pushed.py` checks "registry committed and HEAD pushed" via git; in a
   monorepo the same check covers more of the world. Verified: all tools anchor paths on
   `Path(__file__)`, so they work unchanged from a subdirectory.

### Arguments against (and mitigations)

1. **PR-reference rot.** canbus commit messages reference PRs `#19`–`#26`. After the
   merge, GitHub will hyperlink those to *esphome-devices* PRs with the same numbers.
   *Mitigation:* archive `afmotta/canbus` (read-only) so the real PRs stay browsable, and
   say so in the merge commit message. There are no open PRs or issues to strand
   (verified 2026-07-05).

2. **BMAD collision.** Both repos carry a `_bmad/` framework install and a
   `_bmad-output/` artifact tree, with overlapping epic numbering (HVAC Epics 1–20 vs
   CAN Epics 1–5) and their own `sprint-status.yaml`.
   *Mitigation:* keep the root install as the single framework copy, delete
   `canbus/_bmad/`; leave canbus artifacts under `canbus/_bmad-output/` (they
   cross-reference by relative path); namespace future epic references as **CAN-Epic N**
   vs **HVAC-Epic N**.

3. **Different lifecycles sharing `main`.** `esphome-devices` is a *live production*
   climate system whose `remotes/*.yaml` pull configs from GitHub `@main`; canbus is
   pre-live and churning. A bad merge to `main` is fetchable by production climate
   devices.
   *Mitigation:* the path spaces are fully disjoint (`canbus/` vs everything else), the
   climate remotes reference explicit paths, and canbus already has a live-freeze
   checklist culture. Risk is real but small; the existing "never push untested to
   main" discipline covers it.

4. **Two convention sets.** Different entity-naming conventions, different CLAUDE.md
   contexts. *Mitigation:* conventions are subsystem-scoped by design; a nested
   `canbus/CLAUDE.md` keeps the contexts separate (Claude Code loads nested CLAUDE.md
   files when working in that subtree).

### Alternative considered: stay separate, integrate via `map.json`

ADR-0009 deliberately designed `map.json` as a cross-boundary export, so separate repos
*can* work. But the contract is still provisional (open item 5), the consumer is the
other repo, and both are one-person projects for one house — the coordination overhead of
two repos buys nothing here. Rejected.

---

## 2. Merge plan

### Phase 0 — prep `esphome-devices`

1. Deal with the dirty working tree: commit or stash the `components/room_sensors.yaml`
   modification; decide fate of untracked `devices/test.yaml` / `locals/test.yaml`.
2. Delete the stale root `canbus-smart-home-reference.md` (superseded by
   `canbus/docs/canbus-smart-home-reference.md`, which is current: CANBed RP2040,
   8-button standard set).
3. Make sure `canbus` local repo is fully pushed (it is the system of record for
   bindings until the merge lands).

### Phase 1 — history-preserving subtree merge

Mount the whole canbus repo under a `canbus/` prefix. Do **not** splice its contents into
`boards/`/`devices/`/`components/` — canbus is a self-contained ecosystem (protocol
headers, generator, registry-as-system-of-record, native tests, push gate) whose internal
relative paths all hold under relocation as a unit.

```bash
cd ~/src/esphome-devices
git remote add canbus-local ~/src/canbus
git fetch canbus-local
git merge -s ours --no-commit --allow-unrelated-histories canbus-local/main
git read-tree --prefix=canbus/ -u canbus-local/main
git commit -m "Merge afmotta/canbus as canbus/ subtree (full history; old PR #N refs resolve in the archived repo)"
git remote remove canbus-local
```

Full commit history is preserved (`git log canbus/firmware/...` works; add `--follow`
for renames).

### Phase 2 — de-dup and adapt (one follow-up commit)

- `git rm -r canbus/_bmad/` — root `_bmad/` is the single framework install. Diff the two
  `config.yaml`s first and port anything canbus-specific.
- Drop `canbus/.claude/`, `canbus/.vscode/` after merging any useful
  permissions/settings into the root equivalents.
- Merge `.gitignore` entries into the root file where they're repo-global; nested
  `.gitignore`s (nodes/, gateway/, tests/) stay as they are.
- Add `canbus/CLAUDE.md`: short subsystem guide (dumb nodes / smart gateway principle,
  the generator workflow, "never hand-edit `nodes/`", the push gate, test commands).
- Update root `CLAUDE.md` repository-structure section: add the `canbus/` subtree and a
  one-paragraph description of the second subsystem.
- Fix root-relative paths in canbus docs: `docs/reflash-campaign-runbook.md` and
  `docs/live-freeze-checklist.md` reference `firmware/...` from the old repo root —
  grep and prefix with `canbus/`.
- Verify from the new location:
  - `python3 canbus/firmware/tools/generate_nodes.py` → byte-identical regeneration.
  - `python3 canbus/firmware/tests/test_bindings.py` and `test_generate_exports.py`.
  - `python3 canbus/firmware/tests/test_push_gate.py` and a live
    `python3 canbus/firmware/tools/check_registry_pushed.py` run.
  - Native C++ tests (`test_protocol`, `test_ha_arbitration`, `test_node_health`,
    `test_bridge_forwarding`).
  - `esphome compile canbus/firmware/tests/compile_sensor_node.yaml` and a gateway
    compile (secrets live next to `gateway.yaml`, unaffected by the move).

### Phase 3 — retire the old repo

1. Push merged `main`; re-run the push gate to confirm green.
2. In `afmotta/canbus`: one final commit replacing README content with a pointer —
   "Merged into afmotta/esphome-devices under `canbus/` (full history preserved)" — then
   **archive** the repo on GitHub. PRs #1–#26 stay browsable there.
3. Keep `~/src/canbus` locally until the verification list above is green in the new
   home, then delete it.
4. Note for Claude Code: per-project memory is keyed to the working directory, so the
   canbus session memory does not auto-carry to `~/src/esphome-devices` — copy the memory
   files across (`~/.claude/projects/-Users-alberto-src-canbus/memory/` →
   `-Users-alberto-src-esphome-devices/memory/`) and merge the two `MEMORY.md` indexes.

### Phase 4 — consolidation wins (optional, after the dust settles)

- Move the HA-side canbus YAML (`ha_hold_automations.yaml`,
  `ha_arbitration_automations.yaml`, generated `ha_manifest_package.yaml`) under
  `home-assistant/` next to the dashboards — one directory answers "what does HA import".
  Requires teaching `generate_nodes.py` the new output path.
- Close ADR-0009 open item 5 in-repo: freeze the `map.json` field shape against the
  actual HVAC consumer code.
- The canbus gateway and the climate master are both Waveshare ESP32-S3-POE family;
  a shared board package may fall out naturally, but don't force it — the gateway is
  esp-idf/TWAI-specific.

---

## 3. Epic/sprint numbering going forward

Existing artifacts keep their numbers (they live in separate `_bmad-output` trees).
Future commit messages and sprint docs disambiguate with a prefix: `CAN-Epic 5`,
`HVAC-Epic 21`. The Epic-3-retro status-hygiene gate (mechanical story-close check)
applies to the merged repo as-is.
