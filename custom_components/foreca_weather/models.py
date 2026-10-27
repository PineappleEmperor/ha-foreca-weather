"""Data the coordinator hands to the entities."""

from dataclasses import dataclass

from pyforeca import AirQualityForecast, CurrentWeather, DailyForecast, HourlyForecast


@dataclass(frozen=True, kw_only=True)
class ForecaData:
    """One refresh for a location; air_quality is None when Foreca sends no hour."""

    current: CurrentWeather
    hourly: list[HourlyForecast]
    daily: list[DailyForecast]
    air_quality: AirQualityForecast | None
