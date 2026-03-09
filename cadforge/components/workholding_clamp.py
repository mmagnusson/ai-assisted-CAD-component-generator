"""DIN 6314-style step block strap clamp for CNC workholding."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class WorkholdingClamp(Component):
    """Step block strap clamp (DIN 6314 style) for CNC workholding.

    A rectangular bar with stepped bottom surface for height adjustment,
    a through-slot for the hold-down stud, and an angled toe at the front
    that presses down on the workpiece.
    """

    name: str = "workholding_clamp"
    clamp_length: float = 100.0
    clamp_width: float = 25.0
    clamp_thickness: float = 12.0
    step_height: float = 15.0
    step_count: int = 3
    stud_slot_width: float = 14.0
    stud_slot_length: float = 30.0
    toe_length: float = 20.0
    toe_angle: float = 10.0

    def build(self) -> cq.Workplane:
        # Main rectangular bar, centered on origin
        result = (
            cq.Workplane("XY")
            .box(self.clamp_length, self.clamp_width, self.clamp_thickness)
        )

        # Stepped bottom surface: steps are cut from the bottom face along
        # the length (X axis), on the back half (away from the toe).
        # Steps increase in height from front to back so the clamp can
        # rest on a step block at different heights.
        if self.step_count > 0 and self.step_height > 0:
            step_region_length = self.clamp_length - self.toe_length
            single_step_length = step_region_length / self.step_count
            step_height_increment = self.step_height / self.step_count

            for i in range(self.step_count):
                cut_height = step_height_increment * (i + 1)
                # Only cut if it doesn't exceed the clamp thickness
                if cut_height >= self.clamp_thickness:
                    continue

                # Position each step: starts from the back end (-X side)
                step_center_x = (
                    -self.clamp_length / 2.0
                    + single_step_length * i
                    + single_step_length / 2.0
                )
                step_center_z = -self.clamp_thickness / 2.0 + cut_height / 2.0

                step_cut = (
                    cq.Workplane("XY")
                    .transformed(offset=cq.Vector(
                        step_center_x,
                        0,
                        step_center_z,
                    ))
                    .box(
                        single_step_length + 0.01,
                        self.clamp_width + 0.01,
                        cut_height,
                    )
                )
                result = result.cut(step_cut)

        # Through-slot for the hold-down stud, centered in the clamp body
        slot_cut = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, 0))
            .box(
                self.stud_slot_length,
                self.stud_slot_width,
                self.clamp_thickness + 1,
            )
        )
        result = result.cut(slot_cut)

        # Toe/nose at the front end (+X side): angled downward.
        # We cut a wedge from the bottom-front to create the angled toe.
        if self.toe_angle > 0 and self.toe_length > 0:
            # The toe drops down by toe_length * tan(toe_angle)
            toe_drop = self.toe_length * math.tan(math.radians(self.toe_angle))

            # Create a wedge-shaped cut under the toe region.
            # Use a lofted or extruded polygon to remove material from the
            # bottom of the front section, creating the downward angle.
            toe_start_x = self.clamp_length / 2.0 - self.toe_length
            toe_end_x = self.clamp_length / 2.0

            # Build a triangular prism to cut the angled surface
            # The triangle is in the XZ plane, extruded along Y
            pts = [
                (toe_start_x, -self.clamp_thickness / 2.0),
                (toe_end_x, -self.clamp_thickness / 2.0),
                (toe_end_x, -self.clamp_thickness / 2.0 + toe_drop),
            ]
            wedge_cut = (
                cq.Workplane("XZ")
                .polyline(pts)
                .close()
                .extrude(self.clamp_width / 2.0, both=True)
            )
            result = result.cut(wedge_cut)

        return result
