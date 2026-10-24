"""The coordinator that polls Foreca for one config entry."""

import logging
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from pyforeca import ForecaAuthError, ForecaError, ForecaRateLimitError

from .api import ForecaWeatherApi
from .const import DOMAIN, UPDATE_INTERVAL
from .models import ForecaData

_LOGGER = logging.getLogger(__name__)

type ForecaConfigEntry = ConfigEntry[ForecaCoordinator]


class ForecaCoordinator(DataUpdateCoordinator[ForecaData]):
    """Fetches the current conditions and both forecasts on one schedule."""

    config_entry: ForecaConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ForecaConfigEntry, api: ForecaWeatherApi
    ) -> None:
        """Poll the entry's location every update interval."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            always_update=False,
        )
        self.api = api

    @override
    async def _async_update_data(self) -> ForecaData:
        """Fetch one refresh, mapping Foreca's errors onto Home Assistant's."""
        try:
            return await self.api.async_get_data()
        except ForecaAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN, translation_key="invalid_auth"
            ) from err
        except ForecaRateLimitError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN, translation_key="rate_limited"
            ) from err
        except ForecaError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders={"error": str(err)},
            ) from err
