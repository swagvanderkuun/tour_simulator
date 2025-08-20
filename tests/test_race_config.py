"""
Tests for race configuration system.
"""

import pytest
import json
from pathlib import Path
import tempfile
from datetime import datetime

from tour_simulator.config.race_config import (
    RaceConfig, StageConfig, StageCategory, 
    create_tour_de_france_2025
)


class TestStageCategory:
    """Test StageCategory enum."""
    
    def test_stage_category_values(self):
        """Test that all stage categories have correct values."""
        assert StageCategory.SPRINT.value == "sprint"
        assert StageCategory.PUNCH.value == "punch"
        assert StageCategory.ITT.value == "itt"
        assert StageCategory.TTT.value == "ttt"
        assert StageCategory.MOUNTAIN.value == "mountain"
        assert StageCategory.BREAK_AWAY.value == "break_away"
    
    def test_ttt_category_exists(self):
        """Test that TTT category was successfully added."""
        assert StageCategory.TTT in StageCategory
        assert StageCategory.TTT.value == "ttt"


class TestStageConfig:
    """Test StageConfig class."""
    
    def test_stage_config_creation(self):
        """Test basic stage configuration creation."""
        stage = StageConfig(
            stage_number=1,
            stage_name="Stage 1: Flat",
            stage_type={StageCategory.SPRINT: 1.0}
        )
        
        assert stage.stage_number == 1
        assert stage.stage_name == "Stage 1: Flat"
        assert stage.stage_type[StageCategory.SPRINT] == 1.0
    
    def test_stage_config_with_optional_fields(self):
        """Test stage configuration with optional fields."""
        stage = StageConfig(
            stage_number=2,
            stage_name="Stage 2: Mountain",
            stage_type={StageCategory.MOUNTAIN: 0.8, StageCategory.BREAK_AWAY: 0.2},
            distance=180.5,
            elevation_gain=3000,
            start_city="Nice",
            finish_city="Col du Galibier"
        )
        
        assert stage.distance == 180.5
        assert stage.elevation_gain == 3000
        assert stage.start_city == "Nice"
        assert stage.finish_city == "Col du Galibier"
    
    def test_stage_config_weight_validation(self):
        """Test that stage type weights must sum to 1.0."""
        # Valid weights
        StageConfig(
            stage_number=1,
            stage_name="Test",
            stage_type={StageCategory.SPRINT: 0.6, StageCategory.PUNCH: 0.4}
        )
        
        # Invalid weights
        with pytest.raises(ValueError, match="Stage type weights must sum to 1.0"):
            StageConfig(
                stage_number=1,
                stage_name="Test",
                stage_type={StageCategory.SPRINT: 0.6, StageCategory.PUNCH: 0.5}
            )
    
    def test_ttt_stage_config(self):
        """Test TTT stage configuration."""
        stage = StageConfig(
            stage_number=5,
            stage_name="Stage 5: Team Time Trial",
            stage_type={StageCategory.TTT: 1.0}
        )
        
        assert StageCategory.TTT in stage.stage_type
        assert stage.stage_type[StageCategory.TTT] == 1.0


