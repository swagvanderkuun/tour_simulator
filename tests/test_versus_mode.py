"""
Tests for the versus_mode module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock, PropertyMock

from tour_simulator.services.versus_mode import VersusMode, UserTeam
from tour_simulator.core.riders import RiderDatabase, Rider
from tour_simulator.models.rider_parameters import RiderParameters
from tour_simulator.services.team_optimization import TeamSelection


class TestUserTeam:
    """Test UserTeam dataclass."""

    def test_creation(self):
        """Test user team creation."""
        params = RiderParameters(90, 85, 80, 75, 70)
        riders = [
            Rider("Rider1", "Team1", params, 25, 2.0, 0.05),
            Rider("Rider2", "Team2", params, 26, 2.5, 0.03)
        ]
        
        user_team = UserTeam(
            riders=riders,
            total_cost=4.5,
            rider_names=["Rider1", "Rider2"]
        )
        
        assert len(user_team.riders) == 2
        assert user_team.total_cost == 4.5
        assert user_team.rider_names == ["Rider1", "Rider2"]
        assert user_team.stage_selections is None
        assert user_team.stage_points is None
        assert user_team.simulation_results is None

    def test_str_representation(self):
        """Test string representation."""
        params = RiderParameters(90, 85, 80, 75, 70)
        riders = [Rider("Rider1", "Team1", params, 25, 2.0, 0.05)]
        
        user_team = UserTeam(
            riders=riders,
            total_cost=2.0,
            rider_names=["Rider1"]
        )
        
        str_repr = str(user_team)
        assert "User Team" in str_repr
        assert "2.00" in str_repr
        assert "Rider1" in str_repr


class TestVersusMode:
    """Test VersusMode class."""

    def test_initialization(self):
        """Test versus mode initialization."""
        versus = VersusMode(budget=48.0, team_size=20)
        
        assert versus.budget == 48.0
        assert versus.team_size == 20
        assert versus.riders_per_stage == 9
        assert versus.final_stage_riders == 20
        assert versus.rider_db is not None
        assert versus.team_optimizer is not None

    def test_initialization_custom_params(self):
        """Test versus mode with custom parameters."""
        versus = VersusMode(
            budget=50.0,
            team_size=15,
            riders_per_stage=8,
            final_stage_riders=15
        )
        
        assert versus.budget == 50.0
        assert versus.team_size == 15
        assert versus.riders_per_stage == 8
        assert versus.final_stage_riders == 15

    def test_get_available_riders(self):
        """Test getting available riders."""
        versus = VersusMode()
        riders_df = versus.get_available_riders()
        
        assert isinstance(riders_df, pd.DataFrame)
        
        expected_columns = [
            'name', 'team', 'age', 'price', 'sprint_ability',
            'punch_ability', 'itt_ability', 'mountain_ability',
            'break_away_ability', 'chance_of_abandon'
        ]
        
        for col in expected_columns:
            assert col in riders_df.columns
        
        # Should have riders
        assert len(riders_df) > 0
        
        # Should be sorted by team and name
        assert riders_df['team'].iloc[0] <= riders_df['team'].iloc[-1]

    def test_validate_team_selection_valid(self):
        """Test validation of valid team selection."""
        versus = VersusMode(budget=48.0, team_size=3)
        
        # Get first 3 riders that fit budget
        riders_df = versus.get_available_riders()
        cheap_riders = riders_df[riders_df['price'] <= 15.0].head(3)
        selected_names = cheap_riders['name'].tolist()
        
        is_valid, message = versus.validate_team_selection(selected_names)
        
        assert is_valid
        assert "valid" in message.lower()

    def test_validate_team_selection_wrong_size(self):
        """Test validation with wrong team size."""
        versus = VersusMode(team_size=20)
        
        selected_names = ["Rider1", "Rider2"]  # Only 2 riders
        
        is_valid, message = versus.validate_team_selection(selected_names)
        
        assert not is_valid
        assert "20 riders" in message

    def test_validate_team_selection_over_budget(self):
        """Test validation with team over budget."""
        versus = VersusMode(budget=5.0, team_size=2)
        
        # Mock expensive riders
        with patch.object(versus.rider_db, 'get_rider') as mock_get:
            params = RiderParameters(90, 85, 80, 75, 70)
            mock_get.side_effect = [
                Rider("Expensive1", "Team1", params, 25, 10.0, 0.05),
                Rider("Expensive2", "Team2", params, 26, 10.0, 0.03)
            ]
            
            selected_names = ["Expensive1", "Expensive2"]
            
            is_valid, message = versus.validate_team_selection(selected_names)
            
            assert not is_valid
            assert "budget" in message.lower()

    def test_validate_team_selection_too_many_from_team(self):
        """Test validation with too many riders from same team."""
        versus = VersusMode(team_size=5)
        
        # Mock riders all from same team
        with patch.object(versus.rider_db, 'get_rider') as mock_get:
            params = RiderParameters(90, 85, 80, 75, 70)
            mock_riders = [
                Rider(f"Rider{i}", "SameTeam", params, 25, 1.0, 0.05)
                for i in range(5)
            ]
            mock_get.side_effect = mock_riders
            
            selected_names = [f"Rider{i}" for i in range(5)]
            
            is_valid, message = versus.validate_team_selection(selected_names)
            
            assert not is_valid
            assert "4" in message  # Maximum 4 riders per team

    def test_validate_team_selection_nonexistent_rider(self):
        """Test validation with non-existent rider."""
        versus = VersusMode(team_size=1)
        
        with patch.object(versus.rider_db, 'get_rider') as mock_get:
            mock_get.side_effect = ValueError("Rider NonexistentRider not found")
            
            selected_names = ["NonexistentRider"]
            
            # Should raise the ValueError since it's not caught
            with pytest.raises(ValueError, match="Rider NonexistentRider not found"):
                versus.validate_team_selection(selected_names)

    def test_create_user_team(self):
        """Test creating user team from rider names."""
        versus = VersusMode()
        
        # Mock riders
        with patch.object(versus.rider_db, 'get_rider') as mock_get:
            params = RiderParameters(90, 85, 80, 75, 70)
            mock_riders = [
                Rider("Rider1", "Team1", params, 25, 2.0, 0.05),
                Rider("Rider2", "Team2", params, 26, 3.0, 0.03)
            ]
            mock_get.side_effect = mock_riders
            
            selected_names = ["Rider1", "Rider2"]
            user_team = versus.create_user_team(selected_names)
            
            assert isinstance(user_team, UserTeam)
            assert len(user_team.riders) == 2
            assert user_team.total_cost == 5.0
            assert user_team.rider_names == selected_names

    @patch('tour_simulator.services.versus_mode.LpProblem')
    @patch('tour_simulator.services.versus_mode.LpVariable')
    def test_optimize_stage_selection(self, mock_lpvar, mock_lpproblem):
        """Test stage selection optimization."""
        versus = VersusMode()
        
        # Create mock user team
        params = RiderParameters(90, 85, 80, 75, 70)
        riders = [Rider("Rider1", "Team1", params, 25, 2.0, 0.05)]
        user_team = UserTeam(riders, 2.0, ["Rider1"])
        
        # Mock rider data
        rider_data = pd.DataFrame({
            'rider_name': ['Rider1'],
            'expected_points': [50.0]
        })
        
        # Create a real problem object for testing
        from pulp import LpProblem, LpStatusOptimal, LpMaximize
        real_prob = LpProblem("test", LpMaximize)
        real_prob.status = LpStatusOptimal
        real_prob.solve = MagicMock(return_value=None)
        mock_lpproblem.return_value = real_prob
        
        # Mock stage vars for all riders and stages
        mock_var = MagicMock()
        mock_var.value.return_value = 1
        stage_vars = {}
        for rider in ["Rider1"]:
            for stage in range(1, 23):  # 22 stages (including final stage 22)
                stage_vars[(rider, stage)] = mock_var
        mock_lpvar.dicts.return_value = stage_vars
        
        # Mock stage performance data
        with patch.object(versus.team_optimizer, '_get_stage_performance_data') as mock_perf:
            mock_perf.return_value = {("Rider1", 1): 25.0}
            
            result = versus.optimize_stage_selection(user_team, rider_data)
            
            assert isinstance(result, UserTeam)

    def test_get_rider_stage_points(self):
        """Test getting rider stage points from simulation."""
        versus = VersusMode()
        
        # Mock simulator with scorito points records
        mock_simulator = MagicMock()
        mock_simulator.scorito_points_records = [
            {'rider': 'Rider1', 'stage': 1, 'scorito_points': 50},
            {'rider': 'Rider1', 'stage': 2, 'scorito_points': 75}
        ]
        
        # Test stage 1 (first stage)
        points_stage_1 = versus._get_rider_stage_points(mock_simulator, 'Rider1', 1)
        assert points_stage_1 == 50
        
        # Test stage 2 (difference from previous)
        points_stage_2 = versus._get_rider_stage_points(mock_simulator, 'Rider1', 2)
        assert points_stage_2 == 25  # 75 - 50

    def test_get_rider_stage_points_missing_rider(self):
        """Test getting stage points for missing rider."""
        versus = VersusMode()
        
        mock_simulator = MagicMock()
        mock_simulator.scorito_points_records = []
        
        points = versus._get_rider_stage_points(mock_simulator, 'MissingRider', 1)
        assert points == 0.0

    def test_calculate_optimal_stage_points_for_simulation(self):
        """Test calculating optimal stage points."""
        versus = VersusMode()
        
        # Mock simulator
        mock_simulator = MagicMock()
        mock_simulator.scorito_points = {'Rider1': 100, 'Rider2': 80, 'Rider3': 60}
        
        # Mock stage points method
        with patch.object(versus, '_get_rider_stage_points') as mock_stage_points:
            # Return different points for different riders/stages
            def side_effect(sim, rider, stage):
                base_points = {'Rider1': 10, 'Rider2': 8, 'Rider3': 6}
                return base_points.get(rider, 0) * stage
            
            mock_stage_points.side_effect = side_effect
            
            rider_names = ['Rider1', 'Rider2', 'Rider3']
            total_points = versus._calculate_optimal_stage_points_for_simulation(
                mock_simulator, rider_names
            )
            
            # Should select best riders for each stage
            assert total_points > 0

    @patch('builtins.print')  # Suppress output
    def test_get_optimal_team(self, mock_print):
        """Test getting optimal team."""
        versus = VersusMode()
        
        # Mock team optimizer methods
        with patch.object(versus.team_optimizer, 'run_simulation_with_teammate_analysis') as mock_run_sim:
            with patch.object(versus.team_optimizer, 'optimize_with_stage_selection') as mock_optimize:
                # Mock simulation results
                mock_run_sim.return_value = pd.DataFrame({
                    'rider_name': ['Rider1', 'Rider2'],
                    'expected_points': [50.0, 60.0]
                })
                
                # Mock optimization result
                params = RiderParameters(90, 85, 80, 75, 70)
                mock_team = TeamSelection(
                    riders=[Rider("Rider1", "Team1", params, 25, 2.0, 0.05)],
                    total_cost=2.0,
                    expected_points=50.0,
                    rider_names=["Rider1"]
                )
                mock_optimize.return_value = mock_team
                
                result = versus.get_optimal_team(num_simulations=10, metric='mean')
                
                assert isinstance(result, TeamSelection)
                mock_run_sim.assert_called_once()
                mock_optimize.assert_called_once()

    def test_compare_teams(self):
        """Test team comparison."""
        versus = VersusMode()
        
        # Create mock teams
        params = RiderParameters(90, 85, 80, 75, 70)
        
        user_team = UserTeam(
            riders=[Rider("Rider1", "Team1", params, 25, 2.0, 0.05)],
            total_cost=2.0,
            rider_names=["Rider1"]
        )
        
        optimal_team = TeamSelection(
            riders=[Rider("Rider2", "Team2", params, 26, 3.0, 0.03)],
            total_cost=3.0,
            expected_points=60.0,
            rider_names=["Rider2"]
        )
        
        # Mock methods
        with patch.object(versus.team_optimizer, 'run_simulation_with_teammate_analysis') as mock_sim:
            with patch.object(versus.team_optimizer, '_get_stage_performance_data') as mock_perf:
                # Mock simulation data
                mock_sim.return_value = pd.DataFrame({
                    'rider_name': ['Rider1', 'Rider2'],
                    'expected_points': [50.0, 60.0],
                    'points_std': [5.0, 6.0],
                    'team': ['Team1', 'Team2'],
                    'age': [25, 26],
                    'price': [2.0, 3.0],
                    'chance_of_abandon': [0.05, 0.03],
                    'teammate_bonus_potential': [0.0, 0.0]
                })
                
                # Mock stage performance
                mock_perf.return_value = {('Rider1', 1): 25.0, ('Rider2', 1): 30.0}
                
                comparison = versus.compare_teams(user_team, optimal_team)
                
                assert isinstance(comparison, dict)
                assert 'user_team' in comparison
                assert 'optimal_team' in comparison
                assert 'comparison' in comparison

    def test_analyze_teammate_bonuses_from_simulation(self):
        """Test teammate bonus analysis."""
        versus = VersusMode()
        
        # Mock simulator with scorito points
        mock_simulator = MagicMock()
        mock_simulator.scorito_points = {'Rider1': 100, 'Rider2': 80, 'Rider3': 0}
        
        # Mock rider database
        with patch.object(versus, 'rider_db') as mock_db:
            params = RiderParameters(90, 85, 80, 75, 70)
            mock_riders = [
                Rider("Rider1", "Team1", params, 25, 2.0, 0.05),
                Rider("Rider2", "Team1", params, 26, 3.0, 0.03),  # Same team
                Rider("Rider3", "Team2", params, 24, 1.5, 0.04)   # Different team
            ]
            mock_db.get_all_riders.return_value = mock_riders
            
            analysis = versus._analyze_teammate_bonuses_from_simulation(mock_simulator)
            
            assert isinstance(analysis, dict)
            assert 'Team1' in analysis
            assert 'Team2' in analysis
            
            # Team1 should have 2 riders
            assert analysis['Team1']['team_size'] == 2
            # Team2 should have 1 rider
            assert analysis['Team2']['team_size'] == 1

    def test_estimate_teammate_bonus_per_rider(self):
        """Test teammate bonus estimation."""
        versus = VersusMode()
        
        # Test different team sizes
        bonus_1 = versus._estimate_teammate_bonus_per_rider(1)
        bonus_2 = versus._estimate_teammate_bonus_per_rider(2)
        bonus_3 = versus._estimate_teammate_bonus_per_rider(3)
        bonus_4 = versus._estimate_teammate_bonus_per_rider(4)
        
        assert bonus_1 == 0.0  # Single rider gets no bonus
        assert bonus_2 == 1.0  # Two riders get some bonus
        assert bonus_3 == 1.5  # Three riders get more bonus
        assert bonus_4 == 2.0  # Four riders get most bonus

    def test_calculate_individual_rider_sum(self):
        """Test individual rider sum calculation."""
        versus = VersusMode()
        
        params = RiderParameters(90, 85, 80, 75, 70)
        user_team = UserTeam(
            riders=[Rider("Rider1", "Team1", params, 25, 2.0, 0.05)],
            total_cost=2.0,
            rider_names=["Rider1", "Rider2"]
        )
        
        rider_data = pd.DataFrame({
            'rider_name': ['Rider1', 'Rider2'],
            'expected_points': [50.0, 60.0]
        })
        
        total_sum = versus.calculate_individual_rider_sum(user_team, rider_data)
        assert total_sum == 110.0  # 50 + 60


class TestVersusIntegration:
    """Integration tests for versus mode."""

    def test_full_versus_workflow_mocked(self):
        """Test complete versus workflow with mocking."""
        versus = VersusMode(budget=10.0, team_size=2)
        
        # Mock all external dependencies
        with patch.object(versus.rider_db, 'get_rider') as mock_get_rider:
            with patch.object(versus, 'optimize_stage_selection') as mock_optimize_stage:
                with patch.object(versus, 'get_optimal_team') as mock_get_optimal:
                    with patch.object(versus, 'compare_teams') as mock_compare:
                        
                        # Setup mocks
                        params = RiderParameters(90, 85, 80, 75, 70)
                        rider1 = Rider("Rider1", "Team1", params, 25, 2.0, 0.05)
                        rider2 = Rider("Rider2", "Team2", params, 26, 3.0, 0.03)
                        
                        def get_rider_mock(name):
                            if name == "Rider1":
                                return rider1
                            elif name == "Rider2":
                                return rider2
                            else:
                                raise ValueError(f"Rider {name} not found")
                        
                        mock_get_rider.side_effect = get_rider_mock
                        mock_riders = [rider1, rider2]
                        
                        user_team = UserTeam(mock_riders, 5.0, ["Rider1", "Rider2"])
                        mock_optimize_stage.return_value = user_team
                        
                        optimal_team = TeamSelection(mock_riders, 5.0, 100.0, ["Rider1", "Rider2"])
                        mock_get_optimal.return_value = optimal_team
                        
                        comparison = {
                            'user_team': {'expected_points': 90.0},
                            'optimal_team': {'expected_points': 100.0},
                            'comparison': {'performance_difference': -10.0}
                        }
                        mock_compare.return_value = comparison
                        
                        # Test workflow
                        selected_names = ["Rider1", "Rider2"]
                        
                        # Validate team
                        is_valid, _ = versus.validate_team_selection(selected_names)
                        assert is_valid
                        
                        # Create user team
                        created_team = versus.create_user_team(selected_names)
                        assert isinstance(created_team, UserTeam)
                        
                        # Get optimal team
                        opt_team = versus.get_optimal_team()
                        assert isinstance(opt_team, TeamSelection)
                        
                        # Compare teams
                        comp_result = versus.compare_teams(created_team, opt_team)
                        assert isinstance(comp_result, dict)

    def test_performance_characteristics(self):
        """Test versus mode performance characteristics."""
        import time
        
        versus = VersusMode(budget=5.0, team_size=2)
        
        # Test that basic operations complete quickly
        start_time = time.time()
        
        riders_df = versus.get_available_riders()
        cheap_riders = riders_df[riders_df['price'] <= 2.0].head(2)
        selected_names = cheap_riders['name'].tolist()
        
        if len(selected_names) == 2:
            is_valid, _ = versus.validate_team_selection(selected_names)
            if is_valid:
                user_team = versus.create_user_team(selected_names)
        
        end_time = time.time()
        
        # Should complete quickly (< 2 seconds)
        execution_time = end_time - start_time
        assert execution_time < 2, f"Basic operations took {execution_time:.2f}s, should be < 2s"

    def test_data_consistency(self):
        """Test data consistency across versus mode operations."""
        versus = VersusMode()
        
        # Get available riders
        riders_df = versus.get_available_riders()
        
        # Pick first rider
        first_rider_name = riders_df.iloc[0]['name']
        first_rider_price = riders_df.iloc[0]['price']
        
        # Create team with that rider
        user_team = versus.create_user_team([first_rider_name])
        
        # Data should be consistent
        assert len(user_team.riders) == 1
        assert user_team.riders[0].name == first_rider_name
        assert user_team.riders[0].price == first_rider_price
        assert user_team.total_cost == first_rider_price


if __name__ == "__main__":
    pytest.main([__file__]) 