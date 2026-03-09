"""Cylindrical plug gauge (Go/No-Go) for hole inspection."""

import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class GoNoGoGauge(Component):
    """Double-ended cylindrical plug gauge for hole inspection.

    A handle cylinder in the center with a GO pin extending from one end
    and a NOGO pin from the other. The GO pin is at nominal diameter and
    should pass through the hole; the NOGO pin is slightly larger and
    should not.
    """

    name: str = "go_nogo_gauge"
    go_diameter: float = 10.0
    nogo_diameter: float = 10.05
    go_length: float = 20.0
    nogo_length: float = 12.0
    handle_diameter: float = 15.0
    handle_length: float = 30.0
    gauge_style: str = "double_ended"

    def build(self) -> cq.Workplane:
        go_r = self.go_diameter / 2.0
        nogo_r = self.nogo_diameter / 2.0
        handle_r = self.handle_diameter / 2.0

        # Total length along Z axis. Layout (bottom to top):
        #   NOGO pin -> handle -> GO pin
        # Center the assembly so the handle is at the origin.

        handle_bottom = -self.handle_length / 2.0
        handle_top = self.handle_length / 2.0

        # Handle: central cylinder
        handle = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, handle_bottom))
            .circle(handle_r)
            .extrude(self.handle_length)
        )

        # Chamfer the handle edges for grip (approximation of knurling)
        chamfer_size = min(1.0, self.handle_diameter * 0.05, self.handle_length * 0.1)
        if chamfer_size > 0.1:
            handle = handle.faces(">Z").chamfer(chamfer_size)
            handle = handle.faces("<Z").chamfer(chamfer_size)

        # GO pin: extends from the top of the handle upward (+Z)
        go_pin = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, handle_top))
            .circle(go_r)
            .extrude(self.go_length)
        )

        # NOGO pin: extends from the bottom of the handle downward (-Z)
        nogo_pin = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, handle_bottom))
            .circle(nogo_r)
            .extrude(-self.nogo_length)
        )

        # Union all parts
        result = handle.union(go_pin).union(nogo_pin)

        return result
