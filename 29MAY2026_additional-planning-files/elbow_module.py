"""Project Wayland — Elbow Module v1 : parametric cuff + actuator mount.

One parametric cuff (reused for upper-arm and forearm by changing radius/length) and
one actuator mount that bolts to the QDD output face and links to the cuff. Built so the
`cadverify` harness has something to check: exports STEP/STL per part plus a features.json
(bolt circle, bore, cuff inner radius, tab holes) the mounting/clearance checks consume.

Run:  python elbow_module.py            # builds both, exports to ./out
"""
from __future__ import annotations
import json
import logging
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path

import cadquery as cq

logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("wayland.elbow.cad")


# ----------------------------------------------------------------------------- params
@dataclass
class CuffParams:
    name: str = "forearm"
    limb_radius: float = 42.0     # mm, limb cross-section radius at the cuff
    pad_gap: float = 6.0          # mm, padding / clearance between limb and shell inner wall
    wall: float = 4.0             # mm, shell wall thickness
    length: float = 90.0          # mm, axial length of the cuff
    wrap_angle: float = 210.0     # deg of material (>180 so it cradles & clips on)
    slot_w: float = 5.0           # tangential width of strap slot
    slot_h: float = 22.0          # axial height of strap slot
    edge_margin_deg: float = 18.0 # how far in from the open edge the slots sit
    # mounting tab (mates to the actuator-mount pad)
    tab_w: float = 26.0           # tangential width of the tab
    tab_len: float = 40.0         # axial length of the tab
    tab_thk: float = 8.0          # radial thickness of the tab
    tab_bolt_spacing: float = 22.0
    bolt_d: float = 4.2           # M4 clearance


@dataclass
class MountParams:
    name: str = "actuator_mount"
    mount_plate_r: float = 35.0   # mm, plate radius (covers actuator output face)
    mount_thk: float = 6.0
    bore_r: float = 8.0           # central bore for shaft / output boss
    bolt_circle_r: float = 25.0   # actuator output bolt circle radius
    n_bolts: int = 6
    bolt_d: float = 4.2           # M4 clearance
    arm_len: float = 55.0         # reach from plate edge to the cuff pad
    arm_w: float = 26.0
    tab_bolt_spacing: float = 22.0  # MUST match CuffParams.tab_bolt_spacing


# ----------------------------------------------------------------------------- helpers
def _sector(angle_deg: float, radius: float, length: float, steps: int = 96) -> cq.Workplane:
    """Solid pie-wedge of `angle_deg`, centered on +X, extruded along +Z."""
    half = math.radians(angle_deg / 2.0)
    pts = [(0.0, 0.0)]
    for i in range(steps + 1):
        a = -half + (2 * half) * i / steps
        pts.append((radius * math.cos(a), radius * math.sin(a)))
    return cq.Workplane("XY").polyline(pts).close().extrude(length)


def _hole_along_x(d: float, length: float) -> cq.Workplane:
    """Cylinder of diameter d, axis along X, centered on the origin."""
    return (cq.Workplane("XY").circle(d / 2.0).extrude(length)
            .translate((0, 0, -length / 2.0))
            .rotate((0, 0, 0), (0, 1, 0), 90))


# ----------------------------------------------------------------------------- cuff
def build_cuff(p: CuffParams) -> tuple[cq.Workplane, dict]:
    r_in = p.limb_radius + p.pad_gap
    r_out = r_in + p.wall
    logger.info("cuff build", extra={"part_name": p.name, "r_in": r_in, "r_out": r_out})

    tube = (cq.Workplane("XY").circle(r_out).extrude(p.length)
            .cut(cq.Workplane("XY").circle(r_in).extrude(p.length)))
    cuff = tube.intersect(_sector(p.wrap_angle, r_out * 1.25, p.length))

    # strap slots near each open edge, two along the length
    r_mid = (r_in + r_out) / 2.0
    theta_edge = p.wrap_angle / 2.0 - p.edge_margin_deg
    slot_zs = [p.length * 0.3, p.length * 0.7]
    for theta in (theta_edge, -theta_edge):
        for z in slot_zs:
            slot = (cq.Workplane("XY").box(p.wall * 3.0, p.slot_w, p.slot_h)
                    .translate((r_mid, 0, 0))
                    .rotate((0, 0, 0), (0, 0, 1), theta)
                    .translate((0, 0, z)))
            cuff = cuff.cut(slot)

    # mounting tab on the +X outer face, mid-length
    tab = (cq.Workplane("XY").box(p.tab_thk, p.tab_w, p.tab_len)
           .translate((r_out + p.tab_thk / 2.0 - 0.6, 0, p.length / 2.0)))
    cuff = cuff.union(tab)

    # two radial bolt holes through the tab
    tab_holes = []
    for dz in (-p.tab_bolt_spacing / 2.0, p.tab_bolt_spacing / 2.0):
        hole = _hole_along_x(p.bolt_d, p.tab_thk * 4.0).translate(
            (r_out + p.tab_thk / 2.0, 0, p.length / 2.0 + dz))
        cuff = cuff.cut(hole)
        tab_holes.append([round(p.length / 2.0 + dz, 2)])

    feats = {
        "part": "cuff",
        "name": p.name,
        "cuff_inner_radius": r_in,
        "cuff_outer_radius": r_out,
        "wrap_angle_deg": p.wrap_angle,
        "tab_bolt_spacing": p.tab_bolt_spacing,
        "tab_bolt_d": p.bolt_d,
    }
    return cuff, feats


