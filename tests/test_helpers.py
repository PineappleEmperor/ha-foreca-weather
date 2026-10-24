"""Tests for the symbol-to-condition map."""

import pytest

from custom_components.foreca_weather.helpers import CONDITIONS, symbol_to_condition


@pytest.mark.parametrize(
    ("code", "condition"),
    [
        # Foreca's own examples.
        pytest.param("d000", "sunny", id="d000"),
        pytest.param("d421", "snowy-rainy", id="d421"),
        pytest.param("n210", "rainy", id="n210"),
        # One per row of the map, in the order it is read.
        pytest.param("d240", "lightning-rainy", id="thunder"),
        pytest.param("d342", "lightning-rainy", id="thunder-before-snow"),
        pytest.param("d212", "snowy", id="snow"),
        pytest.param("n331", "snowy-rainy", id="sleet"),
        pytest.param("d430", "pouring", id="continuous-overcast"),
        pytest.param("d330", "rainy", id="continuous-broken"),
        pytest.param("d110", "rainy", id="slight"),
        pytest.param("d600", "fog", id="fog"),
        pytest.param("n100", "clear-night", id="almost-clear-night"),
        pytest.param("d100", "sunny", id="almost-clear-day"),
        pytest.param("d200", "partlycloudy", id="half-cloudy"),
        pytest.param("n300", "partlycloudy", id="broken"),
        pytest.param("d500", "partlycloudy", id="thin-high"),
        pytest.param("d400", "cloudy", id="overcast"),
    ],
)
def test_symbol_to_condition(code: str, condition: str) -> None:
    """Each documented symbol maps to its condition, which the sensor offers."""
    assert symbol_to_condition(code) == condition
    assert condition in CONDITIONS


@pytest.mark.parametrize(
    "code",
    [
        pytest.param(None, id="missing"),
        pytest.param("", id="empty"),
        pytest.param("x000", id="bad-prefix"),
        pytest.param("d0000", id="too-long"),
        pytest.param("d700", id="unknown-cloudiness"),
    ],
)
def test_symbol_without_condition(code: str | None) -> None:
    """A code Foreca's legend does not cover maps to no condition."""
    assert symbol_to_condition(code) is None
