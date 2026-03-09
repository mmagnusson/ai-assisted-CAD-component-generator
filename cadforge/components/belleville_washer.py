"""Belleville washer (disc spring) component."""

import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class BellevilleWasher(Component):
    """Belleville washer (conical disc spring) per DIN 2093.

    Built as a solid of revolution from a trapezoidal cross-section.
    The inner edge is higher than the outer edge by cone_height,
    with material_thickness defining the wall thickness.
    """

    name: str = "belleville_washer"
    outer_diameter: float = 20.0
    inner_diameter: float = 10.0
    thickness: float = 1.0
    cone_height: float = 0.5
    material_thickness: float = 0.3

    def build(self) -> cq.Workplane:
        outer_r = self.outer_diameter / 2.0
        inner_r = self.inner_diameter / 2.0

        # The cross-section is a trapezoid in the RZ plane (for revolution).
        # Inner edge is elevated by cone_height relative to outer edge.
        # material_thickness is the thickness of the conical wall.
        #
        # Profile points (in XZ plane, X = radial distance from axis):
        #   Bottom-outer: (outer_r, 0)
        #   Top-outer:    (outer_r, material_thickness)
        #   Top-inner:    (inner_r, cone_height + material_thickness)
        #   Bottom-inner: (inner_r, cone_height)
        #
        # We draw this as a closed polyline and revolve it.

        p1 = (outer_r, 0.0)
        p2 = (outer_r, self.material_thickness)
        p3 = (inner_r, self.cone_height + self.material_thickness)
        p4 = (inner_r, self.cone_height)

        # Build the cross-section on the XZ plane and revolve around Z axis.
        result = (
            cq.Workplane("XZ")
            .moveTo(*p1)
            .lineTo(*p2)
            .lineTo(*p3)
            .lineTo(*p4)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )

        return result
