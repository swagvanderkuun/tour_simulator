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

@dataclass
class RiderParameters:
    sprint_ability: int  # Ability in sprint finishes
    punch_ability: int   # Ability in punchy stages
    itt_ability: int     # Time trial ability
    mountain_ability: int  # Climbing ability in high mountains
    hills_ability: int     # Ability in hilly terrain

    def get_probability_range(self, stage_type: str) -> Tuple[float, float, float]:
        """
        Convert rider parameters into probability ranges for stage results.
        Returns (min, mode, max) for triangular distribution.
        Lower numbers = better result (1 = winner)

        Probability ranges by ability tier:
        >=98: (1, 1, 3)    - Dominant, very likely to win
        95-97: (1, 2, 5)   - Can win any day
        90-94: (1, 3, 8)   - Regular podium contender
        80-89: (2, 5, 12)  - Can make top 5
        70-79: (5, 10, 20) - Regular top 10
        50-69: (10, 20, 40) - Mid-pack finisher
        <50: (30, 50, 80)  - Back of the pack
        """
        # Base conversion of ability to probabilities
        def ability_to_prob(ability: int) -> Tuple[float, float, float]:
            if ability >= 98:  # Exceptional
                return (1, 1, 20)
            elif ability >= 95:  # World Class
                return (1, 3, 30)
            elif ability >= 90:  # Elite
                return (1, 6, 30)
            elif ability >= 80:  # Very Good
                return (1, 10, 40)
            elif ability >= 70:  # Good
                return (1, 15, 50)
            elif ability >= 50:  # Average
                return (10, 20, 60)
            else:  # Below Average
                return (30, 50, 80)

        # Get relevant ability for stage type
        ability = {
            "sprint": self.sprint_ability,
            "punch": self.punch_ability,
            "itt": self.itt_ability,
            "mountain": self.mountain_ability,
            "hills": self.hills_ability
        }[stage_type]

        # Get base probabilities
        min_val, mode_val, max_val = ability_to_prob(ability)

        return (min_val, mode_val, max_val)

# Define rider parameters
RIDER_PARAMETERS = {
    # GC Contenders
    "Jonas Vingegaard": RiderParameters(
        sprint_ability=45,     # Below Average
        punch_ability=85,      # Very Good
        itt_ability=88,        # Very Good
        mountain_ability=99,   # Exceptional
        hills_ability=92       # Elite
    ),
    "Tadej Pogačar": RiderParameters(
        sprint_ability=75,     # Good
        punch_ability=98,      # Exceptional
        itt_ability=92,        # Elite
        mountain_ability=96,   # World Class
        hills_ability=95       # World Class
    ),
    
    # Sprinters
    "Jasper Philipsen": RiderParameters(
        sprint_ability=99,     # Exceptional
        punch_ability=65,      # Average
        itt_ability=45,        # Below Average
        mountain_ability=35,   # Below Average
        hills_ability=55       # Average
    ),
    
    # Puncheurs
    "Mathieu van der Poel": RiderParameters(
        sprint_ability=88,     # Very Good
        punch_ability=99,      # Exceptional
        itt_ability=82,        # Very Good
        mountain_ability=65,   # Average
        hills_ability=90       # Elite
    ),
    
    # All-rounders
    "Wout van Aert": RiderParameters(
        sprint_ability=92,     # Elite
        punch_ability=95,      # World Class
        itt_ability=90,        # Elite
        mountain_ability=75,   # Good
        hills_ability=88       # Very Good
    ),

    # Continue with all riders...
}

def get_rider_parameters(rider_name: str) -> RiderParameters:
    """Get the parameters for a specific rider."""
    # Return default parameters if rider not found
    default = RiderParameters(
        sprint_ability=50,
        punch_ability=50,
        itt_ability=50,
        mountain_ability=50,
        hills_ability=50
    )
    return RIDER_PARAMETERS.get(rider_name, default) 