#!/usr/bin/env python3
"""
Standalone native test for tools/bindings.py (no ESPHome required).
Run:  python3 canbus/tests/test_bindings.py

Covers the ADR-0009 §3 canonical-hash contract (determinism under key/binding/whitespace
reordering, sensitivity to data changes, empty-manifest stability) and the strict-subset
reader + registry validation (unknown node_id, duplicate key, bad op, missing key).
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import bindings  # noqa: E402


def _parse(text: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as f:
        f.write(text)
        path = Path(f.name)
    try:
        return bindings.load_bindings(path)
    finally:
        path.unlink()


NODE_IDS = {100, 101}

# Same data, different surface form: reordered bindings, reordered keys within a binding,
# extra blank lines, comments, and varied whitespace. Must hash identically.
FORM_A = """\
schema_version: 1
bindings:
  - node_id: 100
    button: 0
    relay: 0
    op: toggle
  - node_id: 101
    button: 3
    relay: 2
    op: on
"""

FORM_B = """\
# binding manifest (reformatted)
schema_version: 1

bindings:
  - op: on            # key order shuffled
    node_id: 101
    relay: 2
    button: 3
  - op: toggle
    node_id: 100
    relay: 0
    button: 0
"""


def test_hash_determinism():
    a = _parse(FORM_A)
    b = _parse(FORM_B)
    assert bindings.validate(a, NODE_IDS) == []
    assert bindings.validate(b, NODE_IDS) == []
    assert bindings.canonical_hash(a) == bindings.canonical_hash(b), "reordering changed the hash"
    assert len(bindings.canonical_hash(a)) == 16


def test_hash_sensitivity():
    base = _parse(FORM_A)
    changed = _parse(FORM_A.replace("op: toggle", "op: on"))
    assert bindings.canonical_hash(base) != bindings.canonical_hash(changed), "op change did not flip hash"


def test_empty_manifest_stable():
    e1 = _parse("schema_version: 1\nbindings: []\n")
    e2 = _parse("# nothing bound yet\nschema_version: 1\nbindings: []\n")
    assert bindings.validate(e1, NODE_IDS) == []
    assert bindings.canonical_hash(e1) == bindings.canonical_hash(e2)
    assert bindings.canonical_hash(e1) != bindings.canonical_hash(_parse(FORM_A))


def test_scalar_typing():
    p = _parse(FORM_A)
    b0 = p["bindings"][0]
    assert b0["node_id"] == 100 and isinstance(b0["node_id"], int)
    assert b0["op"] == "toggle" and isinstance(b0["op"], str)


def test_validation_unknown_node_id():
    p = _parse(FORM_A.replace("node_id: 101", "node_id: 999"))
    errs = bindings.validate(p, NODE_IDS)
    assert any("999" in e and "registry" in e for e in errs), errs


def test_validation_duplicate_key():
    dup = """\
schema_version: 1
bindings:
  - node_id: 100
    button: 0
    relay: 0
    op: toggle
  - node_id: 100
    button: 0
    relay: 1
    op: on
"""
    errs = bindings.validate(_parse(dup), NODE_IDS)
    assert any("duplicate" in e for e in errs), errs


def test_validation_bad_op_and_missing_key():
    bad_op = _parse(FORM_A.replace("op: toggle", "op: explode"))
    assert any("explode" in e for e in bindings.validate(bad_op, NODE_IDS))

    missing = """\
schema_version: 1
bindings:
  - node_id: 100
    button: 0
    op: toggle
