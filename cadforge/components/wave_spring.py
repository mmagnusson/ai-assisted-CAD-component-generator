"""Wave spring component."""

import math
from dataclasses import dataclass

import cadquery as cq

from cadforge.core import Component


@dataclass
class WaveSpring(Component):
    """Wave spring approximated as stacked wavy annular rings.

    Each turn is built as a series of annular sectors with alternating
    Z offsets following a sinusoidal wave profile, then lofted to form
    a smooth wavy ring. Turns are stacked vertically.
    """

    name: str = "wave_spring"
    outer_diameter: float = 30.0
    inner_diameter: float = 20.0
    free_height: float = 10.0
    num_waves: int = 3
    num_turns: int = 2
    wire_thickness: float = 0.5
    wire_width: float = 3.0

    def build(self) -> cq.Workplane:
        outer_r = self.outer_diameter / 2.0
        inner_r = self.inner_diameter / 2.0
        mid_r = (outer_r + inner_r) / 2.0
        ring_width = outer_r - inner_r

        # Height per turn
        height_per_turn = self.free_height / self.num_turns
        # Wave amplitude (peak-to-peak is the height per turn)
        amplitude = height_per_turn / 2.0

        # Number of segments per ring for smooth approximation
        segments_per_wave = 12
        total_segments = self.num_waves * segments_per_wave

        result = None

        for turn in range(self.num_turns):
            base_z = turn * height_per_turn + height_per_turn / 2.0

            # Build the wavy ring as a series of small box segments
            # positioned along the circular path with sinusoidal Z offset
            for seg in range(total_segments):
                angle = (seg / total_segments) * 2.0 * math.pi
                next_angle = ((seg + 1) / total_segments) * 2.0 * math.pi
                mid_angle = (angle + next_angle) / 2.0

                # Sinusoidal Z offset based on wave count
                z_offset = amplitude * math.sin(self.num_waves * mid_angle)
                z_pos = base_z + z_offset

                # Position of this segment center
                cx = mid_r * math.cos(mid_angle)
                cy = mid_r * math.sin(mid_angle)

                # Segment arc length
                arc_len = mid_r * (next_angle - angle)
                # Ensure minimum segment length
                seg_len = max(arc_len * 1.2, 0.5)

                # Create a small box for this segment
                seg_solid = (
                    cq.Workplane("XY")
                    .box(seg_len, self.wire_width, self.wire_thickness)
                )

                # Rotate to align tangent to the circle
                rot_angle_deg = math.degrees(mid_angle)
                seg_solid = seg_solid.rotate(
                    (0, 0, 0), (0, 0, 1), rot_angle_deg + 90
                )

                # Translate to position
                seg_solid = seg_solid.translate((cx, cy, z_pos))

                if result is None:
                    result = seg_solid
                else:
                    result = result.union(seg_solid)

        return result
