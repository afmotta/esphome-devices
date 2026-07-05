# map.json vs HVAC Zone Vocabulary — Gap Analysis

| Field | Value |
|-------|-------|
| **Date** | 2026-07-05 |
| **Type** | Research / factual inventory (no decisions) |
| **Feeds** | ADR-0009 open item 5 — "`map.json` field confirmation with HVAC firmware" (`canbus/_bmad-output/implementation-artifacts/deferred-work.md`, "Deferred from: spec-adr-0009" section) |
| **Scope** | Cross-cutting CAN ↔ HVAC; documentation only, no code/YAML/registry changes |

## Purpose

`canbus/firmware/registry/map.json` is the read-only export the HVAC (climate) controller
is expected to consume (`canbus/CLAUDE.md`, "Integration with the climate system";
ADR-0009 §7 in `canbus/_bmad-output/planning-artifacts/adrs/0009-central-map-binding-manifest-system-of-record.md`).
Its node field shape is explicitly provisional: the `build_map_export()` docstring in
`canbus/firmware/tools/generate_nodes.py` carries a `NOTE (ADR-0009 open item 5)` saying
the shape must be confirmed against the HVAC controller before freezing. No climate-side
consumer code exists yet — a repo-wide grep for `map.json` matches only files under
`canbus/` (verified 2026-07-05).

Before a spec can freeze the shape, this document inventories what each side actually
calls things, maps the current nodes onto climate zones, and lists the gaps as factual
observations. It deliberately makes **no design decisions** (see §6).

---

## 1. Current map.json shape

Verbatim content of `canbus/firmware/registry/map.json` (generated from
`canbus/firmware/registry/nodes.csv` by `canbus/firmware/tools/generate_nodes.py`,
`build_map_export()`):

```json
{
  "schema_version": 1,
  "map_version": "08ba65f1e2523065",
  "manifest_hash": "d66767448ba37b2f",
  "nodes": [
    {
      "node_id": 100,
      "floor": 0,
      "room": 7,
      "board": 0,
      "location": "Ground floor hallway",
      "sensors": 0
    },
    {
      "node_id": 101,
      "floor": 0,
      "room": 8,
      "board": 0,
      "location": "Ground floor living room",
      "sensors": 0
    }
  ]
}
```

### 1.1 Top-level fields

| Field | Semantics | Source |
|-------|-----------|--------|
| `schema_version` | Integer, currently `1`. The export contract is frozen-additive per ADR-0009 §7 (fields may be added, never changed or removed). | `build_map_export()` in `generate_nodes.py`; ADR-0009 §7 |
| `map_version` | 16-hex **deterministic content digest**: SHA-256 over the sorted-keys JSON of the export body, truncated to 16 chars (`_digest()` in `generate_nodes.py`). It is content identity, *not* a timestamp — a deliberate divergence from ADR-0009 §7's "generation timestamp" wording (Alberto's call, recorded in the `_digest()` docstring) so an unchanged registry regenerates byte-for-byte. The same value is compiled into the gateway as `NODE_MAP_VERSION` (`canbus/firmware/protocol/node_map.h`) for ADR-0009 §6 drift visibility. | `generate_nodes.py` (`_digest()`, `write_node_map()` docstring) |
| `manifest_hash` | Canonical hash of `canbus/firmware/registry/bindings.yaml` (the button-binding manifest, ADR-0009 §3). Used by the gateway↔Home-Assistant `ha_ready` arbitration heartbeat; it identifies *button bindings*, not placement. | `write_exports()` in `generate_nodes.py`; `spec-adr-0009-central-map-binding-manifest.md` |
| `nodes[]` | One entry per physical wall-button board, copied from `nodes.csv`, sorted by `node_id` so the export is stable regardless of CSV row order. | `build_map_export()` docstring |

### 1.2 Per-node fields