"""
    assert any("missing" in e for e in bindings.validate(_parse(missing), NODE_IDS))


def test_valid_ops_frozen_subset():
    # ("on", "off", "toggle") must remain accepted (frozen-additive per ADR-0013 open item 2);
    # removing one should fail here, not just change validate()'s behavior silently.
    assert set(("on", "off", "toggle")) <= set(bindings.VALID_OPS)


def test_validation_button_out_of_range():
    # button is the gesture index into the standard 8-button set (0-7). Outside that range
    # is a silently dead binding (no such button exists), so reject it at validation.
    too_high = bindings.validate(_parse(FORM_A.replace("button: 3", "button: 8")), NODE_IDS)
    assert any("button" in e and "8" in e for e in too_high), too_high
    negative = bindings.validate(_parse(FORM_A.replace("button: 0", "button: -1")), NODE_IDS)
    assert any("button" in e for e in negative), negative
    # An in-range button (0-7) stays valid.
    assert bindings.validate(_parse(FORM_A.replace("button: 3", "button: 7")), NODE_IDS) == []


def test_multi_relay_parse_and_validate():
    # One click → several relays via a comma-list scalar (no nesting). parse_relays
    # normalizes to a sorted, de-duplicated int list; the binding validates clean.
    assert bindings.parse_relays(0) == [0]
    assert bindings.parse_relays("0,1,2") == [0, 1, 2]
    assert bindings.parse_relays("2,0,0") == [0, 2], "not de-duplicated/sorted"
    fan = _parse(FORM_A.replace("relay: 0", 'relay: "0,1,2"'))
    assert bindings.validate(fan, NODE_IDS) == []


def test_multi_relay_hash_representation_independent():
    # "2,0", "0,2", and "0, 2 " are the same fan-out and must hash identically; and a single
    # channel as int 0 vs scalar "0" must agree too (canonical_hash normalizes relay).
    a = _parse(FORM_A.replace("relay: 0", 'relay: "0,2"'))
    b = _parse(FORM_A.replace("relay: 0", 'relay: "2, 0 "'))
    assert bindings.canonical_hash(a) == bindings.canonical_hash(b)
    single_int = _parse(FORM_A)
    single_str = _parse(FORM_A.replace("relay: 0", 'relay: "0"'))
    assert bindings.canonical_hash(single_int) == bindings.canonical_hash(single_str)
    # But a different channel set really does change the hash.
    assert bindings.canonical_hash(a) != bindings.canonical_hash(single_int)


def test_validation_relay_out_of_bounds():
    # relay is a 0-based id into the single 32-channel Waveshare Relay 32CH bank
    # (ADR-0014). Outside 0-31 is a silently dead binding (no such relay exists),
    # so reject it at validation.
    too_high = bindings.validate(_parse(FORM_A.replace("relay: 0", "relay: 32")), NODE_IDS)
    assert any("relay" in e and "32" in e for e in too_high), too_high
    # The top of the valid range stays valid.
    assert bindings.validate(_parse(FORM_A.replace("relay: 0", "relay: 31")), NODE_IDS) == []
    # A fan-out with one out-of-range channel is rejected for that channel.
    fan_out = bindings.validate(_parse(FORM_A.replace("relay: 0", 'relay: "0,32"')), NODE_IDS)
    assert any("relay" in e and "32" in e for e in fan_out), fan_out


def test_multi_relay_bad_channel_rejected():
    not_int = bindings.validate(_parse(FORM_A.replace("relay: 0", 'relay: "0,x"')), NODE_IDS)
    assert any("relay" in e for e in not_int), not_int
    negative = bindings.validate(_parse(FORM_A.replace("relay: 0", 'relay: "-1,2"')), NODE_IDS)
    assert any("relay" in e and ">= 0" in e for e in negative), negative
    empty = bindings.validate(_parse(FORM_A.replace("relay: 0", 'relay: ""')), NODE_IDS)
    assert any("relay" in e for e in empty), empty


def test_validation_bad_schema_version():
    assert any("schema_version" in e for e in bindings.validate(_parse("schema_version: 2\nbindings: []\n"), NODE_IDS))


def test_reader_rejects_unknown_top_key():
    try:
        _parse("schema_version: 1\nbogus: 5\nbindings: []\n")
    except bindings.BindingError:
        return
    raise AssertionError("reader accepted an unknown top-level key")


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\nAll {len(tests)} binding-manifest tests passed.")


if __name__ == "__main__":
    main()
