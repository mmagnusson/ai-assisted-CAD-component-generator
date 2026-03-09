"""Tests for mate points and assembly constraints (Phase 2)."""

import json
import math

import pytest

from cadforge.core import MatePoint
from cadforge.assembly import Assembly, MateConstraint
from cadforge.components.bracket import LBracket
from cadforge.components.bearing_mount import FlangedBearingMount
from cadforge.components.shaft_coupler import ShaftCoupler
from cadforge.components.standoff import Standoff
from cadforge.components.enclosure import Enclosure


# ------------------------------------------------------------------
# MatePoint basics
# ------------------------------------------------------------------


class TestMatePoint:
    def test_create_mate_point(self):
        mp = MatePoint(
            name="top",
            origin=(0.0, 0.0, 10.0),
            normal=(0.0, 0.0, 1.0),
        )
        assert mp.name == "top"
        assert mp.origin == (0.0, 0.0, 10.0)
        assert mp.normal == (0.0, 0.0, 1.0)
        assert mp.mate_type == "face"

    def test_mate_type_axis(self):
        mp = MatePoint(
            name="bore",
            origin=(0, 0, 0),
            normal=(0, 0, 1),
            mate_type="axis",
        )
        assert mp.mate_type == "axis"


# ------------------------------------------------------------------
# Component.mates()
# ------------------------------------------------------------------


class TestComponentMates:
    def test_base_component_no_mates(self):
        from cadforge.core import Component
        c = Component()
        assert c.mates() == []

    def test_bracket_has_mates(self):
        bracket = LBracket(width=50, height=30, thickness=5)
        mates = bracket.mates()
        assert len(mates) == 3
        names = {m.name for m in mates}
        assert "horizontal_face" in names
        assert "horizontal_bottom" in names
        assert "vertical_face" in names

    def test_bracket_mate_positions(self):
        bracket = LBracket(width=60, height=40, thickness=5)
        mates = {m.name: m for m in bracket.mates()}

        h_face = mates["horizontal_face"]
        assert h_face.origin == (30.0, 30.0, 5.0)
        assert h_face.normal == (0.0, 0.0, 1.0)

        h_bottom = mates["horizontal_bottom"]
        assert h_bottom.origin == (30.0, 30.0, 0.0)
        assert h_bottom.normal == (0.0, 0.0, -1.0)

    def test_bearing_mount_has_mates(self):
        mount = FlangedBearingMount(
            flange_thickness=10, hub_height=20
        )
        mates = mount.mates()
        assert len(mates) == 3
        names = {m.name for m in mates}
        assert "bottom" in names
        assert "top" in names
        assert "bore_axis" in names

    def test_bearing_mount_top_position(self):
        mount = FlangedBearingMount(
            flange_thickness=10, hub_height=20
        )
        mates = {m.name: m for m in mount.mates()}
        assert mates["top"].origin == (0.0, 0.0, 30.0)
        assert mates["bore_axis"].origin == (0.0, 0.0, 15.0)
        assert mates["bore_axis"].mate_type == "axis"

    def test_shaft_coupler_has_mates(self):
        coupler = ShaftCoupler(length=40)
        mates = coupler.mates()
        assert len(mates) == 3
        names = {m.name for m in mates}
        assert "bore_1_entry" in names
        assert "bore_2_entry" in names
        assert "center_axis" in names

    def test_shaft_coupler_positions(self):
        coupler = ShaftCoupler(length=50)
        mates = {m.name: m for m in coupler.mates()}
        assert mates["bore_1_entry"].origin == (0.0, 0.0, 0.0)
        assert mates["bore_2_entry"].origin == (0.0, 0.0, 50.0)
        assert mates["center_axis"].origin == (0.0, 0.0, 25.0)

    def test_standoff_has_mates(self):
        standoff = Standoff(height=15)
        mates = standoff.mates()
        assert len(mates) == 3
        names = {m.name for m in mates}
        assert "bottom" in names
        assert "top" in names
        assert "center_axis" in names

    def test_standoff_top_position(self):
        standoff = Standoff(height=12)
        mates = {m.name: m for m in standoff.mates()}
        assert mates["top"].origin == (0.0, 0.0, 12.0)

    def test_enclosure_has_mates(self):
        enc = Enclosure(length=100, width=60, height=40)
        mates = enc.mates()
        assert len(mates) == 6
        names = {m.name for m in mates}
        assert names == {"bottom", "top", "front", "back", "left", "right"}

    def test_enclosure_positions(self):
        enc = Enclosure(length=100, width=60, height=40)
        mates = {m.name: m for m in enc.mates()}
        assert mates["top"].origin == (0.0, 0.0, 40.0)
        assert mates["right"].origin == (50.0, 0.0, 20.0)
        assert mates["front"].normal == (0.0, -1.0, 0.0)


# ------------------------------------------------------------------
# MateConstraint
# ------------------------------------------------------------------


