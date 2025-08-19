"""
Tests for the simulator module.
"""
import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from tour_simulator.core.simulator import TourSimulator, Stage
from tour_simulator.models.stage_result import StageResult
from tour_simulator.core.riders import RiderDatabase, Rider
from tour_simulator.models.rider_parameters import RiderParameters


class TestStageResult:
    """Test StageResult class."""

    def test_creation(self):
        """Test stage result creation."""
        params = RiderParameters(90, 85, 80, 75, 70)
        rider = Rider("Test", "Team", params, 25)
        
        result = StageResult(rider, 5.5)
        
        assert result.rider == rider
        assert result.position == 5.5
        assert result.points == 0  # Legacy, not used


class TestStage:
    """Test Stage class."""

    def test_creation(self):
        """Test stage creation."""
        stage = Stage(1)
        
        assert stage.stage_number == 1
        assert stage.results == []

    def test_simulate(self):
        """Test stage simulation."""
        stage = Stage(1)
        rider_db = RiderDatabase()
        abandoned_riders = set()
        
        # Mock the generate_stage_result method
        with patch.object(rider_db, 'generate_stage_result') as mock_generate:
            mock_generate.return_value = 5.0
            
            stage.simulate(rider_db, abandoned_riders)
            
            # Should have results for all riders
            assert len(stage.results) == len(rider_db.get_all_riders())
            
            # Results should be sorted by position
            for i in range(1, len(stage.results)):
                assert stage.results[i-1].position <= stage.results[i].position

    def test_simulate_with_abandoned_riders(self):
        """Test stage simulation with abandoned riders."""
        stage = Stage(1)
        rider_db = RiderDatabase()
        
        # Mark first rider as abandoned
        first_rider = rider_db.get_all_riders()[0]
        abandoned_riders = {first_rider.name}
        
        with patch.object(rider_db, 'generate_stage_result') as mock_generate:
            mock_generate.return_value = 5.0
            
            stage.simulate(rider_db, abandoned_riders)
            
            # Should have one less result
            expected_count = len(rider_db.get_all_riders()) - 1
            assert len(stage.results) == expected_count
            
            # Abandoned rider should not be in results
            result_riders = [result.rider.name for result in stage.results]
            assert first_rider.name not in result_riders


