---
project_name: 'canbus'
user_name: 'Alberto'
date: '2026-05-29'
sections_completed: ['technology_stack', 'language_rules', 'framework_rules', 'testing_rules', 'code_quality', 'workflow', 'critical_rules']
status: 'complete'
rule_count: 32
optimized_for_llm: true
---

# Project Context for AI Agents

_Critical rules and patterns for implementing code in this project. Focus on unobvious details agents might otherwise miss._

---

## Technology Stack & Versions

- **ESPHome** — firmware framework (version pinned by your ESPHome installation; use latest stable)
- **RP2040** platform — `rpipico` board, ESPHome `rp2040` platform
- **ESP32-S3** platform — `esp32s3` variant, `esp-idf` framework (required for native TWAI CAN)
- **MCP2515** CAN controller — SPI, 16 MHz oscillator (CANBed RP2040 fixed board design)
- **W5500** Ethernet — Waveshare ESP32-S3-POE-ETH-8DI-8DO fixed pin mapping
- **PCA9554** I2C GPIO expander — address `0x20`, 8 digital outputs on gateway
- **CAN bus** — 125 kbps, standard 11-bit IDs
- **Python 3** — `generate_nodes.py` code generation (stdlib only, no extra packages)
- **Home Assistant** — integration via ESPHome native API over PoE Ethernet

## Critical Implementation Rules

### C++ Lambda Rules (ESPHome `!lambda`)

- All lambdas receiving CAN frame data have access to `x` as `std::vector<uint8_t>` — always validate `x.size() >= N` before indexing any byte.
- Lambda return types are inferred — payload builders return `std::vector<uint8_t>`, `can_id()` returns `uint32_t`. Do not cast unnecessarily.
- `canbus_protocol.h` is the single source of truth for all constants and helpers. Never inline raw bit shifts or magic numbers in YAML lambdas — use the named functions.
- ESPHome globals are accessed as `id(global_name)` inside lambdas, not as plain variables.
- `to_string()` and `std::string()` are available in ESP-IDF lambdas (gateway); use them for `homeassistant.event` string conversions.

### Python (`generate_nodes.py`)

- Uses stdlib only (`csv`, `pathlib`) — do not add external dependencies.
- The script validates: node_id 0–399, room/board 0–255, max 6 GPIOs per node, no duplicate node_ids, and no duplicate GPIOs within one node row. Add new validations here, not in the template string.
- If `nodes.csv` is missing, the script seeds the current PoC example rows (nodes 100 and 101 on GPIO20/21) and exits before generating `nodes/` output.
- Output files in `nodes/` are fully regenerated on each run — do not add logic there.

### ESPHome Framework Rules

**Package / include system:**

- Shared config lives in `common/` as packages. Nodes include them via `packages:` + `!include`.
- Per-button packages use the parameterized form:
  `btn0: !include { file: ../common/button.yaml, vars: { button_index: "0", button_gpio: "2" } }`
- All substitution variables (`${node_id}`, `${room_id}`, etc.) must be declared in the top-level `substitutions:` block of the node YAML before the `packages:` block.

**CAN bus filtering (gateway):**

- The gateway matches all frames of a given category using mask filtering: `can_id: 0x200` + `can_id_mask: 0x600` catches all CAT_INPUT frames regardless of node.
- Category bits are bits 10:9 of the 11-bit CAN ID. Mask `0x600` = `0b11000000000`.
- CAT_INPUT = 1 → base ID `0x200`; CAT_STATUS = 3 → base ID `0x600`.

**`homeassistant.event` data:**

- Data values must be strings. Use `to_string(...)` or `std::string(char_ptr)` (e.g. `room: !lambda 'return to_string(payload_room(x));'`).
- Attach a per-field `!lambda` to each data key that re-decodes directly from the frame vector `x`. This is the shipped gateway pattern (`firmware/gateway.yaml` CAT_INPUT handler) — **no globals**. A `!lambda` on the data field runs in the `on_frame` scope where `x` is in scope.
- The real constraint is narrower than "use globals": you cannot reference a variable declared in a *separate preceding* `lambda:` action, because the data block runs in its own action context. Re-decode in the field `!lambda` instead of staging.

**`on_multi_click` ordering:**

- Patterns MUST be ordered longest-first: triple → double → single → long → extra_long. ESPHome matches the first satisfied pattern; shorter patterns shadow longer ones if listed first.

**Platform differences:**

- Nodes use `rp2040` + `rpipico` board; gateway uses `esp32` + `esp32s3` variant + `esp-idf`.
- Gateway requires `esp-idf` framework for native TWAI (`esp32_can` platform). Arduino framework does not support native TWAI on ESP32-S3.
- Nodes do NOT have WiFi or API — no OTA, no web server, no logger over network.

### Testing & Validation

- **No unit test framework** — ESPHome YAML is validated by `esphome compile`. The primary "test" is a successful compile.
- **Compile before flashing:** always run `esphome compile <node>.yaml` locally before flashing. The `on_frame` + `can_id_mask` + `homeassistant.event` chain in `gateway.yaml` has not yet been compiled/tested against hardware — treat it as unverified.
- **Code generation validation:** `generate_nodes.py` prints a CAN ID map on completion. Review it for duplicate IDs and unexpected CAN addresses before flashing any batch of nodes.
- **Hardware pin verification complete:** Story 1.2 resolved GPIO20→GPIO11 for MCP2515 INT pin and confirmed button GPIOs as GPIO20–GPIO27. See `firmware/README.md` for full details.

