"""Crank-slider (piston) mechanism component."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class CrankSlider(Component):
    """Crank-slider (piston) mechanism.

    A crankshaft disc drives a connecting rod that moves a piston
    linearly inside a cylinder bore. All parts are positioned at the
    given crank angle.
    """

    name: str = "crank_slider"
    crank_radius: float = 25.0
    connecting_rod_length: float = 80.0
    piston_bore: float = 40.0
    piston_height: float = 30.0
    piston_wall: float = 3.0
    crank_thickness: float = 10.0
    rod_width: float = 12.0
    rod_thickness: float = 8.0
    pin_diameter: float = 8.0
    crank_angle: float = 45.0  # degrees
    cylinder_wall: float = 4.0
    cylinder_length: float = 0.0  # 0 = auto

    def build(self) -> cq.Workplane:
        # Resolve auto cylinder length
        cyl_len = (
            self.cylinder_length
            if self.cylinder_length > 0
            else self.crank_radius + self.connecting_rod_length + self.piston_height + 20.0
        )

        angle_rad = math.radians(self.crank_angle)

        # Crank pin position (mechanism in XZ plane)
        crank_pin_x = self.crank_radius * math.cos(angle_rad)
        crank_pin_z = self.crank_radius * math.sin(angle_rad)

        # Piston position (slider moves along +Z axis)
        # From crank-slider kinematics:
        # piston_z = crank_radius * cos(angle) + sqrt(rod_length^2 - (crank_radius * sin(angle))^2)
        # But we orient the mechanism so piston slides along +X
        # Actually let's use X axis for the linear motion:
        # Crank center at origin, piston slides along +X
        crank_pin_x = self.crank_radius * math.cos(angle_rad)
        crank_pin_y_mech = self.crank_radius * math.sin(angle_rad)

        # Piston X position from slider-crank kinematics
        sin_a = self.crank_radius * math.sin(angle_rad) / self.connecting_rod_length
        # Clamp for safety
        sin_a = max(-1.0, min(1.0, sin_a))
        piston_x = (
            self.crank_radius * math.cos(angle_rad)
            + self.connecting_rod_length * math.cos(math.asin(sin_a))
        )

        # -----------------------------------------------------------
        # Crankshaft disc (in XY plane at Z=0)
        # -----------------------------------------------------------
        shaft_hole_d = self.pin_diameter + 4.0  # main shaft bore
        crank_disc = (
            cq.Workplane("XY")
            .circle(self.crank_radius + 5.0)
            .circle(shaft_hole_d / 2.0)
            .extrude(self.crank_thickness)
            .translate((0, 0, -self.crank_thickness / 2.0))
        )

        # Crank pin
        crank_pin = (
            cq.Workplane("XY")
            .circle(self.pin_diameter / 2.0)
            .extrude(self.crank_thickness + self.rod_thickness)
            .translate((crank_pin_x, crank_pin_y_mech, -self.crank_thickness / 2.0))
        )

        # -----------------------------------------------------------
        # Connecting rod
        # -----------------------------------------------------------
        # Rod connects crank pin to piston (wrist) pin
        # Crank pin at (crank_pin_x, crank_pin_y_mech, 0)
        # Wrist pin at (piston_x, 0, 0)
        rod_cx = (crank_pin_x + piston_x) / 2.0
        rod_cy = crank_pin_y_mech / 2.0

        rod_angle = math.degrees(math.atan2(
            crank_pin_y_mech - 0,
            crank_pin_x - piston_x,
        ))

        rod = (
            cq.Workplane("XY")
            .box(self.connecting_rod_length, self.rod_width, self.rod_thickness)
        )
        # Drill pin holes at each end of the rod
        rod = (
            rod
            .faces(">Z")
            .workplane()
            .center(self.connecting_rod_length / 2.0 - self.rod_width / 2.0, 0)
            .hole(self.pin_diameter)
        )
        rod = (
            rod
            .faces(">Z")
            .workplane()
            .center(-self.connecting_rod_length / 2.0 + self.rod_width / 2.0, 0)
            .hole(self.pin_diameter)
        )

        # Rotate and position the rod
        rod = rod.rotate((0, 0, 0), (0, 0, 1), rod_angle + 180)
        rod = rod.translate((rod_cx, rod_cy, 0))

        # -----------------------------------------------------------
        # Piston: hollow cylinder with wrist pin hole
        # -----------------------------------------------------------
        piston = (
            cq.Workplane("YZ")
            .circle(self.piston_bore / 2.0 - 0.5)  # slight clearance
            .circle(self.piston_bore / 2.0 - self.piston_wall)
            .extrude(self.piston_height)
            .translate((piston_x, 0, 0))
        )

        # Piston head (closed end)
        piston_head = (
            cq.Workplane("YZ")
            .circle(self.piston_bore / 2.0 - 0.5)
            .extrude(self.piston_wall)
            .translate((piston_x + self.piston_height - self.piston_wall, 0, 0))
        )
        piston = piston.union(piston_head)

        # Wrist pin hole through the piston sides
        wrist_pin_hole = (
            cq.Workplane("XZ")
            .circle(self.pin_diameter / 2.0)
            .extrude(self.piston_bore)
            .translate((piston_x + self.piston_height * 0.3, -self.piston_bore / 2.0, 0))
        )
        piston = piston.cut(wrist_pin_hole)

        # -----------------------------------------------------------
        # Cylinder bore: hollow cylinder, open at one end
        # -----------------------------------------------------------
        cyl_od = self.piston_bore + 2.0 * self.cylinder_wall
        cylinder = (
            cq.Workplane("YZ")
            .circle(cyl_od / 2.0)
            .circle(self.piston_bore / 2.0)
            .extrude(cyl_len)
            .translate((self.connecting_rod_length - self.crank_radius, 0, 0))
        )

        # Cylinder head (closed end)
        cyl_head = (
            cq.Workplane("YZ")
            .circle(cyl_od / 2.0)
            .extrude(self.cylinder_wall)
            .translate((self.connecting_rod_length - self.crank_radius + cyl_len - self.cylinder_wall, 0, 0))
        )
        cylinder = cylinder.union(cyl_head)

        # -----------------------------------------------------------
        # Union all parts
        # -----------------------------------------------------------
        result = crank_disc.union(crank_pin).union(rod).union(piston).union(cylinder)

        return result
