"""LLM planning layer for CAD Forge.

Provides the JSON schema for assembly specifications, validation of
specs before building, and introspection utilities that give an LLM
the context it needs to generate valid assembly specs.

The LLM workflow:
1. Query available parts:  ``get_available_parts()``
2. Generate a JSON spec conforming to ``ASSEMBLY_SCHEMA``
3. Validate the spec:  ``validate_spec(spec)``
4. Build:  ``Assembly.from_spec(spec)``
"""

from __future__ import annotations

from dataclasses import fields as dc_fields
from typing import Any


# ------------------------------------------------------------------
# JSON Schema for assembly specifications
# ------------------------------------------------------------------

ASSEMBLY_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "CAD Forge Assembly Specification",
    "description": (
        "Defines a multi-part CAD assembly for CAD Forge. "
        "An LLM generates this JSON to produce 3D geometry."
    ),
    "type": "object",
    "required": ["name", "parts"],
    "properties": {
        "name": {
            "type": "string",
            "description": "Name of the assembly (used for output filenames).",
        },
        "parts": {
            "type": "array",
            "description": "List of parts in the assembly.",
            "items": {
                "type": "object",
                "required": ["type", "name"],
                "properties": {
                    "type": {
                        "type": "string",
                        "description": (
                            "Component type. Use a registry name (e.g. 'l_bracket'), "
                            "or a catalog reference: 'catalog:hex_bolt:M6' / "
                            "'catalog:bearing:608' / 'catalog:motor:nema17'."
                        ),
                    },
                    "name": {
                        "type": "string",
                        "description": "Unique name for this part in the assembly.",
                    },
                    "params": {
                        "type": "object",
                        "description": "Component parameters (varies by type).",
                    },
                    "location": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 3,
                        "maxItems": 3,
                        "description": "Position [x, y, z] in mm.",
                    },
                    "rotation": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 3,
                        "maxItems": 3,
                        "description": "Euler XYZ rotation [rx, ry, rz] in degrees.",
                    },
                    "color": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                        "description": "RGBA color [r, g, b, a] where each is 0-1.",
                    },
                },
            },
        },
        "compounds": {
            "type": "array",
            "description": "Compound sub-assemblies (optional).",
            "items": {
                "type": "object",
                "required": ["type", "name"],
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Compound type from COMPOUND_REGISTRY.",
                    },
                    "name": {
                        "type": "string",
                        "description": "Unique name for this compound.",
                    },
                    "params": {
                        "type": "object",
                        "description": "Compound parameters.",
                    },
                    "location": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 3,
                        "maxItems": 3,
                    },
                    "rotation": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 3,
                        "maxItems": 3,
                    },
                },
            },
        },
        "constraints": {
            "type": "array",
            "description": "Mate constraints between parts (optional).",
            "items": {
                "type": "object",
                "required": ["part1", "mate1", "part2", "mate2"],
                "properties": {
                    "part1": {"type": "string"},
                    "mate1": {"type": "string"},
                    "part2": {"type": "string"},
                    "mate2": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": ["coincident", "coaxial", "offset"],
                        "default": "coincident",
                    },
                    "offset": {"type": "number", "default": 0.0},
                },
            },
        },
        "fits": {
            "type": "array",
            "description": "Dimensional fit specifications (optional).",
            "items": {
                "type": "object",
                "required": [
                    "source_part", "source_param",
                    "target_part", "target_param",
                ],
                "properties": {
                    "source_part": {"type": "string"},
                    "source_param": {"type": "string"},
                    "target_part": {"type": "string"},
                    "target_param": {"type": "string"},
                    "fit_type": {
                        "type": "string",
                        "enum": ["clearance", "transition", "interference", "exact"],
                        "default": "clearance",
                    },
                    "allowance": {"type": "number", "default": 0.0},
                },
            },
        },
    },
}


# ------------------------------------------------------------------
# Introspection: what's available for the LLM
# ------------------------------------------------------------------


def get_available_parts() -> dict[str, Any]:
    """Return a complete manifest of available parts for LLM context.

    Returns a dict with sections for components, catalog parts,
    and compounds — each listing parameters, defaults, and mate points.
    """
    return {
        "components": _list_components(),
        "catalog": _list_catalog(),
        "compounds": _list_compounds(),
    }


