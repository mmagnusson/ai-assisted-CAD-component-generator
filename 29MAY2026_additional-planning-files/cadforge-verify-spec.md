# CAD Forge — Verification Loop Harness (`cadverify`)

A build-and-check harness that wraps CadQuery/Build123d code generation in a closed
verification loop. The model emits build code; the harness executes it, runs exact
geometric assertions for the things the model **cannot see**, renders multiview images
for a vision-review pass, and emits a structured JSON report the model reads to revise.

**Design premise:** the model is good at the language/code/planning layer and blind at
the spatial layer. This harness moves the spatial judgment out of the model and into
kernel math (OpenCASCADE via OCP) + simulation, so model-quality gains convert into
fewer bad parts instead of better guesses.

---

## 0. Stack & dependencies

- Python 3.11+, `pathlib.Path` everywhere (never string-concat paths).
- `cadquery` and/or `build123d` (both sit on OCP, so the OCP calls below work for either).
- `OCP` (OpenCASCADE Python bindings) — pulled in by cadquery; we call it directly for
  distance and mass properties.
- `trimesh` + `numpy` — mesh-level checks (overhang, wall thickness) and STL I/O.
- `pyvista` — off-screen multiview rendering. On headless Linux: `pv.start_xvfb()`.
- `pydantic` (or stdlib `dataclasses`) for the contracts below. Pydantic preferred for
  JSON (de)serialization of reports.

> **AI-efficient requirements (baked in from scaffold, not bolted on later):**
> - Named `logging.getLogger(__name__)` per module; structured `extra={...}`; JSON formatter
>   in CI, human-readable in dev. Every check logs measured value + threshold + verdict.
> - One-action `debug_export(part_id)` -> single JSON blob: spec, generated source, bbox,
>   mass props, every CheckResult, render paths, last N log lines. Hand to a fresh session.
> - Seed parts ship **with** the feature, including a deliberately broken one, so the
>   asserts are self-testing (a known 0.2 mm interference *must* fail the interference check).
> - **Fresh-eyes review is mandatory** here, not optional: parts feed real machines / ICS-
>   adjacent gear. Loop runner emits a handoff summary for a second session on every failed
>   converge.

---

## 1. Module layout

```
cadverify/
  __init__.py
  contracts.py        # Spec, BuildResult, CheckResult, VerifyReport (the interfaces)
  executor.py         # run generated build code in-process, capture shapes + kernel errors
  geom.py             # OCP wrappers: distance, intersection volume, bbox, mass props
  checks/
    __init__.py
    interference.py    # forbidden-pair boolean intersection volume > eps
    clearance.py       # required-pair min distance >= gap
    envelope.py        # assembly bbox fits enclosure / build plate
    mass.py            # volume * density -> mass; COM inside support polygon (tip-over)
    mounting.py        # hole-pattern / datum alignment vs mating part
    manufacture.py     # overhang angle, min wall (approximate, mesh-based)
    kinematics.py      # sweep joints through range, assert no self-collision
  render.py           # pyvista off-screen multiview PNG + per-pose renders
  review.py           # vision-review hook: renders + intent -> model critique
  report.py           # aggregate CheckResults -> VerifyReport, JSON + console
  debug_export.py     # one-action state dump for AI debugging
  loop.py             # run -> check -> report -> (revise) loop runner + convergence
  config.py           # densities, thresholds, view definitions, paths
  seeds/
    bracket_good.py    # passes everything
    bracket_bad.py     # deliberate 0.2 mm interference + a 30 deg overhang  <- test fixture
  logging_config.py
```

---

## 2. Contracts (`contracts.py`)

These are the crisp interfaces Claude Code should pin down first; everything else
consumes them.

