"""SVG rendering for CAD Forge components.

Uses CadQuery's built-in SVG exporter to produce a 2D projection of
a 3D workplane.
"""

from __future__ import annotations

from pathlib import Path

import cadquery as cq
from cadquery import exporters


def render_svg(
    workplane: cq.Workplane,
    filepath: str | Path,
    width: int = 800,
    height: int = 600,
) -> Path:
    """Export a 2D SVG projection of *workplane* to *filepath*.

    Parameters
    ----------
    workplane:
        The CadQuery ``Workplane`` to render.
    filepath:
        Destination path for the SVG file.
    width:
        SVG viewport width in pixels.
    height:
        SVG viewport height in pixels.

    Returns
    -------
    Path
        The resolved output path.
    """
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    svg_opts: dict = {
        "width": width,
        "height": height,
        "showAxes": False,
        "showHidden": False,
        "marginLeft": 10,
        "marginTop": 10,
    }

    exporters.export(
        workplane,
        str(filepath),
        exporters.ExportTypes.SVG,
        opt=svg_opts,
    )

    return filepath
