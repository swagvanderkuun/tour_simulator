"""
Tests for the riders module.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from tour_simulator.core.riders import RiderDatabase, Rider, ABILITY_TIERS
from tour_simulator.models.rider_parameters import RiderParameters
from tour_simulator.core.stage_profiles import StageType


class TestRiderParameters:
    """Test RiderParameters class."""

    def test_creation(self):
        """Test basic parameter creation."""
        params = RiderParameters(
            sprint_ability=95,
            punch_ability=85,
            itt_ability=75,
            mountain_ability=90,
            break_away_ability=80
        )
        
        assert params.sprint_ability == 95
        assert params.punch_ability == 85
        assert params.itt_ability == 75
        assert params.mountain_ability == 90
        assert params.break_away_ability == 80

    def test_get_probability_range_exceptional(self):
        """Test probability range for exceptional rider."""
        params = RiderParameters(
            sprint_ability=98,  # Exceptional
            punch_ability=50,
            itt_ability=50,
            mountain_ability=50,
            break_away_ability=50
        )
        
        # Mock stage profile
        stage_profile = {StageType.SPRINT: 1.0}
        
        min_val, mode_val, max_val = params.get_weighted_probability_range(stage_profile)
        
        # Exceptional riders should have low values (better positions)
        assert min_val <= mode_val <= max_val
        assert min_val >= 1  # Position 1 is best possible
        assert max_val <= 10  # Should be in top 10

    def test_get_probability_range_average(self):
        """Test probability range for average rider."""
        params = RiderParameters(
            sprint_ability=55,  # Average
            punch_ability=50,
            itt_ability=50,
            mountain_ability=50,
            break_away_ability=50
        )
        
        stage_profile = {StageType.SPRINT: 1.0}
        min_val, mode_val, max_val = params.get_weighted_probability_range(stage_profile)
        
        # Average riders should have higher values (worse positions)
        assert min_val <= mode_val <= max_val
        assert mode_val >= 20  # Should be around middle of pack

    def test_weighted_probability_range_mixed_stage(self):
        """Test weighted probability for mixed stage types."""
        params = RiderParameters(
            sprint_ability=95,  # Excellent sprinter
            punch_ability=70,   # Average puncher
            itt_ability=50,
            mountain_ability=50,
            break_away_ability=50
        )
        
        # 60% sprint, 40% punch stage
        stage_profile = {
            StageType.SPRINT: 0.6,
            StageType.PUNCH: 0.4
        }
        
        min_val, mode_val, max_val = params.get_weighted_probability_range(stage_profile)
        
        # Should be weighted between sprint (excellent) and punch (average)
        assert min_val <= mode_val <= max_val


class TestRider:
    """Test Rider class."""

    def test_creation(self):
        """Test basic rider creation."""
        params = RiderParameters(90, 85, 80, 75, 70)
        rider = Rider(
            name="Test Rider",
            team="Test Team",
            parameters=params,
            age=25,
            price=2.5,
            chance_of_abandon=0.05
        )
        
        assert rider.name == "Test Rider"
        assert rider.team == "Test Team"
        assert rider.age == 25
        assert rider.price == 2.5
        assert rider.chance_of_abandon == 0.05
        assert rider.parameters == params

    def test_get_stage_probability(self):
        """Test stage probability calculation."""
        params = RiderParameters(95, 85, 80, 75, 70)
        rider = Rider("Test", "Team", params, 25)
        
        # Mock stage profile
        with patch('tour_simulator.core.riders.get_stage_profile') as mock_profile:
            mock_profile.return_value = {StageType.SPRINT: 1.0}
            
            min_val, mode_val, max_val = rider.get_stage_probability(1)
            
            assert min_val <= mode_val <= max_val
            mock_profile.assert_called_once_with(1)


class TestRiderDatabase:
    """Test RiderDatabase class."""

    def test_initialization(self):
        """Test database initialization."""
        db = RiderDatabase()
        
        # Should have riders loaded
        riders = db.get_all_riders()
        assert len(riders) > 0
        
        # Check first rider has expected attributes
        rider = riders[0]
        assert hasattr(rider, 'name')
        assert hasattr(rider, 'team')
        assert hasattr(rider, 'parameters')
        assert hasattr(rider, 'age')
        assert hasattr(rider, 'price')
        assert hasattr(rider, 'chance_of_abandon')

    def test_get_rider_by_name(self):
        """Test getting rider by name."""
        db = RiderDatabase()
        
        # Get first rider name
        all_riders = db.get_all_riders()
        test_rider_name = all_riders[0].name
        
        # Test getting existing rider
        rider = db.get_rider(test_rider_name)
        assert rider.name == test_rider_name
        
        # Test getting non-existent rider
        with pytest.raises(ValueError, match="not found"):
            db.get_rider("Non-existent Rider")

    def test_get_youth_riders(self):
        """Test getting youth riders."""
        db = RiderDatabase()
        
        youth_riders = db.get_youth_riders(25)
        all_riders = db.get_all_riders()
        
        # All youth riders should be <= 25 years old
        for rider in youth_riders:
            assert rider.age <= 25
        
        # Should be subset of all riders
        assert len(youth_riders) <= len(all_riders)

    @patch('numpy.random.triangular')
    def test_generate_stage_result(self, mock_triangular):
        """Test stage result generation."""
        db = RiderDatabase()
        rider = db.get_all_riders()[0]
        
        # Mock the random result
        mock_triangular.return_value = 5.5
        
        result = db.generate_stage_result(rider, 1)
        
        assert result == 5.5
        mock_triangular.assert_called_once()

    def test_rider_data_consistency(self):
        """Test that rider data is consistent."""
        db = RiderDatabase()
        riders = db.get_all_riders()
        
        for rider in riders:
            # Check all required fields are present
            assert rider.name is not None
            assert rider.team is not None
            assert rider.age > 0
            assert rider.price >= 0
            assert 0 <= rider.chance_of_abandon <= 1
            
            # Check parameters are valid
            assert 0 <= rider.parameters.sprint_ability <= 100
            assert 0 <= rider.parameters.punch_ability <= 100
            assert 0 <= rider.parameters.itt_ability <= 100
            assert 0 <= rider.parameters.mountain_ability <= 100
            assert 0 <= rider.parameters.break_away_ability <= 100

    def test_ability_tiers_mapping(self):
        """Test ABILITY_TIERS mapping is correct."""
        assert ABILITY_TIERS["S"] == 98
        assert ABILITY_TIERS["A"] == 95
        assert ABILITY_TIERS["B"] == 90
        assert ABILITY_TIERS["C"] == 80
        assert ABILITY_TIERS["D"] == 70
        assert ABILITY_TIERS["E"] == 40

    def test_rider_tier_assignment(self):
        """Test that riders are assigned correct ability values based on tiers."""
        db = RiderDatabase()
        riders = db.get_all_riders()
        
        # Check that abilities match tier values
        for rider in riders:
            abilities = [
                rider.parameters.sprint_ability,
                rider.parameters.punch_ability,
                rider.parameters.itt_ability,
                rider.parameters.mountain_ability,
                rider.parameters.break_away_ability
            ]
            
            for ability in abilities:
                # Should match one of the tier values
                assert ability in ABILITY_TIERS.values()

    def test_team_constraints(self):
        """Test that team distribution makes sense."""
        db = RiderDatabase()
        riders = db.get_all_riders()
        
        # Group by team
        teams = {}
        for rider in riders:
            if rider.team not in teams:
                teams[rider.team] = []
            teams[rider.team].append(rider)
        
        # Should have multiple teams
        assert len(teams) > 1
        
        # Teams should have reasonable number of riders
        for team, team_riders in teams.items():
            assert len(team_riders) >= 1  # At least one rider per team


class TestRiderIntegration:
    """Integration tests for rider-related functionality."""

    def test_simulation_with_riders(self):
        """Test that riders work correctly in simulation context."""
        from tour_simulator.core.simulator import TourSimulator
        
        # Create simulator with default rider database
        simulator = TourSimulator()
        
        # Check that rider database is properly initialized
        assert len(simulator.rider_db.get_all_riders()) > 0
        assert len(simulator.youth_rider_names) > 0
        
        # Check youth riders are properly identified
        all_riders = simulator.rider_db.get_all_riders()
        youth_count = len([r for r in all_riders if r.age < 25])
        assert len(simulator.youth_rider_names) == youth_count

    def test_rider_performance_distribution(self):
        """Test that rider performance follows expected distribution."""
        db = RiderDatabase()
        rider = db.get_all_riders()[0]
        
        # Generate multiple results for same stage
        results = []
        for _ in range(100):
            result = db.generate_stage_result(rider, 1)
            results.append(result)
        
        # Results should be distributed (not all the same)
        assert len(set(results)) > 1
        
        # Results should be positive
        assert all(r > 0 for r in results)


if __name__ == "__main__":
    pytest.main([__file__]) 