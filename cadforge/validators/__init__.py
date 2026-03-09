"""Validation utilities for CAD Forge."""

from __future__ import annotations

from typing import Any

from .geometry import GeometryValidator, ValidationResult
from .manufacturing import ManufacturingValidator


def validate_solid(solid: Any) -> list[ValidationResult]:
    """Run all geometry and manufacturing checks on a solid.

    Parameters
    ----------
    solid:
        A CadQuery ``Shape`` / OCCT solid to validate.

    Returns
    -------
    list[ValidationResult]
        Results for each check that was run.
    """
    results: list[ValidationResult] = []
    results.extend(GeometryValidator.check_valid(solid))
    results.extend(GeometryValidator.check_watertight(solid))
    results.extend(ManufacturingValidator.check_min_wall_thickness(solid))
    results.extend(ManufacturingValidator.check_min_radius(solid))
    results.extend(ManufacturingValidator.check_aspect_ratio(solid))
    return results