def get_component_info(name: str) -> dict[str, Any]:
    """Return detailed info about a specific component, catalog part, or compound.

    Args:
        name: Registry name (e.g. "l_bracket"), catalog ref (e.g.
              "catalog:hex_bolt:M6"), or compound name (e.g. "motorized_joint").

    Returns:
        Dict with parameters, defaults, mate points, and description.
    """
    # Check catalog references
    if name.startswith("catalog:"):
        return _catalog_part_info(name)

    # Check component registry
    from .components import REGISTRY
    if name in REGISTRY:
        return _component_info(name, REGISTRY[name])

    # Check compound registry
    from .compounds import COMPOUND_REGISTRY
    if name in COMPOUND_REGISTRY:
        return _compound_info(name, COMPOUND_REGISTRY[name])

    raise ValueError(
        f"Unknown part '{name}'. Use get_available_parts() to see options."
    )


def _list_components() -> list[dict[str, Any]]:
    """List all registered components with their parameters."""
    from .components import REGISTRY

    result = []
    for name, cls in sorted(REGISTRY.items()):
        result.append(_component_info(name, cls))
    return result


def _component_info(name: str, cls: type) -> dict[str, Any]:
    """Build info dict for a component class."""
    params = []
    for f in dc_fields(cls):
        if f.name.startswith("_") or f.name == "name":
            continue
        params.append({
            "name": f.name,
            "type": f.type if isinstance(f.type, str) else str(f.type),
            "default": f.default if f.default is not f.default_factory else None,
        } if not hasattr(f.default, '__call__') else {
            "name": f.name,
            "type": str(f.type),
        })

    # Get mate points from a default instance
    try:
        instance = cls()
        mate_names = [m.name for m in instance.mates()]
    except Exception:
        mate_names = []

    return {
        "name": name,
        "class": cls.__name__,
        "doc": (cls.__doc__ or "").strip().split("\n")[0],
        "parameters": params,
        "mates": mate_names,
    }


def _list_catalog() -> dict[str, Any]:
    """List catalog parts organized by category."""
    from .catalog.fasteners import BOLT_TABLE, NUT_TABLE, WASHER_TABLE
    from .catalog.bearings import BEARING_TABLE
    from .catalog.motors import MOTOR_TABLE

    return {
        "fasteners": {
            "hex_bolt": {
                "sizes": sorted(BOLT_TABLE.keys()),
                "requires_length": True,
                "spec_type": "catalog:hex_bolt:<SIZE>",
                "mates": ["head_top", "head_bearing", "shank_end", "axis"],
            },
            "socket_head_cap_screw": {
                "sizes": sorted(BOLT_TABLE.keys()),
                "requires_length": True,
                "spec_type": "catalog:socket_head_cap_screw:<SIZE>",
                "mates": ["head_top", "head_bearing", "shank_end", "axis"],
            },
            "hex_nut": {
                "sizes": sorted(NUT_TABLE.keys()),
                "spec_type": "catalog:hex_nut:<SIZE>",
                "mates": ["bottom", "top", "axis"],
            },
            "flat_washer": {
                "sizes": sorted(WASHER_TABLE.keys()),
                "spec_type": "catalog:flat_washer:<SIZE>",
                "mates": ["bottom", "top", "axis"],
            },
        },
        "bearings": {
            "designations": sorted(BEARING_TABLE.keys()),
            "spec_type": "catalog:bearing:<DESIGNATION>",
            "mates": ["front", "back", "bore_axis"],
        },
        "motors": {
            "frames": sorted(MOTOR_TABLE.keys()),
            "spec_type": "catalog:motor:<FRAME>",
            "mates": ["faceplate", "back", "shaft_tip", "shaft_axis"],
        },
    }


