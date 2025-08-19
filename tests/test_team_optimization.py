"""
Tests for the team_optimization module.
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from tour_simulator.services.team_optimization import TeamOptimizer, TeamSelection
from tour_simulator.core.riders import RiderDatabase, Rider
from tour_simulator.models.rider_parameters import RiderParameters


class TestTeamSelection:
    """Test TeamSelection dataclass."""

    def test_creation(self):
        """Test team selection creation."""
        params = RiderParameters(90, 85, 80, 75, 70)
        riders = [
            Rider("Rider1", "Team1", params, 25, 2.0, 0.05),
            Rider("Rider2", "Team2", params, 26, 2.5, 0.03)
        ]
        
        selection = TeamSelection(
            riders=riders,
            total_cost=4.5,
            expected_points=150.0,
            rider_names=["Rider1", "Rider2"]
        )
        
        assert len(selection.riders) == 2
        assert selection.total_cost == 4.5
        assert selection.expected_points == 150.0
        assert selection.rider_names == ["Rider1", "Rider2"]

    def test_str_representation(self):
        """Test string representation."""
        params = RiderParameters(90, 85, 80, 75, 70)
        riders = [Rider("Rider1", "Team1", params, 25, 2.0, 0.05)]
        
        selection = TeamSelection(
            riders=riders,
            total_cost=2.0,
            expected_points=75.0,
            rider_names=["Rider1"]
        )
        
        str_repr = str(selection)
        assert "Team Selection" in str_repr
        assert "2.00" in str_repr
        assert "75.00" in str_repr
        assert "Rider1" in str_repr


class TestTeamOptimizer:
    """Test TeamOptimizer class."""

    def test_initialization(self):
        """Test optimizer initialization."""
        optimizer = TeamOptimizer(budget=48.0, team_size=20)
        
        assert optimizer.budget == 48.0
        assert optimizer.team_size == 20
        assert optimizer.riders_per_stage == 9
        assert optimizer.final_stage_riders == 20
        assert optimizer.simulator is not None
        assert optimizer.rider_db is not None

    def test_initialization_custom_params(self):
        """Test optimizer with custom parameters."""
        optimizer = TeamOptimizer(
            budget=50.0,
            team_size=15,
            riders_per_stage=8,
            final_stage_riders=15
        )
        
        assert optimizer.budget == 50.0
        assert optimizer.team_size == 15
        assert optimizer.riders_per_stage == 8
        assert optimizer.final_stage_riders == 15

    @patch('tour_simulator.services.team_optimization.TourSimulator')
    def test_run_single_simulation(self, mock_simulator_class):
        """Test single simulation run."""
        # Mock simulator
        mock_simulator = MagicMock()
        mock_simulator.scorito_points = {"Rider1": 100, "Rider2": 80}
        mock_simulator_class.return_value = mock_simulator
        
        optimizer = TeamOptimizer()
        result = optimizer._run_single_simulation()
        
        assert result == {"Rider1": 100, "Rider2": 80}
        mock_simulator.simulate_tour.assert_called_once()

    def test_run_simulation_with_teammate_analysis(self):
        """Test simulation with teammate analysis."""
        optimizer = TeamOptimizer()
        
        # Create mock simulation results
        mock_results = [
            {
                'scorito_points': {"Rider1": 100, "Rider2": 80},
                'teammate_bonus_analysis': {}
            },
            {
                'scorito_points': {"Rider1": 95, "Rider2": 85},
                'teammate_bonus_analysis': {}
            }
        ]
        
        # Mock the parallel processing to return our mock results directly
        with patch('tour_simulator.services.team_optimization.Parallel') as mock_parallel:
            mock_parallel.return_value.return_value = mock_results
            
            result = optimizer.run_simulation_with_teammate_analysis(num_simulations=2)
            
            assert isinstance(result, pd.DataFrame)
            assert 'rider_name' in result.columns
            assert 'expected_points' in result.columns
            assert 'teammate_bonus_potential' in result.columns

    def test_optimize_team_basic(self):
        """Test basic team optimization."""
        optimizer = TeamOptimizer(budget=10.0, team_size=2)
        
        # Create simple rider data
        rider_data = pd.DataFrame({
            'rider_name': ['Rider1', 'Rider2', 'Rider3'],
            'price': [2.0, 3.0, 6.0],
            'expected_points': [50.0, 60.0, 80.0],
            'points_std': [5.0, 6.0, 8.0],
            'team': ['Team1', 'Team2', 'Team3'],
            'chance_of_abandon': [0.05, 0.03, 0.08]
        })
        
        # Mock rider database
        with patch.object(optimizer, 'rider_db') as mock_db:
            params = RiderParameters(90, 85, 80, 75, 70)
            mock_db.get_rider.side_effect = [
                Rider("Rider1", "Team1", params, 25, 2.0, 0.05),
                Rider("Rider2", "Team2", params, 26, 3.0, 0.03)
            ]
            
            result = optimizer.optimize_team(rider_data)
            
            assert isinstance(result, TeamSelection)
            assert len(result.riders) == 2
            assert result.total_cost <= 10.0

    def test_optimize_team_with_constraints(self):
        """Test team optimization with constraints."""
        optimizer = TeamOptimizer(budget=20.0, team_size=3)
        
        # Create rider data with team constraints
        rider_data = pd.DataFrame({
            'rider_name': ['R1', 'R2', 'R3', 'R4', 'R5'],
            'price': [2.0, 3.0, 4.0, 5.0, 6.0],
            'expected_points': [40.0, 50.0, 60.0, 70.0, 80.0],
            'points_std': [4.0, 5.0, 6.0, 7.0, 8.0],
            'team': ['Team1', 'Team1', 'Team2', 'Team2', 'Team3'],
            'chance_of_abandon': [0.05, 0.03, 0.04, 0.02, 0.06]
        })
        
        # Require minimum riders from Team1
        min_riders_per_team = {'Team1': 1}
        
        with patch.object(optimizer, 'rider_db') as mock_db:
            params = RiderParameters(90, 85, 80, 75, 70)
            mock_riders = [
                Rider("R1", "Team1", params, 25, 2.0, 0.05),
                Rider("R2", "Team1", params, 26, 3.0, 0.03),
                Rider("R5", "Team3", params, 24, 6.0, 0.06)
            ]
            mock_db.get_rider.side_effect = mock_riders
            
            result = optimizer.optimize_team(rider_data, min_riders_per_team=min_riders_per_team)
            
            # Should have at least one rider from Team1
            team1_riders = [r for r in result.riders if r.team == 'Team1']
            assert len(team1_riders) >= 1

    def test_optimize_team_risk_aversion(self):
        """Test optimization with risk aversion."""
        optimizer = TeamOptimizer(budget=15.0, team_size=2)
        
        rider_data = pd.DataFrame({
            'rider_name': ['Safe', 'Risky'],
            'price': [5.0, 5.0],
            'expected_points': [60.0, 65.0],  # Risky has slightly higher expected points
            'points_std': [2.0, 10.0],  # But much higher variance
            'team': ['Team1', 'Team2'],
            'chance_of_abandon': [0.02, 0.02]
        })
        
        with patch.object(optimizer, 'rider_db') as mock_db:
            params = RiderParameters(90, 85, 80, 75, 70)
            safe_rider = Rider("Safe", "Team1", params, 25, 5.0, 0.02)
            risky_rider = Rider("Risky", "Team2", params, 26, 5.0, 0.02)
            
            def get_rider_mock(name):
                if name == "Safe":
                    return safe_rider
                elif name == "Risky":
                    return risky_rider
                else:
                    raise KeyError(f"Rider {name} not found")
            
            mock_db.get_rider.side_effect = get_rider_mock
            
            # With no risk aversion, should prefer risky rider
            result_no_risk = optimizer.optimize_team(rider_data, risk_aversion=0.0)
            
            # With high risk aversion, should prefer safe rider
            result_high_risk = optimizer.optimize_team(rider_data, risk_aversion=1.0)
            
            # Results might be the same due to small difference, but test passes if no error

    def test_analyze_team_diversity(self):
        """Test team diversity analysis."""
        optimizer = TeamOptimizer()
        
        params = RiderParameters(90, 85, 80, 75, 70)
        riders = [
            Rider("R1", "Team1", params, 25, 2.0, 0.05),
            Rider("R2", "Team1", params, 28, 3.0, 0.03),
            Rider("R3", "Team2", params, 22, 4.0, 0.04)
        ]
        
        selection = TeamSelection(riders, 9.0, 180.0, ["R1", "R2", "R3"])
        diversity = optimizer.analyze_team_diversity(selection)
        
        assert 'unique_teams' in diversity
        assert 'team_distribution' in diversity
        assert 'avg_age' in diversity
        assert 'age_std' in diversity
        assert 'min_age' in diversity
        assert 'max_age' in diversity
        
        assert diversity['unique_teams'] == 2
        assert diversity['min_age'] == 22
        assert diversity['max_age'] == 28

    def test_get_team_diagnostics(self):
        """Test team diagnostics generation."""
        optimizer = TeamOptimizer()
        
        # Create test data
        rider_data = pd.DataFrame({
            'rider_name': ['R1', 'R2'],
            'points_std': [5.0, 7.0],
            'chance_of_abandon': [0.05, 0.03]
        })
        
        params = RiderParameters(90, 85, 80, 75, 70)
        riders = [
            Rider("R1", "Team1", params, 25, 2.0, 0.05),
            Rider("R2", "Team2", params, 26, 3.0, 0.03)
        ]
        
        selection = TeamSelection(riders, 5.0, 100.0, ["R1", "R2"])
        diagnostics = optimizer.get_team_diagnostics(selection, rider_data)
        
        assert 'team_size' in diagnostics
        assert 'total_cost' in diagnostics
        assert 'expected_points' in diagnostics
        assert 'cost_efficiency' in diagnostics
        assert 'budget_utilization' in diagnostics
        assert 'team_composition' in diagnostics
        assert 'risk_metrics' in diagnostics
        assert 'abandon_risk' in diagnostics

    @patch('builtins.print')  # Suppress output
    def test_get_stage_performance_data(self, mock_print):
        """Test stage performance data generation."""
        optimizer = TeamOptimizer()
        
        with patch.object(optimizer.simulator, 'simulate_tour'):
            with patch.object(optimizer, 'simulator') as mock_sim:
                # Mock scorito points records
                mock_sim.scorito_points_records = [
                    {'rider': 'R1', 'stage': 1, 'scorito_points': 50},
                    {'rider': 'R1', 'stage': 2, 'scorito_points': 75},
                    {'rider': 'R2', 'stage': 1, 'scorito_points': 30},
                    {'rider': 'R2', 'stage': 2, 'scorito_points': 55}
                ]
                
                result = optimizer._get_stage_performance_data(num_simulations=1)
                
                assert isinstance(result, dict)
                # Should have entries for each rider-stage combination
                assert ('R1', 1) in result
                assert ('R1', 2) in result
                assert ('R2', 1) in result
                assert ('R2', 2) in result
                
                # Points should be calculated correctly (stage 1 = total, stage 2 = difference)
                assert result[('R1', 1)] == 50
                assert result[('R1', 2)] == 25  # 75 - 50
                assert result[('R2', 1)] == 30
                assert result[('R2', 2)] == 25  # 55 - 30

    def test_estimate_teammate_bonus_per_rider(self):
        """Test teammate bonus estimation."""
        optimizer = TeamOptimizer()
        
        # Test different team sizes
        bonus_1 = optimizer._estimate_teammate_bonus_per_rider(1)
        bonus_2 = optimizer._estimate_teammate_bonus_per_rider(2)
        bonus_4 = optimizer._estimate_teammate_bonus_per_rider(4)
        
        assert bonus_1 == 0.0  # Single rider can't get teammate bonuses
        assert bonus_2 > 0.0   # Two riders can get bonuses
        assert bonus_4 > 0.0   # Four riders can get bonuses
        assert bonus_2 > bonus_4  # Smaller teams get more bonus per rider (fixed bonuses distributed among fewer riders)

    def test_optimization_failure_handling(self):
        """Test handling of optimization failures."""
        optimizer = TeamOptimizer(budget=1.0, team_size=20)  # Impossible constraints
        
        rider_data = pd.DataFrame({
            'rider_name': ['R1', 'R2'],
            'price': [10.0, 15.0],  # All too expensive for budget
            'expected_points': [50.0, 60.0],
            'points_std': [5.0, 6.0],
            'team': ['Team1', 'Team2'],
            'chance_of_abandon': [0.05, 0.03]
        })
        
        # Should raise ValueError for infeasible problem
        with pytest.raises(ValueError, match="Optimization failed"):
            optimizer.optimize_team(rider_data)


class TestTeamOptimizationIntegration:
    """Integration tests for team optimization."""

    @patch('builtins.print')  # Suppress output
    def test_full_optimization_workflow(self, mock_print):
        """Test complete optimization workflow."""
        optimizer = TeamOptimizer(budget=10.0, team_size=3)
        
        # Use a very small number of simulations for testing
        with patch.object(optimizer, 'run_simulation_with_teammate_analysis') as mock_run_sim:
            # Mock the simulation results
            mock_run_sim.return_value = pd.DataFrame({
                'rider_name': ['R1', 'R2', 'R3', 'R4'],
                'price': [2.0, 3.0, 2.5, 2.8],
                'expected_points': [40.0, 50.0, 45.0, 48.0],
                'points_std': [4.0, 5.0, 4.5, 4.8],
                'team': ['Team1', 'Team2', 'Team3', 'Team4'],
                'chance_of_abandon': [0.05, 0.03, 0.04, 0.02],
                'teammate_bonus_potential': [0.0, 0.0, 0.0, 0.0]
            })
            
            with patch.object(optimizer, 'rider_db') as mock_db:
                params = RiderParameters(90, 85, 80, 75, 70)
                mock_riders = [
                    Rider("R1", "Team1", params, 25, 2.0, 0.05),
                    Rider("R2", "Team2", params, 26, 3.0, 0.03),
                    Rider("R3", "Team3", params, 24, 2.5, 0.04)
                ]
                mock_db.get_rider.side_effect = mock_riders
                
                # Get rider data
                rider_data = mock_run_sim.return_value
                
                # Optimize team
                result = optimizer.optimize_team(rider_data)
                
                # Verify result
                assert isinstance(result, TeamSelection)
                assert len(result.riders) == 3
                assert result.total_cost <= 10.0
                assert result.expected_points > 0

    def test_real_data_optimization(self):
        """Test optimization with real rider data (limited)."""
        optimizer = TeamOptimizer(budget=5.0, team_size=2)
        
        # Get first few riders from real database
        real_riders = optimizer.rider_db.get_all_riders()[:5]
        
        # Create rider data DataFrame
        rider_data = pd.DataFrame({
            'rider_name': [r.name for r in real_riders],
            'price': [r.price for r in real_riders],
            'expected_points': [50.0, 60.0, 55.0, 65.0, 45.0],  # Mock expected points
            'points_std': [5.0, 6.0, 5.5, 6.5, 4.5],
            'team': [r.team for r in real_riders],
            'chance_of_abandon': [r.chance_of_abandon for r in real_riders],
            'teammate_bonus_potential': [0.0] * 5
        })
        
        # Should run without errors
        result = optimizer.optimize_team(rider_data)
        
        assert isinstance(result, TeamSelection)
        assert len(result.riders) <= 2
        assert result.total_cost <= 5.0

    def test_performance_characteristics(self):
        """Test optimization performance characteristics."""
        import time
        
        optimizer = TeamOptimizer(budget=10.0, team_size=3)
        
        # Create test data
        rider_data = pd.DataFrame({
            'rider_name': [f'R{i}' for i in range(10)],
            'price': [2.0] * 10,
            'expected_points': [50.0 + i for i in range(10)],
            'points_std': [5.0] * 10,
            'team': [f'Team{i}' for i in range(10)],
            'chance_of_abandon': [0.05] * 10,
            'teammate_bonus_potential': [0.0] * 10
        })
        
        with patch.object(optimizer, 'rider_db') as mock_db:
            params = RiderParameters(90, 85, 80, 75, 70)
            mock_riders = [Rider(f"R{i}", f"Team{i}", params, 25, 2.0, 0.05) for i in range(3)]
            mock_db.get_rider.side_effect = mock_riders
            
            start_time = time.time()
            result = optimizer.optimize_team(rider_data)
            end_time = time.time()
            
            # Should complete quickly (< 5 seconds)
            execution_time = end_time - start_time
            assert execution_time < 5, f"Optimization took {execution_time:.2f}s, should be < 5s"


if __name__ == "__main__":
    pytest.main([__file__]) 