"""CAD Forge - AI-Assisted CAD Component Generation"""

__version__ = "0.1.0"

from .core import Component, MatePoint
from .assembly import Assembly, AssemblyPart, MateConstraint
from .compounds import CompoundComponent, COMPOUND_REGISTRY
from .fitting import FitSpec, FitResolver
from .catalog import get_fastener, get_bearing, get_motor
from .planner import ASSEMBLY_SCHEMA, get_available_parts, validate_spec
