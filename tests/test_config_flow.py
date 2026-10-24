"""Tests for the config flow."""

from typing import Any

from aiohttp import ClientError
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.foreca_weather.const import DOMAIN

from .conftest import API_KEY, LATITUDE, LOCATION, LONGITUDE, mock_error, mock_responses

USER_INPUT = {
    CONF_API_KEY: API_KEY,
    CONF_LOCATION: {CONF_LATITUDE: LATITUDE, CONF_LONGITUDE: LONGITUDE},
}

ERRORS = [
    pytest.param({"status": 401}, "invalid_auth", id="invalid_auth"),
    pytest.param({"status": 403}, "invalid_auth", id="forbidden"),
    pytest.param({"status": 429}, "rate_limited", id="rate_limited"),
    pytest.param({"status": 500}, "cannot_connect", id="server_error"),
    pytest.param({"exc": ClientError()}, "cannot_connect", id="client_error"),
    pytest.param({"exc": ValueError()}, "unknown", id="unexpected"),
]


@pytest.mark.usefixtures("mock_foreca")
async def test_user_flow(hass: HomeAssistant) -> None:
    """The user step creates an entry titled with Foreca's name for the place."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Helsinki"
    assert result["data"] == {
        CONF_API_KEY: API_KEY,
        CONF_LATITUDE: LATITUDE,
        CONF_LONGITUDE: LONGITUDE,
    }
    assert result["result"].unique_id == LOCATION


async def test_user_flow_without_name(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
) -> None:
    """A location Foreca gives no name falls back to the home's name."""
    mock_responses(
        aioclient_mock, LOCATION, {**payloads, "location": {"id": 100658225}}
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == hass.config.location_name


@pytest.mark.parametrize(("failure", "error"), ERRORS)
async def test_user_flow_errors(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
    failure: dict[str, Any],
    error: str,
) -> None:
    """Each failure shows its error, and the flow recovers once Foreca answers."""
    mock_error(aioclient_mock, LOCATION, **failure)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    aioclient_mock.clear_requests()
    mock_responses(aioclient_mock, LOCATION, payloads)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("mock_foreca")
async def test_user_flow_already_configured(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """A location already set up is refused."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_flow(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
    mock_config_entry: MockConfigEntry,
) -> None:
    """A rejected key is shown as an error, and a good one replaces it."""
    mock_config_entry.add_to_hass(hass)
    mock_error(aioclient_mock, LOCATION, status=401)
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "bad-key"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    aioclient_mock.clear_requests()
    mock_responses(aioclient_mock, LOCATION, payloads)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: "new-key"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data[CONF_API_KEY] == "new-key"


async def test_reconfigure_flow(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
    mock_config_entry: MockConfigEntry,
) -> None:
    """A new location moves the entry, its unique id and its title."""
    mock_config_entry.add_to_hass(hass)
    mock_responses(
        aioclient_mock,
        "23.761,61.4978",
        {**payloads, "location": {"name": "Tampere"}},
    )
    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: 61.4978, CONF_LONGITUDE: 23.761}},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.title == "Tampere"
    assert mock_config_entry.unique_id == "23.7610,61.4978"
    assert mock_config_entry.data[CONF_LATITUDE] == 61.4978
    assert mock_config_entry.data[CONF_LONGITUDE] == 23.761


async def test_reconfigure_flow_error(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    payloads: dict[str, dict[str, Any]],
    mock_config_entry: MockConfigEntry,
) -> None:
    """An error keeps the form open; the same location then saves unchanged."""
    mock_config_entry.add_to_hass(hass)
    mock_error(aioclient_mock, LOCATION, status=500)
    result = await mock_config_entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: LATITUDE, CONF_LONGITUDE: LONGITUDE}},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    aioclient_mock.clear_requests()
    mock_responses(aioclient_mock, LOCATION, payloads)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: LATITUDE, CONF_LONGITUDE: LONGITUDE}},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.unique_id == LOCATION
    assert mock_config_entry.title == "Helsinki"


@pytest.mark.usefixtures("mock_foreca")
async def test_reconfigure_flow_already_configured(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Moving onto a location another entry has is refused."""
    mock_config_entry.add_to_hass(hass)
    other = MockConfigEntry(
        domain=DOMAIN,
        title="Tampere",
        unique_id="23.7610,61.4978",
        data={CONF_API_KEY: API_KEY, CONF_LATITUDE: 61.4978, CONF_LONGITUDE: 23.761},
    )
    other.add_to_hass(hass)
    result = await other.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_LOCATION: {CONF_LATITUDE: LATITUDE, CONF_LONGITUDE: LONGITUDE}},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
