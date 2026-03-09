"""Tests for compound components (Phase 3)."""

import json

import pytest

import cadquery as cq

from cadforge.assembly import Assembly, MateConstraint
from cadforge.core import MatePoint
from cadforge.compounds import CompoundComponent, COMPOUND_REGISTRY
from cadforge.compounds.motorized_joint import MotorizedJoint
from cadforge.compounds.pillow_block import PillowBlock


# ------------------------------------------------------------------
# CompoundComponent base class
# ------------------------------------------------------------------


class TestCompoundComponentBase:
    def test_base_not_implemented(self):
        cc = CompoundComponent()
        with pytest.raises(NotImplementedError):
            cc.components()

    def test_base_mates_empty(self):
        cc = CompoundComponent()
        assert cc.mates() == []

    def test_base_internal_constraints_empty(self):
        cc = CompoundComponent()
        assert cc.internal_constraints() == []


# ------------------------------------------------------------------
# Registry
# ------------------------------------------------------------------


class TestCompoundRegistry:
    def test_motorized_joint_registered(self):
        assert "motorized_joint" in COMPOUND_REGISTRY

    def test_pillow_block_registered(self):
        assert "pillow_block" in COMPOUND_REGISTRY

    def test_registry_classes(self):
        assert COMPOUND_REGISTRY["motorized_joint"] is MotorizedJoint
        assert COMPOUND_REGISTRY["pillow_block"] is PillowBlock


# ------------------------------------------------------------------
# MotorizedJoint
# ------------------------------------------------------------------


class TestMotorizedJoint:
    def test_default_construction(self):
        mj = MotorizedJoint()
        assert mj.name == "motorized_joint"
        assert mj.motor_shaft_diameter == 8.0
        assert mj.output_shaft_diameter == 10.0

    def test_custom_params(self):
        mj = MotorizedJoint(
            motor_shaft_diameter=6.0,
            bearing_bore=20.0,
            bracket_width=100.0,
        )
        assert mj.motor_shaft_diameter == 6.0
        assert mj.bearing_bore == 20.0
        assert mj.bracket_width == 100.0

    def test_components_list(self):
        mj = MotorizedJoint()
        comps = mj.components()
        assert len(comps) == 3
        names = [name for _, name in comps]
        assert "base_bracket" in names
        assert "bearing_mount" in names
        assert "shaft_coupler" in names

    def test_internal_constraints(self):
        mj = MotorizedJoint()
        constraints = mj.internal_constraints()
        assert len(constraints) == 2
        assert all(isinstance(c, MateConstraint) for c in constraints)

    def test_mates(self):
        mj = MotorizedJoint()
        mates = mj.mates()
        assert len(mates) == 4
        names = {m.name for m in mates}
        assert "base_bottom" in names
        assert "bearing_top" in names
        assert "output_axis" in names
        assert "vertical_face" in names

    def test_get_assembly(self):
        mj = MotorizedJoint()
        assy = mj.get_assembly()
        assert isinstance(assy, Assembly)
        assert len(assy.parts) == 3
        assert len(assy.constraints) == 2

    def test_build(self):
        mj = MotorizedJoint()
        result = mj.build()
        assert isinstance(result, cq.Assembly)

    def test_bounding_box(self):
        mj = MotorizedJoint()
        bbox = mj.bounding_box()
        assert len(bbox) == 3
        assert all(d > 0 for d in bbox)

    def test_parts_list(self):
        mj = MotorizedJoint()
        bom = mj.parts_list()
        assert len(bom) == 3

    def test_metadata(self):
        mj = MotorizedJoint()
        meta = mj.metadata()
        assert meta["compound"] == "MotorizedJoint"
        assert "mates" in meta
        assert len(meta["mates"]) == 4
        assert "assembly" in meta

    def test_export_step(self, tmp_path):
        mj = MotorizedJoint()
        assy = mj.get_assembly()
        path = assy.export_step(tmp_path / "motorized_joint.step")
        assert path.exists()
        assert path.stat().st_size > 0

    def test_caches_assembly(self):
        mj = MotorizedJoint()
        a1 = mj.get_assembly()
        a2 = mj.get_assembly()
        assert a1 is a2


# ------------------------------------------------------------------
# PillowBlock
# ------------------------------------------------------------------


