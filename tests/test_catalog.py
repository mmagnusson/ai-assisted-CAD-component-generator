"""Tests for the standard parts catalog (Phase 5)."""

import pytest

import cadquery as cq

from cadforge.catalog import get_fastener, get_bearing, get_motor
from cadforge.catalog.fasteners import (
    BOLT_TABLE, NUT_TABLE, WASHER_TABLE,
    HexBolt, SocketHeadCapScrew, HexNut, FlatWasher,
)
from cadforge.catalog.bearings import BEARING_TABLE, DeepGrooveBearing
from cadforge.catalog.motors import MOTOR_TABLE, NemaMotor
from cadforge.assembly import Assembly


# ------------------------------------------------------------------
# Fastener tables
# ------------------------------------------------------------------


class TestFastenerTables:
    def test_bolt_table_has_common_sizes(self):
        for size in ["M3", "M4", "M5", "M6", "M8", "M10"]:
            assert size in BOLT_TABLE

    def test_nut_table_matches_bolt_sizes(self):
        for size in BOLT_TABLE:
            assert size in NUT_TABLE, f"Missing nut for {size}"

    def test_washer_table_matches_bolt_sizes(self):
        for size in BOLT_TABLE:
            assert size in WASHER_TABLE, f"Missing washer for {size}"

    def test_bolt_dimensions_sane(self):
        for size, dims in BOLT_TABLE.items():
            assert dims["head_diameter"] > dims["thread_diameter"]
            assert dims["head_height"] > 0


# ------------------------------------------------------------------
# Fastener components — build and geometry
# ------------------------------------------------------------------


class TestHexBolt:
    def test_build(self):
        bolt = HexBolt(thread_diameter=6.0, head_diameter=10.0,
                       head_height=4.0, length=20.0)
        wp = bolt.build()
        assert wp.val().isValid()

    def test_mates(self):
        bolt = HexBolt(length=25.0, head_height=4.0)
        mates = {m.name: m for m in bolt.mates()}
        assert "head_top" in mates
        assert "head_bearing" in mates
        assert "shank_end" in mates
        assert "axis" in mates
        assert mates["shank_end"].origin[2] == -25.0

    def test_bounding_box_height(self):
        bolt = HexBolt(head_height=4.0, length=20.0)
        bbox = bolt.bounding_box()
        assert bbox[2] == pytest.approx(24.0, abs=0.5)


class TestSocketHeadCapScrew:
    def test_build(self):
        screw = SocketHeadCapScrew(thread_diameter=6.0, head_diameter=10.0,
                                   head_height=6.0, length=20.0)
        wp = screw.build()
        assert wp.val().isValid()

    def test_mates(self):
        screw = SocketHeadCapScrew(length=30.0, head_height=6.0)
        mates = {m.name: m for m in screw.mates()}
        assert mates["shank_end"].origin[2] == -30.0
        assert mates["head_top"].origin[2] == 6.0


class TestHexNut:
    def test_build(self):
        nut = HexNut(thread_diameter=6.0, across_flats=10.0, height=5.2)
        wp = nut.build()
        assert wp.val().isValid()

    def test_mates(self):
        nut = HexNut(height=5.2)
        mates = {m.name: m for m in nut.mates()}
        assert mates["top"].origin[2] == 5.2


class TestFlatWasher:
    def test_build(self):
        washer = FlatWasher(inner_diameter=6.4, outer_diameter=12.0,
                            thickness=1.6)
        wp = washer.build()
        assert wp.val().isValid()

    def test_mates(self):
        washer = FlatWasher(thickness=2.0)
        mates = {m.name: m for m in washer.mates()}
        assert mates["top"].origin[2] == 2.0


# ------------------------------------------------------------------
# get_fastener() lookup
# ------------------------------------------------------------------


