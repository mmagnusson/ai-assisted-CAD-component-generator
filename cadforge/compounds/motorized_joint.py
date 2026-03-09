"""Motorized joint compound component.

A motor mount + shaft coupler + bearing mount, pre-constrained as a
single reusable unit.  Represents a single powered rotary joint, the
fundamental building block of robotic arms and actuated mechanisms.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..assembly import MateConstraint
from ..components.bearing_mount import FlangedBearingMount
from ..components.bracket import LBracket
from ..components.shaft_coupler import ShaftCoupler
from ..core import Component, MatePoint
from . import CompoundComponent


@dataclass
class MotorizedJoint(CompoundComponent):
    """A motorized rotary joint: bracket base + bearing mount + shaft coupler.

    The bracket serves as the structural base.  The bearing mount sits
    on top of the bracket, and the shaft coupler is aligned coaxially
    with the bearing bore.

    Parameters:
        motor_shaft_diameter: Diameter of the motor output shaft (mm).
        output_shaft_diameter: Diameter of the driven shaft (mm).
        bearing_bore: Bore diameter of the bearing mount (mm).
        bracket_width: Width of the base bracket (mm).
        bracket_height: Height of the base bracket (mm).
        bracket_thickness: Material thickness of the bracket (mm).
        flange_diameter: Outer diameter of the bearing flange (mm).
        bolt_count: Number of bolts on the bearing mount.
    """

    name: str = "motorized_joint"
    motor_shaft_diameter: float = 8.0
    output_shaft_diameter: float = 10.0
    bearing_bore: float = 25.0
    bracket_width: float = 80.0
    bracket_height: float = 40.0
    bracket_thickness: float = 5.0
    flange_diameter: float = 60.0
    bolt_count: int = 4

    def components(self) -> list[tuple[Component, str]]:
        bracket = LBracket(
            width=self.bracket_width,
            height=self.bracket_height,
            thickness=self.bracket_thickness,
        )
        bearing = FlangedBearingMount(
            bore_diameter=self.bearing_bore,
            flange_diameter=self.flange_diameter,
            bolt_count=self.bolt_count,
        )
        coupler = ShaftCoupler(
            bore_1=self.motor_shaft_diameter,
            bore_2=self.output_shaft_diameter,
        )
        return [
            (bracket, "base_bracket"),
            (bearing, "bearing_mount"),
            (coupler, "shaft_coupler"),
        ]

    def internal_constraints(self) -> list[MateConstraint]:
        return [
            # Bearing sits on top of the bracket's horizontal face
            MateConstraint(
                part1_name="base_bracket",
                mate1_name="horizontal_face",
                part2_name="bearing_mount",
                mate2_name="bottom",
            ),
            # Shaft coupler aligns coaxially with bearing bore
            MateConstraint(
                part1_name="bearing_mount",
                mate1_name="bore_axis",
                part2_name="shaft_coupler",
                mate2_name="center_axis",
                constraint_type="coaxial",
            ),
        ]

    def mates(self) -> list[MatePoint]:
        # Expose connection points for the parent assembly.
        # These are in the compound's resolved coordinate frame.
        bracket = LBracket(
            width=self.bracket_width,
            height=self.bracket_height,
            thickness=self.bracket_thickness,
        )
        bearing = FlangedBearingMount(
            bore_diameter=self.bearing_bore,
            flange_diameter=self.flange_diameter,
        )
        total_height = (
            self.bracket_thickness
            + bearing.flange_thickness
            + bearing.hub_height
        )

        return [
            # Bottom of the whole unit (bracket bottom)
            MatePoint(
                name="base_bottom",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            # Top of the bearing mount
            MatePoint(
                name="bearing_top",
                origin=(
                    self.bracket_width / 2,
                    self.bracket_width / 2,
                    total_height,
                ),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            # Output axis (for connecting to the next link)
            MatePoint(
                name="output_axis",
                origin=(
                    self.bracket_width / 2,
                    self.bracket_width / 2,
                    total_height / 2,
                ),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
            # Vertical face of bracket (for side-mounting)
            MatePoint(
                name="vertical_face",
                origin=(
                    self.bracket_thickness,
                    self.bracket_width / 2,
                    self.bracket_height / 2,
                ),
                normal=(-1.0, 0.0, 0.0),
                mate_type="face",
            ),
        ]
