"""NEMA stepper motor envelopes for CAD Forge.

Provides NEMA 14, 17, 23, and 34 frame sizes with correct faceplate
dimensions, bolt patterns, pilot diameters, and shaft sizes.
Geometry is envelope-level — a rectangular body with a cylindrical
pilot boss and shaft stub.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

from ..core import Component, MatePoint


# ------------------------------------------------------------------
# NEMA frame dimension table (all in mm)
# ------------------------------------------------------------------

MOTOR_TABLE: dict[str, dict[str, float]] = {
    "nema14": {
        "faceplate_width": 35.2,
        "body_length": 36.0,
        "shaft_diameter": 5.0,
        "shaft_length": 20.0,
        "bolt_hole_spacing": 26.0,
        "bolt_hole_diameter": 3.0,
        "pilot_diameter": 22.0,
        "pilot_height": 2.0,
    },
    "nema17": {
        "faceplate_width": 42.3,
        "body_length": 48.0,
        "shaft_diameter": 5.0,
        "shaft_length": 24.0,
        "bolt_hole_spacing": 31.0,
        "bolt_hole_diameter": 3.0,
        "pilot_diameter": 22.0,
        "pilot_height": 2.0,
    },
    "nema23": {
        "faceplate_width": 57.2,
        "body_length": 56.0,
        "shaft_diameter": 6.35,
        "shaft_length": 21.0,
        "bolt_hole_spacing": 47.1,
        "bolt_hole_diameter": 5.0,
        "pilot_diameter": 38.1,
        "pilot_height": 1.6,
    },
    "nema34": {
        "faceplate_width": 86.0,
        "body_length": 66.0,
        "shaft_diameter": 12.7,
        "shaft_length": 37.0,
        "bolt_hole_spacing": 69.6,
        "bolt_hole_diameter": 5.5,
        "pilot_diameter": 73.0,
        "pilot_height": 1.6,
    },
}


@dataclass
class NemaMotor(Component):
    """NEMA stepper motor envelope geometry.

    The motor body extends in -Z from the faceplate at Z=0.
    The shaft and pilot boss extend in +Z.
    """

    name: str = "nema_motor"
    frame_size: str = "nema17"
    faceplate_width: float = 42.3
    body_length: float = 48.0
    shaft_diameter: float = 5.0
    shaft_length: float = 24.0
    bolt_hole_spacing: float = 31.0
    bolt_hole_diameter: float = 3.0
    pilot_diameter: float = 22.0
    pilot_height: float = 2.0

    def build(self) -> cq.Workplane:
        w = self.faceplate_width

        # Main body: square cross-section, extends in -Z
        body = (
            cq.Workplane("XY")
            .rect(w, w)
            .extrude(-self.body_length)
        )

        # Pilot boss on the faceplate (extends in +Z)
        pilot = (
            cq.Workplane("XY")
            .circle(self.pilot_diameter / 2)
            .extrude(self.pilot_height)
        )
        result = body.union(pilot)

        # Output shaft (extends in +Z from pilot top)
        shaft = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, self.pilot_height))
            .circle(self.shaft_diameter / 2)
            .extrude(self.shaft_length)
        )
        result = result.union(shaft)

        # Bolt holes on the faceplate (4 holes in a square pattern)
        half_spacing = self.bolt_hole_spacing / 2
        bolt_positions = [
            (half_spacing, half_spacing),
            (-half_spacing, half_spacing),
            (-half_spacing, -half_spacing),
            (half_spacing, -half_spacing),
        ]
        result = (
            result
            .faces(">Z[-2]")  # faceplate face at Z=0
            .workplane()
            .pushPoints(bolt_positions)
            .hole(self.bolt_hole_diameter, 5.0)
        )

        return result

    def mates(self) -> list[MatePoint]:
        shaft_tip_z = self.pilot_height + self.shaft_length
        return [
            MatePoint(
                name="faceplate",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="back",
                origin=(0.0, 0.0, -self.body_length),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="shaft_tip",
                origin=(0.0, 0.0, shaft_tip_z),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="shaft_axis",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
        ]
