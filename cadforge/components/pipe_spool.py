import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class PipeSpool(Component):
    """A piping spool piece: straight pipe + 90-degree elbow + flange."""

    name: str = "pipe_spool"
    pipe_od: float = 60.3
    pipe_wall: float = 3.9
    straight_length: float = 200.0
    elbow_radius: float = 76.0
    flange_od: float = 125.0
    flange_thickness: float = 16.0
    bolt_circle_diameter: float = 99.0
    bolt_count: int = 4
    bolt_hole_diameter: float = 16.0
    flange_id: float = 0.0

    def build(self) -> cq.Workplane:
        od = self.pipe_od
        wall = self.pipe_wall
        pipe_id = od - 2 * wall
        flange_bore = self.flange_id if self.flange_id > 0 else pipe_id

        # --- Straight pipe section along Z, bottom at z=0 ---
        straight_outer = (
            cq.Workplane("XY")
            .circle(od / 2)
            .extrude(self.straight_length)
        )
        straight_inner = (
            cq.Workplane("XY")
            .circle(pipe_id / 2)
            .extrude(self.straight_length + 1)
            .translate((0, 0, -0.5))
        )
        straight = straight_outer.cut(straight_inner)

        # --- 90-degree elbow at the top of the straight section ---
        # The elbow bends from the +Z direction toward the +X direction.
        # Centre of the bend arc is at (elbow_radius, 0, straight_length).
        # We sweep a pipe-cross-section ring along a 90-degree arc.
        er = self.elbow_radius

        # Create the arc path as a wire in the XZ plane.
        # Arc goes from (0, 0, straight_length) bending toward +X.
        arc_path = (
            cq.Workplane("XZ")
            .center(er, self.straight_length)
            .threePointArc((er - er * math.cos(math.pi / 4),
                            er * math.sin(math.pi / 4)),
                           (er, er))
            .wire()
        )

        # Sweep the pipe cross-section (annular ring) along the arc.
        elbow_outer = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, self.straight_length))
            .circle(od / 2)
            .sweep(arc_path, isFrenet=True)
        )
        elbow_inner = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(0, 0, self.straight_length))
            .circle(pipe_id / 2)
            .sweep(arc_path, isFrenet=True)
        )
        elbow = elbow_outer.cut(elbow_inner)

        # --- Weld neck flange at the bottom (z = -flange_thickness to z = 0) ---
        ft = self.flange_thickness
        flange_disc = (
            cq.Workplane("XY")
            .circle(self.flange_od / 2)
            .extrude(-ft)
        )
        flange_bore_cut = (
            cq.Workplane("XY")
            .circle(flange_bore / 2)
            .extrude(-ft - 1)
            .translate((0, 0, 0.5))
        )
        flange = flange_disc.cut(flange_bore_cut)

        # Bolt holes on bolt circle
        bcd = self.bolt_circle_diameter
        bhd = self.bolt_hole_diameter
        bolt_pts = []
        for i in range(self.bolt_count):
            angle = 2 * math.pi * i / self.bolt_count
            bx = bcd / 2 * math.cos(angle)
            by = bcd / 2 * math.sin(angle)
            bolt_pts.append((bx, by))

        bolt_holes = (
            cq.Workplane("XY")
            .pushPoints(bolt_pts)
            .circle(bhd / 2)
            .extrude(-ft - 1)
            .translate((0, 0, 0.5))
        )
        flange = flange.cut(bolt_holes)

        # --- Union everything ---
        result = straight.union(elbow).union(flange)

        return result