class TestMateConstraint:
    def test_create_constraint(self):
        mc = MateConstraint(
            part1_name="bracket",
            mate1_name="top",
            part2_name="mount",
            mate2_name="bottom",
        )
        assert mc.constraint_type == "coincident"
        assert mc.offset == 0.0

    def test_add_constraint_to_assembly(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        assy.add_part(FlangedBearingMount(), name="mount")
        mc = assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
        )
        assert isinstance(mc, MateConstraint)
        assert len(assy.constraints) == 1

    def test_add_constraint_invalid_part_raises(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        with pytest.raises(ValueError, match="not found in assembly"):
            assy.add_constraint("bracket", "top", "ghost", "bottom")

    def test_add_constraint_invalid_mate_raises(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        assy.add_part(FlangedBearingMount(), name="mount")
        with pytest.raises(ValueError, match="Mate.*not found"):
            assy.add_constraint("bracket", "nonexistent", "mount", "bottom")

    def test_constraint_invalidates_cache(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="bracket")
        assy.add_part(FlangedBearingMount(), name="mount")
        r1 = assy.build()
        assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
        )
        r2 = assy.build()
        assert r1 is not r2


# ------------------------------------------------------------------
# Constraint solving — positioning
# ------------------------------------------------------------------


class TestConstraintSolving:
    def test_coincident_z_face(self):
        """Mount's bottom should land on bracket's horizontal face."""
        assy = Assembly()
        assy.add_part(
            LBracket(width=50, height=30, thickness=5),
            name="bracket",
            location=(0, 0, 0),
        )
        assy.add_part(FlangedBearingMount(), name="mount")
        assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
        )
        assy.build()

        # After solving, mount should be positioned so its bottom
        # (z=0 in local coords) aligns with bracket's horizontal_face
        # (which is at z=5 in bracket's local frame, at (25, 25, 5)).
        resolved = assy._resolve_constraints()
        mount_loc = resolved["mount"][0]

        # The mount's origin (0,0,0) + location should put its
        # bottom face at bracket's horizontal_face origin
        assert mount_loc[2] == pytest.approx(5.0, abs=0.01)

    def test_coincident_positions_part(self):
        """Verify the positioned mount is at the expected world location."""
        assy = Assembly()
        bracket = LBracket(width=50, height=30, thickness=5)
        assy.add_part(bracket, name="bracket", location=(0, 0, 0))

        mount = FlangedBearingMount(
            flange_thickness=10, hub_height=20
        )
        assy.add_part(mount, name="mount")

        assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
        )

        resolved = assy._resolve_constraints()
        mount_loc = resolved["mount"][0]

        # bracket's horizontal_face is at (25, 25, 5)
        # mount's bottom mate is at (0, 0, 0) in local frame
        # So mount should be placed at (25, 25, 5)
        assert mount_loc[0] == pytest.approx(25.0, abs=0.01)
        assert mount_loc[1] == pytest.approx(25.0, abs=0.01)
        assert mount_loc[2] == pytest.approx(5.0, abs=0.01)

    def test_coaxial_constraint(self):
        """Two parts with coaxial constraint should share axis position."""
        assy = Assembly()
        mount = FlangedBearingMount(
            flange_thickness=10, hub_height=20
        )
        coupler = ShaftCoupler(length=40)

        assy.add_part(mount, name="mount", location=(0, 0, 0))
        assy.add_part(coupler, name="coupler")

        assy.add_constraint(
            "mount", "bore_axis",
            "coupler", "center_axis",
            constraint_type="coaxial",
        )

        resolved = assy._resolve_constraints()
        coupler_loc = resolved["coupler"][0]

        # mount bore_axis is at (0, 0, 15)
        # coupler center_axis is at (0, 0, 20) in local frame
        # After alignment, coupler should be at x=0, y=0
        assert coupler_loc[0] == pytest.approx(0.0, abs=0.01)
        assert coupler_loc[1] == pytest.approx(0.0, abs=0.01)

    def test_offset_constraint(self):
        """Offset constraint should leave a gap between parts."""
        assy = Assembly()
        bracket = LBracket(width=50, height=30, thickness=5)
        standoff = Standoff(height=10)

        assy.add_part(bracket, name="bracket", location=(0, 0, 0))
        assy.add_part(standoff, name="standoff")

        assy.add_constraint(
            "bracket", "horizontal_face",
            "standoff", "bottom",
            constraint_type="offset",
            offset=2.0,
        )

        resolved = assy._resolve_constraints()
        standoff_loc = resolved["standoff"][0]

        # bracket's horizontal_face normal is (0, 0, 1) at z=5
        # offset of 2mm along that normal → standoff at z=7
        # But standoff bottom is at (0,0,0) local, and its normal
        # is (0,0,-1), so it needs to be flipped.
        # After flip, bottom is still at origin, placed at z=5+2=7
        assert standoff_loc[2] == pytest.approx(7.0, abs=0.01)

    def test_unconstrained_parts_keep_location(self):
        """Parts without constraints stay at their manual location."""
        assy = Assembly()
        assy.add_part(
            LBracket(), name="bracket",
            location=(100, 200, 300),
        )
        resolved = assy._resolve_constraints()
        assert "bracket" not in resolved

    def test_chain_of_constraints(self):
        """Three parts chained: bracket → standoff → mount."""
        assy = Assembly()
        bracket = LBracket(width=50, height=30, thickness=5)
        standoff = Standoff(height=10)
        mount = FlangedBearingMount(flange_thickness=8, hub_height=15)

        assy.add_part(bracket, name="bracket", location=(0, 0, 0))
        assy.add_part(standoff, name="standoff")
        assy.add_part(mount, name="mount")

        # standoff on top of bracket
        assy.add_constraint(
            "bracket", "horizontal_face",
            "standoff", "bottom",
        )
        # mount on top of standoff
        assy.add_constraint(
            "standoff", "top",
            "mount", "bottom",
        )

        resolved = assy._resolve_constraints()

        standoff_z = resolved["standoff"][0][2]
        assert standoff_z == pytest.approx(5.0, abs=0.01)

        mount_z = resolved["mount"][0][2]
        # standoff top is at standoff_loc + height = 5 + 10 = 15
        # But we need to account for standoff's placement.
        # standoff is placed so its bottom (0,0,0) + flip is at
        # bracket's horizontal_face (25, 25, 5).
        # standoff top mate is at (0, 0, 10) local.
        # After flip (180 around X), the top mate origin (0,0,10)
        # becomes (0, 0, -10). So in world: (25, 25, 5) + (0, 0, -10)?
        # Wait — let me reconsider. The standoff bottom normal is
        # (0,0,-1) and bracket horizontal_face normal is (0,0,1).
        # To oppose: rotated n2 should equal -(0,0,1) = (0,0,-1).
        # n2 is (0,0,-1), target is (0,0,-1). They're already equal!
        # So rotation is (0,0,0). Standoff keeps its orientation.
        # standoff placed at (25, 25, 5).
        # standoff top mate in local = (0, 0, 10), world = (25, 25, 15).
        # mount bottom in local = (0, 0, 0) with normal (0,0,-1).
        # To oppose standoff top normal (0,0,1): mount rotated so its
        # bottom normal becomes (0,0,-1). It's already (0,0,-1) → no rotation.
        # mount placed at (25, 25, 15).
        assert mount_z == pytest.approx(15.0, abs=0.01)

    def test_build_with_constraints_exports(self, tmp_path):
        """Assembly with constraints should export a valid STEP file."""
        assy = Assembly(name="constrained")
        assy.add_part(
            LBracket(width=50, height=30, thickness=5),
            name="bracket",
            location=(0, 0, 0),
        )
        assy.add_part(FlangedBearingMount(), name="mount")
        assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
        )

        step_path = assy.export_step(tmp_path / "constrained.step")
        assert step_path.exists()
        assert step_path.stat().st_size > 0