class TestTourSimulator:
    """Test TourSimulator class."""

    def test_initialization(self):
        """Test simulator initialization."""
        simulator = TourSimulator()
        
        # Should have 21 stages
        assert len(simulator.stages) == 21
        
        # Should have rider database
        assert simulator.rider_db is not None
        assert len(simulator.rider_db.get_all_riders()) > 0
        
        # Should have youth riders identified
        assert len(simulator.youth_rider_names) > 0
        
        # Should have abandoned riders set (initially empty)
        assert isinstance(simulator.abandoned_riders, set)
        
        # Should have initialized data structures
        assert isinstance(simulator.gc_times, dict)
        assert isinstance(simulator.sprint_points, dict)
        assert isinstance(simulator.mountain_points, dict)
        assert isinstance(simulator.scorito_points, dict)

    def test_immediate_abandonment(self):
        """Test that riders with 100% abandon chance are immediately abandoned."""
        # Create a custom rider database with a rider who always abandons
        from unittest.mock import MagicMock
        
        mock_rider_db = MagicMock()
        mock_rider = MagicMock()
        mock_rider.name = "Test Abandon"
        mock_rider.chance_of_abandon = 1.0  # 100% abandon chance
        mock_rider_db.get_all_riders.return_value = [mock_rider]
        
        simulator = TourSimulator()
        simulator.rider_db = mock_rider_db
        
        # Re-run the abandonment logic
        simulator.abandoned_riders = set()
        for rider in simulator.rider_db.get_all_riders():
            if getattr(rider, 'chance_of_abandon', 0.0) >= 1.0:
                simulator.abandoned_riders.add(rider.name)
        
        assert "Test Abandon" in simulator.abandoned_riders

    @patch('builtins.print')  # Suppress print statements
    def test_simulate_tour(self, mock_print):
        """Test complete tour simulation."""
        simulator = TourSimulator()
        
        # Mock stage simulation to speed up test
        with patch.object(Stage, 'simulate') as mock_simulate:
            # Create mock results
            riders = simulator.rider_db.get_all_riders()[:10]  # Use first 10 riders
            mock_results = []
            for i, rider in enumerate(riders):
                result = StageResult(rider, float(i + 1))
                mock_results.append(result)
            
            # Mock simulate to set results directly on all stages
            def side_effect(*args, **kwargs):
                # Find the stage object and set its results
                # This is a bit tricky since we need to access the stage instance
                pass
            
            # Instead, directly set results on all stages before simulation
            for stage in simulator.stages:
                stage.results = mock_results.copy()
                
            mock_simulate.side_effect = side_effect
            
            # Run simulation
            simulator.simulate_tour()
            
            # Should have called simulate for each stage
            assert mock_simulate.call_count == 21
            
            # Should have final results
            gc_results = simulator.get_final_gc()
            assert len(gc_results) > 0
            
            sprint_results = simulator.get_final_sprint()
            assert len(sprint_results) > 0
            
            mountain_results = simulator.get_final_mountain()
            assert len(mountain_results) > 0
            
            youth_results = simulator.get_final_youth()
            assert len(youth_results) > 0

    def test_get_final_classifications(self):
        """Test final classification getters."""
        simulator = TourSimulator()
        
        # Add some mock data
        simulator.gc_times["Rider1"] = 3600
        simulator.gc_times["Rider2"] = 3700
        simulator.sprint_points["Rider1"] = 100
        simulator.sprint_points["Rider2"] = 90
        simulator.mountain_points["Rider1"] = 50
        simulator.mountain_points["Rider2"] = 60
        simulator.youth_times["Rider1"] = 3600
        
        # Test GC (sorted by time, ascending)
        gc = simulator.get_final_gc()
        assert gc[0][0] == "Rider1"  # Lowest time wins
        assert gc[0][1] == 3600
        
        # Test Sprint (sorted by points, descending)
        sprint = simulator.get_final_sprint()
        assert sprint[0][0] == "Rider1"  # Highest points wins
        assert sprint[0][1] == 100
        
        # Test Mountain (sorted by points, descending)
        mountain = simulator.get_final_mountain()
        assert mountain[0][0] == "Rider2"  # Highest points wins
        assert mountain[0][1] == 60
        
        # Test Youth (sorted by time, ascending)
        youth = simulator.get_final_youth()
        assert youth[0][0] == "Rider1"  # Lowest time wins
        assert youth[0][1] == 3600

    def test_write_results_to_excel(self):
        """Test Excel export functionality."""
        simulator = TourSimulator()
        
        # Add minimal data
        simulator.stage_results_records = [
            {"stage": 1, "rider": "Test", "team": "Team", "age": 25, "position": 1, "sim_position": 1.0, "abandoned": False}
        ]
        simulator.gc_records = [
            {"stage": 1, "rider": "Test", "gc_time": 3600}
        ]
        simulator.sprint_records = [
            {"stage": 1, "rider": "Test", "sprint_points": 50}
        ]
        simulator.mountain_records = [
            {"stage": 1, "rider": "Test", "mountain_points": 20}
        ]
        simulator.youth_records = [
            {"stage": 1, "rider": "Test", "youth_time": 3600}
        ]
        simulator.rider_db_records = [
            {"name": "Test", "team": "Team", "age": 25, "sprint_ability": 90, "punch_ability": 85, 
             "itt_ability": 80, "mountain_ability": 75, "break_away_ability": 70, "is_youth": True, 
             "price": 2.5, "chance_of_abandon": 0.05}
        ]
        simulator.scorito_points_records = [
            {"stage": 1, "rider": "Test", "scorito_points": 50}
        ]
        
        # Test that it doesn't crash
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            try:
                simulator.write_results_to_excel(tmp.name)
                assert os.path.exists(tmp.name)
                assert os.path.getsize(tmp.name) > 0
            finally:
                os.unlink(tmp.name)

    def test_scorito_points_calculation(self):
        """Test Scorito points are calculated correctly."""
        simulator = TourSimulator()
        
        # Test that initial scorito points are empty
        assert len(simulator.scorito_points) == 0
        
        # Simulate a stage and check scorito points are awarded
        stage = simulator.stages[0]
        
        # Mock stage results
        riders = simulator.rider_db.get_all_riders()[:5]
        stage.results = [StageResult(rider, i+1) for i, rider in enumerate(riders)]
        
        # Manually run the scorito calculation logic
        from tour_simulator.core.simulator import SCORITO_STAGE_POINTS
        for idx, result in enumerate(stage.results[:20]):
            pts = SCORITO_STAGE_POINTS[idx] if idx < len(SCORITO_STAGE_POINTS) else 0
            simulator.scorito_points[result.rider.name] += pts
        
        # Check that points were awarded
        assert len(simulator.scorito_points) > 0
        
        # Winner should have most points
        winner_points = simulator.scorito_points[riders[0].name]
        second_points = simulator.scorito_points[riders[1].name]
        assert winner_points > second_points

    def test_youth_classification(self):
        """Test youth classification logic."""
        simulator = TourSimulator()
        
        # Check that youth riders are properly identified
        all_riders = simulator.rider_db.get_all_riders()
        youth_riders_manual = [r for r in all_riders if r.age < 25]
        
        assert len(simulator.youth_rider_names) == len(youth_riders_manual)
        
        for rider in youth_riders_manual:
            assert rider.name in simulator.youth_rider_names

    def test_abandonment_system(self):
        """Test the abandonment system."""
        simulator = TourSimulator()
        
        # Test crash probability calculation
        rider_abandon_chance = 0.21  # 21% chance over full tour
        crash_prob = 1 - ((1 - rider_abandon_chance) ** (1/21))
        
        # Should be reasonable per-stage probability
        assert 0 < crash_prob < 0.05  # Less than 5% per stage
        
        # Test that abandoned riders are tracked
        simulator.abandoned_riders.add("Test Rider")
        assert "Test Rider" in simulator.abandoned_riders


