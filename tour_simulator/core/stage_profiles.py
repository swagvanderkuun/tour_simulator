"""
Stage profiles for the Tour de France 2025.
Each stage can be a mix of different types with weights that sum to 1.
This affects how rider parameters influence their probability distributions.
"""

from enum import Enum
from typing import Dict, List

class StageType(Enum):
    SPRINT = "sprint"
    PUNCH = "punch"
    ITT = "itt"
    MOUNTAIN = "mountain"
    BREAK_AWAY = "break_away"

# Stage profiles for the Tour de France 2025
# Each stage can be a mix of different types with weights that sum to 1
STAGE_PROFILES = {
    1: {StageType.SPRINT: 1.0},
    2: {StageType.PUNCH: 0.8, StageType.SPRINT: 0.2},
    3: {StageType.SPRINT: 1.0},
    4: {StageType.PUNCH: 0.7, StageType.SPRINT: 0.3},
    5: {StageType.ITT: 1.0},
    6: {StageType.PUNCH: 0.6, StageType.BREAK_AWAY: 0.3, StageType.MOUNTAIN: 0.1},
    7: {StageType.PUNCH: 0.7, StageType.MOUNTAIN: 0.3},
    8: {StageType.SPRINT: 0.9, StageType.PUNCH: 0.1},
    9: {StageType.SPRINT: 1.0},
    10: {StageType.MOUNTAIN: 0.5, StageType.BREAK_AWAY: 0.5},
    11: {StageType.BREAK_AWAY: 0.2, StageType.SPRINT: 0.2, StageType.PUNCH: 0.6},
    12: {StageType.MOUNTAIN: 1.0},
    13: {StageType.ITT: 0.2, StageType.MOUNTAIN: 0.8},
    14: {StageType.MOUNTAIN: 0.8, StageType.BREAK_AWAY: 0.2},
    15: {StageType.BREAK_AWAY: 0.8, StageType.SPRINT: 0.2},
    16: {StageType.MOUNTAIN: 1.0},
    17: {StageType.BREAK_AWAY: 0.4, StageType.SPRINT: 0.6},
    18: {StageType.MOUNTAIN: 1.0},
    19: {StageType.MOUNTAIN: 1.0},
    20: {StageType.BREAK_AWAY: 0.8, StageType.SPRINT: 0.2},
    21: {StageType.SPRINT: 0.6, StageType.PUNCH: 0.4}
}

def get_stage_profile(stage_number: int) -> Dict[StageType, float]:
    """Get the weighted profile of a specific stage."""
    return STAGE_PROFILES[stage_number]

def get_stage_type(stage_number: int) -> StageType:
    """Get the primary type of a specific stage (for backward compatibility)."""
    profile = STAGE_PROFILES[stage_number]
    # Return the stage type with the highest weight
    return max(profile.items(), key=lambda x: x[1])[0]

def get_stages_of_type(stage_type: StageType) -> List[int]:
    """Get all stage numbers where a specific type has the highest weight."""
    return [stage for stage, profile in STAGE_PROFILES.items() 
            if max(profile.items(), key=lambda x: x[1])[0] == stage_type]

def validate_stage_profile(profile: Dict[StageType, float]) -> bool:
    """Validate that stage profile weights sum to 1.0."""
    total_weight = sum(profile.values())
    return abs(total_weight - 1.0) < 0.001  # Allow small floating point errors

def update_stage_profile(stage_number: int, profile: Dict[StageType, float]):
    """Update a stage profile with validation."""
    if not validate_stage_profile(profile):
        raise ValueError(f"Stage profile weights must sum to 1.0, got {sum(profile.values())}")
    STAGE_PROFILES[stage_number] = profile 