| Field | Type / range | Semantics |
|-------|-------------|-----------|
| `node_id` | 0–8191 (13-bit field of the 29-bit Extended CAN ID; `NODE_ID_MAX = 8191` in `generate_nodes.py`, mask in `canbus/firmware/protocol/canbus_protocol.h`) | The node's **only flashed identity** (ADR-0007 flat-node_id model). Every frame the node sends — button events and sensor frames — carries this id in the CAN ID. Uniqueness is the one load-bearing registry invariant (`generate_nodes.py` duplicate check). |
| `floor` | Integer, **not range-validated** (only parsed as `int` in `generate_nodes.py`) | Map-seed metadata; not flashed into the node. There is **no formal floor enum**. The only floor vocabulary in the canbus subtree is the display-label dict `FLOOR_LABELS = {0: "Ground", 1: "First", 2: "Second", 3: "Third"}` in `generate_nodes.py`, used for generator console output. Notably, `floor` is *excluded* from the gateway's compiled `node_map.h` (which carries only `node_id → {room, board, name}`); it exists only in the CSV and this export. |
| `room` | uint8, 0–255 (`ROOM_BOARD_MAX = 255` in `generate_nodes.py`; `MAX_RB = 255` in `canbus/firmware/tools/commission.py`, matching the `uint8_t` in `node_map.h`) | A **freely allocated numeric code with no central meaning table**. No file in the repo defines what room `7` or `8` means; per ADR-0007 ("meaning lives in a central map"), the code's meaning is carried solely by the row's free-text `location`. `(room, board) = (0, 0)` is the reserved "unassigned/not-yet-commissioned" placeholder (seeded by `allocate_node.py`, exempted from uniqueness in `generate_nodes.py`); `(room, board)` must otherwise be unique among commissioned nodes. `0xFF` is the gateway's "unknown node" sentinel (`node_map.h`), so 255 is effectively reserved too. ADR-0006/ADR-0009 §2 placement rule: a sensor-hosting node's `room` **must be the sensors' physical room** (sensor frames carry only the host `node_id`). |
| `board` | uint8, 0–255 (same bounds as `room`) | Disambiguates multiple wall boxes/boards within one room; `(room, board)` together form the gateway's "location address" (`generate_nodes.py` uniqueness check). |
| `location` | Free-text string (English, in current rows) | Human-readable label; C-escaped into `node_map.h` as the node's `name`. Carries the *only* human meaning of the numeric `room` code. |
| `sensors` | Strictly `0` or `1` (generator rejects anything except blank/`0`/`1`, `generate_nodes.py` sensors-column validation) | Despite the plural name, **not a bitfield or count**: a boolean "this node hosts the ADR-0006 sensor kit" flag. `1` = the fixed SHT45 + SEN66 kit (`canbus/firmware/packages/sensor_kit.yaml`). The kit's measurement vocabulary is fixed in `canbus/firmware/protocol/canbus_protocol.h` (types 1–11: SHT45 temp/RH; SEN66 temp, RH, PM1.0/2.5/4.0/10, VOC index, NOx index, CO₂). Each measurement is one `CAT_SENSOR` frame every 30 s; per `sensor_kit.yaml`'s header comment, the consumer (named there as "the dedicated HVAC controller, external firmware") is expected to mark a measurement stale after 90 s without a `SENSOR_STATUS_OK` frame. Both current nodes have `sensors: 0`, so **no sensor data flows today**. |

One vocabulary note already flagged in-code: ADR-0009 §7 describes the node list as
"(id, floor, room, board, location, sensors)", but the export deliberately uses the
repo-wide name `node_id` over the ADR's shorthand `id` until the consumer confirms
(`build_map_export()` NOTE).

---

## 2. Climate system zone vocabulary

The climate system keys every entity on an Italian `room_slug` (root `CLAUDE.md` entity-ID
convention: `{scope}_{component}[_{mode}][_{aspect}]`). Slugs are declared as
`defaults: room_slug:` in each room file under `components/rooms/` and wired by the floor
aggregators (`ground-floor.yaml`, `first-floor.yaml`, `second-floor.yaml`).

