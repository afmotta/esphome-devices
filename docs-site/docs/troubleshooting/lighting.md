# Lighting — Diagnose & Fix: Common Problems

The lighting system turns wall-button presses into light actions. Button
presses arrive over the CAN bus (shared infrastructure — see
[CAN Bus troubleshooting](canbus.md) for wiring/node problems) and are
decoded by the **lighting controller**, which either hands the press to Home
Assistant (for rich behavior like dimming and scenes) or, if Home Assistant
can't be reached, acts on it directly using its own relay bank over RS485
(see [RS485 / Modbus](rs485-modbus.md) for that bus). This page covers
problems specific to that decision-making and to the button→light mapping
itself.

!!! warning "This page is new"
    Unlike the other troubleshooting pages, there is no existing
    troubleshooting documentation anywhere in the project for the lighting
    system to draw on — the lighting system is real but not yet physically
    installed, and no field failures have happened yet. Everything below is
    reasoned from the system's design documents, not from experience fixing
    a real fault. Treat it accordingly. 🔵 DESIGNED throughout unless marked
    otherwise.

!!! note "How to read the confidence tags on this page"
    🟢 VERIFIED = confirmed on a bench or in the field. 🔵 DESIGNED = built
    and intended to work this way, not yet proven against a real fault.
    ⚠️ KNOWN GAP = genuinely unresolved.

---

## A relay doesn't respond to a Home Assistant command or a button press

**Symptom:** Toggling a light from Home Assistant does nothing, or pressing
its wall button does nothing (or does the wrong thing).

**Diagnostic steps, in order (each rules out one layer before moving to the
next):**

1. **Check that the controller and Home Assistant agree on what the button
   does.** The lighting controller and Home Assistant both work from the
   same "binding manifest" — the file that maps each button to a relay
   action — and each side carries a hash (a fingerprint) of that manifest.
   If the manifest was edited and pushed to one side but the controller
   wasn't reflashed with the update (or vice versa), the two sides disagree
   about what should happen, and the mismatch also affects the readiness
   gate described in the next section. See
   [Everyday Monitoring](../monitoring.md) for where to check this.
2. **Check the shared RS485 relay bus.** The lighting controller drives its
   relay bank over its own RS485/Modbus bus — the same kind of bus the
   climate system uses (a separate, independent bus, not the same wire, but
   wired and diagnosed the same way). See
   [RS485 / Modbus](rs485-modbus.md) for the full diagnostic flow (no
   communication / intermittent / some devices not responding / high error
   rate).
3. **Check the relay board itself.** If the bus checks out (the controller
   can reach other channels on the same board) but one specific relay
   channel never responds, the board or that channel may have failed.

**Fix:** Depends on which layer above turned out to be the problem —
regenerate/push the binding manifest and reflash if it's a mismatch, follow
the RS485 fixes if it's a bus problem, or replace the board if a specific
channel has failed.

**When to escalate:** Once the bus itself is confirmed healthy and the
manifest hashes agree, but a specific relay channel still won't respond, go
to [Relay board replacement](../hardware/relay-board.md).

---

## The system falls back to basic on/off control on every button press, even when Home Assistant looks fine

**Symptom:** Lights only ever turn fully on or off — no dimming, no scenes —
even though Home Assistant appears to be running normally. A diagnostic
`ha_ready` entity, if visible, reads `false`.

**Background:** This is the same arbitration mechanism used elsewhere in the
house (shared with the CAN bus health-monitoring design): the lighting
controller only hands a button press to Home Assistant when it's confident
Home Assistant is genuinely ready — API connected, a recent readiness signal
received, and the two sides' binding-manifest hashes matching. If any one of
those isn't true, the controller falls back to acting on the press itself,
using only the simple "toggle relay N" logic it has built in — this is
intentional, so lights keep working at all when Home Assistant can't be
reached, but it means "rich" behavior is temporarily unavailable. See
[CAN Bus troubleshooting](canbus.md#ha_ready-reads-false-or-the-system-falls-back-to-local-relay-control-when-it-shouldnt)
for the full explanation of this mechanism, which applies identically here.

**Likely causes:** Same as the CAN bus page's `ha_ready` section — almost
always Home Assistant itself, network connectivity, or a stale binding
manifest, and almost never the button node that happens to be pressed.

**Diagnostic steps:**

1. Confirm Home Assistant is actually reachable and running.
2. Check the lighting controller's own network connectivity — see
   [Network / Home Assistant](network.md).
3. Check for a binding-manifest mismatch (edited but not pushed/reflashed on
   both sides).

**Fix:** Restore whichever upstream condition is failing; the readiness gate
recovers on its own once the underlying cause is fixed — no manual reset is
required.

**When to escalate:** This is a connectivity/configuration issue, not a
hardware fault — it's essentially never a reason to replace CAN or relay
hardware. If Home Assistant, networking, and the manifest hash all check out
and the fallback still won't clear, treat it as a software investigation.

---

## A button press doesn't produce the light action you expect

**Symptom:** The button clearly registers (the node isn't the problem — see
[CAN Bus troubleshooting](canbus.md) if you're not sure), but nothing
happens, or the wrong light/relay responds.

**Background:** What a specific button does — which relay(s) it controls,
and what action (on/off/toggle) — is defined by an explicit binding entry
for that exact `(node, button)` pair. **Only single clicks have a defined
fallback action** when Home Assistant is unreachable; double-click,
triple-click, and hold/hold-release gestures are Home Assistant-only by
design, so if Home Assistant is down, those gestures simply do nothing —
that's expected, not a bug. A button with no binding entry at all also does
nothing, by design (it's not an error state, just "not configured yet").

**Diagnostic steps:**

1. Confirm which gesture you're testing. If it's anything other than a
   single click, and the system is currently in local-fallback mode (see the
   previous section), that gesture is expected to do nothing right now —
   check `ha_ready` first.
2. Check whether that exact button has a binding entry at all, and whether
   it maps to the relay/action you expect. The binding manifest is the
   source of truth for this mapping.
3. Check whether a recently-added or recently-changed binding has actually
   been generated and pushed to both Home Assistant and the controller, and
   whether the controller has been reflashed since — an edited-but-not-yet-
   deployed binding looks identical to "nothing happened" from the button
   side. See [Routine Maintenance](../maintenance-tasks.md) for the
   push/regenerate/reflash sequence.

**Fix:** Add or correct the binding entry for that button, then run the
generation step and push/reflash both sides so the controller and Home
Assistant agree again.

**When to escalate:** If the binding is confirmed correct and deployed on
both sides, and the button still doesn't do the right thing, treat it as a
relay/wiring problem — see [RS485 / Modbus](rs485-modbus.md) or
[Relay board replacement](../hardware/relay-board.md).
