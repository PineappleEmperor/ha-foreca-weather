"""Tests that every translation and icon key the code uses exists."""

import json
from pathlib import Path
import re

import pytest

from custom_components.foreca_weather.sensor import SENSORS, ForecaSensorDescription

PACKAGE = Path(__file__).parent.parent / "custom_components" / "foreca_weather"
STRINGS = json.loads((PACKAGE / "translations" / "en.json").read_text())
ICONS = json.loads((PACKAGE / "icons.json").read_text())
EXCEPTION_KEYS = sorted(
    set(
        re.findall(
            r'translation_key="([a-z_]+)"',
            (PACKAGE / "coordinator.py").read_text(),
        )
    )
)
TRANSLATED = [desc for desc in SENSORS if desc.translation_key is not None]
WITHOUT_DEVICE_CLASS = [desc for desc in SENSORS if desc.device_class is None]


@pytest.mark.parametrize("key", EXCEPTION_KEYS)
def test_exception_translated(key: str) -> None:
    """Every exception the coordinator raises has its message."""
    assert STRINGS["exceptions"][key]["message"]


@pytest.mark.parametrize("desc", TRANSLATED, ids=lambda desc: desc.key)
def test_sensor_name_translated(desc: ForecaSensorDescription) -> None:
    """Every sensor translation key has a name."""
    assert STRINGS["entity"]["sensor"][desc.translation_key]["name"]


@pytest.mark.parametrize("desc", WITHOUT_DEVICE_CLASS, ids=lambda desc: desc.key)
def test_sensor_icon(desc: ForecaSensorDescription) -> None:
    """Every sensor without a device class to give it an icon has one of its own."""
    assert ICONS["entity"]["sensor"][desc.translation_key]["default"]