class TestPillowBlock:
    def test_default_construction(self):
        pb = PillowBlock()
        assert pb.name == "pillow_block"
        assert pb.bearing_bore == 25.0
        assert pb.standoff_height == 20.0

    def test_components_list(self):
        pb = PillowBlock()
        comps = pb.components()
        assert len(comps) == 3
        names = [name for _, name in comps]
        assert "standoff_left" in names
        assert "standoff_right" in names
        assert "bearing" in names

    def test_internal_constraints(self):
        pb = PillowBlock()
        constraints = pb.internal_constraints()
        assert len(constraints) == 1

    def test_mates(self):
        pb = PillowBlock()
        mates = pb.mates()
        assert len(mates) == 4
        names = {m.name for m in mates}
        assert "base_left" in names
        assert "base_right" in names
        assert "bearing_top" in names
        assert "bore_axis" in names

    def test_build(self):
        pb = PillowBlock()
        result = pb.build()
        assert isinstance(result, cq.Assembly)

    def test_bounding_box(self):
        pb = PillowBlock()
        bbox = pb.bounding_box()
        assert all(d > 0 for d in bbox)

    def test_export_step(self, tmp_path):
        pb = PillowBlock()
        assy = pb.get_assembly()
        path = assy.export_step(tmp_path / "pillow_block.step")
        assert path.exists()
        assert path.stat().st_size > 0


# ------------------------------------------------------------------
# Adding compounds to Assembly
# ------------------------------------------------------------------


class TestAssemblyWithCompounds:
    def test_add_compound(self):
        assy = Assembly(name="test")
        mj = MotorizedJoint()
        name = assy.add_compound(mj, name="joint_1")
        assert name == "joint_1"

    def test_add_compound_auto_name(self):
        assy = Assembly(name="test")
        mj = MotorizedJoint()
        name = assy.add_compound(mj)
        assert name == "motorized_joint_0"

    def test_add_compound_duplicate_raises(self):
        assy = Assembly(name="test")
        assy.add_compound(MotorizedJoint(), name="joint")
        with pytest.raises(ValueError, match="Duplicate"):
            assy.add_compound(MotorizedJoint(), name="joint")

    def test_add_non_compound_raises(self):
        from cadforge.components.bracket import LBracket
        assy = Assembly(name="test")
        with pytest.raises(TypeError, match="CompoundComponent"):
            assy.add_compound(LBracket(), name="bracket")

    def test_build_with_compound(self):
        assy = Assembly(name="test")
        assy.add_compound(MotorizedJoint(), name="joint_1")
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_build_mixed_parts_and_compounds(self):
        from cadforge.components.bracket import LBracket

        assy = Assembly(name="mixed")
        assy.add_part(LBracket(), name="base_plate")
        assy.add_compound(
            MotorizedJoint(),
            name="joint_1",
            location=(0, 0, 5),
        )
        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_export_with_compound(self, tmp_path):
        from cadforge.components.bracket import LBracket

        assy = Assembly(name="compound_export")
        assy.add_part(LBracket(width=100), name="base")
        assy.add_compound(
            MotorizedJoint(),
            name="joint",
            location=(50, 50, 5),
        )
        path = assy.export_step(tmp_path / "with_compound.step")
        assert path.exists()
        assert path.stat().st_size > 0

    def test_parts_list_includes_compounds(self):
        assy = Assembly(name="test")
        assy.add_compound(MotorizedJoint(), name="joint_1")
        bom = assy.parts_list()
        assert len(bom) == 1
        assert bom[0]["name"] == "joint_1"
        assert bom[0]["is_compound"] is True
        assert len(bom[0]["sub_parts"]) == 3

    def test_multiple_compounds(self, tmp_path):
        """Build an assembly with two motorized joints — like a 2-DOF arm."""
        assy = Assembly(name="two_dof_arm")
        assy.add_compound(
            MotorizedJoint(bracket_width=80),
            name="shoulder",
            location=(0, 0, 0),
        )
        assy.add_compound(
            MotorizedJoint(bracket_width=60),
            name="elbow",
            location=(100, 0, 0),
        )

        result = assy.build()
        assert isinstance(result, cq.Assembly)

        path = assy.export_step(tmp_path / "two_dof.step")
        assert path.exists()

        bom = assy.parts_list()
        assert len(bom) == 2
        total_sub_parts = sum(len(b["sub_parts"]) for b in bom)
        assert total_sub_parts == 6  # 3 parts per joint
