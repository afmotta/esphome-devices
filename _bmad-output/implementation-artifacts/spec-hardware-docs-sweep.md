---
title: 'Hardware docs sweep — retire Kincony/KC868 references, fix gateway hardware description, commissioning tooling'
type: 'chore'
created: '2026-07-10'
status: 'in-review'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
baseline_commit: 'cce72099c0c32a6bb43aa0740250e3c84a0f1df5'
final_revision: ''
context: ['{project-root}/_bmad-output/planning-artifacts/adrs/0014-standardized-controller-modbus-io-hardware.md', '{project-root}/_bmad-output/implementation-artifacts/spec-hvac-controller-swap-t-connect-pro.md', '{project-root}/_bmad-output/implementation-artifacts/spec-light-gateway-swap-t-connect-pro.md', '{project-root}/_bmad-output/implementation-artifacts/spec-light-fallback-actuation.md']
warnings: []
---

<intent-contract>

## Intent

**Problem:** Once P3-P5 land, several documents still describe hardware that no longer
exists: root `CLAUDE.md`'s Hardware table (Kincony KC868-A6/A16, a stale XY-MD02 Modbus
room-sensor claim), `canbus/CLAUDE.md` and `canbus/docs/canbus-smart-home-reference.md`'s
gateway description (both cite the Waveshare ESP32-S3-POE with CAN on GPIO2/3 — which never
matched the deployed `devices/gateway.yaml` either, a pre-existing three-way discrepancy this
epic finally resolves by replacing the board entirely), `lighting/CLAUDE.md`'s "no relay
actuation exists yet" / "physical split" wording (both resolved by ADR-0014), the
`docs/change_modbus_address*.yaml` utilities (hardcoded to KC868-A6/A16 UART pins and a
different device's Modbus register than any Waveshare board this house now uses), and
`devices/secrets.yaml.example` (missing the `encryption_key`/`github_username`/`github_pat`
keys the climate-control locals/remotes wrappers already reference). The orphaned
`boards/a6*.yaml`/`a16*.yaml` files (zero consumers, confirmed by repo-wide grep before P1)
are also still sitting in the tree.

**Approach:** A sweep, not a rewrite — most of this is surgical correction of specific
sections/lines, not wholesale document regeneration. Each file below has its own precise
task; several long documents (`docs/rs485-wiring-guide.md`) keep their generic
educational content untouched and only get their project-specific (KC868/topology/baud)
sections corrected.

## Boundaries & Constraints

**Always:**
- Run this phase **after P3, P4, and P5** — it documents what they built; running it earlier
  means guessing at details those specs pin precisely (exact pins, exact relay-id numbering,
  exact framework choice).
- Where a claim can't be verified without hardware in hand (e.g. the Waveshare Analog Output
  8CH (B)'s address-configuration register — ADR-0014 confirms the *relay* board's is holding
  register `0x4000` via FC 0x06, but the analog board's equivalent register was never
  independently confirmed during planning), say so explicitly in the doc/comment rather than
  asserting an unverified register number as fact.
- One commit (AD-9): the deletions and the doc corrections land together, and a final
  repo-wide grep for the deleted files' names comes back clean.

**Block If:** none.

**Never:**
- Do not touch `hvac/CLAUDE.md`'s Appendices A-C or "Master/Slave Pattern" section — those
  are P3's job, already scoped there. If you find them still stale when this phase runs,
  that means P3 didn't land as specified — fix it by re-running P3's task, not by duplicating
  the work here under a different spec.
- Do not rewrite `docs/rs485-wiring-guide.md`'s generic RS485 theory (signaling basics,
  cable requirements, termination theory, generic troubleshooting) — only its
  project-specific topology/pin/baud sections are stale; the rest is accurate reference
  material regardless of which boards are on the bus.
- Do not invent cable-length measurements for the new topology in
  `docs/rs485-wiring-guide.md`'s "This Project's Cable Lengths" table — the physical
  installation hasn't happened yet; mark that table as pending re-measurement instead of
  guessing numbers.
