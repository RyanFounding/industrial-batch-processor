from __future__ import annotations

import pytest

from spec_extractor.quality import completeness, plausibility_warnings
from spec_extractor.schemas import CompressorSpecs


def specs(**overrides: object) -> CompressorSpecs:
    base: dict[str, object] = {
        "model_name": "EK40C",
        "max_supported_power_kw": 60.0,
        "aerodynamic_efficiency_percent": 78.0,
        "max_motor_shaft_speed_rpm": 110_000,
        "rated_motor_current_amps": 160.0,
        "weight_kg": 21.0,
        "cooling_medium": "water/glycol",
        "summary": "High power density; requires liquid cooling.",
    }
    return CompressorSpecs.model_validate({**base, **overrides})


def test_complete_datasheet_scores_one() -> None:
    assert completeness(specs()) == 1.0


def test_completeness_counts_missing_fields() -> None:
    partial = specs(rated_motor_current_amps=None, weight_kg=None, cooling_medium=None)

    assert completeness(partial) == 0.5


def test_plausible_values_produce_no_warnings() -> None:
    assert plausibility_warnings(specs()) == []


def test_efficiency_given_as_fraction_is_flagged() -> None:
    [warning] = plausibility_warnings(specs(aerodynamic_efficiency_percent=0.78))

    assert warning.field == "aerodynamic_efficiency_percent"
    assert "fraction" in warning.message


@pytest.mark.parametrize("value", [0.0, 140.0, -5.0])
def test_impossible_efficiency_is_flagged(value: float) -> None:
    [warning] = plausibility_warnings(specs(aerodynamic_efficiency_percent=value))

    assert "outside" in warning.message


@pytest.mark.parametrize(
    "field", ["max_supported_power_kw", "weight_kg", "rated_motor_current_amps"]
)
def test_non_positive_physical_values_are_flagged(field: str) -> None:
    [warning] = plausibility_warnings(specs(**{field: 0}))

    assert warning.field == field
