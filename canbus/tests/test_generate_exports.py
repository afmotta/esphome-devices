#!/usr/bin/env python3
"""
Standalone native test for the ADR-0009 §4/§7 export pipeline in tools/generate_nodes.py
(no ESPHome required). Run:  python3 canbus/tests/test_generate_exports.py

Covers the pure renderers added for the export slice:
  - build_map_export: field shape, node-order independence, deterministic map_version that
    is sensitive to node and binding-hash changes (the "no wall-clock" stamp decision).
  - render_bindings_header: empty manifest -> null table + size 0; populated -> sorted
    BINDINGS[] rows; the hash and binding_find accessor are always present.
  - render_ha_package: the manifest hash is baked into the generated heartbeat.
  - room_slug climate join (spec-map-json-contract): the FLOOR_SLUGS conversion table, the
    known-zone list read from hvac/rooms/**, and validate_room_slug's branches.
"""

import json
import contextlib
import io
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import generate_nodes as g  # noqa: E402

NODES = [
    {"node_id": 101, "floor": 0, "room": 8, "board": 0, "location": "Living room",
     "sensors": 0, "room_slug": ""},
    {"node_id": 100, "floor": 0, "room": 7, "board": 0, "location": "Hallway",
     "sensors": 1, "room_slug": "anticamera"},
]
HASH = "d66767448ba37b2f"
PROTOCOL_PATH = Path(__file__).resolve().parents[1] / "protocol" / "canbus_protocol.h"


def _write_temp_climate_zones(repo_root, extra_rooms=None):
    rooms = {
        "ground_floor": ["anticamera", "soggiorno"],
        "first_floor": ["camera_nord"],
        "second_floor": ["sottotetto"],
    }
    if extra_rooms:
        for floor_slug, room_slugs in extra_rooms.items():
            rooms.setdefault(floor_slug, []).extend(room_slugs)
    for floor_slug, room_slugs in rooms.items():
        floor_dir = repo_root / "hvac" / "rooms" / floor_slug
        floor_dir.mkdir(parents=True, exist_ok=True)
        for room_slug in room_slugs:
            (floor_dir / f"{room_slug}.yaml").write_text(
                "defaults:\n"
                f"  room_slug: {room_slug}\n"
            )


