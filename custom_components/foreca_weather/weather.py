"""The Foreca weather entity: current conditions and hourly and daily forecasts."""

from typing import override

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util
from pyforeca import CurrentWeather, DailyForecast, HourlyForecast

from .const import ATTRIBUTION
from .coordinator import ForecaConfigEntry, ForecaCoordinator
from .entity import foreca_device_info
from .helpers import symbol_to_condition

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ForecaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add the entry's weather entity."""
    async_add_entities([ForecaWeather(entry.runtime_data)])


def _hourly_forecast(start: str, item: HourlyForecast) -> Forecast:
    """Turn one hour of Foreca's forecast into Home Assistant's shape."""
    return Forecast(
        datetime=start,
        condition=symbol_to_condition(item.symbol),
        native_temperature=item.temperature,
        native_apparent_temperature=item.feels_like_temp,
        native_dew_point=item.dew_point,
        humidity=item.rel_humidity,
        native_pressure=item.pressure,
        native_wind_speed=item.wind_speed,
        native_wind_gust_speed=item.wind_gust,
        wind_bearing=item.wind_dir,
        native_precipitation=item.precip_accum,
        precipitation_probability=item.precip_prob,
        cloud_coverage=item.cloudiness,
        uv_index=item.uv_index,
    )


def _daily_forecast(date: str, item: DailyForecast) -> Forecast:
    """Turn one day of Foreca's forecast into Home Assistant's shape."""
    return Forecast(
        datetime=date,
        condition=symbol_to_condition(item.symbol),
        native_temperature=item.max_temp,
        native_templow=item.min_temp,
        native_apparent_temperature=item.max_feels_like_temp,
        native_pressure=item.pressure,
        native_wind_speed=item.max_wind_speed,
        native_wind_gust_speed=item.max_wind_gust,
        wind_bearing=item.wind_dir,
        native_precipitation=item.precip_accum,
        precipitation_probability=item.precip_prob,
        cloud_coverage=item.cloudiness,
        uv_index=item.uv_index,
    )


class ForecaWeather(SingleCoordinatorWeatherEntity[ForecaCoordinator]):
    """The weather at the entry's location, as Foreca forecasts it."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_native_wind_speed_unit = UnitOfSpeed.METERS_PER_SECOND
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: ForecaCoordinator) -> None:
        """Key the entity to its config entry."""
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._attr_unique_id = entry.entry_id
        self._attr_device_info = foreca_device_info(entry)

    @property
    def _current(self) -> CurrentWeather:
        """The latest current conditions."""
        return self.coordinator.data.current

    @property
    @override
    def condition(self) -> str | None:
        """Return the current condition."""
        return symbol_to_condition(self._current.symbol)

    @property
    @override
    def native_temperature(self) -> float | None:
        """Return the temperature."""
        return self._current.temperature

    @property
    @override
    def native_apparent_temperature(self) -> float | None:
        """Return the feels-like temperature."""
        return self._current.feels_like_temp

    @property
    @override
    def native_dew_point(self) -> float | None:
        """Return the dew point."""
        return self._current.dew_point

    @property
    @override
    def humidity(self) -> float | None:
        """Return the relative humidity."""
        return self._current.rel_humidity

    @property
    @override
    def native_pressure(self) -> float | None:
        """Return the sea-level pressure."""
        return self._current.pressure

    @property
    @override
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        return self._current.wind_speed

    @property
    @override
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed."""
        return self._current.wind_gust

    @property
    @override
    def wind_bearing(self) -> float | None:
        """Return the direction the wind blows from, in degrees."""
        return self._current.wind_dir

    @property
    @override
    def cloud_coverage(self) -> float | None:
        """Return the cloud cover in percent."""
        return self._current.cloudiness

    @property
    @override
    def uv_index(self) -> float | None:
        """Return the UV index."""
        return self._current.uv_index

    @property
    @override
    def native_visibility(self) -> float | None:
        """Return the visibility, which Foreca gives in metres, in kilometres."""
        visibility = self._current.visibility
        return None if visibility is None else visibility / 1000

    @callback
    @override
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hours still ahead."""
        now = dt_util.utcnow()
        return [
            _hourly_forecast(time, item)
            for item in self.coordinator.data.hourly
            if (time := item.time) is not None
            and (start := dt_util.parse_datetime(time)) is not None
            and start >= now
        ]

    @callback
    @override
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the days Foreca forecasts."""
        return [
            _daily_forecast(date, item)
            for item in self.coordinator.data.daily
            if (date := item.date) is not None
        ]
