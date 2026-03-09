"""Standard parts catalog for CAD Forge.

Provides lookup functions for off-the-shelf parts with standard
dimensions.  Components are parametric CadQuery geometry locked to
real-world sizes — you get an M6x20 bolt with the correct head
diameter, not a guess.

Usage::

    from cadforge.catalog import get_fastener, get_bearing, get_motor

    bolt = get_fastener("hex_bolt", "M6", length=20)
    bearing = get_bearing("608")
    motor = get_motor("nema17")
"""

from __future__ import annotations

from typing import Any

from ..core import Component


def get_fastener(
    kind: str,
    size: str,
    length: float | None = None,
) -> Component:
    """Look up a standard fastener.

    Args:
        kind: Fastener type — "hex_bolt", "hex_nut", "flat_washer",
              "socket_head_cap_screw".
        size: ISO metric size string, e.g. "M3", "M6", "M10".
        length: Shank/thread length in mm (required for bolts/screws).

    Returns:
        A Component instance with standard dimensions.

    Raises:
        ValueError: If the kind or size is not in the catalog.
    """
    from .fasteners import (
        BOLT_TABLE,
        NUT_TABLE,
        WASHER_TABLE,
        HexBolt,
        HexNut,
        FlatWasher,
        SocketHeadCapScrew,
    )

    size_upper = size.upper()

    if kind == "hex_bolt":
        if size_upper not in BOLT_TABLE:
            raise ValueError(
                f"Unknown bolt size '{size}'. "
                f"Available: {', '.join(sorted(BOLT_TABLE))}"
            )
        if length is None:
            raise ValueError("length is required for hex_bolt")
        dims = BOLT_TABLE[size_upper]
        return HexBolt(
            thread_diameter=dims["thread_diameter"],
            head_diameter=dims["head_diameter"],
            head_height=dims["head_height"],
            length=length,
        )

    elif kind == "socket_head_cap_screw":
        if size_upper not in BOLT_TABLE:
            raise ValueError(
                f"Unknown screw size '{size}'. "
                f"Available: {', '.join(sorted(BOLT_TABLE))}"
            )
        if length is None:
            raise ValueError("length is required for socket_head_cap_screw")
        dims = BOLT_TABLE[size_upper]
        return SocketHeadCapScrew(
            thread_diameter=dims["thread_diameter"],
            head_diameter=dims["socket_head_diameter"],
            head_height=dims["socket_head_height"],
            length=length,
        )

    elif kind == "hex_nut":
        if size_upper not in NUT_TABLE:
            raise ValueError(
                f"Unknown nut size '{size}'. "
                f"Available: {', '.join(sorted(NUT_TABLE))}"
            )
        dims = NUT_TABLE[size_upper]
        return HexNut(
            thread_diameter=dims["thread_diameter"],
            across_flats=dims["across_flats"],
            height=dims["height"],
        )

    elif kind == "flat_washer":
        if size_upper not in WASHER_TABLE:
            raise ValueError(
                f"Unknown washer size '{size}'. "
                f"Available: {', '.join(sorted(WASHER_TABLE))}"
            )
        dims = WASHER_TABLE[size_upper]
        return FlatWasher(
            inner_diameter=dims["inner_diameter"],
            outer_diameter=dims["outer_diameter"],
            thickness=dims["thickness"],
        )

    else:
        raise ValueError(
            f"Unknown fastener kind '{kind}'. "
            f"Available: hex_bolt, socket_head_cap_screw, hex_nut, flat_washer"
        )


def get_bearing(designation: str) -> Component:
    """Look up a standard deep-groove ball bearing.

    Args:
        designation: Bearing designation, e.g. "608", "6001", "6200".

    Returns:
        A Component with standard bore, OD, and width.

    Raises:
        ValueError: If the designation is not in the catalog.
    """
    from .bearings import BEARING_TABLE, DeepGrooveBearing

    if designation not in BEARING_TABLE:
        raise ValueError(
            f"Unknown bearing '{designation}'. "
            f"Available: {', '.join(sorted(BEARING_TABLE))}"
        )
    dims = BEARING_TABLE[designation]
    return DeepGrooveBearing(
        designation=designation,
        bore=dims["bore"],
        outer_diameter=dims["outer_diameter"],
        width=dims["width"],
    )


def get_motor(frame: str) -> Component:
    """Look up a NEMA stepper motor envelope.

    Args:
        frame: NEMA frame size — "nema14", "nema17", "nema23", "nema34".

    Returns:
        A Component representing the motor envelope geometry.

    Raises:
        ValueError: If the frame size is not in the catalog.
    """
    from .motors import MOTOR_TABLE, NemaMotor

    frame_lower = frame.lower()
    if frame_lower not in MOTOR_TABLE:
        raise ValueError(
            f"Unknown motor frame '{frame}'. "
            f"Available: {', '.join(sorted(MOTOR_TABLE))}"
        )
    dims = MOTOR_TABLE[frame_lower]
    return NemaMotor(
        frame_size=frame_lower,
        faceplate_width=dims["faceplate_width"],
        body_length=dims["body_length"],
        shaft_diameter=dims["shaft_diameter"],
        shaft_length=dims["shaft_length"],
        bolt_hole_spacing=dims["bolt_hole_spacing"],
        bolt_hole_diameter=dims["bolt_hole_diameter"],
        pilot_diameter=dims["pilot_diameter"],
        pilot_height=dims["pilot_height"],
    )
