import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component, MatePoint


@dataclass
class Standoff(Component):
    """A PCB mounting standoff with hex or round body and configurable gender."""

    name: str = "standoff"
    height: float = 10.0
    thread_diameter: float = 3.0
    base_diameter: float = 6.0
    head_diameter: float = 6.0
    hex_across_flats: float = 5.5
    body_style: str = "hex"
    gender: str = "male_female"
    thread_length: float = 5.0

    def build(self) -> cq.Workplane:
        # Build the main body
        if self.body_style == "hex":
            # Regular hexagon inscribed in a circle.
            # hex_across_flats is the distance between parallel flats,
            # which equals the inscribed circle diameter.
            result = (
                cq.Workplane("XY")
                .polygon(6, self.hex_across_flats / math.cos(math.pi / 6))
                .extrude(self.height)
            )
        else:
            # Round body
            result = (
                cq.Workplane("XY")
                .circle(self.base_diameter / 2)
                .extrude(self.height)
            )

        # Determine which ends get a male stud vs female hole.
        # bottom = Z=0 side, top = Z=height side.
        if self.gender == "male_female":
            bottom_male = True
            top_male = False
        elif self.gender == "male_male":
            bottom_male = True
            top_male = True
        elif self.gender == "female_female":
            bottom_male = False
            top_male = False
        else:
            bottom_male = True
            top_male = False

        # Top end
        if top_male:
            # Add a threaded stud (cylinder) extending above the body
            stud_top = (
                cq.Workplane("XY")
                .transformed(offset=cq.Vector(0, 0, self.height))
                .circle(self.thread_diameter / 2)
                .extrude(self.thread_length)
            )
            result = result.union(stud_top)
        else:
            # Female: drill a tapped hole from the top
            result = (
                result
                .faces(">Z")
                .workplane()
                .hole(self.thread_diameter, self.thread_length)
            )

        # Bottom end
        if bottom_male:
            # Add a threaded stud (cylinder) extending below the body
            stud_bottom = (
                cq.Workplane("XY")
                .circle(self.thread_diameter / 2)
                .extrude(-self.thread_length)
            )
            result = result.union(stud_bottom)
        else:
            # Female: drill a tapped hole from the bottom
            result = (
                result
                .faces("<Z")
                .workplane()
                .hole(self.thread_diameter, self.thread_length)
            )

        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="bottom",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="top",
                origin=(0.0, 0.0, self.height),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="center_axis",
                origin=(0.0, 0.0, self.height / 2),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
        ]
