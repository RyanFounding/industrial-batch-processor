"""Compressor datasheet schema. Field descriptions are sent to the model as instructions."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CompressorSpecs(BaseModel):
    model_name: str = Field(description="Model name or series of the compressor")
    max_supported_power_kw: float | None = Field(
        default=None,
        description="Maximum motor power in kW. Convert hp to kW (1 hp = 0.7457 kW).",
    )
    aerodynamic_efficiency_percent: float | None = Field(
        default=None,
        description="Maximum efficiency as a percentage between 0 and 100 (78% becomes 78)",
    )
    max_motor_shaft_speed_rpm: int | None = Field(
        default=None, description="Maximum motor shaft speed in RPM"
    )
    rated_motor_current_amps: float | None = Field(
        default=None, description="Rated motor current in amperes"
    )
    weight_kg: float | None = Field(
        default=None, description="Weight in kg. Convert lb to kg (1 lb = 0.4536 kg)."
    )
    cooling_medium: str | None = Field(
        default=None, description="Cooling medium, e.g. air, water, oil or glycol"
    )
    summary: str = Field(
        description="One sentence on the main strengths and limitations stated in the datasheet"
    )


NUMERIC_SPEC_FIELDS: tuple[str, ...] = (
    "max_supported_power_kw",
    "aerodynamic_efficiency_percent",
    "max_motor_shaft_speed_rpm",
    "rated_motor_current_amps",
    "weight_kg",
)

SPEC_FIELDS: tuple[str, ...] = (*NUMERIC_SPEC_FIELDS, "cooling_medium")
