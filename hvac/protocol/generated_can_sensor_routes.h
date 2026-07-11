#pragma once
#include <cstddef>
#include <cstdint>
#include "canbus_protocol.h"

// =============================================================================
// generated_can_sensor_routes.h — GENERATED from registry/nodes.csv by
// canbus/tools/generate_nodes.py. DO NOT EDIT.
// HVAC CAN sensor route metadata for receiver freshness tracking.
// =============================================================================

struct HvacCanSensorRoute
{
  uint16_t node_id;
  uint16_t measurement_type;
};

inline constexpr const HvacCanSensorRoute *HVAC_CAN_SENSOR_ROUTES = nullptr;
inline constexpr std::size_t HVAC_CAN_SENSOR_ROUTES_SIZE = 0;
