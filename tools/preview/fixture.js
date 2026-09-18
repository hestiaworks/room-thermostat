/**
 * A house to draw, with no Home Assistant behind it.
 *
 * Three rooms — one out of season, one heating, one cooling — and enough
 * history for both charts, because a chart with no data looks fine and a
 * chart with real data is where the layout falls over.
 */

export const ROOMS = [
  {
    id: "living-room", name: "Living Room",
    temperature_sensor: "sensor.living_room_temp",
    humidity_sensor: "sensor.living_room_humidity",
    cooler: "climate.living_room_ac", heaters: [], inverted_heaters: [],
    cooling_strategy: "gated", offset_correction: false, parked_setpoint: 17,
    cool_cold_tolerance: 0.5, cool_hot_tolerance: 0.5,
    cool_min_on: 900, cool_min_off: 900,
    heat_cold_tolerance: 0.3, heat_hot_tolerance: 0.3,
    heat_min_on: 300, heat_min_off: 300,
    valve_travel: 180, allow_ac_heat: false, frost_temperature: 5,
  },
  {
    id: "bedroom", name: "Bedroom",
    temperature_sensor: "sensor.bedroom_temp", humidity_sensor: "sensor.bedroom_humidity",
    cooler: "climate.bedroom_ac", heaters: ["valve.bedroom"], inverted_heaters: [],
    cooling_strategy: "passthrough", offset_correction: false, parked_setpoint: 17,
    cool_cold_tolerance: 0.5, cool_hot_tolerance: 0.5,
    cool_min_on: 900, cool_min_off: 900,
    heat_cold_tolerance: 0.3, heat_hot_tolerance: 0.3,
    heat_min_on: 300, heat_min_off: 300,
    valve_travel: 180, allow_ac_heat: false, frost_temperature: 5,
  },
  {
    id: "office", name: "Office Thermostat",
    temperature_sensor: "sensor.office_temp", humidity_sensor: null,
    cooler: "climate.office_ac", heaters: ["valve.office"], inverted_heaters: [],
    cooling_strategy: "passthrough", offset_correction: false, parked_setpoint: 17,
    cool_cold_tolerance: 0.5, cool_hot_tolerance: 0.5,
    cool_min_on: 900, cool_min_off: 900,
    heat_cold_tolerance: 0.3, heat_hot_tolerance: 0.3,
    heat_min_on: 300, heat_min_off: 300,
    valve_travel: 180, allow_ac_heat: false, frost_temperature: 5,
  },
];

export const HOUSE = {
  outdoor_sensor: "weather.forecast_home", damping_hours: 30,
  season_dwell_hours: 6, heat_limit: 16, heat_limit_hysteresis: 1,
  cool_limit: 15, cool_limit_hysteresis: 1, heat_override: 4, cool_override: 4,
};

const climate = (entityId, name, roomId, extra) => [entityId, {
  entity_id: entityId,
  state: extra.mode,
  attributes: {
    friendly_name: name, room_id: roomId,
    current_temperature: extra.temperature, current_humidity: extra.humidity,
    temperature: extra.target, hvac_action: extra.action,
    hvac_modes: extra.modes || ["off", "heat", "cool", "dry", "fan_only", "heat_cool"],
    heating_season: extra.heatingSeason, cooling_season: true,
    min_temp: 16, max_temp: 30,
  },
}];

/** A few of the house's own entities, so the pickers have something to find. */
const SOURCES = [
  ["sensor.living_room_temp", "Living Room Temp", { device_class: "temperature", unit_of_measurement: "°C" }, "21.4"],
  ["sensor.living_room_humidity", "Living Room Humidity", { device_class: "humidity" }, "48"],
  ["sensor.bedroom_temp", "Bedroom Temp", { device_class: "temperature" }, "19.8"],
  ["sensor.bedroom_humidity", "Bedroom Humidity", { device_class: "humidity" }, "52"],
  ["sensor.office_temp", "Office Temp", { device_class: "temperature" }, "22.1"],
  ["sensor.hall_temp", "Hall Temp", { device_class: "temperature" }, "20.2"],
  ["climate.living_room_ac", "Living Room AC", {}, "cool"],
  ["climate.bedroom_ac", "Bedroom AC", {}, "off"],
  ["climate.office_ac", "Office AC", {}, "cool"],
  ["valve.bedroom", "Bedroom Radiator", {}, "closed"],
  ["valve.office", "Office Radiator", {}, "open"],
  ["switch.hall_floor", "Hall Floor Loop", {}, "off"],
  ["weather.forecast_home", "Forecast Home", { temperature: 19.4, temperature_unit: "°C" }, "cloudy"],
];

