"""Fit system for CAD Forge.

Automatically propagates dimensional relationships between mated
components in an assembly.  When a shaft connects to a bore, the
bore diameter can be derived from the shaft diameter plus an
appropriate clearance.

Fit types follow ISO 286 conventions:

- **clearance**: bore > shaft (parts slide freely)
- **transition**: bore ≈ shaft (light press or sliding, depends on tolerance)
- **interference**: bore < shaft (press fit, force-assembled)
- **exact**: bore = shaft (same nominal dimension)

Usage::

    assy = Assembly(name="example")
    assy.add_part(ShaftCoupler(bore_1=8.0), name="coupler")
    assy.add_part(FlangedBearingMount(), name="mount")
    assy.add_constraint("coupler", "bore_2_entry", "mount", "bottom")

    assy.add_fit(FitSpec(
        source_part="coupler",
        source_param="bore_2",
        target_part="mount",
        target_param="bore_diameter",
        fit_type="clearance",
    ))
    # mount.bore_diameter will be set to coupler.bore_2 + clearance
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FitSpec:
    """Defines a dimensional relationship between two part parameters.

    The *source* parameter drives the *target* parameter.  The target
    is adjusted based on ``fit_type`` and ``allowance``.

    Attributes:
        source_part:  Name of the driving part in the assembly.
        source_param: Attribute name on the source component.
        target_part:  Name of the driven part in the assembly.
        target_param: Attribute name on the target component.
        fit_type:     One of "clearance", "transition", "interference",
                      or "exact".
        allowance:    Explicit allowance override in mm.  If 0.0 (default),
                      a standard allowance is computed from the fit type
                      and the nominal dimension.
    """

    source_part: str
    source_param: str
    target_part: str
    target_param: str
    fit_type: str = "clearance"
    allowance: float = 0.0


def default_allowance(fit_type: str, nominal: float) -> float:
    """Return a reasonable default allowance for a fit type.

    Based on simplified ISO 286 tolerances for general-purpose
    machining.  Values are one-sided (added to or subtracted from
    nominal).

    Args:
        fit_type: "clearance", "transition", "interference", or "exact".
        nominal: The driving dimension in mm.

    Returns:
        Signed allowance in mm (positive = bore larger than shaft).
    """
    if fit_type == "exact":
        return 0.0

    # Simple tiered allowances based on nominal size.
    # These approximate H7/g6 (clearance), H7/k6 (transition),
    # H7/p6 (interference) for general machining.
    if nominal <= 6:
        base = 0.012
    elif nominal <= 18:
        base = 0.018
    elif nominal <= 30:
        base = 0.021
    elif nominal <= 50:
        base = 0.025
    elif nominal <= 80:
        base = 0.030
    elif nominal <= 120:
        base = 0.035
    else:
        base = 0.040

    if fit_type == "clearance":
        return base
    elif fit_type == "transition":
        return base * 0.25  # tight, may be slight clearance or interference
    elif fit_type == "interference":
        return -base * 0.8  # negative = bore smaller than shaft
    else:
        return 0.0


def compute_driven_value(
    source_value: float,
    fit_type: str,
    allowance: float = 0.0,
) -> float:
    """Compute the target parameter value from the source value and fit.

    Args:
        source_value: The driving dimension (e.g., shaft diameter).
        fit_type: Fit type string.
        allowance: Explicit allowance.  If 0.0, uses default_allowance().

    Returns:
        The adjusted target dimension.
    """
    if allowance != 0.0:
        return source_value + allowance

    auto_allowance = default_allowance(fit_type, source_value)
    return source_value + auto_allowance


class FitResolver:
    """Resolves fit specifications across an assembly.

    Given an assembly with fit specs, computes the adjusted parameter
    values and applies them to the target components.
    """

    @staticmethod
    def resolve(
        fits: list[FitSpec],
        parts: dict[str, Any],
    ) -> dict[str, dict[str, float]]:
        """Compute adjusted parameters without modifying components.

        Args:
            fits: List of FitSpec definitions.
            parts: Dict mapping part name to component instance.

        Returns:
            Dict mapping ``{part_name: {param_name: new_value}}``.

        Raises:
            ValueError: If a referenced part or parameter doesn't exist.
        """
        adjustments: dict[str, dict[str, float]] = {}

        for fit in fits:
            # Validate source
            if fit.source_part not in parts:
                raise ValueError(
                    f"Fit source part '{fit.source_part}' not found"
                )
            source_comp = parts[fit.source_part]
            if not hasattr(source_comp, fit.source_param):
                raise ValueError(
                    f"Parameter '{fit.source_param}' not found on "
                    f"'{fit.source_part}' ({type(source_comp).__name__})"
                )

            # Validate target
            if fit.target_part not in parts:
                raise ValueError(
                    f"Fit target part '{fit.target_part}' not found"
                )
            target_comp = parts[fit.target_part]
            if not hasattr(target_comp, fit.target_param):
                raise ValueError(
                    f"Parameter '{fit.target_param}' not found on "
                    f"'{fit.target_part}' ({type(target_comp).__name__})"
                )

            source_value = getattr(source_comp, fit.source_param)
            new_value = compute_driven_value(
                source_value, fit.fit_type, fit.allowance
            )

            if fit.target_part not in adjustments:
                adjustments[fit.target_part] = {}
            adjustments[fit.target_part][fit.target_param] = new_value

        return adjustments

    @staticmethod
    def apply(
        adjustments: dict[str, dict[str, float]],
        parts: dict[str, Any],
    ) -> None:
        """Apply resolved adjustments to component instances.

        Modifies components in-place and invalidates their build cache.
        """
        for part_name, param_updates in adjustments.items():
            comp = parts[part_name]
            for param, value in param_updates.items():
                setattr(comp, param, value)
            # Invalidate the component's build cache
            comp._workplane = None
