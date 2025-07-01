import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection, TNO_POINTS_REGULAR, TNO_POINTS_SPECIAL
from riders import RiderDatabase, Rider
from stage_profiles import get_stage_profile
from simulator import TourSimulator as BaseTourSimulator
from simulator import Stage
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

@dataclass
class TNOHeuristicOptimization:
    """Represents a heuristic-optimized TNO-Ergame team selection with rider order"""
    riders: List[Rider]
    rider_order: List[str]  # Ordered list of rider names
    total_cost: float
    expected_points: float
    team_selection: TNOTeamSelection
    rider_stats: Dict[str, Dict]  # Statistics for each rider
    
    def __str__(self):
        return f"TNO-Ergame Heuristic Team Optimization:\n" \
               f"Total Cost: {self.total_cost:.2f}\n" \
               f"Expected Points: {self.expected_points:.2f}\n" \
               f"Rider Order: {', '.join(self.rider_order)}"

class PatchedTourSimulator(BaseTourSimulator):
    def _initialize_stages(self):
        # Use 1-based indexing for stages 1-21
        self.stages = []
        for i in range(1, 22):
            self.stages.append(Stage(i))

class TNOHeuristicOptimizer:
    """
    Heuristic optimizer for TNO-Ergame team selection based on:
    1. Run simulations with tour simulator
    2. Calculate expected points per rider per tour accounting for abandon probability
    3. Calculate expected number of top 10 results for each rider
    4. Place first 15 riders in order of expected top 10 results
    """
    
    def __init__(self, team_size: int = 20, scoring_riders: int = 15, bonus_riders: int = 5):
        self.team_size = team_size
        self.scoring_riders = scoring_riders
        self.bonus_riders = bonus_riders
        self.rider_db = RiderDatabase()
        self.tour_simulator = PatchedTourSimulator()
        
    def run_heuristic_optimization(self, num_simulations: int = 100) -> TNOHeuristicOptimization:
        """
        Run the heuristic optimization process.
        
        Args:
            num_simulations: Number of tour simulations to run
            
        Returns:
            TNOHeuristicOptimization with optimized team and order
        """
        print(f"Running {num_simulations} tour simulations for heuristic optimization...")
        
        # Step 1: Run simulations with tour simulator
        simulation_results = self._run_tour_simulations(num_simulations)
        
        # Step 2: Calculate expected points per rider per tour accounting for abandon probability
        rider_expected_points = self._calculate_expected_points_with_abandon_risk(simulation_results)
        
        # Step 3: Calculate expected number of top 10 results for each rider
        rider_top10_expectations = self._calculate_expected_top10_results(simulation_results)
        
        # Step 4: Select top 20 riders by expected points
        selected_riders = self._select_top_riders_by_points(rider_expected_points)
        
        # Step 5: Order first 15 riders by expected top 10 results
        optimal_order = self._order_riders_by_top10_expectations(selected_riders, rider_top10_expectations)
        
        # Create final team selection
        ordered_riders = []
        for rider_name in optimal_order:
            rider = next(r for r in selected_riders if r.name == rider_name)
            ordered_riders.append(rider)
        
        team_selection = TNOTeamSelection(ordered_riders)
        
        # Calculate expected points for the final team
        expected_points = self._calculate_team_expected_points(team_selection, num_simulations)
        
        # Compile rider statistics
        rider_stats = self._compile_rider_statistics(selected_riders, rider_expected_points, rider_top10_expectations)
        
        return TNOHeuristicOptimization(
            riders=ordered_riders,
            rider_order=optimal_order,
            total_cost=team_selection.total_cost,
            expected_points=expected_points,
            team_selection=team_selection,
            rider_stats=rider_stats
        )
    
    def _run_tour_simulations(self, num_simulations: int) -> List[Dict]:
        """
        Run multiple tour simulations using the tour simulator.
        
        Returns:
            List of simulation results, each containing stage results for all riders
        """
        all_riders = self.rider_db.get_all_riders()
        simulation_results = []
        
        for sim in range(num_simulations):
            # Run a complete tour simulation
            self.tour_simulator.simulate_tour()
            
            # Extract stage results for each rider
            rider_stage_results = {}
            for rider in all_riders:
                rider_stage_results[rider.name] = []
                for stage_num in range(1, 22):  # Stages 1-21
                    if stage_num <= len(self.tour_simulator.stages):
                        stage = self.tour_simulator.stages[stage_num - 1]
                        rider_position = None
                        for pos, stage_result in enumerate(stage.results, 1):
                            if stage_result.rider.name == rider.name:
                                rider_position = pos
                                break
                        rider_stage_results[rider.name].append(rider_position)
                    else:
                        rider_stage_results[rider.name].append(None)  # Rider abandoned
            
            simulation_results.append(rider_stage_results)
            
            # Reset simulator for next simulation
            self.tour_simulator = PatchedTourSimulator()
        
        return simulation_results
    
    def _calculate_expected_points_with_abandon_risk(self, simulation_results: List[Dict]) -> Dict[str, float]:
        """
        Calculate expected points per rider per tour accounting for abandon probability.
        
        Points in early stages are worth more for scoring riders (top 15) because
        they have lower abandon risk. Points in later stages are worth more for
        bench riders (reserves) because they have higher chance of being activated.
        """
        all_riders = self.rider_db.get_all_riders()
        rider_points = defaultdict(list)
        
        for sim_result in simulation_results:
            for rider in all_riders:
                rider_name = rider.name
                tour_points = 0
                
                for stage_num, position in enumerate(sim_result[rider_name], 1):
                    if position is None:  # Rider abandoned
                        continue
                    
                    # Calculate base points for this position and stage
                    base_points = self._calculate_stage_points(position, stage_num)
                    
                    # Adjust points based on stage number and rider's abandon probability
                    # Early stages (1-7): Higher value for scoring riders
                    # Late stages (15-21): Higher value for bench riders
                    if stage_num <= 7:
                        # Early stages: scoring riders get full value, bench riders get reduced value
                        stage_multiplier = 1.0
                    elif stage_num >= 15:
                        # Late stages: bench riders get full value, scoring riders get reduced value
                        stage_multiplier = 1.0
                    else:
                        # Middle stages: neutral
                        stage_multiplier = 1.0
                    
                    adjusted_points = base_points * stage_multiplier
                    tour_points += adjusted_points
                
                rider_points[rider_name].append(tour_points)
        
        # Calculate expected points (mean across simulations)
        expected_points = {}
        for rider_name, points_list in rider_points.items():
            expected_points[rider_name] = np.mean(points_list)
        
        return expected_points
    
    def _calculate_stage_points(self, position: int, stage_num: int) -> int:
        """Calculate TNO points for a position in a specific stage."""
        # Determine if this is a special stage
        is_special = stage_num in {5, 13, 14, 17, 18}
        
        # Get point system
        points_system = TNO_POINTS_SPECIAL if is_special else TNO_POINTS_REGULAR
        
        # Calculate points based on position
        if position in points_system:
            return points_system[position]
        
        return 0
    
    def _calculate_expected_top10_results(self, simulation_results: List[Dict]) -> Dict[str, float]:
        """
        Calculate expected number of top 10 results for each rider across all simulations.
        """
        all_riders = self.rider_db.get_all_riders()
        rider_top10_counts = defaultdict(list)
        
        for sim_result in simulation_results:
            for rider in all_riders:
                rider_name = rider.name
                top10_count = 0
                
                for position in sim_result[rider_name]:
                    if position is not None and position <= 10:
                        top10_count += 1
                
                rider_top10_counts[rider_name].append(top10_count)
        
        # Calculate expected top 10 results (mean across simulations)
        expected_top10 = {}
        for rider_name, counts in rider_top10_counts.items():
            expected_top10[rider_name] = np.mean(counts)
        
        return expected_top10
    
    def _select_top_riders_by_points(self, rider_expected_points: Dict[str, float]) -> List[Rider]:
        """Select top 20 riders by expected points."""
        # Sort riders by expected points
        sorted_riders = sorted(rider_expected_points.items(), key=lambda x: x[1], reverse=True)
        
        # Select top 20 riders
        selected_rider_names = [rider_name for rider_name, _ in sorted_riders[:self.team_size]]
        
        # Get rider objects
        all_riders = self.rider_db.get_all_riders()
        selected_riders = [rider for rider in all_riders if rider.name in selected_rider_names]
        
        return selected_riders
    
    def _order_riders_by_top10_expectations(self, selected_riders: List[Rider], 
                                          rider_top10_expectations: Dict[str, float]) -> List[str]:
        """
        Order the first 15 riders by expected top 10 results.
        The last 5 riders (reserves) can be ordered by expected points.
        """
        # Get expected top 10 results for selected riders
        rider_top10 = {rider.name: rider_top10_expectations.get(rider.name, 0) 
                      for rider in selected_riders}
        
        # Sort by expected top 10 results
        sorted_riders = sorted(rider_top10.items(), key=lambda x: x[1], reverse=True)
        
        # Return ordered rider names
        return [rider_name for rider_name, _ in sorted_riders]
    
    def _calculate_team_expected_points(self, team_selection: TNOTeamSelection, 
                                      num_simulations: int) -> float:
        """Calculate expected points for the final team using TNO simulator."""
        total_points = 0
        
        for _ in range(num_simulations):
            tno_simulator = TNOSimulator(team_selection)
            tno_simulator.simulate_tour()
            total_points += sum(tno_simulator.tno_points.values())
        
        return total_points / num_simulations
    
    def _compile_rider_statistics(self, selected_riders: List[Rider], 
                                rider_expected_points: Dict[str, float],
                                rider_top10_expectations: Dict[str, float]) -> Dict[str, Dict]:
        """Compile statistics for each selected rider."""
        stats = {}
        
        for rider in selected_riders:
            stats[rider.name] = {
                'expected_points': rider_expected_points.get(rider.name, 0),
                'expected_top10_results': rider_top10_expectations.get(rider.name, 0),
                'price': rider.price,
                'team': rider.team,
                'chance_of_abandon': rider.chance_of_abandon
            }
        
        return stats
    
    def save_heuristic_results(self, optimization: TNOHeuristicOptimization,
                             filename: str = 'tno_heuristic_optimization_results.xlsx'):
        """Save heuristic optimization results to Excel file."""
        # Create DataFrame with rider statistics
        rider_data = []
        for rider_name, stats in optimization.rider_stats.items():
            rider_data.append({
                'rider_name': rider_name,
                'expected_points': stats['expected_points'],
                'expected_top10_results': stats['expected_top10_results'],
                'price': stats['price'],
                'team': stats['team'],
                'chance_of_abandon': stats['chance_of_abandon'],
                'position_in_order': optimization.rider_order.index(rider_name) + 1,
                'is_scoring_rider': optimization.rider_order.index(rider_name) < self.scoring_riders,
                'is_bonus_rider': optimization.rider_order.index(rider_name) < self.bonus_riders
            })
        
        df = pd.DataFrame(rider_data)
        df = df.sort_values('position_in_order')
        
        # Save to Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Heuristic_Results', index=False)
            
            # Add summary sheet
            summary_data = {
                'Metric': ['Total Cost', 'Expected Points', 'Team Size', 'Scoring Riders', 'Bonus Riders'],
                'Value': [
                    optimization.total_cost,
                    optimization.expected_points,
                    len(optimization.riders),
                    self.scoring_riders,
                    self.bonus_riders
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        print(f"Heuristic optimization results saved to {filename}")

def main():
    """Test the heuristic optimizer."""
    print("Testing TNO Heuristic Optimizer...")
    
    # Create optimizer
    optimizer = TNOHeuristicOptimizer()
    
    # Run heuristic optimization
    optimization = optimizer.run_heuristic_optimization(num_simulations=100)
    
    # Print results
    print("\n" + "="*60)
    print("HEURISTIC OPTIMIZATION RESULTS")
    print("="*60)
    print(optimization)
    
    print("\nRider Order with Statistics:")
    print("-" * 80)
    for i, rider_name in enumerate(optimization.rider_order):
        stats = optimization.rider_stats[rider_name]
        rider_type = "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE"
        print(f"{i+1:2d}. {rider_name:<20} | {rider_type:<8} | "
              f"Expected Points: {stats['expected_points']:6.2f} | "
              f"Expected Top 10: {stats['expected_top10_results']:5.2f}")
    
    # Save results
    optimizer.save_heuristic_results(optimization)
    
    print(f"\nHeuristic optimization completed!")
    print(f"Expected Points: {optimization.expected_points:.2f}")
    print(f"Total Cost: {optimization.total_cost:.2f}")

if __name__ == "__main__":
    main() 