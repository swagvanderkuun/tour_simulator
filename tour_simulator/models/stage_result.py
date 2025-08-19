"""Stage result data model."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tour_simulator.core.riders import Rider


@dataclass
class StageResult:
    """Represents a rider's result in a single stage."""
    
    rider: 'Rider'
    position: float
    points: int = 0  # Legacy field, not currently used
    
    def __post_init__(self):
        """Validate stage result data."""
        if self.position < 0:
            raise ValueError("Position cannot be negative")
        if self.points < 0:
            raise ValueError("Points cannot be negative") 