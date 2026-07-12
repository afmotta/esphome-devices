#!/usr/bin/env python3
"""
generate_nodes.py — Generate ESPHome node configs from the registry CSV.

Usage:
    1. Fill in registry/nodes.csv with your physical layout
    2. Run: python tools/generate_nodes.py
    3. Generated configs appear in nodes/

CSV format:
    node_id,floor,room,board,location,sensors,room_slug
    100,0,7,0,"Ground floor hallway",0,

The `sensors` column (blank/0 = none, 1 = SHT45+SEN66 kit) adds the ADR-0006 sensor_kit
package to the generated node. Sensor frames carry the host node's node_id, so a
sensor-equipped node's registry room must be the sensors' physical room.

The `room_slug` column (spec-map-json-contract) joins a node to a climate zone. Values are
validated against the climate room packages (hvac/rooms/**), never freehand;
blank = not joined to a climate zone (corridors, stairwells, not-yet-commissioned). A
sensors=1 node MUST carry a room_slug — its measurements are consumed per climate zone. The
numeric floor must convert (FLOOR_SLUGS) to the zone's climate floor.

The CSV header must match CSV_HEADER exactly. Pre-live there is exactly one nodes.csv (the
committed one), so there is no legacy-format tolerance: a schema change edits CSV_HEADER and
the committed CSV together, in place (no migration shims — same doctrine as no PROTO bumps).

Flat node_id model (ADR-0007): node_id is the node's only identity, carried in the 29-bit
Extended CAN ID. It is the ONLY thing flashed into the node. floor/room/board/location are
map-seed metadata for the central node_id -> {...} map on the controller/HA — they are NOT
flashed into the node config (kept here as the registry / map seed).

Every node carries the standard 8-button set (btn0–btn7), SPI/CAN pins, and heartbeat from
packages/base_node.yaml, so each generated file is minimal: just its node_id + debounce_ms
and a single include.
"""

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import bindings  # binding-manifest reader + canonical hash (ADR-0009)

ROOT = Path(__file__).resolve().parent.parent  # canbus/ (flattened out of firmware/, Phase 6a)
REPO_ROOT = ROOT.parent  # repo root (registry/ lives here, elevated out of firmware/)

TEMPLATE = """\
# =============================================================================
# Node: {name} — node_id {node_id}
# =============================================================================
# GENERATED from registry/nodes.csv by tools/generate_nodes.py. DO NOT EDIT.
# Identity-only: the node knows just its node_id. Floor/room/board/location are NOT known at
# flash time (the node is flashed at allocation, positioned/commissioned later) — they live in
# the registry and the gateway's node_map.h, never here (ADR-0007).
# Buttons:  standard 8-button set (btn0–btn7) from packages/base_node.yaml
{sensor_comment}# CAN IDs (29-bit Extended, computed at runtime from node_id):
#   Input  = 0x{input_id:08X}  (CAT_INPUT,  node -> controller, button events)
#   Status = 0x{status_id:08X}  (CAT_STATUS, node -> controller, heartbeat)
# =============================================================================

substitutions:
  node_id: "{node_id}"
  debounce_ms: "50"

packages:
  base: !include ../packages/base_node.yaml
{sensor_pkg}"""

# Appended to TEMPLATE for rows with sensors=1 (ADR-0006). The sensor frames carry the host
# node's node_id, so the host's registry room must be the sensors' physical room.
SENSOR_COMMENT = (
    "# Sensors:  SHT45 + SEN66 kit from packages/sensor_kit.yaml "
    "(CAT_SENSOR, host room = sensor room)\n"
)
SENSOR_PKG = "  sensor_kit: !include ../packages/sensor_kit.yaml\n"

FLOOR_LABELS = {0: "Ground", 1: "First", 2: "Second", 3: "Third"}

# Fixed floor number -> climate floor slug conversion (spec-map-json-contract CAP-2). The
# numeric `floor` stays canbus map-seed metadata (not flashed, not range-validated); any
# consumer deriving a climate floor slug for a node goes through this table. Floors outside
# it (e.g. 3) simply have no climate floor and cannot host a room_slug.
FLOOR_SLUGS = {0: "ground_floor", 1: "first_floor", 2: "second_floor"}

# The registry schema, single source of truth: allocate_node.py and commission.py import it.
CSV_HEADER = ["node_id", "floor", "room", "board", "location", "sensors", "room_slug"]
EXAMPLE_ROWS = [
    CSV_HEADER,
    [100, 0, 7, 0, "Ground floor hallway", 0, ""],
    [101, 0, 8, 0, "Ground floor living room", 0, ""],
]

CAN_SENSOR_ROUTES_PATH = Path("hvac") / "packages" / "generated" / "can_sensor_routes.yaml"
CAN_SENSOR_ROUTES_HEADER_PATH = Path("hvac") / "protocol" / "generated_can_sensor_routes.h"

