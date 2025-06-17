import numpy as np
import pandas as pd
from typing import List, Dict
from riders import RiderDatabase, Rider
from stage_profiles import get_stage_type, StageType
from dataclasses import dataclass
from collections import defaultdict
from datetime import datetime

# Points arrays for classifications
SPRINT_SPRINT_POINTS = [50, 45, 40, 35, 30, 25, 20, 15, 10, 5]
HILLS_SPRINT_POINTS = [10, 8, 7, 6, 5, 4, 3, 2, 1, 0]
HILLS_MOUNTAIN_POINTS = [20, 18, 16, 14, 12, 10, 8, 6, 4, 2]
MOUNTAIN_MOUNTAIN_POINTS = [50, 45, 40, 35, 30, 25, 20, 15, 10, 5]
PUNCH_SPRINT_POINTS = [20, 18, 16, 14, 12, 10, 8, 6, 4, 2]
PUNCH_MOUNTAIN_POINTS = [10, 8, 7, 6, 5, 4, 3, 2, 1, 0]

# Time gaps per place for each stage type (in seconds)
STAGE_TIME_GAPS = {
    "sprint": 0.1,
    "punch": 0.2,
    "hills": 1,
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

    def simulate(self, rider_db: RiderDatabase):
        for rider in rider_db.get_all_riders():
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
                "hills_ability": rider.parameters.hills_ability,
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
            print(f"\nSimulating Stage {stage_idx+1}")
            print("-------------------")
            stage.simulate(self.rider_db)  # Pass rider_db to stage simulation
            stage_type = get_stage_type(stage_idx+1).value

            # --- General Classification (GC) ---
            base_time = 0 
            time_gap = STAGE_TIME_GAPS[stage_type]
            for place, result in enumerate(stage.results):
                rider_name = result.rider.name
                # Winner gets base_time, others get +gap per place
                self.gc_times[rider_name] += base_time + time_gap * place
                # Youth GC - only track times for eligible riders
                if rider_name in self.youth_rider_names:
                    self.youth_times[rider_name] = self.gc_times[rider_name]  # Use same time as GC

            # --- Sprint Classification ---
            if stage_type == "sprint":
                for idx, result in enumerate(stage.results[:len(SPRINT_SPRINT_POINTS)]):
                    self.sprint_points[result.rider.name] += SPRINT_SPRINT_POINTS[idx]
            elif stage_type == "hills":
                for idx, result in enumerate(stage.results[:len(HILLS_SPRINT_POINTS)]):
                    self.sprint_points[result.rider.name] += HILLS_SPRINT_POINTS[idx]
            elif stage_type == "punch":
                for idx, result in enumerate(stage.results[:len(PUNCH_SPRINT_POINTS)]):
                    self.sprint_points[result.rider.name] += PUNCH_SPRINT_POINTS[idx]

            # --- Mountain Classification ---
            if stage_type == "mountain":
                for idx, result in enumerate(stage.results[:len(MOUNTAIN_MOUNTAIN_POINTS)]):
                    self.mountain_points[result.rider.name] += MOUNTAIN_MOUNTAIN_POINTS[idx]
            elif stage_type == "hills":
                for idx, result in enumerate(stage.results[:len(HILLS_MOUNTAIN_POINTS)]):
                    self.mountain_points[result.rider.name] += HILLS_MOUNTAIN_POINTS[idx]
            elif stage_type == "punch":
                for idx, result in enumerate(stage.results[:len(PUNCH_MOUNTAIN_POINTS)]):
                    self.mountain_points[result.rider.name] += PUNCH_MOUNTAIN_POINTS[idx]

            # --- Collect Data for DataFrames ---
            # Stage results
            for place, result in enumerate(stage.results, 1):
                self.stage_results_records.append({
                    "stage": stage_idx+1,
                    "rider": result.rider.name,
                    "team": result.rider.team,
                    "age": result.rider.age,
                    "position": place,
                    "sim_position": result.position
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
            # Stage result points (top 20)
            for idx, result in enumerate(stage.results[:20]):
                pts = SCORITO_STAGE_POINTS[idx]
                self.scorito_points[result.rider.name] += pts
            # GC classification points (top 5 after this stage)
            gc_sorted = sorted(self.gc_times.items(), key=lambda x: x[1])[:5]
            for idx, (name, _) in enumerate(gc_sorted):
                pts = SCORITO_STAGE_GC_POINTS[idx]
                self.scorito_points[name] += pts
            # Sprint classification points (top 5 after this stage)
            sprint_sorted = sorted(self.sprint_points.items(), key=lambda x: x[1], reverse=True)[:5]
            for idx, (name, _) in enumerate(sprint_sorted):
                pts = SCORITO_STAGE_SPRINT_POINTS[idx]
                self.scorito_points[name] += pts
            # Mountain classification points (top 5 after this stage)
            mountain_sorted = sorted(self.mountain_points.items(), key=lambda x: x[1], reverse=True)[:5]
            for idx, (name, _) in enumerate(mountain_sorted):
                pts = SCORITO_STAGE_MOUNTAIN_POINTS[idx]
                self.scorito_points[name] += pts
            # Youth classification points (top 5 after this stage)
            youth_sorted = sorted(self.youth_times.items(), key=lambda x: x[1])[:5]
            for idx, (name, _) in enumerate(youth_sorted):
                pts = SCORITO_STAGE_YOUTH_POINTS[idx]
                self.scorito_points[name] += pts

            # --- Teammate Bonus Points ---
            # Find winners
            stage_winner = stage.results[0].rider
            gc_leader = gc_sorted[0][0] if gc_sorted else None
            sprint_leader = sprint_sorted[0][0] if sprint_sorted else None
            mountain_leader = mountain_sorted[0][0] if mountain_sorted else None
            youth_leader = youth_sorted[0][0] if youth_sorted else None
            # Map rider names to teams
            name_to_team = {r.name: r.team for r in self.rider_db.get_all_riders()}
            for rider in self.rider_db.get_all_riders():
                # Stage winner teammate bonus
                if rider.name != stage_winner.name and name_to_team[rider.name] == stage_winner.team:
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

            # Record scorito points after this stage for export
            for rider in self.rider_db.get_all_riders():
                self.scorito_points_records.append({
                    "stage": stage_idx+1,
                    "rider": rider.name,
                    "scorito_points": self.scorito_points[rider.name]
                })

            # --- Print Standings after Stage ---
            print("\nGC Standings (Top 5):")
            for name, t in sorted(self.gc_times.items(), key=lambda x: x[1])[:5]:
                print(f"{name}: {t/3600:.2f}h")
            print("\nSprint Standings (Top 5):")
            for name, pts in sorted(self.sprint_points.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"{name}: {pts} pts")
            print("\nMountain Standings (Top 5):")
            for name, pts in sorted(self.mountain_points.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"{name}: {pts} pts")
            print("\nYouth GC Standings (Top 5):")
            for name, t in sorted(self.youth_times.items(), key=lambda x: x[1])[:5]:
                print(f"{name}: {t/3600:.2f}h")

        # After all stages, award final GC points
        final_gc = self.get_final_gc()
        for idx, (name, _) in enumerate(final_gc[:len(SCORITO_FINAL_GC_POINTS)]):
            pts = SCORITO_FINAL_GC_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_gc[:len(SCORITO_FINAL_GC_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,  # Use 22 to indicate final GC points
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award final Sprint points
        final_sprint = self.get_final_sprint()
        for idx, (name, _) in enumerate(final_sprint[:len(SCORITO_FINAL_SPRINT_POINTS)]):
            pts = SCORITO_FINAL_SPRINT_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_sprint[:len(SCORITO_FINAL_SPRINT_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award final Mountain points
        final_mountain = self.get_final_mountain()
        for idx, (name, _) in enumerate(final_mountain[:len(SCORITO_FINAL_MOUNTAIN_POINTS)]):
            pts = SCORITO_FINAL_MOUNTAIN_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_mountain[:len(SCORITO_FINAL_MOUNTAIN_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award final Youth points
        final_youth = self.get_final_youth()
        for idx, (name, _) in enumerate(final_youth[:len(SCORITO_FINAL_YOUTH_POINTS)]):
            pts = SCORITO_FINAL_YOUTH_POINTS[idx]
            self.scorito_points[name] += pts
        for idx, (name, _) in enumerate(final_youth[:len(SCORITO_FINAL_YOUTH_POINTS)]):
            self.scorito_points_records.append({
                "stage": 22,
                "rider": name,
                "scorito_points": self.scorito_points[name]
            })

        # Award teammate bonus points for final classification winners
        # Map rider names to teams
        name_to_team = {r.name: r.team for r in self.rider_db.get_all_riders()}
        # Get winners
        gc_winner = final_gc[0][0] if final_gc else None
        sprint_winner = final_sprint[0][0] if final_sprint else None
        mountain_winner = final_mountain[0][0] if final_mountain else None
        youth_winner = final_youth[0][0] if final_youth else None
        for rider in self.rider_db.get_all_riders():
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
                stage_results = stage_results[['rider', 'team', 'age', 'position']]
                stage_results.columns = ['Rider', 'Team', 'Age', 'Position']
                
                # Get GC standings after this stage
                gc_standings = df_gc[df_gc['stage'] == stage].copy()
                gc_standings = gc_standings.sort_values('gc_time')
                gc_standings['gc_time'] = gc_standings['gc_time'] / 3600  # Convert to hours
                gc_standings = gc_standings[['rider', 'gc_time']]
                gc_standings.columns = ['Rider', 'GC Time (h)']
                
                # Get Sprint standings after this stage
                sprint_standings = df_sprint[df_sprint['stage'] == stage].copy()
                sprint_standings = sprint_standings.sort_values('sprint_points', ascending=False)
                sprint_standings = sprint_standings[['rider', 'sprint_points']]
                sprint_standings.columns = ['Rider', 'Sprint Points']
                
                # Get Mountain standings after this stage
                mountain_standings = df_mountain[df_mountain['stage'] == stage].copy()
                mountain_standings = mountain_standings.sort_values('mountain_points', ascending=False)
                mountain_standings = mountain_standings[['rider', 'mountain_points']]
                mountain_standings.columns = ['Rider', 'Mountain Points']
                
                # Get Youth standings after this stage
                youth_standings = df_youth[df_youth['stage'] == stage].copy()
                youth_standings = youth_standings.sort_values('youth_time')
                youth_standings['youth_time'] = youth_standings['youth_time'] / 3600  # Convert to hours
                youth_standings = youth_standings[['rider', 'youth_time']]
                youth_standings.columns = ['Rider', 'Youth Time (h)']
                
                # Get scorito points after this stage
                scorito_stage = df_scorito[df_scorito['stage'] == stage].copy()
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
        
        print(f"\nExcel file '{filename}' written with all results.")

    def get_final_gc(self):
        return sorted(self.gc_times.items(), key=lambda x: x[1])
    def get_final_sprint(self):
        return sorted(self.sprint_points.items(), key=lambda x: x[1], reverse=True)
    def get_final_mountain(self):
        return sorted(self.mountain_points.items(), key=lambda x: x[1], reverse=True)
    def get_final_youth(self):
        return sorted(self.youth_times.items(), key=lambda x: x[1])

def main():
    simulator = TourSimulator()
    simulator.simulate_tour()
    
    # Export results with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    simulator.write_results_to_excel(f"tour_simulation_results_{timestamp}.xlsx")
    
    print("\nFINAL GENERAL CLASSIFICATION (TOP 10):")
    for name, t in simulator.get_final_gc()[:10]:
        print(f"{name}: {t/3600:.2f}h")
    print("\nFINAL SPRINT CLASSIFICATION (TOP 10):")
    for name, pts in simulator.get_final_sprint()[:10]:
        print(f"{name}: {pts} pts")
    print("\nFINAL MOUNTAIN CLASSIFICATION (TOP 10):")
    for name, pts in simulator.get_final_mountain()[:10]:
        print(f"{name}: {pts} pts")
    print("\nFINAL YOUTH CLASSIFICATION (TOP 10):")
    for name, t in simulator.get_final_youth()[:10]:
        print(f"{name}: {t/3600:.2f}h")

if __name__ == "__main__":
    main() 