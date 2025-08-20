"""
Race configuration system for flexible multi-stage race support.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import json
from pathlib import Path


class StageCategory(Enum):
    """Extended stage categories including Team Time Trial."""
    SPRINT = "sprint"
    PUNCH = "punch"
    ITT = "itt"
    TTT = "ttt"  # New: Team Time Trial
    MOUNTAIN = "mountain"
    BREAK_AWAY = "break_away"


@dataclass
class StageConfig:
    """Configuration for a single stage."""
    stage_number: int
    stage_name: str
    stage_type: Dict[StageCategory, float]  # Stage type weights
    distance: Optional[float] = None
    elevation_gain: Optional[float] = None
    start_city: Optional[str] = None
    finish_city: Optional[str] = None
    
    def __post_init__(self):
        """Validate stage configuration."""
        # Ensure weights sum to 1.0
        total_weight = sum(self.stage_type.values())
        if abs(total_weight - 1.0) > 0.001:
            raise ValueError(f"Stage type weights must sum to 1.0, got {total_weight}")


@dataclass
class RaceConfig:
    """Configuration for a complete stage race."""
    race_name: str
    race_short_name: str
    year: int
    total_stages: int
    stages: List[StageConfig] = field(default_factory=list)
    
    # Scoring configuration
    sprint_points: Dict[str, List[int]] = field(default_factory=dict)
    mountain_points: Dict[str, List[int]] = field(default_factory=dict)
    
    # Race-specific settings
    youth_age_limit: int = 25
    max_riders_per_team: int = 4
    
    # UI text configuration
    ui_texts: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default configurations."""
        if not self.ui_texts:
            self.ui_texts = {
                "app_title": f"{self.race_name} Simulator",
                "app_icon": "🚴‍♂️",
                "welcome_message": f"Welcome to the {self.race_name} {self.year} Simulator",
                "stage_label": "Stage",
                "gc_label": "General Classification",
                "sprint_label": "Sprint Classification",
                "mountain_label": "Mountain Classification",
                "youth_label": "Youth Classification"
            }
        
        if not self.sprint_points:
            self.sprint_points = {
                "category_1": [65, 55, 45, 30, 20, 18, 16, 10, 8, 7, 6, 5, 4, 3, 2],
                "category_2": [40, 30, 25, 22, 17, 15, 13, 11, 9, 7, 6, 5, 3, 2],
                "category_3": [20, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
                "category_4": [20, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
            }
        
        if not self.mountain_points:
            self.mountain_points = {
                "hc": [50, 30, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2],
                "category_1": [30, 25, 22, 19, 17, 15, 13, 11, 9, 7, 5, 3, 1],
                "category_2": [20, 15, 12, 10, 8, 6, 4, 2],
                "category_3": [10, 6, 4, 2, 1],
                "category_4": [5, 3, 2, 1]
            }
    
    def add_stage(self, stage: StageConfig) -> None:
        """Add a stage to the race configuration."""
        if stage.stage_number != len(self.stages) + 1:
            raise ValueError(f"Stage number {stage.stage_number} should be {len(self.stages) + 1}")
        self.stages.append(stage)
    
    def get_stage(self, stage_number: int) -> Optional[StageConfig]:
        """Get stage configuration by number."""
        for stage in self.stages:
            if stage.stage_number == stage_number:
                return stage
        return None
    
    def save_to_file(self, filepath: Path) -> None:
        """Save race configuration to JSON file."""
        # Convert to serializable format
        data = {
            "race_name": self.race_name,
            "race_short_name": self.race_short_name,
            "year": self.year,
            "total_stages": self.total_stages,
            "youth_age_limit": self.youth_age_limit,
            "max_riders_per_team": self.max_riders_per_team,
            "ui_texts": self.ui_texts,
            "sprint_points": self.sprint_points,
            "mountain_points": self.mountain_points,
            "stages": [
                {
                    "stage_number": stage.stage_number,
                    "stage_name": stage.stage_name,
                    "stage_type": {cat.value: weight for cat, weight in stage.stage_type.items()},
                    "distance": stage.distance,
                    "elevation_gain": stage.elevation_gain,
                    "start_city": stage.start_city,
                    "finish_city": stage.finish_city
                }
                for stage in self.stages
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> 'RaceConfig':
        """Load race configuration from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create race config
        race_config = cls(
            race_name=data["race_name"],
            race_short_name=data["race_short_name"],
            year=data["year"],
            total_stages=data["total_stages"],
            youth_age_limit=data.get("youth_age_limit", 25),
            max_riders_per_team=data.get("max_riders_per_team", 4),
            ui_texts=data.get("ui_texts", {}),
            sprint_points=data.get("sprint_points", {}),
            mountain_points=data.get("mountain_points", {})
        )
        
        # Add stages
        for stage_data in data["stages"]:
            stage_type = {
                StageCategory(cat): weight 
                for cat, weight in stage_data["stage_type"].items()
            }
            stage = StageConfig(
                stage_number=stage_data["stage_number"],
                stage_name=stage_data["stage_name"],
                stage_type=stage_type,
                distance=stage_data.get("distance"),
                elevation_gain=stage_data.get("elevation_gain"),
                start_city=stage_data.get("start_city"),
                finish_city=stage_data.get("finish_city")
            )
            race_config.stages.append(stage)
        
        return race_config


def create_tour_de_france_2025() -> RaceConfig:
    """Create default Tour de France 2025 configuration."""
    race = RaceConfig(
        race_name="Tour de France",
        race_short_name="TDF",
        year=2025,
        total_stages=21
    )
    
    # Define stage profiles (simplified for example)
    stage_profiles = [
        {"name": "Stage 1: Grand Départ", "type": {StageCategory.SPRINT: 1.0}},
        {"name": "Stage 2: Sprint Stage", "type": {StageCategory.SPRINT: 0.8, StageCategory.PUNCH: 0.2}},
        {"name": "Stage 3: Hilly Stage", "type": {StageCategory.PUNCH: 0.6, StageCategory.SPRINT: 0.4}},
        {"name": "Stage 4: Sprint Stage", "type": {StageCategory.SPRINT: 1.0}},
        {"name": "Stage 5: TTT", "type": {StageCategory.TTT: 1.0}},  # Team Time Trial
        {"name": "Stage 6: Mountain Stage", "type": {StageCategory.MOUNTAIN: 0.8, StageCategory.BREAK_AWAY: 0.2}},
        {"name": "Stage 7: Mountain Stage", "type": {StageCategory.MOUNTAIN: 1.0}},
        {"name": "Stage 8: Sprint Stage", "type": {StageCategory.SPRINT: 1.0}},
        {"name": "Stage 9: ITT", "type": {StageCategory.ITT: 1.0}},
        {"name": "Stage 10: Break Away", "type": {StageCategory.BREAK_AWAY: 0.7, StageCategory.PUNCH: 0.3}},
        {"name": "Stage 11: Mountain Stage", "type": {StageCategory.MOUNTAIN: 0.9, StageCategory.BREAK_AWAY: 0.1}},
        {"name": "Stage 12: Mountain Stage", "type": {StageCategory.MOUNTAIN: 1.0}},
        {"name": "Stage 13: Mountain Stage", "type": {StageCategory.MOUNTAIN: 0.8, StageCategory.BREAK_AWAY: 0.2}},
        {"name": "Stage 14: Mountain Stage", "type": {StageCategory.MOUNTAIN: 1.0}},
        {"name": "Stage 15: Sprint Stage", "type": {StageCategory.SPRINT: 0.8, StageCategory.PUNCH: 0.2}},
        {"name": "Stage 16: Mountain Stage", "type": {StageCategory.MOUNTAIN: 0.9, StageCategory.BREAK_AWAY: 0.1}},
        {"name": "Stage 17: Mountain Stage", "type": {StageCategory.MOUNTAIN: 1.0}},
        {"name": "Stage 18: Mountain Stage", "type": {StageCategory.MOUNTAIN: 0.8, StageCategory.BREAK_AWAY: 0.2}},
        {"name": "Stage 19: Mountain Stage", "type": {StageCategory.MOUNTAIN: 1.0}},
        {"name": "Stage 20: ITT", "type": {StageCategory.ITT: 1.0}},
        {"name": "Stage 21: Champs-Élysées", "type": {StageCategory.SPRINT: 1.0}}
    ]
    
    for i, stage_data in enumerate(stage_profiles, 1):
        stage = StageConfig(
            stage_number=i,
            stage_name=stage_data["name"],
            stage_type=stage_data["type"]
        )
        race.add_stage(stage)
    
    return race 