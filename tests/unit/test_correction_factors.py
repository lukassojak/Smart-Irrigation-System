import pytest
from unittest.mock import MagicMock, patch
from smart_irrigation_system.correction_factors import CorrectionFactors


def test_default_factors_are_zero():
    cf = CorrectionFactors()
    assert cf.get_factor("sunlight") == 0.0
    assert cf.get_factor("rain") == 0.0
    assert cf.get_factor("temperature") == 0.0


def test_custom_initial_factors():
    cf = CorrectionFactors(sunlight=1.0, rain=0.5, temperature=3.8)
    assert cf.get_factor("sunlight") == 1.0
    assert cf.get_factor("rain") == 0.5
    assert cf.get_factor("temperature") == 3.8


def test_set_and_get_valid_factors():
    cf = CorrectionFactors()
    cf.set_factor("sunlight", 2.5)
    assert cf.get_factor("sunlight") == 2.5

    cf.set_factor("rain", 1.1)
    assert cf.get_factor("rain") == 1.1

    cf.set_factor("temperature", 0.3)
    assert cf.get_factor("temperature") == 0.3


def test_set_invalid_parameter_raises():
    cf = CorrectionFactors()
    with pytest.raises(ValueError) as exc_info:
        cf.set_factor("humidity", 0.9)
    assert "Unknown parameter: humidity" in str(exc_info.value)