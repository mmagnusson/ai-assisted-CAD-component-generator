"""Standard metric fasteners for CAD Forge.

Provides hex bolts (ISO 4014), socket head cap screws (ISO 4762),
hex nuts (ISO 4032), and flat washers (ISO 7089) with correct
dimensions for M2 through M20.

Geometry is envelope-level (no thread modeling) — sufficient for
assembly design and clearance checking.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cadquery as cq

from ..core import Component, MatePoint


# ------------------------------------------------------------------
# Dimension tables (ISO standards, dimensions in mm)
# ------------------------------------------------------------------

# Hex bolt / socket head cap screw dimensions by metric size
BOLT_TABLE: dict[str, dict[str, float]] = {
    "M2":  {"thread_diameter": 2.0,  "head_diameter": 4.0,  "head_height": 1.4,  "socket_head_diameter": 3.8,  "socket_head_height": 2.0},
    "M2.5":{"thread_diameter": 2.5, "head_diameter": 5.0,  "head_height": 1.7,  "socket_head_diameter": 4.5,  "socket_head_height": 2.5},
    "M3":  {"thread_diameter": 3.0,  "head_diameter": 5.5,  "head_height": 2.0,  "socket_head_diameter": 5.5,  "socket_head_height": 3.0},
    "M4":  {"thread_diameter": 4.0,  "head_diameter": 7.0,  "head_height": 2.8,  "socket_head_diameter": 7.0,  "socket_head_height": 4.0},
    "M5":  {"thread_diameter": 5.0,  "head_diameter": 8.0,  "head_height": 3.5,  "socket_head_diameter": 8.5,  "socket_head_height": 5.0},
    "M6":  {"thread_diameter": 6.0,  "head_diameter": 10.0, "head_height": 4.0,  "socket_head_diameter": 10.0, "socket_head_height": 6.0},
    "M8":  {"thread_diameter": 8.0,  "head_diameter": 13.0, "head_height": 5.3,  "socket_head_diameter": 13.0, "socket_head_height": 8.0},
    "M10": {"thread_diameter": 10.0, "head_diameter": 16.0, "head_height": 6.4,  "socket_head_diameter": 16.0, "socket_head_height": 10.0},
    "M12": {"thread_diameter": 12.0, "head_diameter": 18.0, "head_height": 7.5,  "socket_head_diameter": 18.0, "socket_head_height": 12.0},
    "M16": {"thread_diameter": 16.0, "head_diameter": 24.0, "head_height": 10.0, "socket_head_diameter": 24.0, "socket_head_height": 16.0},
    "M20": {"thread_diameter": 20.0, "head_diameter": 30.0, "head_height": 12.5, "socket_head_diameter": 30.0, "socket_head_height": 20.0},
}

NUT_TABLE: dict[str, dict[str, float]] = {
    "M2":  {"thread_diameter": 2.0,  "across_flats": 4.0,  "height": 1.6},
    "M2.5":{"thread_diameter": 2.5, "across_flats": 5.0,  "height": 2.0},
    "M3":  {"thread_diameter": 3.0,  "across_flats": 5.5,  "height": 2.4},
    "M4":  {"thread_diameter": 4.0,  "across_flats": 7.0,  "height": 3.2},
    "M5":  {"thread_diameter": 5.0,  "across_flats": 8.0,  "height": 4.7},
    "M6":  {"thread_diameter": 6.0,  "across_flats": 10.0, "height": 5.2},
    "M8":  {"thread_diameter": 8.0,  "across_flats": 13.0, "height": 6.8},
    "M10": {"thread_diameter": 10.0, "across_flats": 16.0, "height": 8.4},
    "M12": {"thread_diameter": 12.0, "across_flats": 18.0, "height": 10.8},
    "M16": {"thread_diameter": 16.0, "across_flats": 24.0, "height": 14.8},
    "M20": {"thread_diameter": 20.0, "across_flats": 30.0, "height": 18.0},
}

WASHER_TABLE: dict[str, dict[str, float]] = {
    "M2":  {"inner_diameter": 2.2,  "outer_diameter": 5.0,  "thickness": 0.3},
    "M2.5":{"inner_diameter": 2.7, "outer_diameter": 6.0,  "thickness": 0.5},
    "M3":  {"inner_diameter": 3.2,  "outer_diameter": 7.0,  "thickness": 0.5},
    "M4":  {"inner_diameter": 4.3,  "outer_diameter": 9.0,  "thickness": 0.8},
    "M5":  {"inner_diameter": 5.3,  "outer_diameter": 10.0, "thickness": 1.0},
    "M6":  {"inner_diameter": 6.4,  "outer_diameter": 12.0, "thickness": 1.6},
    "M8":  {"inner_diameter": 8.4,  "outer_diameter": 16.0, "thickness": 1.6},
    "M10": {"inner_diameter": 10.5, "outer_diameter": 20.0, "thickness": 2.0},
    "M12": {"inner_diameter": 13.0, "outer_diameter": 24.0, "thickness": 2.5},
    "M16": {"inner_diameter": 17.0, "outer_diameter": 30.0, "thickness": 3.0},
    "M20": {"inner_diameter": 21.0, "outer_diameter": 37.0, "thickness": 3.0},
}


# ------------------------------------------------------------------
# Component classes
# ------------------------------------------------------------------


@dataclass
class HexBolt(Component):
    """ISO 4014/4017 hex head bolt (envelope geometry, no threads)."""

    name: str = "hex_bolt"
    thread_diameter: float = 6.0
    head_diameter: float = 10.0
    head_height: float = 4.0
    length: float = 20.0

    def build(self) -> cq.Workplane:
        # Hex head (inscribed in head_diameter circle)
        across_flats = self.head_diameter
        across_corners = across_flats / math.cos(math.pi / 6)
        result = (
            cq.Workplane("XY")
            .polygon(6, across_corners)
            .extrude(self.head_height)
        )
        # Shank extends downward from Z=0
        shank = (
            cq.Workplane("XY")
            .circle(self.thread_diameter / 2)
            .extrude(-self.length)
        )
        result = result.union(shank)
        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="head_top",
                origin=(0.0, 0.0, self.head_height),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="head_bearing",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="shank_end",
                origin=(0.0, 0.0, -self.length),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="axis",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="axis",
            ),
        ]


@dataclass
class SocketHeadCapScrew(Component):
    """ISO 4762 socket head cap screw (envelope geometry)."""

    name: str = "socket_head_cap_screw"
    thread_diameter: float = 6.0
    head_diameter: float = 10.0
    head_height: float = 6.0
    length: float = 20.0

    def build(self) -> cq.Workplane:
        # Cylindrical head
        result = (
            cq.Workplane("XY")
            .circle(self.head_diameter / 2)
            .extrude(self.head_height)
        )
        # Socket recess (hex, ~60% of head diameter)
        socket_af = self.head_diameter * 0.55
        socket_depth = self.head_height * 0.6
        socket_ac = socket_af / math.cos(math.pi / 6)
        result = (
            result
            .faces(">Z")
            .workplane()
            .polygon(6, socket_ac)
            .cutBlind(-socket_depth)
        )
        # Shank extends downward
        shank = (
            cq.Workplane("XY")
            .circle(self.thread_diameter / 2)
            .extrude(-self.length)
        )
        result = result.union(shank)
        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="head_top",
                origin=(0.0, 0.0, self.head_height),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="head_bearing",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="shank_end",
                origin=(0.0, 0.0, -self.length),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="axis",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="axis",
            ),
        ]


@dataclass
class HexNut(Component):
    """ISO 4032 hex nut (envelope geometry)."""

    name: str = "hex_nut"
    thread_diameter: float = 6.0
    across_flats: float = 10.0
    height: float = 5.2

    def build(self) -> cq.Workplane:
        across_corners = self.across_flats / math.cos(math.pi / 6)
        result = (
            cq.Workplane("XY")
            .polygon(6, across_corners)
            .extrude(self.height)
        )
        # Through-hole
        result = (
            result
            .faces(">Z")
            .workplane()
            .hole(self.thread_diameter, self.height)
        )
        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="bottom",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="top",
                origin=(0.0, 0.0, self.height),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="axis",
                origin=(0.0, 0.0, self.height / 2),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
        ]


@dataclass
class FlatWasher(Component):
    """ISO 7089 flat washer."""

    name: str = "flat_washer"
    inner_diameter: float = 6.4
    outer_diameter: float = 12.0
    thickness: float = 1.6

    def build(self) -> cq.Workplane:
        result = (
            cq.Workplane("XY")
            .circle(self.outer_diameter / 2)
            .circle(self.inner_diameter / 2)
            .extrude(self.thickness)
        )
        return result

    def mates(self) -> list[MatePoint]:
        return [
            MatePoint(
                name="bottom",
                origin=(0.0, 0.0, 0.0),
                normal=(0.0, 0.0, -1.0),
                mate_type="face",
            ),
            MatePoint(
                name="top",
                origin=(0.0, 0.0, self.thickness),
                normal=(0.0, 0.0, 1.0),
                mate_type="face",
            ),
            MatePoint(
                name="axis",
                origin=(0.0, 0.0, self.thickness / 2),
                normal=(0.0, 0.0, 1.0),
                mate_type="axis",
            ),
        ]
