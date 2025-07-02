import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from riders import RiderDatabase, Rider
from stage_profiles import get_stage_profile, StageType
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

# TNO-Ergame point system
TNO_POINTS_REGULAR = {
    1: 20, 2: 15, 3: 12, 4: 9, 5: 7, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1
}

TNO_POINTS_SPECIAL = {
    1: 30, 2: 20, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

# Special stages (5, 13, 14, 17, 18)
TNO_SPECIAL_STAGES = {5, 13, 14, 17, 18}

# Bonus points for top 5 riders in the list when they finish top 10
TNO_BONUS_POINTS = {1: 5, 2: 4, 3: 3, 4: 2, 5: 1}

# Time gaps per place for each stage type (in seconds) - same as main simulator
STAGE_TIME_GAPS = {
    "sprint": 0.1,
    "punch": 0.2,
    "break_away": 1,
    "mountain": 20,
    "itt": 5
}

@dataclass
class TNOStageResult:
    def __init__(self, rider: Rider, position: float):
        self.rider = rider
        self.position = position
        self.tno_points = 0  # Will be calculated later

class TNOStage:
    def __init__(self, stage_number: int):
        self.stage_number = stage_number
        self.results: List[TNOStageResult] = []
        self.is_special = stage_number in TNO_SPECIAL_STAGES

    def simulate(self, rider_db: RiderDatabase, abandoned_riders: set, team_riders: List[Rider] = None):
        """Simulate stage using the same realistic engine as main simulator"""
        # If team_riders is provided, only simulate those riders
        # Otherwise, simulate all riders (for compatibility)
        riders_to_simulate = team_riders if team_riders is not None else rider_db.get_all_riders()
        
        for rider in riders_to_simulate:
            # Skip riders who have already abandoned
            if rider.name in abandoned_riders:
                continue
            # Use the same realistic position generation as main simulator
            position = rider_db.generate_stage_result(rider, self.stage_number)
            self.results.append(TNOStageResult(rider, position))
        self.results.sort(key=lambda x: x.position)

class TNOTeamSelection:
    """Represents a TNO-Ergame team selection with rider order"""
    def __init__(self, riders: List[Rider]):
        self.riders = riders  # Ordered list of 20 riders
        self.total_cost = sum(rider.price for rider in riders)
        self.rider_names = [rider.name for rider in riders]
        
        # Track which riders are scoring riders (first 15) vs reserves (last 5)
        self.scoring_riders = riders[:15]
        self.reserve_riders = riders[15:]
        
        # Track bonus positions (first 5 riders)
        self.bonus_riders = riders[:5]
        
        # Track abandonments and replacements
        self.abandoned_riders = set()
        self.replacement_history = []  # Track when riders are replaced

    def get_scoring_riders_for_stage(self, stage_number: int) -> Tuple[List[Rider], List[Rider]]:
        """Get the current scoring riders and bonus riders for a specific stage, considering abandonments"""
        current_scoring = []
        current_bonus = []
        
        # Start with original order
        for i, rider in enumerate(self.riders):
            if rider.name not in self.abandoned_riders:
                if len(current_scoring) < 15:
                    current_scoring.append(rider)
                if len(current_bonus) < 5:
                    current_bonus.append(rider)
        
        return current_scoring, current_bonus

    def handle_abandonment(self, rider_name: str, stage_number: int):
        """Handle rider abandonment and update team structure"""
        if rider_name in self.abandoned_riders:
            return  # Already abandoned
        
        self.abandoned_riders.add(rider_name)
        
        # Find the rider's original position
        original_position = None
        for i, rider in enumerate(self.riders):
            if rider.name == rider_name:
                original_position = i + 1  # 1-indexed
                break
        
        if original_position is None:
            return
        
        # Record the replacement
        self.replacement_history.append({
            'stage': stage_number,
            'abandoned_rider': rider_name,
            'original_position': original_position
        })

class TNOSimulator:
    def __init__(self, team_selection: TNOTeamSelection):
        self.team_selection = team_selection
        self.stages: List[TNOStage] = []
        self.gc_times: Dict[str, float] = defaultdict(float)  # seconds
        self.tno_points: Dict[str, int] = defaultdict(int)  # TNO points per rider
        self._initialize_stages()
        
        # Use the same rider database instance to ensure consistency
        self.rider_db = RiderDatabase()
        
        # Track abandoned riders
        self.abandoned_riders = set()
        
        # Immediately abandon riders with 100% abandon chance
        for rider in self.rider_db.get_all_riders():
            if getattr(rider, 'chance_of_abandon', 0.0) >= 1.0:
                self.abandoned_riders.add(rider.name)
        
        # For DataFrame collection
        self.stage_results_records = []
        self.gc_records = []
        self.tno_points_records = []
        
        # Collect rider database information
        self.rider_db_records = []
        for rider in self.rider_db.get_all_riders():
            self.rider_db_records.append({
                "name": rider.name,
                "team": rider.team,
                "age": rider.age,
                "sprint_ability": rider.parameters.sprint_ability,
                "punch_ability": rider.parameters.punch_ability,
                "itt_ability": rider.parameters.itt_ability,
                "mountain_ability": rider.parameters.mountain_ability,
                "break_away_ability": rider.parameters.break_away_ability,
                "price": rider.price,
                "chance_of_abandon": rider.chance_of_abandon
            })

    def _initialize_stages(self):
        for i in range(21):  # Only 21 stages for TNO-Ergame
            self.stages.append(TNOStage(i + 1))

    def calculate_tno_points(self, stage: TNOStage, scoring_riders: List[Rider], bonus_riders: List[Rider]) -> Dict[str, int]:
        """Calculate TNO points for the stage based on realistic positions"""
        stage_points = defaultdict(int)
        
        # Get point system for this stage
        points_system = TNO_POINTS_SPECIAL if stage.is_special else TNO_POINTS_REGULAR
        
        # Calculate points for each rider based on their stage result
        for place, result in enumerate(stage.results, 1):
            rider_name = result.rider.name
            
            # Only award points if rider is in scoring riders
            if any(r.name == rider_name for r in scoring_riders):
                # Award points based on position
                if place in points_system:
                    stage_points[rider_name] += points_system[place]
                
                # Award bonus points if rider is in bonus positions and finished top 10
                if place <= 10:
                    for bonus_pos, bonus_rider in enumerate(bonus_riders, 1):
                        if bonus_rider.name == rider_name:
                            stage_points[rider_name] += TNO_BONUS_POINTS[bonus_pos]
                            break
        
        return stage_points

    def simulate_tour(self):
        for stage_idx, stage in enumerate(self.stages):
            # Simulate stage using realistic engine - only simulate team riders
            stage.simulate(self.rider_db, self.abandoned_riders, self.team_selection.riders)
            stage_profile = get_stage_profile(stage_idx + 1)
            
            # Calculate weighted time gap based on stage profile (same as main simulator)
            weighted_time_gap = 0.0
            for stage_type, weight in stage_profile.items():
                weighted_time_gap += STAGE_TIME_GAPS[stage_type.value] * weight

            # --- Handle Crashes/Abandonments ---
            # Only check team riders for abandonments since we're only simulating team riders
            for rider in self.team_selection.riders:
                if rider.name not in self.abandoned_riders:
                    # Calculate crash probability for this stage (same as main simulator)
                    if rider.chance_of_abandon == 0.0:
                        crash_probability = 0.0
                    else:
                        crash_probability = 1 - ((1 - rider.chance_of_abandon) ** (1/21))
                    
                    if np.random.random() < crash_probability:
                        self.abandoned_riders.add(rider.name)
                        self.team_selection.handle_abandonment(rider.name, stage_idx + 1)

            # --- General Classification (GC) ---
            base_time = 0
            time_gap = weighted_time_gap
            for place, result in enumerate(stage.results):
                rider_name = result.rider.name
                # Winner gets base_time, others get +gap per place
                self.gc_times[rider_name] += base_time + time_gap * place

            # --- TNO Points Calculation ---
            # Get current scoring and bonus riders for this stage
            scoring_riders, bonus_riders = self.team_selection.get_scoring_riders_for_stage(stage_idx + 1)
            
            # Calculate TNO points for this stage
            stage_tno_points = self.calculate_tno_points(stage, scoring_riders, bonus_riders)
            
            # Add to total TNO points
            for rider_name, points in stage_tno_points.items():
                self.tno_points[rider_name] += points

            # Record stage results
            for place, result in enumerate(stage.results, 1):
                rider_name = result.rider.name
                rider = result.rider
                
                # Record stage result
                self.stage_results_records.append({
                    'stage': stage_idx + 1,
                    'rider': rider_name,
                    'team': rider.team,
                    'position': place,
                    'gc_time': self.gc_times[rider_name],
                    'tno_points': stage_tno_points.get(rider_name, 0),
                    'is_scoring_rider': any(r.name == rider_name for r in scoring_riders),
                    'is_bonus_rider': any(r.name == rider_name for r in bonus_riders),
                    'abandoned': False
                })
            
            # Add abandoned riders to stage results with DNF
            for rider_name in self.abandoned_riders:
                # Find the rider object
                rider_obj = None
                for rider in self.rider_db.get_all_riders():
                    if rider.name == rider_name:
                        rider_obj = rider
                        break
                if rider_obj:
                    self.stage_results_records.append({
                        'stage': stage_idx + 1,
                        'rider': rider_name,
                        'team': rider_obj.team,
                        'position': None,  # DNF
                        'gc_time': self.gc_times.get(rider_name, 0),
                        'tno_points': 0,
                        'is_scoring_rider': False,
                        'is_bonus_rider': False,
                        'abandoned': True
                    })
            
            # GC standings
            for name, t in self.gc_times.items():
                self.gc_records.append({
                    'stage': stage_idx + 1,
                    'rider': name,
                    'gc_time': t
                })
            
            # TNO points standings
            for name, pts in self.tno_points.items():
                self.tno_points_records.append({
                    'stage': stage_idx + 1,
                    'rider': name,
                    'tno_points': pts
                })

    def get_final_gc(self):
        """Get final GC standings"""
        return sorted(self.gc_times.items(), key=lambda x: x[1])

    def get_final_tno_points(self):
        """Get final TNO points standings"""
        return sorted(self.tno_points.items(), key=lambda x: x[1], reverse=True)

    def get_team_performance(self) -> Dict:
        """Get team performance summary"""
        # Calculate total TNO points for team riders
        team_tno_points = 0
        team_abandonments = 0
        
        for rider in self.team_selection.riders:
            if rider.name in self.abandoned_riders:
                team_abandonments += 1
            else:
                team_tno_points += self.tno_points.get(rider.name, 0)
        
        return {
            'total_points': team_tno_points,
            'abandonments': team_abandonments,
            'team_cost': self.team_selection.total_cost,
            'scoring_riders': len([r for r in self.team_selection.scoring_riders if r.name not in self.abandoned_riders]),
            'bonus_riders': len([r for r in self.team_selection.bonus_riders if r.name not in self.abandoned_riders])
        }

    def write_results_to_excel(self, filename="tno_ergame_simulation_results.xlsx"):
        """Write simulation results to Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Stage results
            stage_results_df = pd.DataFrame(self.stage_results_records)
            stage_results_df.to_excel(writer, sheet_name='Stage_Results', index=False)
            
            # GC standings
            gc_df = pd.DataFrame(self.gc_records)
            gc_df.to_excel(writer, sheet_name='GC_Standings', index=False)
            
            # TNO points standings
            tno_points_df = pd.DataFrame(self.tno_points_records)
            tno_points_df.to_excel(writer, sheet_name='TNO_Points', index=False)
            
            # Team performance
            team_perf = self.get_team_performance()
            team_df = pd.DataFrame([team_perf])
            team_df.to_excel(writer, sheet_name='Team_Performance', index=False)
            
            # Rider database
            rider_db_df = pd.DataFrame(self.rider_db_records)
            rider_db_df.to_excel(writer, sheet_name='Rider_Database', index=False)

def main():
    """Example usage of TNO-Ergame simulator"""
    # Create a sample team selection
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
    simulator.write_results_to_excel()

if __name__ == "__main__":
    main() 