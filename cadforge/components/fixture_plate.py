"""Fixture plate with hole grid and optional dowel pins."""

import math
from dataclasses import dataclass, field
from typing import List, Tuple

import cadquery as cq

from cadforge.core import Component


@dataclass
class FixturePlate(Component):
    """Rectangular fixture plate with a regular grid of through-holes
    and optional dowel pin holes at specified positions.
    """

    name: str = "fixture_plate"
    length: float = 200.0
    width: float = 150.0
    thickness: float = 20.0
    hole_grid_spacing: float = 25.0
    hole_diameter: float = 8.0
    border_margin: float = 15.0
    dowel_hole_diameter: float = 6.0
    dowel_positions: List[Tuple[float, float]] = field(default_factory=list)

    def build(self) -> cq.Workplane:
        # Main rectangular plate
        result = (
            cq.Workplane("XY")
            .box(self.length, self.width, self.thickness)
        )

        # Calculate grid hole positions within the border margin.
        # The plate is centered at the origin.
        x_min = -self.length / 2.0 + self.border_margin
        x_max = self.length / 2.0 - self.border_margin
        y_min = -self.width / 2.0 + self.border_margin
        y_max = self.width / 2.0 - self.border_margin

        grid_points = []
        x = x_min
        while x <= x_max + 1e-9:
            y = y_min
            while y <= y_max + 1e-9:
                grid_points.append((x, y))
                y += self.hole_grid_spacing
            x += self.hole_grid_spacing

        # Drill grid holes through the plate
        if grid_points:
            result = (
                result
                .faces(">Z")
                .workplane()
                .pushPoints(grid_points)
                .hole(self.hole_diameter, self.thickness)
            )

        # Drill dowel pin holes at specified positions
        if self.dowel_positions:
            result = (
                result
                .faces(">Z")
                .workplane()
                .pushPoints(self.dowel_positions)
                .hole(self.dowel_hole_diameter, self.thickness)
            )

        return result