class TestGetFastener:
    def test_hex_bolt_m6(self):
        bolt = get_fastener("hex_bolt", "M6", length=20)
        assert isinstance(bolt, HexBolt)
        assert bolt.thread_diameter == 6.0
        assert bolt.length == 20.0
        bolt.build()  # should not raise

    def test_hex_bolt_case_insensitive(self):
        bolt = get_fastener("hex_bolt", "m8", length=30)
        assert bolt.thread_diameter == 8.0

    def test_socket_head_cap_screw(self):
        screw = get_fastener("socket_head_cap_screw", "M5", length=16)
        assert isinstance(screw, SocketHeadCapScrew)
        assert screw.thread_diameter == 5.0
        screw.build()

    def test_hex_nut(self):
        nut = get_fastener("hex_nut", "M10")
        assert isinstance(nut, HexNut)
        assert nut.thread_diameter == 10.0
        nut.build()

    def test_flat_washer(self):
        washer = get_fastener("flat_washer", "M6")
        assert isinstance(washer, FlatWasher)
        assert washer.inner_diameter == 6.4
        washer.build()

    def test_unknown_kind_raises(self):
        with pytest.raises(ValueError, match="Unknown fastener kind"):
            get_fastener("wing_nut", "M6")

    def test_unknown_size_raises(self):
        with pytest.raises(ValueError, match="Unknown bolt size"):
            get_fastener("hex_bolt", "M7", length=20)

    def test_bolt_without_length_raises(self):
        with pytest.raises(ValueError, match="length is required"):
            get_fastener("hex_bolt", "M6")

    @pytest.mark.parametrize("size", list(BOLT_TABLE.keys()))
    def test_all_bolt_sizes_build(self, size):
        bolt = get_fastener("hex_bolt", size, length=20)
        wp = bolt.build()
        assert wp.val().isValid()

    @pytest.mark.parametrize("size", list(NUT_TABLE.keys()))
    def test_all_nut_sizes_build(self, size):
        nut = get_fastener("hex_nut", size)
        wp = nut.build()
        assert wp.val().isValid()


# ------------------------------------------------------------------
# Bearings
# ------------------------------------------------------------------


class TestBearingTable:
    def test_common_bearings_present(self):
        for d in ["608", "6001", "6200", "6205"]:
            assert d in BEARING_TABLE

    def test_dimensions_sane(self):
        for des, dims in BEARING_TABLE.items():
            assert dims["outer_diameter"] > dims["bore"]
            assert dims["width"] > 0


class TestDeepGrooveBearing:
    def test_build_608(self):
        b = DeepGrooveBearing(bore=8.0, outer_diameter=22.0, width=7.0)
        wp = b.build()
        assert wp.val().isValid()

    def test_mates(self):
        b = DeepGrooveBearing(width=7.0)
        mates = {m.name: m for m in b.mates()}
        assert "front" in mates
        assert "back" in mates
        assert "bore_axis" in mates
        assert mates["back"].origin[2] == 7.0


class TestGetBearing:
    def test_608(self):
        b = get_bearing("608")
        assert isinstance(b, DeepGrooveBearing)
        assert b.bore == 8.0
        assert b.outer_diameter == 22.0
        b.build()

    def test_6205(self):
        b = get_bearing("6205")
        assert b.bore == 25.0
        b.build()

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown bearing"):
            get_bearing("9999")

    @pytest.mark.parametrize("designation", list(BEARING_TABLE.keys()))
    def test_all_bearings_build(self, designation):
        b = get_bearing(designation)
        wp = b.build()
        assert wp.val().isValid()


# ------------------------------------------------------------------
# Motors
# ------------------------------------------------------------------


class TestMotorTable:
    def test_nema_sizes_present(self):
        for frame in ["nema14", "nema17", "nema23", "nema34"]:
            assert frame in MOTOR_TABLE


