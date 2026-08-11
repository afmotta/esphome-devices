#pragma once
#include "binding_actuation.h"
#include "esphome/core/log.h"
#include <cstdint>
#include <cstddef>
#include <cstring>
#include <string>

// =============================================================================
// remote_store.h — lighting fallback actuation over HTTP, ESPHome glue (ADR-0019)
// =============================================================================
// The remote counterpart to relay_store.h. When HA is down and a bound button
// targets an output id in the REMOTE range (>= REMOTE_ID_BASE, ADR-0013 §1's
// transport-agnostic id absorbing a remote realization), fire_binding_fallback()
// (relay_store.h) enqueues an (output_id, op) command here instead of driving a
// local Switch*. A NON-BLOCKING YAML drain loop (lighting/packages/
// remote_actuators.yaml) then pops the queue and issues the actual
// http_request.post — so the CAN on_frame handler and the 250ms ACK sweep, which
// call fire_binding_fallback, only ever enqueue and never block on the network.
//
// Not natively testable (ESP_LOGW + the ESPHome-flattened build), same split as
// relay_store.h. The pure classification/bounds it relies on
// (output_id_kind/binding_outputs_in_bounds) lives in binding_actuation.h and IS
// tested. The id->host realization is deployment config: object_id (the stable
// logical half) is the small table below; the target HOST is a YAML
// substitution in remote_actuators.yaml, not baked into this protocol header.
// =============================================================================

// Remote output id -> target light object_id (the ESPHome web_server REST path
// segment, i.e. the slug of the light's name). Indexed by (id - REMOTE_ID_BASE);
// keep the entry count == MAX_REMOTE_ACTUATORS (binding_actuation.h). Returns
// nullptr for a non-remote or unmapped id (callers guard on it).
inline const char *remote_object_id(uint8_t id)
{
  if (output_id_kind(id) != OUTPUT_REMOTE)
    return nullptr;
  static const char *const OBJECT_IDS[MAX_REMOTE_ACTUATORS] = {
      "tunable_white_1",  // id 32 -> an-penta-1 strip 1
      "tunable_white_2",  // id 33 -> an-penta-1 strip 2
  };
  return OBJECT_IDS[id - REMOTE_ID_BASE];
}

// op ("on"/"off"/"toggle") -> ESPHome web_server REST verb path segment. Null
// (unrecognized/null op — a stale/hand-edited bindings.h, the class of defect
// binding_outputs_in_bounds can't catch) means "don't issue a request".
inline const char *remote_op_path(const char *op)
{
  if (op == nullptr)
    return nullptr;
  if (strcmp(op, "on") == 0)
    return "turn_on";
  if (strcmp(op, "off") == 0)
    return "turn_off";
  if (strcmp(op, "toggle") == 0)
    return "toggle";
  return nullptr;
}

// A fixed-capacity FIFO of pending remote commands. Same header-accessor shape
// as pending_acks_store()/relay_store() — ESPHome globals can't hold a struct
// array. Single-producer (fire_binding_fallback, on the main loop) /
// single-consumer (the drain interval, also main loop), so no locking needed.
struct RemoteCmd { uint8_t output_id; const char *op; };

inline constexpr std::size_t REMOTE_QUEUE_CAP = 8;

struct RemoteCmdQueue {
  RemoteCmd buf[REMOTE_QUEUE_CAP];
  std::size_t head = 0;   // index of the next command to pop
  std::size_t count = 0;  // number of queued commands
};

inline RemoteCmdQueue &remote_cmd_queue()
{
  static RemoteCmdQueue q;
  return q;
}

inline bool remote_cmd_pending() { return remote_cmd_queue().count > 0; }

// Enqueue a remote command. Drops (loudly) if the queue is full rather than
// overwriting — a full queue means the target has been unreachable for many
// clicks, which is worth a log, and dropping the newest is the least-surprising
// loss. op points into bindings.h's static storage (compiled constant), so the
// stored pointer stays valid.
inline void remote_cmd_push(uint8_t output_id, const char *op)
{
  RemoteCmdQueue &q = remote_cmd_queue();
  if (q.count >= REMOTE_QUEUE_CAP) {
    ESP_LOGW("arb", "FALLBACK remote: queue full (cap=%u), dropping output_id=%u",
             (unsigned) REMOTE_QUEUE_CAP, (unsigned) output_id);
    return;
  }
  q.buf[(q.head + q.count) % REMOTE_QUEUE_CAP] = RemoteCmd{output_id, op};
  q.count++;
}

// Copy the front command without removing it (the drain loop peeks to build the
// URL, then pops unconditionally so a bad entry can't wedge the queue).
inline bool remote_cmd_peek(RemoteCmd *out)
{
  RemoteCmdQueue &q = remote_cmd_queue();
  if (q.count == 0)
    return false;
  *out = q.buf[q.head];
  return true;
}

inline void remote_cmd_pop()
{
  RemoteCmdQueue &q = remote_cmd_queue();
  if (q.count == 0)
    return;
  q.head = (q.head + 1) % REMOTE_QUEUE_CAP;
  q.count--;
}

// Build the full REST URL for the front command against `host` (the gateway
// config's target address — a static/reserved IP, passed in from the YAML
// substitution). Returns "" when the queue is empty or the id/op is unmapped;
// the drain loop skips the POST on "" and still pops.
//   http://<host>/light/<object_id>/<verb>
inline std::string remote_cmd_front_url(const char *host)
{
  RemoteCmd c{};
  if (!remote_cmd_peek(&c))
    return std::string();
  const char *obj = remote_object_id(c.output_id);
  const char *verb = remote_op_path(c.op);
  if (obj == nullptr || verb == nullptr)
    return std::string();
  std::string url = "http://";
  url += host;
  url += "/light/";
  url += obj;
  url += "/";
  url += verb;
  return url;
}
