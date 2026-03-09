"""Compound components for CAD Forge.

A CompoundComponent is a reusable sub-assembly template built from
base Components.  Unlike an Assembly (which is a top-level container),
a CompoundComponent acts like a single unit that can be added to an
Assembly and exposes its own mate points for further connections.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cadquery as cq

from ..assembly import Assembly, MateConstraint, _make_location
from ..core import Component, MatePoint


@dataclass
class CompoundComponent:
    """Base class for reusable sub-assembly templates.

    Subclasses define:
    - ``components()`` — the parts that make up this compound
    - ``internal_constraints()`` — how those parts connect to each other
    - ``mates()`` — connection points exposed to the outside world

    The compound builds an internal Assembly, solves its constraints,
    and can be added to a parent Assembly as a positioned sub-assembly.
    """

    name: str = "compound"

    # Internal cache
    _assembly: Assembly | None = field(
        default=None, init=False, repr=False
    )

    def components(self) -> list[tuple[Component, str]]:
        """Return ``(component, name)`` pairs for this compound.

        Subclasses **must** override this method.
        """
        raise NotImplementedError(
            f"{type(self).__name__} must implement components()"
        )

    def internal_constraints(self) -> list[MateConstraint]:
        """Return constraints between internal components.

        Subclasses should override this to define how their
        internal parts connect.  Default returns an empty list.
        """
        return []

    def mates(self) -> list[MatePoint]:
        """Return mate points exposed for external connections.

        Subclasses should override this to expose connection
        geometry for use in parent assemblies.
        """
        return []

    def get_assembly(self) -> Assembly:
        """Build and return the internal Assembly (cached)."""
        if self._assembly is not None:
            return self._assembly

        assy = Assembly(name=self.name)

        for comp, comp_name in self.components():
            assy.add_part(comp, name=comp_name)

        for mc in self.internal_constraints():
            assy.add_constraint(
                part1_name=mc.part1_name,
                mate1_name=mc.mate1_name,
                part2_name=mc.part2_name,
                mate2_name=mc.mate2_name,
                constraint_type=mc.constraint_type,
                offset=mc.offset,
            )

        self._assembly = assy
        return assy

    def build(self) -> cq.Assembly:
        """Build and return the CadQuery Assembly."""
        return self.get_assembly().build()

    def bounding_box(self) -> tuple[float, float, float]:
        """Return bounding box of the solved compound."""
        return self.get_assembly().bounding_box()

    def parts_list(self) -> list[dict[str, Any]]:
        """Return BOM for internal components."""
        return self.get_assembly().parts_list()

    def metadata(self) -> dict[str, Any]:
        """Return metadata including compound name and internals."""
        inner = self.get_assembly().metadata()
        return {
            "compound": type(self).__name__,
            "name": self.name,
            "mates": [
                {"name": m.name, "origin": list(m.origin),
                 "normal": list(m.normal), "type": m.mate_type}
                for m in self.mates()
            ],
            "assembly": inner,
        }


# Compound registry — maps string names to compound classes
COMPOUND_REGISTRY: dict[str, type[CompoundComponent]] = {}

# -- Import compound components ------------------------------------------------
try:
    from .motorized_joint import MotorizedJoint
    COMPOUND_REGISTRY["motorized_joint"] = MotorizedJoint
except ImportError:
    pass

try:
    from .pillow_block import PillowBlock
    COMPOUND_REGISTRY["pillow_block"] = PillowBlock
except ImportError:
    pass
