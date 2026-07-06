# Adversarial Review — ARCHITECTURE-SPINE.md (esphome-devices layered restructure)

| Field | Value |
|---|---|
| Target | `_bmad-output/planning-artifacts/architecture/architecture-esphome-devices-2026-07-05/ARCHITECTURE-SPINE.md` (+ `MIGRATION-MAP.md`) |
| Lens | ADVERSARY — construct pairs of units that each obey every AD to the letter yet build incompatibly |
| Date | 2026-07-05 |
| Verdict | **pass-with-fixes** — the layering and contract instincts are sound, but six seams admit letter-compliant incompatible builds; one is on the critical path of the very next LIGHT epic |

Method: for each finding I construct two concrete units one level down (a future LIGHT-epic
vs CAN-epic, or two independent implementers of adjacent slices), show each unit citing the
AD text it satisfies, show the collision, then propose the tightened or new AD that closes it.
Repo state was verified against actual code (`canbus/firmware/tools/bindings.py`,
`generate_nodes.py`, `registry/bindings.yaml`, `boards/`, `devices/`) — several attacks are
grounded in code that already exists, not hypotheticals.

---

## F1 — CRITICAL — The generator is a three-system choke point and AD-3 gives no rule for composite changes

**Attack.** `generate_nodes.py` today simultaneously (a) parses and validates lighting's
`bindings.yaml` (via `bindings.py`), (b) validates canbus's `nodes.csv`, (c) validates
`room_slug` against hvac's `components/rooms/**` glob, (d) stamps `protocol/bindings.h`,
(e) emits `map.json` under hvac's frozen contract. AD-3 says: *"A schema change requires
its file's owner; a mechanism change requires canbus."* Nearly every non-trivial lighting
schema change is **both**.

Two units, both letter-compliant:

- **LIGHT-Epic 2** ("per-relay ops" — literally ADR-0009 open item 1, the deferred PyYAML
  decision): lighting owns `bindings.yaml` schema (AD-3), so the implementer edits the
  schema comment block, extends the parser in `bindings.py`, and adjusts `canonical_hash()`
  so the new nested shape hashes stably. Every touched behavior is "what the bytes mean"
  — lighting's territory per AD-7's own words ("lighting owns what the bytes mean (schema,
  ops, fan-out)").
- **CAN-Epic 7** ("registry mechanism hardening"): canbus owns the mechanism (AD-3:
  generator, canonicalization, hash), so the implementer refactors `bindings.py`'s
  reader/canonicalizer — say, tightening the strict no-nesting reader that per-relay ops
  just relaxed.

Both epics edit the same functions in the same file under different prefixes, each holding
an AD-3 sentence that says the file is theirs. There is no rule naming who may edit
`generate_nodes.py`/`bindings.py` when a lighting schema change needs generator support,
no rule for which epic prefix the composite change carries (AD-10 lists three prefixes and
no tie-breaker), and no rule for whether the schema-parsing layer inside canbus-owned code
is schema (lighting) or mechanism (canbus).

**Why critical:** this is not a tail risk — it is the *next* lighting work item (ADR-0009
open item 1 and ADR-0013 open item 2 both route through this code), and the spine ships
with the collision unresolved.

**Close it — tighten AD-3 (add):**
> The generator's schema-facing layer is itself an AD-6 contract: the parsed-binding shape
> (`parse_relays` output, the strict-reader guarantees, the canonical form) is frozen in a
> spec owned jointly at the seam. A change to what `bindings.yaml` may express is a
> **lighting schema change carried as a LIGHT epic**, but any edit it requires inside
> `tools/` (parser, canonicalizer, hash) is a **mechanism slice inside that epic that
> requires canbus sign-off** (in practice: the same person wearing the canbus hat, but the
> commit message names both `LIGHT-Epic N` and the mechanism-contract spec it updates).
> Concurrent CAN mechanism epics may not touch schema-facing functions while a LIGHT schema
> epic is open, and vice versa — one seam, one epic at a time.

---

## F2 — HIGH — AD-7's "semantics-blind" hash is already false in code, and canonicalization-relevant schema changes have no gate

**Attack.** AD-7: *"canbus … hashes canonical bytes without interpreting them"*, and
*"lighting never re-canonicalizes"*. But `canonical_hash()` in `bindings.py` **interprets
every field**: it normalizes the `relay` scalar into a sorted de-duplicated int list, sorts
bindings by `(node_id, button, event)`, sorts object keys, and injects `schema_version`.
Canonicalization is schema-aware by construction — it cannot be otherwise for a YAML
manifest. So the AD-7 division of labor ("infra is blind, lighting owns meaning") is a
fiction, and the fiction has teeth:

