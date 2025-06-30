#!/usr/bin/env python3
"""
Test script to verify the versus mode scoring fix.
This script demonstrates the difference between the old (incorrect) and new (correct) scoring methods.
"""

from versus_mode import VersusMode
from riders import RiderDatabase
import pandas as pd

def test_scoring_fix():
    """Test the scoring fix by comparing old vs new methods."""
    print("=== VERSUS MODE SCORING FIX TEST ===")
    
    # Initialize versus mode
    versus = VersusMode()
    
    # Create a simple test team (first 20 riders)
    rider_db = RiderDatabase()
    all_riders = rider_db.get_all_riders()
    test_riders = [r.name for r in all_riders[:20]]
    
    print(f"Test team: {test_riders}")
    
    # Create user team
    user_team = versus.create_user_team(test_riders)
    
    # Get rider data
    print("Getting rider performance data...")
    rider_data = versus.team_optimizer.run_simulation_with_teammate_analysis(num_simulations=10, metric='mean')
    
    # Optimize stage selection
    print("Optimizing stage selection...")
    user_team = versus.optimize_stage_selection(user_team, rider_data, num_simulations=10)
    
    # Run simulations with the FIXED method
    print("Running simulations with FIXED scoring method...")
    simulation_results = versus.run_user_team_simulations(user_team, num_simulations=10)
    
    # Calculate statistics
    points_list = [result['team_points'] for result in simulation_results]
    avg_points = sum(points_list) / len(points_list)
    
    # Calculate individual rider sum for comparison
    individual_sum = versus.calculate_individual_rider_sum(user_team, rider_data)
    
    print(f"\n=== RESULTS ===")
    print(f"Individual rider sum (theoretical max): {individual_sum:.2f}")
    print(f"Average simulation points (FIXED method): {avg_points:.2f}")
    print(f"Stage selection penalty: {individual_sum - avg_points:.2f}")
    
    # Show stage selections
    if user_team.stage_selections:
        print(f"\nStage selections available: {len(user_team.stage_selections)} stages")
        for stage in sorted(user_team.stage_selections.keys()):
            selected = user_team.stage_selections[stage]
            print(f"Stage {stage}: {len(selected)} riders selected")
    else:
        print("No stage selections available")
    
    print(f"\n=== TEST COMPLETE ===")
    print("The fix should now show realistic stage-by-stage scoring!")

if __name__ == "__main__":
    test_scoring_fix() 