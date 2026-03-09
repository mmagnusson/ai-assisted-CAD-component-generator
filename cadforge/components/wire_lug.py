import math
from dataclasses import dataclass, field
import cadquery as cq
from cadforge.core import Component


@dataclass
class WireLug(Component):
    """A crimp-style wire lug terminal."""

    name: str = "wire_lug"
    wire_gauge_mm: float = 6.0
    hole_diameter: float = 8.0
    tongue_width: float = 16.0
    tongue_length: float = 20.0
    tongue_thickness: float = 2.0
    barrel_od: float = 0.0
    barrel_length: float = 15.0
    barrel_wall: float = 1.0
    transition_length: float = 5.0

    def _resolve_barrel_od(self) -> float:
        if self.barrel_od > 0:
            return self.barrel_od
        return self.wire_gauge_mm + 2 * self.barrel_wall + 2.0

    def build(self) -> cq.Workplane:
        bod = self._resolve_barrel_od()
        barrel_ir = bod / 2.0 - self.barrel_wall

        # ------------------------------------------------------------------
        # Tongue / palm: flat plate with mounting hole
        # Tongue extends along +X from origin, centered on Y and Z
        # ------------------------------------------------------------------
        tongue = (
            cq.Workplane("XY")
            .box(
                self.tongue_length,
                self.tongue_width,
                self.tongue_thickness,
                centered=(False, True, True),
            )
        )
        # Round the far end of the tongue
        tongue = tongue.edges("|Z and >X").fillet(self.tongue_width / 2.0 - 0.5)

        # Mounting hole centered in the tongue
        hole_center_x = self.tongue_length / 2.0
        tongue = (
            tongue
            .faces(">Z")
            .workplane()
            .center(hole_center_x - self.tongue_length / 2.0, 0)
            .hole(self.hole_diameter)
        )

        # ------------------------------------------------------------------
        # Transition zone: tapered solid from rectangular tongue end to
        # circular barrel. Approximated as a simple loft.
        # ------------------------------------------------------------------
        # Rectangular profile at tongue end (at X=0)
        transition_start_x = 0.0
        transition_end_x = -self.transition_length

        rect_half_w = self.tongue_width / 2.0
        rect_half_h = self.tongue_thickness / 2.0

        transition = (
            cq.Workplane("YZ")
            .rect(self.tongue_width, self.tongue_thickness)
            .workplane(offset=-self.transition_length)
            .circle(bod / 2.0)
            .loft()
            .translate((-self.transition_length, 0, 0))
        )

        # ------------------------------------------------------------------
        # Barrel: hollow cylinder for crimping onto wire
        # Extends along -X from the transition
        # ------------------------------------------------------------------
        barrel_start_x = -self.transition_length
        barrel = (
            cq.Workplane("YZ")
            .circle(bod / 2.0)
            .circle(barrel_ir)
            .extrude(self.barrel_length)
            .translate((-self.transition_length - self.barrel_length, 0, 0))
        )

        # ------------------------------------------------------------------
        # Combine all parts
        # ------------------------------------------------------------------
        result = tongue.union(transition).union(barrel)

        return result
