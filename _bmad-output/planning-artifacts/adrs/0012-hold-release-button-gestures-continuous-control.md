---
adr: 0012
title: 'Hold/release button gestures for continuous control (dimming, covers): single gesture vocabulary, central long-press derivation, bounded actuation'
status: 'Accepted'
date: '2026-06-12'
acceptedDate: '2026-06-12'
deciders: ['Alberto']
author: 'Winston (System Architect)'
dependsOn:
  - 'ADR-0003: Centralized single-controller with on-board fallback (node-side semantic events; ha_ready/ACK arbitration)'
  - 'ADR-0005: Segmented topology (forward-all bridges stay untouched by new event types)'
  - 'ADR-0007: Flat node_id with central meaning map (gestures on the node, meaning central)'
  - 'ADR-0008: Post-LIVE evolution doctrine (node firmware changes are physical campaigns after LIVE — this lands before)'
relatedDocuments:
  - _bmad-output/planning-artifacts/adrs/0003-centralized-single-controller-with-onboard-fallback.md
  - _bmad-output/planning-artifacts/adrs/0007-flat-node-id-with-central-meaning-map.md
  - _bmad-output/planning-artifacts/adrs/0008-post-live-firmware-evolution-no-can-bootloader.md
  - _bmad-output/implementation-artifacts/4-2-button-event-acceptance-matrix-node-100.md
  - docs/live-freeze-checklist.md
  - firmware/protocol/canbus_protocol.h
  - firmware/packages/button.yaml
  - firmware/gateway/gateway.yaml
  - firmware/gateway/ha_hold_automations.yaml
---

# ADR-0012: Hold/release button gestures, single vocabulary

## Status

**Accepted (2026-06-12).** Replaces the release-time long/extra-long press events with a
press-phase gesture pair — `hold` (fires *while the button is still down*) and
`hold_release` (fires when it comes back up) — emitted by **every** button, so a wall
button can drive continuous actions in Home Assistant: hold-to-dim a light, hold-to-move
a window cover, release to stop. A "long press" stops being a wire event and becomes a
central derivation (hold followed by hold_release).

*Revision note:* the initially-accepted form of this ADR (same day, never committed) kept
long/extra-long press alive via a per-button dual-mode scheme — a second button package, a
`hold_buttons` registry column, and a generator seam. Alberto withdrew the constraint that
motivated it ("don't remove gestures from existing buttons"), accepting the long/extra-long
fold to gain a simpler setup; the dual-mode design is recorded under Alternatives.

ADR-0008 is the clock on this decision: after LIVE, changing the gesture vocabulary of
fielded buttons is a physical reflash campaign. Today it is a lock-step recompile of a
two-node bench fleet. The decision should be made — and soaked — before the first board
goes into a wall.

## Context

1. **Every pre-existing event fired at or after release.** The original five-event
   vocabulary (single/double/triple click, long press, extra-long press) was built on
   `on_multi_click` patterns that all end in an `OFF` entry — even `long_press` only fired
   once the finger lifted (plus a 300 ms OFF-confirmation). Complete for discrete actions,
   but unable to express *continuous* ones: "dim while I hold this", "move the cover until
   I let go".