| Floor | `room_slug` | `room_name` | File |
|-------|-------------|-------------|------|
| Ground | `soggiorno` | Soggiorno (living room) | `components/rooms/ground_floor/soggiorno.yaml` |
| Ground | `cucina` | Cucina (kitchen) | `components/rooms/ground_floor/cucina.yaml` |
| Ground | `bagno_terra` | Bagno Piano Terra (bathroom) | `components/rooms/ground_floor/bagno.yaml` — **slug differs from filename** |
| Ground | `anticamera` | Anticamera (entry hall) | `components/rooms/ground_floor/anticamera.yaml` |
| Ground | `locale_tecnico` | Locale Tecnico (technical room) | `components/rooms/ground_floor/locale_tecnico.yaml` |
| First | `bagno_grande` | Bagno Grande | `components/rooms/first_floor/bagno_grande.yaml` |
| First | `bagno_ospiti` | Bagno Ospiti | `components/rooms/first_floor/bagno_ospiti.yaml` |
| First | `bagno_padronale` | Bagno Padronale | `components/rooms/first_floor/bagno_padronale.yaml` |
| First | `camera_nord` | Camera Nord | `components/rooms/first_floor/camera_nord.yaml` |
| First | `camera_sud` | Camera Sud | `components/rooms/first_floor/camera_sud.yaml` |
| First | `camera_ospiti` | Camera Ospiti | `components/rooms/first_floor/camera_ospiti.yaml` |
| First | `camera_padronale` | Camera Padronale | `components/rooms/first_floor/camera_padronale.yaml` |
| First | `lavanderia` | Lavanderia (laundry) | `components/rooms/first_floor/lavanderia.yaml` |
| Second | `sottotetto` | Sottotetto (attic) | `components/rooms/second_floor/sottotetto.yaml` |

