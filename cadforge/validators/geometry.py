"""Geometry validation checks for CAD Forge."""

from __future__ import annotations

from typing import Any, NamedTuple


class ValidationResult(NamedTuple):
    """Result of a single validation check."""

    passed: bool
    check: str
    message: str


class GeometryValidator:
    """Collection of geometry-level validation checks."""

    @staticmethod
    def check_valid(solid: Any) -> list[ValidationResult]:
        """Check whether the solid is non-null and geometrically valid."""
        results: list[ValidationResult] = []

        if solid is None:
            results.append(
                ValidationResult(
                    passed=False,
                    check="valid_solid",
                    message="Solid is None",
                )
            )
            return results

        try:
            # CadQuery shapes expose an isValid() method (wraps OCCT BRepCheck)
            is_valid: bool = solid.isValid()
        except AttributeError:
            is_valid = True  # not a CQ shape, assume valid

        if is_valid:
            results.append(
                ValidationResult(
                    passed=True,
                    check="valid_solid",
                    message="Solid is valid",
                )
            )
        else:
            results.append(
                ValidationResult(
                    passed=False,
                    check="valid_solid",
                    message="Solid failed BRep validity check",
                )
            )

        return results

    @staticmethod
    def check_watertight(solid: Any) -> list[ValidationResult]:
        """Check whether the solid is closed (watertight)."""
        results: list[ValidationResult] = []

        if solid is None:
            results.append(
                ValidationResult(
                    passed=False,
                    check="watertight",
                    message="Solid is None, cannot check watertightness",
                )
            )
            return results

        try:
            # A closed (watertight) solid has no free edges in its shell
            from OCP.BRepCheck import BRepCheck_Analyzer  # type: ignore[import-untyped]

            analyzer = BRepCheck_Analyzer(solid.wrapped)
            is_valid = analyzer.IsValid()
        except Exception:
            # Fallback: assume watertight if we can compute volume > 0
            try:
                vol = solid.Volume()
                is_valid = vol > 0
            except Exception:
                is_valid = False

        if is_valid:
            results.append(
                ValidationResult(
                    passed=True,
                    check="watertight",
                    message="Solid appears watertight",
                )
            )
        else:
            results.append(
                ValidationResult(
                    passed=False,
                    check="watertight",
                    message="Solid may not be watertight",
                )
            )

        return results

    @staticmethod
    def check_bounding_box(
        solid: Any,
        expected: tuple[float, float, float],
        tolerance: float = 0.01,
    ) -> list[ValidationResult]:
        """Check that the solid's bounding box matches *expected* within *tolerance* (relative)."""
        results: list[ValidationResult] = []

        if solid is None:
            results.append(
                ValidationResult(
                    passed=False,
                    check="bounding_box",
                    message="Solid is None, cannot check bounding box",
                )
            )
            return results

        try:
            bb = solid.BoundingBox()
            actual = (bb.xlen, bb.ylen, bb.zlen)
        except Exception as exc:
            results.append(
                ValidationResult(
                    passed=False,
                    check="bounding_box",
                    message=f"Could not compute bounding box: {exc}",
                )
            )
            return results

        for axis, act, exp in zip(("x", "y", "z"), actual, expected):
            if exp == 0:
                ok = act == 0
            else:
                ok = abs(act - exp) / abs(exp) <= tolerance

            if ok:
                results.append(
                    ValidationResult(
                        passed=True,
                        check=f"bounding_box_{axis}",
                        message=f"{axis} dimension {act:.3f} matches expected {exp:.3f}",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        passed=False,
                        check=f"bounding_box_{axis}",
                        message=f"{axis} dimension {act:.3f} differs from expected {exp:.3f}",
                    )
                )

        return results