# Route every ADR-0006 producer measurement to a room-scoped CAN source sensor. The
# `constant` names intentionally match canbus_protocol.h so the generated receiver-facing
# branches do not bake protocol numbers into YAML lambdas.
CAN_SENSOR_MEASUREMENTS = (
    {
        "constant": "SENSOR_SHT45_TEMP",
        "target_suffix": "temp",
        "label": "Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "accuracy_decimals": 2,
    },
    {
        "constant": "SENSOR_SHT45_RH",
        "target_suffix": "humidity",
        "label": "Humidity",
        "unit": "%",
        "device_class": "humidity",
        "accuracy_decimals": 2,
    },
    {
        "constant": "SENSOR_SEN66_TEMP",
        "target_suffix": "sen66_temp",
        "label": "SEN66 Temperature",
        "unit": "°C",
        "device_class": "temperature",
        "accuracy_decimals": 2,
    },
    {
        "constant": "SENSOR_SEN66_RH",
        "target_suffix": "sen66_humidity",
        "label": "SEN66 Humidity",
        "unit": "%",
        "device_class": "humidity",
        "accuracy_decimals": 2,
    },
    {
        "constant": "SENSOR_SEN66_PM1_0",
        "target_suffix": "pm1_0",
        "label": "PM1.0",
        "unit": "ug/m3",
        "accuracy_decimals": 1,
    },
    {
        "constant": "SENSOR_SEN66_PM2_5",
        "target_suffix": "pm2_5",
        "label": "PM2.5",
        "unit": "ug/m3",
        "accuracy_decimals": 1,
    },
    {
        "constant": "SENSOR_SEN66_PM4_0",
        "target_suffix": "pm4_0",
        "label": "PM4.0",
        "unit": "ug/m3",
        "accuracy_decimals": 1,
    },
    {
        "constant": "SENSOR_SEN66_PM10",
        "target_suffix": "pm10",
        "label": "PM10",
        "unit": "ug/m3",
        "accuracy_decimals": 1,
    },
    {
        "constant": "SENSOR_SEN66_VOC_INDEX",
        "target_suffix": "voc_index",
        "label": "VOC Index",
        "accuracy_decimals": 0,
    },
    {
        "constant": "SENSOR_SEN66_NOX_INDEX",
        "target_suffix": "nox_index",
        "label": "NOx Index",
        "accuracy_decimals": 0,
    },
    {
        "constant": "SENSOR_SEN66_CO2",
        "target_suffix": "co2",
        "label": "CO2",
        "unit": "ppm",
        "device_class": "carbon_dioxide",
        "accuracy_decimals": 0,
    },
)

# HVAC-1.4/HVAC-1.5: room-level route targets are declared once per room in
# hvac/room_sensors.yaml itself (via ${room_slug} substitution), so this generator
# must only emit publish dispatch for them. Keeping declarations static prevents
# duplicate-id errors when registry-driven routes include the same room.
STATIC_CAN_SENSOR_TARGET_SUFFIXES = frozenset({
    "temp",
    "humidity",
    "co2",
    "voc_index",
    "nox_index",
    "pm1_0",
    "pm2_5",
    "pm4_0",
    "pm10",
})

# CAN ID layout — must match canbus_protocol.h: [category:4][node_id:13][reserved:12].
CAT_SHIFT = 25
NODE_SHIFT = 12
CAT_INPUT, CAT_STATUS = 1, 3
NODE_ID_MAX = 8191  # 13 bits
ROOM_BOARD_MAX = 255  # room/board are uint8 in node_map.h (matches commission.py MAX_RB)


def can_id(category: int, node_id: int) -> int:
    return ((category & 0x0F) << CAT_SHIFT) | ((node_id & 0x1FFF) << NODE_SHIFT)


