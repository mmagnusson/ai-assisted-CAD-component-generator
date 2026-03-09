"""Gas spring (gas strut) component."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class GasSpring(Component):
    """Gas strut / gas spring, like those used on car hatchbacks.

    Consists of a cylinder body, piston rod, and end eyes (clevis mounts)
    on both ends for pivoting attachment.
    """

    name: str = "gas_spring"
    bore_diameter: float = 20.0
    rod_diameter: float = 8.0
    stroke: float = 100.0
    extended_length: float = 0.0  # 0 = auto: stroke * 2 + 50
    body_wall: float = 2.0
    end_eye_id: float = 8.0
    end_eye_od: float = 16.0
    end_eye_thickness: float = 6.0

    def build(self) -> cq.Workplane:
        # Resolve auto parameters
        ext_len = self.extended_length if self.extended_length > 0 else self.stroke * 2.0 + 50.0

        body_od = self.bore_diameter + 2.0 * self.body_wall
        body_length = ext_len - self.stroke
        rod_length = self.stroke + 20.0  # 20mm overlap inside cylinder
        rod_exposed = self.stroke

        # Cylinder body - hollow tube along Z axis
        body = (
            cq.Workplane("XY")
            .circle(body_od / 2.0)
            .circle(self.bore_diameter / 2.0)
            .extrude(body_length)
        )

        # Cap the bottom of the cylinder body
        body_cap = (
            cq.Workplane("XY")
            .circle(body_od / 2.0)
            .extrude(self.body_wall)
        )
        body = body.union(body_cap)

        # Piston rod - solid cylinder extending from the top of the body
        rod = (
            cq.Workplane("XY")
            .circle(self.rod_diameter / 2.0)
            .extrude(rod_exposed)
            .translate((0, 0, body_length))
        )

        # End eye (body end) - flat plate with rounded top and mounting hole
        # Positioned at Z=0 (bottom of body)
        eye_height = self.end_eye_od * 1.5
        body_eye = (
            cq.Workplane("XZ")
            .moveTo(0, 0)
            .rect(self.end_eye_thickness, eye_height)
            .extrude(self.end_eye_od / 2.0)
            .translate((0, 0, 0))
        )

        # Create the body-end eye as a rounded plate with a hole
        body_eye = (
            cq.Workplane("XZ")
            .moveTo(0, eye_height / 2.0)
            .rect(self.end_eye_thickness, eye_height)
            .extrude(self.end_eye_od / 2.0)
            .mirror("XZ", basePointVector=(0, 0, 0), union=True)
        )
        # Drill the eye hole
        body_eye = (
            body_eye
            .faces(">Y")
            .workplane()
            .hole(self.end_eye_id)
        )
        # Position at the bottom
        body_eye = body_eye.translate((0, 0, -eye_height / 2.0))

        # End eye (rod end) - same style at the tip of the rod
        rod_eye = (
            cq.Workplane("XZ")
            .moveTo(0, eye_height / 2.0)
            .rect(self.end_eye_thickness, eye_height)
            .extrude(self.end_eye_od / 2.0)
            .mirror("XZ", basePointVector=(0, 0, 0), union=True)
        )
        rod_eye = (
            rod_eye
            .faces(">Y")
            .workplane()
            .hole(self.end_eye_id)
        )
        # Position at the tip of the rod
        rod_eye = rod_eye.translate((0, 0, body_length + rod_exposed + eye_height / 2.0))

        # Union all parts
        result = body.union(rod).union(body_eye).union(rod_eye)

        return result
