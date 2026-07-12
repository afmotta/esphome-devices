#include <cassert>
#include <cmath>
#include <cstdint>
#include <vector>

#include "canbus_protocol.h"
#include "can_sensor_receiver.h"

namespace
{

  constexpr HvacCanSensorRoute TEST_ROUTES[] = {
      {100, SENSOR_SHT45_TEMP},
      {100, SENSOR_SHT45_RH},
      {100, SENSOR_SEN66_TEMP},
      {100, SENSOR_SEN66_RH},
      {100, SENSOR_SEN66_PM1_0},
      {100, SENSOR_SEN66_PM2_5},
      {100, SENSOR_SEN66_PM4_0},
      {100, SENSOR_SEN66_PM10},
      {100, SENSOR_SEN66_VOC_INDEX},
      {100, SENSOR_SEN66_NOX_INDEX},
      {100, SENSOR_SEN66_CO2},
  };

  constexpr std::size_t TEST_ROUTE_COUNT = sizeof(TEST_ROUTES) / sizeof(TEST_ROUTES[0]);

  void assert_close(float actual, float expected)
  {
    assert(std::fabs(actual - expected) < 0.001f);
  }

  void reset_state(CanSensorRouteState *state)
  {
    for (std::size_t i = 0; i < TEST_ROUTE_COUNT; i++)
    {
      state[i] = {TEST_ROUTES[i].node_id, TEST_ROUTES[i].measurement_type, 0, false, false};
    }
  }

  CanSensorHandleResult handle(CanSensorRouteState *state, uint32_t frame_id,
                               const std::vector<uint8_t> &payload, uint32_t now_ms)
  {
    return can_sensor_handle_frame(state, TEST_ROUTE_COUNT, frame_id, payload, now_ms);
  }

