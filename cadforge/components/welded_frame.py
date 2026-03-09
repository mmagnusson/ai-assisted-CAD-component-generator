import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


def _hollow_rect_tube(
    width: float, height: float, wall: float, length: float
) -> cq.Workplane:
    """Create a hollow rectangular tube along Z, centred at origin."""
    outer = cq.Workplane("XY").box(width, height, length)
    inner = cq.Workplane("XY").box(
        width - 2 * wall, height - 2 * wall, length + 2
    )
    return outer.cut(inner)


def _right_triangle_prism(
    leg_a: float, leg_b: float, thickness: float
) -> cq.Workplane:
    """Return a right-triangle prism (thickness along Z).

    The right angle is at the origin, with legs along +X and +Y.
    """
    pts = [(0, 0), (leg_a, 0), (0, leg_b), (0, 0)]
    return (
        cq.Workplane("XY")
        .polyline(pts)
        .close()
        .extrude(thickness)
        .translate((0, 0, -thickness / 2))
    )


@dataclass
class WeldedFrame(Component):
    """A rectangular welded tube frame/chassis with gussets and mounting plates."""

    name: str = "welded_frame"
    frame_length: float = 500.0
    frame_width: float = 300.0
    frame_height: float = 200.0
    tube_width: float = 50.0
    tube_height: float = 50.0
    tube_wall_thickness: float = 3.0
    gusset_thickness: float = 5.0
    gusset_size: float = 40.0
    mounting_plate_thickness: float = 6.0
    mounting_plate_width: float = 80.0
    mounting_hole_diameter: float = 10.0

    def build(self) -> cq.Workplane:
        tw = self.tube_width
        th = self.tube_height
        wall = self.tube_wall_thickness
        fl = self.frame_length
        fw = self.frame_width
        fh = self.frame_height

        result = cq.Workplane("XY").box(0.01, 0.01, 0.01)  # seed solid

        # Corner post positions (centres at corners, bottom at z=0)
        corner_xs = [-fl / 2 + tw / 2, fl / 2 - tw / 2]
        corner_ys = [-fw / 2 + th / 2, fw / 2 - th / 2]

        # --- Vertical corner posts (along Z) ---
        for cx in corner_xs:
            for cy in corner_ys:
                post = _hollow_rect_tube(tw, th, wall, fh).translate(
                    (cx, cy, fh / 2)
                )
                result = result.union(post)

        # --- Bottom rails (z centred at tube_height/2) ---
        rail_z_bot = th / 2
        # Rails along X (length direction) at each Y side
        rail_len_x = fl - 2 * tw  # span between posts
        for cy in corner_ys:
            rail = _hollow_rect_tube(rail_len_x, th, wall, tw).translate(
                (0, cy, rail_z_bot)
            )
            # Rail along X: length is X, so tube runs along X -> rotate so
            # the extrude direction (Z) becomes X.
            rail = (
                _hollow_rect_tube(tw, th, wall, rail_len_x)
                .rotateAboutCenter((0, 1, 0), 90)
                .translate((0, cy, rail_z_bot))
            )
            result = result.union(rail)

        # Rails along Y (width direction) at each X side
        rail_len_y = fw - 2 * th
        for cx in corner_xs:
            rail = (
                _hollow_rect_tube(tw, th, wall, rail_len_y)
                .rotateAboutCenter((1, 0, 0), 90)
                .translate((cx, 0, rail_z_bot))
            )
            result = result.union(rail)

        # --- Top rails (z centred at frame_height - tube_height/2) ---
        rail_z_top = fh - th / 2
        for cy in corner_ys:
            rail = (
                _hollow_rect_tube(tw, th, wall, rail_len_x)
                .rotateAboutCenter((0, 1, 0), 90)
                .translate((0, cy, rail_z_top))
            )
            result = result.union(rail)

        for cx in corner_xs:
            rail = (
                _hollow_rect_tube(tw, th, wall, rail_len_y)
                .rotateAboutCenter((1, 0, 0), 90)
                .translate((cx, 0, rail_z_top))
            )
            result = result.union(rail)

        # --- Gusset plates at bottom corners ---
        gs = self.gusset_size
        gt = self.gusset_thickness
        for ix, cx in enumerate(corner_xs):
            for iy, cy in enumerate(corner_ys):
                # X-direction gusset (vertical triangle in XZ plane)
                x_sign = 1 if ix == 0 else -1
                y_sign = 1 if iy == 0 else -1
                gusset_xz = (
                    _right_triangle_prism(gs, gs, gt)
                    .rotateAboutCenter((1, 0, 0), 90)
                )
                # Position: at post corner, oriented inward
                gx = cx + x_sign * tw / 2
                gy = cy
                gz = th
                if x_sign < 0:
                    gusset_xz = gusset_xz.mirror("YZ")
                gusset_xz = gusset_xz.translate((gx, gy, gz))
                result = result.union(gusset_xz)

                # Y-direction gusset (vertical triangle in YZ plane)
                gusset_yz = (
                    _right_triangle_prism(gs, gs, gt)
                    .rotateAboutCenter((0, 1, 0), -90)
                    .rotateAboutCenter((0, 0, 1), 90)
                )
                gx2 = cx
                gy2 = cy + y_sign * th / 2
                gz2 = th
                if y_sign < 0:
                    gusset_yz = gusset_yz.mirror("XZ")
                gusset_yz = gusset_yz.translate((gx2, gy2, gz2))
                result = result.union(gusset_yz)

        # --- Mounting plates at the bottom of each post ---
        mpw = self.mounting_plate_width
        mpt = self.mounting_plate_thickness
        mhd = self.mounting_hole_diameter
        for cx in corner_xs:
            for cy in corner_ys:
                plate = (
                    cq.Workplane("XY")
                    .box(mpw, mpw, mpt)
                    .faces(">Z")
                    .workplane()
                    .hole(mhd)
                    .translate((cx, cy, -mpt / 2))
                )
                result = result.union(plate)

        return result