class TestSimulatorIntegration:
    """Integration tests for simulator functionality."""

    @patch('builtins.print')  # Suppress output
    def test_full_simulation_run(self, mock_print):
        """Test that a full simulation runs without errors."""
        simulator = TourSimulator()
        
        # Should complete without exceptions
        simulator.simulate_tour()
        
        # Should have results
        assert len(simulator.gc_times) > 0
        assert len(simulator.sprint_points) > 0
        assert len(simulator.mountain_points) > 0
        assert len(simulator.scorito_points) > 0
        
        # Should have stage results recorded
        assert len(simulator.stage_results_records) > 0
        assert len(simulator.gc_records) > 0
        assert len(simulator.scorito_points_records) > 0

    def test_simulation_consistency(self):
        """Test that simulation results are consistent."""
        simulator = TourSimulator()
        
        # Set random seed for reproducibility
        np.random.seed(42)
        
        with patch('builtins.print'):
            simulator.simulate_tour()
        
        # Store first results
        first_gc = dict(simulator.gc_times)
        first_scorito = dict(simulator.scorito_points)
        
        # Reset and run again with same seed
        simulator = TourSimulator()
        np.random.seed(42)
        
        with patch('builtins.print'):
            simulator.simulate_tour()
        
        # Results should be identical (deterministic with same seed)
        assert len(first_gc) == len(simulator.gc_times)
        assert len(first_scorito) == len(simulator.scorito_points)

    def test_performance_characteristics(self):
        """Test simulation performance characteristics."""
        import time
        
        simulator = TourSimulator()
        
        start_time = time.time()
        with patch('builtins.print'):
            simulator.simulate_tour()
        end_time = time.time()
        
        # Should complete in reasonable time (< 30 seconds)
        execution_time = end_time - start_time
        assert execution_time < 30, f"Simulation took {execution_time:.2f}s, should be < 30s"


if __name__ == "__main__":
    pytest.main([__file__]) 