import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component, MatePoint


@dataclass
class LBracket(Component):
    """An L-shaped mounting bracket with filleted corner and mounting holes."""

    name: str = "l_bracket"
    width: float = 50.0
    height: float = 30.0
    thickness: float = 5.0
    hole_diameter: float = 6.0
    fillet_radius: float = 2.0
    hole_count: int = 2

    def build(self) -> cq.Workplane:
        # Horizontal leg: extends along +X, depth along Y, thin in Z
        horizontal = (
            cq.Workplane("XY")
            .box(self.width, self.width, self.thickness, centered=False)
        )

        # Vertical leg: extends along +Z from the back edge, thin in X
        vertical = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, 0))
            .box(self.thickness, self.width, self.height, centered=False)
        )

        # Union the two legs
        result = horizontal.union(vertical)

        # Fillet the inside corner edge where the two legs meet.
        # The inside corner runs along Y at (x=thickness, y=*, z=thickness).
        result = (
            result
            .edges("|Y")
            .edges(
                cq.selectors.NearestToPointSelector(
                    (self.thickness, self.width / 2, self.thickness)
                )
            )
            .fillet(self.fillet_radius)
        )

        # Mounting holes on the horizontal leg (through Z, on the top face).
        # Evenly spaced along X starting from an offset.
        margin = self.width / (self.hole_count + 1)
        hole_positions_h = [
            (margin + i * margin, self.width / 2)
            for i in range(self.hole_count)
        ]
        # Holes start from the top face of the horizontal leg at z=thickness,
        # drilled through the thickness.
        result = (
            result
            .faces(">Z[-2]")
            .workplane()
            .pushPoints(hole_positions_h)
            .hole(self.hole_diameter, self.thickness)
        )

        # Mounting holes on the vertical leg (through X, on the outer face).
        # Evenly spaced along Z on the vertical leg.
        leg_start_z = self.thickness
        leg_height = self.height - self.thickness
        z_margin = leg_height / (self.hole_count + 1)
        hole_positions_v = [
            (self.width / 2, leg_start_z + z_margin + i * z_margin)
            for i in range(self.hole_count)
        ]
        result = (
            result
            .faces("<X")
            .workplane()
            .pushPoints(hole_positions_v)
            .hole(self.hole_diameter, self.thickness)
        )

        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="horizontal_face",
                origin=(self.width / 2, self.width / 2, self.thickness),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="horizontal_bottom",
                origin=(self.width / 2, self.width / 2, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="vertical_face",
                origin=(self.thickness, self.width / 2, self.height / 2),
                normal=(-1.0, 0.0, 0.0),
                mate_type="face",
            ),
        ]
