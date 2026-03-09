"""Over-center toggle clamp component."""

import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class ToggleClamp(Component):
    """Over-center toggle clamp in the static/open position.

    Consists of a base plate with mounting holes, a vertical pivot bracket
    (two uprights with a pivot pin hole), and a pivoting arm with handle.
    """

    name: str = "toggle_clamp"
    base_length: float = 80.0
    base_width: float = 30.0
    base_thickness: float = 8.0
    arm_length: float = 60.0
    arm_width: float = 15.0
    arm_thickness: float = 6.0
    pivot_height: float = 25.0
    pivot_pin_diameter: float = 6.0
    handle_length: float = 100.0
    clamp_force_point_height: float = 30.0

    def build(self) -> cq.Workplane:
        # --- Base plate ---
        base = (
            cq.Workplane("XY")
            .box(self.base_length, self.base_width, self.base_thickness,
                 centered=(True, True, False))
        )

        # Mounting holes in base (4 corners)
        hole_inset_x = self.base_length * 0.2
        hole_inset_y = self.base_width * 0.3
        mount_points = [
            (-self.base_length / 2 + hole_inset_x, -self.base_width / 2 + hole_inset_y),
            (-self.base_length / 2 + hole_inset_x, self.base_width / 2 - hole_inset_y),
            (self.base_length / 2 - hole_inset_x, -self.base_width / 2 + hole_inset_y),
            (self.base_length / 2 - hole_inset_x, self.base_width / 2 - hole_inset_y),
        ]
        base = (
            base
            .faces(">Z")
            .workplane()
            .pushPoints(mount_points)
            .hole(self.pivot_pin_diameter * 0.8, self.base_thickness)
        )

        # --- Pivot bracket: two vertical uprights ---
        bracket_thickness = self.arm_thickness
        bracket_width = self.arm_thickness
        gap = self.arm_width + 2  # gap between uprights for the arm

        # Left upright
        left_upright = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, -(gap / 2 + bracket_width / 2), 0))
            .box(bracket_thickness * 2, bracket_width, self.pivot_height,
                 centered=(True, True, False))
        )
        # Right upright
        right_upright = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, (gap / 2 + bracket_width / 2), 0))
            .box(bracket_thickness * 2, bracket_width, self.pivot_height,
                 centered=(True, True, False))
        )

        # Move uprights up to sit on top of the base
        left_upright = left_upright.translate((0, 0, self.base_thickness))
        right_upright = right_upright.translate((0, 0, self.base_thickness))

        result = base.union(left_upright).union(right_upright)

        # Pivot pin holes through both uprights
        pivot_z = self.base_thickness + self.pivot_height * 0.75
        pin_hole = (
            cq.Workplane("XZ")
            .transformed(offset=cq.Vector(0, pivot_z, 0))
            .cylinder(
                self.base_width + 2,
                self.pivot_pin_diameter / 2,
                centered=(True, True, True),
            )
        )
        result = result.cut(pin_hole)

        # --- Arm with handle (open position, angled upward) ---
        arm_angle = 45  # degrees from horizontal in open position
        arm_angle_rad = math.radians(arm_angle)

        # Build the arm as a box, then rotate and position
        arm = (
            cq.Workplane("XY")
            .box(self.arm_length, self.arm_width, self.arm_thickness,
                 centered=(False, True, True))
        )

        # Pin hole at the pivot end of the arm
        arm = (
            arm
            .faces(">Y")
            .workplane()
            .center(-self.arm_length / 2, 0)
            .hole(self.pivot_pin_diameter, self.arm_width)
        )

        # Rotate arm to open position and translate to pivot point
        arm = arm.rotate((0, 0, 0), (0, 1, 0), -arm_angle)
        arm = arm.translate((0, 0, pivot_z))

        result = result.union(arm)

        # --- Handle: extends from the rear of the arm ---
        handle_start_x = -self.arm_length * math.cos(arm_angle_rad) * 0.1
        handle_start_z = pivot_z + self.arm_length * math.sin(arm_angle_rad) * 0.1
        handle_end_x = -(self.handle_length * 0.7) * math.cos(arm_angle_rad)
        handle_end_z = pivot_z + (self.handle_length * 0.7) * math.sin(arm_angle_rad)

        handle = (
            cq.Workplane("XY")
            .box(self.handle_length, self.arm_width * 0.6, self.arm_thickness * 0.8,
                 centered=(False, True, True))
        )
        handle = handle.rotate((0, 0, 0), (0, 1, 0), -arm_angle)
        handle = handle.translate((
            -self.arm_length * math.cos(arm_angle_rad) * 0.5,
            0,
            pivot_z + self.arm_length * math.sin(arm_angle_rad) * 0.5,
        ))

        result = result.union(handle)

        return result