class TestNemaMotor:
    def test_build_nema17(self):
        m = NemaMotor()
        wp = m.build()
        assert wp.val().isValid()

    def test_mates(self):
        m = NemaMotor(shaft_length=24.0, pilot_height=2.0, body_length=48.0)
        mates = {m.name: m for m in m.mates()}
        assert "faceplate" in mates
        assert "back" in mates
        assert "shaft_tip" in mates
        assert "shaft_axis" in mates
        assert mates["shaft_tip"].origin[2] == 26.0
        assert mates["back"].origin[2] == -48.0


class TestGetMotor:
    def test_nema17(self):
        m = get_motor("nema17")
        assert isinstance(m, NemaMotor)
        assert m.faceplate_width == 42.3
        m.build()

    def test_case_insensitive(self):
        m = get_motor("NEMA23")
        assert m.shaft_diameter == 6.35

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown motor frame"):
            get_motor("nema99")

    @pytest.mark.parametrize("frame", list(MOTOR_TABLE.keys()))
    def test_all_motors_build(self, frame):
        m = get_motor(frame)
        wp = m.build()
        assert wp.val().isValid()


# ------------------------------------------------------------------
# Integration: catalog parts in assemblies
# ------------------------------------------------------------------


class TestCatalogInAssembly:
    def test_bolt_in_assembly(self):
        assy = Assembly(name="bolted")
        bolt = get_fastener("hex_bolt", "M6", length=20)
        washer = get_fastener("flat_washer", "M6")
        nut = get_fastener("hex_nut", "M6")

        assy.add_part(bolt, name="bolt")
        assy.add_part(washer, name="washer")
        assy.add_part(nut, name="nut")

        result = assy.build()
        assert isinstance(result, cq.Assembly)

    def test_bearing_with_fit(self):
        from cadforge.components.shaft_coupler import ShaftCoupler

        assy = Assembly(name="shaft_bearing")
        bearing = get_bearing("6205")  # 25mm bore
        coupler = ShaftCoupler(bore_2=25.0)

        assy.add_part(coupler, name="coupler")
        assy.add_part(bearing, name="bearing")

        # Shaft coupler bore_2 drives bearing bore with clearance
        assy.add_fit(
            "coupler", "bore_2",
            "bearing", "bore",
            fit_type="clearance",
        )

        assy.build()
        assert bearing.bore > 25.0  # clearance applied

    def test_motor_with_coupler(self, tmp_path):
        from cadforge.components.shaft_coupler import ShaftCoupler

        assy = Assembly(name="motor_drive")
        motor = get_motor("nema17")
        coupler = ShaftCoupler(bore_1=5.0, bore_2=8.0)

        assy.add_part(motor, name="motor", location=(0, 0, 0))
        assy.add_part(coupler, name="coupler")

        # Mate coupler to motor shaft
        assy.add_constraint(
            "motor", "shaft_tip",
            "coupler", "bore_1_entry",
        )
        # Shaft diameter drives coupler bore
        assy.add_fit(
            "motor", "shaft_diameter",
            "coupler", "bore_1",
            fit_type="clearance",
        )

        path = assy.export_step(tmp_path / "motor_drive.step")
        assert path.exists()
        assert coupler.bore_1 > 5.0  # clearance applied

    def test_full_bolted_joint(self, tmp_path):
        """Bolt + washer + nut stacked correctly."""
        from cadforge.components.bracket import LBracket

        assy = Assembly(name="bolted_joint")
        bracket = LBracket(width=50, thickness=5)
        bolt = get_fastener("hex_bolt", "M6", length=25)
        washer = get_fastener("flat_washer", "M6")
        nut = get_fastener("hex_nut", "M6")

        assy.add_part(bracket, name="bracket", location=(0, 0, 0))
        assy.add_part(bolt, name="bolt", location=(25, 25, 5))
        assy.add_part(washer, name="washer", location=(25, 25, -20))
        assy.add_part(nut, name="nut", location=(25, 25, -22))

        path = assy.export_step(tmp_path / "bolted_joint.step")
        assert path.exists()
