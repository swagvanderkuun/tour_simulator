#!/usr/bin/env python3
"""
Test to check bonus points and bench rider replacement logic.
"""

import warnings
warnings.filterwarnings('ignore')

def test_bonus_points():
    """Test bonus points and bench rider replacement logic."""
    print("🔍 Testing Bonus Points and Bench Rider Logic")
    print("=" * 50)
    
    try:
        from tno_ergame_simulator import TNOSimulator, TNOTeamSelection, TNO_BONUS_POINTS
        from riders import RiderDatabase
        
        print("✅ TNOSimulator imported successfully")
        
        # Create a test team
        rider_db = RiderDatabase()
        all_riders = rider_db.get_all_riders()
        
        # Create a team with top riders
        test_team = TNOTeamSelection(all_riders[:20])
        
        print(f"Test team created with {len(test_team.riders)} riders")
        print(f"Scoring riders: {len(test_team.scoring_riders)}")
        print(f"Bonus riders: {len(test_team.bonus_riders)}")
        
        # Show bonus point system
        print(f"\n🏆 Bonus Point System:")
        for pos, points in TNO_BONUS_POINTS.items():
            print(f"  Position {pos}: {points} bonus points")
        
        # Run a single simulation to see what's happening
        print("\n🧪 Running single simulation...")
        simulator = TNOSimulator(test_team)
        simulator.simulate_tour()
        
        # Analyze results
        total_points = sum(simulator.tno_points.values())
        print(f"Total team points: {total_points}")
        
        # Check bonus points specifically
        print(f"\n🏆 Bonus Points Analysis:")
        bonus_points_total = 0
        for rider in test_team.bonus_riders:
            points = simulator.tno_points.get(rider.name, 0)
            bonus_points_total += points
            print(f"  {rider.name}: {points} points")
        print(f"Total bonus rider points: {bonus_points_total}")
        
        # Check scoring riders
        print(f"\n🎯 Scoring Riders Analysis:")
        scoring_points_total = 0
        for rider in test_team.scoring_riders:
            points = simulator.tno_points.get(rider.name, 0)
            scoring_points_total += points
            if points > 0:
                print(f"  {rider.name}: {points} points")
        print(f"Total scoring rider points: {scoring_points_total}")
        
        # Check bench riders (positions 16-20)
        print(f"\n🔄 Bench Riders Analysis:")
        bench_points_total = 0
        for i in range(15, 20):
            rider = test_team.riders[i]
            points = simulator.tno_points.get(rider.name, 0)
            bench_points_total += points
            if points > 0:
                print(f"  {rider.name} (position {i+1}): {points} points")
        print(f"Total bench rider points: {bench_points_total}")
        
        # Check stage-by-stage bonus points
        print(f"\n📈 Stage-by-stage bonus points:")
        stage_bonus = {}
        for record in simulator.stage_results_records:
            if record['is_bonus_rider'] and record['tno_points'] > 0:
                stage = record['stage']
                if stage not in stage_bonus:
                    stage_bonus[stage] = 0
                stage_bonus[stage] += record['tno_points']
        
        for stage in sorted(stage_bonus.keys()):
            print(f"  Stage {stage}: {stage_bonus[stage]} bonus points")
        
        # Check if abandonments are happening and bench riders are replacing
        print(f"\n💀 Abandonment Analysis:")
        abandoned_count = len(simulator.abandoned_riders)
        print(f"Total abandonments: {abandoned_count}")
        
        if abandoned_count > 0:
            print("Abandoned riders:")
            for rider_name in simulator.abandoned_riders:
                print(f"  {rider_name}")
        
        # Check replacement history
        if test_team.replacement_history:
            print("Replacement history:")
            for replacement in test_team.replacement_history:
                print(f"  Stage {replacement['stage']}: {replacement['abandoned_rider']} (position {replacement['original_position']})")
        
        # Calculate expected vs actual
        print(f"\n📊 Expected vs Actual Analysis:")
        
        # Expected calculation:
        # - 21 stages
        # - Each stage: ~10-15 points for regular stages, ~15-20 for special stages
        # - Bonus points: ~50-100 points total
        # - Total: ~1000-1500 points
        
        expected_min = 1000
        expected_max = 1500
        
        print(f"Expected range: {expected_min}-{expected_max} points")
        print(f"Actual points: {total_points}")
        
        if total_points < expected_min:
            print("⚠️  Score is too low - missing bonus points or bench rider replacements")
        elif total_points > expected_max:
            print("⚠️  Score is too high")
        else:
            print("✅ Score is in expected range")
        
        # Check if the issue is with bench riders not getting points
        print(f"\n🔍 Potential Issues:")
        if bench_points_total == 0:
            print("⚠️  Bench riders are not scoring any points")
            print("   This could be because they're not replacing abandoned riders properly")
        
        if bonus_points_total < 50:
            print("⚠️  Bonus points seem low")
            print("   This could be because bonus riders aren't finishing top 10 enough")
        
        print("\n🎯 Test completed!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bonus_points() 