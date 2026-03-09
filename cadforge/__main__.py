"""CLI entry point for CAD Forge.

Usage::

    python -m cadforge generate --type l_bracket --params '{"width": 40}'
    python -m cadforge list
    python -m cadforge validate output/part.step
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__


def cmd_generate(args: argparse.Namespace) -> None:
    """Generate a component and export STEP, STL, and SVG."""
    from .components import REGISTRY

    comp_name: str = args.type
    if comp_name not in REGISTRY:
        print(f"Error: unknown component '{comp_name}'")
        print(f"Available: {', '.join(sorted(REGISTRY))}")
        sys.exit(1)

    params: dict = {}
    if args.params:
        params = json.loads(args.params)

    cls = REGISTRY[comp_name]
    component = cls(**params)

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    step_path = component.export_step(outdir / f"{comp_name}.step")
    stl_path = component.export_stl(outdir / f"{comp_name}.stl")
    svg_path = component.export_svg(outdir / f"{comp_name}.svg")

    print(f"Generated '{comp_name}':")
    print(f"  STEP -> {step_path}")
    print(f"  STL  -> {stl_path}")
    print(f"  SVG  -> {svg_path}")

    bbox = component.bounding_box()
    print(f"  BBox -> {bbox[0]:.2f} x {bbox[1]:.2f} x {bbox[2]:.2f} mm")


def cmd_list(args: argparse.Namespace) -> None:
    """List all registered components."""
    from .components import REGISTRY

    if not REGISTRY:
        print("No components registered.")
        return

    print(f"Available components ({len(REGISTRY)}):")
    for name, cls in sorted(REGISTRY.items()):
        print(f"  {name:30s} {cls.__name__}")


def cmd_assemble(args: argparse.Namespace) -> None:
    """Assemble multiple components from a JSON spec."""
    from .assembly import Assembly

    if args.file:
        spec_path = Path(args.file)
        if not spec_path.exists():
            print(f"Error: file not found: {spec_path}")
            sys.exit(1)
        spec = json.loads(spec_path.read_text())
    elif args.spec:
        spec = json.loads(args.spec)
    else:
        print("Error: provide --spec JSON or --file path")
        sys.exit(1)

    assembly = Assembly.from_spec(spec)

    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    assy_name = assembly.name
    step_path = assembly.export_step(outdir / f"{assy_name}.step")
    stl_path = assembly.export_stl(outdir / f"{assy_name}.stl")

    print(f"Assembled '{assy_name}' ({len(assembly.parts)} parts):")
    print(f"  STEP -> {step_path}")
    print(f"  STL  -> {stl_path}")

    for entry in assembly.parts_list():
        print(f"  Part: {entry['name']} ({entry['component_type']})")

    bbox = assembly.bounding_box()
    print(f"  BBox -> {bbox[0]:.2f} x {bbox[1]:.2f} x {bbox[2]:.2f} mm")


def cmd_schema(args: argparse.Namespace) -> None:
    """Output the assembly JSON schema and available parts."""
    from .planner import ASSEMBLY_SCHEMA, get_available_parts

    if args.parts:
        info = get_available_parts()
        print(json.dumps(info, indent=2, default=str))
    else:
        print(json.dumps(ASSEMBLY_SCHEMA, indent=2))


def cmd_inspect(args: argparse.Namespace) -> None:
    """Show detailed info about a component, catalog part, or compound."""
    from .planner import get_component_info

    try:
        info = get_component_info(args.name)
        print(json.dumps(info, indent=2, default=str))
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate a STEP file."""
    from .validators import validate_solid

    step_path = Path(args.step_file)
    if not step_path.exists():
        print(f"Error: file not found: {step_path}")
        sys.exit(1)

    import cadquery as cq

    wp = cq.importers.importStep(str(step_path))
    solid = wp.val()

    results = validate_solid(solid)

    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"  [{status}] {r.check}: {r.message}")

    print(f"\n{passed} passed, {failed} failed out of {len(results)} checks.")
    if failed > 0:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="cadforge",
        description="CAD Forge - AI-Assisted CAD Component Generation",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # -- generate --
    gen_parser = subparsers.add_parser(
        "generate", help="Generate a component"
    )
    gen_parser.add_argument(
        "--type", required=True, help="Component type name"
    )
    gen_parser.add_argument(
        "--params",
        default=None,
        help="JSON string of component parameters",
    )
    gen_parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output/)",
    )
    gen_parser.set_defaults(func=cmd_generate)

    # -- list --
    list_parser = subparsers.add_parser(
        "list", help="List available components"
    )
    list_parser.set_defaults(func=cmd_list)

    # -- assemble --
    asm_parser = subparsers.add_parser(
        "assemble", help="Assemble components from a JSON spec"
    )
    asm_parser.add_argument(
        "--spec",
        default=None,
        help="JSON string of assembly specification",
    )
    asm_parser.add_argument(
        "--file",
        default=None,
        help="Path to a JSON assembly spec file",
    )
    asm_parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output/)",
    )
    asm_parser.set_defaults(func=cmd_assemble)

    # -- schema --
    schema_parser = subparsers.add_parser(
        "schema", help="Show assembly JSON schema or available parts"
    )
    schema_parser.add_argument(
        "--parts",
        action="store_true",
        help="List available parts instead of the schema",
    )
    schema_parser.set_defaults(func=cmd_schema)

    # -- inspect --
    inspect_parser = subparsers.add_parser(
        "inspect", help="Show details for a component/catalog/compound"
    )
    inspect_parser.add_argument(
        "name",
        help=(
            "Component name (e.g. 'l_bracket'), catalog ref "
            "(e.g. 'catalog:hex_bolt:M6'), or compound name"
        ),
    )
    inspect_parser.set_defaults(func=cmd_inspect)

    # -- validate --
    val_parser = subparsers.add_parser(
        "validate", help="Validate a STEP file"
    )
    val_parser.add_argument("step_file", help="Path to STEP file")
    val_parser.set_defaults(func=cmd_validate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
