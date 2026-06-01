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