def _c_str(s: str) -> str:
    """Escape a Python string for a C string literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


# A room package declares its slug as a `defaults:` entry at 2-space indent; parameter
# passing inside `packages:` blocks is deeper-indented and must not match.
_ROOM_SLUG_RE = re.compile(r'^\s{2}room_slug:\s*"?([a-z0-9_]+)"?\s*$')


def load_climate_zones(rooms_dir: Path = None) -> dict:
    """Read the known climate zones from the climate room packages: room_slug -> climate
    floor slug. Sourced from hvac/rooms/** rather than a hardcoded set so the list
    cannot drift as rooms are added, renamed, or removed (spec-map-json-contract open
    question, resolved toward the shared source). Slugs come from file CONTENTS, not
    filenames — ground_floor/bagno.yaml declares bagno_terra."""
    if rooms_dir is None:
        rooms_dir = REPO_ROOT / "hvac" / "rooms"
    zones = {}
    for floor_slug in FLOOR_SLUGS.values():
        for path in sorted((rooms_dir / floor_slug).glob("*.yaml")):
            for line in path.read_text().splitlines():
                m = _ROOM_SLUG_RE.match(line)
                if m:
                    zones[m.group(1)] = floor_slug
                    break
    if not zones:
        print(f"ERROR: no climate zones found under {rooms_dir} — cannot validate room_slug",
              file=sys.stderr)
        sys.exit(1)
    return zones


def validate_room_slug(room_slug: str, floor: int, has_sensors: bool, zones: dict):
    """Return an error string (or None) for a row's climate-zone join (spec-map-json-contract).

    - sensors=1 requires a room_slug: sensor measurements are consumed per climate zone.
    - A non-empty room_slug must be a known climate zone — never a freehand string.
    - The row's numeric floor must convert (FLOOR_SLUGS) to the zone's climate floor.
    Blank room_slug on a sensor-less node is valid: non-zone spaces, not-yet-commissioned."""
    if not room_slug:
        if has_sensors:
            return "sensors=1 requires a room_slug (sensor data joins to a climate zone)"
        return None
    if room_slug not in zones:
        return (f"unknown room_slug '{room_slug}' "
                f"(known climate zones: {', '.join(sorted(zones))})")
    floor_slug = FLOOR_SLUGS.get(floor)
    if floor_slug != zones[room_slug]:
        return (f"floor {floor} ({floor_slug or 'no climate floor'}) does not match "
                f"room_slug '{room_slug}' ({zones[room_slug]})")
    return None


def write_node_map(entries, map_version: str, path: Path) -> None:
    """Emit the gateway's compiled central map: node_id -> {room, board, name} (ADR-0007).

    NODE_MAP_VERSION is the same deterministic map_version stamped into registry/map.json
    (build_map_export); compiling it in lets the gateway expose its map identity as a
    drift-visibility diagnostic (ADR-0009 §6) that a dashboard compares against the committed
    map.json — surfacing "committed in git but not yet reflashed" instead of a misbehaving
    button. It tracks the full registry map (incl. floor/sensors), not just the compiled rows,
    so the comparison is against map.json verbatim; over-signalling (a floor-only edit rolls
    the version) errs toward a harmless reflash, the safe direction."""
    rows = "\n".join(
        f'    {{{nid}, {room}, {board}, "{_c_str(loc)}"}},'
        for nid, room, board, loc in sorted(entries)
    )
    path.write_text(
        "#pragma once\n"
        "#include <cstdint>\n"
        "#include <cstddef>\n\n"
        "// =============================================================================\n"
        "// node_map.h — GENERATED from nodes.csv by generate_nodes.py. DO NOT EDIT.\n"
        "// Central node_id -> {room, board, name} map (ADR-0007), compiled into the gateway.\n"
        "// An unknown node_id resolves to the sentinel (room/board 0xFF, name \"unknown\") —\n"
        "// i.e. a node that is on the bus but not yet in the map (uncommissioned).\n"
        "// NODE_MAP_VERSION mirrors registry/map.json's map_version for drift visibility (§6).\n"
        "// =============================================================================\n\n"
        f'inline constexpr char NODE_MAP_VERSION[] = "{map_version}";\n\n'
        "struct NodeMapEntry { uint16_t node_id; uint8_t room; uint8_t board; const char *name; };\n\n"
        "inline constexpr uint8_t NODE_MAP_UNKNOWN = 0xFF;\n\n"
        f"inline constexpr NodeMapEntry NODE_MAP[] = {{\n{rows}\n}};\n"
        "inline constexpr std::size_t NODE_MAP_SIZE = sizeof(NODE_MAP) / sizeof(NODE_MAP[0]);\n\n"
        "inline const NodeMapEntry *node_map_find(uint16_t node_id) {\n"
        "  for (std::size_t i = 0; i < NODE_MAP_SIZE; i++)\n"
        "    if (NODE_MAP[i].node_id == node_id) return &NODE_MAP[i];\n"
        "  return nullptr;\n"
        "}\n"
        "inline bool node_map_known(uint16_t node_id) { return node_map_find(node_id) != nullptr; }\n"
        "inline uint8_t node_map_room(uint16_t node_id) { auto e = node_map_find(node_id); return e ? e->room : NODE_MAP_UNKNOWN; }\n"
        "inline uint8_t node_map_board(uint16_t node_id) { auto e = node_map_find(node_id); return e ? e->board : NODE_MAP_UNKNOWN; }\n"
        "inline const char *node_map_name(uint16_t node_id) { auto e = node_map_find(node_id); return e ? e->name : \"unknown\"; }\n"
    )


def _digest(payload) -> str:
    """Deterministic 16-hex content marker over a JSON-able payload (same family as the
    binding canonical hash). Used as the map's version stamp instead of a wall-clock
    timestamp, so an unchanged export regenerates byte-for-byte (Alberto's call, ADR-0009 §7:
    the 'generation marker' is content identity, not time — no diff churn on every run)."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def render_bindings_header(manifest_hash: str, bindings_list) -> str:
    """Render protocol/bindings.h: the binding-manifest identity (ADR-0009 §3) PLUS the full
    compiled BINDINGS[] fallback table (ADR-0009 §4). Frozen-additive, mirrors node_map.h.

    Deterministic — no generation timestamp — so regenerating unchanged bindings produces no
    diff. The table is the gateway's fallback-bindings artifact; it is committed now and
    grows as bindings.yaml is authored (today it is empty: fallback is still log-only,
    ADR-0003 open item 7). op is stored as a C string (like node_map.h names) — no new enums —
    so the action vocabulary can grow additively without a header redesign.

    Fallback acts on the single click only, so a binding is keyed by (node_id, button) with no
    event field. A binding may drive several relays from one click (ADR-0009 open item 1): each
    entry carries a {relay_count, relays} list rather than a single channel, so fan-out needs
    no per-binding firmware change. One `op` applies to every relay in the list.
    """
    ordered = sorted(bindings_list, key=lambda b: (b["node_id"], b["button"]))
    if ordered:
        # Each binding's relay list is a named static array the table points at; the list is
        # normalized (sorted, de-duplicated) by the same parser the hash uses.
        relay_lists = [bindings.parse_relays(b["relay"]) for b in ordered]
        decls = "\n".join(
            f"inline constexpr uint8_t BINDING_RELAYS_{i}[] = {{{', '.join(map(str, relays))}}};"
            for i, relays in enumerate(relay_lists)
        )
        rows = "\n".join(
            f'    {{{b["node_id"]}, {b["button"]}, '
            f'{len(relays)}, BINDING_RELAYS_{i}, "{_c_str(str(b["op"]))}"}},'
            for i, (b, relays) in enumerate(zip(ordered, relay_lists))
        )
        table = (
            f"{decls}\n"
            f"inline constexpr BindingEntry BINDINGS[] = {{\n{rows}\n}};\n"
            "inline constexpr std::size_t BINDINGS_SIZE = sizeof(BINDINGS) / sizeof(BINDINGS[0]);\n"
        )
    else:
        # An empty manifest yields a 0-length table. A zero-size array is non-standard, so
        # expose a null pointer + size 0 instead — binding_find() never dereferences it.
        table = (
            "inline constexpr const BindingEntry *BINDINGS = nullptr;\n"
            "inline constexpr std::size_t BINDINGS_SIZE = 0;\n"
        )
    return (
        "#pragma once\n"
        "#include <cstdint>\n"
        "#include <cstddef>\n\n"
        "// =============================================================================\n"
        "// bindings.h — GENERATED from registry/bindings.yaml by tools/generate_nodes.py. DO NOT EDIT.\n"
        "// Binding-manifest identity + compiled fallback table for the ha_ready arbitration\n"
        "// (ADR-0009 §3/§4). BINDINGS_MANIFEST_HASH is the canonical hash of bindings.yaml,\n"
        "// which the gateway compares against the hash Home Assistant echoes in its readiness\n"
        "// heartbeat (ADR-0003); a mismatch keeps ha_ready off. BINDINGS[] is the controller's\n"
        "// fallback action table — frozen-additive, currently log-only (ADR-0003 open item 7).\n"
        "// Keyed by (node_id, button): fallback fires on the single click only. relays/relay_count\n"
        "// carry one-or-more gateway relay ids so one click can fan out to several relays\n"
        "// (ADR-0009 open item 1); the single `op` applies to every relay.\n"
        "// =============================================================================\n\n"
        f'inline constexpr char BINDINGS_MANIFEST_HASH[] = "{manifest_hash}";\n\n'
        "struct BindingEntry { uint16_t node_id; uint8_t button; "
        "uint8_t relay_count; const uint8_t *relays; const char *op; };\n\n"
        f"{table}\n"
        "inline const BindingEntry *binding_find(uint16_t node_id, uint8_t button) {\n"
        "  for (std::size_t i = 0; i < BINDINGS_SIZE; i++)\n"
        "    if (BINDINGS[i].node_id == node_id && BINDINGS[i].button == button)\n"
        "      return &BINDINGS[i];\n"
        "  return nullptr;\n"
        "}\n"
    )


def build_map_export(export_nodes, manifest_hash: str) -> dict:
    """Build the registry/map.json payload (ADR-0009 §7): the read-only export for non-C
    consumers (HVAC controller, dashboards, tooling). schema_version + a deterministic
    map_version marker + the binding manifest_hash + the node list. Nodes are sorted by
    node_id so the export is stable regardless of CSV row order.

    FROZEN HVAC-consumer contract (ADR-0009 open item 5, closed by spec-map-json-contract):
    `schema_version`, `map_version`, `nodes[].node_id`, `nodes[].room_slug`,
    `nodes[].location`, `nodes[].sensors` are frozen-additive — fields may be added, never
    renamed, removed, or reinterpreted without a new spec. `manifest_hash` (ha_ready
    arbitration, §3) and `board` (wall-box disambiguation) are explicitly OUTSIDE the freeze:
    changing them needs no HVAC-side compatibility review. `floor`/`room` stay canbus
    map-seed metadata; a consumer derives a climate floor slug from `floor` via FLOOR_SLUGS.
    An empty `room_slug` means the node is not joined to a climate zone.
    """
    nodes = [
        {
            "node_id": n["node_id"],
            "floor": n["floor"],
            "room": n["room"],
            "board": n["board"],
            "location": n["location"],
            "sensors": n["sensors"],
            "room_slug": n["room_slug"],
        }
        for n in sorted(export_nodes, key=lambda n: n["node_id"])
    ]
    body = {"schema_version": 1, "manifest_hash": manifest_hash, "nodes": nodes}
    return {
        "schema_version": 1,
        "map_version": _digest(body),
        "manifest_hash": manifest_hash,
        "nodes": nodes,
    }


def render_ha_package(manifest_hash: str) -> str:
    """Render canbus/home-assistant/ha_manifest_package.yaml (ADR-0009 §4): the GENERATED Home Assistant
    half of the readiness heartbeat, with the manifest hash baked in so HA echoes it
    automatically — retiring the interim hand-paste. Heartbeat only; the ACK automation
    stays hand-maintained in ha_arbitration_automations.yaml until bindings are real and
    manifest-derived (ADR-0009 open item 3, resolved this slice: heartbeat-only package)."""
    return (
        "# =============================================================================\n"
        "# ha_manifest_package.yaml — GENERATED from registry/bindings.yaml by\n"
        "# tools/generate_nodes.py. DO NOT EDIT — re-run the generator after editing bindings.\n"
        "# =============================================================================\n"
        "# Home Assistant package (NOT ESPHome config). It carries the readiness-heartbeat\n"
        "# automation with the binding manifest hash baked in, so HA proves it runs the same\n"
        "# bindings the gateway compiled (ADR-0009 §3/§4). Wire it into HA once, e.g.:\n"
        "#   homeassistant:\n"
        "#     packages:\n"
        "#       canbus_manifest: !include ha_manifest_package.yaml\n"
        "# Regenerating with unchanged bindings produces no diff. The ACK automation stays\n"
        "# hand-maintained in ha_arbitration_automations.yaml (still log-only, ADR-0003).\n"
        "# =============================================================================\n\n"
        "automation:\n"
        "  - id: canbus_gateway_readiness_heartbeat\n"
        '    alias: "CAN gateway: readiness heartbeat"\n'
        "    mode: single\n"
        "    triggers:\n"
        '      - trigger: time_pattern\n'
        '        seconds: "/5"\n'
        "    actions:\n"
        "      - action: esphome.canbus_gateway_ha_readiness_heartbeat\n"
        "        data:\n"
        f'          manifest_hash: "{manifest_hash}"\n'
    )


def _room_title(room_slug: str) -> str:
    return " ".join(part.capitalize() for part in room_slug.split("_"))


def _route_target_id(room_slug: str, measurement: dict) -> str:
    return f"{room_slug}_{measurement['target_suffix']}_can"


def _is_esphome_id_prefix(value: str) -> bool:
    if not value or not (value[0].isalpha() or value[0] == "_"):
        return False
    return all(ch.isalnum() or ch == "_" for ch in value)


def _sensor_route_nodes(export_nodes):
    sensor_nodes = sorted(
        (n for n in export_nodes if int(n.get("sensors", 0)) == 1),
        key=lambda n: (str(n.get("room_slug", "")), int(n["node_id"])),
    )
    seen_rooms = {}
    for node in sensor_nodes:
        room_slug = node.get("room_slug", "")
        if not room_slug:
            raise ValueError(
                f"sensors=1 requires a room_slug for node_id {node['node_id']} "
                "before CAN sensor routes can be generated"
            )
        if not _is_esphome_id_prefix(room_slug):
            raise ValueError(
                f"room_slug '{room_slug}' for sensors=1 node_id {node['node_id']} "
                "cannot be used as an ESPHome id prefix"
            )
        if room_slug in seen_rooms:
            raise ValueError(
                f"duplicate sensors=1 room_slug '{room_slug}' for node_id {seen_rooms[room_slug]} "
                f"and node_id {node['node_id']}"
            )
        seen_rooms[room_slug] = node["node_id"]
    return sensor_nodes


def render_can_sensor_routes(export_nodes) -> str:
    """Render the HVAC-owned compile-time route artifact for CAN sensor receivers.

    The current story only emits the deterministic route package. Receiver composition,
    freshness, and failover remain separate HVAC-1 stories. Does not declare its own
    `esphome: includes:` for canbus_protocol.h (needed for the SENSOR_* constants used in
    the dispatch scripts below) — every composing entry point (devices/climate-control.yaml,
    hvac/tests/compile_can_sensor_receiver.yaml) already includes it at the correct
    CLI-invoked-file-relative depth, and this package's own directory depth doesn't match
    that depth, so redeclaring it here would just be a second, wrong-depth copy.
    """
    sensor_nodes = _sensor_route_nodes(export_nodes)
    header = (
        "# =============================================================================\n"
        "# can_sensor_routes.yaml — GENERATED from registry/nodes.csv by\n"
        "# canbus/tools/generate_nodes.py. DO NOT EDIT.\n"
        "# =============================================================================\n"
        "# HVAC CAN sensor routing artifact. Includes only sensors=1 registry rows whose\n"
        "# room_slug was validated against hvac/rooms/** before this file was written.\n"
        "#\n"
        "# Temp/humidity targets (<room_slug>_temp_can / <room_slug>_humidity_can) are declared\n"
        "# statically in hvac/room_sensors.yaml for every known HVAC room (HVAC-1.4) — this\n"
        "# file only dispatches published values into them. All other measurements keep their\n"
        "# entity declared here, scoped to sensors=1 rows only.\n"
        "# =============================================================================\n\n"
    )
    if not sensor_nodes:
        return (
            header
            + "substitutions: {}\n\n"
            + "# No sensors=1 registry rows; no CAN sensor route targets generated.\n\n"
            + "script:\n"
            + "  - id: can_sensor_route_publish\n"
            + "    mode: queued\n"
            + "    parameters:\n"
            + "      node_id: uint16_t\n"
            + "      measurement_type: uint16_t\n"
            + "      value: float\n"
            + "    then:\n"
            + "      - lambda: |-\n"
            + "          (void) node_id;\n"
            + "          (void) measurement_type;\n"
            + "          (void) value;\n"
            + "  - id: can_sensor_route_publish_nan\n"
            + "    mode: queued\n"
            + "    parameters:\n"
            + "      node_id: uint16_t\n"
            + "      measurement_type: uint16_t\n"
            + "    then:\n"
            + "      - lambda: |-\n"
            + "          (void) node_id;\n"
            + "          (void) measurement_type;\n"
        )

    lines = [
        header.rstrip(),
        "",
        "sensor:",
    ]
    for node in sensor_nodes:
        room_slug = node["room_slug"]
        room_name = _room_title(room_slug)
        for measurement in CAN_SENSOR_MEASUREMENTS:
            if measurement["target_suffix"] in STATIC_CAN_SENSOR_TARGET_SUFFIXES:
                # Entity already declared statically in hvac/room_sensors.yaml
                # (HVAC-1.4) — only the dispatch script (below) needs to know its id.
                continue
            lines.extend([
                "  - platform: template",
                f"    id: {_route_target_id(room_slug, measurement)}",
                f"    name: \"{room_name} {measurement['label']} CAN\"",
                "    state_class: measurement",
                f"    accuracy_decimals: {measurement['accuracy_decimals']}",
            ])
            if "unit" in measurement:
                lines.append(f"    unit_of_measurement: \"{measurement['unit']}\"")
            if "device_class" in measurement:
                lines.append(f"    device_class: {measurement['device_class']}")
            lines.append("")

    lines.extend([
        "script:",
        "  - id: can_sensor_route_publish",
        "    mode: queued",
        "    parameters:",
        "      node_id: uint16_t",
        "      measurement_type: uint16_t",
        "      value: float",
        "    then:",
    ])
    for node in sorted(sensor_nodes, key=lambda n: int(n["node_id"])):
        room_slug = node["room_slug"]
        for measurement in CAN_SENSOR_MEASUREMENTS:
            lines.extend([
                "      - if:",
                "          condition:",
                "            lambda: |-",
                f"              return node_id == {node['node_id']} && measurement_type == {measurement['constant']};",
                "          then:",
                "            - sensor.template.publish:",
                f"                id: {_route_target_id(room_slug, measurement)}",
                "                state: !lambda \"return value;\"",
            ])

    lines.extend([
        "",
        "  - id: can_sensor_route_publish_nan",
        "    mode: queued",
        "    parameters:",
        "      node_id: uint16_t",
        "      measurement_type: uint16_t",
        "    then:",
    ])
    for node in sorted(sensor_nodes, key=lambda n: int(n["node_id"])):
        room_slug = node["room_slug"]
        for measurement in CAN_SENSOR_MEASUREMENTS:
            lines.extend([
                "      - if:",
                "          condition:",
                "            lambda: |-",
                f"              return node_id == {node['node_id']} && measurement_type == {measurement['constant']};",
                "          then:",
                "            - sensor.template.publish:",
                f"                id: {_route_target_id(room_slug, measurement)}",
                "                state: !lambda \"return NAN;\"",
            ])

    return "\n".join(lines).rstrip() + "\n"


def render_can_sensor_routes_header(export_nodes) -> str:
    """Render the generated route metadata consumed by the HVAC CAN receiver.

    The YAML package owns ESPHome target entities and publish scripts; this C++ header owns
    the compact route table that lets the receiver refresh and expire only real routed
    (node_id, measurement_type) pairs without parsing registry data at runtime.
    """
    sensor_nodes = _sensor_route_nodes(export_nodes)
    header = (
        "#pragma once\n"
        "#include <cstddef>\n"
        "#include <cstdint>\n"
        "#include \"canbus_protocol.h\"\n\n"
        "// =============================================================================\n"
        "// generated_can_sensor_routes.h — GENERATED from registry/nodes.csv by\n"
        "// canbus/tools/generate_nodes.py. DO NOT EDIT.\n"
        "// HVAC CAN sensor route metadata for receiver freshness tracking.\n"
        "// =============================================================================\n\n"
        "struct HvacCanSensorRoute { uint16_t node_id; uint16_t measurement_type; };\n\n"
    )
    if not sensor_nodes:
        return (
            header
            + "inline constexpr const HvacCanSensorRoute *HVAC_CAN_SENSOR_ROUTES = nullptr;\n"
            + "inline constexpr std::size_t HVAC_CAN_SENSOR_ROUTES_SIZE = 0;\n"
        )

    rows = []
    for node in sorted(sensor_nodes, key=lambda n: int(n["node_id"])):
        for measurement in CAN_SENSOR_MEASUREMENTS:
            rows.append(f"    {{{node['node_id']}, {measurement['constant']}}},")
    return (
        header
        + "inline constexpr HvacCanSensorRoute HVAC_CAN_SENSOR_ROUTES[] = {\n"
        + "\n".join(rows)
        + "\n};\n"
        + "inline constexpr std::size_t HVAC_CAN_SENSOR_ROUTES_SIZE = "
        + "sizeof(HVAC_CAN_SENSOR_ROUTES) / sizeof(HVAC_CAN_SENSOR_ROUTES[0]);\n"
    )


def write_can_sensor_routes(export_nodes, repo_root: Path) -> None:
    route_path = repo_root / CAN_SENSOR_ROUTES_PATH
    route_path.parent.mkdir(parents=True, exist_ok=True)
    route_path.write_text(render_can_sensor_routes(export_nodes))
    header_path = repo_root / CAN_SENSOR_ROUTES_HEADER_PATH
    header_path.parent.mkdir(parents=True, exist_ok=True)
    header_path.write_text(render_can_sensor_routes_header(export_nodes))
    route_count = len(_sensor_route_nodes(export_nodes))
    print(f"  ✓ {route_path.name}  (HVAC CAN sensor routes, {route_count} sensor node(s))")
    print(f"  ✓ {header_path.name}  (HVAC CAN sensor route metadata)")


def write_exports(seen_node_ids, export_nodes, root: Path, repo_root: Path):
    """Validate registry/bindings.yaml against the registry, then emit every binding-derived
    artifact from one source in one run (ADR-0009 §4/§7): bindings.h (hash + table), map.json
    (read-only export), and ha_manifest_package.yaml (HA echoes the hash). Returns
    (manifest_hash, map_version) — the latter is also compiled into node_map.h for drift
    visibility (§6). Aborts (sys.exit) on an invalid manifest, writing nothing.

    `root` anchors canbus-internal outputs (protocol/); `repo_root` anchors registry/
    (elevated out of firmware/) and canbus/home-assistant/ — pass the caller's REPO_ROOT
    rather than re-deriving it here, so there is exactly one place that knows the
    repo-root depth."""
    bindings_path = repo_root / "registry" / "bindings.yaml"
    if not bindings_path.exists():
        print(f"Creating empty {bindings_path} ...")
        bindings_path.write_text("schema_version: 1\nbindings: []\n")

    manifest = bindings.load_bindings(bindings_path)
    errors = bindings.validate(manifest, set(seen_node_ids))
    if errors:
        print("ERROR: invalid binding manifest (registry/bindings.yaml):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)

    manifest_hash = bindings.canonical_hash(manifest)

    header_path = root / "protocol" / "bindings.h"
    header_path.write_text(render_bindings_header(manifest_hash, manifest["bindings"]))
    print(f"  ✓ {header_path.name}  (binding manifest hash {manifest_hash}, "
          f"{len(manifest['bindings'])} binding(s))")

    map_export = build_map_export(export_nodes, manifest_hash)
    map_path = repo_root / "registry" / "map.json"
    map_path.write_text(json.dumps(map_export, indent=2) + "\n")
    print(f"  ✓ {map_path.name}  (read-only export, map_version {map_export['map_version']}, "
          f"{len(map_export['nodes'])} node(s))")

    ha_path = repo_root / "canbus" / "home-assistant" / "ha_manifest_package.yaml"
    ha_path.write_text(render_ha_package(manifest_hash))
    print(f"  ✓ {ha_path.name}  (HA readiness heartbeat echoes the hash automatically)")

    return manifest_hash, map_export["map_version"]


def main():
    csv_path = REPO_ROOT / "registry" / "nodes.csv"
    out_dir = ROOT / "nodes"
    out_dir.mkdir(exist_ok=True)

    if not csv_path.exists():
        print(f"Creating example {csv_path} ...")
        with open(csv_path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerows(EXAMPLE_ROWS)
        print(f"  Seeded {csv_path} with current PoC example rows. Review and re-run.\n")
        return

    seen_node_ids = {}
    seen_room_board = {}  # (room, board) -> location, for the commissioned-uniqueness invariant
    seen_sensor_room_slugs = {}  # room_slug -> (node_id, row), one sensor producer per room target
    count = 0
    floor_groups = {}
    map_entries = []  # (node_id, room, board, location) -> compiled into the gateway's node_map.h
    export_nodes = []  # full rows (incl. floor + sensors) -> registry/map.json (ADR-0009 §7)
    node_files = []  # (path, content, log) staged here, written only after the manifest validates

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        # Strict header check: pre-live there is exactly one nodes.csv (the committed one),
        # so a header that isn't exactly CSV_HEADER is an error, not a legacy format — a
        # missing/misspelled column would otherwise silently disable every sensor kit or
        # drop every climate join via the row.get defaults below.
        fields = reader.fieldnames or []
        if fields != CSV_HEADER:
            print(f"ERROR: nodes.csv header {fields} does not match the expected "
                  f"{CSV_HEADER} — pre-live, update the CSV in place.", file=sys.stderr)
            sys.exit(1)
        climate_zones = None  # loaded on the first row that needs a climate-join validation
        for row in reader:
            location = row["location"]

            # Optional sensors column (ADR-0006): blank/0 = none, 1 = SHT45+SEN66 kit.
            # Strict on anything else so a registry typo can't silently drop a sensor kit.
            sensors_raw = (row.get("sensors") or "0").strip()
            if sensors_raw not in ("", "0", "1"):
                print(f"ERROR: Invalid sensors value '{sensors_raw}' on CSV row {reader.line_num} "
                      f"(valid: blank, 0, 1)", file=sys.stderr)
                sys.exit(1)
            has_sensors = sensors_raw == "1"

            try:
                node_id = int(row["node_id"])
                floor = int(row["floor"])
                room = int(row["room"])
                board = int(row["board"])
            except ValueError as exc:
                print(f"ERROR: Invalid integer value on CSV row {reader.line_num}: {exc}", file=sys.stderr)
                sys.exit(1)

            if not (0 <= node_id <= NODE_ID_MAX):
                print(f"ERROR: node_id {node_id} out of range (valid: 0-{NODE_ID_MAX})", file=sys.stderr)
                sys.exit(1)

            # node_id uniqueness is the one load-bearing invariant (it is the bus address).
            if node_id in seen_node_ids:
                print(f"ERROR: Duplicate node_id {node_id}: '{location}' vs '{seen_node_ids[node_id]}'", file=sys.stderr)
                sys.exit(1)
            seen_node_ids[node_id] = location

            if not (0 <= room <= ROOM_BOARD_MAX) or not (0 <= board <= ROOM_BOARD_MAX):
                print(f"ERROR: room/board out of range for node_id {node_id} "
                      f"(room={room}, board={board}; valid: 0-{ROOM_BOARD_MAX})", file=sys.stderr)
                sys.exit(1)

            # Optional room_slug column (spec-map-json-contract): the climate-zone join key.
            # Validated against the real climate zones — a sensors=1 node must join one.
            room_slug = (row.get("room_slug") or "").strip()
            if room_slug or has_sensors:
                if climate_zones is None:
                    climate_zones = load_climate_zones()
                slug_err = validate_room_slug(room_slug, floor, has_sensors, climate_zones)
                if slug_err:
                    print(f"ERROR: {slug_err} (node_id {node_id}, CSV row {reader.line_num})",
                          file=sys.stderr)
                    sys.exit(1)
            if has_sensors:
                previous = seen_sensor_room_slugs.get(room_slug)
                if previous:
                    prev_node_id, prev_row = previous
                    print(f"ERROR: duplicate sensors=1 room_slug '{room_slug}' "
                          f"(node_id {prev_node_id}, CSV row {prev_row}; "
                          f"node_id {node_id}, CSV row {reader.line_num})",
                          file=sys.stderr)
                    sys.exit(1)
                seen_sensor_room_slugs[room_slug] = (node_id, reader.line_num)

            # (room, board) is the gateway's location address; it must be unique among commissioned
            # nodes. (0, 0) is the unassigned placeholder (allocate_node.py seeds it) — exempt it so
            # multiple not-yet-commissioned nodes can coexist.
            if (room, board) != (0, 0):
                if (room, board) in seen_room_board:
                    print(f"ERROR: Duplicate (room, board) ({room}, {board}): "
                          f"'{location}' vs '{seen_room_board[(room, board)]}'", file=sys.stderr)
                    sys.exit(1)
                seen_room_board[(room, board)] = location

            name = f"node{node_id:03d}"
            input_id = can_id(CAT_INPUT, node_id)
            status_id = can_id(CAT_STATUS, node_id)

            yaml_content = TEMPLATE.format(
                name=name,
                node_id=node_id,
                input_id=input_id,
                status_id=status_id,
                sensor_comment=SENSOR_COMMENT if has_sensors else "",
                sensor_pkg=SENSOR_PKG if has_sensors else "",
            )

            sensor_note = "  +sensors" if has_sensors else ""
            floor_groups.setdefault(floor, []).append((node_id, room, board, location))
            map_entries.append((node_id, room, board, location))
            export_nodes.append({
                "node_id": node_id, "floor": floor, "room": room, "board": board,
                "location": location, "sensors": 1 if has_sensors else 0,
                "room_slug": room_slug,
            })
            node_files.append((
                out_dir / f"{name}.yaml", yaml_content,
                f"  ✓ {name}.yaml  Input=0x{input_id:08X}  node_id={node_id}  [{location}]{sensor_note}",
            ))
            count += 1

    # Binding-derived exports (ADR-0009 §4/§7): validate the manifest against the registry,
    # then emit bindings.h (hash + fallback table), map.json, and the generated HA package.
    # Run FIRST, before any node artifact is written: write_exports aborts (sys.exit) on an
    # invalid manifest, so validating here means a bad bindings.yaml never leaves nodes/ or
    # node_map.h half-regenerated (validate-before-persist). It also yields map_version, which
    # is compiled into node_map.h for §6 drift visibility.
    try:
        _sensor_route_nodes(export_nodes)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    manifest_hash, map_version = write_exports(seen_node_ids, export_nodes, ROOT, REPO_ROOT)

    write_can_sensor_routes(export_nodes, REPO_ROOT)

    # Manifest validated — now persist the node artifacts.
    for path, content, log in node_files:
        path.write_text(content)
        print(log)

    map_path = ROOT / "protocol" / "node_map.h"
    write_node_map(map_entries, map_version, map_path)
    print(f"  ✓ {map_path.name}  (central node_id -> room/board/name map + map_version {map_version}, compiled into the gateway)")

    print(f"\nGenerated {count} node configs in {out_dir}/")
    print(f"Binding manifest hash: {manifest_hash}  "
          f"(HA echoes it automatically via canbus/home-assistant/ha_manifest_package.yaml)")
    print("\n── CAN ID Map (Input id) ──")
    for floor in sorted(floor_groups):
        label = FLOOR_LABELS.get(floor, f"Floor {floor}")
        print(f"\n  {label} floor:")
        for nid, rm, bd, loc in sorted(floor_groups[floor]):
            print(f"    node_id={nid:<5d}  0x{can_id(CAT_INPUT, nid):08X}  (map-seed R{rm}B{bd})  {loc}")


if __name__ == "__main__":
    main()
