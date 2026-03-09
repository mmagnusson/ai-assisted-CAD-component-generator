"""Tests for the fit system (Phase 4)."""

import json

import pytest

from cadforge.fitting import (
    FitSpec,
    FitResolver,
    compute_driven_value,
    default_allowance,
)
from cadforge.assembly import Assembly
from cadforge.components.shaft_coupler import ShaftCoupler
from cadforge.components.bearing_mount import FlangedBearingMount
from cadforge.components.bracket import LBracket
from cadforge.components.standoff import Standoff


# ------------------------------------------------------------------
# default_allowance
# ------------------------------------------------------------------


class TestDefaultAllowance:
    def test_exact_is_zero(self):
        assert default_allowance("exact", 10.0) == 0.0
        assert default_allowance("exact", 100.0) == 0.0

    def test_clearance_positive(self):
        for size in [5, 10, 25, 40, 60, 100, 150]:
            a = default_allowance("clearance", size)
            assert a > 0, f"Clearance should be positive for {size}mm"

    def test_interference_negative(self):
        for size in [5, 10, 25, 40, 60, 100, 150]:
            a = default_allowance("interference", size)
            assert a < 0, f"Interference should be negative for {size}mm"

    def test_transition_small_positive(self):
        for size in [5, 10, 25, 40]:
            a = default_allowance("transition", size)
            assert a > 0
            assert a < default_allowance("clearance", size)

    def test_scales_with_size(self):
        small = default_allowance("clearance", 5.0)
        large = default_allowance("clearance", 100.0)
        assert large > small

    def test_size_tiers(self):
        # Verify the tiered behavior
        a6 = default_allowance("clearance", 6.0)
        a18 = default_allowance("clearance", 18.0)
        a30 = default_allowance("clearance", 30.0)
        assert a6 < a18 < a30


# ------------------------------------------------------------------
# compute_driven_value
# ------------------------------------------------------------------


class TestComputeDrivenValue:
    def test_exact(self):
        assert compute_driven_value(10.0, "exact") == 10.0

    def test_clearance_larger(self):
        result = compute_driven_value(10.0, "clearance")
        assert result > 10.0

    def test_interference_smaller(self):
        result = compute_driven_value(10.0, "interference")
        assert result < 10.0

    def test_explicit_allowance_overrides(self):
        result = compute_driven_value(10.0, "clearance", allowance=0.5)
        assert result == 10.5

    def test_explicit_negative_allowance(self):
        result = compute_driven_value(10.0, "interference", allowance=-0.3)
        assert result == 9.7


# ------------------------------------------------------------------
# FitSpec
# ------------------------------------------------------------------


class TestFitSpec:
    def test_defaults(self):
        fs = FitSpec(
            source_part="a",
            source_param="diameter",
            target_part="b",
            target_param="bore",
        )
        assert fs.fit_type == "clearance"
        assert fs.allowance == 0.0

    def test_custom_allowance(self):
        fs = FitSpec(
            source_part="a",
            source_param="d",
            target_part="b",
            target_param="bore",
            fit_type="interference",
            allowance=-0.05,
        )
        assert fs.allowance == -0.05


# ------------------------------------------------------------------
# FitResolver
# ------------------------------------------------------------------


