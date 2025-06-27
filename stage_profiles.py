"""
Stage profiles for the Tour de France 2025.
Each stage is categorized by its type, which affects how rider parameters influence their probability distributions.
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
STAGE_PROFILES = {
    1: StageType.SPRINT,
    2: StageType.PUNCH,
    3: StageType.SPRINT,
    4: StageType.PUNCH,
    5: StageType.ITT,
    6: StageType.PUNCH,
    7: StageType.PUNCH,
    8: StageType.SPRINT,
    9: StageType.SPRINT,
    10: StageType.MOUNTAIN,
    11: StageType.BREAK_AWAY,
    12: StageType.MOUNTAIN,
    13: StageType.MOUNTAIN,  # Mountain ITT
    14: StageType.MOUNTAIN,
    15: StageType.BREAK_AWAY,
    16: StageType.MOUNTAIN,
    17: StageType.SPRINT,
    18: StageType.MOUNTAIN,
    19: StageType.MOUNTAIN,
    20: StageType.BREAK_AWAY,
    21: StageType.SPRINT
}

def get_stage_type(stage_number: int) -> StageType:
    """Get the type of a specific stage."""
    return STAGE_PROFILES[stage_number]

def get_stages_of_type(stage_type: StageType) -> List[int]:
    """Get all stage numbers of a specific type."""
    return [stage for stage, type_ in STAGE_PROFILES.items() if type_ == stage_type] 