- Do not touch the frozen `canbus/_bmad-output/` tree (AD-1) — every doc named above is
  either at repo root, or a live (non-frozen) file under `canbus/docs/`/`canbus/CLAUDE.md`.
- Do not add a version bump or compatibility shim.

</intent-contract>

## Code Map

1. **Root `CLAUDE.md`** — Hardware table (`### Hardware` under Project Overview): replace
   the Kincony KC868-A6/KC868-A16 rows with LilyGO T-Connect Pro (both controllers),
   Waveshare Modbus RTU Relay 32CH, Waveshare Modbus RTU Analog Output 8CH (B); keep
   WaveShare ESP32-S3-POE only if still accurate for anything else in the repo (it isn't,
   post P3/P4 — remove it), keep S1 Pro Multi-Sense unchanged (unrelated to this epic).
   Remove the "XY-MD02 Modbus Sensors: Room temperature/humidity sensors" row — room sensor
   data is HA-primary/UDP-secondary (`hvac/room_sensors.yaml`'s failover, unrelated to this
   epic but adjacent and already known-stale), not Modbus room sensors. Under System
   Capabilities, correct "Autonomous operation: RS485 Modbus RTU communication between
   boards for operation without Home Assistant" — there is one Modbus master, not
   board-to-board communication; the true autonomy story is that relay/analog/MEV actuation
   runs entirely on the one controller regardless of HA, while room-sensor data specifically
   depends on the HA→UDP failover chain. Add a Changelog row (next version, e.g. 1.5) noting
   the hardware standardization.
2. **`canbus/CLAUDE.md`** — "Design principle" section's parenthetical "(Waveshare
   ESP32-S3-POE, TWAI CAN over PoE Ethernet)" → "(LilyGO T-Connect Pro, TWAI CAN over
   Ethernet)".
3. **`canbus/docs/canbus-smart-home-reference.md`** — the gateway hardware description
   ("Gateway: Waveshare ESP32-S3-POE-ETH-8DI-8DO... TWAI CAN controller (GPIO2 TX, GPIO3
   RX)" plus its W5500 pin list) — replace with the LilyGO T-Connect Pro's actual, verified
   pins: CAN TX=IO6/RX=IO7; W5500 SCLK=IO12, MOSI=IO11, MISO=IO13, CS=IO10, INT=IO9,
   RST=IO48. This retires the three-way gateway-hardware discrepancy this repo has carried
   (docs said POE-ETH+GPIO2/3; the deployed config was WiFi RS485-CAN+GPIO15/16; neither
   matched) — after P4 there is exactly one true description, and this is where it lives.
4. **`lighting/CLAUDE.md`** — the header note "It is **pre-live**: no relay actuation exists
   yet (ADR-0013 open item 2 — fallback is log-only)... relay outputs land with ADR-0013's
   hardware decision, which also triggers the intended physical split onto a dedicated
   lighting gateway device" is resolved twice over by this point: relay actuation exists
   (P4/P5), and ADR-0014 resolved the physical-split question as *no further split* — the
   gateway keeps composing canbus + lighting packages on one device (AD-4). Rewrite this
   paragraph to state both facts plainly and drop the "pending" framing. (The system stays
   pre-live in the sense that no bindings are authored yet — keep that part.)
5. **`docs/change_modbus_address.yaml`** and **`docs/change_modbus_address_simple.yaml`** —
   both hardcode KC868-A6/A16 UART pins (`GPIO27/14`, `GPIO13/16`) and target a generic
   0-10V adapter's register `0x0000` at 9600 baud — a device this house no longer uses (the
   Waveshare boards are the standardized peripherals now). Retire both files (`git rm`) —
   they document a commissioning procedure for hardware that's gone, and AD-9 is explicit
   that pre-live cleanups don't need a deprecation period. Replace with **one** new utility,
   `docs/change_waveshare_relay_address.yaml`, targeting the Relay 32CH's confirmed
   addressing procedure: holding register `0x4000`, FC `0x06`, works when addressed at
   broadcast address `0x00` — model its structure on the retired `change_modbus_address.yaml`
   (same shape: isolated single-device UART/modbus/api/ota scaffolding, a button that writes
   the new address, a status text_sensor) but with T-Connect Pro RS485 pins (IO17/IO18) and
   the relay board's real register. Add a code comment flagging that the Analog Output 8CH
   (B) board's own address-configuration register was **not independently verified** during
   ADR-0014's planning (only the relay board's `0x4000` was) — confirm against its physical
   manual before reusing this same script for the analog board.