export const STATES = Object.fromEntries([
  ...SOURCES.map(([entityId, name, attributes, state]) => [entityId, {
    entity_id: entityId, state,
    attributes: { friendly_name: name, ...attributes },
  }]),
  climate("climate.living_room_thermostat", "Living Room", "living-room", {
    mode: "heat", temperature: 21.4, humidity: 48, target: 22,
    action: "idle", heatingSeason: false,
  }),
  climate("climate.bedroom_thermostat", "Bedroom", "bedroom", {
    mode: "heat", temperature: 19.8, humidity: 52, target: 21,
    action: "heating", heatingSeason: true,
  }),
  climate("climate.office_thermostat", "Office Thermostat", "office", {
    mode: "cool", temperature: 22.1, humidity: undefined, target: 24,
    action: "cooling", heatingSeason: true,
    modes: ["off", "cool", "dry", "fan_only"],
  }),
  ["binary_sensor.room_thermostat_heating_season", {
    entity_id: "binary_sensor.room_thermostat_heating_season",
    state: "off",
    attributes: {
      friendly_name: "Heating season", damped: 17.2, outdoor: 19.4,
      limit: 16, hysteresis: 1, averaging_hours: 30, dwell_hours: 6,
    },
  }],
  ["sensor.room_thermostat_outdoor_average", {
    entity_id: "sensor.room_thermostat_outdoor_average",
    state: "17.2", attributes: { friendly_name: "Outdoor average" },
  }],
]);

/** A day's worth of weather, as a sine wave, so the charts have a shape. */
function history(span) {
  const buckets = { "24h": 96, "7d": 168, "30d": 120, "90d": 90 }[span] || 168;
  const seconds = { "24h": 86400, "7d": 604800, "30d": 2592000, "90d": 7776000 }[span];
  const end = Date.now() / 1000;
  const start = end - seconds;
  const days = seconds / 86400;
  const wave = (i, mean, amplitude) =>
    mean - amplitude * Math.cos((i / buckets) * days * 2 * Math.PI);
  const drift = (i) => 17 + 3 * Math.sin((i / buckets) * Math.PI);
  return {
    start, end, buckets,
    series: {
      outdoor: Array.from({ length: buckets }, (_, i) => wave(i, drift(i), 7)),
      damped: Array.from({ length: buckets }, (_, i) => drift(i) + 0.2),
      rooms: {
        "living-room": {
          name: "Living Room",
          points: Array.from({ length: buckets }, (_, i) => wave(i, 21.4, 0.8)),
        },
        bedroom: {
          name: "Bedroom",
          // A gap where the sensor dropped out, so the break in the line is
          // drawn at least once before anybody sees it on the real house.
          points: Array.from({ length: buckets }, (_, i) =>
            i > buckets * 0.3 && i < buckets * 0.36 ? null : wave(i, 19.8, 1.2)),
        },
        office: {
          name: "Office Thermostat",
          points: Array.from({ length: buckets }, (_, i) => wave(i, 22.1, 0.5)),
        },
      },
    },
    seasons: [[start + seconds * 0.08, start + seconds * 0.42]],
    demand: {
      "living-room": Array.from({ length: buckets }, (_, i) => (i % 17 < 4 ? 1 : 0)),
      bedroom: Array.from({ length: buckets }, (_, i) => (i % 11 < 5 ? 1 : 0)),
      office: Array.from({ length: buckets }, () => 0),
    },
    daily: Array.from({ length: 46 }, (_, i) => {
      const outdoor = i * 0.5;
      const hours = Math.max(0, 11 - outdoor * 0.72) + ((i % 4) - 1.5) * 0.5;
      return {
        date: `2026-01-${String((i % 28) + 1).padStart(2, "0")}`,
        outdoor,
        hours: Math.max(0, hours),
      };
    }),
    balance_point: 14.6,
  };
}

export function fakeHass() {
  return {
    states: STATES,
    themes: {},
    callService: async () => ({}),
    connection: {
      sendMessagePromise: async (message) => {
        if (message.type === "room_thermostat/rooms/list") {
          return { rooms: ROOMS, house: HOUSE };
        }
        if (message.type === "room_thermostat/history") return history(message.span);
        if (message.type === "room_thermostat/rooms/update") {
          return { ...ROOMS[0], ...message.room };
        }
        if (message.type === "room_thermostat/rooms/create") {
          return { ...message.room, id: "new-room" };
        }
        if (message.type === "room_thermostat/rooms/delete") {
          return { deleted: message.room_id };
        }
        if (message.type === "room_thermostat/house/update") {
          return { ...HOUSE, ...message.house };
        }
        return {};
      },
      subscribeEvents: async () => () => {},
    },
  };
}
