import math
from dataclasses import dataclass, field
import cadquery as cq
from cadforge.core import Component


@dataclass
class CircularConnector(Component):
    """A MIL-DTL-38999-style circular connector shell."""

    name: str = "circular_connector"
    shell_diameter: float = 25.0
    shell_length: float = 30.0
    flange_diameter: float = 35.0
    flange_thickness: float = 3.0
    bore_diameter: float = 18.0
    num_pins: int = 12
    pin_circle_diameter: float = 14.0
    keyway_width: float = 3.0
    keyway_depth: float = 2.0
    coupling_thread_od: float = 28.0
    coupling_thread_length: float = 8.0
    mounting_hole_count: int = 4
    mounting_hole_diameter: float = 3.0
    mounting_circle_diameter: float = 32.0

    def build(self) -> cq.Workplane:
        shell_r = self.shell_diameter / 2.0
        bore_r = self.bore_diameter / 2.0

        # ------------------------------------------------------------------
        # Main cylindrical shell body
        # ------------------------------------------------------------------
        body = (
            cq.Workplane("XY")
            .circle(shell_r)
            .extrude(self.shell_length)
        )

        # ------------------------------------------------------------------
        # Central bore through the entire body
        # ------------------------------------------------------------------
        body = (
            body
            .faces(">Z")
            .workplane()
            .hole(self.bore_diameter, self.shell_length)
        )

        # ------------------------------------------------------------------
        # Flange at the rear end (Z=0)
        # ------------------------------------------------------------------
        flange = (
            cq.Workplane("XY")
            .circle(self.flange_diameter / 2.0)
            .extrude(self.flange_thickness)
            .translate((0, 0, -self.flange_thickness))
        )
        # Bore through flange
        flange = (
            flange
            .faces("<Z")
            .workplane()
            .hole(self.bore_diameter)
        )

        # Mounting holes on the flange
        if self.mounting_hole_count > 0:
            mount_r = self.mounting_circle_diameter / 2.0
            mount_pts = [
                (
                    mount_r * math.cos(2 * math.pi * i / self.mounting_hole_count),
                    mount_r * math.sin(2 * math.pi * i / self.mounting_hole_count),
                )
                for i in range(self.mounting_hole_count)
            ]
            flange = (
                flange
                .faces("<Z")
                .workplane()
                .pushPoints(mount_pts)
                .hole(self.mounting_hole_diameter)
            )

        body = body.union(flange)

        # ------------------------------------------------------------------
        # Coupling thread region at the front (plain cylinder, no threads)
        # ------------------------------------------------------------------
        coupling = (
            cq.Workplane("XY")
            .circle(self.coupling_thread_od / 2.0)
            .circle(bore_r)
            .extrude(self.coupling_thread_length)
            .translate((0, 0, self.shell_length))
        )
        body = body.union(coupling)

        # ------------------------------------------------------------------
        # Keyway: rectangular slot cut into the bore at the front face
        # ------------------------------------------------------------------
        keyway_block = (
            cq.Workplane("XY")
            .box(
                self.keyway_width,
                self.keyway_depth,
                self.coupling_thread_length + 2,
                centered=(True, True, False),
            )
            .translate((
                0,
                bore_r + self.keyway_depth / 2.0 - self.keyway_depth,
                self.shell_length - 1,
            ))
        )
        body = body.cut(keyway_block)

        # ------------------------------------------------------------------
        # Pin holes on the bore face (rear face, Z=0 side)
        # ------------------------------------------------------------------
        if self.num_pins > 0:
            pin_r = self.pin_circle_diameter / 2.0
            pin_hole_d = 1.0
            pin_depth = 4.0
            pin_pts = [
                (
                    pin_r * math.cos(2 * math.pi * i / self.num_pins),
                    pin_r * math.sin(2 * math.pi * i / self.num_pins),
                )
                for i in range(self.num_pins)
            ]
            body = (
                body
                .faces("<Z")
                .workplane()
                .pushPoints(pin_pts)
                .hole(pin_hole_d, pin_depth)
            )

        return body
