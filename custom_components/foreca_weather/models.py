"""Data the coordinator hands to the entities."""

from dataclasses import dataclass

from pyforeca import CurrentWeather, DailyForecast, HourlyForecast


@dataclass(frozen=True, kw_only=True)
class ForecaData:
    """One refresh: the current conditions and both forecasts for a location."""

    current: CurrentWeather
    hourly: list[HourlyForecast]
    daily: list[DailyForecast]
