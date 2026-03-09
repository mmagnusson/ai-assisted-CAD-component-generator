"""Manufacturing-oriented validation checks for CAD Forge.

These are currently stubs.  Full implementations would require mesh
analysis or ray-casting against the solid geometry.
"""

from __future__ import annotations

from typing import Any

from .geometry import ValidationResult


class ManufacturingValidator:
    """Collection of manufacturing-oriented validation checks."""

    @staticmethod
    def check_min_wall_thickness(
        solid: Any,
        min_thickness: float = 0.5,
    ) -> list[ValidationResult]:
        """Check that the thinnest wall is at least *min_thickness* mm.

        .. note:: Stub implementation -- always passes.
        """
        return [
            ValidationResult(
                passed=True,
                check="min_wall_thickness",
                message=(
                    f"Wall thickness check passed (stub, min={min_thickness} mm)"
                ),
            )
        ]

    @staticmethod
    def check_min_radius(
        solid: Any,
        min_radius: float = 0.5,
    ) -> list[ValidationResult]:
        """Check that the smallest fillet / edge radius is at least *min_radius* mm.

        .. note:: Stub implementation -- always passes.
        """
        return [
            ValidationResult(
                passed=True,
                check="min_radius",
                message=(
                    f"Minimum radius check passed (stub, min={min_radius} mm)"
                ),
            )
        ]

    @staticmethod
    def check_aspect_ratio(
        solid: Any,
        max_ratio: float = 10.0,
    ) -> list[ValidationResult]:
        """Check that the bounding-box aspect ratio does not exceed *max_ratio*.

        Computes ``max(dim) / min(dim)`` where ``dim`` are the three
        bounding-box edge lengths.
        """
        if solid is None:
            return [
                ValidationResult(
                    passed=False,
                    check="aspect_ratio",
                    message="Solid is None, cannot check aspect ratio",
                )
            ]

        try:
            bb = solid.BoundingBox()
            dims = sorted([bb.xlen, bb.ylen, bb.zlen])
        except Exception as exc:
            return [
                ValidationResult(
                    passed=False,
                    check="aspect_ratio",
                    message=f"Could not compute bounding box: {exc}",
                )
            ]

        min_dim = dims[0]
        max_dim = dims[2]

        if min_dim <= 0:
            return [
                ValidationResult(
                    passed=False,
                    check="aspect_ratio",
                    message="Minimum bounding-box dimension is zero or negative",
                )
            ]

        ratio = max_dim / min_dim

        if ratio <= max_ratio:
            return [
                ValidationResult(
                    passed=True,
                    check="aspect_ratio",
                    message=f"Aspect ratio {ratio:.2f} within limit {max_ratio}",
                )
            ]
        else:
            return [
                ValidationResult(
                    passed=False,
                    check="aspect_ratio",
                    message=f"Aspect ratio {ratio:.2f} exceeds limit {max_ratio}",
                )
            ]
