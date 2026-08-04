# Registry — house system-of-record

`registry/` is the single, git-versioned home for the house's unrebuildable
data (AD-3). One mechanism (generator, push gate, canonicalization, manifest
hash) is owned by canbus; each data file has exactly one owning system.

| File | Owner | Notes |
| --- | --- | --- |
| `nodes.csv` | canbus | node_id / floor / room / board / location / profile / room_slug; validated schema |
| `node_id_hwm` | canbus | persistent monotonic node_id high-water mark |
| `bindings.yaml` | lighting | binding manifest (schema, ops, fan-out) |
| `map.json` | generated | read-only export; consumer contract owned by hvac (frozen, `spec-map-json-contract`) |

A schema change to `nodes.csv` or `bindings.yaml` requires that file's owning
system. A mechanism change (generator, canonicalization, push gate) requires
canbus. One push gate (`canbus/tools/check_registry_pushed.py`)
covers the whole registry.

### `nodes.csv` — the `profile` column (ADR-0017)

Each row's `profile` is a single value naming what the board *is*, and it selects
the ESPHome packages the generated config composes:

| `profile` | Deployment |
| --- | --- |
| `buttons` | wall plate, no sensing |
| `buttons+sensors` | wall plate + the ADR-0006 SHT45/SEN66 kit |
| `sensors` | sensor puck, no switch plate |
| `bridge` | ADR-0005 segment forwarder (CANBed + a second MCP2515) |
| `buttons+bridge` | wall plate that is also a forwarder — where a segment splits at a button box |

Single-valued on purpose: ADR-0005 requires single-purpose bridge firmware, so a
one-of-N column makes "bridge AND sensors" impossible to write rather than something
validation has to catch. Buttons are the one thing allowed to share a board with a
bridge (they add no blocking I/O); the sensor kit is not, and never will be.

Blank is **not** a shorthand for anything — the generator rejects it, so a dropped
cell can never silently downgrade a sensor node or a bridge. The valid values live in
`PROFILES` in `canbus/tools/generate_nodes.py`; a sensor-bearing profile also requires
a `room_slug`.

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
git diff -- canbus climate registry
```

Commit the registry source and generated artifacts together. Do not flash a
controller from a local-only registry commit; push first, then run the gate:

```bash
python3 canbus/tools/check_registry_pushed.py
```

The gate checks that guarded registry/generated paths are clean and that `HEAD`
is reachable from a remote. That makes the remote repository the backup for
unrebuildable house data before firmware is reflashed.
