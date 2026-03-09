"""Tests for the LLM planning layer (Phase 6)."""

import json

import pytest

import cadquery as cq

from cadforge.planner import (
    ASSEMBLY_SCHEMA,
    get_available_parts,
    get_component_info,
    validate_spec,
)
from cadforge.assembly import Assembly


# ------------------------------------------------------------------
# Schema
# ------------------------------------------------------------------


class TestSchema:
    def test_schema_is_valid_json_schema(self):
        assert ASSEMBLY_SCHEMA["type"] == "object"
        assert "parts" in ASSEMBLY_SCHEMA["properties"]
        assert "constraints" in ASSEMBLY_SCHEMA["properties"]
        assert "fits" in ASSEMBLY_SCHEMA["properties"]
        assert "compounds" in ASSEMBLY_SCHEMA["properties"]

    def test_schema_is_json_serializable(self):
        json_str = json.dumps(ASSEMBLY_SCHEMA)
        parsed = json.loads(json_str)
        assert parsed["title"] == "CAD Forge Assembly Specification"


# ------------------------------------------------------------------
# get_available_parts
# ------------------------------------------------------------------


class TestGetAvailableParts:
    def test_returns_three_sections(self):
        parts = get_available_parts()
        assert "components" in parts
        assert "catalog" in parts
        assert "compounds" in parts

    def test_components_list(self):
        parts = get_available_parts()
        components = parts["components"]
        assert isinstance(components, list)
        assert len(components) > 0
        # Check structure of first component
        first = components[0]
        assert "name" in first
        assert "parameters" in first
        assert "mates" in first

    def test_catalog_sections(self):
        parts = get_available_parts()
        catalog = parts["catalog"]
        assert "fasteners" in catalog
        assert "bearings" in catalog
        assert "motors" in catalog

    def test_catalog_fasteners(self):
        parts = get_available_parts()
        fasteners = parts["catalog"]["fasteners"]
        assert "hex_bolt" in fasteners
        assert "M6" in fasteners["hex_bolt"]["sizes"]
        assert "hex_nut" in fasteners
        assert "flat_washer" in fasteners

    def test_catalog_bearings(self):
        parts = get_available_parts()
        bearings = parts["catalog"]["bearings"]
        assert "608" in bearings["designations"]
        assert "6205" in bearings["designations"]

    def test_catalog_motors(self):
        parts = get_available_parts()
        motors = parts["catalog"]["motors"]
        assert "nema17" in motors["frames"]

    def test_compounds_list(self):
        parts = get_available_parts()
        compounds = parts["compounds"]
        assert isinstance(compounds, list)
        names = [c["name"] for c in compounds]
        assert "motorized_joint" in names
        assert "pillow_block" in names

    def test_compound_has_mates(self):
        parts = get_available_parts()
        compounds = {c["name"]: c for c in parts["compounds"]}
        mj = compounds["motorized_joint"]
        assert "mates" in mj
        assert len(mj["mates"]) > 0

    def test_is_json_serializable(self):
        parts = get_available_parts()
        json_str = json.dumps(parts, default=str)
        parsed = json.loads(json_str)
        assert "components" in parsed


# ------------------------------------------------------------------
# get_component_info
# ------------------------------------------------------------------


class TestGetComponentInfo:
    def test_registry_component(self):
        info = get_component_info("l_bracket")
        assert info["name"] == "l_bracket"
        assert info["class"] == "LBracket"
        assert len(info["parameters"]) > 0
        assert "horizontal_face" in info["mates"]

    def test_catalog_bolt(self):
        info = get_component_info("catalog:hex_bolt:M6")
        assert info["category"] == "fastener"
        assert info["size"] == "M6"
        assert info["requires_length"] is True

    def test_catalog_bearing(self):
        info = get_component_info("catalog:bearing:608")
        assert info["category"] == "bearing"
        assert info["dimensions"]["bore"] == 8.0

    def test_catalog_motor(self):
        info = get_component_info("catalog:motor:nema17")
        assert info["category"] == "motor"
        assert info["frame"] == "nema17"

    def test_compound(self):
        info = get_component_info("motorized_joint")
        assert info["class"] == "MotorizedJoint"
        assert len(info["sub_parts"]) == 3

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown part"):
            get_component_info("nonexistent_widget")

    def test_invalid_catalog_ref(self):
        with pytest.raises(ValueError):
            get_component_info("catalog:bad")