6. **`docs/rs485-wiring-guide.md`** — surgical fixes only:
   - "This Project's Topology" section (KC868-A6/A16 diagram, room-sensor addresses 0x0A-0x0D,
     0-10V adapter at 0x1E): replace with the new topology — one T-Connect Pro master per
     system, Relay 32CH bank(s), Analog 8CH (B) (hvac only), MEV (hvac only, unchanged
     address `0x10`) — using the mirrored-address scheme from ADR-0014 §4.
   - "KC868-A6 (Master) Terminal Block" / "KC868-A16 (Slaves) Terminal Block" / "Room Sensors
     (XY-MD02) Terminal Block" wiring tables: replace with the T-Connect Pro's RS485 terminal
     description and the Waveshare boards' terminal blocks (consult their manuals for exact
     terminal labels if available; otherwise mark as pending verification rather than
     guessing).
   - "This Project's Cable Lengths" table: mark as **pending re-measurement** — the physical
     installation for the new topology hasn't happened; don't invent numbers.
   - Baud-rate-specific troubleshooting text that says "(must be 9600)": note the live bus
     runs 38400 8E1 (per ADR-0014 §4), pending the bring-up parity check that same section
     documents as an open item.
   - Leave every other section (RS485 signaling basics, cable requirements, termination
     theory, generic troubleshooting decision trees, RS485 standard limits table) untouched.
7. **`devices/secrets.yaml.example`** — add the two currently-missing keys the
   `devices/locals/climate-control.yaml` / `devices/remotes/climate-control.yaml` wrappers
   already reference: `encryption_key` (distinct from the gateway's own `api_encryption_key`
   — each ESPHome device has its own API encryption key; add a comment on each noting which
   device(s) it belongs to) and, for the `remotes/` GitHub-pull path, `github_username` and
   `github_pat`. Do not rename `api_encryption_key` or touch `devices/gateway.yaml` — this is
   purely completing the example template to match what already-existing consumers need.
8. **Delete `boards/a6.yaml`, `boards/a6_ethernet.yaml`, `boards/a16.yaml`,
   `boards/a16_ethernet.yaml`** — confirmed zero consumers (no `devices/*.yaml` entry point
   includes any of them; verified by repo-wide grep before P1 started). `git rm` all four.
9. **`_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md`**
   — Deferred table: mark three rows resolved (this is the live spine doc, not the frozen
   canbus tree — editing it is in scope):
   - "Master-controller swap (Lilygo T-Connect PRO)" → resolved by ADR-0014, implemented
     P3 (hvac) / P4 (lighting gateway).
   - "Physical gateway split..." → resolved: no further split. The gateway continues
     composing canbus + lighting packages on one device (AD-4); HVAC was already a separate
     physical device. ADR-0014 made this an explicit decision rather than an open question.
   - "boards/ package unification (gateway vs climate master, both Waveshare family)" →
     resolved as a **byproduct**, matching the row's own "let it fall out, don't force it"
     philosophy: both entry points now compose the same `boards/t-connect-pro.yaml`, not
     because unification was pursued, but because the hardware standardization made the
     boards identical.

## Tasks & Acceptance

**Execution:**
- [x] Confirm P3, P4, P5 have landed (their specs' `Auto Run Result` status is not
  `ready-for-dev`) before starting — this phase documents their actual outcomes
- [x] Root `CLAUDE.md` Hardware table + System Capabilities autonomy bullet + Changelog row
- [x] `canbus/CLAUDE.md` gateway parenthetical
- [x] `canbus/docs/canbus-smart-home-reference.md` gateway hardware description
- [x] `lighting/CLAUDE.md` pre-live/relay/physical-split paragraph
- [x] Retire `docs/change_modbus_address.yaml` + `docs/change_modbus_address_simple.yaml`;
  add `docs/change_waveshare_relay_address.yaml`
