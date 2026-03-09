"""Torsion bar spring component."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class TorsionBar(Component):
    """A simple torsion bar spring.

    Consists of a smooth cylindrical bar with a splined end on one side
    and a hexagonal anchor end on the other.
    """

    name: str = "torsion_bar"
    diameter: float = 20.0
    active_length: float = 300.0
    spline_od: float = 22.0
    spline_length: float = 30.0
    spline_count: int = 24
    anchor_hex_af: float = 24.0  # across-flats
    anchor_hex_length: float = 25.0
    total_length: float = 0.0  # 0 = auto

    def build(self) -> cq.Workplane:
        # Resolve auto total_length
        total_len = (
            self.total_length
            if self.total_length > 0
            else self.spline_length + self.active_length + self.anchor_hex_length
        )

        # Build along the Z axis
        # Splined end at the bottom (Z=0 to spline_length)
        # Main bar in the middle
        # Hex anchor at the top

        # Main bar: smooth cylinder
        bar = (
            cq.Workplane("XY")
            .circle(self.diameter / 2.0)
            .extrude(self.active_length)
            .translate((0, 0, self.spline_length))
        )

        # Splined end: cylinder with longitudinal flats cut to approximate splines
        # Ensure spline OD is at least larger than bar diameter
        spline_od = max(self.spline_od, self.diameter + 2.0)
        spline_base = (
            cq.Workplane("XY")
            .circle(spline_od / 2.0)
            .extrude(self.spline_length)
        )

        # Cut spline grooves as narrow slots around the circumference
        groove_depth = (spline_od - self.diameter) / 2.0 + 0.5
        groove_width = max(0.5, math.pi * spline_od / self.spline_count * 0.4)

        for i in range(self.spline_count):
            angle = i * 360.0 / self.spline_count
            # Create a cutting box positioned at the outer edge
            cut_x = (spline_od / 2.0) * math.cos(math.radians(angle))
            cut_y = (spline_od / 2.0) * math.sin(math.radians(angle))
            cutter = (
                cq.Workplane("XY")
                .box(groove_width, groove_depth, self.spline_length)
                .rotate((0, 0, 0), (0, 0, 1), angle)
                .translate((cut_x * 0.5, cut_y * 0.5, self.spline_length / 2.0))
            )
            # Move cutter outward to cut at the perimeter
            cutter = cutter.translate((
                cut_x * 0.5,
                cut_y * 0.5,
                0,
            ))
            spline_base = spline_base.cut(cutter)

        # Hex anchor end: hexagonal prism
        # CadQuery polygon with 6 sides, inscribed in a circle
        # across-flats = circumradius * sqrt(3) => circumradius = af / sqrt(3)
        anchor_af = max(self.anchor_hex_af, self.diameter + 2.0)
        hex_circumradius = anchor_af / math.sqrt(3.0)
        hex_end = (
            cq.Workplane("XY")
            .polygon(6, hex_circumradius * 2.0)
            .extrude(self.anchor_hex_length)
            .translate((0, 0, self.spline_length + self.active_length))
        )

        # Union all parts
        result = bar.union(spline_base).union(hex_end)

        return result