- **Lighting implementer** adds an optional field with a default (say `dimmable: false`,
  omittable). Obeying AD-7 to the letter — never touching canonicalization — they document
  that omitted means false. Bindings authored with the explicit default and without it are
  semantically identical but hash differently: `manifest_hash` disagreement between a
  gateway flashed before the doc change and HA regenerated after it. `ha_ready` flaps.
  Lighting complied ("owns what the bytes mean"); canbus complied ("hashed without
  interpreting").
- **Canbus implementer**, owning canonicalization, "improves" it (e.g. drops the vestigial
  `event` sort key — the schema comment in `bindings.yaml` says bindings carry no `event`
  field, yet `canonical_hash` sorts by it). Pure mechanism change per AD-3; hash of an
  unchanged `bindings.yaml` changes; lighting's fallback behavior gates on a hash it never
  touched.

**Close it — tighten AD-7:**
> Delete "without interpreting them" — it is untrue and the untruth hides the seam. Replace
> with: canonicalization is a **schema-coupled mechanism**: its definition (field set, sort
> keys, normalization rules, treatment of optional fields/defaults) is a frozen AD-6
> contract (`spec-bindings-canonical-form`) with a golden-hash drift test (fixed input
> file → fixed hash). Any change to canonical bytes — whether it originates as a lighting
> schema edit or a canbus mechanism edit — updates that spec, its test, and every hash
> consumer (bindings.h stamp, HA manifest package, gateway) **in one commit** (AD-9).
> Optional-with-default fields are forbidden in `bindings.yaml` unless the canonical form
> explicitly materializes the default. Do not wait for Phase 5 to write this spec — the
> Phase 5 `BindingEntry`/`bindings.h` contract covers the *compiled* surface, not the
> canonical-form surface, and F2's attacks live entirely in the latter.

---

## F3 — HIGH — `boards/` has no owner, no change gate, and the spine defers exactly the event that weaponizes it

**Attack.** AD-1 names `boards/` a home; no AD assigns ownership or edit rules; the
Deferred table explicitly anticipates gateway and climate master converging on shared
Waveshare board packages ("let it fall out, don't force it"). The moment it falls out:

- **HVAC-Epic** implementer edits `boards/base.yaml` (today included by every climate
  device via the board packages) — bumps logger to DEBUG for Modbus troubleshooting, or
  reworks the `api:` block for the failover tiers. AD-1 satisfied (file stays in its home);
  AD-4 satisfied (it's not an entry point); no other AD binds them.
- **LIGHT/CAN-Epic** implementer, post-unification, includes the same `waveshare-s3.yaml`/
  `base.yaml` from `devices/gateway.yaml` and edits it for gateway needs (CAN driver
  pin muxing, api reboot timeout for `ha_ready` semantics).

Each edit compiles the editor's own entry point; neither AD nor the verification battery
compiles the *other* system's entry points (the battery runs `esphome config
locals/climate-control.yaml` + the sensor-node compile — post-Phase-5 gateway/bridge
compiles are added, but nothing says a `boards/` edit must run all of them). Two systems
mutate one shared file with no contract, the exact "implicit contract drifting silently"
AD-6 exists to kill — but AD-6 only triggers on things someone has recognized as a
cross-system boundary, and nobody files a frozen spec for a logger block.

**Close it — new AD (AD-11, boards ownership):**
> `boards/` is composition-layer territory, steward: whoever the root CLAUDE.md names
> (default: devices/entry-point owner = the human, not a system). Rule: any edit under
> `boards/` must end with `esphome config` (minimum) of **every** entry point in `devices/`
> that transitively includes the touched file — add a `boards-touched` clause to the AD-9
> battery. A system needing board-level behavior that another system's entry points must
> not inherit puts it in `<system>/packages/`, never in `boards/`.

---

## F4 — HIGH — "Frozen" contracts have no change procedure, and the repo's own pre-live norm lets the non-owner unfreeze them

**Attack.** AD-6 freezes contracts; AD-3 says hvac owns the map.json contract. But this
repo's standing pre-live discipline (AD-9, PROTO-version policy, "no shims — edit schema
constant and file together, fail loudly") authorizes in-place breaking changes landed
atomically. Watch two letter-compliant implementers:

- **LIGHT-Epic** adds a binding capability that changes `map.json` shape (new column via
  the generator). The contract test fails; the implementer — following AD-9's "a move and
  every consumer land in one commit" and the house norm that pre-live breaking changes are
  made in place — edits `spec-map-json-contract`, the generator, and the test **in one
  commit**. Fully compliant with every written rule: AD-6 says a contract needs a spec and
  a drift test, and after the commit it still has both.
- **HVAC-Epic** implementer builds the CAN-frame consumer against the spec as frozen,
  believing "frozen per spec-map-json-contract" (AD-3's words) means *immutable without
  hvac*. Their consumer and lighting's export drift in the same week; each side holds a
  green test at their commit.

The Migration Map even models the loophole: Phase 4 has canbus editing the hvac-owned
spec (the rooms-glob path) unilaterally, correctly calling it "an AD-6 contract edit" —
proving non-owners already edit owned specs with no ack step defined.

**Close it — tighten AD-6 (add):**
> "Frozen" means: the spec file changes only in a commit whose epic prefix is the
> **owning** system's, or that carries an explicit owner ack line
> (`Contract-Ack: hvac`) in the commit message. Mechanical, greppable, push-gate-checkable.
> A change originating in another system is proposed by touching code + test in a branch,
> but cannot land until the spec commit satisfies the ack rule. (Phase 4's glob edit is
> fine — just make it carry the ack line, establishing the pattern.)

---

## F5 — MEDIUM — AD-5 has no home for automations that span two systems

**Attack.** "Button 3 double-click sets the soggiorno fancoil to boost." An HA automation
triggered by a canbus button event (double-click is HA-only by design — ADR/bindings.yaml
say gestures beyond single-click exist *only* as HA behavior) that mutates an hvac climate
entity. Three defensible homes under AD-5's letter:

- `canbus/home-assistant/` — "it consumes the canbus HA event surface, and canbus already
  hosts event-adjacent automations (arbitration)".
- `lighting/home-assistant/` — "button gesture semantics are what lighting does; hold
  automations already live here, this is the same shape with a different target".
- `hvac/home-assistant/` — "it encodes climate behavior; AD-5's own stated purpose is
  automations living with the system whose *behavior they encode*".

Two implementers each create one — now the same physical click drives the same climate
entity through **two** automations in two homes (two owners of one entity, conflicting
state-mutation paths), or the automation lands in a home the other system's maintainer
never looks at when changing the event payload. AD-2 makes it worse: "lighting and hvac
never depend on each other — they interact only through the registry and AD-6 contracts"
— an HA automation binding a button to a fancoil *is* lateral app-to-app coupling with no
registry file and no AD-6 contract naming the event payload.

**Close it — tighten AD-5 (add) + AD-6 instance:**
> A spanning automation lives with the system it **actuates** (effect side), and consumes
> the trigger side only through a frozen AD-6 contract. Concretely: button→HVAC automations
> live in `hvac/home-assistant/`; the canbus HA event payload (event type, fields, gesture
> names) becomes a named AD-6 contract instance with a drift test the moment the first
> cross-system consumer exists — same trigger condition as the ADR-0006 sensor-frame
> contract already listed in AD-6. One actuated entity, one automation, one home.

---

## F6 — MEDIUM — AD-4's "hand-maintained deployable entry point" is not decidable at the edges, and the migration map already contradicts a literal reading

**Attack.** AD-4: hand-maintained deployable entry points live in `devices/`. Probe the
boundary:

- `canbus/firmware/tests/compile_sensor_node.yaml` — hand-maintained, composes packages,
  flashable to a board. A literal reader puts it in `devices/`; the Migration Map keeps it
  in `canbus/tests/`. Both readings cite AD-4.
- `vesta/examples/two_zone_radiant_fancoil.yaml` — hand-maintained, deployable by design
  (examples exist to be flashed). AD-4 says `devices/`; AD-2 says vesta depends on nothing
  in-repo and is extractable, so its examples must stay inside `vesta/`. Two ADs, two homes
  for one file.
- The first lighting dev-board smoke config (relay outputs, ADR-0013 item 2): implementer
  A creates `devices/lighting-testbench.yaml` ("hand-maintained, deployable, composes
  lighting+canbus packages"); implementer B creates `lighting/tests/compile_relays.yaml`
  ("it's the sensor-node compile-test pattern"). Same artifact, two homes, both compliant
  — and `devices/remotes/` production tooling now globs over a testbench config.

**Close it — tighten AD-4 (define "deployable"):**
> An entry point belongs in `devices/` iff it targets a **house device**: it references
> `secrets.yaml`, carries OTA/production identity, and appears in the `locals/`/`remotes/`
> deployment envelope. Compile-check and dev-board configs are tests: they live in
> `<system>/tests/` and never reference secrets. Library examples are docs: they live in
> `vesta/examples/`, are self-contained per AD-2, and are compile-checked but never
> deployed. Three named categories; every YAML with an `esphome:` block is exactly one.

---

## F7 — MEDIUM — `devices/` entry points are a multi-system mutation surface with no thinness rule and no convention arbiter

**Attack.** Post-Phase-5, `devices/gateway.yaml` composes canbus + lighting packages;
a future master controller composes lighting + hvac (AD-4 says so explicitly). AD-4
"prevents entry points hoarding logic" — prevention prose, not a rule; nothing bounds what
an entry point may contain. Two implementers:

- **LIGHT-Epic** adds fallback relay outputs, and — since the relays are "defined in the
  gateway config, not in this registry" (bindings.yaml's own words) — defines
  `output:`/`switch:` blocks with ids directly in `devices/gateway.yaml`, under lighting's
  entity convention.
- **CAN-Epic** adds a health-status LED to the same file under canbus's convention, plus
  substitutions that collide with lighting's (`status_led`, `relay_1`).

Both cite AD-4 ("entry point composes across systems") and AD-10 ("conventions are
per-system" — but *which* system's convention governs an id defined in a file owned by no
system?). Every future epic on either system queues edits to the same file; entity-id
collisions surface only at compile, and ownership of a given block in the entry point is
archaeology.

**Close it — tighten AD-4 (add):**
> Entry points are **manifests, not programs**: substitutions, `packages:` includes,
> secrets wiring, network selection — nothing else. Any `output:`/`switch:`/`sensor:`/
> lambda block belongs in some system's `packages/` (gateway relay outputs → a
> `lighting/packages/relays_*.yaml` parameterized by pin substitutions, exactly the
> ADR-0013 item-2 shape Phase 5 already gestures at). Consequence: entity ids are always
> defined inside a system package, so AD-10's per-system conventions always have an
> unambiguous governing system, and cross-epic edits to `devices/*.yaml` reduce to
> add/remove of include lines — merge-trivial.

---

## F8 — LOW — Phases 2–4 open a contract-free window on lighting-owned data that infra reads

**Attack.** AD-2: canbus tooling may read application data *only where a frozen contract
names the path*. Phase 2 makes lighting the owner of `bindings.yaml`; the bindings →
arbitration contract spec lands in Phase 5. Between those commits, `generate_nodes.py`
(canbus) reads and validates lighting-owned data with **no** frozen contract — the
migration plan itself violates AD-2 for two phases, and a fast-moving LIGHT-Epic (born in
Phase 2, with F1's schema work on its backlog) can legally change the schema in the window
with no drift test on either side.

**Close it — sequencing rule, not a new AD:**
> Phase 2 additionally freezes the *current* bindings schema: a one-page spec (the schema
> comment block in `bindings.yaml` is already 90% of it) + the golden-hash test from F2.
> Cheap (size XS), and it means lighting is never the owner of an uncontracted seam.
> Alternatively, an explicit line in `lighting/CLAUDE.md`: "schema is change-frozen until
> the Phase 5 contract lands" — weaker but written.

---

## Verdict and priority

**pass-with-fixes.** The spine's skeleton — layered systems, per-file registry ownership,
contracts-with-drift-tests, atomic pre-live moves — survives the attack; none of the
findings require re-architecting. But six seams admit letter-compliant incompatible
builds, and two (F1, F2) sit directly under the first planned lighting work (ADR-0009
item 1, ADR-0013 item 2, Migration Phase 5). Fix order:

| # | Severity | Fix | When |
|---|---|---|---|
| F1 | critical | AD-3 composite-change rule; generator schema layer as AD-6 contract | before any LIGHT schema epic |
| F2 | high | AD-7 rewrite; `spec-bindings-canonical-form` + golden-hash test | Phase 2 (merges with F8) |
| F4 | high | AD-6 owner-ack rule for frozen-spec edits | before Phase 4 (its spec edit sets the precedent) |
| F3 | high | AD-11 boards ownership + all-entry-points compile clause in battery | before board unification "falls out" |
| F5 | medium | AD-5 actuation-side rule; HA event payload contract trigger | before first spanning automation |
| F6 | medium | AD-4 three-category test (device/test/example) | Phase 5 (gateway/bridge move) |
| F7 | medium | AD-4 manifest-not-program rule | Phase 5 (extraction slice) |
| F8 | low | Phase 2 schema freeze (subsumed by F2) | Phase 2 |
