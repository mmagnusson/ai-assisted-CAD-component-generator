"""Rack and pinion gear set component."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class RackAndPinion(Component):
    """Rack and pinion gear set with simplified tooth profiles.

    The pinion is modeled as a plain cylinder at the pitch diameter.
    Rack teeth are approximated as rectangular notches spaced at
    pi * module intervals.
    """

    name: str = "rack_and_pinion"
    module: float = 2.0
    pinion_teeth: int = 12
    rack_length: float = 100.0
    rack_height: float = 20.0
    rack_width: float = 15.0
    pressure_angle: float = 20.0
    gear_width: float = 15.0
    shaft_diameter: float = 10.0
    housing_wall: float = 5.0
    mounting_hole_diameter: float = 5.0

    def build(self) -> cq.Workplane:
        pitch_diameter = self.module * self.pinion_teeth
        pitch_radius = pitch_diameter / 2.0
        tooth_height = 2.25 * self.module  # standard full depth
        tooth_pitch = math.pi * self.module  # circular pitch
        tooth_width = tooth_pitch / 2.0  # tooth and gap are equal

        # -----------------------------------------------------------
        # Rack: rectangular bar with teeth on top
        # -----------------------------------------------------------
        rack = (
            cq.Workplane("XY")
            .box(self.rack_length, self.rack_width, self.rack_height)
        )
        # Rack is centered at origin; teeth are on the +Z face

        # Cut tooth notches along the top of the rack
        num_teeth = int(self.rack_length / tooth_pitch) + 1
        rack_top_z = self.rack_height / 2.0

        for i in range(num_teeth):
            x_pos = -self.rack_length / 2.0 + tooth_pitch * 0.25 + i * tooth_pitch
            if abs(x_pos) > self.rack_length / 2.0:
                continue
            notch = (
                cq.Workplane("XY")
                .box(tooth_width, self.rack_width + 2.0, self.module)
                .translate((x_pos, 0, rack_top_z - self.module / 2.0 + 0.01))
            )
            rack = rack.cut(notch)

        # -----------------------------------------------------------
        # Pinion: plain cylinder at pitch diameter
        # -----------------------------------------------------------
        # Position pinion above the rack at correct center distance
        # Center distance = rack top + pitch_radius (teeth mesh at pitch line)
        pinion_center_z = rack_top_z + pitch_radius

        pinion = (
            cq.Workplane("XZ")
            .circle(pitch_radius)
            .extrude(self.gear_width)
            .translate((0, -self.gear_width / 2.0, pinion_center_z))
        )

        # Shaft bore through pinion center
        shaft_bore = (
            cq.Workplane("XZ")
            .circle(self.shaft_diameter / 2.0)
            .extrude(self.gear_width + 2.0)
            .translate((0, -self.gear_width / 2.0 - 1.0, pinion_center_z))
        )
        pinion = pinion.cut(shaft_bore)

        # -----------------------------------------------------------
        # Housing: U-channel around the rack with bearing bores
        # -----------------------------------------------------------
        hw = self.housing_wall
        housing_inner_w = self.rack_width + 2.0  # clearance
        housing_outer_w = housing_inner_w + 2.0 * hw
        housing_h = self.rack_height + pitch_diameter + hw
        housing_len = self.rack_length + 2.0 * hw

        # Outer housing box
        housing = (
            cq.Workplane("XY")
            .box(housing_len, housing_outer_w, housing_h)
            .translate((0, 0, housing_h / 2.0 - self.rack_height / 2.0 - hw))
        )

        # Cut the inner channel (open top)
        inner_cut_h = housing_h  # cut all the way through the top
        inner_cut = (
            cq.Workplane("XY")
            .box(self.rack_length + 1.0, housing_inner_w, inner_cut_h)
            .translate((0, 0, housing_h / 2.0 - self.rack_height / 2.0 - hw + hw))
        )
        housing = housing.cut(inner_cut)

        # Bearing bores through the housing sides for the pinion shaft
        bearing_bore_y = housing_outer_w / 2.0 + 1.0
        for side in [1, -1]:
            bore = (
                cq.Workplane("XZ")
                .circle(self.shaft_diameter / 2.0 + 1.0)
                .extrude(hw + 2.0)
                .translate((0, side * (housing_inner_w / 2.0 - 1.0), pinion_center_z))
            )
            housing = housing.cut(bore)

        # Mounting holes in the housing base
        base_z = -self.rack_height / 2.0 - hw
        for x_off in [-self.rack_length / 3.0, self.rack_length / 3.0]:
            for y_off in [-housing_outer_w / 4.0, housing_outer_w / 4.0]:
                m_hole = (
                    cq.Workplane("XY")
                    .workplane(offset=base_z - 1.0)
                    .center(x_off, y_off)
                    .circle(self.mounting_hole_diameter / 2.0)
                    .extrude(hw + 2.0)
                )
                housing = housing.cut(m_hole)

        # Union all parts
        result = housing.union(rack).union(pinion)

        return result