  void test_scaling_all_supported_measurements()
  {
    assert_close(can_sensor_scale_value(SENSOR_SHT45_TEMP, 2156), 21.56f);
    assert_close(can_sensor_scale_value(SENSOR_SHT45_TEMP, -525), -5.25f);
    assert_close(can_sensor_scale_value(SENSOR_SHT45_RH, 5025), 50.25f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_TEMP, 2345), 23.45f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_RH, 6123), 61.23f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_PM1_0, 123), 12.3f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_PM2_5, 456), 45.6f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_PM4_0, 789), 78.9f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_PM10, 1001), 100.1f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_VOC_INDEX, 125), 125.0f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_NOX_INDEX, 42), 42.0f);
    assert_close(can_sensor_scale_value(SENSOR_SEN66_CO2, 800), 800.0f);
    assert(std::isnan(can_sensor_scale_value(65000, 123)));
  }

  void test_valid_routed_ok_frame_publishes_and_refreshes()
  {
    CanSensorRouteState state[TEST_ROUTE_COUNT]{};
    reset_state(state);

    auto result = handle(state, can_id(CAT_SENSOR, 100), sensor_payload(SENSOR_SHT45_TEMP, 2156), 1000);
    assert(result.decoded);
    assert(result.routed);
    assert(result.publish_value);
    assert(!result.publish_nan);
    assert(result.refreshed);
    assert(result.node_id == 100);
    assert(result.measurement_type == SENSOR_SHT45_TEMP);
    assert_close(result.value, 21.56f);
    assert(state[0].seen_ok);
    assert(!state[0].stale);
    assert(state[0].last_ok_ms == 1000);
    for (std::size_t i = 1; i < TEST_ROUTE_COUNT; i++)
    {
      assert(!state[i].seen_ok);
    }
  }

  void test_non_sensor_and_malformed_frames_are_ignored()
  {
    CanSensorRouteState state[TEST_ROUTE_COUNT]{};
    reset_state(state);

    auto non_sensor = handle(state, can_id(CAT_INPUT, 100), sensor_payload(SENSOR_SHT45_TEMP, 2156), 1000);
    assert(!non_sensor.decoded);

    auto short_payload = sensor_payload(SENSOR_SHT45_TEMP, 2156);
    short_payload.pop_back();
    auto short_result = handle(state, can_id(CAT_SENSOR, 100), short_payload, 1000);
    assert(!short_result.decoded);

    auto wrong_proto_payload = sensor_payload(SENSOR_SHT45_TEMP, 2156);
    wrong_proto_payload[0] = 0x7F;
    auto wrong_proto = handle(state, can_id(CAT_SENSOR, 100), wrong_proto_payload, 1000);
    assert(!wrong_proto.decoded);
    assert(!state[0].seen_ok);
  }

  void test_non_ok_status_publishes_nan_without_refresh()
  {
    CanSensorRouteState state[TEST_ROUTE_COUNT]{};
    reset_state(state);

    auto result = handle(state, can_id(CAT_SENSOR, 100),
                         sensor_payload(SENSOR_SHT45_TEMP, 2156, SENSOR_STATUS_ERROR), 1000);
    assert(result.decoded);
    assert(result.routed);
    assert(!result.publish_value);
    assert(result.publish_nan);
    assert(!result.refreshed);
    assert(!state[0].seen_ok);
  }

  void test_unknown_routes_do_not_publish_or_refresh()
  {
    CanSensorRouteState state[TEST_ROUTE_COUNT]{};
    reset_state(state);

    auto unknown_node = handle(state, can_id(CAT_SENSOR, 101), sensor_payload(SENSOR_SHT45_TEMP, 2156), 1000);
    assert(unknown_node.decoded);
    assert(!unknown_node.routed);
    assert(!unknown_node.publish_value);
    assert(!unknown_node.publish_nan);

    auto unsupported_measurement = handle(state, can_id(CAT_SENSOR, 100), sensor_payload(65000, 1), 1000);
    assert(unsupported_measurement.decoded);
    assert(!unsupported_measurement.routed);
    assert(!unsupported_measurement.publish_value);
    assert(!unsupported_measurement.publish_nan);
    assert(!state[0].seen_ok);
  }

  void test_stale_expiry_marks_exact_route_once_until_refreshed()
  {
    CanSensorRouteState state[] = {{100, SENSOR_SHT45_TEMP, 0, false, false}};
    constexpr std::size_t route_count = sizeof(state) / sizeof(state[0]);

    assert(can_sensor_refresh_route(state, route_count, 100, SENSOR_SHT45_TEMP, 1000));

    auto early = can_sensor_take_stale_routes(state, route_count, 90999);
    assert(early.empty());

    auto stale = can_sensor_take_stale_routes(state, route_count, 91000);
    assert(stale.size() == 1);
    assert(stale[0].node_id == 100);
    assert(stale[0].measurement_type == SENSOR_SHT45_TEMP);

    auto repeated = can_sensor_take_stale_routes(state, route_count, 100000);
    assert(repeated.empty());

    assert(can_sensor_refresh_route(state, route_count, 100, SENSOR_SHT45_TEMP, 101000));
    auto stale_again = can_sensor_take_stale_routes(state, route_count, 191000);
    assert(stale_again.size() == 1);
    assert(stale_again[0].measurement_type == SENSOR_SHT45_TEMP);
  }

  void test_stale_expiry_returns_all_expired_routes()
  {
    CanSensorRouteState state[] = {
        {100, SENSOR_SHT45_TEMP, 0, false, false},
        {100, SENSOR_SEN66_CO2, 0, false, false},
    };
    constexpr std::size_t route_count = sizeof(state) / sizeof(state[0]);

    assert(can_sensor_refresh_route(state, route_count, 100, SENSOR_SHT45_TEMP, 1000));
    assert(can_sensor_refresh_route(state, route_count, 100, SENSOR_SEN66_CO2, 1000));

    auto stale = can_sensor_take_stale_routes(state, route_count, 91000);
    assert(stale.size() == 2);
    assert(stale[0].node_id == 100);
    assert(stale[0].measurement_type == SENSOR_SHT45_TEMP);
    assert(stale[1].node_id == 100);
    assert(stale[1].measurement_type == SENSOR_SEN66_CO2);
  }

  void test_never_seen_route_expires_after_boot_threshold()
  {
    CanSensorRouteState state[TEST_ROUTE_COUNT]{};
    reset_state(state);

    auto early = can_sensor_take_stale_routes(state, TEST_ROUTE_COUNT, 89999);
    assert(early.empty());

    auto stale = can_sensor_take_stale_routes(state, TEST_ROUTE_COUNT, 90000);
    assert(stale.size() == TEST_ROUTE_COUNT);
    assert(stale[0].node_id == 100);
    assert(stale[0].measurement_type == SENSOR_SHT45_TEMP);
  }

  void test_millis_wraparound_staleness()
  {
    CanSensorRouteState state[] = {{100, SENSOR_SHT45_TEMP, 0, false, false}};
    constexpr std::size_t route_count = sizeof(state) / sizeof(state[0]);

    assert(can_sensor_refresh_route(state, route_count, 100, SENSOR_SHT45_TEMP, 0xFFFFFF00u));
    auto not_stale = can_sensor_take_stale_routes(state, route_count, 1000);
    assert(not_stale.empty());
    auto stale = can_sensor_take_stale_routes(state, route_count,
                                              static_cast<uint32_t>(0xFFFFFF00u + HVAC_CAN_SENSOR_STALE_TIMEOUT_MS));
    assert(stale.size() == 1);
  }

} // namespace

int main()
{
  test_scaling_all_supported_measurements();
  test_valid_routed_ok_frame_publishes_and_refreshes();
  test_non_sensor_and_malformed_frames_are_ignored();
  test_non_ok_status_publishes_nan_without_refresh();
  test_unknown_routes_do_not_publish_or_refresh();
  test_stale_expiry_marks_exact_route_once_until_refreshed();
  test_stale_expiry_returns_all_expired_routes();
  test_never_seen_route_expires_after_boot_threshold();
  test_millis_wraparound_staleness();
  return 0;
}
