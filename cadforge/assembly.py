"""Assembly support for CAD Forge.

An Assembly holds multiple Component instances positioned in 3D space,
wrapping CadQuery's native cq.Assembly for constraint solving and
multi-body STEP export.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cadquery as cq
from cadquery import exporters

from .core import Component, MatePoint
from .validators.geometry import ValidationResult


@dataclass
class AssemblyPart:
    """A positioned component within an assembly.

    Locations and rotations use plain tuples so they serialize to JSON
    for LLM interaction.
    """

    component: Component
    name: str
    location: tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: tuple[float, float, float] = (0.0, 0.0, 0.0)  # euler XYZ degrees
    color: tuple[float, float, float, float] | None = None  # RGBA 0-1


@dataclass
class MateConstraint:
    """A constraint between two mate points in an assembly.

    Attributes:
        part1_name:      Name of the first part in the assembly.
        mate1_name:      Name of the mate point on part 1.
        part2_name:      Name of the second part in the assembly.
        mate2_name:      Name of the mate point on part 2.
        constraint_type: How the mates connect:
            - "coincident": faces touch, normals oppose (default)
            - "coaxial": axes align
            - "offset": faces aligned with a gap
        offset:          Distance for "offset" constraints (mm).
    """

    part1_name: str
    mate1_name: str
    part2_name: str
    mate2_name: str
    constraint_type: str = "coincident"  # "coincident", "coaxial", "offset"
    offset: float = 0.0


def _make_location(
    loc: tuple[float, float, float],
    rot: tuple[float, float, float],
) -> cq.Location:
    """Convert position + euler angles (degrees) to a cq.Location."""
    return cq.Location(
        cq.Vector(*loc),
        cq.Vector(1, 0, 0),
        rot[0],
    ) * cq.Location(
        cq.Vector(0, 0, 0),
        cq.Vector(0, 1, 0),
        rot[1],
    ) * cq.Location(
        cq.Vector(0, 0, 0),
        cq.Vector(0, 0, 1),
        rot[2],
    )


@dataclass
class Assembly:
    """Multi-part assembly composed of positioned Components.

    Wraps ``cq.Assembly`` internally.  All spatial data uses plain
    tuples so assembly specs can round-trip through JSON.
    """

    name: str = "assembly"
    parts: list[AssemblyPart] = field(default_factory=list)
    constraints: list[MateConstraint] = field(default_factory=list)
    fits: list[Any] = field(default_factory=list)  # list[FitSpec]

    # Internal cache
    _cq_assembly: cq.Assembly | None = field(
        default=None, init=False, repr=False
    )

    def add_part(
        self,
        component: Component,
        name: str | None = None,
        location: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: tuple[float, float, float, float] | None = None,
    ) -> AssemblyPart:
        """Add a component to the assembly and return the AssemblyPart."""
        if name is None:
            name = f"{component.name}_{len(self.parts)}"

        # Check for duplicate names
        existing_names = {p.name for p in self.parts}
        if name in existing_names:
            raise ValueError(f"Duplicate part name: '{name}'")

        part = AssemblyPart(
            component=component,
            name=name,
            location=location,
            rotation=rotation,
            color=color,
        )
        self.parts.append(part)
        self._cq_assembly = None  # invalidate cache
        return part

    def add_compound(
        self,
        compound: Any,
        name: str | None = None,
        location: tuple[float, float, float] = (0.0, 0.0, 0.0),
        rotation: tuple[float, float, float] = (0.0, 0.0, 0.0),
        color: tuple[float, float, float, float] | None = None,
    ) -> str:
        """Add a CompoundComponent as a nested sub-assembly.

        Returns the name used for the compound in this assembly.
        The compound's mate points are accessible for constraints
        via ``compound_name/mate_name``.
        """
        from .compounds import CompoundComponent

        if not isinstance(compound, CompoundComponent):
            raise TypeError(
                f"Expected CompoundComponent, got {type(compound).__name__}"
            )

        if name is None:
            name = f"{compound.name}_{len(self.parts)}"

        # Check for duplicate names
        existing = {p.name for p in self.parts} | self._compound_names()
        if name in existing:
            raise ValueError(f"Duplicate name: '{name}'")

        # Store the compound in a separate list for building
        if not hasattr(self, '_compounds'):
            self._compounds: list[tuple[Any, str, tuple, tuple, Any]] = []
        self._compounds.append((compound, name, location, rotation, color))
        self._cq_assembly = None
        return name

    def _compound_names(self) -> set[str]:
        """Return names of all added compounds."""
        if not hasattr(self, '_compounds'):
            return set()
        return {name for _, name, _, _, _ in self._compounds}

    def add_constraint(
        self,
        part1_name: str,
        mate1_name: str,
        part2_name: str,
        mate2_name: str,
        constraint_type: str = "coincident",
        offset: float = 0.0,
    ) -> MateConstraint:
        """Add a mate constraint between two parts.

        The first part listed in the assembly with a constraint is
        treated as fixed; the solver positions subsequent parts
        relative to it.
        """
        # Validate part names exist
        part_names = {p.name for p in self.parts}
        for pn in (part1_name, part2_name):
            if pn not in part_names:
                raise ValueError(
                    f"Part '{pn}' not found in assembly. "
                    f"Available: {', '.join(sorted(part_names))}"
                )

        # Validate mate names exist on the components
        self._get_mate_point(part1_name, mate1_name)
        self._get_mate_point(part2_name, mate2_name)

        mc = MateConstraint(
            part1_name=part1_name,
            mate1_name=mate1_name,
            part2_name=part2_name,
            mate2_name=mate2_name,
            constraint_type=constraint_type,
            offset=offset,
        )
        self.constraints.append(mc)
        self._cq_assembly = None  # invalidate cache
        return mc

    def add_fit(
        self,
        source_part: str,
        source_param: str,
        target_part: str,
        target_param: str,
        fit_type: str = "clearance",
        allowance: float = 0.0,
    ) -> Any:
        """Add a fit specification between two part parameters.

        The source parameter drives the target parameter.  The target
        is adjusted based on the fit type (clearance, transition,
        interference, or exact).

        Example::

            assy.add_fit(
                "coupler", "bore_2",
                "mount", "bore_diameter",
                fit_type="clearance",
            )
        """
        from .fitting import FitSpec

        # Validate parts exist
        part_names = {p.name for p in self.parts}
        for pn in (source_part, target_part):
            if pn not in part_names:
                raise ValueError(
                    f"Part '{pn}' not found in assembly. "
                    f"Available: {', '.join(sorted(part_names))}"
                )

        # Validate params exist
        source_comp = self._get_part(source_part).component
        if not hasattr(source_comp, source_param):
            raise ValueError(
                f"Parameter '{source_param}' not found on "
                f"'{source_part}' ({type(source_comp).__name__})"
            )
        target_comp = self._get_part(target_part).component
        if not hasattr(target_comp, target_param):
            raise ValueError(
                f"Parameter '{target_param}' not found on "
                f"'{target_part}' ({type(target_comp).__name__})"
            )

        fit = FitSpec(
            source_part=source_part,
            source_param=source_param,
            target_part=target_part,
            target_param=target_param,
            fit_type=fit_type,
            allowance=allowance,
        )
        self.fits.append(fit)
        self._cq_assembly = None
        return fit

    def _apply_fits(self) -> None:
        """Apply fit specifications to adjust component parameters."""
        if not self.fits:
            return

        from .fitting import FitResolver

        parts_dict = {p.name: p.component for p in self.parts}
        adjustments = FitResolver.resolve(self.fits, parts_dict)
        FitResolver.apply(adjustments, parts_dict)

    def _get_part(self, name: str) -> AssemblyPart:
        """Look up a part by name."""
        for p in self.parts:
            if p.name == name:
                return p
        raise ValueError(f"Part '{name}' not found in assembly")

    def _get_mate_point(self, part_name: str, mate_name: str) -> MatePoint:
        """Look up a mate point on a part."""
        part = self._get_part(part_name)
        for mp in part.component.mates():
            if mp.name == mate_name:
                return mp
        available = [m.name for m in part.component.mates()]
        raise ValueError(
            f"Mate '{mate_name}' not found on '{part_name}'. "
            f"Available: {', '.join(available) or '(none)'}"
        )

    def _resolve_constraints(self) -> dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]]:
        """Compute part positions from mate constraints.

        Returns a dict mapping part_name -> (location, rotation) for
        each constrained part.  Parts not involved in constraints keep
        their manually-specified locations.

        The algorithm walks constraints sequentially: the first part
        referenced is fixed at its current location, then each
        subsequent constrained part is positioned so its mate point
        aligns with the target mate point on the already-placed part.
        """
        import math

        if not self.constraints:
            return {}

        # Track which parts have been placed
        placed: dict[str, tuple[tuple[float, float, float], tuple[float, float, float]]] = {}

        for mc in self.constraints:
            # Ensure part1 is placed (fix it at its current location)
            if mc.part1_name not in placed:
                p1 = self._get_part(mc.part1_name)
                placed[mc.part1_name] = (p1.location, p1.rotation)

            if mc.part2_name not in placed:
                mp1 = self._get_mate_point(mc.part1_name, mc.mate1_name)
                mp2 = self._get_mate_point(mc.part2_name, mc.mate2_name)

                p1_loc = placed[mc.part1_name][0]

                # Target point in world space: part1 location + mate1 origin
                target = (
                    p1_loc[0] + mp1.origin[0],
                    p1_loc[1] + mp1.origin[1],
                    p1_loc[2] + mp1.origin[2],
                )

                if mc.constraint_type == "coincident":
                    # Position part2 so that mate2 origin lands on target,
                    # with normals opposing (face-to-face contact).
                    # We compute the rotation needed to flip mate2's
                    # normal to oppose mate1's normal.
                    rot = _rotation_to_oppose(mp1.normal, mp2.normal)

                    # After rotation, mate2's origin may have changed.
                    # Apply the rotation to mate2's origin to find where
                    # it ends up, then translate to align.
                    rotated_mp2_origin = _rotate_point(mp2.origin, rot)

                    loc = (
                        target[0] - rotated_mp2_origin[0],
                        target[1] - rotated_mp2_origin[1],
                        target[2] - rotated_mp2_origin[2],
                    )
                    placed[mc.part2_name] = (loc, rot)

                elif mc.constraint_type == "coaxial":
                    # Align axes: rotate part2 so mate2's normal
                    # parallels mate1's normal, then translate so
                    # the axis origins coincide.
                    rot = _rotation_to_align(mp1.normal, mp2.normal)
                    rotated_mp2_origin = _rotate_point(mp2.origin, rot)

                    loc = (
                        target[0] - rotated_mp2_origin[0],
                        target[1] - rotated_mp2_origin[1],
                        target[2] - rotated_mp2_origin[2],
                    )
                    placed[mc.part2_name] = (loc, rot)

                elif mc.constraint_type == "offset":
                    # Like coincident but with a gap along mate1's normal.
                    rot = _rotation_to_oppose(mp1.normal, mp2.normal)
                    rotated_mp2_origin = _rotate_point(mp2.origin, rot)

                    # Push along mate1's normal by offset amount
                    n = mp1.normal
                    n_len = math.sqrt(n[0]**2 + n[1]**2 + n[2]**2)
                    if n_len > 0:
                        n_unit = (n[0]/n_len, n[1]/n_len, n[2]/n_len)
                    else:
                        n_unit = (0, 0, 0)

                    loc = (
                        target[0] - rotated_mp2_origin[0] + n_unit[0] * mc.offset,
                        target[1] - rotated_mp2_origin[1] + n_unit[1] * mc.offset,
                        target[2] - rotated_mp2_origin[2] + n_unit[2] * mc.offset,
                    )
                    placed[mc.part2_name] = (loc, rot)

        return placed

    def build(self) -> cq.Assembly:
        """Build all components and return a ``cq.Assembly``.

        If constraints have been defined, part positions are computed
        from mate points before building.
        """
        if self._cq_assembly is not None:
            return self._cq_assembly

        # Apply fit specs (adjusts component params before building)
        self._apply_fits()

        # Resolve constraint-based positions
        resolved = self._resolve_constraints()

        assy = cq.Assembly(name=self.name)

        for part in self.parts:
            wp = part.component.build()

            # Use resolved position if available, otherwise manual
            if part.name in resolved:
                loc_tuple, rot_tuple = resolved[part.name]
            else:
                loc_tuple, rot_tuple = part.location, part.rotation

            loc = _make_location(loc_tuple, rot_tuple)

            color_arg = None
            if part.color is not None:
                color_arg = cq.Color(*part.color)

            assy.add(wp, loc=loc, name=part.name, color=color_arg)

        # Add compound components as nested sub-assemblies
        if hasattr(self, '_compounds'):
            for compound, cname, cloc, crot, ccolor in self._compounds:
                sub_assy = compound.build()
                loc = _make_location(cloc, crot)
                color_arg = None
                if ccolor is not None:
                    color_arg = cq.Color(*ccolor)
                assy.add(sub_assy, loc=loc, name=cname, color=color_arg)

        self._cq_assembly = assy
        return assy

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def export_step(self, path: str | Path) -> Path:
        """Export the assembly to a multi-body STEP file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        assy = self.build()
        assy.export(str(path), exportType="STEP")
        return path

    def export_stl(self, path: str | Path) -> Path:
        """Export the assembly to an STL file (merged mesh)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        assy = self.build()
        compound = assy.toCompound()
        exporters.export(compound, str(path), exporters.ExportTypes.STL)
        return path

    # ------------------------------------------------------------------
    # Validation & introspection
    # ------------------------------------------------------------------

    def validate(self) -> list[ValidationResult]:
        """Validate each part individually and run assembly-level checks."""
        results: list[ValidationResult] = []

        if not self.parts:
            results.append(
                ValidationResult(
                    passed=False,
                    check="assembly_not_empty",
                    message="Assembly has no parts",
                )
            )
            return results

        results.append(
            ValidationResult(
                passed=True,
                check="assembly_not_empty",
                message=f"Assembly has {len(self.parts)} part(s)",
            )
        )

        # Per-part validation
        for part in self.parts:
            part_results = part.component.validate()
            for r in part_results:
                results.append(
                    ValidationResult(
                        passed=r.passed,
                        check=f"{part.name}/{r.check}",
                        message=r.message,
                    )
                )

        # Assembly-level: verify all parts build successfully
        try:
            self.build()
            results.append(
                ValidationResult(
                    passed=True,
                    check="assembly_builds",
                    message="Assembly built successfully",
                )
            )
        except Exception as exc:
            results.append(
                ValidationResult(
                    passed=False,
                    check="assembly_builds",
                    message=f"Assembly build failed: {exc}",
                )
            )

        return results

    def bounding_box(self) -> tuple[float, float, float]:
        """Return ``(xlen, ylen, zlen)`` of the whole assembly."""
        assy = self.build()
        compound = assy.toCompound()
        bb = compound.BoundingBox()
        return (bb.xlen, bb.ylen, bb.zlen)

    def parts_list(self) -> list[dict[str, Any]]:
        """Return a BOM-style list of parts (including compound internals)."""
        bom: list[dict[str, Any]] = []
        for part in self.parts:
            bom.append(
                {
                    "name": part.name,
                    "component_type": type(part.component).__name__,
                    "location": list(part.location),
                    "rotation": list(part.rotation),
                }
            )
        if hasattr(self, '_compounds'):
            for compound, cname, cloc, crot, _ in self._compounds:
                bom.append(
                    {
                        "name": cname,
                        "component_type": type(compound).__name__,
                        "is_compound": True,
                        "location": list(cloc),
                        "rotation": list(crot),
                        "sub_parts": compound.parts_list(),
                    }
                )
        return bom

    def metadata(self) -> dict[str, Any]:
        """Return metadata for the full assembly tree."""
        parts_meta: list[dict[str, Any]] = []
        for part in self.parts:
            parts_meta.append(
                {
                    "name": part.name,
                    "component": part.component.metadata(),
                    "location": list(part.location),
                    "rotation": list(part.rotation),
                }
            )

        bbox = self.bounding_box()
        return {
            "assembly": self.name,
            "part_count": len(self.parts),
            "parts": parts_meta,
            "bounding_box": {"x": bbox[0], "y": bbox[1], "z": bbox[2]},
        }

    # ------------------------------------------------------------------
    # JSON serialization (for LLM round-trip)
    # ------------------------------------------------------------------

    def to_spec(self) -> dict[str, Any]:
        """Serialize the assembly to a JSON-compatible spec dict.

        This is the format an LLM would generate.
        """
        from dataclasses import fields as dc_fields

        parts_spec: list[dict[str, Any]] = []
        for part in self.parts:
            comp = part.component
            params: dict[str, Any] = {}
            for f in dc_fields(comp):
                if f.name.startswith("_") or f.name == "name":
                    continue
                params[f.name] = getattr(comp, f.name)

            entry: dict[str, Any] = {
                "type": _component_registry_name(comp),
                "name": part.name,
                "params": params,
                "location": list(part.location),
                "rotation": list(part.rotation),
            }
            if part.color is not None:
                entry["color"] = list(part.color)
            parts_spec.append(entry)

        constraints_spec: list[dict[str, Any]] = []
        for mc in self.constraints:
            entry = {
                "part1": mc.part1_name,
                "mate1": mc.mate1_name,
                "part2": mc.part2_name,
                "mate2": mc.mate2_name,
                "type": mc.constraint_type,
            }
            if mc.offset != 0.0:
                entry["offset"] = mc.offset
            constraints_spec.append(entry)

        fits_spec: list[dict[str, Any]] = []
        for fit in self.fits:
            entry = {
                "source_part": fit.source_part,
                "source_param": fit.source_param,
                "target_part": fit.target_part,
                "target_param": fit.target_param,
                "fit_type": fit.fit_type,
            }
            if fit.allowance != 0.0:
                entry["allowance"] = fit.allowance
            fits_spec.append(entry)

        result: dict[str, Any] = {"name": self.name, "parts": parts_spec}
        if constraints_spec:
            result["constraints"] = constraints_spec
        if fits_spec:
            result["fits"] = fits_spec
        return result

    @classmethod
    def from_spec(cls, spec: dict[str, Any]) -> "Assembly":
        """Build an Assembly from a JSON spec dict.

        Supports three part type formats:

        - **Registry component**: ``"type": "l_bracket"``
        - **Catalog part**: ``"type": "catalog:hex_bolt:M6"``
          (with ``"params": {"length": 20}`` for bolts/screws)
        - **Compounds** via the ``"compounds"`` array

        Full format::

            {
                "name": "my_assembly",
                "parts": [
                    {"type": "l_bracket", "name": "base", "params": {"width": 60}},
                    {"type": "catalog:hex_bolt:M6", "name": "bolt1",
                     "params": {"length": 20}},
                    {"type": "catalog:bearing:608", "name": "brg1"},
                    {"type": "catalog:motor:nema17", "name": "motor1"}
                ],
                "compounds": [
                    {"type": "motorized_joint", "name": "joint1",
                     "params": {"bracket_width": 80}, "location": [0,0,0]}
                ],
                "constraints": [...],
                "fits": [...]
            }
        """
        from .components import REGISTRY

        assy = cls(name=spec.get("name", "assembly"))

        for part_spec in spec.get("parts", []):
            comp_type = part_spec["type"]
            params = part_spec.get("params", {})

            component = _resolve_part_type(comp_type, params, REGISTRY)

            assy.add_part(
                component=component,
                name=part_spec.get("name"),
                location=tuple(part_spec.get("location", [0, 0, 0])),
                rotation=tuple(part_spec.get("rotation", [0, 0, 0])),
                color=(
                    tuple(part_spec["color"])
                    if "color" in part_spec
                    else None
                ),
            )

        # Add compounds
        from .compounds import COMPOUND_REGISTRY
        for comp_spec in spec.get("compounds", []):
            comp_type = comp_spec["type"]
            if comp_type not in COMPOUND_REGISTRY:
                raise ValueError(
                    f"Unknown compound type: '{comp_type}'. "
                    f"Available: {', '.join(sorted(COMPOUND_REGISTRY))}"
                )
            compound_cls = COMPOUND_REGISTRY[comp_type]
            compound_params = comp_spec.get("params", {})
            compound = compound_cls(**compound_params)
            assy.add_compound(
                compound=compound,
                name=comp_spec.get("name"),
                location=tuple(comp_spec.get("location", [0, 0, 0])),
                rotation=tuple(comp_spec.get("rotation", [0, 0, 0])),
            )

        # Apply constraints
        for c_spec in spec.get("constraints", []):
            assy.add_constraint(
                part1_name=c_spec["part1"],
                mate1_name=c_spec["mate1"],
                part2_name=c_spec["part2"],
                mate2_name=c_spec["mate2"],
                constraint_type=c_spec.get("type", "coincident"),
                offset=c_spec.get("offset", 0.0),
            )

        # Apply fits
        for f_spec in spec.get("fits", []):
            assy.add_fit(
                source_part=f_spec["source_part"],
                source_param=f_spec["source_param"],
                target_part=f_spec["target_part"],
                target_param=f_spec["target_param"],
                fit_type=f_spec.get("fit_type", "clearance"),
                allowance=f_spec.get("allowance", 0.0),
            )

        return assy


def _rotation_to_oppose(
    n1: tuple[float, float, float],
    n2: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Compute euler angles (degrees) to rotate n2 so it opposes n1.

    "Opposes" means the rotated n2 equals -n1 (face-to-face contact).
    """
    import math

    # Target direction for n2 after rotation: -n1
    target = (-n1[0], -n1[1], -n1[2])
    return _rotation_between(n2, target)


