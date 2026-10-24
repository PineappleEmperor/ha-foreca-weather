"""Tests for the weather entity."""

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_WEATHER_APPARENT_TEMPERATURE,
    ATTR_WEATHER_CLOUD_COVERAGE,
    ATTR_WEATHER_DEW_POINT,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_UV_INDEX,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED,
    DOMAIN as WEATHER_DOMAIN,
    SERVICE_GET_FORECASTS,
)
from homeassistant.const import ATTR_ATTRIBUTION, ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

WEATHER = "weather.helsinki"


@pytest.mark.usefixtures("init_integration")
async def test_current_conditions(hass: HomeAssistant) -> None:
    """The state is the mapped condition; the attributes are the current values."""
    state = hass.states.get(WEATHER)
    assert state.state == "cloudy"
    assert state.attributes[ATTR_WEATHER_TEMPERATURE] == 7.1
    assert state.attributes[ATTR_WEATHER_APPARENT_TEMPERATURE] == 3.2
    assert state.attributes[ATTR_WEATHER_DEW_POINT] == 4.1
    assert state.attributes[ATTR_WEATHER_HUMIDITY] == 82
    assert state.attributes[ATTR_WEATHER_PRESSURE] == 1012.4
    assert state.attributes[ATTR_WEATHER_WIND_SPEED] == 15.48
    assert state.attributes[ATTR_WEATHER_WIND_GUST_SPEED] == 34.56
    assert state.attributes[ATTR_WEATHER_WIND_BEARING] == 220
    assert state.attributes[ATTR_WEATHER_CLOUD_COVERAGE] == 75
    assert state.attributes[ATTR_WEATHER_UV_INDEX] == 1
    assert state.attributes[ATTR_WEATHER_VISIBILITY] == 19.93
    assert state.attributes[ATTR_ATTRIBUTION] == "Weather data provided by Foreca"


async def test_unique_id(
    entity_registry: er.EntityRegistry, init_integration: MockConfigEntry
) -> None:
    """The weather entity is keyed to its config entry."""
    entry = entity_registry.async_get(WEATHER)
    assert entry.unique_id == init_integration.entry_id


@pytest.mark.usefixtures("init_integration")
async def test_hourly_forecast(hass: HomeAssistant) -> None:
    """The hourly forecast leaves out the hour that has passed."""
    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: WEATHER, "type": "hourly"},
        blocking=True,
        return_response=True,
    )
    forecast = response[WEATHER]["forecast"]
    assert [hour[ATTR_FORECAST_CONDITION] for hour in forecast] == [
        "rainy",
        "pouring",
    ]
    assert forecast[0][ATTR_FORECAST_TEMP] == 7.3
    assert forecast[1][ATTR_FORECAST_PRECIPITATION] == 1.2
    assert forecast[1][ATTR_FORECAST_PRECIPITATION_PROBABILITY] == 80


@pytest.mark.usefixtures("init_integration")
async def test_daily_forecast(hass: HomeAssistant) -> None:
    """The daily forecast carries each day's high and low."""
    response = await hass.services.async_call(
        WEATHER_DOMAIN,
        SERVICE_GET_FORECASTS,
        {ATTR_ENTITY_ID: WEATHER, "type": "daily"},
        blocking=True,
        return_response=True,
    )
    forecast = response[WEATHER]["forecast"]
    assert [day["datetime"] for day in forecast] == ["2026-10-24", "2026-10-25"]
    assert [day[ATTR_FORECAST_CONDITION] for day in forecast] == [
        "rainy",
        "partlycloudy",
    ]
    assert forecast[0][ATTR_FORECAST_TEMP] == 8.2
    assert forecast[0][ATTR_FORECAST_TEMP_LOW] == 3.9
