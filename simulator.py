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
YOUTH_AGE_LIMIT = 24

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
                "is_youth": rider.name in self.youth_rider_names
            })

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

    def write_results_to_excel(self, filename="tour_simulation_results.xlsx"):
        # Convert records to DataFrames
        df_stage = pd.DataFrame(self.stage_results_records)
        df_gc = pd.DataFrame(self.gc_records)
        df_sprint = pd.DataFrame(self.sprint_records)
        df_mountain = pd.DataFrame(self.mountain_records)
        df_youth = pd.DataFrame(self.youth_records)
        df_riders = pd.DataFrame(self.rider_db_records)
        # Write to Excel
        with pd.ExcelWriter(filename) as writer:
            df_stage.to_excel(writer, sheet_name="StageResults", index=False)
            df_gc.to_excel(writer, sheet_name="GC", index=False)
            df_sprint.to_excel(writer, sheet_name="Sprint", index=False)
            df_mountain.to_excel(writer, sheet_name="Mountain", index=False)
            df_youth.to_excel(writer, sheet_name="Youth", index=False)
            df_riders.to_excel(writer, sheet_name="RiderDatabase", index=False)
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