#!/usr/bin/env python3
"""
Test script to compare original optimizer vs heuristic optimizer team point calculations.
"""

import warnings
warnings.filterwarnings('ignore')

def test_optimizer_comparison():
    """Compare original optimizer vs heuristic optimizer team calculations."""
    print("🔍 Comparing Original vs Heuristic Optimizer...")
    print("=" * 60)
    
    try:
        from tno_optimizer import TNOTeamOptimizer
        from tno_heuristic_optimizer import TNOHeuristicOptimizer
        
        print("✅ Both optimizers imported successfully")
        
        # Test with same number of simulations
        num_simulations = 50
        
        print(f"\n📊 Running optimizations with {num_simulations} simulations...")
        
        # Test original optimizer
        print("\n🔧 Testing Original Optimizer...")
        original_opt = TNOTeamOptimizer()
        
        # Run simulations for rider data
        print("Running simulations for rider data...")
        rider_data = original_opt.run_simulation_for_riders(num_simulations=num_simulations)
        
        # Run optimization
        print("Running team optimization...")
        original_result = original_opt.optimize_team_with_order(rider_data, num_simulations=num_simulations)
        
        print(f"Original Optimizer Result:")
        print(f"  Expected Points: {original_result.expected_points:.2f}")
        print(f"  Total Cost: {original_result.total_cost:.2f}")
        print(f"  Team Size: {len(original_result.riders)}")
        
        # Test heuristic optimizer
        print("\n🔧 Testing Heuristic Optimizer...")
        heuristic_opt = TNOHeuristicOptimizer()
        
        # Run heuristic optimization
        print("Running heuristic optimization...")
        heuristic_result = heuristic_opt.run_heuristic_optimization(num_simulations=num_simulations)
        
        print(f"Heuristic Optimizer Result:")
        print(f"  Expected Points: {heuristic_result.expected_points:.2f}")
        print(f"  Total Cost: {heuristic_result.total_cost:.2f}")
        print(f"  Team Size: {len(heuristic_result.riders)}")
        
        # Compare results
        print("\n📈 Comparison Analysis:")
        print("=" * 40)
        
        point_diff = heuristic_result.expected_points - original_result.expected_points
        point_ratio = heuristic_result.expected_points / original_result.expected_points if original_result.expected_points > 0 else 0
        
        print(f"Point Difference (Heuristic - Original): {point_diff:+.2f}")
        print(f"Point Ratio (Heuristic / Original): {point_ratio:.2f}")
        
        if abs(point_ratio - 1.0) < 0.2:
            print("✅ Point calculations are reasonably similar")
        elif point_ratio < 0.5:
            print("⚠️  Heuristic optimizer points are significantly lower")
        elif point_ratio > 2.0:
            print("⚠️  Heuristic optimizer points are significantly higher")
        else:
            print("ℹ️  Point calculations differ but within acceptable range")
        
        # Check if teams are similar
        original_riders = set(r.name for r in original_result.riders)
        heuristic_riders = set(r.name for r in heuristic_result.riders)
        common_riders = original_riders & heuristic_riders
        
        print(f"\nTeam Comparison:")
        print(f"  Original team riders: {len(original_riders)}")
        print(f"  Heuristic team riders: {len(heuristic_riders)}")
        print(f"  Common riders: {len(common_riders)}")
        print(f"  Similarity: {len(common_riders) / len(original_riders) * 100:.1f}%")
        
        if len(common_riders) / len(original_riders) > 0.7:
            print("✅ Teams are reasonably similar")
        else:
            print("⚠️  Teams are quite different")
        
        # Detailed analysis of rider ordering and bonus points
        print(f"\n🔍 Detailed Analysis:")
        print("=" * 30)
        
        print(f"Original Optimizer - First 5 riders (bonus positions):")
        for i, rider_name in enumerate(original_result.rider_order[:5]):
            print(f"  {i+1}. {rider_name}")
        
        print(f"\nHeuristic Optimizer - First 5 riders (bonus positions):")
        for i, rider_name in enumerate(heuristic_result.rider_order[:5]):
            print(f"  {i+1}. {rider_name}")
        
        # Check if the issue might be that heuristic optimizer is not properly calculating bonus points
        print(f"\n💡 Potential Issue Analysis:")
        print("The heuristic optimizer might be calculating points correctly, but the difference")
        print("could be due to:")
        print("1. Different team selection strategies")
        print("2. Different rider ordering affecting bonus points")
        print("3. Different simulation methodologies")
        
        # Test if using the same team would give similar results
        print(f"\n🧪 Testing with same team...")
        
        # Create a test using the original optimizer's team in the heuristic optimizer
        from tno_ergame_simulator import TNOTeamSelection, TNOSimulator
        
        # Use original optimizer's team selection
        original_team_selection = original_result.team_selection
        
        # Test heuristic optimizer's team calculation method on original team
        test_points = 0
        for _ in range(10):  # Quick test with fewer simulations
            tno_simulator = TNOSimulator(original_team_selection)
            tno_simulator.simulate_tour()
            test_points += sum(tno_simulator.tno_points.values())
        test_points /= 10
        
        print(f"Original team tested with TNOSimulator: {test_points:.2f} points")
        print(f"Original optimizer reported: {original_result.expected_points:.2f} points")
        
        if abs(test_points - original_result.expected_points) < 100:
            print("✅ TNOSimulator calculation is consistent")
        else:
            print("⚠️  TNOSimulator calculation differs significantly")
        
        print("\n🎯 Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimizer_comparison() 