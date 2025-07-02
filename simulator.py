import numpy as np
import pandas as pd
from typing import List, Dict
from riders import RiderDatabase, Rider
from stage_profiles import get_stage_type, StageType, get_stage_profile
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

# Points arrays for classifications
# New sprint classification categories
SPRINT_CATEGORY_1_POINTS = [75, 55, 45, 30, 20, 18, 16, 10, 8, 7, 6, 5, 4, 3, 2]
SPRINT_CATEGORY_2_POINTS = [30, 25, 22, 19, 17, 15, 13, 11, 9, 7, 6, 5, 3, 2]
SPRINT_CATEGORY_3_POINTS = [20, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
SPRINT_CATEGORY_4_POINTS = [20, 17, 15, 13, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

# Stage to sprint category mapping
SPRINT_CATEGORY_MAPPING = {
    1: 1,   # Stage 1: Category 1
    2: 2,   # Stage 2: Category 2
    3: 1,   # Stage 3: Category 1
    4: 2,   # Stage 4: Category 2
    5: 3,   # Stage 5: Category 3
    6: 2,   # Stage 6: Category 2
    7: 2,   # Stage 7: Category 2
    8: 1,   # Stage 8: Category 1
    9: 1,   # Stage 9: Category 1
    10: 3,  # Stage 10: Category 3
    11: 1,  # Stage 11: Category 1
    12: 3,  # Stage 12: Category 3
    13: 3,  # Stage 13: Category 3
    14: 3,  # Stage 14: Category 3
    15: 2,  # Stage 15: Category 2
    16: 3,  # Stage 16: Category 3
    17: 1,  # Stage 17: Category 1
    18: 3,  # Stage 18: Category 3
    19: 3,  # Stage 19: Category 3
    20: 2,  # Stage 20: Category 2
    21: 1   # Stage 21: Category 1
}

# Legacy points arrays (kept for mountain classification)
BREAK_AWAY_SPRINT_POINTS = [15, 10, 7, 6, 5, 4, 3, 2, 1, 0]
BREAK_AWAY_MOUNTAIN_POINTS = [20, 18, 16, 14, 12, 10, 8, 6, 4, 2]
MOUNTAIN_MOUNTAIN_POINTS = [50, 45, 40, 35, 30, 25, 20, 15, 10, 5]
PUNCH_SPRINT_POINTS = [30, 25, 20, 15, 12, 10, 8, 6, 4, 2]
PUNCH_MOUNTAIN_POINTS = [10, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Time gaps per place for each stage type (in seconds)
STAGE_TIME_GAPS = {
    "sprint": 0.1,
    "punch": 0.2,
    "break_away": 1,
    "mountain": 20,
    "itt": 5
}

# Youth age limit (example: 25)
YOUTH_AGE_LIMIT = 25

SCORITO_STAGE_POINTS = [50, 44, 40, 36, 32, 30, 28, 26, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]
SCORITO_STAGE_GC_POINTS = [10, 8, 6, 4, 2]
SCORITO_STAGE_SPRINT_POINTS = [8, 6, 4, 2, 1]
SCORITO_STAGE_MOUNTAIN_POINTS = [8, 6, 4, 2, 1]
SCORITO_STAGE_YOUTH_POINTS = [6, 4, 3, 2, 1]
# Final GC points for top 20 after last stage
SCORITO_FINAL_GC_POINTS = [100, 80, 60, 50, 40, 36, 32, 28, 24, 22, 20, 18, 16, 14, 12, 10, 8, 6, 4, 2]
SCORITO_FINAL_SPRINT_POINTS = [80, 60, 40, 30, 20, 10, 8, 6, 4, 2]
SCORITO_FINAL_MOUNTAIN_POINTS = [80, 60, 40, 30, 20, 10, 8, 6, 4, 2]
SCORITO_FINAL_YOUTH_POINTS = [60, 40, 30, 20, 10]

class StageResult:
    def __init__(self, rider: Rider, position: float):
        self.rider = rider
        self.position = position
        self.points = self._calculate_points(position)

    def _calculate_points(self, position: float) -> int:
        # This is not used for the new classification logic, but kept for compatibility
        return 0

class Stage:
    def __init__(self, stage_number: int):
        self.stage_number = stage_number
        self.results: List[StageResult] = []

    def simulate(self, rider_db: RiderDatabase, abandoned_riders: set):
        for rider in rider_db.get_all_riders():
            # Skip riders who have already abandoned
            if rider.name in abandoned_riders:
                continue
            position = rider_db.generate_stage_result(rider, self.stage_number)
            self.results.append(StageResult(rider, position))
        self.results.sort(key=lambda x: x.position)

class TourSimulator:
    def __init__(self):
        self.stages: List[Stage] = []
        self.gc_times: Dict[str, float] = defaultdict(float)  # seconds
        self.sprint_points: Dict[str, int] = defaultdict(int)
        self.mountain_points: Dict[str, int] = defaultdict(int)
        self.youth_times: Dict[str, float] = defaultdict(float)
        self._initialize_stages()
        # Create a new rider database instance
        self.rider_db = RiderDatabase()
        # Get youth riders once for the whole tour - properly filter by age
        self.youth_rider_names = set(r.name for r in self.rider_db.get_all_riders() if r.age < YOUTH_AGE_LIMIT)
        # Track abandoned riders
        self.abandoned_riders = set()
        # Immediately abandon riders with 100% abandon chance
        for rider in self.rider_db.get_all_riders():
            if getattr(rider, 'chance_of_abandon', 0.0) >= 1.0:
                self.abandoned_riders.add(rider.name)
        # For DataFrame collection
        self.stage_results_records = []
        self.gc_records = []
        self.sprint_records = []
        self.mountain_records = []
        self.youth_records = []
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
                "is_youth": rider.name in self.youth_rider_names,
                "price": rider.price,
                "chance_of_abandon": rider.chance_of_abandon
            })
        # Scorito points tracking
        self.scorito_points = defaultdict(int)  # total points per rider
        self.scorito_points_records = []  # per stage, for export

    def _initialize_stages(self):
        for i in range(21):
            self.stages.append(Stage(i))

    def simulate_tour(self):
        for stage_idx, stage in enumerate(self.stages):
            # Simulating stage silently (for dashboard use)
            stage.simulate(self.rider_db, self.abandoned_riders)  # Pass rider_db and abandoned_riders to stage simulation
            stage_profile = get_stage_profile(stage_idx+1)
            
            # Calculate weighted time gap based on stage profile
            weighted_time_gap = 0.0
            for stage_type, weight in stage_profile.items():
                weighted_time_gap += STAGE_TIME_GAPS[stage_type.value] * weight

            # --- Handle Crashes/Abandonments (except for stage 22) ---
            if stage_idx < 21:  # Stages 1-20 (0-indexed, so stages 1-21)
                for rider in self.rider_db.get_all_riders():
                    if rider.name not in self.abandoned_riders:
                        # Calculate crash probability for this stage
                        # Formula: (1 - chance_of_abandon ^ (1/21))
                        # Handle the case where chance_of_abandon is 0.0 (no chance of abandoning)
                        if rider.chance_of_abandon == 0.0:
                            crash_probability = 0.0
                        else:
                            crash_probability = 1 - ((1 - rider.chance_of_abandon) ** (1/21))
                        if np.random.random() < crash_probability:
                            self.abandoned_riders.add(rider.name)
                            # Rider crashed silently (for dashboard use)
            
            # Track abandoned riders silently (for dashboard use)

            # --- General Classification (GC) ---
            base_time = 0
            time_gap = weighted_time_gap
            for place, result in enumerate(stage.results):
                rider_name = result.rider.name
                # Winner gets base_time, others get +gap per place
                self.gc_times[rider_name] += base_time + time_gap * place
                # Youth GC - only track times for eligible riders
                if rider_name in self.youth_rider_names:
                    self.youth_times[rider_name] = self.gc_times[rider_name]  # Use same time as GC

            # --- Sprint Classification ---
            # Get sprint category for this stage
            stage_number = stage_idx + 1
            sprint_category = SPRINT_CATEGORY_MAPPING.get(stage_number, 3)  # Default to category 3
            
            # Select the appropriate points array based on category
            if sprint_category == 1:
                sprint_points_array = SPRINT_CATEGORY_1_POINTS
            elif sprint_category == 2:
                sprint_points_array = SPRINT_CATEGORY_2_POINTS
            elif sprint_category == 3:
                sprint_points_array = SPRINT_CATEGORY_3_POINTS
            else:  # category 4 (same as 3)
                sprint_points_array = SPRINT_CATEGORY_4_POINTS
            
            # Award sprint points based on stage finish position
            for idx, result in enumerate(stage.results[:len(sprint_points_array)]):
                self.sprint_points[result.rider.name] += sprint_points_array[idx]

            # --- Mountain Classification ---
            # Calculate weighted mountain points based on stage profile
            for stage_type, weight in stage_profile.items():
                if stage_type == StageType.MOUNTAIN:
                    for idx, result in enumerate(stage.results[:len(MOUNTAIN_MOUNTAIN_POINTS)]):
                        self.mountain_points[result.rider.name] += int(MOUNTAIN_MOUNTAIN_POINTS[idx] * weight)
                elif stage_type == StageType.BREAK_AWAY:
                    for idx, result in enumerate(stage.results[:len(BREAK_AWAY_MOUNTAIN_POINTS)]):
                        self.mountain_points[result.rider.name] += int(BREAK_AWAY_MOUNTAIN_POINTS[idx] * weight)
                elif stage_type == StageType.PUNCH:
                    for idx, result in enumerate(stage.results[:len(PUNCH_MOUNTAIN_POINTS)]):
                        self.mountain_points[result.rider.name] += int(PUNCH_MOUNTAIN_POINTS[idx] * weight)

            # --- Collect Data for DataFrames ---
            # Stage results
            for place, result in enumerate(stage.results, 1):
                self.stage_results_records.append({
                    "stage": stage_idx+1,
                    "rider": result.rider.name,
                    "team": result.rider.team,
                    "age": result.rider.age,
                    "position": place,
                    "sim_position": result.position,
                    "abandoned": False
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
                        "stage": stage_idx+1,
                        "rider": rider_name,
                        "team": rider_obj.team,
                        "age": rider_obj.age,
                        "position": None,  # DNF
                        "sim_position": None,  # DNF
                        "abandoned": True
                    })
            
            # GC standings
            for name, t in self.gc_times.items():
                self.gc_records.append({
                    "stage": stage_idx+1,
                    "rider": name,
                    "gc_time": t
                })
            # Sprint standings
            for name, pts in self.sprint_points.items():
                self.sprint_records.append({
                    "stage": stage_idx+1,
                    "rider": name,
                    "sprint_points": pts
                })
            # Mountain standings
            for name, pts in self.mountain_points.items():
                self.mountain_records.append({
                    "stage": stage_idx+1,
                    "rider": name,
                    "mountain_points": pts
                })
            # Youth GC standings
            for name, t in self.youth_times.items():
                self.youth_records.append({
                    "stage": stage_idx+1,
                    "rider": name,
                    "youth_time": t
                })

            # --- Scorito Points Calculation ---
            # Stage result points (top 20) - only for non-abandoned riders
            for idx, result in enumerate(stage.results[:20]):
                pts = SCORITO_STAGE_POINTS[idx]
                self.scorito_points[result.rider.name] += pts
            # GC classification points (top 5 after this stage) - only for non-abandoned riders
            gc_sorted = sorted([(name, time) for name, time in self.gc_times.items() if name not in self.abandoned_riders], key=lambda x: x[1])[:5]
            for idx, (name, _) in enumerate(gc_sorted):
                pts = SCORITO_STAGE_GC_POINTS[idx]
                self.scorito_points[name] += pts
            # Sprint classification points (top 5 after this stage) - only for non-abandoned riders
            sprint_sorted = sorted([(name, pts) for name, pts in self.sprint_points.items() if name not in self.abandoned_riders], key=lambda x: x[1], reverse=True)[:5]
            for idx, (name, _) in enumerate(sprint_sorted):
                pts = SCORITO_STAGE_SPRINT_POINTS[idx]
                self.scorito_points[name] += pts
            # Mountain classification points (top 5 after this stage) - only for non-abandoned riders
            mountain_sorted = sorted([(name, pts) for name, pts in self.mountain_points.items() if name not in self.abandoned_riders], key=lambda x: x[1], reverse=True)[:5]
            for idx, (name, _) in enumerate(mountain_sorted):
                pts = SCORITO_STAGE_MOUNTAIN_POINTS[idx]
                self.scorito_points[name] += pts
            # Youth classification points (top 5 after this stage) - only for non-abandoned riders
            youth_sorted = sorted([(name, time) for name, time in self.youth_times.items() if name not in self.abandoned_riders], key=lambda x: x[1])[:5]
            for idx, (name, _) in enumerate(youth_sorted):
                pts = SCORITO_STAGE_YOUTH_POINTS[idx]
                self.scorito_points[name] += pts

            # --- Teammate Bonus Points ---
            # Find winners (only among non-abandoned riders)
            stage_winner = stage.results[0].rider if stage.results else None
            gc_leader = gc_sorted[0][0] if gc_sorted else None
            sprint_leader = sprint_sorted[0][0] if sprint_sorted else None
            mountain_leader = mountain_sorted[0][0] if mountain_sorted else None
            youth_leader = youth_sorted[0][0] if youth_sorted else None
            # Map rider names to teams
            name_to_team = {r.name: r.team for r in self.rider_db.get_all_riders()}
            for rider in self.rider_db.get_all_riders():
                # Skip abandoned riders for teammate bonuses
                if rider.name in self.abandoned_riders:
                    continue
                # Stage winner teammate bonus
                if stage_winner and rider.name != stage_winner.name and name_to_team[rider.name] == stage_winner.team:
                    self.scorito_points[rider.name] += 10
                # GC leader teammate bonus
                if gc_leader and rider.name != gc_leader and name_to_team[rider.name] == name_to_team[gc_leader]:
                    self.scorito_points[rider.name] += 8
                # Sprint leader teammate bonus
                if sprint_leader and rider.name != sprint_leader and name_to_team[rider.name] == name_to_team[sprint_leader]:
                    self.scorito_points[rider.name] += 6
                # Mountain leader teammate bonus
                if mountain_leader and rider.name != mountain_leader and name_to_team[rider.name] == name_to_team[mountain_leader]:
                    self.scorito_points[rider.name] += 6
                # Youth leader teammate bonus
                if youth_leader and rider.name != youth_leader and name_to_team[rider.name] == name_to_team[youth_leader]:
                    self.scorito_points[rider.name] += 4

            # Record scorito points after this stage for export (only non-abandoned riders)
            for rider in self.rider_db.get_all_riders():
                if rider.name not in self.abandoned_riders:
                    self.scorito_points_records.append({
                        "stage": stage_idx+1,
                        "rider": rider.name,
                        "scorito_points": self.scorito_points[rider.name]
                    })

            # --- Track Standings after Stage (silent mode for dashboard) ---
            # All standings calculations remain the same, just not printed

        # After all stages, award final GC points (only for non-abandoned riders)
        final_gc = [(name, time) for name, time in self.get_final_gc() if name not in self.abandoned_riders]
        for idx, (name, _) in enumerate(final_gc[:len(SCORITO_FINAL_GC_POINTS)]):
            pts = SCORITO_FINAL_GC_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_gc[:len(SCORITO_FINAL_GC_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,  # Use 22 to indicate final GC points
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award final Sprint points (only for non-abandoned riders)
        final_sprint = [(name, pts) for name, pts in self.get_final_sprint() if name not in self.abandoned_riders]
        for idx, (name, _) in enumerate(final_sprint[:len(SCORITO_FINAL_SPRINT_POINTS)]):
            pts = SCORITO_FINAL_SPRINT_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_sprint[:len(SCORITO_FINAL_SPRINT_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award final Mountain points (only for non-abandoned riders)
        final_mountain = [(name, pts) for name, pts in self.get_final_mountain() if name not in self.abandoned_riders]
        for idx, (name, _) in enumerate(final_mountain[:len(SCORITO_FINAL_MOUNTAIN_POINTS)]):
            pts = SCORITO_FINAL_MOUNTAIN_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_mountain[:len(SCORITO_FINAL_MOUNTAIN_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award final Youth points (only for non-abandoned riders)
        final_youth = [(name, time) for name, time in self.get_final_youth() if name not in self.abandoned_riders]
        for idx, (name, _) in enumerate(final_youth[:len(SCORITO_FINAL_YOUTH_POINTS)]):
            pts = SCORITO_FINAL_YOUTH_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_youth[:len(SCORITO_FINAL_YOUTH_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award teammate bonus points for final classification winners (only non-abandoned riders)
        # Map rider names to teams
        name_to_team = {r.name: r.team for r in self.rider_db.get_all_riders()}
        # Get winners (only among non-abandoned riders)
        gc_winner = final_gc[0][0] if final_gc else None
        sprint_winner = final_sprint[0][0] if final_sprint else None
        mountain_winner = final_mountain[0][0] if final_mountain else None
        youth_winner = final_youth[0][0] if final_youth else None
        for rider in self.rider_db.get_all_riders():
            # Skip abandoned riders for final teammate bonuses
            if rider.name in self.abandoned_riders:
                continue
            # GC winner teammate bonus
            if gc_winner and rider.name != gc_winner and name_to_team[rider.name] == name_to_team[gc_winner]:
                self.scorito_points[rider.name] += 24
                self.scorito_points_records.append({
                    "stage": 22,
                    "rider": rider.name,
                    "scorito_points": self.scorito_points[rider.name]
                })
            # Sprint winner teammate bonus
            if sprint_winner and rider.name != sprint_winner and name_to_team[rider.name] == name_to_team[sprint_winner]:
                self.scorito_points[rider.name] += 18
                self.scorito_points_records.append({
                    "stage": 22,
                    "rider": rider.name,
                    "scorito_points": self.scorito_points[rider.name]
                })
            # Mountain winner teammate bonus
            if mountain_winner and rider.name != mountain_winner and name_to_team[rider.name] == name_to_team[mountain_winner]:
                self.scorito_points[rider.name] += 18
                self.scorito_points_records.append({
                    "stage": 22,
                    "rider": rider.name,
                    "scorito_points": self.scorito_points[rider.name]
                })
            # Youth winner teammate bonus
            if youth_winner and rider.name != youth_winner and name_to_team[rider.name] == name_to_team[youth_winner]:
                self.scorito_points[rider.name] += 9
                self.scorito_points_records.append({
                    "stage": 22,
                    "rider": rider.name,
                    "scorito_points": self.scorito_points[rider.name]
                })

    def write_results_to_excel(self, filename="tour_simulation_results.xlsx"):
        # Convert records to DataFrames
        df_stage = pd.DataFrame(self.stage_results_records)
        df_gc = pd.DataFrame(self.gc_records)
        df_sprint = pd.DataFrame(self.sprint_records)
        df_mountain = pd.DataFrame(self.mountain_records)
        df_youth = pd.DataFrame(self.youth_records)
        df_riders = pd.DataFrame(self.rider_db_records)
        df_scorito = pd.DataFrame(self.scorito_points_records)

        # Write to Excel
        with pd.ExcelWriter(filename) as writer:
            # Write rider database to first sheet
            df_riders.to_excel(writer, sheet_name="RiderDatabase", index=False)
            # Write scorito points per stage
            df_scorito.to_excel(writer, sheet_name="ScoritoPointsPerStage", index=False)
            # Write final scorito points total
            # For the final stage, only keep the last (i.e., final) scorito_points per rider
            final_stage = df_scorito['stage'].max()
            final_scorito = (
                df_scorito[df_scorito['stage'] == final_stage]
                .sort_values(['rider', 'scorito_points'])
                .groupby('rider', as_index=False)
                .last()
                .sort_values('scorito_points', ascending=False)
            )
            final_scorito.to_excel(writer, sheet_name="ScoritoTotal", index=False)
            
            # For each stage, create a sheet with all results up to that stage
            for stage in range(1, 23):  # 22 stages
                sheet_name = f"Stage {stage}"
                
                # Get stage results for current stage
                stage_results = df_stage[df_stage['stage'] == stage].copy()
                stage_results = stage_results[['rider', 'team', 'age', 'position', 'abandoned']]
                stage_results.columns = ['Rider', 'Team', 'Age', 'Position', 'Abandoned']
                # Replace None positions with "DNF" for abandoned riders
                stage_results['Position'] = stage_results['Position'].fillna('DNF')
                
                # Get GC standings after this stage (only non-abandoned riders)
                gc_standings = df_gc[df_gc['stage'] == stage].copy()
                # Filter out abandoned riders
                abandoned_in_stage = df_stage[(df_stage['stage'] == stage) & (df_stage['abandoned'] == True)]['rider'].tolist()
                gc_standings = gc_standings[~gc_standings['rider'].isin(abandoned_in_stage)]
                gc_standings = gc_standings.sort_values('gc_time')
                gc_standings['gc_time'] = gc_standings['gc_time'] / 3600  # Convert to hours
                gc_standings = gc_standings[['rider', 'gc_time']]
                gc_standings.columns = ['Rider', 'GC Time (h)']
                
                # Get Sprint standings after this stage (only non-abandoned riders)
                sprint_standings = df_sprint[df_sprint['stage'] == stage].copy()
                sprint_standings = sprint_standings[~sprint_standings['rider'].isin(abandoned_in_stage)]
                sprint_standings = sprint_standings.sort_values('sprint_points', ascending=False)
                sprint_standings = sprint_standings[['rider', 'sprint_points']]
                sprint_standings.columns = ['Rider', 'Sprint Points']
                
                # Get Mountain standings after this stage (only non-abandoned riders)
                mountain_standings = df_mountain[df_mountain['stage'] == stage].copy()
                mountain_standings = mountain_standings[~mountain_standings['rider'].isin(abandoned_in_stage)]
                mountain_standings = mountain_standings.sort_values('mountain_points', ascending=False)
                mountain_standings = mountain_standings[['rider', 'mountain_points']]
                mountain_standings.columns = ['Rider', 'Mountain Points']
                
                # Get Youth standings after this stage (only non-abandoned riders)
                youth_standings = df_youth[df_youth['stage'] == stage].copy()
                youth_standings = youth_standings[~youth_standings['rider'].isin(abandoned_in_stage)]
                youth_standings = youth_standings.sort_values('youth_time')
                youth_standings['youth_time'] = youth_standings['youth_time'] / 3600  # Convert to hours
                youth_standings = youth_standings[['rider', 'youth_time']]
                youth_standings.columns = ['Rider', 'Youth Time (h)']
                
                # Get scorito points after this stage (only non-abandoned riders)
                scorito_stage = df_scorito[df_scorito['stage'] == stage].copy()
                scorito_stage = scorito_stage[~scorito_stage['rider'].isin(abandoned_in_stage)]
                scorito_stage = scorito_stage[['rider', 'scorito_points']]
                scorito_stage = scorito_stage.sort_values('scorito_points', ascending=False)
                scorito_stage.columns = ['Rider', 'Scorito Points']
                
                # Write all dataframes to the same sheet
                stage_results.to_excel(writer, sheet_name=sheet_name, startrow=0, index=False)
                gc_standings.to_excel(writer, sheet_name=sheet_name, startrow=len(stage_results) + 3, index=False)
                sprint_standings.to_excel(writer, sheet_name=sheet_name, startrow=len(stage_results) + len(gc_standings) + 6, index=False)
                mountain_standings.to_excel(writer, sheet_name=sheet_name, startrow=len(stage_results) + len(gc_standings) + len(sprint_standings) + 9, index=False)
                youth_standings.to_excel(writer, sheet_name=sheet_name, startrow=len(stage_results) + len(gc_standings) + len(sprint_standings) + len(mountain_standings) + 12, index=False)
                scorito_stage.to_excel(writer, sheet_name=sheet_name, startrow=len(stage_results) + len(gc_standings) + len(sprint_standings) + len(mountain_standings) + len(youth_standings) + 15, index=False)
                
                # Add headers for each section
                worksheet = writer.sheets[sheet_name]
                worksheet.cell(row=1, column=1, value=f"Stage {stage} Results")
                worksheet.cell(row=len(stage_results) + 3, column=1, value="General Classification")
                worksheet.cell(row=len(stage_results) + len(gc_standings) + 6, column=1, value="Sprint Classification")
                worksheet.cell(row=len(stage_results) + len(gc_standings) + len(sprint_standings) + 9, column=1, value="Mountain Classification")
                worksheet.cell(row=len(stage_results) + len(gc_standings) + len(sprint_standings) + len(mountain_standings) + 12, column=1, value="Youth Classification")
                worksheet.cell(row=len(stage_results) + len(gc_standings) + len(sprint_standings) + len(mountain_standings) + len(youth_standings) + 15, column=1, value="Scorito Points")
        
        # Excel file written silently (for dashboard use)

    def get_final_gc(self):
        return sorted(self.gc_times.items(), key=lambda x: x[1])
    def get_final_sprint(self):
        return sorted(self.sprint_points.items(), key=lambda x: x[1], reverse=True)
    def get_final_mountain(self):
        return sorted(self.mountain_points.items(), key=lambda x: x[1], reverse=True)
    def get_final_youth(self):
        return sorted(self.youth_times.items(), key=lambda x: x[1])

def run_versus_mode():
    """Run the Versus Mode functionality."""
    try:
        from versus_mode import main as versus_main
        versus_main()
    except ImportError:
        print("Versus Mode not available. Make sure versus_mode.py is in the same directory.")
    except Exception as e:
        print(f"Error running Versus Mode: {e}")

def main():
    print("=== TOUR DE FRANCE SIMULATOR ===")
    print("Choose an option:")
    print("1. Run regular tour simulation")
    print("2. Run Versus Mode (compare your team against optimal team)")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        
        if choice == "1":
            print("\nRunning regular tour simulation...")
            simulator = TourSimulator()
            simulator.simulate_tour()
            
            # Export results with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            simulator.write_results_to_excel(f"tour_simulation_results_{timestamp}.xlsx")
            
            print("\nFINAL GENERAL CLASSIFICATION (TOP 10):")
            for name, t in simulator.get_final_gc():
                if name not in simulator.abandoned_riders:
                    print(f"{name}: {t/3600:.2f}h")
            print("\nFINAL SPRINT CLASSIFICATION (TOP 10):")
            for name, pts in simulator.get_final_sprint():
                if name not in simulator.abandoned_riders:
                    print(f"{name}: {pts} pts")
            print("\nFINAL MOUNTAIN CLASSIFICATION (TOP 10):")
            for name, pts in simulator.get_final_mountain():
                if name not in simulator.abandoned_riders:
                    print(f"{name}: {pts} pts")
            print("\nFINAL YOUTH CLASSIFICATION (TOP 10):")
            for name, t in simulator.get_final_youth():
                if name not in simulator.abandoned_riders:
                    print(f"{name}: {t/3600:.2f}h")
            break
            
        elif choice == "2":
            print("\nStarting Versus Mode...")
            run_versus_mode()
            break
            
        else:
            print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main() 