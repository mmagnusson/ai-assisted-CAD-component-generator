"""Component registry for CAD Forge.

All component classes are imported here and exposed via the ``REGISTRY``
dict that maps short string names to their classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core import Component

REGISTRY: dict[str, type[Component]] = {}

# -- Brackets & Mounts ---------------------------------------------------
try:
    from .bracket import LBracket
    REGISTRY["l_bracket"] = LBracket
except ImportError:
    pass

try:
    from .bearing_mount import FlangedBearingMount
    REGISTRY["flanged_bearing_mount"] = FlangedBearingMount
except ImportError:
    pass

# -- Enclosures & Structural ----------------------------------------------
try:
    from .enclosure import Enclosure
    REGISTRY["enclosure"] = Enclosure
except ImportError:
    pass

try:
    from .standoff import Standoff
    REGISTRY["standoff"] = Standoff
except ImportError:
    pass

try:
    from .shaft_coupler import ShaftCoupler
    REGISTRY["shaft_coupler"] = ShaftCoupler
except ImportError:
    pass

# -- Workholding -----------------------------------------------------------
try:
    from .soft_jaw import SoftJaw
    REGISTRY["soft_jaw"] = SoftJaw
except ImportError:
    pass

try:
    from .fixture_plate import FixturePlate
    REGISTRY["fixture_plate"] = FixturePlate
except ImportError:
    pass

try:
    from .toggle_clamp import ToggleClamp
    REGISTRY["toggle_clamp"] = ToggleClamp
except ImportError:
    pass

try:
    from .workholding_clamp import WorkholdingClamp
    REGISTRY["workholding_clamp"] = WorkholdingClamp
except ImportError:
    pass

try:
    from .collet import Collet
    REGISTRY["collet"] = Collet
except ImportError:
    pass

try:
    from .go_nogo_gauge import GoNoGoGauge
    REGISTRY["go_nogo_gauge"] = GoNoGoGauge
except ImportError:
    pass

# -- Electrical & Connectors ------------------------------------------------
try:
    from .dsub_connector import DSubConnector
    REGISTRY["dsub_connector"] = DSubConnector
except ImportError:
    pass

try:
    from .circular_connector import CircularConnector
    REGISTRY["circular_connector"] = CircularConnector
except ImportError:
    pass

try:
    from .pcb_card_guide import PCBCardGuide
    REGISTRY["pcb_card_guide"] = PCBCardGuide
except ImportError:
    pass

try:
    from .wire_lug import WireLug
    REGISTRY["wire_lug"] = WireLug
except ImportError:
    pass

try:
    from .strain_relief import StrainRelief
    REGISTRY["strain_relief"] = StrainRelief
except ImportError:
    pass

# -- Springs & Washers -----------------------------------------------------
try:
    from .wave_spring import WaveSpring
    REGISTRY["wave_spring"] = WaveSpring
except ImportError:
    pass

try:
    from .belleville_washer import BellevilleWasher
    REGISTRY["belleville_washer"] = BellevilleWasher
except ImportError:
    pass

# -- Mechanisms ------------------------------------------------------------
try:
    from .geneva_mechanism import GenevaMechanism
    REGISTRY["geneva_mechanism"] = GenevaMechanism
except ImportError:
    pass

try:
    from .four_bar_linkage import FourBarLinkage
    REGISTRY["four_bar_linkage"] = FourBarLinkage
except ImportError:
    pass

# -- Structural & Piping ----------------------------------------------------
try:
    from .welded_frame import WeldedFrame
    REGISTRY["welded_frame"] = WeldedFrame
except ImportError:
    pass

try:
    from .pipe_spool import PipeSpool
    REGISTRY["pipe_spool"] = PipeSpool
except ImportError:
    pass

try:
    from .pressure_vessel import PressureVessel
    REGISTRY["pressure_vessel"] = PressureVessel
except ImportError:
    pass

try:
    from .truss_structure import TrussStructure
    REGISTRY["truss_structure"] = TrussStructure
except ImportError:
    pass

# -- Springs (additional) ----------------------------------------------------
try:
    from .constant_force_spring import ConstantForceSpring
    REGISTRY["constant_force_spring"] = ConstantForceSpring
except ImportError:
    pass

try:
    from .torsion_bar import TorsionBar
    REGISTRY["torsion_bar"] = TorsionBar
except ImportError:
    pass

# -- Actuators & Struts ------------------------------------------------------
try:
    from .gas_spring import GasSpring
    REGISTRY["gas_spring"] = GasSpring
except ImportError:
    pass

# -- Mechanisms (additional) -------------------------------------------------
try:
    from .scotch_yoke import ScotchYoke
    REGISTRY["scotch_yoke"] = ScotchYoke
except ImportError:
    pass

try:
    from .crank_slider import CrankSlider
    REGISTRY["crank_slider"] = CrankSlider
except ImportError:
    pass

try:
    from .rack_and_pinion import RackAndPinion
    REGISTRY["rack_and_pinion"] = RackAndPinion
except ImportError:
    pass

# -- Detents & Plungers ------------------------------------------------------
try:
    from .ball_detent import BallDetent
    REGISTRY["ball_detent"] = BallDetent
except ImportError:
    pass
