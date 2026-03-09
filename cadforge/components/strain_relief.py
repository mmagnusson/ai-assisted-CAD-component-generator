import math
from dataclasses import dataclass, field
import cadquery as cq
from cadforge.core import Component


@dataclass
class StrainRelief(Component):
    """A cable strain relief / panel bushing."""

    name: str = "strain_relief"
    cable_diameter: float = 8.0
    panel_hole_diameter: float = 12.0
    panel_thickness: float = 2.0
    body_od: float = 16.0
    body_length: float = 15.0
    thread_od: float = 12.0
    thread_length: float = 8.0
    grip_segments: int = 4
    grip_taper_angle: float = 5.0
    nut_od: float = 18.0
    nut_thickness: float = 5.0

    def build(self) -> cq.Workplane:
        cable_r = self.cable_diameter / 2.0
        body_r = self.body_od / 2.0
        thread_r = self.thread_od / 2.0

        # ------------------------------------------------------------------
        # Body: cylinder with central bore, positioned along Z
        # Body sits at Z=0 upward
        # ------------------------------------------------------------------
        body = (
            cq.Workplane("XY")
            .circle(body_r)
            .circle(cable_r)
            .extrude(self.body_length)
        )

        # ------------------------------------------------------------------
        # Cable grip: circumferential grooves cut around the OD
        # ------------------------------------------------------------------
        if self.grip_segments > 0:
            groove_depth = 1.0
            groove_width = 1.5
            segment_length = self.body_length / (self.grip_segments + 1)

            for i in range(self.grip_segments):
                z_pos = segment_length * (i + 1)
                groove = (
                    cq.Workplane("XY")
                    .transformed(offset=cq.Vector(0, 0, z_pos - groove_width / 2.0))
                    .circle(body_r + 1)
                    .circle(body_r - groove_depth)
                    .extrude(groove_width)
                )
                body = body.cut(groove)

        # ------------------------------------------------------------------
        # Panel thread section: plain cylinder extending below the body
        # (from Z=0 downward)
        # ------------------------------------------------------------------
        thread_section = (
            cq.Workplane("XY")
            .circle(thread_r)
            .circle(cable_r)
            .extrude(self.thread_length)
            .translate((0, 0, -self.thread_length))
        )
        body = body.union(thread_section)

        # ------------------------------------------------------------------
        # Nut: hexagonal piece on the thread section
        # Positioned below the body, stacked on the thread
        # ------------------------------------------------------------------
        # Hex nut: use polygon(6, ...) with the OD as the circumscribed diameter
        hex_circumscribed = self.nut_od / math.cos(math.pi / 6)
        nut = (
            cq.Workplane("XY")
            .polygon(6, hex_circumscribed)
            .circle(thread_r)
            .extrude(self.nut_thickness)
            .translate((0, 0, -self.thread_length + (self.thread_length - self.nut_thickness) / 2.0))
        )
        body = body.union(nut)

        return body