# ------------------------------------------------------------------
# validate_spec
# ------------------------------------------------------------------


class TestValidateSpec:
    def test_valid_spec(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "l_bracket", "name": "bracket", "params": {}},
            ],
        }
        errors = validate_spec(spec)
        assert errors == []

    def test_missing_name(self):
        spec = {"parts": []}
        errors = validate_spec(spec)
        assert any("name" in e for e in errors)

    def test_missing_parts(self):
        spec = {"name": "test"}
        errors = validate_spec(spec)
        assert any("parts" in e for e in errors)

    def test_missing_part_type(self):
        spec = {
            "name": "test",
            "parts": [{"name": "x"}],
        }
        errors = validate_spec(spec)
        assert any("type" in e for e in errors)

    def test_missing_part_name(self):
        spec = {
            "name": "test",
            "parts": [{"type": "l_bracket"}],
        }
        errors = validate_spec(spec)
        assert any("name" in e for e in errors)

    def test_unknown_component_type(self):
        spec = {
            "name": "test",
            "parts": [{"type": "fake_widget", "name": "x"}],
        }
        errors = validate_spec(spec)
        assert any("unknown component" in e for e in errors)

    def test_duplicate_names(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "l_bracket", "name": "x"},
                {"type": "l_bracket", "name": "x"},
            ],
        }
        errors = validate_spec(spec)
        assert any("duplicate" in e for e in errors)

    def test_catalog_type_valid(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "catalog:hex_bolt:M6", "name": "bolt",
                 "params": {"length": 20}},
            ],
        }
        errors = validate_spec(spec)
        assert errors == []

    def test_catalog_bolt_missing_length(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "catalog:hex_bolt:M6", "name": "bolt"},
            ],
        }
        errors = validate_spec(spec)
        assert any("length" in e for e in errors)

    def test_catalog_bearing_valid(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "catalog:bearing:608", "name": "brg"},
            ],
        }
        errors = validate_spec(spec)
        assert errors == []

    def test_invalid_catalog_kind(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "catalog:sprocket:XL", "name": "x"},
            ],
        }
        errors = validate_spec(spec)
        assert any("catalog kind" in e for e in errors)

    def test_invalid_catalog_format(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "catalog:bad", "name": "x"},
            ],
        }
        errors = validate_spec(spec)
        assert any("catalog reference" in e for e in errors)

    def test_constraint_unknown_part(self):
        spec = {
            "name": "test",
            "parts": [{"type": "l_bracket", "name": "a"}],
            "constraints": [
                {"part1": "a", "mate1": "top", "part2": "ghost", "mate2": "bottom"},
            ],
        }
        errors = validate_spec(spec)
        assert any("ghost" in e for e in errors)

    def test_constraint_invalid_type(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "l_bracket", "name": "a"},
                {"type": "l_bracket", "name": "b"},
            ],
            "constraints": [
                {"part1": "a", "mate1": "top", "part2": "b",
                 "mate2": "bottom", "type": "glue"},
            ],
        }
        errors = validate_spec(spec)
        assert any("invalid type" in e for e in errors)

    def test_fit_unknown_part(self):
        spec = {
            "name": "test",
            "parts": [{"type": "l_bracket", "name": "a"}],
            "fits": [
                {"source_part": "a", "source_param": "width",
                 "target_part": "ghost", "target_param": "width"},
            ],
        }
        errors = validate_spec(spec)
        assert any("ghost" in e for e in errors)

    def test_fit_invalid_type(self):
        spec = {
            "name": "test",
            "parts": [
                {"type": "l_bracket", "name": "a"},
                {"type": "l_bracket", "name": "b"},
            ],
            "fits": [
                {"source_part": "a", "source_param": "width",
                 "target_part": "b", "target_param": "width",
                 "fit_type": "magic"},
            ],
        }
        errors = validate_spec(spec)
        assert any("fit_type" in e for e in errors)

    def test_compound_valid(self):
        spec = {
            "name": "test",
            "parts": [],
            "compounds": [
                {"type": "motorized_joint", "name": "joint1"},
            ],
        }
        errors = validate_spec(spec)
        assert errors == []

    def test_compound_unknown_type(self):
        spec = {
            "name": "test",
            "parts": [],
            "compounds": [
                {"type": "antigravity_device", "name": "x"},
            ],
        }
        errors = validate_spec(spec)
        assert any("unknown compound" in e for e in errors)


