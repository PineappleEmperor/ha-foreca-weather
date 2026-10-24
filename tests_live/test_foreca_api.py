"""Contract tests against Foreca's live API.

These answer what a mock cannot: whether the key is accepted, whether the plan
serves every endpoint the integration calls, and whether the responses still have
the shape the integration reads. They run only through the Live API Tests
workflow, which hands them FORECA_API_KEY from an environment secret behind a
required reviewer. Home Assistant's test harness blocks the network, so they live
outside tests/ and run with it switched off. The location is a public one, and the
assertions name shapes and types, never values.
"""

from collections.abc import AsyncGenerator
import os

import aiohttp
from homeassistant.util import dt as dt_util
import pytest

from custom_components.foreca_weather.api import ForecaWeatherApi
from custom_components.foreca_weather.const import DAILY_PERIODS, HOURLY_PERIODS
from custom_components.foreca_weather.helpers import CONDITIONS, symbol_to_condition

LATITUDE = 60.1699
LONGITUDE = 24.9384


@pytest.fixture
async def api() -> AsyncGenerator[ForecaWeatherApi]:
    """Build the integration's API wrapper over a session of its own."""
    async with aiohttp.ClientSession() as session:
        yield ForecaWeatherApi(
            os.environ["FORECA_API_KEY"], LATITUDE, LONGITUDE, session
        )


async def test_location_name(api: ForecaWeatherApi) -> None:
    """The plan serves the location endpoint the config flow validates the key with."""
    name = await api.async_get_location_name()
    assert isinstance(name, str)
    assert name


async def test_current_conditions(api: ForecaWeatherApi) -> None:
    """The current conditions carry the values the entities read."""
    current = (await api.async_get_data()).current
    assert isinstance(current.temperature, int | float)
    assert isinstance(current.rel_humidity, int | float)
    assert isinstance(current.pressure, int | float)
    assert isinstance(current.wind_speed, int | float)
    assert symbol_to_condition(current.symbol) in CONDITIONS


async def test_hourly_forecast(api: ForecaWeatherApi) -> None:
    """The hourly forecast is the length asked for, with times Home Assistant parses."""
    hourly = (await api.async_get_data()).hourly
    assert len(hourly) == HOURLY_PERIODS
    assert all(dt_util.parse_datetime(hour.time or "") for hour in hourly)
    assert all(symbol_to_condition(hour.symbol) in CONDITIONS for hour in hourly)


async def test_daily_forecast(api: ForecaWeatherApi) -> None:
    """The daily forecast is the length asked for, with a date, a high and a low."""
    daily = (await api.async_get_data()).daily
    assert len(daily) == DAILY_PERIODS
    assert all(dt_util.parse_date(day.date or "") for day in daily)
    assert all(isinstance(day.max_temp, int | float) for day in daily)
    assert all(isinstance(day.min_temp, int | float) for day in daily)
