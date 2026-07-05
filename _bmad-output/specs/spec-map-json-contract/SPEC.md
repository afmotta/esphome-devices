---
id: SPEC-map-json-contract
companions:
  - ../../analysis/map-json-hvac-consumer-gap-analysis.md
  - ../../../canbus/_bmad-output/planning-artifacts/adrs/0009-central-map-binding-manifest-system-of-record.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability only — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Freeze the map.json HVAC-Consumer Contract

## Why

ADR-0009 named `map.json` as the read-only export for non-C consumers (HVAC controller, dashboards) but explicitly left its node field shape provisional — a `NOTE (ADR-0009 open item 5)` in `generate_nodes.py` blocks freezing it until confirmed against the HVAC controller. That confirmation was impossible while canbus and the climate system lived in separate repos with no shared consumer code. The 2026-07-05 subtree merge removed that blocker: this is a mandate to close a named, tracked open item now that the excuse for deferring it is gone. Closing it lets the canbus registry validate its own data against real climate zones instead of free text, and gives the HVAC side a stable, documented field list to build against.

## Capabilities

- **CAP-1**
  - **intent:** The canbus registry can record which climate zone (`room_slug`) each wall-button node belongs to, so any consumer can join canbus placement data to a real climate zone without reading free-text `location` strings.
  - **success:** `nodes.csv` gains an additive `room_slug` column (per the ADR-0009 §2 precedent used for the `sensors` column); `generate_nodes.py` rejects generation if any `sensors=1` node's `room_slug` isn't a known climate zone; `map.json` `nodes[]` entries carry `room_slug`; regenerating an unchanged registry stays byte-identical (existing idempotence test continues to pass).

- **CAP-2**
  - **intent:** A `map.json` consumer can resolve a node's climate floor slug (`ground_floor` / `first_floor` / `second_floor`) without learning canbus's internal numeric floor scheme.
  - **success:** A fixed conversion table (0→`ground_floor`, 1→`first_floor`, 2→`second_floor`) exists and is used wherever a floor slug is derived for a node; given each of canbus's floor values it produces the correct climate slug. Canbus's numeric `floor` field itself is untouched (still map-seed metadata, not flashed).

- **CAP-3**
  - **intent:** Anyone building against `map.json` can tell exactly which fields are covered by the frozen HVAC contract versus free to change for other purposes.
  - **success:** A written frozen-field list exists — `schema_version`, `map_version`, `nodes[].node_id`, `nodes[].room_slug`, `nodes[].location`, `nodes[].sensors` — explicitly excluding `manifest_hash` (ha_ready arbitration, ADR-0009 §3) and `board` (wall-box disambiguation). Changes to the two excluded fields do not require an HVAC-side compatibility review; changes to the frozen list follow the existing frozen-additive rule (fields may be added, never renamed or removed).

- **CAP-4**
  - **intent:** A reader of ADR-0009 §7 sees field names and semantics that match what the generator actually produces, not the original pre-implementation wording.
  - **success:** ADR-0009 §7 is edited so `"(id, floor, room, board, location, sensors)"` reads `"(node_id, floor, room, board, location, sensors)"`, and its `map_version` description changes from "generation timestamp" to a deterministic content digest (SHA-256 over the sorted-keys export body, truncated to 16 hex characters), matching `_digest()` in `generate_nodes.py`.

## Constraints

- **Authority boundary holds (ADR-0009 §7 / ADR-0006 §6):** the HVAC controller only reads `map.json`; it never writes `nodes.csv` or allocates `node_id`s. The `room_slug` column and its validation are canbus-registry-owned.
- **Export stays frozen-additive (ADR-0009 §7):** fields may be added; `node_id` and `map_version` are ratified as-is (CAP-4) and must not be renamed or reinterpreted again without a new spec.
- **`room_slug` values must be real climate zones**, drawn from the room packages under `components/rooms/**` (currently 14 zones across 3 floors) — never invented or freehand strings.
- **Registry stays git-system-of-record (ADR-0009):** the additive column is committed like any other registry change; no out-of-band mapping file that could drift from git history.

## Non-goals

- **How the climate firmware consumes CAN data is not decided here** — neither the transport (direct CAN transceiver on a new controller board vs. relaying through the existing gateway) nor the resulting hardware choice. Parked as a follow-up architecture decision.
- **The climate master controller hardware swap is not decided here** (candidate: Lilygo T-Connect PRO with onboard RS485+CAN, replacing the current Waveshare ESP32-S3-POE board and its PCA9554 relay driver with RS485 Modbus relay boards). Separate follow-up; also affects an undocumented, out-of-repo "Lighting system."
- **The sensor measurement contract (types 1–11, 30 s cadence, 90 s staleness, status-byte semantics) is not added to `map.json`** — it stays as mirrored C++/prose constants in `canbus_protocol.h` and `sensor_kit.yaml`, since the kit is fleet-fixed (ADR-0006) and no node has `sensors=1` in production yet.
- **How CAN-sensed rooms plug into the climate system's 3-tier sensor failover (HA → UDP → Emergency) is not decided here.** A preference was recorded for the follow-up: CAN as the sole source for CAN-equipped rooms, reusing the existing ADR-0011 `node_health.h` "LOST after 90 s" doctrine as the safety net, rather than layering CAN alongside HA/UDP — but this depends on the parked consumption-mechanism decision above and is not binding.
- **No concrete node-to-`room_slug` values are assigned by this spec.** The two rows currently in `nodes.csv` (`node_id` 100/101) are development placeholders, not real deployed nodes; the real registry has yet to be created.

## Success signal

`canbus/firmware/registry/nodes.csv` carries a validated `room_slug` column; `canbus/firmware/registry/map.json` exports `node_id`/`room_slug`/`location`/`sensors` per node as the frozen HVAC-read contract, with floor convertible via a fixed table and `manifest_hash`/`board` explicitly outside the freeze; ADR-0009 §7's text matches the generator's real behavior. A climate-side reader can join any commissioned node to its climate zone using only fields present in `map.json` — no free-text guessing, no reading generator source to understand `map_version`.

## Assumptions

- How the generator sources its "known climate room_slug list" (a hardcoded set vs. reading a shared file) is left as an implementation detail for whoever builds CAP-1 — the spec requires the validation to exist, not a specific mechanism.
- `map_version`'s digest already covers the new `room_slug` column with no format change, since it hashes the sorted-keys export body generically.

## Open Questions

- Should the known-room_slug validation list (CAP-1) be maintained as a static set inside `generate_nodes.py`, or generated/shared from the climate room definitions (`components/rooms/**`) so it can't drift as rooms are added, renamed, or removed? Not resolved in this session.
