"""Diagnostics for a Foreca Weather config entry."""

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .coordinator import ForecaConfigEntry

TO_REDACT = {CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ForecaConfigEntry
) -> dict[str, Any]:
    """Return the entry's settings and the latest refresh, key and location redacted."""
    data = entry.runtime_data.data
    return {
        "entry_data": async_redact_data(entry.data, TO_REDACT),
        "current": asdict(data.current),
        "hourly": [asdict(item) for item in data.hourly],
        "daily": [asdict(item) for item in data.daily],
    }
