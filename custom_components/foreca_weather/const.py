"""Constants for the Foreca Weather integration."""

from datetime import timedelta
from typing import Final

DOMAIN: Final = "foreca_weather"

ATTRIBUTION: Final = "Weather data provided by Foreca"
MANUFACTURER: Final = "Foreca"
CONFIGURATION_URL: Final = "https://www.foreca.com"

# Four requests per refresh: 576 a day against the free plan's 2,000.
UPDATE_INTERVAL: Final = timedelta(minutes=10)

HOURLY_PERIODS: Final = 24
DAILY_PERIODS: Final = 7
# The nearest hour of the air-quality forecast stands for the current reading.
AIR_QUALITY_PERIODS: Final = 1
