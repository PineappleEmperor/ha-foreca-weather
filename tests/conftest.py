"""Fixtures for the integration's tests."""

from collections.abc import Generator
from datetime import timedelta
from typing import Any
from unittest.mock import PropertyMock, patch

from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    load_json_object_fixture,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

# Without this import, setup fails with "Integration not found".
import custom_components  # noqa: F401
from custom_components.foreca_weather.const import DOMAIN

API_KEY = "test-api-key"
LATITUDE = 60.1699
LONGITUDE = 24.9384
LOCATION = "24.9384,60.1699"
BASE_URL = "https://weatherapi.foreca.net/api/v1"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Let Home Assistant load integrations from custom_components/ in every test."""


@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Create every entity enabled, as core's fixture of the same name does."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        return_value=True,
        new_callable=PropertyMock,
    ):
        yield


def mock_responses(
    aioclient_mock: AiohttpClientMocker,
    location: str,
    payloads: dict[str, dict[str, Any]],
) -> None:
    """Answer every Foreca request for a location with the given payloads."""
    aioclient_mock.get(f"{BASE_URL}/location/{location}", json=payloads["location"])
    aioclient_mock.get(f"{BASE_URL}/current/{location}", json=payloads["current"])
    aioclient_mock.get(
        f"{BASE_URL}/forecast/hourly/{location}", json=payloads["hourly"]
    )
    aioclient_mock.get(f"{BASE_URL}/forecast/daily/{location}", json=payloads["daily"])


def mock_error(
    aioclient_mock: AiohttpClientMocker,
    location: str,
    status: int = 200,
    exc: Exception | None = None,
) -> None:
    """Fail every Foreca request for a location with a status or an exception."""
    for path in ("location", "current", "forecast/hourly", "forecast/daily"):
        aioclient_mock.get(f"{BASE_URL}/{path}/{location}", status=status, exc=exc)


@pytest.fixture
def payloads() -> dict[str, dict[str, Any]]:
    """Load the fixtures, the hourly times moved so only the first has passed."""
    hourly = load_json_object_fixture("hourly.json")
    now = dt_util.utcnow()
    hourly["forecast"] = [
        {**item, "time": (now + timedelta(hours=offset)).isoformat("T", "minutes")}
        for offset, item in zip((-1, 1, 2), hourly["forecast"], strict=True)
    ]
    return {
        "location": load_json_object_fixture("location.json"),
        "current": load_json_object_fixture("current.json"),
        "hourly": hourly,
        "daily": load_json_object_fixture("daily.json"),
    }


@pytest.fixture
def mock_foreca(
    aioclient_mock: AiohttpClientMocker, payloads: dict[str, dict[str, Any]]
) -> AiohttpClientMocker:
    """Answer Foreca's API for the test location from the fixtures."""
    mock_responses(aioclient_mock, LOCATION, payloads)
    return aioclient_mock


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """A config entry for the test location."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Helsinki",
        unique_id=LOCATION,
        data={
            CONF_API_KEY: API_KEY,
            CONF_LATITUDE: LATITUDE,
            CONF_LONGITUDE: LONGITUDE,
        },
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_foreca: AiohttpClientMocker,
) -> MockConfigEntry:
    """Set the test config entry up against the mocked API."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry
