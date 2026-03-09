import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component, MatePoint


@dataclass
class ShaftCoupler(Component):
    """A rigid shaft-to-shaft coupler with optional keyway and clamping slit."""

    name: str = "shaft_coupler"
    bore_1: float = 8.0
    bore_2: float = 10.0
    outer_diameter: float = 30.0
    length: float = 40.0
    set_screw_diameter: float = 4.0
    set_screw_count: int = 2
    keyway_width: float = 0.0
    keyway_depth: float = 0.0
    slit_width: float = 1.0

    def build(self) -> cq.Workplane:
        half = self.length / 2

        # Main cylindrical body
        result = (
            cq.Workplane("XY")
            .circle(self.outer_diameter / 2)
            .extrude(self.length)
        )

        # Bore from bottom (Z=0) for bore_1, blind to the midpoint
        result = (
            result
            .faces("<Z")
            .workplane()
            .circle(self.bore_1 / 2)
            .cutBlind(half)
        )

        # Bore from top (Z=length) for bore_2, blind to the midpoint
        result = (
            result
            .faces(">Z")
            .workplane()
            .circle(self.bore_2 / 2)
            .cutBlind(half)
        )

        # Set screw holes on bore_1 section (radial, through the wall)
        if self.set_screw_count > 0 and self.set_screw_diameter > 0:
            # Place set screws evenly around bore_1 section at z = half/2
            screw_z_1 = half / 2
            for i in range(self.set_screw_count):
                angle = 360.0 * i / self.set_screw_count
                result = (
                    result
                    .faces(">Z")
                    .workplane(offset=-(self.length - screw_z_1))
                    .transformed(rotate=cq.Vector(0, 0, angle))
                    .transformed(rotate=cq.Vector(0, 90, 0))
                    .circle(self.set_screw_diameter / 2)
                    .cutBlind(self.outer_diameter / 2)
                )

            # Set screws on bore_2 section at z = half + half/2
            screw_z_2 = half + half / 2
            for i in range(self.set_screw_count):
                angle = 360.0 * i / self.set_screw_count
                result = (
                    result
                    .faces(">Z")
                    .workplane(offset=-(self.length - screw_z_2))
                    .transformed(rotate=cq.Vector(0, 0, angle))
                    .transformed(rotate=cq.Vector(0, 90, 0))
                    .circle(self.set_screw_diameter / 2)
                    .cutBlind(self.outer_diameter / 2)
                )

        # Optional keyway on bore_1 side
        if self.keyway_width > 0 and self.keyway_depth > 0:
            # Keyway is a rectangular slot cut into the bore_1 wall,
            # running the full length of the bore_1 section.
            bore_r = self.bore_1 / 2
            result = (
                result
                .faces("<Z")
                .workplane()
                .transformed(
                    offset=cq.Vector(bore_r + self.keyway_depth / 2, 0, 0)
                )
                .rect(self.keyway_depth, self.keyway_width)
                .cutBlind(half)
            )

        # Optional coupling slit for clamping flexibility
        if self.slit_width > 0:
            # A thin slot cut across the full diameter, through the wall,
            # running most of the coupler length (leaving a small bridge
            # at each end for structural integrity).
            bridge = min(3.0, self.length * 0.1)
            slit_length = self.length - 2 * bridge
            result = (
                result
                .faces(">Z")
                .workplane(offset=-bridge)
                .transformed(rotate=cq.Vector(90, 0, 0))
                .rect(self.slit_width, self.outer_diameter)
                .cutBlind(slit_length)
            )

        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="bore_1_entry",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="bore_2_entry",
                origin=(0.0, 0.0, self.length),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="center_axis",
                origin=(0.0, 0.0, self.length / 2),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
        ]
