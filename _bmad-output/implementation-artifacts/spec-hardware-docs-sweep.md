---
title: 'Hardware docs sweep — retire Kincony/KC868 references, fix gateway hardware description, commissioning tooling'
type: 'chore'
created: '2026-07-10'
status: 'ready-for-dev'
review_loop_iteration: 0
followup_review_recommended: false
baseline_revision: 'bb7f173f4bc9499ce3722d4f164e2013d5441003'
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
- [ ] Confirm P3, P4, P5 have landed (their specs' `Auto Run Result` status is not
  `ready-for-dev`) before starting — this phase documents their actual outcomes
- [ ] Root `CLAUDE.md` Hardware table + System Capabilities autonomy bullet + Changelog row
- [ ] `canbus/CLAUDE.md` gateway parenthetical
- [ ] `canbus/docs/canbus-smart-home-reference.md` gateway hardware description
- [ ] `lighting/CLAUDE.md` pre-live/relay/physical-split paragraph
- [ ] Retire `docs/change_modbus_address.yaml` + `docs/change_modbus_address_simple.yaml`;
  add `docs/change_waveshare_relay_address.yaml`
- [ ] `docs/rs485-wiring-guide.md` surgical fixes (topology, terminal blocks, cable-length
  table marked pending, baud-rate note)
- [ ] `devices/secrets.yaml.example` — add `encryption_key`, `github_username`, `github_pat`
- [ ] `git rm boards/a6.yaml boards/a6_ethernet.yaml boards/a16.yaml boards/a16_ethernet.yaml`
- [ ] `ARCHITECTURE-SPINE.md` Deferred table — three rows annotated resolved
- [ ] Repo-wide grep sweep for the deleted files' names and for remaining "KC868"/"Kincony"/
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

## Review Triage Log

## Auto Run Result

Status: ready-for-dev — not yet executed.
