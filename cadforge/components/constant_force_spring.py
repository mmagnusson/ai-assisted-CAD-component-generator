"""Constant force spring component."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class ConstantForceSpring(Component):
    """Motor-style constant force spring (flat coiled strip).

    A tightly coiled flat strip that unrolls to provide constant force.
    The coiled portion is modeled as a hollow cylinder and the extended
    portion as a flat rectangular strip extending tangentially from the coil.
    """

    name: str = "constant_force_spring"
    strip_width: float = 15.0
    strip_thickness: float = 0.3
    natural_radius: float = 15.0
    num_coils: float = 5.0
    extended_length: float = 50.0
    spool_id: float = 0.0  # 0 = auto: 2 * natural_radius

    def build(self) -> cq.Workplane:
        # Resolve auto parameters
        spool_id = self.spool_id if self.spool_id > 0 else 2.0 * self.natural_radius

        # Coil dimensions
        coil_id = spool_id - self.strip_thickness
        coil_od = spool_id + 2.0 * self.num_coils * self.strip_thickness
        coil_height = self.strip_width

        # Build the coil as a hollow cylinder
        coil = (
            cq.Workplane("XY")
            .circle(coil_od / 2.0)
            .circle(coil_id / 2.0)
            .extrude(coil_height)
        )

        # Center the coil vertically
        coil = coil.translate((0, 0, -coil_height / 2.0))

        # Build the extended flat strip, extending tangentially from the coil OD
        # Strip starts at the rightmost point of the coil OD and extends in +X
        strip = (
            cq.Workplane("XY")
            .box(self.extended_length, self.strip_thickness, self.strip_width)
        )

        # Position the strip tangentially: its left edge at the coil OD
        strip_x = coil_od / 2.0 + self.extended_length / 2.0
        strip = strip.translate((strip_x, 0, 0))

        # Union coil and strip
        result = coil.union(strip)

        return result
