"""
Tour Simulator - Professional Tour de France Cycling Simulator

A comprehensive simulation engine for Tour de France cycling with team optimization,
versus mode, and detailed performance analytics.
"""

__version__ = "1.0.0"
__author__ = "Tour Simulator Team"

# Core classes
from tour_simulator.core.simulator import TourSimulator
from tour_simulator.core.riders import RiderDatabase, Rider
from tour_simulator.core.stage_profiles import StageType

# Models
from tour_simulator.models.rider_parameters import RiderParameters
from tour_simulator.models.stage_result import StageResult

# Services
from tour_simulator.services.team_optimization import TeamOptimizer, TeamSelection
from tour_simulator.services.versus_mode import VersusMode, UserTeam

__all__ = [
    "TourSimulator",
    "RiderDatabase", 
    "Rider",
    "StageType",
    "RiderParameters",
    "StageResult", 
    "TeamOptimizer",
    "TeamSelection",
    "VersusMode",
    "UserTeam"
] 