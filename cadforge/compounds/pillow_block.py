"""Pillow block compound component.

A bearing mount on standoffs, forming a raised shaft support.
Common in conveyor systems, linear motion, and robotic bases.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..assembly import MateConstraint
from ..components.bearing_mount import FlangedBearingMount
from ..components.standoff import Standoff
from ..core import Component, MatePoint
from . import CompoundComponent


@dataclass
class PillowBlock(CompoundComponent):
    """A bearing mount raised on standoffs.

    Two standoffs support a flanged bearing mount, creating a raised
    pillow block for shaft support.

    Parameters:
        bearing_bore: Bore diameter of the bearing (mm).
        standoff_height: Height of the support standoffs (mm).
        flange_diameter: Outer diameter of the bearing flange (mm).
        bolt_circle_diameter: Bolt circle on the bearing mount (mm).
        bolt_count: Number of mounting bolts.
        standoff_diameter: Base diameter of the standoffs (mm).
    """

    name: str = "pillow_block"
    bearing_bore: float = 25.0
    standoff_height: float = 20.0
    flange_diameter: float = 80.0
    bolt_circle_diameter: float = 60.0
    bolt_count: int = 4
    standoff_diameter: float = 6.0

    def components(self) -> list[tuple[Component, str]]:
        bearing = FlangedBearingMount(
            bore_diameter=self.bearing_bore,
            flange_diameter=self.flange_diameter,
            bolt_circle_diameter=self.bolt_circle_diameter,
            bolt_count=self.bolt_count,
        )
        standoff_left = Standoff(
            height=self.standoff_height,
            base_diameter=self.standoff_diameter,
        )
        standoff_right = Standoff(
            height=self.standoff_height,
            base_diameter=self.standoff_diameter,
        )
        return [
            (standoff_left, "standoff_left"),
            (standoff_right, "standoff_right"),
            (bearing, "bearing"),
        ]

    def internal_constraints(self) -> list[MateConstraint]:
        # Position standoffs first, then bearing on top.
        # Standoffs are placed manually via location; the bearing
        # is constrained on top of the left standoff.
        return [
            MateConstraint(
                part1_name="standoff_left",
                mate1_name="top",
                part2_name="bearing",
                mate2_name="bottom",
            ),
        ]

    def mates(self) -> list[MatePoint]:
        bearing = FlangedBearingMount(
            bore_diameter=self.bearing_bore,
            flange_diameter=self.flange_diameter,
        )
        total_height = (
            self.standoff_height
            + bearing.flange_thickness
            + bearing.hub_height
        )

        return [
            MatePoint(
                name="base_left",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="base_right",
                origin=(self.bolt_circle_diameter, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="bearing_top",
                origin=(0.0, 0.0, total_height),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="bore_axis",
                origin=(0.0, 0.0, total_height / 2),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
        ]
