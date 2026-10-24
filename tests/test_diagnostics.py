"""Tests for the diagnostics download."""

from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
) -> None:
    """The download carries the latest refresh with the key and location redacted."""
    result = await get_diagnostics_for_config_entry(hass, hass_client, init_integration)
    assert result["entry_data"] == {
        "api_key": REDACTED,
        "latitude": REDACTED,
        "longitude": REDACTED,
    }
    assert result["current"]["temperature"] == 7.1
    assert len(result["hourly"]) == 3
    assert [day["date"] for day in result["daily"]] == ["2026-10-24", "2026-10-25"]
    assert result["air_quality"]["aqi"] == 102