2. **The press-phase trigger already exists in the stack.** ESPHome's `on_multi_click`
   does **not** wait for a falling edge when the final timing entry is `ON for at least X`
   (verified against the ESPHome binary_sensor docs: "an `ON for at least` timing without
   an `OFF` does not await a falling edge"). A `hold` event that fires mid-press is the
   same mechanism `button.yaml` already used — new timing entries, not a new component.

3. **Hold and long-press patterns structurally collide.** A button cannot carry both: any
   hold also satisfies the long/extra-long timings and would fire duplicates. So the real
   choice was never "add hold"; it was *which side of the collision to keep* — and whether
   keeping both vocabularies on different buttons (dual mode) was worth its machinery.

4. **"Long press" is reconstructible centrally — including its timing.** Hold followed by
   hold_release *is* a long press. The old long vs extra-long (3 s) distinction is also
   recoverable in HA by measuring the hold→release gap — coarse enough (seconds) that
   CAN→gateway→HA jitter (tens of ms) is irrelevant. Verified consumers: nothing in the
   repo binds `long_press`/`extra_long_press` — the gateway forwards event strings
   without caring which, and no HA automation references them.

5. **Two consumers are waiting on the pair.** Dimmable lights and window covers — both
   start/stop interactions over an analog quantity. KNX solved the identical problem with
   its 4-bit relative-dimming object (press = start ramp, release = stop, ramp bounded in
   the actuator); Zigbee buttons (IKEA, Hue) emit exactly this press/hold/release
   primitive vocabulary and leave "long press" to the controller.

## Decision

Five parts. The stance in one line: **every button speaks one gesture vocabulary; the node
names the gesture, HA gives it meaning — including "long press", which is now a derived
meaning, not a wire event — and every continuous action must be bounded so a lost release
can never run away.**

### 1. One vocabulary, on every button: clicks + the hold pair

`packages/button.yaml` (the single per-button package) emits five event types:

- `click` / `double_click` / `triple_click` — release-time, node-detected, unchanged.
- `EVT_HOLD = 0x06` (`"hold"`) — fires **while the button is still pressed**, once the
  press has lasted `hold_ms` (default 800 ms; a fleet-wide substitution, open item 1).
  Pattern: `ON for at least ${hold_ms}` as the final timing entry.
- `EVT_HOLD_RELEASE = 0x07` (`"hold_release"`) — fires when a hold ends. Pattern:
  `ON for at least ${hold_ms}`, then `OFF for at least 0.05s`. It can only follow a hold;
  a bare click can never emit it.

Clicks coexist with the pair because they are timing-disjoint (ON ≤ 0.5 s vs ≥ 800 ms; the
0.5–0.8 s dead zone is deliberate gesture separation). `"hold_release"`, not bare
`"release"`, so the HA event can never be misread as a generic button-up. Payload layout,
`button_payload()`, and `CAT_INPUT` framing are unchanged. Bus cost: two frames per hold
gesture — noise at 125 kbps.

Raw `down`/`up` edge events remain explicitly rejected (Alternatives): they triple the
traffic of every ordinary click, move *click* timing onto a jittery network path, and make
a lost `up` an unbounded failure.

### 2. Long/extra-long press are removed from the protocol and derived centrally

- `EVT_LONG_PRESS` / `EVT_EXTRA_LONG_PRESS` are **removed outright** from
  `canbus_protocol.h` (constants, decoder strings, and the dead pre-PRD alias block) —
  pre-LIVE there is no fielded firmware to stay compatible with, and the versioning
  policy absorbs breaking changes in place. Wire values 0x04/0x05 stay **unassigned**
  (hold is 0x06/0x07, not renumbered): during the reflash window a not-yet-reflashed
  node's `long_press` frame decodes as `"unknown"` — logged and dropped — instead of
  misdecoding as a hold event.
- **A long press is `hold` followed by `hold_release`,** reconstructed in HA (reference
  automation in `ha_hold_automations.yaml`). By default the old long vs extra-long
  distinction is **folded into this one gesture**.
- If a binding ever needs the 3 s split back, it is an HA automation choice, not a
  firmware change: trigger on `hold`, `wait_for_trigger` the release with a timeout of
  (3 s − `hold_ms`); release before the timeout = long press, after = extra-long. The
  extra-long branch may even fire *at* the threshold while still held — something
  node-side detection never could.
- Latency improves: the old node-side `long_press` fired 300 ms after release (its
  OFF-confirmation window); the derived gesture fires at `hold_release`, 50 ms after
  release plus transport.

This completes the ADR-0007 trajectory: the last piece of *timing meaning* (the 1 s / 3 s
thresholds) leaves node firmware and becomes a centrally re-mappable interpretation. The
node's vocabulary is now purely structural: how many taps, and is it still held.

### 3. No per-button configuration

Because every button speaks the same vocabulary, nothing about buttons is configurable per
node or per button: no registry column, no package variant, no generator involvement. The
eight button includes stay in `base_node.yaml`; generated node files keep their minimal
identity-only form; `generate_nodes.py`, `allocate_node.py`, and `commission.py` are
untouched by this ADR. Which button dims, opens a cover, or long-presses a scene is —
as always — a binding in HA (ADR-0007), assignable and re-assignable without reflashing.

### 4. The change is additive end-to-end; only nodes need reflashing

- **Protocol:** two new event values, no payload or framing change, no `PROTO_V1` bump
  (pre-LIVE absorption; the removed 0x04/0x05 decode as `"unknown"` during the reflash
  window — graceful, see §2).
- **Gateway:** zero logic change — it forwards any event whose `event_type_str` is not
  `"unknown"`, through the existing ha_ready / pending-ACK arbitration; `hold` and
  `hold_release` each get an `event_id` and an ACK like any click. Recompile + WiFi OTA.
- **Bridges:** untouched — forward-all (ADR-0005) is version-agnostic by design.
- **Nodes:** lock-step reflash (pre-LIVE policy; the fleet is two bench boards).

### 5. The runaway rule: every continuous action in HA must be bounded

The one genuinely new failure mode is a lost `hold_release`. The KNX answer is adopted as
a **review-time rule for every consumer of `hold`**:

- The action started by `hold` must reach a bound on its own: a dim loop with a maximum
  iteration count (`repeat` + `brightness_step_pct` capped at full range), or a single
  transition-to-bound command. Covers get this free — end stops are physical bounds;
  `hold_release` → `cover.stop` merely stops early.
- **Derived long presses satisfy the rule by construction:** the action fires *on*
  `hold_release`, so a lost release means the action simply does not fire — benign no-op,
  press again. (Corollary: if a binding uses the timing-discrimination variant, a lost
  release lands in the extra-long branch; the default fold has no such misclassification.)
- Unbounded patterns (`while true` dim loops) are rejected at review, same enforcement
  model as ADR-0008's "controller-absorbed first".
- When bindings become real, the gateway's local fallback (ADR-0003) needs the same
  hold→release derivation to act on long presses while HA is down. The derivation rule
  should be *generated* into both HA and the fallback from the binding manifest
  (ADR-0009) — one source, two emitters (open item 2).

Direction handling (dim up vs down, open vs close) is an HA-side concern, not protocol:
the recommended pattern is **two buttons** (up/down — boards have eight), with
single-button direction-alternation allowed where buttons are scarce (open item 3).

## Implementation plan

1. **Protocol header** — add `EVT_HOLD` / `EVT_HOLD_RELEASE` + `event_type_str` cases to
   `firmware/protocol/canbus_protocol.h`; remove `EVT_LONG_PRESS`/`EVT_EXTRA_LONG_PRESS`
   (and the dead pre-PRD alias block), leaving 0x04/0x05 unassigned; extend
   `firmware/tests/test_protocol.cpp` (round-trip, string mapping, 0x04/0x05 decode as
   `"unknown"`).
2. **`packages/button.yaml`** — replace the long/extra-long patterns with the two hold
   patterns from Decision §1; `hold_ms` as a substitution defaulting to 800 ms. No other
   file in the node build changes; `base_node.yaml` keeps its eight includes.
3. **HA reference automations** — `gateway/ha_hold_automations.yaml` (same copy-into-HA
   model as the arbitration automations): bounded dim up/down pair, cover
   open/close/stop trio, and the derived long press. Seeds for the binding-manifest
   generator (ADR-0009; open item 2).
4. **Gateway** — recompile and OTA; no YAML change. Verify `hold`/`hold_release` flow
   through forward + ACK like clicks.
5. **Bench acceptance matrix** — extend the 4-2/4-3 matrix pattern: `hold` fires *while
   held* at ~`hold_ms` (not at release); `hold_release` fires on release of a hold and
   never after a bare click; single/double/triple unchanged; **no long/extra-long frames
   on the bus**; derived long press fires in HA on hold → release. Plus the §5 pull-test:
   kill the HA dim automation mid-hold and confirm the light lands at its bound.
6. **Reflash** — lock-step reflash of the bench nodes (pre-LIVE policy).

## Consequences

### Positive

- **Continuous control becomes a first-class gesture** — hold-to-dim and hold-to-move
  with stock wall buttons, the interaction KNX/Hue users expect.
- **One vocabulary, zero configuration** — no per-button modes, no registry column, no
  second package, no generator seam; every button is interchangeable and every gesture's
  meaning lives in HA. The simplest possible firmware surface ships into the walls.
- **"Long press" becomes centrally re-definable** — its threshold, its existence, and
  even the long/extra-long split are HA decisions now, changeable per binding without a
  reflash campaign. The last timing semantics leave node firmware (ADR-0007 completed).
- **Derived long press is faster** than the node-side event it replaces (release + 50 ms
  vs release + 300 ms) and fail-benign (lost release = no-op).
- **Additive everywhere that is hard to change** — no payload change, no version bump, no
  gateway logic, no bridge involvement; the ACK arbitration covers the new events with
  zero new machinery.

### Negative / costs

- **Long and extra-long press leave the protocol entirely.** Folded into one derived
  gesture by default; the distinction survives only as an opt-in HA timing measurement.
  Accepted explicitly by Alberto as the price of the simpler setup — including removing
  the constants/decoder rather than keeping them for mixed-fleet decode, since pre-LIVE
  there is no fleet to be mixed with (the unassigned-value gap covers the bench reflash
  window).
- **Two frames instead of one** per long-ish press (hold + release). Negligible at
  125 kbps.
- **A lost `hold_release` silently drops a derived long-press action** (vs. node-side
  detection, where the gesture completed locally). Benign and self-evident, but a real
  behavior change; the bench matrix's pull-test exercises it.
- **The derivation rule will eventually live in two places** — HA and the gateway
  fallback (ADR-0003) — which is why it must be manifest-generated, not hand-copied
  (open item 2).
- **One fleet-wide `hold_ms` serves two meanings** — dim-start feel and long-press
  threshold are coupled to a single knob (deliberate: one number to tune, no per-button
  drift).
- **The §5 bound is discipline, not tooling** — an unbounded HA automation is caught by
  review (or by the future binding generator), not by the compiler.

## Alternatives considered

- **Per-button dual mode — the initially-accepted form of this ADR.** Keep the old
  five-event package alongside a hold-mode variant, selected per button via a
  `hold_buttons` registry column; the generator emits per-button includes (a seam that
  required moving button includes out of `base_node.yaml` and touching
  `allocate_node.py`/`commission.py`). Fully implemented and verified, then withdrawn the
  same day: the machinery existed solely to preserve long/extra-long on non-dimmer
  buttons — a constraint Alberto explicitly declared not worth its complexity. Demoted
  here with its implementation reverted; the central derivation (§2) recovers the lost
  gestures anyway, making dual mode strictly worse: same capability, more moving parts.
- **Raw `down`/`up` edge events, all gesture detection in HA.** Rejected: every ordinary
  click becomes three frames / three HA events / three ACK round-trips, polluting the
  ADR-0003 RTT tuning data; *click* timing moves onto a network path with jitter the
  node's GPIO loop doesn't have; the gateway fallback can act on "hold" but not on a
  context-free edge; a lost `up` is an unbounded failure. The single-vocabulary design
  takes the one good idea (centralize interpretation) only for the gesture where timing
  is coarse enough to survive transport — the long press.
- **Dead-man hold ticks** (node repeats a `hold_tick` frame while pressed; action
  continues only while ticks arrive). Most loss-robust, but chatty (5 Hz per held button
  through the ACK store) and unnecessary once §5 bounds the action. Documented
  escalation if bench/field experience ever shows lost releases mattering; would be
  another additive event value.
- **Zero-firmware stopgap: bind `long_press` as a ±20 % step.** Worked before this ADR,
  rejected as the answer: fires at release, no continuous feel. Moot once long_press
  leaves the wire.
- **Defer until after LIVE.** Rejected — the ADR-0008 trap in miniature: a bench
  recompile today vs. a multi-day physical campaign after the fleet is fielded, for a
  gesture pair two named consumers (dimmers, covers) already want.

## Open items

1. **`hold_ms` tuning** — 800 ms default is a guess between "clearly not a click"
   (> 0.5 s + margin) and "doesn't feel laggy"; it now also sets the derived long-press
   threshold (the old node-side value was 1 s — tune for feel, not for parity). Tune on
   bench hardware during implementation-plan §5 and record the value in the acceptance
   matrix and the LIVE-freeze checklist.
2. **Binding-manifest interplay (ADR-0009)** — hold/hold_release bindings, the §5
   count-bound, and the long-press derivation rule should be generated from the manifest
   into *both* HA and the gateway fallback (ADR-0003), not hand-written; the slice-3
   reference automations are the template. Tracked in `deferred-work.md`.
3. **Single-button direction-alternation UX** — whether the alternate-direction pattern
   (one button toggling dim-up/dim-down per gesture) is offered in the reference
   automations or two-button is mandated initially. HA-side, reversible, low stakes.
4. **LIVE-gate interplay** — *resolved at acceptance:* the hold-gesture soak (continuous
   action + derived long press + the §5 lost-release pull-test) is a checkbox in
   `docs/live-freeze-checklist.md` — the checklist exists precisely so the frozen surface
   is the soaked surface.

## Notes

The press-phase trigger semantics (final `ON for at least` fires without awaiting a
falling edge) were verified against the ESPHome binary_sensor documentation before this
ADR was drafted — it is the load-bearing fact of Decision §1, and it means no new ESPHome
component or custom code is involved. The failure-mode stance in §5 is borrowed from KNX
relative dimming (start/stop with bounded ramp, shipped in walls for thirty years); the
vocabulary itself — press-phase primitives on the device, "long press" as a controller
interpretation — is the Zigbee button model. ADR-0004 established KNX as this project's
design yardstick; this is that yardstick applied to gestures.
