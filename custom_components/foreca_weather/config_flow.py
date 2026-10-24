"""Config flow for the Foreca Weather integration.

One entry per location. Foreca's name for the location titles the entry, and asking
for it is also the request that proves the API key.
"""

from collections.abc import Mapping
import logging
from typing import Any, override

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    LocationSelector,
    LocationSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)
import probatio
from pyforeca import ForecaAuthError, ForecaError, ForecaRateLimitError

from .api import ForecaWeatherApi
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

API_KEY_SELECTOR = TextSelector(TextSelectorConfig(type=TextSelectorType.PASSWORD))
LOCATION_SELECTOR = LocationSelector(LocationSelectorConfig(radius=False))

USER_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_API_KEY): API_KEY_SELECTOR,
        probatio.Required(CONF_LOCATION): LOCATION_SELECTOR,
    }
)
REAUTH_SCHEMA = probatio.Schema({probatio.Required(CONF_API_KEY): API_KEY_SELECTOR})
RECONFIGURE_SCHEMA = probatio.Schema(
    {probatio.Required(CONF_LOCATION): LOCATION_SELECTOR}
)


def _unique_id(latitude: float, longitude: float) -> str:
    """Identify an entry by its location, to four decimal places."""
    return f"{longitude:.4f},{latitude:.4f}"


class ForecaWeatherConfigFlow(ConfigFlow, domain=DOMAIN):
    """Set up a location with a Foreca API key."""

    VERSION = 1

    async def _async_try_connect(
        self, api_key: str, latitude: float, longitude: float
    ) -> tuple[str | None, dict[str, str]]:
        """Return Foreca's name for the location, and the errors to show."""
        api = ForecaWeatherApi(
            api_key, latitude, longitude, async_get_clientsession(self.hass)
        )
        try:
            name = await api.async_get_location_name()
        except ForecaAuthError:
            return None, {"base": "invalid_auth"}
        except ForecaRateLimitError:
            return None, {"base": "rate_limited"}
        except ForecaError:
            return None, {"base": "cannot_connect"}
        except Exception:
            _LOGGER.exception("Unexpected error asking Foreca for the location")
            return None, {"base": "unknown"}
        return name, {}

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the API key and the location."""
        errors: dict[str, str] = {}
        if user_input is not None:
            latitude = user_input[CONF_LOCATION][CONF_LATITUDE]
            longitude = user_input[CONF_LOCATION][CONF_LONGITUDE]
            await self.async_set_unique_id(_unique_id(latitude, longitude))
            self._abort_if_unique_id_configured()
            name, errors = await self._async_try_connect(
                user_input[CONF_API_KEY], latitude, longitude
            )
            if not errors:
                return self.async_create_entry(
                    title=name or self.hass.config.location_name,
                    data={
                        CONF_API_KEY: user_input[CONF_API_KEY],
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                    },
                )
            suggested = user_input
        else:
            suggested = {
                CONF_LOCATION: {
                    CONF_LATITUDE: self.hass.config.latitude,
                    CONF_LONGITUDE: self.hass.config.longitude,
                }
            }
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, suggested),
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start over with a new API key once Foreca rejects the old one."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the new API key."""
        errors: dict[str, str] = {}
        if user_input is not None:
            entry = self._get_reauth_entry()
            _, errors = await self._async_try_connect(
                user_input[CONF_API_KEY],
                entry.data[CONF_LATITUDE],
                entry.data[CONF_LONGITUDE],
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry, data_updates={CONF_API_KEY: user_input[CONF_API_KEY]}
                )
        return self.async_show_form(
            step_id="reauth_confirm", data_schema=REAUTH_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Move the entry to another location."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            latitude = user_input[CONF_LOCATION][CONF_LATITUDE]
            longitude = user_input[CONF_LOCATION][CONF_LONGITUDE]
            unique_id = _unique_id(latitude, longitude)
            if unique_id != entry.unique_id:
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
            name, errors = await self._async_try_connect(
                entry.data[CONF_API_KEY], latitude, longitude
            )
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    title=name or entry.title,
                    unique_id=unique_id,
                    data_updates={CONF_LATITUDE: latitude, CONF_LONGITUDE: longitude},
                )
            suggested = user_input
        else:
            suggested = {
                CONF_LOCATION: {
                    CONF_LATITUDE: entry.data[CONF_LATITUDE],
                    CONF_LONGITUDE: entry.data[CONF_LONGITUDE],
                }
            }
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                RECONFIGURE_SCHEMA, suggested
            ),
            errors=errors,
        )
