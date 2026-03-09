"""ER-style collet (simplified geometry)."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component

# Standard ER collet dimensions: {er_size: (outer_diameter, body_length)}
ER_DIMENSIONS = {
    11: (11.5, 18.0),
    16: (17.0, 22.0),
    20: (21.0, 31.0),
    25: (26.0, 34.0),
    32: (33.0, 40.0),
    40: (41.0, 46.0),
    50: (52.0, 60.0),
}


@dataclass
class Collet(Component):
    """Simplified ER-style collet with tapered outer body, central bore, and radial slots.

    The outer body is a truncated cone (larger at the nose), with the taper_angle
    controlling the half-angle of the collet nose taper. Radial slots are cut from
    the nose end to allow the collet to compress onto the tool shank.
    """

    name: str = "collet"
    er_size: int = 32
    bore_diameter: float = 10.0
    body_length: float = 0.0
    taper_angle: float = 8.0
    num_slots: int = 8
    slot_width: float = 1.0
    slot_depth: float = 0.0

    def _get_dimensions(self) -> tuple[float, float]:
        """Return (outer_diameter, body_length) based on ER size."""
        if self.er_size in ER_DIMENSIONS:
            od, default_length = ER_DIMENSIONS[self.er_size]
        else:
            # Fallback: approximate from er_size
            od = self.er_size + 1.0
            default_length = self.er_size * 1.25

        length = self.body_length if self.body_length > 0 else default_length
        return od, length

    def build(self) -> cq.Workplane:
        od, length = self._get_dimensions()
        outer_radius = od / 2.0
        bore_radius = self.bore_diameter / 2.0

        # The collet has a tapered nose section (~40%) and a straight back section.
        # Larger OD at the nose (top, +Z), smaller at the back (Z=0).
        taper_length = length * 0.4
        straight_length = length - taper_length

        # The taper reduces the radius from outer_radius (nose) down to back_radius
        taper_radius_reduction = taper_length * math.tan(math.radians(self.taper_angle))
        back_radius = outer_radius - taper_radius_reduction
        if back_radius < bore_radius + 1.0:
            back_radius = bore_radius + 1.0

        # Build the full outer body by revolving an axial profile around Z.
        # Profile in XZ plane (X = radius, Z = height), revolved around Z axis.
        # CadQuery revolve on XZ plane: X is radial, Y in the sketch is Z in 3D.
        # We draw the right-side profile and revolve around the Y axis of the sketch.
        profile_pts = [
            (bore_radius, 0),                          # bottom inner
            (back_radius, 0),                          # bottom outer
            (back_radius, straight_length),             # junction outer
            (outer_radius, length),                     # nose outer (tapered)
            (bore_radius, length),                      # nose inner
        ]

        result = (
            cq.Workplane("XZ")
            .polyline(profile_pts)
            .close()
            .revolve(360, (0, 0, 0), (0, 1, 0))
        )

        # Radial slots from the nose end, extending ~60% of body length
        effective_slot_depth = self.slot_depth if self.slot_depth > 0 else length * 0.6
        slot_height = effective_slot_depth
        slot_extent = outer_radius + 1.0  # extend beyond OD to fully cut

        for i in range(self.num_slots):
            angle = i * (360.0 / self.num_slots)
            radial_length = slot_extent - bore_radius + 1.0

            slot_box = (
                cq.Workplane("XY")
                .transformed(
                    offset=cq.Vector(0, 0, length - slot_height / 2.0),
                    rotate=cq.Vector(0, 0, angle),
                )
                .center(radial_length / 2.0 + bore_radius - 0.5, 0)
                .box(radial_length, self.slot_width, slot_height)
            )
            result = result.cut(slot_box)

        return result