class TestRaceConfig:
    """Test RaceConfig class."""
    
    def test_race_config_creation(self):
        """Test basic race configuration creation."""
        race = RaceConfig(
            race_name="Test Race",
            race_short_name="TR",
            year=2025,
            total_stages=5
        )
        
        assert race.race_name == "Test Race"
        assert race.race_short_name == "TR"
        assert race.year == 2025
        assert race.total_stages == 5
        assert len(race.stages) == 0
    
    def test_race_config_default_initialization(self):
        """Test that race config initializes with proper defaults."""
        race = RaceConfig(
            race_name="Test Race",
            race_short_name="TR",
            year=2025,
            total_stages=3
        )
        
        # Check UI texts
        assert "app_title" in race.ui_texts
        assert race.ui_texts["app_title"] == "Test Race Simulator"
        assert race.ui_texts["app_icon"] == "🚴‍♂️"
        
        # Check default points
        assert "category_1" in race.sprint_points
        assert "hc" in race.mountain_points
        
        # Check other defaults
        assert race.youth_age_limit == 25
        assert race.max_riders_per_team == 4
    
    def test_add_stage(self):
        """Test adding stages to race configuration."""
        race = RaceConfig("Test", "T", 2025, 2)
        
        stage1 = StageConfig(1, "Stage 1", {StageCategory.SPRINT: 1.0})
        race.add_stage(stage1)
        
        assert len(race.stages) == 1
        assert race.stages[0] == stage1
        
        stage2 = StageConfig(2, "Stage 2", {StageCategory.MOUNTAIN: 1.0})
        race.add_stage(stage2)
        
        assert len(race.stages) == 2
    
    def test_add_stage_wrong_number(self):
        """Test that adding stage with wrong number raises error."""
        race = RaceConfig("Test", "T", 2025, 3)
        
        # Should fail - first stage should be number 1, not 2
        with pytest.raises(ValueError, match="Stage number 2 should be 1"):
            stage = StageConfig(2, "Stage 2", {StageCategory.SPRINT: 1.0})
            race.add_stage(stage)
    
    def test_get_stage(self):
        """Test getting stage by number."""
        race = RaceConfig("Test", "T", 2025, 2)
        
        stage1 = StageConfig(1, "Stage 1", {StageCategory.SPRINT: 1.0})
        stage2 = StageConfig(2, "Stage 2", {StageCategory.TTT: 1.0})
        race.add_stage(stage1)
        race.add_stage(stage2)
        
        assert race.get_stage(1) == stage1
        assert race.get_stage(2) == stage2
        assert race.get_stage(3) is None
    
    def test_save_and_load_race_config(self):
        """Test saving and loading race configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_race.json"
            
            # Create and save race config
            race = RaceConfig("Test Race", "TR", 2025, 2)
            stage1 = StageConfig(1, "Sprint Stage", {StageCategory.SPRINT: 1.0})
            stage2 = StageConfig(2, "TTT Stage", {StageCategory.TTT: 1.0}, distance=50.0)
            race.add_stage(stage1)
            race.add_stage(stage2)
            
            race.save_to_file(filepath)
            
            # Load and verify
            loaded_race = RaceConfig.load_from_file(filepath)
            
            assert loaded_race.race_name == "Test Race"
            assert loaded_race.race_short_name == "TR"
            assert loaded_race.year == 2025
            assert loaded_race.total_stages == 2
            assert len(loaded_race.stages) == 2
            
            # Check stages
            loaded_stage1 = loaded_race.get_stage(1)
            assert loaded_stage1.stage_name == "Sprint Stage"
            assert StageCategory.SPRINT in loaded_stage1.stage_type
            
            loaded_stage2 = loaded_race.get_stage(2)
            assert loaded_stage2.stage_name == "TTT Stage"
            assert StageCategory.TTT in loaded_stage2.stage_type
            assert loaded_stage2.distance == 50.0


class TestTourDeFrance2025:
    """Test Tour de France 2025 configuration."""
    
    def test_create_tour_de_france_2025(self):
        """Test creating default Tour de France 2025 configuration."""
        race = create_tour_de_france_2025()
        
        assert race.race_name == "Tour de France"
        assert race.race_short_name == "TDF"
        assert race.year == 2025
        assert race.total_stages == 21
        assert len(race.stages) == 21
    
    def test_tdf_2025_has_ttt_stage(self):
        """Test that TDF 2025 configuration includes TTT stage."""
        race = create_tour_de_france_2025()
        
        # Stage 5 should be TTT
        stage5 = race.get_stage(5)
        assert stage5 is not None
        assert "TTT" in stage5.stage_name
        assert StageCategory.TTT in stage5.stage_type
        assert stage5.stage_type[StageCategory.TTT] == 1.0
    
    def test_tdf_2025_stage_variety(self):
        """Test that TDF 2025 has variety of stage types."""
        race = create_tour_de_france_2025()
        
        # Check that we have different stage types
        stage_types_used = set()
        for stage in race.stages:
            for stage_type in stage.stage_type.keys():
                stage_types_used.add(stage_type)
        
        # Should have at least sprint, mountain, ITT, TTT
        assert StageCategory.SPRINT in stage_types_used
        assert StageCategory.MOUNTAIN in stage_types_used
        assert StageCategory.ITT in stage_types_used
        assert StageCategory.TTT in stage_types_used
    
    def test_tdf_2025_ui_texts(self):
        """Test that TDF 2025 has proper UI texts."""
        race = create_tour_de_france_2025()
        
        assert race.ui_texts["app_title"] == "Tour de France Simulator"
        assert "Welcome to the Tour de France 2025" in race.ui_texts["welcome_message"]
        assert race.ui_texts["gc_label"] == "General Classification"


class TestIntegration:
    """Integration tests for race configuration system."""
    
    def test_full_race_configuration_workflow(self):
        """Test complete workflow of creating, saving, and loading race config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "vuelta_2025.json"
            
            # Create Vuelta España 2025 configuration
            race = RaceConfig(
                race_name="Vuelta a España",
                race_short_name="Vuelta",
                year=2025,
                total_stages=21
            )
            
            # Add some stages with different types
            stages_data = [
                ("Prologue ITT", {StageCategory.ITT: 1.0}),
                ("Flat Stage", {StageCategory.SPRINT: 1.0}),
                ("Hilly Stage", {StageCategory.PUNCH: 0.7, StageCategory.SPRINT: 0.3}),
                ("Team Time Trial", {StageCategory.TTT: 1.0}),
                ("Mountain Stage", {StageCategory.MOUNTAIN: 0.9, StageCategory.BREAK_AWAY: 0.1})
            ]
            
            for i, (name, stage_type) in enumerate(stages_data, 1):
                stage = StageConfig(i, f"Stage {i}: {name}", stage_type)
                race.add_stage(stage)
            
            # Save configuration
            race.save_to_file(filepath)
            
            # Load and verify
            loaded_race = RaceConfig.load_from_file(filepath)
            
            assert loaded_race.race_name == "Vuelta a España"
            assert loaded_race.race_short_name == "Vuelta"
            assert len(loaded_race.stages) == 5
            
            # Verify TTT stage exists
            ttt_stage = loaded_race.get_stage(4)
            assert "Team Time Trial" in ttt_stage.stage_name
            assert StageCategory.TTT in ttt_stage.stage_type 