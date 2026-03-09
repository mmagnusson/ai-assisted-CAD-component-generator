import math
from dataclasses import dataclass, field

import cadquery as cq

from cadforge.core import Component


def _rect_member(length: float, width: float, height: float, thickness: float) -> cq.Workplane:
    """Create a hollow rectangular tube member along Z axis, centred at origin.

    If thickness <= 0 or would leave no interior, create a solid bar.
    """
    if thickness <= 0 or width <= 2 * thickness or height <= 2 * thickness:
        return cq.Workplane("XY").box(width, height, length)
    outer = cq.Workplane("XY").box(width, height, length)
    inner = cq.Workplane("XY").box(
        width - 2 * thickness, height - 2 * thickness, length + 2
    )
    return outer.cut(inner)


@dataclass
class TrussStructure(Component):
    """A planar Pratt truss structure with rectangular tube members."""

    name: str = "truss_structure"
    span: float = 1000.0
    height: float = 200.0
    num_panels: int = 6
    chord_width: float = 30.0
    chord_height: float = 30.0
    chord_thickness: float = 3.0
    diagonal_width: float = 20.0
    diagonal_height: float = 20.0
    diagonal_thickness: float = 2.0
    truss_depth: float = 30.0
    gusset_plate_thickness: float = 5.0
    gusset_plate_size: float = 50.0

    def build(self) -> cq.Workplane:
        span = self.span
        h = self.height
        n = self.num_panels
        panel_len = span / n

        cw = self.chord_width
        ch = self.chord_height
        ct = self.chord_thickness
        dw = self.diagonal_width
        dh = self.diagonal_height
        dt = self.diagonal_thickness
        gpt = self.gusset_plate_thickness
        gps = self.gusset_plate_size

        # We build the truss in the XZ plane, with X along the span and
        # Z as the vertical. Y is the depth/thickness direction.
        # Members created along their local Z then rotated into place.

        result = cq.Workplane("XY").box(0.01, 0.01, 0.01)  # seed solid

        # --- Top chord: full span along X at z = height ---
        top_chord = (
            _rect_member(span, cw, ch, ct)
            .rotateAboutCenter((0, 1, 0), 90)
            .translate((span / 2, 0, h))
        )
        result = result.union(top_chord)

        # --- Bottom chord: full span along X at z = 0 ---
        bot_chord = (
            _rect_member(span, cw, ch, ct)
            .rotateAboutCenter((0, 1, 0), 90)
            .translate((span / 2, 0, 0))
        )
        result = result.union(bot_chord)

        # --- Vertical members at each panel point ---
        for i in range(n + 1):
            x = i * panel_len
            vert = (
                _rect_member(h, dw, dh, dt)
                .translate((x, 0, h / 2))
            )
            result = result.union(vert)

        # --- Diagonal members (Pratt pattern) ---
        # In a Pratt truss, diagonals slope toward the centre from
        # bottom chord to top chord. We alternate direction per panel.
        diag_len = math.sqrt(panel_len ** 2 + h ** 2)
        diag_angle = math.degrees(math.atan2(h, panel_len))

        for i in range(n):
            x_left = i * panel_len
            x_right = (i + 1) * panel_len
            # Pratt pattern: in the left half, diagonals go from bottom-left
            # to top-right; in the right half, bottom-right to top-left.
            if i < n / 2:
                # Diagonal from (x_left, 0) to (x_right, h)
                cx = (x_left + x_right) / 2
                cz = h / 2
                diag = (
                    _rect_member(diag_len, dw, dh, dt)
                    .rotateAboutCenter((0, 1, 0), -diag_angle)
                    .translate((cx, 0, cz))
                )
            else:
                # Diagonal from (x_right, 0) to (x_left, h)
                cx = (x_left + x_right) / 2
                cz = h / 2
                diag = (
                    _rect_member(diag_len, dw, dh, dt)
                    .rotateAboutCenter((0, 1, 0), diag_angle)
                    .translate((cx, 0, cz))
                )
            result = result.union(diag)

        # --- Gusset plates at each node ---
        # Place flat rectangular gusset plates (XZ plane) at top and bottom
        # chord panel points.
        for i in range(n + 1):
            x = i * panel_len
            # Bottom gusset
            bot_gusset = (
                cq.Workplane("XZ")
                .center(x, 0)
                .rect(gps, gps)
                .extrude(gpt)
                .translate((0, -gpt / 2, 0))
            )
            result = result.union(bot_gusset)

            # Top gusset
            top_gusset = (
                cq.Workplane("XZ")
                .center(x, h)
                .rect(gps, gps)
                .extrude(gpt)
                .translate((0, -gpt / 2, 0))
            )
            result = result.union(top_gusset)

        return result