# ----------------------------------------------------------------------------- mount
def build_mount(p: MountParams) -> tuple[cq.Workplane, dict]:
    logger.info("mount build", extra={"part_name": p.name, "n_bolts": p.n_bolts})
    plate = (cq.Workplane("XY").circle(p.mount_plate_r).extrude(p.mount_thk)
             .cut(cq.Workplane("XY").circle(p.bore_r).extrude(p.mount_thk)))

    bolt_positions = []
    for i in range(p.n_bolts):
        a = 2 * math.pi * i / p.n_bolts
        x, y = p.bolt_circle_r * math.cos(a), p.bolt_circle_r * math.sin(a)
        plate = plate.cut(cq.Workplane("XY").center(x, y).circle(p.bolt_d / 2.0).extrude(p.mount_thk))
        bolt_positions.append([round(x, 2), round(y, 2)])

    arm = (cq.Workplane("XY").box(p.arm_len, p.arm_w, p.mount_thk)
           .translate((p.mount_plate_r + p.arm_len / 2.0 - 3.0, 0, p.mount_thk / 2.0)))
    pad = (cq.Workplane("XY").box(p.arm_w, p.arm_w, p.mount_thk)
           .translate((p.mount_plate_r + p.arm_len, 0, p.mount_thk / 2.0)))
    mount = plate.union(arm).union(pad)

    pad_cx = p.mount_plate_r + p.arm_len
    for dy in (-p.tab_bolt_spacing / 2.0, p.tab_bolt_spacing / 2.0):
        mount = mount.cut(cq.Workplane("XY").center(pad_cx, dy).circle(p.bolt_d / 2.0).extrude(p.mount_thk))

    feats = {
        "part": "actuator_mount",
        "name": p.name,
        "bore_radius": p.bore_r,
        "actuator_bolt_circle": {
            "radius": p.bolt_circle_r, "n": p.n_bolts,
            "bolt_d": p.bolt_d, "positions": bolt_positions,
        },
        "pad_bolt_spacing": p.tab_bolt_spacing,
    }
    return mount, feats


# ----------------------------------------------------------------------------- export
def _export(part: cq.Workplane, stem: Path) -> None:
    cq.exporters.export(part, str(stem.with_suffix(".step")))
    cq.exporters.export(part, str(stem.with_suffix(".stl")))
    try:
        cq.exporters.export(part, str(stem.with_suffix(".svg")),
                            opt={"width": 640, "height": 480,
                                 "projectionDir": (1.0, 1.0, 0.7),
                                 "showAxes": False})
    except Exception:
        logger.warning("svg export skipped", exc_info=True)
    bb = part.val().BoundingBox()
    logger.info("exported", extra={"stem": stem.name,
                                   "bbox_mm": (round(bb.xlen, 1), round(bb.ylen, 1), round(bb.zlen, 1)),
                                   "volume_mm3": round(part.val().Volume(), 1)})


def main(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    features = {}

    # forearm cuff + upper-arm cuff (same code, different params -> extensibility)
    for cp in (CuffParams(name="forearm", limb_radius=42.0, length=90.0),
               CuffParams(name="upperarm", limb_radius=52.0, length=110.0)):
        part, feats = build_cuff(cp)
        assert part.val().Volume() > 0, f"empty cuff {cp.name}"
        _export(part, out / f"cuff_{cp.name}")
        features[f"cuff_{cp.name}"] = feats

    mp = MountParams()
    mount, mfeats = build_mount(mp)
    assert mount.val().Volume() > 0, "empty mount"
    _export(mount, out / "actuator_mount")
    features["actuator_mount"] = mfeats

    # consistency check the harness would also assert
    assert mp.tab_bolt_spacing == CuffParams().tab_bolt_spacing, "cuff/mount bolt spacing mismatch"

    (out / "features.json").write_text(json.dumps(features, indent=2))
    logger.info("features written", extra={"path": str(out / "features.json")})


if __name__ == "__main__":
    main(Path(__file__).parent / "out")
