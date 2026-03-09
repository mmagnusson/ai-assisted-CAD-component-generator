"""Scotch yoke mechanism component."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class ScotchYoke(Component):
    """Scotch yoke mechanism that converts rotary motion to reciprocating
    linear motion.

    Consists of a rotating crank disc with an offset pin, a slotted
    yoke/slider block, and linear guide rails.
    """

    name: str = "scotch_yoke"
    crank_radius: float = 30.0
    crank_thickness: float = 8.0
    crank_pin_diameter: float = 8.0
    slider_width: float = 20.0
    slider_height: float = 40.0
    slider_thickness: float = 8.0
    yoke_slot_width: float = 10.0
    yoke_slot_length: float = 0.0  # 0 = auto: 2 * crank_radius + clearance
    guide_length: float = 120.0
    guide_width: float = 25.0
    guide_thickness: float = 8.0
    shaft_diameter: float = 12.0

    def build(self) -> cq.Workplane:
        # Resolve auto parameters
        slot_length = (
            self.yoke_slot_length
            if self.yoke_slot_length > 0
            else 2.0 * self.crank_radius + 10.0
        )

        # All parts built on XY plane, mechanism operates in XZ plane
        # Crank rotates in XZ, slider moves along X

        # Crank disc: cylinder with central shaft hole and offset crank pin
        crank_disc = (
            cq.Workplane("XY")
            .circle(self.crank_radius)
            .circle(self.shaft_diameter / 2.0)
            .extrude(self.crank_thickness)
            .translate((0, 0, -self.crank_thickness / 2.0))
        )

        # Crank pin: cylinder at crank_radius offset (along +X at angle 0)
        pin_height = self.crank_thickness + self.slider_thickness
        crank_pin = (
            cq.Workplane("XY")
            .circle(self.crank_pin_diameter / 2.0)
            .extrude(pin_height)
            .translate((self.crank_radius, 0, -pin_height / 2.0))
        )

        # Slider/yoke block: rectangular with a horizontal slot for the crank pin
        # Positioned with pin at center of slot (at crank_radius along X)
        slider = (
            cq.Workplane("XY")
            .box(self.slider_width, slot_length, self.slider_thickness)
            .translate((self.crank_radius, 0, 0))
        )

        # Cut the yoke slot through the slider (slot runs along Y for the pin)
        slot_cutter = (
            cq.Workplane("XY")
            .box(self.crank_pin_diameter + 1.0, slot_length + 2.0, self.slider_thickness + 2.0)
            .translate((self.crank_radius, 0, 0))
        )
        # Actually the slot should allow the pin to slide along Y (the crank radius direction)
        # Re-think: the yoke slot is horizontal (along Y axis here) to allow the pin to sweep
        slot_cutter = (
            cq.Workplane("XY")
            .box(self.yoke_slot_width, slot_length, self.slider_thickness + 2.0)
            .translate((self.crank_radius, 0, 0))
        )
        slider = slider.cut(slot_cutter)

        # Guide rails: two parallel bars flanking the slider
        rail_spacing = slot_length / 2.0 + self.guide_width / 2.0 + 2.0
        rail1 = (
            cq.Workplane("XY")
            .box(self.guide_length, self.guide_width, self.guide_thickness)
            .translate((self.crank_radius, rail_spacing, 0))
        )
        rail2 = (
            cq.Workplane("XY")
            .box(self.guide_length, self.guide_width, self.guide_thickness)
            .translate((self.crank_radius, -rail_spacing, 0))
        )

        # Union everything
        result = crank_disc.union(crank_pin).union(slider).union(rail1).union(rail2)

        return result
