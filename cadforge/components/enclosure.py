from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class Enclosure(Component):
    """An electronics enclosure box with rounded corners and mounting posts."""

    name: str = "enclosure"
    length: float = 100.0
    width: float = 60.0
    height: float = 40.0
    wall_thickness: float = 2.5
    lid_thickness: float = 2.0
    corner_radius: float = 3.0
    mounting_post_diameter: float = 6.0
    mounting_hole_diameter: float = 3.0

    def build(self) -> cq.Workplane:
        # Outer shell: rounded rectangle extruded to full height
        outer = (
            cq.Workplane("XY")
            .rect(self.length, self.width)
            .extrude(self.height)
        )

        # Apply corner radius to the vertical edges
        if self.corner_radius > 0:
            outer = outer.edges("|Z").fillet(self.corner_radius)

        # Inner cavity: cut from the top, leaving wall_thickness on sides
        # and a solid floor of wall_thickness at the bottom.
        inner_length = self.length - 2 * self.wall_thickness
        inner_width = self.width - 2 * self.wall_thickness
        cavity_depth = self.height - self.wall_thickness

        inner_cut = (
            outer
            .faces(">Z")
            .workplane()
            .rect(inner_length, inner_width)
            .cutBlind(-cavity_depth)
        )

        result = inner_cut

        # Mounting posts at the four interior corners.
        # Posts sit on the floor and rise to the full cavity depth.
        inset = self.wall_thickness + self.mounting_post_diameter / 2
        post_x = self.length / 2 - inset
        post_y = self.width / 2 - inset

        post_positions = [
            (post_x, post_y),
            (-post_x, post_y),
            (-post_x, -post_y),
            (post_x, -post_y),
        ]

        # Add cylindrical posts from the floor up to cavity height
        result = (
            result
            .faces("<Z[1]")  # select the internal floor face
            .workplane()
            .pushPoints(post_positions)
            .circle(self.mounting_post_diameter / 2)
            .extrude(cavity_depth)
        )

        # Drill screw holes through the mounting posts from the top
        result = (
            result
            .faces(">Z")
            .workplane()
            .pushPoints(post_positions)
            .hole(self.mounting_hole_diameter, cavity_depth)
        )

        return result
