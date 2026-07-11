#pragma once
#include <cstddef>
#include <cstdint>
#include <limits>
#include <vector>

#include "canbus_protocol.h"
#include "generated_can_sensor_routes.h"

// =============================================================================
// can_sensor_receiver.h — HVAC CAT_SENSOR decode, routing, and freshness logic
// =============================================================================
// Pure helper code for the climate controller's receive-only CAN sensor path.
// ESPHome YAML owns publishing through generated scripts; this header owns the
// protocol validation and per-route last-OK state so it is native-testable.
// =============================================================================

inline constexpr uint32_t HVAC_CAN_SENSOR_STALE_TIMEOUT_MS = 90000;

struct CanSensorFrame
{
  uint16_t node_id;
  uint16_t measurement_type;
  uint8_t status;
  int32_t raw_value;
};

struct CanSensorRouteState
{
  uint16_t node_id;
  uint16_t measurement_type;
  uint32_t last_ok_ms;
  bool seen_ok;
  bool stale;
};

struct CanSensorStaleRoute
{
  uint16_t node_id;
  uint16_t measurement_type;
};

struct CanSensorHandleResult
{
  bool decoded;
  bool routed;
  bool publish_value;
  bool publish_nan;
  bool refreshed;
  uint16_t node_id;
  uint16_t measurement_type;
  float value;
};

inline bool can_sensor_is_sensor_frame(uint32_t frame_id)
{
  return can_id_category(frame_id) == CAT_SENSOR;
}

inline bool can_sensor_decode_frame(uint32_t frame_id, const std::vector<uint8_t> &payload,
                                    CanSensorFrame *frame)
{
  if (!can_sensor_is_sensor_frame(frame_id) || payload.size() < SENSOR_PAYLOAD_MIN)
    return false;
  if (payload_version(payload) != PROTO_V1)
    return false;
  if (frame != nullptr)
  {
    frame->node_id = can_id_node(frame_id);
    frame->measurement_type = payload_measurement_type(payload);
    frame->status = payload_sensor_status(payload);
    frame->raw_value = payload_sensor_value32(payload);
  }
  return true;
}

inline bool can_sensor_route_matches(const HvacCanSensorRoute &route, uint16_t node_id,
                                     uint16_t measurement_type)
{
  return route.node_id == node_id && route.measurement_type == measurement_type;
}

inline int can_sensor_route_index(uint16_t node_id, uint16_t measurement_type)
{
  for (std::size_t i = 0; i < HVAC_CAN_SENSOR_ROUTES_SIZE; i++)
  {
    if (can_sensor_route_matches(HVAC_CAN_SENSOR_ROUTES[i], node_id, measurement_type))
      return (int)i;
  }
  return -1;
}

inline bool can_sensor_route_known(uint16_t node_id, uint16_t measurement_type)
{
  return can_sensor_route_index(node_id, measurement_type) >= 0;
}

inline float can_sensor_nan()
{
  return std::numeric_limits<float>::quiet_NaN();
}

inline float can_sensor_scale_value(uint16_t measurement_type, int32_t raw_value)
{
  switch (measurement_type)
  {
  case SENSOR_SHT45_TEMP:
  case SENSOR_SEN66_TEMP:
  case SENSOR_SHT45_RH:
  case SENSOR_SEN66_RH:
    return (float)raw_value / 100.0f;
  case SENSOR_SEN66_PM1_0:
  case SENSOR_SEN66_PM2_5:
  case SENSOR_SEN66_PM4_0:
  case SENSOR_SEN66_PM10:
    return (float)raw_value / 10.0f;
  case SENSOR_SEN66_VOC_INDEX:
  case SENSOR_SEN66_NOX_INDEX:
  case SENSOR_SEN66_CO2:
    return (float)raw_value;
  default:
    return can_sensor_nan();
  }
}

inline bool can_sensor_measurement_supported(uint16_t measurement_type)
{
  switch (measurement_type)
  {
  case SENSOR_SHT45_TEMP:
  case SENSOR_SHT45_RH:
  case SENSOR_SEN66_TEMP:
  case SENSOR_SEN66_RH:
  case SENSOR_SEN66_PM1_0:
  case SENSOR_SEN66_PM2_5:
  case SENSOR_SEN66_PM4_0:
  case SENSOR_SEN66_PM10:
  case SENSOR_SEN66_VOC_INDEX:
  case SENSOR_SEN66_NOX_INDEX:
  case SENSOR_SEN66_CO2:
    return true;
  default:
    return false;
  }
}

inline CanSensorRouteState *can_sensor_route_state_store()
{
  static CanSensorRouteState store[HVAC_CAN_SENSOR_ROUTES_SIZE ? HVAC_CAN_SENSOR_ROUTES_SIZE : 1] = {};
  static bool initialized = false;
  if (!initialized)
  {
    for (std::size_t i = 0; i < HVAC_CAN_SENSOR_ROUTES_SIZE; i++)
    {
      store[i].node_id = HVAC_CAN_SENSOR_ROUTES[i].node_id;
      store[i].measurement_type = HVAC_CAN_SENSOR_ROUTES[i].measurement_type;
    }
    initialized = true;
  }
  return store;
}

