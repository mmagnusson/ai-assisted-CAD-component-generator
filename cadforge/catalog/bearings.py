"""Standard deep-groove ball bearings for CAD Forge.

Covers common 600, 6000, and 6200 series bearings with correct
bore, OD, and width per ISO 15.  Geometry is an envelope
(outer ring, inner ring, no balls).
"""

from __future__ import annotations

from dataclasses import dataclass

import cadquery as cq

from ..core import Component, MatePoint


# ------------------------------------------------------------------
# Dimension table: designation -> {bore, outer_diameter, width} in mm
# ------------------------------------------------------------------

BEARING_TABLE: dict[str, dict[str, float]] = {
    # 600 series (miniature)
    "604":  {"bore": 4.0,  "outer_diameter": 12.0,  "width": 4.0},
    "605":  {"bore": 5.0,  "outer_diameter": 14.0,  "width": 5.0},
    "606":  {"bore": 6.0,  "outer_diameter": 17.0,  "width": 6.0},
    "607":  {"bore": 7.0,  "outer_diameter": 19.0,  "width": 6.0},
    "608":  {"bore": 8.0,  "outer_diameter": 22.0,  "width": 7.0},
    "609":  {"bore": 9.0,  "outer_diameter": 24.0,  "width": 7.0},
    # 6000 series (light)
    "6000": {"bore": 10.0, "outer_diameter": 26.0,  "width": 8.0},
    "6001": {"bore": 12.0, "outer_diameter": 28.0,  "width": 8.0},
    "6002": {"bore": 15.0, "outer_diameter": 32.0,  "width": 9.0},
    "6003": {"bore": 17.0, "outer_diameter": 35.0,  "width": 10.0},
    "6004": {"bore": 20.0, "outer_diameter": 42.0,  "width": 12.0},
    "6005": {"bore": 25.0, "outer_diameter": 47.0,  "width": 12.0},
    "6006": {"bore": 30.0, "outer_diameter": 55.0,  "width": 13.0},
    "6007": {"bore": 35.0, "outer_diameter": 62.0,  "width": 14.0},
    "6008": {"bore": 40.0, "outer_diameter": 68.0,  "width": 15.0},
    # 6200 series (medium)
    "6200": {"bore": 10.0, "outer_diameter": 30.0,  "width": 9.0},
    "6201": {"bore": 12.0, "outer_diameter": 32.0,  "width": 10.0},
    "6202": {"bore": 15.0, "outer_diameter": 35.0,  "width": 11.0},
    "6203": {"bore": 17.0, "outer_diameter": 40.0,  "width": 12.0},
    "6204": {"bore": 20.0, "outer_diameter": 47.0,  "width": 14.0},
    "6205": {"bore": 25.0, "outer_diameter": 52.0,  "width": 15.0},
    "6206": {"bore": 30.0, "outer_diameter": 62.0,  "width": 16.0},
    "6207": {"bore": 35.0, "outer_diameter": 72.0,  "width": 17.0},
    "6208": {"bore": 40.0, "outer_diameter": 80.0,  "width": 18.0},
}


@dataclass
class DeepGrooveBearing(Component):
    """Deep-groove ball bearing envelope geometry.

    Modeled as two concentric cylinders (inner race + outer race)
    with a gap representing the ball track.
    """

    name: str = "bearing"
    designation: str = "608"
    bore: float = 8.0
    outer_diameter: float = 22.0
    width: float = 7.0

    def build(self) -> cq.Workplane:
        or_radius = self.outer_diameter / 2
        ir_radius = self.bore / 2
        # Mid-radius for the ball track gap
        mid_radius = (or_radius + ir_radius) / 2
        race_width = (or_radius - ir_radius) * 0.35

        # Outer race
        outer_race = (
            cq.Workplane("XY")
            .circle(or_radius)
            .circle(or_radius - race_width)
            .extrude(self.width)
        )
        # Inner race
        inner_race = (
            cq.Workplane("XY")
            .circle(ir_radius + race_width)
            .circle(ir_radius)
            .extrude(self.width)
        )
        result = outer_race.union(inner_race)
        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="front",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="back",
                origin=(0.0, 0.0, self.width),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="bore_axis",
                origin=(0.0, 0.0, self.width / 2),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
        ]
