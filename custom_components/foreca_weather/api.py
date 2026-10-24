"""Calls to the Foreca Weather API, through pyforeca.

Nothing here imports Home Assistant: the coordinator and the config flow translate
pyforeca's exceptions into Home Assistant's.
"""

import aiohttp
from pyforeca import ForecaApiClient, format_location

from .const import AIR_QUALITY_PERIODS, DAILY_PERIODS, HOURLY_PERIODS
from .models import ForecaData


class ForecaWeatherApi:
    """The Foreca requests one config entry makes, for one location."""

    def __init__(
        self,
        api_key: str,
        latitude: float,
        longitude: float,
        session: aiohttp.ClientSession,
    ) -> None:
        """Bind the key and the location to a shared session."""
        self._client = ForecaApiClient(api_key, session=session)
        self._location = format_location(longitude, latitude)

    async def async_get_location_name(self) -> str | None:
        """Return Foreca's name for the location, which also proves the key."""
        location = await self._client.location_info(self._location)
        return location.name

    async def async_get_data(self) -> ForecaData:
        """Fetch the current conditions, both forecasts and the air quality."""
        air_quality = await self._client.air_quality_hourly(
            self._location, periods=AIR_QUALITY_PERIODS
        )
        return ForecaData(
            current=await self._client.current(self._location),
            hourly=await self._client.forecast_hourly(
                self._location, periods=HOURLY_PERIODS
            ),
            daily=await self._client.forecast_daily(
                self._location, periods=DAILY_PERIODS
            ),
            air_quality=air_quality[0] if air_quality else None,
        )