class TestFitResolver:
    def test_resolve_clearance(self):
        coupler = ShaftCoupler(bore_2=10.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        fits = [
            FitSpec(
                source_part="coupler",
                source_param="bore_2",
                target_part="mount",
                target_param="bore_diameter",
                fit_type="clearance",
            )
        ]
        parts = {"coupler": coupler, "mount": mount}
        adjustments = FitResolver.resolve(fits, parts)

        assert "mount" in adjustments
        assert "bore_diameter" in adjustments["mount"]
        assert adjustments["mount"]["bore_diameter"] > 10.0

    def test_resolve_exact(self):
        coupler = ShaftCoupler(bore_2=12.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        fits = [
            FitSpec(
                source_part="coupler",
                source_param="bore_2",
                target_part="mount",
                target_param="bore_diameter",
                fit_type="exact",
            )
        ]
        parts = {"coupler": coupler, "mount": mount}
        adjustments = FitResolver.resolve(fits, parts)

        assert adjustments["mount"]["bore_diameter"] == 12.0

    def test_resolve_explicit_allowance(self):
        coupler = ShaftCoupler(bore_2=8.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        fits = [
            FitSpec(
                source_part="coupler",
                source_param="bore_2",
                target_part="mount",
                target_param="bore_diameter",
                fit_type="clearance",
                allowance=0.1,
            )
        ]
        parts = {"coupler": coupler, "mount": mount}
        adjustments = FitResolver.resolve(fits, parts)

        assert adjustments["mount"]["bore_diameter"] == pytest.approx(8.1)

    def test_resolve_invalid_source_part(self):
        fits = [
            FitSpec("ghost", "d", "mount", "bore_diameter")
        ]
        parts = {"mount": FlangedBearingMount()}
        with pytest.raises(ValueError, match="source part.*not found"):
            FitResolver.resolve(fits, parts)

    def test_resolve_invalid_source_param(self):
        fits = [
            FitSpec("coupler", "nonexistent", "mount", "bore_diameter")
        ]
        parts = {
            "coupler": ShaftCoupler(),
            "mount": FlangedBearingMount(),
        }
        with pytest.raises(ValueError, match="Parameter.*not found"):
            FitResolver.resolve(fits, parts)

    def test_resolve_invalid_target_param(self):
        fits = [
            FitSpec("coupler", "bore_2", "mount", "nonexistent")
        ]
        parts = {
            "coupler": ShaftCoupler(),
            "mount": FlangedBearingMount(),
        }
        with pytest.raises(ValueError, match="Parameter.*not found"):
            FitResolver.resolve(fits, parts)

    def test_apply(self):
        mount = FlangedBearingMount(bore_diameter=25.0)
        parts = {"mount": mount}
        adjustments = {"mount": {"bore_diameter": 10.018}}

        FitResolver.apply(adjustments, parts)

        assert mount.bore_diameter == pytest.approx(10.018)
        assert mount._workplane is None  # cache invalidated

    def test_multiple_fits(self):
        coupler = ShaftCoupler(bore_1=8.0, bore_2=10.0)
        mount1 = FlangedBearingMount(bore_diameter=25.0)
        mount2 = FlangedBearingMount(bore_diameter=25.0)

        fits = [
            FitSpec("coupler", "bore_1", "mount1", "bore_diameter", "clearance"),
            FitSpec("coupler", "bore_2", "mount2", "bore_diameter", "exact"),
        ]
        parts = {"coupler": coupler, "mount1": mount1, "mount2": mount2}
        adjustments = FitResolver.resolve(fits, parts)

        assert adjustments["mount1"]["bore_diameter"] > 8.0
        assert adjustments["mount2"]["bore_diameter"] == 10.0


# ------------------------------------------------------------------
# Assembly.add_fit integration
# ------------------------------------------------------------------


class TestAssemblyFit:
    def test_add_fit(self):
        assy = Assembly()
        assy.add_part(ShaftCoupler(bore_2=10.0), name="coupler")
        assy.add_part(FlangedBearingMount(), name="mount")

        fit = assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="clearance",
        )
        assert len(assy.fits) == 1

    def test_add_fit_invalid_part(self):
        assy = Assembly()
        assy.add_part(ShaftCoupler(), name="coupler")
        with pytest.raises(ValueError, match="not found"):
            assy.add_fit("coupler", "bore_2", "ghost", "bore_diameter")

    def test_add_fit_invalid_param(self):
        assy = Assembly()
        assy.add_part(ShaftCoupler(), name="coupler")
        assy.add_part(FlangedBearingMount(), name="mount")
        with pytest.raises(ValueError, match="Parameter.*not found"):
            assy.add_fit("coupler", "nonexistent", "mount", "bore_diameter")

    def test_fit_applied_on_build(self):
        assy = Assembly()
        coupler = ShaftCoupler(bore_2=10.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        assy.add_part(coupler, name="coupler")
        assy.add_part(mount, name="mount")
        assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="exact",
        )

        assy.build()
        # mount's bore_diameter should now match coupler's bore_2
        assert mount.bore_diameter == 10.0

    def test_fit_clearance_on_build(self):
        assy = Assembly()
        coupler = ShaftCoupler(bore_2=10.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        assy.add_part(coupler, name="coupler")
        assy.add_part(mount, name="mount")
        assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="clearance",
        )

        assy.build()
        assert mount.bore_diameter > 10.0
        assert mount.bore_diameter < 10.1  # reasonable clearance

    def test_fit_with_explicit_allowance(self):
        assy = Assembly()
        coupler = ShaftCoupler(bore_2=8.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        assy.add_part(coupler, name="coupler")
        assy.add_part(mount, name="mount")
        assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="clearance",
            allowance=0.5,
        )

        assy.build()
        assert mount.bore_diameter == pytest.approx(8.5)

    def test_fit_interference(self):
        assy = Assembly()
        coupler = ShaftCoupler(bore_2=10.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        assy.add_part(coupler, name="coupler")
        assy.add_part(mount, name="mount")
        assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="interference",
        )

        assy.build()
        assert mount.bore_diameter < 10.0

    def test_fit_with_constraints(self, tmp_path):
        """Fits + constraints together: bore sizes propagate, parts positioned."""
        assy = Assembly(name="fitted_constrained")
        bracket = LBracket(width=80, height=40, thickness=5)
        coupler = ShaftCoupler(bore_2=12.0)
        mount = FlangedBearingMount(bore_diameter=25.0)

        assy.add_part(bracket, name="bracket", location=(0, 0, 0))
        assy.add_part(coupler, name="coupler")
        assy.add_part(mount, name="mount")

        # Bore propagation
        assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="clearance",
        )

        # Position mount on bracket
        assy.add_constraint(
            "bracket", "horizontal_face",
            "mount", "bottom",
        )

        path = assy.export_step(tmp_path / "fitted.step")
        assert path.exists()
        assert mount.bore_diameter > 12.0  # clearance applied

    def test_fit_invalidates_cache(self):
        assy = Assembly()
        assy.add_part(ShaftCoupler(), name="coupler")
        assy.add_part(FlangedBearingMount(), name="mount")
        r1 = assy.build()
        assy.add_fit("coupler", "bore_2", "mount", "bore_diameter")
        r2 = assy.build()
        assert r1 is not r2

    def test_chained_fits(self):
        """Parameter propagates through a chain: A → B → C."""
        assy = Assembly()
        coupler1 = ShaftCoupler(bore_2=10.0)
        coupler2 = ShaftCoupler(bore_1=25.0, bore_2=25.0)
        mount = FlangedBearingMount(bore_diameter=50.0)

        assy.add_part(coupler1, name="c1")
        assy.add_part(coupler2, name="c2")
        assy.add_part(mount, name="mount")

        # c1.bore_2 drives c2.bore_1
        assy.add_fit("c1", "bore_2", "c2", "bore_1", fit_type="exact")
        # c2.bore_2 drives mount.bore_diameter
        assy.add_fit("c2", "bore_2", "mount", "bore_diameter", fit_type="exact")

        assy.build()
        assert coupler2.bore_1 == 10.0
        # c2.bore_2 was 25.0 (not driven), so mount gets 25.0
        assert mount.bore_diameter == 25.0


# ------------------------------------------------------------------
# JSON round-trip with fits
# ------------------------------------------------------------------


class TestFitSpec_JSON:
    def test_to_spec_includes_fits(self):
        assy = Assembly(name="test")
        assy.add_part(ShaftCoupler(), name="coupler")
        assy.add_part(FlangedBearingMount(), name="mount")
        assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="clearance",
        )
        spec = assy.to_spec()
        assert "fits" in spec
        assert len(spec["fits"]) == 1
        f = spec["fits"][0]
        assert f["source_part"] == "coupler"
        assert f["source_param"] == "bore_2"
        assert f["fit_type"] == "clearance"

    def test_to_spec_no_fits(self):
        assy = Assembly()
        assy.add_part(LBracket(), name="b")
        spec = assy.to_spec()
        assert "fits" not in spec

    def test_from_spec_with_fits(self):
        spec = {
            "name": "fitted",
            "parts": [
                {"type": "shaft_coupler", "name": "coupler", "params": {"bore_2": 10}},
                {"type": "flanged_bearing_mount", "name": "mount", "params": {}},
            ],
            "fits": [
                {
                    "source_part": "coupler",
                    "source_param": "bore_2",
                    "target_part": "mount",
                    "target_param": "bore_diameter",
                    "fit_type": "exact",
                },
            ],
        }
        assy = Assembly.from_spec(spec)
        assert len(assy.fits) == 1
        assy.build()
        mount = assy._get_part("mount").component
        assert mount.bore_diameter == 10.0

    def test_round_trip_with_fits(self):
        assy = Assembly(name="rt")
        assy.add_part(ShaftCoupler(bore_2=8.0), name="coupler")
        assy.add_part(FlangedBearingMount(), name="mount")
        assy.add_fit(
            "coupler", "bore_2",
            "mount", "bore_diameter",
            fit_type="clearance",
            allowance=0.2,
        )

        spec = assy.to_spec()
        json_str = json.dumps(spec)
        spec2 = json.loads(json_str)
        assy2 = Assembly.from_spec(spec2)

        assert len(assy2.fits) == 1
        assert assy2.fits[0].fit_type == "clearance"
        assert assy2.fits[0].allowance == 0.2

        assy2.build()
        mount2 = assy2._get_part("mount").component
        assert mount2.bore_diameter == pytest.approx(8.2)