```python
from pydantic import BaseModel
from enum import Enum

class Verdict(str, Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    ERROR = "error"   # check itself couldn't run (degenerate geom, kernel exception)

class JointSpec(BaseModel):
    name: str
    part: str                   # the moving part's name in the assembly
    axis: tuple[float, float, float]
    origin: tuple[float, float, float]
    kind: str                   # "revolute" | "prismatic"
    range: tuple[float, float]  # degrees for revolute, mm for prismatic
    steps: int = 24             # sweep resolution for collision check

class Spec(BaseModel):
    """Design intent. The model fills this in alongside the build code."""
    name: str
    forbidden_interferences: list[tuple[str, str]] = []   # pairs that must NOT touch
    required_clearances: dict[str, float] = {}            # "partA|partB" -> min mm
    envelope: tuple[float, float, float] | None = None    # max x,y,z bbox (mm)
    build_plate: tuple[float, float] | None = None        # printable x,y (mm)
    max_mass_g: float | None = None
    support_polygon: list[tuple[float, float]] | None = None  # for COM tip-over check
    print_orientation: tuple[float, float, float] = (0, 0, 1) # build direction
    max_overhang_deg: float = 45.0
    min_wall_mm: float | None = None
    joints: list[JointSpec] = []
    material_density_g_mm3: float = 0.00124   # PLA ~1.24 g/cm^3; override per material

class BuildResult(BaseModel):
    parts: dict[str, object]   # name -> OCP/cadquery Shape (not serialized)
    source: str                # the generated build code, verbatim
    ok: bool
    error: str | None = None
    class Config:
        arbitrary_types_allowed = True

class CheckResult(BaseModel):
    check: str
    verdict: Verdict
    measured: float | None = None
    threshold: float | None = None
    detail: str = ""

class VerifyReport(BaseModel):
    spec_name: str
    overall: Verdict
    checks: list[CheckResult]
    renders: list[str] = []          # png paths
    review_notes: str | None = None  # from vision pass
    def failed(self) -> list[CheckResult]:
        return [c for c in self.checks if c.verdict in (Verdict.FAIL, Verdict.ERROR)]
```

---

## 3. Geometry wrappers (`geom.py`) — get these API names right

CadQuery `Workplane.val().wrapped` and Build123d `obj.wrapped` both give the OCP
`TopoDS_Shape`. Work at that level so checks are library-agnostic.

```python
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

def to_topods(shape):
    return shape.wrapped if hasattr(shape, "wrapped") else shape

def min_distance(a, b) -> float:
    """Minimum surface-to-surface distance in mm. 0.0 means touching/overlapping."""
    ext = BRepExtrema_DistShapeShape(to_topods(a), to_topods(b))
    if not ext.IsDone():
        raise RuntimeError("distance computation failed")
    return ext.Value()

def intersection_volume(a, b) -> float:
    """Volume of overlap. > eps => interference. Guard the boolean; it can throw."""
    try:
        inter = a.intersect(b)          # cadquery Shape API; build123d use (a & b)
        return abs(inter.Volume())
    except Exception:
        return 0.0

def mass_properties(shape, density_g_mm3: float):
    props = GProp_GProps()
    BRepGProp.VolumeProperties_s(to_topods(shape), props)
    volume = props.Mass()               # = volume for VolumeProperties
    com = props.CentreOfMass()
    return {"volume_mm3": volume, "mass_g": volume * density_g_mm3,
            "com": (com.X(), com.Y(), com.Z())}

def bbox(shape):
    bb = shape.BoundingBox()            # cadquery Shape.BoundingBox(); b123d obj.bounding_box()
    return (bb.xlen, bb.ylen, bb.zlen, (bb.xmin, bb.ymin, bb.zmin))
```

---

## 4. Check catalog

Each check is a pure function `(BuildResult, Spec) -> list[CheckResult]`. No side effects
except logging. Confidence tiers matter — be honest about them in output:

**Tier A — exact (kernel math, trustworthy):**
- `interference`: for each forbidden pair, `intersection_volume > eps` (eps ~ 1e-3 mm^3) => FAIL.
- `clearance`: for each required pair, `min_distance < gap` => FAIL; within 10% of gap => WARN.
- `envelope`: assembly bbox vs `envelope`; any axis over => FAIL. Footprint vs `build_plate`.
- `mass`: sum of part masses > `max_mass_g` => FAIL. COM xy outside `support_polygon` => FAIL
  (tip-over) — point-in-polygon on the convex hull of contact points.

**Tier B — approximate (mesh heuristics, calibrate against seed bad part):**
- `manufacture.overhang`: tessellate (`shape.tessellate(tol)` or export STL -> trimesh),
  for the given `print_orientation` flag down-facing faces whose slope exceeds
  `max_overhang_deg`; report total overhang area. Convention is fiddly — **calibrate the
  formula until `bracket_bad` reports its known 30 deg overhang and `bracket_good` reports ~0.**
- `manufacture.min_wall`: genuinely hard exactly. Approximate via voxelization
  (`mesh.voxelized(pitch=min_wall/2)`) or interior ray sampling. Emit WARN not FAIL; flag
  as heuristic in `detail`.
- `mounting`: extract hole circle centers (cylindrical faces normal to a mating plane),
  compare pattern to mating part within tolerance. Start simple: positions only.

**Tier C — simulation (optional, Phase 5):**
- `kinematics`: for each `JointSpec`, transform the moving part across `range` in `steps`,
  run `interference` against the rest of the assembly at every step. Any step with overlap
  => FAIL with the offending angle/position in `detail`.

