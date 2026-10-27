"""Pure functions shared by the platforms.

A Foreca symbol code, such as "d421", is day or night, then cloudiness 0-6,
precipitation rate 0-4 and precipitation type 0-2, as Foreca's symbol legend gives
them. The condition map lets precipitation decide before cloud cover does.
"""

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
)
from pyforeca import Symbol

# fmt: off
# Foreca's names for the main pollutant, as its air-quality schema lists them.
POLLUTANTS = {
    "Carbon monoxide":           "carbon_monoxide",
    "Nitrogen dioxide":          "nitrogen_dioxide",
    "Ozone":                     "ozone",
    "Particulate matter <10um":  "pm10",
    "Particulate matter <2.5um": "pm25",
    "Sulphur dioxide":           "sulphur_dioxide",
}
# fmt: on

# Every condition symbol_to_condition can return, for the condition sensor's options.
CONDITIONS = [
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
]


def pollutant_key(name: str | None) -> str | None:
    """Map Foreca's name for the main pollutant to the sensor's state."""
    return POLLUTANTS.get(name) if name is not None else None


def symbol_to_condition(code: str | None) -> str | None:
    """Map a Foreca symbol code to a Home Assistant condition."""
    if code is None or (symbol := Symbol.parse(code)) is None:
        return None
    if symbol.precip_rate == 4:
        return ATTR_CONDITION_LIGHTNING_RAINY
    if symbol.precip_rate >= 1 and symbol.precip_type == 2:
        return ATTR_CONDITION_SNOWY
    if symbol.precip_rate >= 1 and symbol.precip_type == 1:
        return ATTR_CONDITION_SNOWY_RAINY
    if symbol.precip_rate == 3 and symbol.cloudiness == 4:
        return ATTR_CONDITION_POURING
    if symbol.precip_rate >= 1:
        return ATTR_CONDITION_RAINY
    if symbol.cloudiness == 6:
        return ATTR_CONDITION_FOG
    if symbol.cloudiness in (0, 1):
        return ATTR_CONDITION_SUNNY if symbol.is_day else ATTR_CONDITION_CLEAR_NIGHT
    if symbol.cloudiness in (2, 3, 5):
        return ATTR_CONDITION_PARTLYCLOUDY
    if symbol.cloudiness == 4:
        return ATTR_CONDITION_CLOUDY
    return None
