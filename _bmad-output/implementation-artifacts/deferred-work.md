## Remaining Epic 1 Residuals (2026-06-01)

- **`button_index` is still not range-checked inside `button_payload`** [`firmware/common/canbus_protocol.h`] — Epic 1 continues to enforce the 0–5 invariant at the generator/config layer (`generate_nodes.py` emits at most 6 buttons, `button.yaml` uses those generated indices). No wire-spec-defined invalid-button encoding was added in this follow-up.

## Closed During Epic 1 Deferred-Work Follow-Up (2026-06-01)

- **Heartbeat room/board decoding fixed** [`firmware/common/canbus_protocol.h`, `firmware/gateway.yaml`] — added `payload_heartbeat_room()` / `payload_heartbeat_board()` and switched the gateway heartbeat handler to use them.
- **Header-only constants promoted to `inline constexpr`** [`firmware/common/canbus_protocol.h`] — removes the internal-linkage concern from the previous `static const` definitions while preserving the approved wire values.
- **Generator now rejects duplicate GPIOs in a row** [`firmware/generate_nodes.py`] — rows such as `"20,20"` now fail with a clear error and non-zero exit.
- **Missing-CSV bootstrap updated and made non-destructive** [`firmware/generate_nodes.py`] — the script now seeds current PoC rows (`100` / `101`, GPIO20/21) and exits before generating node YAMLs.
- **Pinned schematic references recorded** [`firmware/README.md`] — README citations now point to commit `fdefed9e521864c67a05bf19a4e5046428b86662` instead of `main`.
- **`can_clock: "16MHZ"` validated** [`firmware/nodes/node100.yaml`] — `esphome compile nodes/node100.yaml` succeeded with the current spelling.
- **Generated node INT pin audit passed** [`firmware/nodes/node100.yaml`, `firmware/nodes/node101.yaml`] — current generated nodes already use `can_int_pin: "GPIO11"`.
- **Include-path concern not reproducible** [`firmware/common/base_node.yaml`, `firmware/gateway.yaml`] — `esphome config` succeeded both from repo root (`firmware/nodes/node100.yaml`) and from `firmware/` (`nodes/node100.yaml`).
- **`MSG_BUTTON_EVENT` / `MSG_HEARTBEAT` sharing `0x01` remains intentional** [`firmware/common/canbus_protocol.h`] — confirmed by the PRD wire spec; category bits disambiguate button vs heartbeat frames.
- **`assert`-based validation note was stale** [`firmware/generate_nodes.py`] — generator validation already used explicit `print + sys.exit(1)` checks before this follow-up.
- **SPI pin corrections are already propagated downstream** [`firmware/generate_nodes.py`, `firmware/nodes/node100.yaml`, `firmware/nodes/node101.yaml`] — template and generated nodes now carry GPIO2 / GPIO3 / GPIO4 and GPIO11.

## Deferred from: code review of 2-2-per-button-package-5-event-types-via-on-multi-click.md (2026-06-02)

- **Long/extra-long press share exact 3s boundary** [`firmware/common/button.yaml`] — `ON for 1s to 3s` and `ON for at least 3s` are adjacent; ESPHome always fires long, never extra-long at exactly 3s. Pre-existing in timing spec.
- **Single-click can fire during slow double-click** [`firmware/common/button.yaml`] — double-click inter-press window `OFF for 0.05s to 0.4s` overlaps single's `OFF for at least 0.3s`; a 0.3–0.4s gap is ambiguous. Tightening double to `OFF for 0.05s to 0.29s` would eliminate the dead zone. Pre-existing.
- **`send_data()` return value silently discarded** [`firmware/common/button.yaml`] — `canbus::Error` is ignored; TX failures on a busy bus (e.g., `ERROR_ALLTXBUSY`) lose events silently. Recommend an `ESP_LOGW` on non-OK result. Pre-existing behavior carried from `canbus.send:` action.
- **node_id ≥ 512 silently produces colliding CAN IDs** [`firmware/common/canbus_protocol.h`] — `can_id()` masks `node_id & 0x1FF` (max 511); node IDs 512+ wrap and collide. Currently safe because `generate_nodes.py` validates node IDs to 0–399. Pre-existing.

## Deferred from: code review of 2-1-base-node-configuration-spi-and-mcp2515-setup.md (2026-06-01)

- `can_int_pin` substitution is generated in node YAMLs but not consumed by `canbus.mcp2515` config in `firmware/common/base_node.yaml`; keep as deferred pre-existing cleanup until platform support or template strategy is revisited.
