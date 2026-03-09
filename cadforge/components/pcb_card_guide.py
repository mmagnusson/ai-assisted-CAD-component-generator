import math
from dataclasses import dataclass, field
import cadquery as cq
from cadforge.core import Component


@dataclass
class PCBCardGuide(Component):
    """A DIN 41612-style PCB card guide rail."""

    name: str = "pcb_card_guide"
    rail_length: float = 100.0
    rail_height: float = 10.0
    rail_width: float = 8.0
    slot_width: float = 1.6
    slot_depth: float = 6.0
    slot_offset: float = 0.0
    retention_tab_count: int = 3
    retention_tab_height: float = 1.5
    mounting_tab_width: float = 12.0
    mounting_tab_thickness: float = 2.0
    mounting_hole_diameter: float = 3.0

    def build(self) -> cq.Workplane:
        # ------------------------------------------------------------------
        # Main rail body: extruded along X axis
        # ------------------------------------------------------------------
        rail = (
            cq.Workplane("YZ")
            .rect(self.rail_width, self.rail_height)
            .extrude(self.rail_length)
        )

        # ------------------------------------------------------------------
        # Card slot: groove running full length along the top face
        # Slot is centered on the rail width with optional offset
        # ------------------------------------------------------------------
        slot_center_y = self.slot_offset
        slot = (
            cq.Workplane("YZ")
            .center(slot_center_y, self.rail_height / 2.0 - self.slot_depth / 2.0)
            .rect(self.slot_width, self.slot_depth)
            .extrude(self.rail_length)
        )
        rail = rail.cut(slot)

        # ------------------------------------------------------------------
        # Retention tabs: small bumps inside the slot at regular intervals
        # ------------------------------------------------------------------
        if self.retention_tab_count > 0:
            tab_width = self.slot_width * 0.3
            tab_length = 2.0  # along rail length
            spacing = self.rail_length / (self.retention_tab_count + 1)

            tab_positions = []
            for i in range(self.retention_tab_count):
                x_pos = spacing * (i + 1)
                tab_positions.append(x_pos)

            for x_pos in tab_positions:
                # Tab on one side of the slot
                tab = (
                    cq.Workplane("XY")
                    .box(
                        tab_length,
                        tab_width,
                        self.retention_tab_height,
                        centered=(True, True, False),
                    )
                    .translate((
                        x_pos,
                        slot_center_y + self.slot_width / 2.0,
                        self.rail_height / 2.0 - self.slot_depth,
                    ))
                )
                rail = rail.union(tab)

                # Tab on the other side
                tab2 = (
                    cq.Workplane("XY")
                    .box(
                        tab_length,
                        tab_width,
                        self.retention_tab_height,
                        centered=(True, True, False),
                    )
                    .translate((
                        x_pos,
                        slot_center_y - self.slot_width / 2.0 - tab_width,
                        self.rail_height / 2.0 - self.slot_depth,
                    ))
                )
                rail = rail.union(tab2)

        # ------------------------------------------------------------------
        # Mounting tabs at each end: wider sections with screw holes
        # ------------------------------------------------------------------
        for x_pos in [0.0, self.rail_length]:
            tab = (
                cq.Workplane("YZ")
                .rect(self.mounting_tab_width, self.rail_height)
                .extrude(self.mounting_tab_thickness)
                .translate((x_pos - self.mounting_tab_thickness / 2.0, 0, 0))
            )
            rail = rail.union(tab)

            # Mounting hole through the tab (vertical hole)
            hole_cut = (
                cq.Workplane("XY")
                .transformed(offset=cq.Vector(
                    x_pos,
                    0,
                    0,
                ))
                .circle(self.mounting_hole_diameter / 2.0)
                .extrude(self.rail_height, both=True)
            )
            rail = rail.cut(hole_cut)

        return rail
