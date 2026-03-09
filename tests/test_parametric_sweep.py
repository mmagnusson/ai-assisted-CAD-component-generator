"""Parametric sweep stress tests for all CAD Forge components.

For each of the 12 registered components, three parameter sets are tested:
small, default (empty dict), and large.  Every combination must produce a
valid solid with positive bounding-box dimensions.
"""

import cadquery as cq
import pytest

from cadforge.components import REGISTRY


# ---------------------------------------------------------------------------
# Parameter sweeps: small / default / large for every component
# ---------------------------------------------------------------------------

SWEEPS = {
    "l_bracket": [
        {"width": 20, "height": 15, "thickness": 2},
        {},  # defaults
        {"width": 100, "height": 80, "thickness": 10},
    ],
    "flanged_bearing_mount": [
        {"bore_diameter": 10, "flange_diameter": 40, "flange_thickness": 5, "hub_height": 10, "hub_diameter": 20},
        {},
        {"bore_diameter": 50, "flange_diameter": 160, "flange_thickness": 20, "hub_height": 40, "hub_diameter": 80},
    ],
    "enclosure": [
        {"length": 40, "width": 30, "height": 20},
        {},
        {"length": 200, "width": 120, "height": 80},
    ],
    "standoff": [
        {"height": 5, "thread_diameter": 2, "base_diameter": 4, "hex_across_flats": 3.5},
        {},
        {"height": 25, "thread_diameter": 5, "base_diameter": 10, "hex_across_flats": 9},
    ],
    "shaft_coupler": [
        {"bore_1": 4, "bore_2": 4, "outer_diameter": 16, "length": 20},
        {},
        {"bore_1": 20, "bore_2": 25, "outer_diameter": 60, "length": 80},
    ],
    "soft_jaw": [
        {"jaw_width": 60, "jaw_height": 15, "jaw_depth": 20, "step_depth": 5, "step_height": 6},
        {},
        {"jaw_width": 300, "jaw_height": 50, "jaw_depth": 80, "step_depth": 20, "step_height": 25},
    ],
    "fixture_plate": [
        {"length": 80, "width": 60, "thickness": 10, "hole_grid_spacing": 20, "border_margin": 10},
        {},
        {"length": 400, "width": 300, "thickness": 40, "hole_grid_spacing": 50, "border_margin": 30},
    ],
    "toggle_clamp": [
        {"base_length": 40, "base_width": 15, "base_thickness": 4, "arm_length": 30, "pivot_height": 12},
        {},
        {"base_length": 160, "base_width": 60, "base_thickness": 16, "arm_length": 120, "pivot_height": 50},
    ],
    "wave_spring": [
        {"outer_diameter": 15, "inner_diameter": 10, "free_height": 5, "num_waves": 2, "num_turns": 1},
        {},
        {"outer_diameter": 60, "inner_diameter": 40, "free_height": 20, "num_waves": 5, "num_turns": 3},
    ],
    "belleville_washer": [
        {"outer_diameter": 10, "inner_diameter": 5, "thickness": 0.5, "cone_height": 0.3, "material_thickness": 0.15},
        {},
        {"outer_diameter": 50, "inner_diameter": 25, "thickness": 3, "cone_height": 1.5, "material_thickness": 0.8},
    ],
    "geneva_mechanism": [
        {"wheel_diameter": 40, "slot_count": 3, "driver_pin_radius": 15, "wheel_thickness": 4},
        {},
        {"wheel_diameter": 160, "slot_count": 6, "driver_pin_radius": 60, "wheel_thickness": 16},
    ],
    "four_bar_linkage": [
        {"ground_link": 50, "input_link": 15, "coupler_link": 35, "output_link": 30, "link_width": 5, "link_thickness": 3},
        {},
        {"ground_link": 200, "input_link": 60, "coupler_link": 140, "output_link": 120, "link_width": 20, "link_thickness": 10},
    ],
    # -- Tooling & Fixtures (additional) --
    "workholding_clamp": [
        {"clamp_length": 50, "clamp_width": 15, "clamp_thickness": 6},
        {},
        {"clamp_length": 200, "clamp_width": 40, "clamp_thickness": 20},
    ],
    "collet": [
        {"er_size": 11, "bore_diameter": 4},
        {},
        {"er_size": 50, "bore_diameter": 25},
    ],
    "go_nogo_gauge": [
        {"go_diameter": 5, "nogo_diameter": 5.02, "go_length": 10, "nogo_length": 6},
        {},
        {"go_diameter": 25, "nogo_diameter": 25.1, "go_length": 40, "nogo_length": 20},
    ],
    # -- Electrical & Connectors --
    "dsub_connector": [
        {"pin_count": 9},
        {},
        {"pin_count": 37, "shell_depth": 16},
    ],
    "circular_connector": [
        {"shell_diameter": 15, "shell_length": 20, "flange_diameter": 22, "bore_diameter": 10},
        {},
        {"shell_diameter": 40, "shell_length": 50, "flange_diameter": 55, "bore_diameter": 30},
    ],
    "pcb_card_guide": [
        {"rail_length": 50, "rail_height": 6, "rail_width": 5},
        {},
        {"rail_length": 200, "rail_height": 15, "rail_width": 12},
    ],
    "wire_lug": [
        {"wire_gauge_mm": 2.5, "hole_diameter": 4, "tongue_width": 8, "tongue_length": 10},
        {},
        {"wire_gauge_mm": 16, "hole_diameter": 14, "tongue_width": 30, "tongue_length": 40},
    ],
    "strain_relief": [
        {"cable_diameter": 4, "body_od": 10, "body_length": 10},
        {},
        {"cable_diameter": 16, "body_od": 28, "body_length": 25},
    ],
    # -- Structural & Piping --
    "welded_frame": [
        {"frame_length": 200, "frame_width": 150, "frame_height": 100, "tube_width": 25, "tube_height": 25},
        {},
        {"frame_length": 1000, "frame_width": 600, "frame_height": 400, "tube_width": 80, "tube_height": 80},
    ],
    "pipe_spool": [
        {"pipe_od": 33.4, "pipe_wall": 2.8, "straight_length": 100},
        {},
        {"pipe_od": 114.3, "pipe_wall": 6.0, "straight_length": 400},
    ],
    "pressure_vessel": [
        {"inner_diameter": 200, "shell_length": 400, "shell_thickness": 6},
        {},
        {"inner_diameter": 1000, "shell_length": 1500, "shell_thickness": 20},
    ],
    "truss_structure": [
        {"span": 500, "height": 100, "num_panels": 4},
        {},
        {"span": 2000, "height": 400, "num_panels": 8},
    ],
    # -- Springs (additional) --
    "constant_force_spring": [
        {"strip_width": 8, "natural_radius": 8, "num_coils": 3, "extended_length": 25},
        {},
        {"strip_width": 25, "natural_radius": 25, "num_coils": 8, "extended_length": 100},
    ],
    "torsion_bar": [
        {"diameter": 10, "active_length": 150},
        {},
        {"diameter": 35, "active_length": 600},
    ],
    "gas_spring": [
        {"bore_diameter": 12, "rod_diameter": 6, "stroke": 50},
        {},
        {"bore_diameter": 30, "rod_diameter": 12, "stroke": 200},
    ],
    # -- Mechanisms (additional) --
    "scotch_yoke": [
        {"crank_radius": 15, "slider_width": 12, "slider_height": 20},
        {},
        {"crank_radius": 60, "slider_width": 35, "slider_height": 70},
    ],
    "crank_slider": [
        {"crank_radius": 12, "connecting_rod_length": 40, "piston_bore": 20},
        {},
        {"crank_radius": 50, "connecting_rod_length": 160, "piston_bore": 80},
    ],
    "rack_and_pinion": [
        {"module": 1.0, "pinion_teeth": 8, "rack_length": 50},
        {},
        {"module": 3.0, "pinion_teeth": 20, "rack_length": 200},
    ],
    "ball_detent": [
        {"body_diameter": 5, "body_length": 10, "ball_diameter": 2.5},
        {},
        {"body_diameter": 12, "body_length": 25, "ball_diameter": 6},
    ],
}


