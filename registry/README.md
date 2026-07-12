# Registry — house system-of-record

`registry/` is the single, git-versioned home for the house's unrebuildable
data (AD-3). One mechanism (generator, push gate, canonicalization, manifest
hash) is owned by canbus; each data file has exactly one owning system.

| File | Owner | Notes |
| --- | --- | --- |
| `nodes.csv` | canbus | node_id / floor / room / board / location; validated schema |
| `node_id_hwm` | canbus | persistent monotonic node_id high-water mark |
| `bindings.yaml` | lighting | binding manifest (schema, ops, fan-out) |
| `map.json` | generated | read-only export; consumer contract owned by hvac (frozen, `spec-map-json-contract`) |

A schema change to `nodes.csv` or `bindings.yaml` requires that file's owning
system. A mechanism change (generator, canonicalization, push gate) requires
canbus. One push gate (`canbus/tools/check_registry_pushed.py`)
covers the whole registry.

The compiled artifacts derived from this data (`canbus/protocol/node_map.h`,
`canbus/protocol/bindings.h`) are canbus-owned and covered by the
same push gate — an uncommitted compiled header is as unsafe to flash as an
uncommitted registry file.

## Edit Workflow

After changing `nodes.csv` or `bindings.yaml`, regenerate and test the derived
artifacts before committing:

```bash
python3 canbus/tools/generate_nodes.py
python3 canbus/tests/test_generate_exports.py
git diff -- canbus hvac registry
```

Commit the registry source and generated artifacts together. Do not flash a
controller from a local-only registry commit; push first, then run the gate:

```bash
python3 canbus/tools/check_registry_pushed.py
```

The gate checks that guarded registry/generated paths are clean and that `HEAD`
is reachable from a remote. That makes the remote repository the backup for
unrebuildable house data before firmware is reflashed.
