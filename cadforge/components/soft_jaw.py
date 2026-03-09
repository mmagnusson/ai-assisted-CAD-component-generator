"""CNC vise soft jaw component."""

import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class SoftJaw(Component):
    """CNC vise soft jaw with step cut, mounting holes, and optional serrations.

    A rectangular block with a step cut on the top face (the workpiece
    sits against the step). Two through-holes for bolting to the vise.
    Optional serration grooves on the gripping face for improved hold.
    """

    name: str = "soft_jaw"
    jaw_width: float = 150.0
    jaw_height: float = 25.0
    jaw_depth: float = 40.0
    step_depth: float = 10.0
    step_height: float = 12.0
    serration_pitch: float = 0.0
    serration_depth: float = 0.0
    mounting_hole_diameter: float = 8.0
    mounting_hole_spacing: float = 100.0

    def build(self) -> cq.Workplane:
        # Main rectangular block centered on XY
        result = (
            cq.Workplane("XY")
            .box(self.jaw_width, self.jaw_depth, self.jaw_height)
        )

        # Step cut: remove material from the top-front of the jaw.
        # The step creates an L-shaped profile when viewed from the side.
        # Cut from the front face (+Y side), top portion.
        step_cut = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(
                0,
                (self.jaw_depth - self.step_depth) / 2,
                (self.jaw_height - self.step_height) / 2,
            ))
            .box(self.jaw_width + 1, self.step_depth + 1, self.step_height + 0.01)
        )
        result = result.cut(step_cut)

        # Mounting holes: two holes along X axis, centered in Y and Z,
        # drilled through the depth of the jaw (Y direction).
        half_spacing = self.mounting_hole_spacing / 2.0
        hole_positions = [
            (-half_spacing, 0),
            (half_spacing, 0),
        ]
        result = (
            result
            .faces("<Y")
            .workplane()
            .pushPoints(hole_positions)
            .hole(self.mounting_hole_diameter, self.jaw_depth)
        )

        # Optional serrations: parallel grooves on the gripping face (+Y, above step)
        if self.serration_pitch > 0 and self.serration_depth > 0:
            grip_height = self.jaw_height - self.step_height
            num_serrations = int(self.jaw_width / self.serration_pitch)
            if num_serrations > 0:
                groove_width = self.serration_pitch * 0.5
                serration_points = []
                start_x = -(num_serrations - 1) * self.serration_pitch / 2.0
                for i in range(num_serrations):
                    x = start_x + i * self.serration_pitch
                    serration_points.append((x, 0))

                # Cut grooves on the front face (the gripping face after step)
                grooves = (
                    cq.Workplane("XY")
                    .transformed(offset=cq.Vector(
                        0,
                        self.jaw_depth / 2,
                        -self.step_height / 2,
                    ))
                    .pushPoints(serration_points)
                    .box(groove_width, self.serration_depth * 2, grip_height)
                )
                result = result.cut(grooves)

        return result
