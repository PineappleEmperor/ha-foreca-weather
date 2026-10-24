"""Foreca sensors: one per value worth a history of its own."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    UV_INDEX,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfRatio,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from pyforeca import AirQualityForecast, DailyForecast

from .coordinator import ForecaConfigEntry, ForecaCoordinator
from .entity import ForecaEntity
from .helpers import CONDITIONS, POLLUTANTS, pollutant_key, symbol_to_condition
from .models import ForecaData

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class ForecaSensorDescription(SensorEntityDescription):
    """Describes one Foreca sensor and where its value comes from."""

    value_fn: Callable[[ForecaData], StateType]


def _today(
    data: ForecaData, value_fn: Callable[[DailyForecast], StateType]
) -> StateType:
    """Read a value from today's forecast, the first day Foreca sends."""
    return value_fn(data.daily[0]) if data.daily else None


def _air_quality(
    data: ForecaData, value_fn: Callable[[AirQualityForecast], StateType]
) -> StateType:
    """Read a value from the nearest hour of the air-quality forecast."""
    return value_fn(data.air_quality) if data.air_quality else None


SENSORS: tuple[ForecaSensorDescription, ...] = (
    ForecaSensorDescription(
        key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.current.temperature,
    ),
    ForecaSensorDescription(
        key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        value_fn=lambda data: data.current.rel_humidity,
    ),
    ForecaSensorDescription(
        key="pressure",
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.HPA,
        value_fn=lambda data: data.current.pressure,
    ),
    ForecaSensorDescription(
        key="wind_speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        value_fn=lambda data: data.current.wind_speed,
    ),
    ForecaSensorDescription(
        key="uv_index",
        translation_key="uv_index",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UV_INDEX,
        value_fn=lambda data: data.current.uv_index,
    ),
    ForecaSensorDescription(
        key="apparent_temperature",
        translation_key="apparent_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.feels_like_temp,
    ),
    ForecaSensorDescription(
        key="dew_point",
        translation_key="dew_point",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.dew_point,
    ),
    ForecaSensorDescription(
        key="wind_gust_speed",
        translation_key="wind_gust_speed",
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.wind_gust,
    ),
    ForecaSensorDescription(
        key="wind_bearing",
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
        native_unit_of_measurement=DEGREE,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.wind_dir,
    ),
    ForecaSensorDescription(
        key="precipitation_intensity",
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.precip_rate,
    ),
    ForecaSensorDescription(
        key="precipitation_probability",
        translation_key="precipitation_probability",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.precip_prob,
    ),
    ForecaSensorDescription(
        key="thunder_probability",
        translation_key="thunder_probability",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.thunder_prob,
    ),
    ForecaSensorDescription(
        key="cloud_coverage",
        translation_key="cloud_coverage",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.cloudiness,
    ),
    ForecaSensorDescription(
        key="visibility",
        translation_key="visibility",
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.KILOMETERS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.visibility,
    ),
    ForecaSensorDescription(
        key="condition",
        translation_key="condition",
        device_class=SensorDeviceClass.ENUM,
        options=CONDITIONS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: symbol_to_condition(data.current.symbol),
    ),
    ForecaSensorDescription(
        key="description",
        translation_key="description",
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.current.symbol_phrase,
    ),
    ForecaSensorDescription(
        key="temperature_high_today",
        translation_key="temperature_high_today",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _today(data, lambda today: today.max_temp),
    ),
    ForecaSensorDescription(
        key="temperature_low_today",
        translation_key="temperature_low_today",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _today(data, lambda today: today.min_temp),
    ),
    ForecaSensorDescription(
        key="precipitation_today",
        translation_key="precipitation_today",
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _today(data, lambda today: today.precip_accum),
    ),
    ForecaSensorDescription(
        key="air_quality_index",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _air_quality(data, lambda aq: aq.aqi),
    ),
    ForecaSensorDescription(
        key="main_pollutant",
        translation_key="main_pollutant",
        device_class=SensorDeviceClass.ENUM,
        options=list(POLLUTANTS.values()),
        entity_registry_enabled_default=False,
        value_fn=lambda data: _air_quality(
            data, lambda aq: pollutant_key(aq.pollutant)
        ),
    ),
    ForecaSensorDescription(
        key="carbon_monoxide_aqi",
        translation_key="carbon_monoxide_aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _air_quality(data, lambda aq: aq.aqi_co),
    ),
    ForecaSensorDescription(
        key="nitrogen_dioxide_aqi",
        translation_key="nitrogen_dioxide_aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _air_quality(data, lambda aq: aq.aqi_no2),
    ),
    ForecaSensorDescription(
        key="ozone_aqi",
        translation_key="ozone_aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _air_quality(data, lambda aq: aq.aqi_o3),
    ),
    ForecaSensorDescription(
        key="sulphur_dioxide_aqi",
        translation_key="sulphur_dioxide_aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _air_quality(data, lambda aq: aq.aqi_so2),
    ),
    ForecaSensorDescription(
        key="pm10_aqi",
        translation_key="pm10_aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _air_quality(data, lambda aq: aq.aqi_pm10),
    ),
    ForecaSensorDescription(
        key="pm25_aqi",
        translation_key="pm25_aqi",
        device_class=SensorDeviceClass.AQI,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda data: _air_quality(data, lambda aq: aq.aqi_pm2p5),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ForecaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add one sensor per description."""
    coordinator = entry.runtime_data
    async_add_entities(ForecaSensor(coordinator, desc) for desc in SENSORS)


class ForecaSensor(ForecaEntity, SensorEntity):
    """One value from the entry's latest refresh."""

    entity_description: ForecaSensorDescription

    def __init__(
        self, coordinator: ForecaCoordinator, description: ForecaSensorDescription
    ) -> None:
        """Bind the sensor to its description."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    @override
    def native_value(self) -> StateType:
        """Return the value the description reads from the latest refresh."""
        return self.entity_description.value_fn(self.coordinator.data)