inline void can_sensor_reset_route_state(CanSensorRouteState *state, std::size_t route_count)
{
  for (std::size_t i = 0; i < route_count; i++)
  {
    state[i].node_id = HVAC_CAN_SENSOR_ROUTES[i].node_id;
    state[i].measurement_type = HVAC_CAN_SENSOR_ROUTES[i].measurement_type;
    state[i].last_ok_ms = 0;
    state[i].seen_ok = false;
    state[i].stale = false;
  }
}

inline bool can_sensor_refresh_route(CanSensorRouteState *state, std::size_t route_count,
                                     uint16_t node_id, uint16_t measurement_type,
                                     uint32_t now_ms)
{
  for (std::size_t i = 0; i < route_count; i++)
  {
    if (state[i].node_id == node_id && state[i].measurement_type == measurement_type)
    {
      state[i].last_ok_ms = now_ms;
      state[i].seen_ok = true;
      state[i].stale = false;
      return true;
    }
  }
  return false;
}

inline bool can_sensor_refresh_route(uint16_t node_id, uint16_t measurement_type, uint32_t now_ms)
{
  return can_sensor_refresh_route(can_sensor_route_state_store(), HVAC_CAN_SENSOR_ROUTES_SIZE,
                                  node_id, measurement_type, now_ms);
}

inline bool can_sensor_state_has_route(const CanSensorRouteState *state, std::size_t route_count,
                                       uint16_t node_id, uint16_t measurement_type)
{
  for (std::size_t i = 0; i < route_count; i++)
  {
    if (state[i].node_id == node_id && state[i].measurement_type == measurement_type)
      return true;
  }
  return false;
}

inline CanSensorHandleResult can_sensor_handle_frame(
    CanSensorRouteState *state, std::size_t route_count, uint32_t frame_id,
    const std::vector<uint8_t> &payload, uint32_t now_ms)
{
  CanSensorHandleResult result{};
  result.value = can_sensor_nan();
  CanSensorFrame frame{};
  if (!can_sensor_decode_frame(frame_id, payload, &frame))
    return result;

  result.decoded = true;
  result.node_id = frame.node_id;
  result.measurement_type = frame.measurement_type;
  if (!can_sensor_measurement_supported(frame.measurement_type))
    return result;

  result.routed = can_sensor_state_has_route(state, route_count, frame.node_id,
                                             frame.measurement_type);
  if (!result.routed)
    return result;

  if (frame.status == SENSOR_STATUS_OK)
  {
    result.refreshed = can_sensor_refresh_route(state, route_count, frame.node_id,
                                                frame.measurement_type, now_ms);
    result.publish_value = result.refreshed;
    result.value = can_sensor_scale_value(frame.measurement_type, frame.raw_value);
  }
  else
  {
    result.publish_nan = true;
  }
  return result;
}

inline CanSensorHandleResult can_sensor_handle_frame(uint32_t frame_id,
                                                     const std::vector<uint8_t> &payload,
                                                     uint32_t now_ms)
{
  return can_sensor_handle_frame(can_sensor_route_state_store(), HVAC_CAN_SENSOR_ROUTES_SIZE,
                                 frame_id, payload, now_ms);
}

inline bool can_sensor_route_is_stale(const CanSensorRouteState &state, uint32_t now_ms,
                                      uint32_t stale_timeout_ms = HVAC_CAN_SENSOR_STALE_TIMEOUT_MS)
{
  if (state.stale)
    return false;
  if (!state.seen_ok)
    return now_ms >= stale_timeout_ms;
  return (uint32_t)(now_ms - state.last_ok_ms) >= stale_timeout_ms;
}

inline std::vector<CanSensorStaleRoute> can_sensor_take_stale_routes(
    CanSensorRouteState *state, std::size_t route_count, uint32_t now_ms,
    uint32_t stale_timeout_ms = HVAC_CAN_SENSOR_STALE_TIMEOUT_MS)
{
  std::vector<CanSensorStaleRoute> stale_routes;
  for (std::size_t i = 0; i < route_count; i++)
  {
    if (can_sensor_route_is_stale(state[i], now_ms, stale_timeout_ms))
    {
      state[i].stale = true;
      stale_routes.push_back({state[i].node_id, state[i].measurement_type});
    }
  }
  return stale_routes;
}

inline std::vector<CanSensorStaleRoute> can_sensor_take_stale_routes(
    uint32_t now_ms, uint32_t stale_timeout_ms = HVAC_CAN_SENSOR_STALE_TIMEOUT_MS)
{
  return can_sensor_take_stale_routes(can_sensor_route_state_store(), HVAC_CAN_SENSOR_ROUTES_SIZE,
                                      now_ms, stale_timeout_ms);
}