- [x] `docs/rs485-wiring-guide.md` surgical fixes (topology, terminal blocks, cable-length
  table marked pending, baud-rate note)
- [x] `devices/secrets.yaml.example` — add `encryption_key`, `github_username`, `github_pat`
- [x] `git rm boards/a6.yaml boards/a6_ethernet.yaml boards/a16.yaml boards/a16_ethernet.yaml`
- [x] `ARCHITECTURE-SPINE.md` Deferred table — three rows annotated resolved
- [x] Repo-wide grep sweep for the deleted files' names and for remaining "KC868"/"Kincony"/
  "XY-MD02" references outside frozen/historical trees

**Acceptance Criteria:**
- Given a repo-wide grep for `KC868|Kincony` outside `_bmad-output/`, `.ai/`,
  `docs/modbus-register-map.md` (a frozen historical document about Gen-1 hardware, out of
  this sweep's scope by name), and `vesta/docs/modbus-relay-board.md`'s generic "works with
  boards like the KC868-A16" compatibility note (accurate — the driver genuinely is generic,
  not a claim about this house's hardware), when run after this spec, then no other hits
  remain.
- Given `boards/a6.yaml`, `boards/a6_ethernet.yaml`, `boards/a16.yaml`,
  `boards/a16_ethernet.yaml`, when checked after this spec, then none exist, and a
  repo-wide grep for `boards/a6\.yaml|boards/a16\.yaml` returns no hits.
- Given `canbus/docs/canbus-smart-home-reference.md` and `canbus/CLAUDE.md` after this spec,
  when their gateway hardware descriptions are compared against `devices/gateway.yaml`
  (post-P4), then they match exactly — one true description, not three.
- Given `devices/secrets.yaml.example` after this spec, when compared against every
  `!secret <name>` reference in `devices/`, `devices/locals/`, `devices/remotes/`, then every
  referenced secret name appears in the example with a comment.
- Given `esphome config devices/locals/climate-control.yaml` and
  `esphome compile devices/gateway.yaml`, when run after this spec (docs-only changes, no
  YAML entry point touched), then both still pass exactly as they did after P3/P4/P5.

## Design Notes

This is the only phase that touches `ARCHITECTURE-SPINE.md` — every prior phase in this
epic left it alone since none of them needed to *re-decide* anything the spine already
recorded; this phase just closes out rows the spine explicitly marked as waiting on ADR-0014.

**The new commissioning utility is compile-verified, not just config-verified.** The
retired `change_modbus_address_simple.yaml` used a `modbus_controller.write_register`
action that does not exist in ESPHome, and the main retired file called
`controller->create_register_write_multiple_command(...)` as a member method — neither
could ever have compiled. The replacement uses the real API
(`ModbusCommandItem::create_write_single_command` + `queue_command`, FC 0x06) and was
built end-to-end with `esphome compile` on the esp32s3/esp-idf target before landing. It
is deliberately self-contained (placeholder WiFi, no `!secret`): `docs/` has no
`secrets.yaml`, so the retired files' `!secret` references could never resolve from where
they lived — a bench tool should flash without the repo's secret infrastructure.

**`vesta/README.md` is inside the `vesta` git submodule.** The one-line reword there
needs its own commit in `afmotta/vesta` plus a gitlink bump in this repo's sweep commit —
the same two-step P2 already followed for the 32-ch driver. Flagged so the final commit
doesn't silently leave the submodule dirty.

**One spec-internal inconsistency resolved in the AC's favor:** the first acceptance
criterion exempts `.ai/` as historical, but the Verification section's second grep
command omits that exclusion. The `.ai/story-1.*-summary.md` files (frozen 2025 story
records, "no modifications" notes) mention `boards/a6.yaml`/`a16.yaml`; editing frozen
story summaries to satisfy a grep would falsify history, so `.ai/` is treated as exempt
in both greps, matching the AC prose.

**Gen-1 wiring-guide figures were not carried anywhere:** the cable-length table was
replaced by an explicit "pending re-measurement" note (per Boundaries), and the RS485
length-limit framing moved from "9600 → 1200m" to the live "38400 target → 500m", which
remains a comfortable house-scale margin.

## Verification

**Commands:**
- `grep -rn "KC868\|Kincony" --include="*.md" --include="*.yaml" . | grep -v "_bmad-output\|\.ai/\|worktrees\|modbus-register-map.md\|vesta/docs/modbus-relay-board.md"` -- expected: no hits
- `grep -rn "boards/a6\.yaml\|boards/a16\.yaml\|boards/a6_ethernet\|boards/a16_ethernet" . | grep -v "_bmad-output\|worktrees"` -- expected: no hits
- `ls boards/ | grep -i "a6\|a16"` -- expected: no output
- `esphome config devices/locals/climate-control.yaml` -- expected: exits 0
- `esphome compile devices/gateway.yaml` -- expected: exits 0
- `git diff --stat` -- confirm only the files named in the Code Map changed, plus the four
  `boards/a*.yaml` deletions

**Manual checks (if no CLI):**
- Read `canbus/docs/canbus-smart-home-reference.md`'s gateway section against this spec's
  verified pin table: confirm every pin matches.

## Spec Change Log

### 2026-07-11 — Scope amendments during execution (documented, not silent)

1. **`boards/waveshare-s3.yaml` + `-ethernet`/`-wifi` deleted alongside a6/a16.** P3's
   review triage explicitly flagged these to this phase via `deferred-work.md` ("flagging
   here so P6's scope gets amended to include it") — they were orphaned by P3's board swap
   through the exact mechanism that orphaned a6/a16. Zero consumers re-confirmed by
   repo-wide grep before deletion.
2. **`.github/copilot-instructions.md` example path updated** (`boards/a6.yaml` →
   `boards/t-connect-pro.yaml`): the file's live "Key concepts" section cited a deleted
   file; the acceptance grep for deleted-file references would otherwise fail.
3. **`vesta/README.md` driver-table row reworded** ("e.g., Kincony KC868" → generic
   Modbus RTU wording): the first acceptance criterion exempts
   `vesta/docs/modbus-relay-board.md`'s generic compatibility note by name but not this
   equivalent README row; reworded rather than exempted, also picking up the P2-added
   32-channel aggregator.
4. **Historical banners added to `docs/deployment-guide.md`,
   `docs/sensor-technology-selection.md`, and `docs/0-10v-adapter-setup-guide.md`**: the
   first two carry XY-MD02/Gen-1 content that the task-list grep tolerates only "outside
   frozen/historical trees" — the banners make that classification explicit instead of
   implied. The third documents commissioning the retired 0-10V adapter whose companion
   utilities this spec deletes; leaving it unmarked while deleting its utilities would be
   incoherent.
5. **Root `CLAUDE.md` fixes beyond the Code Map's three named spots**, all forced by the
   same staleness class or by the deletions: repo-tree/naming-example/hierarchy/important-
   files references to deleted board files; the root file's own "Master/Slave Pattern"
   section (KC868 master/slave — the AC grep would fail on it; distinct from
   `hvac/CLAUDE.md`'s, which P3 already rewrote and which stays untouched); the 3-tier
   failover description (Modbus-primary → the live HA→UDP→Emergency chain, per this spec's
   own Intent framing); the "controller hardware is not yet finalized" claim (aligned to
   `hvac/CLAUDE.md`'s P3-corrected phrasing); ESPHome floor 2026.3.0 → 2026.5.0 (set by
   `boards/t-connect-pro.yaml` since P3); Language-table context notes for the retired
   `gruppo miscelazione`/`distribuzione` device names.
6. **`boards/base.yaml` and `boards/wifi.yaml` newly orphaned — flagged, not deleted.**
   Their only consumers were the deleted `a6.yaml`/`a16.yaml`. Following P3's own
   precedent (flag orphans to a later pass rather than deleting opportunistically
   mid-spec), they are marked "no current consumer" in root `CLAUDE.md`'s tree and left
   in place; deletion deferred (see Review Triage Log).

## Review Triage Log

## Auto Run Result

Status: ready-for-dev — not yet executed.
