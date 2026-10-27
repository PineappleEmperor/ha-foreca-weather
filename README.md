# Foreca Weather

Weather and forecasts from [Foreca](https://www.foreca.com) in Home Assistant: a weather
entity with the current conditions and hourly and daily forecasts, and sensors for the
values worth a history of their own, air quality among them.

> [!NOTE]
> **AI assistance:** I'm a programmer; this project is built with AI (Claude, via Claude Code) for implementation, code review, and QA — under human direction, guided by my [`ha-integration`](https://github.com/PineappleEmperor/ha-skills) skill. Architecture and final review are mine; every change is human-reviewed before it merges.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=PineappleEmperor&repository=ha-foreca-weather&category=integration)

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=foreca_weather)

## What it does

Each entry is one place. For it, the integration asks Foreca's Weather API for the
current conditions, the next 24 hours, the next 7 days and the air quality, and shows
them as:

- a **weather entity**, whose state is the current condition and whose hourly and daily
  forecasts work with the weather card and the `weather.get_forecasts` action;
- **sensors**, one per value, so each can be graphed, kept in long-term statistics and
  used in automations.

Weather data is provided by Foreca, and every entity says so in its attribution.

### Use cases

- Close the blinds or start the irrigation on the forecast rather than the current
  reading.
- Graph temperature, wind and pressure against your own sensors.
- Warn when the chance of precipitation in the next hours passes a threshold.
- Close the windows or start the air purifier when the air quality index climbs.
- Follow several places — home, a cabin, a commute — as separate entries.

## Installation

### HACS

1. Open HACS with the first button above, or add this repository to HACS as a custom
   repository of type *Integration*.
2. Download **Foreca Weather**.
3. Restart Home Assistant.

### Manual

1. Download `foreca_weather.zip` from the latest release.
2. Unzip it into `config/custom_components/foreca_weather/`.
3. Restart Home Assistant.

## Configuration

You need a Foreca Weather API key: sign up at
[developer.foreca.com](https://developer.foreca.com) and create a key under **My API**.

Add the integration with the second button above, or from **Settings** → **Devices &
services** → **Add integration** → **Foreca Weather**.

| Parameter | What it is |
|---|---|
| API key | The key from **My API** on Foreca's developer site. |
| Location | The place to forecast. It starts at your home's location; move the pin for anywhere else. |

The entry is named after Foreca's name for the place. Add another entry for each further
place; the same place cannot be added twice.

- **Change the place:** the entry's menu → **Reconfigure**.
- **Replace a key Foreca no longer accepts:** Home Assistant asks for a new one on its
  own, on the integration's page.

The integration has no options.

## What you get

### The weather entity

| Value | From Foreca |
|---|---|
| Condition | the weather symbol |
| Temperature, apparent temperature, dew point | °C |
| Humidity, cloud coverage | % |
| Pressure | hPa, at sea level |
| Wind speed, wind gust speed | m/s |
| Wind bearing | degrees |
| UV index | — |
| Visibility | km |
| Hourly forecast | the next 24 hours, from the coming hour |
| Daily forecast | 7 days, from today: high, low, precipitation and its probability |

Home Assistant converts every value to your unit system.

### Sensors

The first six are enabled; enable any other from the entity's settings. The air-quality
indices are on the US EPA scale, where lower is better; each pollutant's own index is the
one the overall index takes the worst of.

| Sensor | Enabled by default |
|---|---|
| Temperature | yes |
| Humidity | yes |
| Atmospheric pressure | yes |
| Wind speed | yes |
| UV index | yes |
| Air quality index | yes |
| Apparent temperature | no |
| Dew point | no |
| Wind gust speed | no |
| Wind direction | no |
| Precipitation intensity | no |
| Precipitation probability | no |
| Thunder probability | no |
| Cloud coverage | no |
| Visibility | no |
| Condition | no |
| Description, Foreca's own words for the weather | no |
| High temperature today | no |
| Low temperature today | no |
| Precipitation today | no |
| Main pollutant | no |
| Carbon monoxide, nitrogen dioxide, ozone, sulphur dioxide, PM10 and PM2.5 air quality index, one sensor each | no |

## Data updates

The integration polls Foreca every 10 minutes. Each poll is four requests — current
conditions, hourly forecast, daily forecast, air quality — so one entry makes 576
requests a day, within the free plan's 2,000. Adding a place or changing one makes one request more.

## Example

Turn on a light when rain is likely in the next hour, for an entry Foreca named Helsinki:

```yaml
triggers:
  - trigger: time_pattern
    minutes: "/30"
actions:
  - action: weather.get_forecasts
    target:
      entity_id: weather.helsinki
    data:
      type: hourly
    response_variable: forecast
  - condition: template
    value_template: >
      {{ forecast['weather.helsinki'].forecast[0].precipitation_probability > 60 }}
  - action: light.turn_on
    target:
      entity_id: light.hallway
```

## Known limitations

- Foreca's free plan allows 2,000 requests a day and non-commercial use only; three
  entries on one key use 1,728 of them.
- The conditions come from Foreca's weather symbol, which describes cloud cover and
  precipitation. It has no wind, hail or exceptional weather, so the integration never
  reports `windy`, `windy-variant`, `hail`, `lightning` without rain, or `exceptional`.
- The forecast covers 24 hours and 7 days. Weather warnings and pollen are not included.
- The air quality is the nearest hour of Foreca's air-quality forecast, not a reading
  from a station.
- The values are Foreca's in metric units; Home Assistant does the conversion.

## Troubleshooting

| Symptom | What to do |
|---|---|
| Setup says Foreca rejected the API key | Check the key under **My API**, and that the account is still active: a trial key stops working when the trial ends. |
| Setup says the request limit is used up | Wait for the daily limit to reset, or use a key with fewer entries on it. |
| The entities go unavailable | Foreca could not be reached, or the request limit is used up. They come back on the next successful poll; the log says why. |
| Home Assistant asks for a new API key | Foreca stopped accepting the key. Enter a new one. |

For a bug report, download the diagnostics from the entry's menu — the API key and the
location are redacted — and turn on debug logging:

```yaml
logger:
  logs:
    custom_components.foreca_weather: debug
    pyforeca: debug
```

## Removal

1. **Settings** → **Devices & services** → **Foreca Weather** → each entry's menu →
   **Delete**.
2. In HACS, open **Foreca Weather** and **Remove** it, or delete
   `config/custom_components/foreca_weather/` for a manual install.
3. Restart Home Assistant.

## Licence

MIT. The Foreca name and logo belong to Foreca Ltd and are used only to identify the data
source.
