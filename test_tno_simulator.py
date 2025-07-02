#!/usr/bin/env python3
"""
Test TNOSimulator to verify it's working correctly.
"""

import warnings
warnings.filterwarnings('ignore')

def test_tno_simulator():
    """Test TNOSimulator with different team selections."""
    print("🔍 Testing TNOSimulator...")
    print("=" * 50)
    
    try:
        from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
        from riders import RiderDatabase
        
        print("✅ TNOSimulator imported successfully")
        
        # Get all riders
        rider_db = RiderDatabase()
        all_riders = rider_db.get_all_riders()
        
        print(f"Total riders available: {len(all_riders)}")
        
        # Test 1: Simple team with first 20 riders
        print("\n🧪 Test 1: Simple team (first 20 riders)")
        simple_team = TNOTeamSelection(all_riders[:20])
        
        total_points = 0
        for i in range(10):
            simulator = TNOSimulator(simple_team)
            simulator.simulate_tour()
            points = sum(simulator.tno_points.values())
            total_points += points
            print(f"  Simulation {i+1}: {points:.1f} points")
        
        avg_points = total_points / 10
        print(f"  Average points: {avg_points:.1f}")
        
        # Test 2: Team with top riders by price
        print("\n🧪 Test 2: Team with top riders by price")
        sorted_riders = sorted(all_riders, key=lambda r: r.price, reverse=True)
        price_team = TNOTeamSelection(sorted_riders[:20])
        
        total_points = 0
        for i in range(10):
            simulator = TNOSimulator(price_team)
            simulator.simulate_tour()
            points = sum(simulator.tno_points.values())
            total_points += points
            print(f"  Simulation {i+1}: {points:.1f} points")
        
        avg_points = total_points / 10
        print(f"  Average points: {avg_points:.1f}")
        
        # Test 3: Check if TNOSimulator is awarding points correctly
        print("\n🧪 Test 3: Check point distribution")
        simulator = TNOSimulator(simple_team)
        simulator.simulate_tour()
        
        # Get top 10 point scorers
        top_scorers = sorted(simulator.tno_points.items(), key=lambda x: x[1], reverse=True)[:10]
        print("  Top 10 point scorers:")
        for rider_name, points in top_scorers:
            print(f"    {rider_name}: {points} points")
        
        # Check team structure
        print(f"\n🏗️ Team Structure Analysis:")
        print(f"  Scoring riders (first 15): {len(simple_team.scoring_riders)}")
        print(f"  Bonus riders (first 5): {len(simple_team.bonus_riders)}")
        print(f"  Reserve riders (last 5): {len(simple_team.reserve_riders)}")
        
        # Check if bonus riders are getting bonus points
        bonus_points = 0
        for rider_name, points in simulator.tno_points.items():
            if any(r.name == rider_name for r in simple_team.bonus_riders):
                bonus_points += points
        
        print(f"  Total points from bonus riders: {bonus_points}")
        print(f"  Total team points: {sum(simulator.tno_points.values())}")
        
        print("\n🎯 TNOSimulator test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tno_simulator() 