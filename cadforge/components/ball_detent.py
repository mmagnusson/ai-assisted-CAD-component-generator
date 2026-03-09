"""Ball detent / spring-loaded ball plunger component."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class BallDetent(Component):
    """Spring-loaded ball detent plunger.

    A cylindrical body with a ball sitting in a conical seat at the top,
    a spring bore below the seat, and a hex socket recess at the bottom
    for installation.
    """

    name: str = "ball_detent"
    body_diameter: float = 8.0
    body_length: float = 16.0
    body_thread_od: float = 8.0
    thread_length: float = 10.0
    ball_diameter: float = 4.0
    nose_diameter: float = 5.0
    spring_bore_diameter: float = 4.0
    spring_bore_depth: float = 10.0
    hex_socket_af: float = 4.0
    hex_socket_depth: float = 3.0

    def build(self) -> cq.Workplane:
        # Body: cylindrical, built upward from Z=0
        body = (
            cq.Workplane("XY")
            .circle(self.body_diameter / 2.0)
            .extrude(self.body_length)
        )

        # Nose: slightly reduced diameter at the top for the ball seat area
        # Taper the top to nose_diameter over a short distance
        taper_height = (self.body_diameter - self.nose_diameter) / 2.0 + 1.0
        nose_top_z = self.body_length

        # Create the conical ball seat recess at the top
        # Cone from ball_diameter at top down to spring_bore_diameter
        cone_depth = (self.ball_diameter - self.spring_bore_diameter) / 2.0 + 0.5
        seat_cone = (
            cq.Workplane("XY")
            .workplane(offset=self.body_length)
            .circle(self.ball_diameter / 2.0)
            .workplane(offset=-cone_depth)
            .circle(self.spring_bore_diameter / 2.0)
            .loft()
        )
        body = body.cut(seat_cone)

        # Spring bore: blind hole from below the ball seat going downward
        spring_bore_top_z = self.body_length - cone_depth
        spring_bore = (
            cq.Workplane("XY")
            .workplane(offset=spring_bore_top_z - self.spring_bore_depth)
            .circle(self.spring_bore_diameter / 2.0)
            .extrude(self.spring_bore_depth)
        )
        body = body.cut(spring_bore)

        # Hex socket recess at the bottom
        hex_circumradius = self.hex_socket_af / math.sqrt(3.0)
        hex_socket = (
            cq.Workplane("XY")
            .polygon(6, hex_circumradius * 2.0)
            .extrude(self.hex_socket_depth)
        )
        body = body.cut(hex_socket)

        # Ball: sphere sitting proud of the body top
        # Ball center is at body_length, so half the ball sticks out
        ball_protrusion = self.ball_diameter * 0.3  # ball sits partially recessed
        ball_center_z = self.body_length - self.ball_diameter / 2.0 + ball_protrusion + self.ball_diameter / 2.0
        ball = (
            cq.Workplane("XY")
            .workplane(offset=self.body_length + ball_protrusion)
            .sphere(self.ball_diameter / 2.0)
        )

        result = body.union(ball)

        return result