```python
# checks/clearance.py — representative shape of every check
import logging
from cadverify.contracts import CheckResult, Verdict
from cadverify.geom import min_distance

logger = logging.getLogger(__name__)

def check(build, spec) -> list[CheckResult]:
    out = []
    for key, gap in spec.required_clearances.items():
        a_name, b_name = key.split("|")
        try:
            d = min_distance(build.parts[a_name], build.parts[b_name])
        except Exception:
            logger.error("clearance check errored", extra={"pair": key}, exc_info=True)
            out.append(CheckResult(check=f"clearance:{key}", verdict=Verdict.ERROR))
            continue
        verdict = Verdict.PASS if d >= gap else Verdict.FAIL
        if verdict == Verdict.PASS and d < gap * 1.1:
            verdict = Verdict.WARN
        logger.info("clearance", extra={"pair": key, "measured_mm": round(d, 3),
                                        "gap_mm": gap, "verdict": verdict})
        out.append(CheckResult(check=f"clearance:{key}", verdict=verdict,
                               measured=d, threshold=gap))
    return out
```

---

## 5. Render harness (`render.py`)

```python
import pyvista as pv
from pathlib import Path

VIEWS = {"iso": "iso", "front": "xz", "top": "xy", "right": "yz"}

def render_multiview(stl_path: Path, out_dir: Path, prefix: str) -> list[Path]:
    pv.start_xvfb()  # headless Linux only; no-op/skip on desktop
    mesh = pv.read(str(stl_path))
    paths = []
    for name, cam in VIEWS.items():
        p = pv.Plotter(off_screen=True, window_size=(1024, 768))
        p.add_mesh(mesh, show_edges=True)
        p.camera_position = cam
        out = out_dir / f"{prefix}_{name}.png"
        p.screenshot(str(out)); p.close()
        paths.append(out)
    return paths
```

For kinematics, render the assembly at min/mid/max of each joint so the vision pass can
spot binding the asserts might miss at coarse step resolution.

## 6. Vision review (`review.py`)

Feed the renders + the `Spec` + the design intent prose back to the model and ask for a
*critique*, not a redesign: "Given this intent and these views, list anything that looks
wrong — proportions, fastener access, obvious interference, print orientation problems."
Capture the response into `VerifyReport.review_notes`. This catches the qualitative
"that's not what I meant" failures the numeric asserts pass clean.

---

## 7. Loop runner (`loop.py`)

```
generate build code + Spec
   -> executor.run        (capture shapes or kernel error)
   -> run all checks      -> VerifyReport
   -> render + vision review
   -> if overall PASS: done
      else: feed report.failed() + review_notes back to model to revise
   -> repeat, max K iterations
```

- **Convergence / bad-session detection:** if not converging after 3–5 iterations, stop,
  call `debug_export`, and write a concise fresh-eyes handoff (`handoff_<spec>.md`) rather
  than burning 30 loops.
- Every iteration appends to a run log so the whole loop is reconstructable from one file.

---

## 8. Build order for tonight

- [ ] **Phase 0 — scaffold:** layout, `logging_config.py`, `contracts.py`, `config.py`,
      both seed parts. Confirm `bracket_good` builds and `bracket_bad` builds (it should
      build fine — it's geometrically valid but *wrong*, which is the point).
- [ ] **Phase 1 — executor + Tier A checks + report.** Run against both seeds: `good`
      passes all, `bad` fails interference + envelope. **This alone closes most of the
      blind spot — ship it before touching renders.**
- [ ] **Phase 2 — `render.py` + `debug_export.py`.** Verify headless PNGs come out.
- [ ] **Phase 3 — `review.py` vision hook.**
- [ ] **Phase 4 — Tier B manufacture checks**, calibrated against `bracket_bad`'s overhang.
- [ ] **Phase 5 — kinematics + `loop.py`** with convergence detection + handoff emit.

Worktree branches if you parallelize: `ai/cadverify-phase1-checks`, `ai/cadverify-render`,
`ai/cadverify-kinematics` — never two sessions on the same files.

---

## 9. Acceptance test (write this first, TDD the harness against it)

`bracket_bad` must produce a report where:
- `interference:*` -> FAIL (the 0.2 mm overlap)
- `envelope` -> FAIL (if sized past the plate) or PASS as configured
- `manufacture.overhang` -> FAIL/WARN flagging the 30 deg face

`bracket_good` must produce all PASS. If the harness can't tell these two apart, the
checks are wrong — fix the harness, not the parts.