def _catalog_part_info(ref: str) -> dict[str, Any]:
    """Parse a catalog reference and return info."""
    parts = ref.split(":")
    if len(parts) < 3:
        raise ValueError(
            f"Invalid catalog reference '{ref}'. "
            f"Expected format: catalog:<kind>:<size>"
        )

    _, kind, size = parts[0], parts[1], parts[2]

    from .catalog import get_fastener, get_bearing, get_motor

    if kind in ("hex_bolt", "socket_head_cap_screw"):
        # Just show dimensions, don't require length for info
        from .catalog.fasteners import BOLT_TABLE
        size_upper = size.upper()
        if size_upper not in BOLT_TABLE:
            raise ValueError(f"Unknown size '{size}' for {kind}")
        dims = BOLT_TABLE[size_upper]
        return {
            "name": ref,
            "category": "fastener",
            "kind": kind,
            "size": size_upper,
            "dimensions": dims,
            "requires_length": True,
            "mates": ["head_top", "head_bearing", "shank_end", "axis"],
        }
    elif kind == "hex_nut":
        from .catalog.fasteners import NUT_TABLE
        size_upper = size.upper()
        if size_upper not in NUT_TABLE:
            raise ValueError(f"Unknown size '{size}' for hex_nut")
        return {
            "name": ref,
            "category": "fastener",
            "kind": "hex_nut",
            "size": size_upper,
            "dimensions": NUT_TABLE[size_upper],
            "mates": ["bottom", "top", "axis"],
        }
    elif kind == "flat_washer":
        from .catalog.fasteners import WASHER_TABLE
        size_upper = size.upper()
        if size_upper not in WASHER_TABLE:
            raise ValueError(f"Unknown size '{size}' for flat_washer")
        return {
            "name": ref,
            "category": "fastener",
            "kind": "flat_washer",
            "size": size_upper,
            "dimensions": WASHER_TABLE[size_upper],
            "mates": ["bottom", "top", "axis"],
        }
    elif kind == "bearing":
        from .catalog.bearings import BEARING_TABLE
        if size not in BEARING_TABLE:
            raise ValueError(f"Unknown bearing '{size}'")
        return {
            "name": ref,
            "category": "bearing",
            "designation": size,
            "dimensions": BEARING_TABLE[size],
            "mates": ["front", "back", "bore_axis"],
        }
    elif kind == "motor":
        from .catalog.motors import MOTOR_TABLE
        frame = size.lower()
        if frame not in MOTOR_TABLE:
            raise ValueError(f"Unknown motor frame '{size}'")
        return {
            "name": ref,
            "category": "motor",
            "frame": frame,
            "dimensions": MOTOR_TABLE[frame],
            "mates": ["faceplate", "back", "shaft_tip", "shaft_axis"],
        }
    else:
        raise ValueError(f"Unknown catalog kind '{kind}'")


def _list_compounds() -> list[dict[str, Any]]:
    """List all registered compounds."""
    from .compounds import COMPOUND_REGISTRY

    result = []
    for name, cls in sorted(COMPOUND_REGISTRY.items()):
        result.append(_compound_info(name, cls))
    return result


def _compound_info(name: str, cls: type) -> dict[str, Any]:
    """Build info dict for a compound class."""
    params = []
    for f in dc_fields(cls):
        if f.name.startswith("_") or f.name == "name":
            continue
        if not hasattr(f.default, '__call__'):
            params.append({
                "name": f.name,
                "type": f.type if isinstance(f.type, str) else str(f.type),
                "default": f.default,
            })

    try:
        instance = cls()
        mate_names = [m.name for m in instance.mates()]
        sub_parts = [comp_name for _, comp_name in instance.components()]
    except Exception:
        mate_names = []
        sub_parts = []

    return {
        "name": name,
        "class": cls.__name__,
        "doc": (cls.__doc__ or "").strip().split("\n")[0],
        "parameters": params,
        "mates": mate_names,
        "sub_parts": sub_parts,
    }


# ------------------------------------------------------------------
# Spec validation
# ------------------------------------------------------------------


