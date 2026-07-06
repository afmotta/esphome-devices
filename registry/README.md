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
canbus. One push gate (`canbus/firmware/tools/check_registry_pushed.py`)
covers the whole registry.

The compiled artifacts derived from this data (`canbus/firmware/protocol/node_map.h`,
`canbus/firmware/protocol/bindings.h`) are canbus-owned and covered by the
same push gate — an uncommitted compiled header is as unsafe to flash as an
uncommitted registry file.