### Code Quality & Style Rules

**File naming:**

- Node configs: `node{id:03d}.yaml` — zero-padded 3-digit node ID (e.g. `node000`, `node012`, `node100`).
- Generated files live in `nodes/` — never commit hand-edits to files in that directory.

**C++ header conventions (`canbus_protocol.h`):**

- Constants: `UPPER_SNAKE_CASE` (e.g. `CAT_INPUT`, `EVT_CLICK`, `PROTO_V1`).
- Functions: `snake_case` (e.g. `can_id()`, `button_payload()`, `event_type_str()`).
- All payload builder/decoder functions return or accept `std::vector<uint8_t>`.
- Mark all functions `inline` to avoid ODR violations across multiple includes.

**ESPHome YAML conventions:**

- ESPHome component IDs: `snake_case` (e.g. `can0`, `evt_room`, `tca9554_hub`).
- Substitution variable names: `snake_case` without `${}` in the substitutions block.
- Section headers use `# ---` comment dividers for readability in long YAML files.

**Python conventions:**

- `snake_case` for all identifiers. Constants `UPPER_SNAKE_CASE` (e.g. `FLOOR_LABELS`, `TEMPLATE`).
- Template strings use `{placeholder}` style — escape ESPHome `${...}` as `${{...}}` in the Python template.

**Comments:**

- YAML files: section-header comments (`# --- Section name ---`) are standard; inline comments only for non-obvious pin choices or hardware quirks.
- C++ header: function-level comments explain protocol byte positions, not obvious logic.

### Development Workflow Rules

**Node provisioning workflow (always in this order):**

1. Edit `nodes.csv` to add/update node entries.
2. Run `python3 generate_nodes.py` to regenerate `nodes/`.
3. Compile: `esphome compile nodes/node<id>.yaml`.
4. Flash via USB: `esphome upload nodes/node<id>.yaml` before physical installation.
5. Nodes cannot be updated wirelessly after installation — flashing is a one-shot operation.

**Gateway workflow:**

- Gateway has OTA via ESPHome (`ota: platform: esphome`) and Ethernet — can be updated remotely.
- Always recompile gateway when `canbus_protocol.h` changes to keep constants in sync.

**Protocol changes:**

- `canbus_protocol.h` is shared by both nodes and gateway. Any protocol change requires reflashing ALL affected nodes (no OTA) — treat protocol as frozen unless absolutely necessary.
- Protocol version byte (`PROTO_V1 = 0x01`) must be incremented for any breaking payload change.

**Adding a new node type or new event:**

1. Add constants to `canbus_protocol.h` first.
2. Update `button.yaml` or create a new common package.
3. Update `generate_nodes.py` template if new substitution variables are needed.
4. Update gateway `on_frame` handler and `event_type_str()` decoder.

### Critical Don't-Miss Rules

**NEVER do these:**

- **Never edit files in `nodes/` by hand.** They are generated output. All changes go through `nodes.csv` → `generate_nodes.py`.
- **Never put semantic meaning in the CAN ID.** Room, board, button, and event data belong in the 8-byte payload only. The CAN ID carries only `category` (2 bits) and `node_id` (9 bits).
- **Never assume HA event data fields are integers.** All fields in `esphome.canbus_button` and `esphome.canbus_heartbeat` are strings (`"7"`, not `7`). HA automation `event_data:` filters must use string values.
- **Never skip the `x.size()` guard in CAN frame lambdas.** Malformed or short frames will crash without it.
- **Never use Arduino framework on the gateway.** Native TWAI (`esp32_can`) requires `esp-idf`. Switching to Arduino silently breaks CAN.

**Key non-obvious facts:**

- The gateway fires `homeassistant.event` with a per-field `!lambda` that re-decodes from the frame vector `x` directly (no globals). A variable set in a *separate preceding* `lambda:` action is not in scope inside the data block (separate action context) — but a `!lambda` on the data field itself runs in `on_frame` scope and can read `x`. This per-field re-decode is a deliberate design decision (gateway HA event firing approach); do not "fix" it toward globals or the internal-API single-lambda form.
- Click detection happens on the node, not the gateway. Multi-click timing uses ESPHome's `on_multi_click` which runs locally. Do not attempt to reconstruct click sequences from raw CAN events on the gateway.
- `MSG_BUTTON_EVENT` and `MSG_HEARTBEAT` both equal `0x01` — they are distinguished by the CAN ID category (CAT_INPUT vs CAT_STATUS), not the message type byte alone.
- Node ID `0` is valid — it is not a null/unset sentinel. Node IDs start at 0.
- The `debounce_ms` substitution applies to both `delayed_on` and `delayed_off` GPIO filters — it is not the same as `on_multi_click` timing thresholds, which are hardcoded in `button.yaml`.

---

## Usage Guidelines

**For AI agents:** Read this file before implementing any code. Follow all rules exactly. When in doubt about CAN ID vs payload semantics, re-read the CAN ID section. Never touch `nodes/` directly.

**For humans:** Update when hardware pins are verified, when protocol version bumps, or when new common packages are added. Remove rules that become obvious over time.

_Last updated: 2026-06-01_
