import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


@dataclass
class PressureVessel(Component):
    """ASME-style pressure vessel: cylindrical shell + hemispherical heads + nozzle."""

    name: str = "pressure_vessel"
    inner_diameter: float = 500.0
    shell_length: float = 800.0
    shell_thickness: float = 10.0
    head_thickness: float = 10.0
    nozzle_od: float = 60.0
    nozzle_thickness: float = 5.0
    nozzle_height: float = 80.0
    nozzle_position: float = 0.5
    reinforcement_pad_od: float = 120.0
    reinforcement_pad_thickness: float = 10.0
    support_saddle_width: float = 100.0

    def build(self) -> cq.Workplane:
        ri = self.inner_diameter / 2
        ro = ri + self.shell_thickness
        sl = self.shell_length

        # --- Build shell + heads as a single revolved profile ---
        # Revolve a cross-section around the Z axis to get shell + hemispheres
        # Profile: outer boundary (hemispherical caps + cylinder), minus inner
        # We'll build the outer solid and subtract the inner solid.

        # Outer solid: cylinder with hemispherical end caps
        # Build via revolution of a 2D profile in the XZ plane around Z axis
        # Profile goes: bottom of bottom hemisphere -> up the side -> over top hemisphere
        outer_pts = [
            (0, 0),
            (ro, 0),
            (ro, sl),
        ]
        # Outer body = cylinder + two sphere caps
        outer_cyl = (
            cq.Workplane("XY")
            .circle(ro)
            .extrude(sl)
        )
        # Top hemisphere
        top_sphere = cq.Workplane("XY").transformed(offset=(0, 0, sl)).sphere(ro)
        # Clip to upper half
        top_clip = cq.Workplane("XY").box(ro * 3, ro * 3, ro * 2).translate((0, 0, sl - ro))
        top_cap = top_sphere.cut(top_clip)

        # Bottom hemisphere
        bot_sphere = cq.Workplane("XY").sphere(ro)
        bot_clip = cq.Workplane("XY").box(ro * 3, ro * 3, ro * 2).translate((0, 0, ro))
        bot_cap = bot_sphere.cut(bot_clip)

        outer = outer_cyl.union(top_cap).union(bot_cap)

        # Inner void
        ri_head = ri
        inner_cyl = (
            cq.Workplane("XY")
            .circle(ri_head)
            .extrude(sl)
        )
        top_sphere_i = cq.Workplane("XY").transformed(offset=(0, 0, sl)).sphere(ri_head)
        top_clip_i = cq.Workplane("XY").box(ri_head * 3, ri_head * 3, ri_head * 2).translate((0, 0, sl - ri_head))
        top_cap_i = top_sphere_i.cut(top_clip_i)

        bot_sphere_i = cq.Workplane("XY").sphere(ri_head)
        bot_clip_i = cq.Workplane("XY").box(ri_head * 3, ri_head * 3, ri_head * 2).translate((0, 0, ri_head))
        bot_cap_i = bot_sphere_i.cut(bot_clip_i)

        inner = inner_cyl.union(top_cap_i).union(bot_cap_i)

        result = outer.cut(inner)

        # --- Nozzle (radial, along +X) ---
        nz_od = self.nozzle_od
        nz_id = nz_od - 2 * self.nozzle_thickness
        nz_h = self.nozzle_height
        nz_z = self.nozzle_position * sl  # position along shell

        # Nozzle tube from center outward along X
        nozzle_outer = (
            cq.Workplane("YZ")
            .circle(nz_od / 2)
            .extrude(ro + nz_h)
            .translate((0, 0, nz_z))
        )
        nozzle_bore = (
            cq.Workplane("YZ")
            .circle(nz_id / 2)
            .extrude(ro + nz_h + 2)
            .translate((-1, 0, nz_z))
        )
        nozzle = nozzle_outer.cut(nozzle_bore)

        # Cut bore through shell wall
        shell_bore = (
            cq.Workplane("YZ")
            .circle(nz_id / 2)
            .extrude(ro + 2)
            .translate((-1, 0, nz_z))
        )
        result = result.cut(shell_bore).union(nozzle)

        # --- Reinforcement pad (annular ring at nozzle base) ---
        rp_od = self.reinforcement_pad_od
        rp_t = self.reinforcement_pad_thickness
        pad = (
            cq.Workplane("YZ")
            .circle(rp_od / 2)
            .circle(nz_od / 2)
            .extrude(rp_t)
            .translate((ro, 0, nz_z))
        )
        result = result.union(pad)

        # --- Two saddle supports ---
        sw = self.support_saddle_width
        saddle_h = ro * 0.35
        saddle_w = ro * 1.2
        for frac in (0.25, 0.75):
            sz = frac * sl
            block = (
                cq.Workplane("XY")
                .rect(saddle_w, sw)
                .extrude(saddle_h)
                .translate((0, 0, -ro - saddle_h))
                .translate((0, 0, sz))
            )
            # Cradle cutout matching vessel OD
            cradle = (
                cq.Workplane("XY")
                .circle(ro + 0.5)
                .extrude(sw + 2)
                .rotateAboutCenter((1, 0, 0), 90)
                .translate((0, 0, sz))
            )
            block = block.cut(cradle)
            result = result.union(block)

        return result
