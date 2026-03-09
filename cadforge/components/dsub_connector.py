import math
from dataclasses import dataclass, field
import cadquery as cq
from cadforge.core import Component


# Standard D-Sub dimensions by pin count
_DSUB_STANDARDS = {
    9:  {"shell_width": 16.92, "mounting_spacing": 24.99},
    15: {"shell_width": 23.52, "mounting_spacing": 33.32},
    25: {"shell_width": 33.32, "mounting_spacing": 41.28},
    37: {"shell_width": 43.74, "mounting_spacing": 51.70},
}


@dataclass
class DSubConnector(Component):
    """A D-subminiature connector shell/housing with standard pin configurations."""

    name: str = "dsub_connector"
    pin_count: int = 9
    gender: str = "male"
    mounting_style: str = "panel"
    shell_width: float = 0.0
    shell_height: float = 0.0
    shell_depth: float = 12.0
    flange_width: float = 0.0
    flange_height: float = 16.0
    flange_thickness: float = 2.0
    mounting_hole_diameter: float = 3.0
    mounting_hole_spacing: float = 0.0

    def _resolve_auto(self):
        """Resolve auto-calculated dimensions from pin_count."""
        std = _DSUB_STANDARDS.get(self.pin_count, _DSUB_STANDARDS[9])

        shell_width = self.shell_width if self.shell_width > 0 else std["shell_width"]
        mounting_hole_spacing = (
            self.mounting_hole_spacing
            if self.mounting_hole_spacing > 0
            else std["mounting_spacing"]
        )
        # Shell height is typically ~10 mm for standard D-Sub
        shell_height = self.shell_height if self.shell_height > 0 else 10.0
        # Flange width auto: mounting_hole_spacing + 2 * (mounting_hole_diameter + 2)
        flange_width = (
            self.flange_width
            if self.flange_width > 0
            else mounting_hole_spacing + self.mounting_hole_diameter + 6.0
        )
        return shell_width, shell_height, flange_width, mounting_hole_spacing

    def build(self) -> cq.Workplane:
        sw, sh, fw, mhs = self._resolve_auto()

        # ------------------------------------------------------------------
        # D-shaped shell profile: rectangle with larger top corner radii
        # and smaller bottom corner radii to approximate the D shape.
        # The top is wider conceptually; we model it as a rounded rect with
        # asymmetric fillets.
        # ------------------------------------------------------------------
        top_radius = sh * 0.35
        bot_radius = sh * 0.15

        # Build the D-profile as a CQ sketch
        half_w = sw / 2.0
        half_h = sh / 2.0

        # Create the shell as a box then fillet edges selectively
        shell = (
            cq.Workplane("XY")
            .box(sw, sh, self.shell_depth, centered=(True, True, False))
        )
        # Fillet the top longitudinal edges (larger radius) and bottom (smaller)
        # Top edges run along Z at Y = +half_h
        shell = (
            shell
            .edges("|Z and >Y")
            .fillet(top_radius)
        )
        shell = (
            shell
            .edges("|Z and <Y")
            .fillet(bot_radius)
        )

        # ------------------------------------------------------------------
        # Flange plate at Z=0
        # ------------------------------------------------------------------
        flange = (
            cq.Workplane("XY")
            .box(fw, self.flange_height, self.flange_thickness, centered=(True, True, False))
            .translate((0, 0, -self.flange_thickness))
        )

        # Cut the D-shaped opening through the flange by subtracting a
        # slightly oversized version of the shell profile
        d_cut = (
            cq.Workplane("XY")
            .box(sw + 0.4, sh + 0.4, self.flange_thickness + 2,
                 centered=(True, True, False))
            .translate((0, 0, -self.flange_thickness - 1))
        )
        d_cut = d_cut.edges("|Z and >Y").fillet(top_radius)
        d_cut = d_cut.edges("|Z and <Y").fillet(bot_radius)
        flange = flange.cut(d_cut)

        # Mounting holes in flange
        flange = (
            flange
            .faces("<Z")
            .workplane()
            .pushPoints([(-mhs / 2.0, 0), (mhs / 2.0, 0)])
            .hole(self.mounting_hole_diameter)
        )

        result = shell.union(flange)

        # ------------------------------------------------------------------
        # Pin wells: small blind holes in the connector face
        # ------------------------------------------------------------------
        pin_diameter = 1.0
        pin_depth = 3.0

        # Standard D-Sub pin arrangement: 2 rows
        # Row counts depend on pin_count
        row_configs = {
            9:  (5, 4),
            15: (8, 7),
            25: (13, 12),
            37: (19, 18),
        }
        top_count, bot_count = row_configs.get(self.pin_count, (5, 4))

        pin_spacing = (sw - 3.0) / max(top_count - 1, 1)
        row_spacing = sh * 0.35

        pin_positions = []
        # Top row
        for i in range(top_count):
            x = -((top_count - 1) * pin_spacing) / 2.0 + i * pin_spacing
            pin_positions.append((x, row_spacing / 2.0))
        # Bottom row
        for i in range(bot_count):
            x = -((bot_count - 1) * pin_spacing) / 2.0 + i * pin_spacing
            pin_positions.append((x, -row_spacing / 2.0))

        if pin_positions:
            result = (
                result
                .faces(">Z")
                .workplane()
                .pushPoints(pin_positions)
                .hole(pin_diameter, pin_depth)
            )

        return result
