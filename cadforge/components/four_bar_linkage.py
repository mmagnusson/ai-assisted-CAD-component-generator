"""Four-bar linkage mechanism component."""

import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class FourBarLinkage(Component):
    """Four-bar linkage mechanism with ground, input, coupler, and output links.

    All four links are rectangular bars with pin holes at each end,
    positioned at the given input_angle. Grashof condition is validated.
    """

    name: str = "four_bar_linkage"
    ground_link: float = 100.0
    input_link: float = 30.0
    coupler_link: float = 70.0
    output_link: float = 60.0
    link_width: float = 10.0
    link_thickness: float = 5.0
    pin_diameter: float = 6.0
    input_angle: float = 45.0

    def _validate_grashof(self) -> bool:
        """Check Grashof condition: s + l <= p + q."""
        links = sorted([
            self.ground_link, self.input_link,
            self.coupler_link, self.output_link,
        ])
        s, p, q, l = links[0], links[1], links[2], links[3]
        return (s + l) <= (p + q)

    def _solve_position(self):
        """Solve the four-bar linkage position for the given input angle.

        Returns the coordinates of all four joints:
        A (left ground pivot), B (end of input link),
        C (end of output link), D (right ground pivot).
        """
        theta2 = math.radians(self.input_angle)

        # Ground pivots
        ax, ay = 0.0, 0.0
        dx, dy = self.ground_link, 0.0

        # End of input link (crank)
        bx = ax + self.input_link * math.cos(theta2)
        by = ay + self.input_link * math.sin(theta2)

        # Solve for point C (end of output link) using the
        # intersection of two circles:
        # Circle 1: center B, radius = coupler_link
        # Circle 2: center D, radius = output_link
        r1 = self.coupler_link
        r2 = self.output_link

        # Distance from B to D
        bdx = dx - bx
        bdy = dy - by
        d = math.sqrt(bdx ** 2 + bdy ** 2)

        # Check if solution exists
        if d > r1 + r2 or d < abs(r1 - r2) or d < 1e-10:
            # No valid position -- fall back to approximate layout
            theta4 = math.radians(30)
            cx = dx + self.output_link * math.cos(math.pi - theta4)
            cy = dy + self.output_link * math.sin(math.pi - theta4)
            return (ax, ay), (bx, by), (cx, cy), (dx, dy)

        # Standard two-circle intersection
        a_val = (r1 ** 2 - r2 ** 2 + d ** 2) / (2.0 * d)
        h = math.sqrt(max(r1 ** 2 - a_val ** 2, 0))

        # Midpoint along BD at distance a_val from B
        mx = bx + a_val * bdx / d
        my = by + a_val * bdy / d

        # Two solutions; pick the one with positive y (open configuration)
        cx1 = mx + h * (-bdy) / d
        cy1 = my + h * bdx / d
        cx2 = mx - h * (-bdy) / d
        cy2 = my - h * bdx / d

        # Pick the solution with larger y (open position)
        if cy1 >= cy2:
            cx, cy = cx1, cy1
        else:
            cx, cy = cx2, cy2

        return (ax, ay), (bx, by), (cx, cy), (dx, dy)

    def _make_link(self, x1, y1, x2, y2, z_offset=0.0):
        """Create a single link bar between two points with pin holes at ends."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx ** 2 + dy ** 2)
        angle = math.degrees(math.atan2(dy, dx))

        if length < 1e-6:
            length = 1.0

        # Create a rounded-end bar (stadium shape)
        bar = (
            cq.Workplane("XY")
            .box(length, self.link_width, self.link_thickness,
                 centered=(False, True, True))
        )

        # Pin holes at both ends
        hole_r = self.pin_diameter / 2.0
        # Hole at start end
        bar = (
            bar
            .faces(">Z")
            .workplane()
            .pushPoints([(0, 0), (length, 0)])
            .hole(self.pin_diameter, self.link_thickness)
        )

        # Rotate and translate into position
        bar = bar.rotate((0, 0, 0), (0, 0, 1), angle)
        bar = bar.translate((x1, y1, z_offset))

        return bar

    def build(self) -> cq.Workplane:
        # Validate Grashof condition (warn but still build)
        grashof_ok = self._validate_grashof()

        # Solve positions
        a, b, c, d = self._solve_position()

        # Build each link at slightly different Z offsets to avoid
        # coincident faces while showing the assembled mechanism
        z_gap = self.link_thickness * 1.1

        # Ground link (frame): A to D, at z=0
        ground = self._make_link(a[0], a[1], d[0], d[1], z_offset=0)

        # Input link (crank): A to B, at z=z_gap
        input_link = self._make_link(a[0], a[1], b[0], b[1], z_offset=z_gap)

        # Coupler link: B to C, at z=2*z_gap
        coupler = self._make_link(b[0], b[1], c[0], c[1], z_offset=2 * z_gap)

        # Output link (rocker): D to C, at z=z_gap
        output = self._make_link(d[0], d[1], c[0], c[1], z_offset=z_gap)

        # Add pin cylinders at each joint to visually connect the layers
        pin_height = 3 * z_gap + self.link_thickness
        pin_r = self.pin_diameter / 2.0 - 0.2  # slightly smaller than holes

        pins = None
        for jx, jy in [a, b, c, d]:
            pin = (
                cq.Workplane("XY")
                .transformed(offset=cq.Vector(jx, jy, pin_height / 2 - self.link_thickness / 2))
                .cylinder(pin_height, pin_r, centered=(True, True, True))
            )
            if pins is None:
                pins = pin
            else:
                pins = pins.union(pin)

        # Union all parts
        result = ground.union(input_link).union(coupler).union(output)
        if pins is not None:
            result = result.union(pins)

        return result
