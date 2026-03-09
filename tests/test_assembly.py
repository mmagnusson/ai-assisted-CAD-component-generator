"""Tests for cadforge.assembly module."""

import json
import tempfile
from pathlib import Path

import pytest

from cadforge.assembly import Assembly, AssemblyPart
from cadforge.components.bracket import LBracket
from cadforge.components.bearing_mount import FlangedBearingMount
from cadforge.components.standoff import Standoff


# ------------------------------------------------------------------
# Construction
# ------------------------------------------------------------------


class TestAssemblyConstruction:
    def test_empty_assembly(self):
        assy = Assembly(name="empty")
        assert assy.name == "empty"
        assert len(assy.parts) == 0

    def test_add_single_part(self):
        assy = Assembly(name="test")
        bracket = LBracket(width=40, height=25, thickness=4)
        part = assy.add_part(bracket, name="base")
        assert isinstance(part, AssemblyPart)
        assert part.name == "base"
        assert len(assy.parts) == 1

    def test_add_multiple_parts(self):
        assy = Assembly(name="test")
        assy.add_part(LBracket(), name="bracket")
        assy.add_part(FlangedBearingMount(), name="mount")
        assy.add_part(Standoff(), name="standoff")
        assert len(assy.parts) == 3

    def test_auto_name(self):
        assy = Assembly()
        bracket = LBracket()
        part = assy.add_part(bracket)
        assert part.name == "l_bracket_0"

    def test_duplicate_name_raises(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        with pytest.raises(ValueError, match="Duplicate part name"):
            assy.add_part(LBracket(), name="bracket")

    def test_location_and_rotation(self):
        assy = Assembly()
        part = assy.add_part(
            LBracket(),
            name="bracket",
            location=(10.0, 20.0, 30.0),
            rotation=(0.0, 0.0, 45.0),
        )
        assert part.location == (10.0, 20.0, 30.0)
        assert part.rotation == (0.0, 0.0, 45.0)

    def test_color(self):
        assy = Assembly()
        part = assy.add_part(
            LBracket(),
            name="bracket",
            color=(0.8, 0.2, 0.2, 1.0),
        )
        assert part.color == (0.8, 0.2, 0.2, 1.0)


# ------------------------------------------------------------------
# Build
# ------------------------------------------------------------------


class TestAssemblyBuild:
    def test_build_empty(self):
        import cadquery as cq

        assy = Assembly(name="empty")
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_build_single_part(self):
        import cadquery as cq

        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_build_multi_part(self):
        import cadquery as cq

        assy = Assembly()
        assy.add_part(LBracket(), name="bracket", location=(0, 0, 0))
        assy.add_part(
            FlangedBearingMount(),
            name="mount",
            location=(100, 0, 0),
        )
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_build_with_rotation(self):
        import cadquery as cq

        assy = Assembly()
        assy.add_part(
            LBracket(),
            name="bracket",
            location=(0, 0, 0),
            rotation=(90, 0, 0),
        )
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_build_caches(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        result1 = assy.build()
        result2 = assy.build()
        assert result1 is result2

    def test_add_part_invalidates_cache(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        result1 = assy.build()
        assy.add_part(FlangedBearingMount(), name="mount")
        result2 = assy.build()
        assert result1 is not result2


# ------------------------------------------------------------------
# Export
# ------------------------------------------------------------------


class TestAssemblyExport:
    def test_export_step(self, tmp_path):
        assy = Assembly(name="export_test")
        assy.add_part(LBracket(), name="bracket")
        assy.add_part(
            FlangedBearingMount(), name="mount", location=(100, 0, 0)
        )

        step_path = assy.export_step(tmp_path / "test_assy.step")
        assert step_path.exists()
        assert step_path.stat().st_size > 0

    def test_export_stl(self, tmp_path):
        assy = Assembly(name="export_test")
        assy.add_part(LBracket(), name="bracket")

        stl_path = assy.export_stl(tmp_path / "test_assy.stl")
        assert stl_path.exists()
        assert stl_path.stat().st_size > 0

    def test_export_creates_parent_dirs(self, tmp_path):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        step_path = assy.export_step(tmp_path / "sub" / "dir" / "out.step")
        assert step_path.exists()


# ------------------------------------------------------------------
# Validation
# ------------------------------------------------------------------


class TestAssemblyValidation:
    def test_validate_empty_fails(self):
        assy = Assembly()
        results = assy.validate()
        assert any(not r.passed for r in results)
        assert any("no parts" in r.message for r in results)

    def test_validate_with_parts_passes(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        results = assy.validate()
        assert all(r.passed for r in results)

    def test_validate_prefixes_part_name(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="my_bracket")
        results = assy.validate()
        part_checks = [r for r in results if r.check.startswith("my_bracket/")]
        assert len(part_checks) > 0


# ------------------------------------------------------------------
# Introspection
# ------------------------------------------------------------------


class TestAssemblyIntrospection:
    def test_bounding_box(self):
        assy = Assembly()
        assy.add_part(LBracket(width=50), name="bracket")
        bbox = assy.bounding_box()
        assert len(bbox) == 3
        assert all(d > 0 for d in bbox)

    def test_parts_list(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket", location=(10, 0, 0))
        assy.add_part(FlangedBearingMount(), name="mount")
        bom = assy.parts_list()
        assert len(bom) == 2
        assert bom[0]["name"] == "bracket"
        assert bom[0]["component_type"] == "LBracket"
        assert bom[0]["location"] == [10, 0, 0]

    def test_metadata(self):
        assy = Assembly(name="meta_test")
        assy.add_part(LBracket(), name="bracket")
        meta = assy.metadata()
        assert meta["assembly"] == "meta_test"
        assert meta["part_count"] == 1
        assert len(meta["parts"]) == 1
        assert "bounding_box" in meta


# ------------------------------------------------------------------
# JSON round-trip
# ------------------------------------------------------------------


class TestAssemblySpec:
    def test_to_spec(self):
        assy = Assembly(name="spec_test")
        assy.add_part(
            LBracket(width=60, height=40),
            name="bracket",
            location=(10, 0, 0),
        )
        spec = assy.to_spec()
        assert spec["name"] == "spec_test"
        assert len(spec["parts"]) == 1
        assert spec["parts"][0]["type"] == "l_bracket"
        assert spec["parts"][0]["params"]["width"] == 60

    def test_from_spec(self):
        spec = {
            "name": "from_spec_test",
            "parts": [
                {
                    "type": "l_bracket",
                    "name": "bracket_1",
                    "params": {"width": 70},
                    "location": [0, 0, 0],
                    "rotation": [0, 0, 0],
                },
                {
                    "type": "flanged_bearing_mount",
                    "name": "mount_1",
                    "params": {"bore_diameter": 20},
                    "location": [100, 0, 0],
                    "rotation": [0, 0, 0],
                },
            ],
        }
        assy = Assembly.from_spec(spec)
        assert assy.name == "from_spec_test"
        assert len(assy.parts) == 2
        assert isinstance(assy.parts[0].component, LBracket)
        assert assy.parts[0].component.width == 70

    def test_round_trip(self):
        assy = Assembly(name="roundtrip")
        assy.add_part(
            LBracket(width=55),
            name="bracket",
            location=(5, 10, 15),
            rotation=(0, 0, 45),
        )
        spec = assy.to_spec()

        # Verify it's JSON-serializable
        json_str = json.dumps(spec)
        spec2 = json.loads(json_str)

        assy2 = Assembly.from_spec(spec2)
        assert assy2.name == "roundtrip"
        assert len(assy2.parts) == 1
        assert assy2.parts[0].component.width == 55
        assert assy2.parts[0].location == (5, 10, 15)

    def test_from_spec_unknown_type_raises(self):
        spec = {
            "name": "bad",
            "parts": [{"type": "nonexistent_widget", "name": "x"}],
        }
        with pytest.raises(ValueError, match="Unknown component type"):
            Assembly.from_spec(spec)

    def test_from_spec_with_color(self):
        spec = {
            "name": "colored",
            "parts": [
                {
                    "type": "l_bracket",
                    "name": "red_bracket",
                    "params": {},
                    "color": [1.0, 0.0, 0.0, 1.0],
                },
            ],
        }
        assy = Assembly.from_spec(spec)
        assert assy.parts[0].color == (1.0, 0.0, 0.0, 1.0)


# ------------------------------------------------------------------
# CLI integration (via from_spec, not subprocess)
# ------------------------------------------------------------------


class TestAssemblyCLI:
    def test_spec_file_workflow(self, tmp_path):
        """Simulate the CLI file-based workflow."""
        spec = {
            "name": "cli_test",
            "parts": [
                {
                    "type": "l_bracket",
                    "name": "base",
                    "params": {"width": 50},
                    "location": [0, 0, 0],
                    "rotation": [0, 0, 0],
                },
                {
                    "type": "standoff",
                    "name": "post",
                    "params": {},
                    "location": [25, 25, 5],
                    "rotation": [0, 0, 0],
                },
            ],
        }

        spec_file = tmp_path / "assembly.json"
        spec_file.write_text(json.dumps(spec))

        # Load and build
        loaded_spec = json.loads(spec_file.read_text())
        assy = Assembly.from_spec(loaded_spec)
        assert len(assy.parts) == 2

        # Export
        step_path = assy.export_step(tmp_path / "cli_test.step")
        assert step_path.exists()