def validate_spec(spec: dict[str, Any]) -> list[str]:
    """Validate an assembly spec without building it.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    if not isinstance(spec, dict):
        return ["Spec must be a JSON object"]

    if "name" not in spec:
        errors.append("Missing required field: 'name'")

    if "parts" not in spec:
        errors.append("Missing required field: 'parts'")
        return errors

    if not isinstance(spec["parts"], list):
        errors.append("'parts' must be an array")
        return errors

    # Collect part names for constraint/fit validation
    part_names: set[str] = set()
    for i, part in enumerate(spec["parts"]):
        prefix = f"parts[{i}]"

        if not isinstance(part, dict):
            errors.append(f"{prefix}: must be an object")
            continue

        if "type" not in part:
            errors.append(f"{prefix}: missing 'type'")
        else:
            _validate_part_type(part["type"], part.get("params", {}), prefix, errors)

        if "name" not in part:
            errors.append(f"{prefix}: missing 'name'")
        else:
            if part["name"] in part_names:
                errors.append(f"{prefix}: duplicate name '{part['name']}'")
            part_names.add(part["name"])

    # Validate compounds
    compound_names: set[str] = set()
    for i, comp in enumerate(spec.get("compounds", [])):
        prefix = f"compounds[{i}]"
        if "type" not in comp:
            errors.append(f"{prefix}: missing 'type'")
        else:
            from .compounds import COMPOUND_REGISTRY
            if comp["type"] not in COMPOUND_REGISTRY:
                errors.append(
                    f"{prefix}: unknown compound type '{comp['type']}'"
                )
        if "name" not in comp:
            errors.append(f"{prefix}: missing 'name'")
        else:
            if comp["name"] in part_names or comp["name"] in compound_names:
                errors.append(f"{prefix}: duplicate name '{comp['name']}'")
            compound_names.add(comp["name"])

    all_names = part_names | compound_names

    # Validate constraints
    for i, c in enumerate(spec.get("constraints", [])):
        prefix = f"constraints[{i}]"
        for field in ("part1", "mate1", "part2", "mate2"):
            if field not in c:
                errors.append(f"{prefix}: missing '{field}'")
        if "part1" in c and c["part1"] not in all_names:
            errors.append(f"{prefix}: unknown part '{c['part1']}'")
        if "part2" in c and c["part2"] not in all_names:
            errors.append(f"{prefix}: unknown part '{c['part2']}'")
        if "type" in c and c["type"] not in ("coincident", "coaxial", "offset"):
            errors.append(f"{prefix}: invalid type '{c['type']}'")

    # Validate fits
    for i, f in enumerate(spec.get("fits", [])):
        prefix = f"fits[{i}]"
        for field in ("source_part", "source_param", "target_part", "target_param"):
            if field not in f:
                errors.append(f"{prefix}: missing '{field}'")
        if "source_part" in f and f["source_part"] not in all_names:
            errors.append(f"{prefix}: unknown part '{f['source_part']}'")
        if "target_part" in f and f["target_part"] not in all_names:
            errors.append(f"{prefix}: unknown part '{f['target_part']}'")
        if "fit_type" in f and f["fit_type"] not in (
            "clearance", "transition", "interference", "exact"
        ):
            errors.append(f"{prefix}: invalid fit_type '{f['fit_type']}'")

    return errors


def _validate_part_type(
    type_str: str,
    params: dict,
    prefix: str,
    errors: list[str],
) -> None:
    """Validate a part type reference."""
    if type_str.startswith("catalog:"):
        parts = type_str.split(":")
        if len(parts) < 3:
            errors.append(
                f"{prefix}: invalid catalog reference '{type_str}', "
                f"expected 'catalog:<kind>:<size>'"
            )
            return
        kind = parts[1]
        valid_kinds = {
            "hex_bolt", "socket_head_cap_screw",
            "hex_nut", "flat_washer", "bearing", "motor",
        }
        if kind not in valid_kinds:
            errors.append(
                f"{prefix}: unknown catalog kind '{kind}', "
                f"valid: {', '.join(sorted(valid_kinds))}"
            )
        if kind in ("hex_bolt", "socket_head_cap_screw"):
            if "length" not in params:
                errors.append(
                    f"{prefix}: '{kind}' requires 'length' in params"
                )
    else:
        from .components import REGISTRY
        if type_str not in REGISTRY:
            errors.append(
                f"{prefix}: unknown component type '{type_str}'"
            )
