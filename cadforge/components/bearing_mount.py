import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class FlangedBearingMount(Component):
    """A flanged bearing housing with central hub, bore, and bolt holes."""

    name: str = "flanged_bearing_mount"
    bore_diameter: float = 25.0
    flange_diameter: float = 80.0
    flange_thickness: float = 10.0
    hub_height: float = 20.0
    hub_diameter: float = 40.0
    bolt_circle_diameter: float = 60.0
    bolt_count: int = 4
    bolt_diameter: float = 6.0

    def build(self) -> cq.Workplane:
        # Create the flange plate centered on origin
        result = (
            cq.Workplane("XY")
            .circle(self.flange_diameter / 2)
            .extrude(self.flange_thickness)
        )

        # Add the central hub on top of the flange
        result = (
            result
            .faces(">Z")
            .workplane()
            .circle(self.hub_diameter / 2)
            .extrude(self.hub_height)
        )

        # Through-bore from bottom through the entire part
        total_height = self.flange_thickness + self.hub_height
        result = (
            result
            .faces(">Z")
            .workplane()
            .hole(self.bore_diameter, total_height)
        )

        # Bolt holes on the bolt circle, evenly spaced
        bolt_positions = [
            (
                (self.bolt_circle_diameter / 2)
                * math.cos(2 * math.pi * i / self.bolt_count),
                (self.bolt_circle_diameter / 2)
                * math.sin(2 * math.pi * i / self.bolt_count),
            )
            for i in range(self.bolt_count)
        ]
        result = (
            result
            .faces("<Z")
            .workplane()
            .pushPoints(bolt_positions)
            .hole(self.bolt_diameter, self.flange_thickness)
        )

        return result
