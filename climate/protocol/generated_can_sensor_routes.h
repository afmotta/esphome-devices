#pragma once
#include <cstddef>
#include <cstdint>
#include "canbus_protocol.h"

// =============================================================================
// generated_can_sensor_routes.h — GENERATED from registry/nodes.csv by
// canbus/tools/generate_nodes.py. DO NOT EDIT.
// Climate CAN sensor route metadata for receiver freshness tracking.
// =============================================================================

struct HvacCanSensorRoute { uint16_t node_id; uint16_t measurement_type; };

inline constexpr HvacCanSensorRoute HVAC_CAN_SENSOR_ROUTES[] = {
    {101, SENSOR_SHT45_TEMP},
    {101, SENSOR_SHT45_RH},
    {101, SENSOR_SEN66_TEMP},
    {101, SENSOR_SEN66_RH},
    {101, SENSOR_SEN66_PM1_0},
    {101, SENSOR_SEN66_PM2_5},
    {101, SENSOR_SEN66_PM4_0},
    {101, SENSOR_SEN66_PM10},
    {101, SENSOR_SEN66_VOC_INDEX},
    {101, SENSOR_SEN66_NOX_INDEX},
    {101, SENSOR_SEN66_CO2},
};
inline constexpr std::size_t HVAC_CAN_SENSOR_ROUTES_SIZE = sizeof(HVAC_CAN_SENSOR_ROUTES) / sizeof(HVAC_CAN_SENSOR_ROUTES[0]);
