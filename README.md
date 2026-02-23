# CAD Forge 🔧

**AI-Assisted CAD Component Generation for Claude Code**

CAD Forge is a Python framework that enables Claude Code (or any LLM agent) to generate
parametric CAD components from natural language prompts. It uses CadQuery as the geometry
engine and provides automated validation, testing, and export pipelines.

Built for Projects Sidekick & Wayland.

## Architecture

```
Prompt → CAD Forge CLI → CadQuery Generation → Validation Pipeline → Output Package
                              │                        │
                              ▼                        ▼
                        Parametric .py           Geometry checks
                        source script            Dimensional verify
                                                 Manufacturability
                                                 Visual QA render
```

## Quick Start

```bash
# Install dependencies
pip install cadquery pytest

# Generate a component from the CLI
python -m cadforge generate --type bracket \
    --params '{"width": 50, "height": 30, "thickness": 5, "hole_diameter": 6, "fillet_radius": 2}'

# Run validation suite
python -m cadforge validate output/bracket.step

# Run all tests
pytest tests/ -v
```

## Usage with Claude Code

From Claude Code, invoke CAD Forge directly:

```bash
cd cad-forge
python -m cadforge generate --type flanged_bearing_mount \
    --params '{"bore_diameter": 25, "bolt_circle_diameter": 60, "bolt_count": 4, "bolt_diameter": 6}'
```

Or use the Python API:

```python
from cadforge.components.bearing_mount import FlangedBearingMount

part = FlangedBearingMount(
    bore_diameter=25,
    bolt_circle_diameter=60,
    bolt_count=4,
    bolt_diameter=6
)
result = part.build()
result.export("output/bearing_mount.step")
```

## Component Library

| Component | Description | Key Parameters |
|-----------|-------------|----------------|
| `l_bracket` | L-shaped mounting bracket | width, height, thickness, holes |
| `flanged_bearing_mount` | Bearing housing with bolt pattern | bore, bolt circle, bolt count |
| `enclosure` | Rectangular electronics enclosure | length, width, height, wall thickness |
| `standoff` | PCB mounting standoff | height, thread size, base diameter |
| `shaft_coupler` | Shaft-to-shaft coupler | bore1, bore2, length, set screws |

## Validation Pipeline

Every generated component passes through:

1. **Geometry Validation** — Solid is valid, watertight, no self-intersections
2. **Dimensional Verification** — Bounding box and feature dimensions match spec
3. **Manufacturability Checks** — Min wall thickness, hole depth ratios, printability
4. **Export Verification** — STEP file is valid and re-importable

## Testing

```bash
# Full test suite
pytest tests/ -v

# Just geometry validation tests
pytest tests/test_validators.py -v

# Component-specific tests
pytest tests/test_components.py -v

# Parametric sweep tests (stress testing)
pytest tests/test_parametric_sweep.py -v
```

## Project Structure

```
cad-forge/
├── cadforge/
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   ├── core.py              # Base component class
│   ├── components/          # Parametric component library
│   │   ├── __init__.py
│   │   ├── bracket.py
│   │   ├── bearing_mount.py
│   │   ├── enclosure.py
│   │   └── standoff.py
│   ├── validators/          # Automated validation
│   │   ├── __init__.py
│   │   ├── geometry.py
│   │   └── manufacturing.py
│   └── renderers/           # Visual QA
│       ├── __init__.py
│       └── svg_renderer.py
├── tests/
│   ├── test_components.py
│   ├── test_validators.py
│   └── test_parametric_sweep.py
├── examples/
│   └── generate_all.py
├── output/                  # Generated files land here
└── README.md
```

## License

MIT — Use freely in Sidekick, Wayland, and beyond.
