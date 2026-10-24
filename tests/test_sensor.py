"""Tests for the sensor platform."""

from typing import Any

from homeassistant.components.sensor import ATTR_OPTIONS, ATTR_STATE_CLASS
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_UNIT_OF_MEASUREMENT,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from .conftest import LOCATION, mock_responses

ENABLED = [
    ("sensor.helsinki_temperature", "7.1"),
    ("sensor.helsinki_humidity", "82"),
    ("sensor.helsinki_atmospheric_pressure", "1012.4"),
    ("sensor.helsinki_wind_speed", "15.48"),
    ("sensor.helsinki_uv_index", "1"),
]

DISABLED = [
    ("sensor.helsinki_apparent_temperature", "3.2"),
    ("sensor.helsinki_dew_point", "4.1"),
    ("sensor.helsinki_wind_gust_speed", "34.56"),
    ("sensor.helsinki_wind_direction", "220"),
    ("sensor.helsinki_precipitation_intensity", "0"),
    ("sensor.helsinki_precipitation_probability", "20"),
    ("sensor.helsinki_thunder_probability", "0"),
    ("sensor.helsinki_cloud_coverage", "75"),
    ("sensor.helsinki_visibility", "19.934"),
    ("sensor.helsinki_condition", "cloudy"),
    ("sensor.helsinki_description", "overcast"),
    ("sensor.helsinki_high_temperature_today", "8.2"),
    ("sensor.helsinki_low_temperature_today", "3.9"),
    ("sensor.helsinki_precipitation_today", "2.6"),
]

TODAY = [
    "sensor.helsinki_high_temperature_today",
    "sensor.helsinki_low_temperature_today",
    "sensor.helsinki_precipitation_today",
]


@pytest.mark.usefixtures("init_integration")
@pytest.mark.parametrize(("entity_id", "value"), ENABLED)
async def test_enabled_sensors(hass: HomeAssistant, entity_id: str, value: str) -> None:
    """The common five are on by default and read the current conditions."""
    assert hass.states.get(entity_id).state == value


@pytest.mark.usefixtures("init_integration")
@pytest.mark.parametrize("entity_id", [entity_id for entity_id, _ in DISABLED])
async def test_disabled_by_default(
    entity_registry: er.EntityRegistry, entity_id: str
) -> None:
    """Every other sensor is created disabled."""
    entry = entity_registry.async_get(entity_id)
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
@pytest.mark.parametrize(("entity_id", "value"), DISABLED)
async def test_disabled_sensors_once_enabled(
    hass: HomeAssistant, entity_id: str, value: str
) -> None:
    """Each disabled sensor reads its value once enabled."""
    assert hass.states.get(entity_id).state == value


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "init_integration")
async def test_sensor_classes(hass: HomeAssistant) -> None:
    """The device and state classes are the legal pairs chosen for each value."""
    temperature = hass.states.get("sensor.helsinki_temperature").attributes
    assert temperature[ATTR_DEVICE_CLASS] == "temperature"
    assert temperature[ATTR_STATE_CLASS] == "measurement"
    assert temperature[ATTR_UNIT_OF_MEASUREMENT] == "°C"

    bearing = hass.states.get("sensor.helsinki_wind_direction").attributes
    assert bearing[ATTR_DEVICE_CLASS] == "wind_direction"
    assert bearing[ATTR_STATE_CLASS] == "measurement_angle"

    condition = hass.states.get("sensor.helsinki_condition").attributes
    assert condition[ATTR_DEVICE_CLASS] == "enum"
    assert "cloudy" in condition[ATTR_OPTIONS]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
@pytest.mark.parametrize("entity_id", TODAY)
async def test_today_without_daily_forecast(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
    mock_config_entry: MockConfigEntry,
    entity_id: str,
) -> None:
    """Today's sensors read unknown when Foreca sends no daily forecast."""
    mock_responses(aioclient_mock, LOCATION, {**payloads, "daily": {"forecast": []}})
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == STATE_UNKNOWN