def _build_test_cases():
    """Generate (name, params, label) tuples for parametrize."""
    cases = []
    for name, param_sets in SWEEPS.items():
        labels = ["small", "default", "large"]
        for params, label in zip(param_sets, labels):
            cases.append(pytest.param(name, params, id=f"{name}-{label}"))
    return cases


@pytest.mark.parametrize("name,params", _build_test_cases())
class TestParametricSweep:
    """Stress-test components across small, default, and large parameter sets."""

    def test_build_succeeds(self, name, params):
        """Component builds without raising an exception."""
        cls = REGISTRY[name]
        instance = cls(**params)
        result = instance.build()
        assert isinstance(result, cq.Workplane)

    def test_solid_valid(self, name, params):
        """Built result has a non-None solid."""
        cls = REGISTRY[name]
        instance = cls(**params)
        result = instance.build()
        solid = result.val()
        assert solid is not None

    def test_bounding_box_positive(self, name, params):
        """Bounding box dimensions are all greater than zero."""
        cls = REGISTRY[name]
        instance = cls(**params)
        result = instance.build()
        bb = result.val().BoundingBox()
        assert bb.xlen > 0, f"X dimension is {bb.xlen}"
        assert bb.ylen > 0, f"Y dimension is {bb.ylen}"
        assert bb.zlen > 0, f"Z dimension is {bb.zlen}"


# ---------------------------------------------------------------------------
# Ensure sweep coverage matches registry
# ---------------------------------------------------------------------------

def test_sweep_covers_all_components():
    """Every registered component has a sweep definition."""
    missing = set(REGISTRY.keys()) - set(SWEEPS.keys())
    assert not missing, f"Missing sweep definitions for: {missing}"