def _prepare_temp_generator_repo(repo_root, nodes_csv, extra_rooms=None):
    root = repo_root / "canbus"
    for sub in ("protocol", "home-assistant"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    (repo_root / "registry").mkdir()
    (repo_root / "registry" / "nodes.csv").write_text(nodes_csv)
    (repo_root / "registry" / "bindings.yaml").write_text("schema_version: 1\nbindings: []\n")
    _write_temp_climate_zones(repo_root, extra_rooms)
    return root


def _run_temp_generator(repo_root, root):
    saved_root, saved_repo_root = g.ROOT, g.REPO_ROOT
    stdout, stderr = io.StringIO(), io.StringIO()
    g.ROOT, g.REPO_ROOT = root, repo_root
    try:
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                g.main()
                code = 0
            except SystemExit as e:
                code = e.code
    finally:
        g.ROOT, g.REPO_ROOT = saved_root, saved_repo_root
    return code, stdout.getvalue(), stderr.getvalue()


def _assert_temp_generator_rejects(nodes_csv, expected_error, extra_rooms=None):
    with tempfile.TemporaryDirectory() as d:
        repo_root = Path(d)
        root = _prepare_temp_generator_repo(repo_root, nodes_csv, extra_rooms)
        code, _stdout, stderr = _run_temp_generator(repo_root, root)
        route_path = repo_root / g.CAN_SENSOR_ROUTES_PATH
        assert code == 1
        assert expected_error in stderr
        assert not route_path.exists(), "CAN sensor route artifact written before abort"
        assert not (repo_root / "registry" / "map.json").exists(), "map.json written before abort"
        assert not (root / "protocol" / "bindings.h").exists(), "bindings.h written before abort"
        assert list((root / "nodes").glob("*.yaml")) == [], "node configs written before abort"


def test_repo_root_depth_invariant():
    # Guards the depth assumption baked into this file's temp fixtures (ROOT nested one
    # level below REPO_ROOT, mirroring canbus/ under the real repo root since Phase 6a
    # flattened the old firmware/ level). If a future refactor changes the real nesting,
    # this fails loudly instead of the fixtures silently drifting out of sync with
    # generate_nodes.py's actual path arithmetic.
    assert g.REPO_ROOT == g.ROOT.parent


def test_map_export_shape_and_node_sort():
    m = g.build_map_export(NODES, HASH)
    assert m["schema_version"] == 1
    assert m["manifest_hash"] == HASH
    assert len(m["map_version"]) == 16
    # Nodes are sorted by node_id regardless of input order, and carry the full §7 field set
    # incl. the frozen-contract room_slug join key (empty = no climate zone).
    assert [n["node_id"] for n in m["nodes"]] == [100, 101]
    assert m["nodes"][0] == {
        "node_id": 100, "floor": 0, "room": 7, "board": 0,
        "location": "Hallway", "sensors": 1, "room_slug": "anticamera",
    }
    assert m["nodes"][1]["room_slug"] == ""
    # Serializable as the committed map.json.
    json.dumps(m)


def test_map_version_order_invariant():
    # Reordering the CSV rows must not change the export's identity.
    a = g.build_map_export(NODES, HASH)
    b = g.build_map_export(list(reversed(NODES)), HASH)
    assert a == b
    assert a["map_version"] == b["map_version"]


def test_map_version_sensitive_to_nodes_and_hash():
    base = g.build_map_export(NODES, HASH)
    moved = [dict(n) for n in NODES]
    moved[0]["room"] = 99
    assert g.build_map_export(moved, HASH)["map_version"] != base["map_version"]
    # A binding-only change (new manifest hash) also rolls the map version.
    assert g.build_map_export(NODES, "ffffffffffffffff")["map_version"] != base["map_version"]


def test_bindings_header_empty():
    h = g.render_bindings_header(HASH, [])
    assert f'BINDINGS_MANIFEST_HASH[] = "{HASH}"' in h
    assert "const BindingEntry *BINDINGS = nullptr;" in h
    assert "BINDINGS_SIZE = 0;" in h
    assert "binding_find(" in h


def test_bindings_header_populated_and_sorted():
    rows = [
        {"node_id": 101, "button": 3, "relay": 2, "op": "on"},
        {"node_id": 100, "button": 0, "relay": 0, "op": "toggle"},
    ]
    h = g.render_bindings_header(HASH, rows)
    assert "inline constexpr BindingEntry BINDINGS[] = {" in h
    assert "sizeof(BINDINGS)" in h
    # Keyed by (node_id, button) — no event (fallback is single-click only). Each entry carries
    # a {relay_count, relays-array} list (ADR-0009 open item 1). Sorted: node 100 precedes 101.
    i100 = h.index('{100, 0, 1, BINDING_RELAYS_0, "toggle"}')
    i101 = h.index('{101, 3, 1, BINDING_RELAYS_1, "on"}')
    assert i100 < i101
    assert "inline constexpr uint8_t BINDING_RELAYS_0[] = {0};" in h
    assert "inline constexpr uint8_t BINDING_RELAYS_1[] = {2};" in h


def test_bindings_header_multi_relay_fanout():
    # A comma-list scalar fans one click out to several relays; the compiled entry holds the
    # normalized (sorted, de-duplicated) relay list with its count (ADR-0009 open item 1).
    h = g.render_bindings_header(
        HASH, [{"node_id": 100, "button": 1, "relay": "2,0,1", "op": "toggle"}]
    )
    assert "inline constexpr uint8_t BINDING_RELAYS_0[] = {0, 1, 2};" in h
    assert '{100, 1, 3, BINDING_RELAYS_0, "toggle"}' in h


def test_node_map_emits_version_constant():
    # node_map.h carries NODE_MAP_VERSION so the gateway can expose its compiled map
    # identity as a drift-visibility diagnostic (ADR-0009 §6), without breaking the
    # frozen-additive struct/accessor contract.
    entries = [(101, 8, 0, "Living room"), (100, 7, 0, 'Hall "A"')]
    version = "0123456789abcdef"
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "node_map.h"
        g.write_node_map(entries, version, path)
        h = path.read_text()
    assert f'NODE_MAP_VERSION[] = "{version}";' in h
    # The existing contract is intact: struct, sentinel, accessors, sorted rows, escaping.
    assert "struct NodeMapEntry" in h
    assert "NODE_MAP_UNKNOWN = 0xFF" in h
    assert "node_map_name(" in h
    assert h.index('{100, 7, 0, "Hall \\"A\\""},') < h.index('{101, 8, 0, "Living room"},')


def test_generator_node_map_version_matches_map_json():
    # ADR-0009 §6 drift correlation: the gateway-compiled NODE_MAP_VERSION must equal the
    # map_version published in registry/map.json, or a dashboard comparison is meaningless.
    nodes_csv = "node_id,floor,room,board,location,sensors,room_slug\n100,0,7,0,Hall,0,\n"
    with tempfile.TemporaryDirectory() as d:
        repo_root = Path(d)
        root = _prepare_temp_generator_repo(repo_root, nodes_csv)
        code, _stdout, stderr = _run_temp_generator(repo_root, root)
        assert code == 0, stderr
        map_version = json.loads((repo_root / "registry" / "map.json").read_text())["map_version"]
        header = (root / "protocol" / "node_map.h").read_text()
        assert f'NODE_MAP_VERSION[] = "{map_version}";' in header


def test_generator_aborts_before_writing_node_files():
    # validate-before-persist: an invalid bindings.yaml must abort the generator before any
    # node artifact (nodes/*.yaml, node_map.h) is written, so a bad manifest can't leave the
    # tree half-regenerated. Driven against a temp ROOT/REPO_ROOT so the real registry is
    # untouched. ROOT mirrors the real one-level nesting (canbus/) below REPO_ROOT, where
    # registry/ lives (migration Phase 1 layout, flattened further in Phase 6a).
    saved_root, saved_repo_root = g.ROOT, g.REPO_ROOT
    with tempfile.TemporaryDirectory() as d:
        repo_root = Path(d)
        root = repo_root / "canbus"
        for sub in ("protocol", "gateway"):
            (root / sub).mkdir(parents=True)
        (repo_root / "registry").mkdir()
        (repo_root / "registry" / "nodes.csv").write_text(
            "node_id,floor,room,board,location,sensors,room_slug\n100,0,7,0,Hall,0,\n"
        )
        # node_id 999 is not in nodes.csv -> manifest invalid -> generator aborts.
        (repo_root / "registry" / "bindings.yaml").write_text(
            "schema_version: 1\nbindings:\n"
            "  - node_id: 999\n    button: 0\n    relay: 0\n    op: toggle\n"
        )
        g.ROOT, g.REPO_ROOT = root, repo_root
        try:
            try:
                g.main()
                raise AssertionError("expected SystemExit on an invalid manifest")
            except SystemExit as e:
                assert e.code == 1
            assert list((root / "nodes").glob("*.yaml")) == [], "node configs written before abort"
            assert not (root / "protocol" / "node_map.h").exists(), "node_map.h written before abort"
        finally:
            g.ROOT, g.REPO_ROOT = saved_root, saved_repo_root


def test_floor_slugs_conversion_table():
    # CAP-2 (spec-map-json-contract): the fixed canbus-floor -> climate-floor-slug table.
    # Frozen contract — a consumer resolves floor slugs through exactly this mapping.
    assert g.FLOOR_SLUGS == {0: "ground_floor", 1: "first_floor", 2: "second_floor"}


def test_load_climate_zones_reads_real_room_packages():
    # The known-zone list comes from the climate room packages (file contents, not
    # filenames): ground_floor/bagno.yaml declares bagno_terra — the documented trap.
    zones = g.load_climate_zones()
    assert len(zones) == 14, f"expected 14 climate zones, got {len(zones)}: {sorted(zones)}"
    assert zones["bagno_terra"] == "ground_floor"
    assert zones["soggiorno"] == "ground_floor"
    assert zones["camera_nord"] == "first_floor"
    assert zones["sottotetto"] == "second_floor"


def test_validate_room_slug_branches():
    zones = {"soggiorno": "ground_floor", "camera_nord": "first_floor"}
    ok = g.validate_room_slug
    # Blank slug: fine without sensors (non-zone space), rejected with sensors=1.
    assert ok("", 0, False, zones) is None
    assert "requires a room_slug" in ok("", 0, True, zones)
    # Freehand / unknown slugs are rejected.
    assert "unknown room_slug" in ok("living_room", 0, False, zones)
    # Known slug on the right floor passes, with or without sensors.
    assert ok("soggiorno", 0, False, zones) is None
    assert ok("camera_nord", 1, True, zones) is None
    # Numeric floor must convert (FLOOR_SLUGS) to the zone's climate floor.
    assert "does not match" in ok("camera_nord", 0, False, zones)
    # A floor outside the conversion table cannot host a climate zone.
    assert "does not match" in ok("soggiorno", 3, False, zones)


def test_generator_rejects_stale_csv_header():
    # Pre-live there is exactly one nodes.csv (the committed one): a header that isn't
    # exactly CSV_HEADER aborts — no legacy tolerance, no silent row.get defaults. Schema
    # changes edit CSV_HEADER and the committed CSV together, in place (no migration shims).
    # ROOT mirrors the real one-level nesting (canbus/) below REPO_ROOT, where registry/
    # lives (migration Phase 1 layout, flattened further in Phase 6a).
    saved_root, saved_repo_root = g.ROOT, g.REPO_ROOT
    with tempfile.TemporaryDirectory() as d:
        repo_root = Path(d)
        root = repo_root / "canbus"
        (root / "protocol").mkdir(parents=True)
        (repo_root / "registry").mkdir()
        (repo_root / "registry" / "nodes.csv").write_text(
            "node_id,floor,room,board,location,sensors\n100,0,7,0,Hall,0\n"
        )
        g.ROOT, g.REPO_ROOT = root, repo_root
        try:
            try:
                g.main()
                raise AssertionError("expected SystemExit on a stale CSV header")
            except SystemExit as e:
                assert e.code == 1
            assert list((root / "nodes").glob("*.yaml")) == [], "node configs written before abort"
        finally:
            g.ROOT, g.REPO_ROOT = saved_root, saved_repo_root


def test_ha_package_bakes_hash():
    p = g.render_ha_package(HASH)
    assert f'manifest_hash: "{HASH}"' in p
    assert "esphome.canbus_gateway_ha_readiness_heartbeat" in p
    assert "GENERATED" in p


def test_can_sensor_routes_empty_registry():
    p = g.render_can_sensor_routes([dict(n, sensors=0, room_slug="") for n in NODES])
    assert "can_sensor_routes.yaml" in p
    assert "DO NOT EDIT" in p
    assert "No sensors=1 registry rows" in p
    assert "substitutions: {}" in p
    assert "id: can_sensor_route_publish" in p
    assert "id: can_sensor_route_publish_nan" in p
    assert "(void) node_id;" in p
    assert "sensor:" not in p


def test_can_sensor_routes_empty_registry_has_noop_scripts():
    p = g.render_can_sensor_routes([dict(n, sensors=0, room_slug="") for n in NODES])
    assert "script:" in p
    assert "id: can_sensor_route_publish" in p
    assert "id: can_sensor_route_publish_nan" in p
    assert "(void) measurement_type;" in p
    assert "(void) value;" in p
    assert "sensor:" not in p


def test_can_sensor_routes_mixed_rows_and_targets():
    p = g.render_can_sensor_routes(NODES)
    assert "../../../canbus/protocol/canbus_protocol.h" in p
    assert "id: anticamera_temp_can" in p
    assert "id: anticamera_humidity_can" in p
    assert "id: anticamera_pm1_0_can" in p
    assert "id: anticamera_pm2_5_can" in p
    assert "id: anticamera_pm4_0_can" in p
    assert "id: anticamera_pm10_can" in p
    assert "id: anticamera_voc_index_can" in p
    assert "id: anticamera_nox_index_can" in p
    assert "id: anticamera_co2_can" in p
    assert "id: anticamera_sen66_temp_can" in p
    assert "id: anticamera_sen66_humidity_can" in p
    assert "living_room" not in p
    for measurement in g.CAN_SENSOR_MEASUREMENTS:
        assert measurement["constant"] in p
        assert f"measurement_type == {measurement['constant']}" in p
    assert "id: can_sensor_route_publish" in p
    assert "id: can_sensor_route_publish_nan" in p
    assert 'state: !lambda "return value;"' in p
    assert 'state: !lambda "return NAN;"' in p


def test_can_sensor_routes_deterministic_output():
    a = g.render_can_sensor_routes(NODES)
    b = g.render_can_sensor_routes(list(reversed(NODES)))
    c = g.render_can_sensor_routes([dict(n) for n in NODES])
    assert a == b == c


def test_can_sensor_routes_header_empty_registry():
    h = g.render_can_sensor_routes_header([dict(n, sensors=0, room_slug="") for n in NODES])
    assert "generated_can_sensor_routes.h" in h
    assert "DO NOT EDIT" in h
    assert "HvacCanSensorRoute" in h
    assert "HVAC_CAN_SENSOR_ROUTES = nullptr" in h
    assert "HVAC_CAN_SENSOR_ROUTES_SIZE = 0" in h


def test_can_sensor_routes_header_mixed_rows_and_constants():
    h = g.render_can_sensor_routes_header(NODES)
    assert "#include \"canbus_protocol.h\"" in h
    assert "inline constexpr HvacCanSensorRoute HVAC_CAN_SENSOR_ROUTES[]" in h
    assert "{100, SENSOR_SHT45_TEMP}" in h
    assert "{100, SENSOR_SEN66_CO2}" in h
    assert "{101," not in h
    for measurement in g.CAN_SENSOR_MEASUREMENTS:
        assert f"{{100, {measurement['constant']}}}" in h


def test_can_sensor_measurements_match_protocol_constants():
    header = PROTOCOL_PATH.read_text()
    protocol_constants = set(re.findall(r"inline constexpr uint16_t (SENSOR_(?:SHT45|SEN66)_[A-Z0-9_]+) =", header))
    route_constants = {measurement["constant"] for measurement in g.CAN_SENSOR_MEASUREMENTS}
    assert route_constants == protocol_constants


def test_can_sensor_routes_room_move_retargets_cleanly():
    original = g.render_can_sensor_routes(NODES)
    moved = [dict(n) for n in NODES]
    moved[1]["room_slug"] = "soggiorno"
    moved_output = g.render_can_sensor_routes(moved)
    assert "id: anticamera_temp_can" in original
    assert "id: soggiorno_temp_can" not in original
    assert "id: soggiorno_temp_can" in moved_output
    assert "id: anticamera_temp_can" not in moved_output


def test_generator_rejects_blank_sensor_room_before_route_write():
    _assert_temp_generator_rejects(
        "node_id,floor,room,board,location,sensors,room_slug\n"
        "100,0,7,0,Hall,1,\n",
        "sensors=1 requires a room_slug",
    )


def test_generator_rejects_unknown_sensor_room_before_route_write():
    _assert_temp_generator_rejects(
        "node_id,floor,room,board,location,sensors,room_slug\n"
        "100,0,7,0,Hall,1,unknown_room\n",
        "unknown room_slug 'unknown_room'",
    )


def test_generator_rejects_floor_mismatched_sensor_room_before_route_write():
    _assert_temp_generator_rejects(
        "node_id,floor,room,board,location,sensors,room_slug\n"
        "100,1,7,0,Hall,1,anticamera\n",
        "does not match room_slug 'anticamera'",
    )


def test_generator_rejects_duplicate_sensor_room_before_route_write():
    _assert_temp_generator_rejects(
        "node_id,floor,room,board,location,sensors,room_slug\n"
        "100,0,7,0,Hall,1,anticamera\n"
        "101,0,8,0,Living room,1,anticamera\n",
        "duplicate sensors=1 room_slug 'anticamera'",
    )


def test_generator_rejects_sensor_room_slug_that_cannot_form_esphome_ids():
    _assert_temp_generator_rejects(
        "node_id,floor,room,board,location,sensors,room_slug\n"
        "100,0,7,0,Hall,1,123room\n",
        "cannot be used as an ESPHome id prefix",
        extra_rooms={"ground_floor": ["123room"]},
    )


def test_generator_writes_can_sensor_routes_idempotently():
    nodes_csv = (
        "node_id,floor,room,board,location,sensors,room_slug\n"
        "100,0,7,0,Hall,1,anticamera\n"
        "101,0,8,0,Living room,0,\n"
    )
    with tempfile.TemporaryDirectory() as d:
        repo_root = Path(d)
        root = _prepare_temp_generator_repo(repo_root, nodes_csv)
        route_path = repo_root / g.CAN_SENSOR_ROUTES_PATH

        first_code, _first_stdout, first_stderr = _run_temp_generator(repo_root, root)
        assert first_code == 0, first_stderr
        first = route_path.read_text()

        second_code, _second_stdout, second_stderr = _run_temp_generator(repo_root, root)
        assert second_code == 0, second_stderr
        assert route_path.read_text() == first
        assert "id: anticamera_temp_can" in first


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\nAll {len(tests)} export-pipeline tests passed.")


if __name__ == "__main__":
    main()