# ------------------------------------------------------------------
# JSON round-trip with constraints
# ------------------------------------------------------------------


class TestConstraintSpec:
    def test_to_spec_includes_constraints(self):
        assy = Assembly(name="test")
        assy.add_part(LBracket(), name="bracket")
        assy.add_part(FlangedBearingMount(), name="mount")
        assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
        )
        spec = assy.to_spec()
        assert "constraints" in spec
        assert len(spec["constraints"]) == 1
        c = spec["constraints"][0]
        assert c["part1"] == "bracket"
        assert c["mate1"] == "horizontal_face"
        assert c["type"] == "coincident"

    def test_to_spec_no_constraints(self):
        assy = Assembly(name="test")
        assy.add_part(LBracket(), name="bracket")
        spec = assy.to_spec()
        assert "constraints" not in spec

    def test_from_spec_with_constraints(self):
        spec = {
            "name": "constrained_test",
            "parts": [
                {"type": "l_bracket", "name": "bracket", "params": {"width": 50, "height": 30, "thickness": 5}},
                {"type": "flanged_bearing_mount", "name": "mount", "params": {}},
            ],
            "constraints": [
                {
                    "part1": "bracket",
                    "mate1": "horizontal_face",
                    "part2": "mount",
                    "mate2": "bottom",
                    "type": "coincident",
                },
            ],
        }
        assy = Assembly.from_spec(spec)
        assert len(assy.constraints) == 1
        assert assy.constraints[0].part1_name == "bracket"

    def test_round_trip_with_constraints(self):
        assy = Assembly(name="roundtrip")
        assy.add_part(LBracket(), name="bracket")
        assy.add_part(FlangedBearingMount(), name="mount")
        assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
            constraint_type="offset",
            offset=3.0,
        )

        spec = assy.to_spec()
        json_str = json.dumps(spec)
        spec2 = json.loads(json_str)
        assy2 = Assembly.from_spec(spec2)

        assert len(assy2.constraints) == 1
        assert assy2.constraints[0].constraint_type == "offset"
        assert assy2.constraints[0].offset == 3.0
