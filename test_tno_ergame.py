#!/usr/bin/env python3
"""
Test script for TNO-Ergame simulator and optimizer
"""

import time
from riders import RiderDatabase
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
from tno_ergame_multi_simulator import TNOMultiSimulationAnalyzer
from tno_optimizer import TNOTeamOptimizer

def test_basic_simulation():
    """Test basic TNO-Ergame simulation"""
    # Create a sample team
    rider_db = RiderDatabase()
    all_riders = rider_db.get_all_riders()
    
    # Create a sample team (first 20 riders)
    sample_team = TNOTeamSelection(all_riders[:20])
    
    # Create and run simulation
    simulator = TNOSimulator(sample_team)
    simulator.simulate_tour()
    
    # Get results
    final_gc = simulator.get_final_gc()
    final_tno_points = simulator.get_final_tno_points()
    team_performance = simulator.get_team_performance()
    
    # Save results
    simulator.write_results_to_excel("test_tno_simulation_results.xlsx")

def test_multi_simulation():
    """Test multi-simulation analysis"""
    # Create a sample team
    rider_db = RiderDatabase()
    all_riders = rider_db.get_all_riders()
    sample_team = TNOTeamSelection(all_riders[:20])
    
    # Run multi-simulation analysis
    analyzer = TNOMultiSimulationAnalyzer(20)  # 20 simulations for testing
    metrics = analyzer.run_simulations(sample_team)
    
    # Save metrics
    analyzer.save_metrics_to_json("test_tno_multi_simulation_metrics.json")

def test_optimizer():
    """Test the TNO-Ergame optimizer"""
    # Create optimizer
    optimizer = TNOTeamOptimizer(budget=48.0, team_size=20)
    
    # Get rider performance data (with fewer simulations for testing)
    rider_data = optimizer.run_simulation_for_riders(num_simulations=20)
    
    # Print top 20 riders by expected points
    print(f"\n=== Top 20 Riders by Expected Points ===")
    for i, (_, row) in enumerate(rider_data.head(20).iterrows(), 1):
        print(f"{i}. {row['rider_name']}: {row['expected_points']:.1f} points")
    
    # Optimize team
    optimization = optimizer.optimize_team_with_order(rider_data, num_simulations=20)
    
    # Print results
    print(f"\n=== Optimization Results ===")
    print(f"Expected Points: {optimization.expected_points:.1f}")
    print(f"Total Cost: {optimization.total_cost:.2f}")
    print(f"Team Size: {len(optimization.riders)}")
    
    print(f"\nRider Order (Top 10):")
    for i, rider_name in enumerate(optimization.rider_order[:10], 1):
        rider = next(r for r in optimization.riders if r.name == rider_name)
        bonus_info = f" (Bonus: {6-i}pts)" if i <= 5 else ""
        scoring_info = " [Scoring]" if i <= 15 else " [Reserve]"
        print(f"{i}. {rider_name}{bonus_info}{scoring_info}")
    
    # Save results
    optimizer.save_optimization_results(optimization, rider_data, "test_tno_optimization_results.xlsx")

def main():
    """Run all tests"""
    start_time = time.time()
    
    try:
        test_basic_simulation()
        test_multi_simulation()
        test_optimizer()
        
        end_time = time.time()
        print(f"\n=== All Tests Completed ===")
        print(f"Total time: {end_time - start_time:.2f} seconds")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 