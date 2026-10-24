"""Tests for setting up, refreshing and unloading a config entry."""

from typing import Any

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.foreca_weather.const import DOMAIN, UPDATE_INTERVAL

from .conftest import API_KEY, LOCATION, mock_error, mock_responses

WEATHER = "weather.helsinki"


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The entry loads with its entities, and unloads cleanly."""
    assert init_integration.state is ConfigEntryState.LOADED
    assert hass.states.get(WEATHER) is not None

    assert await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED


async def test_setup_two_entries(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
    mock_config_entry: MockConfigEntry,
) -> None:
    """Two locations set up side by side."""
    mock_responses(aioclient_mock, LOCATION, payloads)
    mock_responses(aioclient_mock, "23.761,61.4978", payloads)
    other = MockConfigEntry(
        domain=DOMAIN,
        title="Tampere",
        unique_id="23.7610,61.4978",
        data={CONF_API_KEY: API_KEY, CONF_LATITUDE: 61.4978, CONF_LONGITUDE: 23.761},
    )
    mock_config_entry.add_to_hass(hass)
    other.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert other.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert await hass.config_entries.async_unload(other.entry_id)


@pytest.mark.parametrize(
    ("status", "state"),
    [
        pytest.param(500, ConfigEntryState.SETUP_RETRY, id="server_error"),
        pytest.param(429, ConfigEntryState.SETUP_RETRY, id="rate_limited"),
        pytest.param(401, ConfigEntryState.SETUP_ERROR, id="invalid_auth"),
    ],
)
async def test_setup_failure(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
    status: int,
    state: ConfigEntryState,
) -> None:
    """A failed first refresh retries, unless Foreca rejected the key."""
    mock_error(aioclient_mock, LOCATION, status=status)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is state


async def test_setup_auth_failure_starts_reauth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """A rejected key at setup asks the user for a new one."""
    mock_error(aioclient_mock, LOCATION, status=401)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]


@pytest.mark.usefixtures("init_integration")
@pytest.mark.parametrize("status", [500, 429])
async def test_refresh_failure_and_recovery(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
    freezer: FrozenDateTimeFactory,
    status: int,
) -> None:
    """A failed refresh takes the entities unavailable until Foreca answers again."""
    aioclient_mock.clear_requests()
    mock_error(aioclient_mock, LOCATION, status=status)
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(WEATHER).state == STATE_UNAVAILABLE

    aioclient_mock.clear_requests()
    mock_responses(aioclient_mock, LOCATION, payloads)
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(WEATHER).state == "cloudy"


async def test_refresh_auth_failure_starts_reauth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    freezer: FrozenDateTimeFactory,
    init_integration: MockConfigEntry,
) -> None:
    """A key Foreca stops accepting takes the entities unavailable and asks for a new one."""
    aioclient_mock.clear_requests()
    mock_error(aioclient_mock, LOCATION, status=401)
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(WEATHER).state == STATE_UNAVAILABLE

    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [flow["context"]["source"] for flow in flows] == [SOURCE_REAUTH]
    assert flows[0]["context"]["entry_id"] == init_integration.entry_id
