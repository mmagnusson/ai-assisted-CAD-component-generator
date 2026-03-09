"""Base Component class for CAD Forge."""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import cadquery as cq
from cadquery import exporters


@dataclass
class Component:
    """Base class for all CAD Forge components.

    Subclasses should override ``build()`` and add their own
    parameter fields as dataclass attributes.
    """

    name: str = "component"

    # Cached build result (not a dataclass field)
    _workplane: cq.Workplane | None = None

    def __post_init__(self) -> None:
        self._workplane = None

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def build(self) -> cq.Workplane:
        """Build and return the CadQuery Workplane for this component.

        Subclasses **must** override this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement build()"
        )

    def _get_workplane(self) -> cq.Workplane:
        """Return the cached workplane, building it if necessary."""
        if self._workplane is None:
            self._workplane = self.build()
        return self._workplane

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def export_step(self, path: str | Path) -> Path:
        """Export the component to a STEP file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wp = self._get_workplane()
        exporters.export(wp, str(path), exporters.ExportTypes.STEP)
        return path

    def export_stl(self, path: str | Path) -> Path:
        """Export the component to an STL file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wp = self._get_workplane()
        exporters.export(wp, str(path), exporters.ExportTypes.STL)
        return path

    def export_svg(self, path: str | Path) -> Path:
        """Export a 2D projection of the component to an SVG file."""
        from .renderers.svg_renderer import render_svg

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        wp = self._get_workplane()
        render_svg(wp, path)
        return path

    # ------------------------------------------------------------------
    # Validation & introspection
    # ------------------------------------------------------------------

    def validate(self) -> list[Any]:
        """Run geometry and manufacturing validation checks.

        Returns a list of ``ValidationResult`` namedtuples.
        """
        from .validators.geometry import GeometryValidator
        from .validators.manufacturing import ManufacturingValidator

        wp = self._get_workplane()
        solid = wp.val()

        results: list[Any] = []
        results.extend(GeometryValidator.check_valid(solid))
        results.extend(GeometryValidator.check_watertight(solid))

        bbox = self.bounding_box()
        results.extend(
            GeometryValidator.check_bounding_box(solid, expected=bbox)
        )

        results.extend(ManufacturingValidator.check_min_wall_thickness(solid))
        results.extend(ManufacturingValidator.check_min_radius(solid))
        results.extend(ManufacturingValidator.check_aspect_ratio(solid))

        return results

    def bounding_box(self) -> tuple[float, float, float]:
        """Return ``(xlen, ylen, zlen)`` of the component bounding box."""
        wp = self._get_workplane()
        bb = wp.val().BoundingBox()
        return (bb.xlen, bb.ylen, bb.zlen)

    def metadata(self) -> dict[str, Any]:
        """Return a metadata dict with component name, params, and bbox."""
        params: dict[str, Any] = {}
        for f in fields(self):
            if f.name.startswith("_"):
                continue
            params[f.name] = getattr(self, f.name)

        bbox = self.bounding_box()

        return {
            "component": type(self).__name__,
            "name": self.name,
            "params": params,
            "bounding_box": {
                "x": bbox[0],
                "y": bbox[1],
                "z": bbox[2],
            },
        }