def _rotation_to_align(
    n1: tuple[float, float, float],
    n2: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Compute euler angles (degrees) to rotate n2 to align with n1."""
    return _rotation_between(n2, n1)


def _rotation_between(
    from_vec: tuple[float, float, float],
    to_vec: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Compute euler XYZ angles (degrees) to rotate from_vec to to_vec.

    Uses a simplified approach: computes the rotation axis and angle,
    then converts to euler angles.  For axis-aligned normals (the
    common case) this produces clean 0/90/180 degree results.
    """
    import math

    fx, fy, fz = from_vec
    tx, ty, tz = to_vec

    f_len = math.sqrt(fx*fx + fy*fy + fz*fz)
    t_len = math.sqrt(tx*tx + ty*ty + tz*tz)

    if f_len == 0 or t_len == 0:
        return (0.0, 0.0, 0.0)

    # Normalize
    fx, fy, fz = fx/f_len, fy/f_len, fz/f_len
    tx, ty, tz = tx/t_len, ty/t_len, tz/t_len

    # Check if already aligned
    dot = fx*tx + fy*ty + fz*tz
    if dot > 0.9999:
        return (0.0, 0.0, 0.0)

    # Check if opposite — rotate 180 around a perpendicular axis
    if dot < -0.9999:
        # Pick a perpendicular axis
        if abs(fx) < 0.9:
            return (180.0, 0.0, 0.0)
        else:
            return (0.0, 180.0, 0.0)

    # Cross product gives rotation axis
    cx = fy*tz - fz*ty
    cy = fz*tx - fx*tz
    cz = fx*ty - fy*tx
    c_len = math.sqrt(cx*cx + cy*cy + cz*cz)
    cx, cy, cz = cx/c_len, cy/c_len, cz/c_len

    angle = math.acos(max(-1.0, min(1.0, dot)))

    # Convert axis-angle to rotation matrix, then extract euler XYZ
    return _axis_angle_to_euler(cx, cy, cz, angle)


def _axis_angle_to_euler(
    ax: float, ay: float, az: float, angle: float
) -> tuple[float, float, float]:
    """Convert axis-angle rotation to euler XYZ angles in degrees."""
    import math

    c = math.cos(angle)
    s = math.sin(angle)
    t = 1 - c

    # Rotation matrix elements
    m00 = c + ax*ax*t
    m01 = ax*ay*t - az*s
    m02 = ax*az*t + ay*s
    m10 = ay*ax*t + az*s
    m11 = c + ay*ay*t
    m12 = ay*az*t - ax*s
    m20 = az*ax*t - ay*s
    m21 = az*ay*t + ax*s
    m22 = c + az*az*t

    # Extract euler XYZ from rotation matrix
    if m20 < -0.9999:
        ry = math.pi / 2
        rx = math.atan2(m01, m02)
        rz = 0.0
    elif m20 > 0.9999:
        ry = -math.pi / 2
        rx = math.atan2(-m01, -m02)
        rz = 0.0
    else:
        ry = math.asin(-m20)
        rx = math.atan2(m21, m22)
        rz = math.atan2(m10, m00)

    return (math.degrees(rx), math.degrees(ry), math.degrees(rz))


def _rotate_point(
    point: tuple[float, float, float],
    euler_xyz: tuple[float, float, float],
) -> tuple[float, float, float]:
    """Rotate a point by euler XYZ angles (degrees)."""
    import math

    rx = math.radians(euler_xyz[0])
    ry = math.radians(euler_xyz[1])
    rz = math.radians(euler_xyz[2])

    x, y, z = point

    # Rotate around X
    y1 = y * math.cos(rx) - z * math.sin(rx)
    z1 = y * math.sin(rx) + z * math.cos(rx)
    x1 = x

    # Rotate around Y
    x2 = x1 * math.cos(ry) + z1 * math.sin(ry)
    z2 = -x1 * math.sin(ry) + z1 * math.cos(ry)
    y2 = y1

    # Rotate around Z
    x3 = x2 * math.cos(rz) - y2 * math.sin(rz)
    y3 = x2 * math.sin(rz) + y2 * math.cos(rz)
    z3 = z2

    return (x3, y3, z3)


def _resolve_part_type(
    type_str: str,
    params: dict[str, Any],
    registry: dict[str, type],
) -> Component:
    """Resolve a part type string to a Component instance.

    Handles both registry names and catalog references.
    """
    if type_str.startswith("catalog:"):
        return _resolve_catalog_part(type_str, params)

    if type_str not in registry:
        raise ValueError(
            f"Unknown component type: '{type_str}'. "
            f"Available: {', '.join(sorted(registry))}"
        )
    comp_cls = registry[type_str]
    return comp_cls(**params)


def _resolve_catalog_part(ref: str, params: dict[str, Any]) -> Component:
    """Resolve a catalog reference like 'catalog:hex_bolt:M6'."""
    from .catalog import get_fastener, get_bearing, get_motor

    parts = ref.split(":")
    if len(parts) < 3:
        raise ValueError(
            f"Invalid catalog reference '{ref}'. "
            f"Expected: catalog:<kind>:<size>"
        )

    kind = parts[1]
    size = parts[2]

    if kind in ("hex_bolt", "socket_head_cap_screw", "hex_nut", "flat_washer"):
        length = params.get("length")
        return get_fastener(kind, size, length=length)
    elif kind == "bearing":
        return get_bearing(size)
    elif kind == "motor":
        return get_motor(size)
    else:
        raise ValueError(f"Unknown catalog kind '{kind}' in '{ref}'")


def _component_registry_name(component: Component) -> str:
    """Look up the registry name for a component instance."""
    from .components import REGISTRY

    comp_type = type(component)
    for name, cls in REGISTRY.items():
        if cls is comp_type:
            return name
    return comp_type.__name__.lower()
