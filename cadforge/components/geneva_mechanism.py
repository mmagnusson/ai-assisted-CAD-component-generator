"""Geneva mechanism component."""

import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class GenevaMechanism(Component):
    """Geneva mechanism: driven wheel with radial slots and driver disc with pin.

    The driven wheel has radial slots cut from the edge toward center, with
    concave locking arcs between slots. The driver disc has a pin at the
    specified radius. Both parts are built in their meshed position.
    """

    name: str = "geneva_mechanism"
    wheel_diameter: float = 80.0
    slot_count: int = 4
    driver_pin_radius: float = 30.0
    slot_width: float = 6.0
    slot_depth: float = 35.0
    wheel_thickness: float = 8.0
    driver_thickness: float = 8.0
    pin_diameter: float = 5.0
    center_distance: float = 0.0

    def build(self) -> cq.Workplane:
        n = self.slot_count
        wheel_r = self.wheel_diameter / 2.0

        # Auto-calculate center distance if not provided
        cd = self.center_distance
        if cd <= 0:
            cd = self.driver_pin_radius / math.sin(math.pi / n)

        # --- Driven wheel (Geneva wheel) ---
        driven = (
            cq.Workplane("XY")
            .cylinder(self.wheel_thickness, wheel_r, centered=(True, True, True))
        )

        # Center bore
        driven = (
            driven
            .faces(">Z")
            .workplane()
            .hole(self.pin_diameter * 1.5, self.wheel_thickness)
        )

        # Cut radial slots
        for i in range(n):
            angle = i * (2.0 * math.pi / n)
            angle_deg = math.degrees(angle)

            # Slot is a rectangular cut from near-center outward past the edge
            slot_start = self.pin_diameter  # don't cut into center bore
            slot_length = self.slot_depth

            slot = (
                cq.Workplane("XY")
                .box(slot_width_actual := self.slot_width,
                     slot_length,
                     self.wheel_thickness + 2,
                     centered=(True, False, True))
                .translate((0, wheel_r - self.slot_depth, 0))
            )
            slot = slot.rotate((0, 0, 0), (0, 0, 1), angle_deg)
            driven = driven.cut(slot)

        # Cut concave locking arcs between slots.
        # The locking arc radius equals the driver_pin_radius.
        # The arc is centered at the center_distance from the driven wheel center,
        # and removes material between adjacent slots.
        lock_arc_r = self.driver_pin_radius
        # The driver center is at (center_distance, 0). The locking arc
        # on the driven wheel is cut by a cylinder at the driver center position.
        # We cut away material outside the locking arc between each pair of slots.
        half_slot_angle = math.pi / n
        for i in range(n):
            mid_angle = (i + 0.5) * (2.0 * math.pi / n)
            # The cut removes the outer rim between two adjacent slots,
            # replacing the flat edge with a concave arc.
            cut_cx = wheel_r * 0.85 * math.cos(mid_angle)
            cut_cy = wheel_r * 0.85 * math.sin(mid_angle)

            # Small cylindrical cut to create the concave recess
            arc_cut_r = wheel_r * 0.15
            arc_cut = (
                cq.Workplane("XY")
                .transformed(offset=cq.Vector(cut_cx, cut_cy, 0))
                .cylinder(self.wheel_thickness + 2, arc_cut_r,
                          centered=(True, True, True))
            )
            driven = driven.cut(arc_cut)

        # --- Driver disc ---
        driver_r = cd - wheel_r + self.driver_pin_radius * 0.6
        # Ensure driver is at least big enough to hold the pin
        driver_r = max(driver_r, self.driver_pin_radius + self.pin_diameter)

        driver = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(cd, 0, 0))
            .cylinder(self.driver_thickness, driver_r,
                      centered=(True, True, True))
        )

        # Center bore on driver
        driver = driver.cut(
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(cd, 0, 0))
            .cylinder(self.driver_thickness + 2, self.pin_diameter * 0.75,
                      centered=(True, True, True))
        )

        # Pin on the driver disc
        pin = (
            cq.Workplane("XY")
            .transformed(offset=cq.Vector(
                cd + self.driver_pin_radius, 0, 0
            ))
            .cylinder(self.wheel_thickness + self.driver_thickness,
                      self.pin_diameter / 2.0,
                      centered=(True, True, True))
        )

        # Combine everything
        result = driven.union(driver).union(pin)

        return result