14 room packages total (5 + 8 + 1), as included by the three floor aggregators. (Root
`CLAUDE.md`'s overview says "13 zones"; the file inventory above is what is actually wired.)

Floor identity on the climate side is **never numeric**. It appears as:
- English directory names / entity-ID scope prefixes: `ground_floor`, `first_floor`,
  `second_floor` (e.g. `ground_floor_max_dew_point` in
  `components/rooms/ground_floor/ground-floor.yaml`);
- Italian display/area names: `piano_terra` / "Piano Terra", `primo_piano`,
  `secondo_piano` (e.g. `area_name: "Radiante Piano Terra"` in `ground-floor.yaml`,
  package key `mixing_pump_primo_piano` in `first-floor.yaml`).

The `room_slug` is also the join key for the climate system's own remote sensors: UDP
`packet_transport` providers are derived as
`room-sensor-${room_slug | replace('_', '-')}` (`components/room_sensors.yaml`), and the
per-room failover entities are `${room_slug}_temp_udp` / `_temp_ha` / `_temp_abstracted`
etc. Per the tier table in `components/room_sensors.yaml`, the current failover order is
**Tier 1 = Home Assistant sensor, Tier 2 = UDP sensor, Tier 3 = Emergency (NaN)**.

---

## 3. Mapping: current map.json nodes → climate zones

| `node_id` | `floor` | `room` | `location` | Candidate `room_slug` | Confidence / notes |
|-----------|---------|--------|------------|----------------------|--------------------|
| 100 | 0 | 7 | "Ground floor hallway" | `anticamera` | **Plausible, unconfirmed.** `anticamera` (entry hall) is the only hallway-like ground-floor climate zone. But "hallway" is English free text — nothing machine-readable ties room code 7 to `anticamera`, and "hallway" vs "entry hall" is an interpretation, not a match. Needs Alberto's confirmation. |
| 101 | 0 | 8 | "Ground floor living room" | `soggiorno` | **High confidence.** "Living room" ↔ soggiorno is unambiguous among the ground-floor slugs; still a human-language match, not a data match. |

Both nodes have `sensors: 0` and `board: 0`, so today the mapping has no operational
consumer: neither node emits climate-relevant data, and buttons are an HA/gateway concern
(ADR-0003), not a climate-controller concern.

Conversely, 12 of the 14 climate zones have **no** canbus node at all — the registry is a
2-node PoC while the climate zone list is complete. Any mapping artifact must tolerate
zones without nodes and (in principle) nodes in spaces that are not climate zones
(corridors, stairwells).

---

## 4. Gaps (factual observations, not decisions)

1. **No machine-readable join key.** map.json identifies rooms by a uint8 code plus
   free-text English `location` (`canbus/firmware/registry/nodes.csv`); the climate
   system keys every entity, sensor, PID, and UDP provider on an Italian `room_slug`
   (`components/room_sensors.yaml`, `components/rooms/**`). The only way to join the two
   today is a human reading the `location` string.

2. **Room codes have no meaning table anywhere.** Per ADR-0007 the numeric `room` code's
   meaning "lives in the central map" — and in the map that meaning is *only* the
   free-text `location` of the same row. There is no room-code enum in
   `canbus/firmware/protocol/` headers, docs, or registry that the climate side could
   consume. (Contrast: `floor` at least has the informal `FLOOR_LABELS` dict in
   `generate_nodes.py`.)

3. **Floor numbering conventions are compatible but not shared.** Canbus `floor 0/1/2`
   maps to Ground/First/Second (`FLOOR_LABELS`, `generate_nodes.py`), which lines up with
   piano_terra / primo_piano / secondo_piano. But the climate side has no numeric floor
   representation at all — floors are directory names and entity-ID prefixes
   (`ground_floor`, …) plus Italian display strings. Any consumer needs a
   number→slug conversion that currently exists nowhere.

4. **Naming-language mismatch is pervasive.** Canbus `location` strings are English
   ("Ground floor living room"); climate slugs and display names are Italian
   (`soggiorno`, "Piano Terra"). Cosmetic in itself, but it means even fuzzy text
   matching between the two vocabularies would cross languages.

5. **`sensors` is kit-presence, not a measurement inventory.** The climate failover
   consumes *per-measurement* entities (temperature and humidity per room,
   `components/room_sensors.yaml`; CO₂/IAQ per room for MEV,
   `components/rooms/first_floor/first-floor.yaml`). map.json's `sensors: 1` says only
   "this node hosts the fixed SHT45+SEN66 kit"; the actual measurement list (types 1–11)
   and encodings live in `canbus/firmware/protocol/canbus_protocol.h`, and the 30 s
   cadence / 90 s staleness contract lives only in a comment in
   `canbus/firmware/packages/sensor_kit.yaml`. A pure-JSON consumer of map.json sees none
   of that. (Because the kit is fleet-fixed by ADR-0006, this is arguably derivable — but
   it is derivable from the C++ header, not from the export.)

6. **Fields with no plausible climate consumer.**
   - `manifest_hash`: identifies the *button-binding* manifest for the gateway↔HA
     `ha_ready` arbitration (ADR-0009 §3); the climate controller plays no role in that
     arbitration.
   - `board`: disambiguates wall boxes within a room; climate zones are per-room, so a
     zone-keyed consumer has no use for it (it would at most need "all node_ids whose
     room maps to this zone").
   - `map_version` *does* have a plausible use (drift diagnostics, ADR-0009 §6), and
     `schema_version` is contract hygiene.

7. **Things the climate side would plausibly need that map.json lacks** (stated as
   observations of the consumer's existing shape, not as requirements):
   - A `room_slug`-compatible join key, since every climate entity ID is derived from it.
   - The reverse lookup it will actually perform: *zone → sensor-bearing node_id(s)*, to
     know which CAN IDs (`can_id(CAT_SENSOR, node_id)`) carry a given zone's data.
     Derivable from `nodes[]` once a join key exists.
   - The staleness/cadence contract (30 s emit, 90 s stale) if the climate side is to
     enforce it — today that contract is only prose in `sensor_kit.yaml`.
   - Sanity-bounds expectations: ADR-0010 open item 3 (recorded in
     `canbus/_bmad-output/implementation-artifacts/deferred-work.md`) recommends
     plausibility clamps on the HVAC side for spoofed `CAT_SENSOR` frames; nothing in the
     export supports or documents that.

8. **The transport path into the climate failover is undefined.** The climate failover
   tiers as implemented are HA (tier 1) → UDP `packet_transport` (tier 2) → NaN emergency
   (`components/room_sensors.yaml`). CAN sensor frames terminate at the canbus gateway
   (ESP32-S3, `canbus/firmware/gateway/gateway.yaml`), which speaks to HA — while
   `sensor_kit.yaml` names "the dedicated HVAC controller" as the frame consumer. Which
   physical/network hop delivers CAN measurements to the climate board, and which tier
   they land in, is not defined anywhere in the repo.

9. **Two shape-freeze footnotes already latent in the generator** that the spec should
   resolve or ratify:
   - `node_id` vs ADR-0009 §7's `id` shorthand (`build_map_export()` NOTE);
   - `map_version` as content digest vs the ADR's "generation timestamp" wording
     (decided in place, `_digest()` docstring — the ADR text was not updated).

10. **One climate slug/filename divergence worth knowing during any mapping exercise:**
    the ground-floor bathroom file is `bagno.yaml` but its slug is `bagno_terra`
    (`components/rooms/ground_floor/bagno.yaml`), and the aggregator references
    `bagno_terra_radiant_pid_is_active` (`ground-floor.yaml`). Any tooling that assumes
    filename == slug will mis-join this room.

---

## 5. What already constrains the solution space (for the spec author)

- ADR-0009 §2 names the **additive-column migration pattern** on `nodes.csv` (the
  `sensors` column migration in `allocate_node.py`) as "the precedent for future
  columns" — i.e. adding a column is an anticipated, tooled operation.
- ADR-0011 open item 5 (deferred-work.md) already plans another additive column
  (`segment`) via the same pattern.
- The export contract is frozen-additive (ADR-0009 §7): fields may be added, never
  changed or removed — so freezing the current shape does not preclude adding a join key
  later, but renaming `sensors` or `node_id` after freeze is off the table.
- Authority boundary (ADR-0009 §7 / ADR-0006 §6): the HVAC controller *reads* exports;
  it never allocates node_ids or writes the registry. A climate-side-owned mapping file
  would not violate this; a climate-side write to `nodes.csv` would.

---

## 6. Open questions for the spec (deliberately not answered here)

1. **Where does the join key live?** Options include: an additive `room_slug` column in
   `canbus/firmware/registry/nodes.csv` (per the §2 additive-column precedent); a
   separate mapping file (registry-side or climate-side) keyed `room`/`node_id` →
   `room_slug`; or a room-code meaning table that both sides consume. Not decided here.
2. **Who owns the join artifact** — the canbus registry (git system of record, ADR-0009)
   or the climate configuration tree — and which side validates that every
   sensor-bearing node resolves to a real climate zone?
3. **How does the climate controller consume the contract** — `map.json` at build/config
   time, `protocol/node_map.h` as a C++ include (both are offered by ADR-0009 §7), or
   indirectly via Home Assistant entities materialized by the gateway?
4. **Where do CAN sensor measurements enter the climate failover tiers**
   (`components/room_sensors.yaml`: HA → UDP → Emergency)? As a new tier, as a
   replacement for the UDP tier in CAN-sensed rooms, or routed through HA into tier 1?
   And which device physically receives the frames?
5. **Should the sensor contract (measurement types 1–11, 30 s cadence, 90 s staleness,
   status-byte semantics) be represented in the export**, or remain C++-header/prose
   constants that the climate firmware mirrors?
6. **Floor representation in the join:** adopt the canbus numeric floor on the climate
   side, or map `0/1/2` → `ground_floor/first_floor/second_floor` inside the join
   artifact?
7. **Freeze scope:** are `manifest_hash` and `board` (no identified climate consumer, §4
   item 6) inside or outside the frozen consumer contract — i.e. does the climate spec
   promise to ignore them, or does the freeze only cover the fields it reads?
8. **Ratify the two latent generator decisions** (§4 item 9): keep `node_id` naming and
   the deterministic `map_version` digest, and update ADR-0009 §7's text to match?
