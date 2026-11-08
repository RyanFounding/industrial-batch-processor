"""Plausibility and completeness checks on extracted specifications.

Datasheets vary in what they publish, and models occasionally misread units.
These checks make both visible in the comparison table, so an engineer can
see which values to trust and which datasheets to read more closely.
"""

from __future__ import annotations

from pydantic import BaseModel

from spec_extractor.schemas import SPEC_FIELDS, CompressorSpecs


class SpecWarning(BaseModel):
    field: str
    message: str


def completeness(specs: CompressorSpecs) -> float:
    """Share of the comparison fields that the datasheet provided, from 0.0 to 1.0."""
    found = sum(getattr(specs, name) is not None for name in SPEC_FIELDS)
    return round(found / len(SPEC_FIELDS), 2)


def plausibility_warnings(specs: CompressorSpecs) -> list[SpecWarning]:
    warnings: list[SpecWarning] = []

    efficiency = specs.aerodynamic_efficiency_percent
    if efficiency is not None:
        if 0 < efficiency <= 1:
            warnings.append(
                SpecWarning(
                    field="aerodynamic_efficiency_percent",
                    message=f"{efficiency} looks like a fraction; expected a percentage (0-100).",
                )
            )
        elif not 0 < efficiency <= 100:
            warnings.append(
                SpecWarning(
                    field="aerodynamic_efficiency_percent",
                    message=f"{efficiency}% is outside the physically possible range.",
                )
            )

    for name in (
        "max_supported_power_kw",
        "max_motor_shaft_speed_rpm",
        "rated_motor_current_amps",
        "weight_kg",
    ):
        value = getattr(specs, name)
        if value is not None and value <= 0:
            warnings.append(SpecWarning(field=name, message=f"{value} must be greater than zero."))

    return warnings