# ------------------------------------------------------------------
# Assembly.from_spec with catalog and compounds
# ------------------------------------------------------------------


class TestFromSpecExtended:
    def test_catalog_bolt_from_spec(self):
        spec = {
            "name": "bolt_test",
            "parts": [
                {"type": "catalog:hex_bolt:M6", "name": "bolt",
                 "params": {"length": 20}},
            ],
        }
        assy = Assembly.from_spec(spec)
        assert len(assy.parts) == 1
        bolt = assy.parts[0].component
        assert bolt.thread_diameter == 6.0
        assert bolt.length == 20.0
        assy.build()

    def test_catalog_bearing_from_spec(self):
        spec = {
            "name": "bearing_test",
            "parts": [
                {"type": "catalog:bearing:608", "name": "brg"},
            ],
        }
        assy = Assembly.from_spec(spec)
        brg = assy.parts[0].component
        assert brg.bore == 8.0
        assy.build()

    def test_catalog_motor_from_spec(self):
        spec = {
            "name": "motor_test",
            "parts": [
                {"type": "catalog:motor:nema17", "name": "motor"},
            ],
        }
        assy = Assembly.from_spec(spec)
        motor = assy.parts[0].component
        assert motor.faceplate_width == 42.3
        assy.build()

    def test_compound_from_spec(self):
        spec = {
            "name": "compound_test",
            "parts": [],
            "compounds": [
                {"type": "motorized_joint", "name": "joint",
                 "params": {"bracket_width": 100},
                 "location": [0, 0, 0]},
            ],
        }
        assy = Assembly.from_spec(spec)
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_mixed_spec(self, tmp_path):
        """Full spec with registry parts, catalog parts, compounds,
        constraints, and fits."""
        spec = {
            "name": "robot_joint",
            "parts": [
                {"type": "l_bracket", "name": "base",
                 "params": {"width": 80, "height": 40, "thickness": 5},
                 "location": [0, 0, 0]},
                {"type": "catalog:hex_bolt:M6", "name": "bolt1",
                 "params": {"length": 20},
                 "location": [20, 40, 5]},
                {"type": "catalog:bearing:6001", "name": "bearing",
                 "location": [40, 40, 5]},
                {"type": "catalog:motor:nema17", "name": "motor",
                 "location": [40, 40, 20]},
                {"type": "shaft_coupler", "name": "coupler",
                 "params": {"bore_1": 5.0, "bore_2": 12.0},
                 "location": [40, 40, 46]},
            ],
            "fits": [
                {"source_part": "motor", "source_param": "shaft_diameter",
                 "target_part": "coupler", "target_param": "bore_1",
                 "fit_type": "clearance"},
            ],
        }

        errors = validate_spec(spec)
        assert errors == [], f"Validation errors: {errors}"

        assy = Assembly.from_spec(spec)
        path = assy.export_step(tmp_path / "robot_joint.step")
        assert path.exists()
        assert path.stat().st_size > 0

        # Verify fit was applied
        coupler = assy._get_part("coupler").component
        assert coupler.bore_1 > 5.0  # clearance applied

    def test_validate_then_build_workflow(self):
        """Simulate the LLM workflow: validate first, then build."""
        spec = {
            "name": "workflow_test",
            "parts": [
                {"type": "l_bracket", "name": "base", "params": {}},
                {"type": "catalog:hex_nut:M8", "name": "nut"},
            ],
        }
        # Step 1: validate
        errors = validate_spec(spec)
        assert errors == []

        # Step 2: build
        assy = Assembly.from_spec(spec)
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_invalid_catalog_ref_in_from_spec(self):
        spec = {
            "name": "bad",
            "parts": [
                {"type": "catalog:sprocket:XL", "name": "x"},
            ],
        }
        with pytest.raises(ValueError):
            Assembly.from_spec(spec)
