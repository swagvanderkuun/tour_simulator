"""
Rider parameters for different stage types.
Each rider has parameters that influence their performance in different types of stages.
Parameters are on a scale of 0-100, where:
- 98-100: Exceptional
- 95-97: World Class
- 90-94: Elite
- 80-89: Very Good
- 70-79: Good
- 50-69: Average
- <50: Below Average
"""

from dataclasses import dataclass
from typing import Dict, Tuple
from stage_profiles import StageType

# Global tier parameters that can be modified by the dashboard
TIER_PARAMETERS = {
    "exceptional": {"min": 1, "mode": 1, "max": 10},      # 98+
    "world_class": {"min": 1, "mode": 3, "max": 20},      # 95-97
    "elite": {"min": 1, "mode": 6, "max": 30},            # 90-94
    "very_good": {"min": 1, "mode": 15, "max": 40},       # 80-89
    "good": {"min": 5, "mode": 20, "max": 50},            # 70-79
    "average": {"min": 20, "mode": 30, "max": 60},        # 50-69
    "below_average": {"min": 50, "mode": 75, "max": 150}  # <50
}

def update_tier_parameters(new_parameters: Dict):
    """Update the global tier parameters"""
    global TIER_PARAMETERS
    TIER_PARAMETERS.update(new_parameters)

def get_tier_parameters() -> Dict:
    """Get the current tier parameters"""
    return TIER_PARAMETERS.copy()

@dataclass
class RiderParameters:
    sprint_ability: int  # Ability in sprint finishes
    punch_ability: int   # Ability in punchy stages
    itt_ability: int     # Time trial ability
    mountain_ability: int  # Climbing ability in high mountains
    break_away_ability: int     # Ability in break away terrain

    def get_probability_range(self, stage_type: str) -> Tuple[float, float, float]:
        """
        Convert rider parameters into probability ranges for stage results.
        Returns (min, mode, max) for triangular distribution.
        Lower numbers = better result (1 = winner)
        """
        # Base conversion of ability to probabilities using configurable parameters
        def ability_to_prob(ability: int) -> Tuple[float, float, float]:
            if ability >= 98:  # Exceptional
                params = TIER_PARAMETERS["exceptional"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 95:  # World Class
                params = TIER_PARAMETERS["world_class"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 90:  # Elite
                params = TIER_PARAMETERS["elite"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 80:  # Very Good
                params = TIER_PARAMETERS["very_good"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 70:  # Good
                params = TIER_PARAMETERS["good"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 50:  # Average
                params = TIER_PARAMETERS["average"]
                return (params["min"], params["mode"], params["max"])
            else:  # Below Average
                params = TIER_PARAMETERS["below_average"]
                return (params["min"], params["mode"], params["max"])

        # Get relevant ability for stage type
        ability = {
            "sprint": self.sprint_ability,
            "punch": self.punch_ability,
            "itt": self.itt_ability,
            "mountain": self.mountain_ability,
            "break_away": self.break_away_ability
        }[stage_type]

        # Get base probabilities
        min_val, mode_val, max_val = ability_to_prob(ability)

        return (min_val, mode_val, max_val)

    def get_weighted_probability_range(self, stage_profile: Dict[StageType, float]) -> Tuple[float, float, float]:
        """
        Convert rider parameters into weighted probability ranges for mixed stage types.
        Returns (min, mode, max) for triangular distribution.
        Lower numbers = better result (1 = winner)
        
        Args:
            stage_profile: Dictionary mapping StageType to weight (must sum to 1.0)
        """
        # Base conversion of ability to probabilities using configurable parameters
        def ability_to_prob(ability: int) -> Tuple[float, float, float]:
            if ability >= 98:  # Exceptional
                params = TIER_PARAMETERS["exceptional"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 95:  # World Class
                params = TIER_PARAMETERS["world_class"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 90:  # Elite
                params = TIER_PARAMETERS["elite"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 80:  # Very Good
                params = TIER_PARAMETERS["very_good"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 70:  # Good
                params = TIER_PARAMETERS["good"]
                return (params["min"], params["mode"], params["max"])
            elif ability >= 50:  # Average
                params = TIER_PARAMETERS["average"]
                return (params["min"], params["mode"], params["max"])
            else:  # Below Average
                params = TIER_PARAMETERS["below_average"]
                return (params["min"], params["mode"], params["max"])

        # Map stage types to abilities
        ability_map = {
            StageType.SPRINT: self.sprint_ability,
            StageType.PUNCH: self.punch_ability,
            StageType.ITT: self.itt_ability,
            StageType.MOUNTAIN: self.mountain_ability,
            StageType.BREAK_AWAY: self.break_away_ability
        }

        # Calculate weighted average of probability parameters
        weighted_min = 0.0
        weighted_mode = 0.0
        weighted_max = 0.0

        for stage_type, weight in stage_profile.items():
            ability = ability_map[stage_type]
            min_val, mode_val, max_val = ability_to_prob(ability)
            
            weighted_min += min_val * weight
            weighted_mode += mode_val * weight
            weighted_max += max_val * weight

        return (weighted_min, weighted_mode, weighted_max)
