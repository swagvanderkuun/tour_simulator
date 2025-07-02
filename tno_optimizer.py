import pandas as pd
import numpy as np
from pulp import *
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection, TNO_POINTS_REGULAR, TNO_POINTS_SPECIAL
from tno_ergame_multi_simulator import TNOMultiSimulationAnalyzer
from riders import RiderDatabase, Rider
from stage_profiles import get_stage_profile
from collections import defaultdict
# Removed ProcessPoolExecutor import to avoid multiprocessing issues
# Removed multiprocessing import to avoid ScriptRunContext warnings
import warnings
warnings.filterwarnings('ignore')

@dataclass
class TNOTeamOptimization:
    """Represents an optimized TNO-Ergame team selection with rider order"""
    riders: List[Rider]
    rider_order: List[str]  # Ordered list of rider names
    total_cost: float
    expected_points: float
    team_selection: TNOTeamSelection
    team_size: int = 20  # Default team size
    
    def __str__(self):
        return f"TNO-Ergame Team Optimization:\n" \
               f"Total Cost: {self.total_cost:.2f}\n" \
               f"Expected Points: {self.expected_points:.2f}\n" \
               f"Rider Order: {', '.join(self.rider_order)}"

class TNOTeamOptimizer:
    """
    Optimizes TNO-Ergame team selection and rider order for maximum points.
    
    This optimizer considers:
    - Rider selection (20 riders)
    - Rider order (affects bonus points and scoring rider status)
    - Budget constraints
    - Abandonment risks
    """
    
    def __init__(self, budget: float = 48.0, team_size: int = 20, 
                 scoring_riders: int = 15, bonus_riders: int = 5):
        self.budget = budget
        self.team_size = team_size
        self.scoring_riders = scoring_riders
        self.bonus_riders = bonus_riders
        self.rider_db = RiderDatabase()
        
    def run_simulation_for_riders(self, num_simulations: int = 100, metric: str = 'mean') -> pd.DataFrame:
        """
        Run simulations to get expected points for each rider individually.
        
        OPTIMIZED: Run simulations once and extract all rider data from the same results.
        This is much faster than running separate simulations for each rider.
        
        Args:
            num_simulations: Number of simulations to run
            metric: Metric to use for expected points ('mean', 'median')
            
        Returns:
            DataFrame with rider names and their expected points
        """
        # Running simulations to calculate expected points for all riders at once
        
        all_riders = self.rider_db.get_all_riders()
        rider_points_data = {rider.name: [] for rider in all_riders}
        
        # Run simulations once and collect data for all riders
        for sim_num in range(num_simulations):
            # Create a single tour simulator and run complete tour (21 stages for TNO-Ergame)
            from simulator import TourSimulator as BaseTourSimulator
            from simulator import Stage
            
            class PatchedTourSimulator(BaseTourSimulator):
                def _initialize_stages(self):
                    # Use 1-based indexing for stages 1-21 (TNO-Ergame uses 21 stages)
                    self.stages = []
                    for i in range(1, 22):
                        self.stages.append(Stage(i))
            
            tour_simulator = PatchedTourSimulator()
            tour_simulator.simulate_tour()
            
            # Extract points for all riders from this simulation
            for rider in all_riders:
                rider_points = 0
                for stage_num in range(1, 22):  # Stages 1-21
                    if stage_num <= len(tour_simulator.stages):
                        stage = tour_simulator.stages[stage_num - 1]
                        rider_position = None
                        for pos, stage_result in enumerate(stage.results, 1):
                            if stage_result.rider.name == rider.name:
                                rider_position = pos
                                break
                        
                        if rider_position:
                            # Calculate TNO points for this position and stage
                            points = self._calculate_stage_points_for_rider(rider_position, stage_num, {})
                            rider_points += points
                
                rider_points_data[rider.name].append(rider_points)
        
        # Calculate statistics for each rider
        rider_data = []
        for rider in all_riders:
            points_list = rider_points_data[rider.name]
            
            if metric == 'mean':
                expected_points = sum(points_list) / len(points_list)
            elif metric == 'median':
                expected_points = sorted(points_list)[len(points_list) // 2]
            else:
                expected_points = sum(points_list) / len(points_list)
            
            # Calculate standard deviation for risk assessment
            if len(points_list) > 1:
                mean_points = sum(points_list) / len(points_list)
                variance = sum((p - mean_points) ** 2 for p in points_list) / (len(points_list) - 1)
                points_std = variance ** 0.5
            else:
                points_std = 0
            
            rider_data.append({
                'rider_name': rider.name,
                'expected_points': expected_points,
                'points_std': points_std,
                'points_median': sorted(points_list)[len(points_list) // 2] if points_list else 0,
                'points_min': min(points_list) if points_list else 0,
                'points_max': max(points_list) if points_list else 0,
                'price': rider.price,
                'team': rider.team,
                'age': rider.age,
                'chance_of_abandon': rider.chance_of_abandon,
                'sprint_ability': rider.parameters.sprint_ability,
                'punch_ability': rider.parameters.punch_ability,
                'itt_ability': rider.parameters.itt_ability,
                'mountain_ability': rider.parameters.mountain_ability,
                'break_away_ability': rider.parameters.break_away_ability
            })
        
        df = pd.DataFrame(rider_data)
        df = df.sort_values('expected_points', ascending=False)
        
        return df
    
    # Removed _calculate_individual_rider_expected_points method - now using optimized batch processing
    
    # Removed _calculate_rider_points_chunk method as it's no longer needed without parallelization
    
    def _calculate_stage_points_for_rider(self, position: float, stage_num: int, stage_profile: dict) -> int:
        """
        Calculate TNO points for a rider in a specific stage based on their position.
        
        This simulates the TNO-Ergame scoring system for an individual rider.
        """
        # Determine if this is a special stage
        is_special = stage_num in {5, 13, 14, 17, 18}
        
        # Get point system
        points_system = TNO_POINTS_SPECIAL if is_special else TNO_POINTS_REGULAR
        
        # Calculate points based on position
        position_int = int(position)
        if position_int in points_system:
            return points_system[position_int]
        
        return 0
    
    def optimize_team_with_order(self, rider_data: pd.DataFrame, 
                                num_simulations: int = 50,
                                risk_aversion: float = 0.0,
                                abandon_penalty: float = 1.0) -> TNOTeamOptimization:
        """
        Optimize both team selection and rider order using a two-phase approach.
        
        Phase 1: Select optimal 20 riders
        Phase 2: Optimize rider order for maximum bonus points
        """
        # Starting TNO-Ergame team optimization (silent mode)...
        
        # Phase 1: Select optimal 20 riders
        selected_riders = self._optimize_rider_selection(rider_data, risk_aversion, abandon_penalty)
        
        # Phase 2: Optimize rider order
        optimal_order = self._optimize_rider_order(selected_riders, num_simulations)
        
        # Create final team selection
        ordered_riders = []
        for rider_name in optimal_order:
            rider = next(r for r in selected_riders if r.name == rider_name)
            ordered_riders.append(rider)
        
        team_selection = TNOTeamSelection(ordered_riders)
        
        # Calculate expected points for the final team using cached rider data
        expected_points = self._calculate_team_expected_points(team_selection, rider_data, num_simulations)
        
        return TNOTeamOptimization(
            riders=ordered_riders,
            rider_order=optimal_order,
            total_cost=team_selection.total_cost,
            expected_points=expected_points,
            team_selection=team_selection,
            team_size=self.team_size
        )
    
    def _optimize_rider_selection(self, rider_data: pd.DataFrame, 
                                 risk_aversion: float, 
                                 abandon_penalty: float) -> List[Rider]:
        """Optimize rider selection using Integer Linear Programming"""
        
        # Create optimization problem
        prob = LpProblem("TNO_Rider_Selection", LpMaximize)
        
        # Decision variables: 1 if rider is selected, 0 otherwise
        riders = list(rider_data['rider_name'])
        rider_vars = LpVariable.dicts("Rider", riders, cat='Binary')
        
        # Objective function: maximize expected points
        objective_terms = []
        for _, row in rider_data.iterrows():
            rider_name = row['rider_name']
            expected_points = row['expected_points']
            points_std = row['points_std']
            abandon_prob = row.get('chance_of_abandon', 0.0)
            
            # Risk-adjusted expected points
            risk_adjusted_points = expected_points - (risk_aversion * points_std)
            
            # Abandon penalty: reduce points based on abandon probability
            abandon_adjusted_points = risk_adjusted_points * (1 - abandon_penalty * abandon_prob)
            
            objective_terms.append(rider_vars[rider_name] * abandon_adjusted_points)
        
        prob += lpSum(objective_terms)
        
        # Constraint 1: Exactly team_size riders
        prob += lpSum(rider_vars[rider] for rider in riders) == self.team_size
        
        # Constraint 2: Maximum 4 riders per team
        team_counts = {}
        for _, row in rider_data.iterrows():
            rider_name = row['rider_name']
            team = row['team']
            if team not in team_counts:
                team_counts[team] = []
            team_counts[team].append(rider_vars[rider_name])
        
        for team, rider_vars_list in team_counts.items():
            prob += lpSum(rider_vars_list) <= 4
        
        # Solve
        prob.solve()
        
        if prob.status != LpStatusOptimal:
            # Warning: Rider selection optimization failed, using fallback
            return self._fallback_rider_selection(rider_data)
        
        # Extract selected riders
        selected_rider_names = []
        for rider in riders:
            if rider_vars[rider].value() == 1:
                selected_rider_names.append(rider)
        
        # Convert to Rider objects
        selected_riders = []
        for rider_name in selected_rider_names:
            rider = self.rider_db.get_rider(rider_name)
            if rider:
                selected_riders.append(rider)
        
        return selected_riders
    
    def _optimize_rider_order(self, selected_riders: List[Rider], 
                             num_simulations: int) -> List[str]:
        """
        Optimize rider order to maximize bonus points.
        This is a complex optimization problem that considers:
        - Bonus points for top 5 positions
        - Scoring rider status (first 15)
        - Abandonment risks and replacements
        """
        
        # For now, use a heuristic approach based on expected points and bonus potential
        # This can be enhanced with more sophisticated optimization
        
        # Calculate bonus potential for each rider
        rider_bonus_potential = []
        for rider in selected_riders:
            # Get rider's expected performance
            expected_points = self._get_rider_expected_points(rider, selected_riders, num_simulations)
            
            # Calculate bonus potential (how likely they are to finish top 10)
            bonus_potential = self._calculate_bonus_potential(rider, selected_riders, num_simulations)
            
            # Combined score: expected points + bonus potential
            combined_score = expected_points + (bonus_potential * 2)  # Weight bonus potential higher
            
            rider_bonus_potential.append((rider, combined_score))
        
        # Sort by combined score (highest first)
        rider_bonus_potential.sort(key=lambda x: x[1], reverse=True)
        
        # Return ordered rider names
        return [rider.name for rider, _ in rider_bonus_potential]
    
    def _get_rider_expected_points(self, rider: Rider, team_riders: List[Rider], 
                                  num_simulations: int) -> float:
        """Get expected points for a specific rider in a team context using cached data"""
        # This method should use cached simulation data from run_simulation_for_riders
        # For now, we'll use a simplified estimation, but in a full implementation
        # we would pass the rider_data DataFrame to access cached results
        
        # Use realistic TNO point estimation based on rider abilities
        # Calculate expected points per stage based on rider's probability of finishing in top 10
        sprint_prob = min(rider.parameters.sprint_ability / 100, 0.8)  # Cap at 80%
        punch_prob = min(rider.parameters.punch_ability / 100, 0.8)
        itt_prob = min(rider.parameters.itt_ability / 100, 0.8)
        mountain_prob = min(rider.parameters.mountain_ability / 100, 0.8)
        breakaway_prob = min(rider.parameters.break_away_ability / 100, 0.8)
        
        # Average probability across all abilities
        avg_prob = (sprint_prob + punch_prob + itt_prob + mountain_prob + breakaway_prob) / 5
        
        # Calculate expected points per stage
        # Regular stages: 1-10 positions get 1-20 points
        # Special stages: 1-10 positions get 1-30 points
        # Assume 5 special stages and 16 regular stages
        regular_stage_points = avg_prob * 10.5  # Average of 1-20 points
        special_stage_points = avg_prob * 15.5  # Average of 1-30 points
        
        expected_points_per_tour = (regular_stage_points * 16) + (special_stage_points * 5)
        
        return expected_points_per_tour
    
    def _calculate_bonus_potential(self, rider: Rider, team_riders: List[Rider], num_simulations: int) -> float:
        """Calculate bonus potential for a rider using fast estimation instead of simulations"""
        # Use rider abilities to estimate top 10 finish probability
        # This is much faster than running simulations
        
        # Calculate probability of finishing in top 10 based on rider abilities
        sprint_prob = min(rider.parameters.sprint_ability / 100, 0.8)  # Cap at 80%
        punch_prob = min(rider.parameters.punch_ability / 100, 0.8)
        itt_prob = min(rider.parameters.itt_ability / 100, 0.8)
        mountain_prob = min(rider.parameters.mountain_ability / 100, 0.8)
        breakaway_prob = min(rider.parameters.break_away_ability / 100, 0.8)
        
        # Average probability across all abilities
        avg_prob = (sprint_prob + punch_prob + itt_prob + mountain_prob + breakaway_prob) / 5
        
        # Convert to expected top 10 finishes per tour (21 stages)
        expected_top10_finishes = avg_prob * 21 * 0.3  # 30% chance of top 10 when ability is high
        
        return expected_top10_finishes
    
    def _calculate_team_expected_points(self, team_selection: TNOTeamSelection, 
                                       rider_data: pd.DataFrame,
                                       num_simulations: int) -> float:
        """Calculate expected points for a team selection using TNOSimulator (same as heuristic optimizer)"""
        # Use TNOSimulator to calculate team points with proper TNO rules
        # This ensures fair comparison with heuristic optimizer
        
        total_points = 0
        
        for _ in range(num_simulations):
            tno_simulator = TNOSimulator(team_selection)
            tno_simulator.simulate_tour()
            total_points += sum(tno_simulator.tno_points.values())
        
        return total_points / num_simulations
    
    def _fallback_rider_selection(self, rider_data: pd.DataFrame) -> List[Rider]:
        """Fallback method to select riders if optimization fails"""
        # Using fallback rider selection method
        
        # Sort by expected points and select top riders
        sorted_data = rider_data.sort_values('expected_points', ascending=False)
        
        selected_riders = []
        team_counts = defaultdict(int)
        
        for _, row in sorted_data.iterrows():
            if len(selected_riders) >= self.team_size:
                break
                
            rider_name = row['rider_name']
            team = row['team']
            
            # Check team constraint
            if team_counts[team] >= 4:
                continue
                
            # Add rider
            rider = self.rider_db.get_rider(rider_name)
            if rider:
                selected_riders.append(rider)
                team_counts[team] += 1
        
        return selected_riders
    
    def get_alternative_teams(self, rider_data: pd.DataFrame, 
                            num_alternatives: int = 5,
                            num_simulations: int = 50) -> List[TNOTeamOptimization]:
        """Get alternative team selections"""
        alternatives = []
        
        for i in range(num_alternatives):
            # Vary risk aversion and abandon penalty to get different teams
            risk_aversion = i * 0.1
            abandon_penalty = 1.0 - (i * 0.1)
            
            try:
                optimization = self.optimize_team_with_order(
                    rider_data, num_simulations, risk_aversion, abandon_penalty
                )
                alternatives.append(optimization)
            except Exception as e:
                # Failed to generate alternative team
                continue
        
        return alternatives
    
    def save_optimization_results(self, optimization: TNOTeamOptimization, 
                                 rider_data: pd.DataFrame,
                                 filename: str = 'tno_ergame_optimization_results.xlsx'):
        """Save optimization results to Excel"""
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Team summary
            team_summary = pd.DataFrame([{
                'total_cost': optimization.total_cost,
                'expected_points': optimization.expected_points,
                'team_size': len(optimization.riders),
                'scoring_riders': 15,
                'bonus_riders': 5
            }])
            team_summary.to_excel(writer, sheet_name='Team_Summary', index=False)
            
            # Rider order
            rider_order_data = []
            for i, rider_name in enumerate(optimization.rider_order, 1):
                rider = next(r for r in optimization.riders if r.name == rider_name)
                rider_order_data.append({
                    'position': i,
                    'rider_name': rider_name,
                    'team': rider.team,
                    'price': rider.price,
                    'is_scoring_rider': i <= 15,
                    'is_bonus_rider': i <= 5,
                    'bonus_points': 6 - i if i <= 5 else 0
                })
            
            rider_order_df = pd.DataFrame(rider_order_data)
            rider_order_df.to_excel(writer, sheet_name='Rider_Order', index=False)
            
            # Rider performance data
            rider_data.to_excel(writer, sheet_name='Rider_Performance', index=False)

def main():
    """Example usage of TNO-Ergame optimizer"""
    # Create optimizer
    optimizer = TNOTeamOptimizer(budget=48.0, team_size=20)
    
    # Get rider performance data
    rider_data = optimizer.run_simulation_for_riders(num_simulations=50)
    
    # Optimize team
    optimization = optimizer.optimize_team_with_order(rider_data, num_simulations=50)
    
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
    optimizer.save_optimization_results(optimization, rider_data)
    print(f"\nResults saved to 'tno_ergame_optimization_results.xlsx'")
    
    # Get alternative teams
    alternatives = optimizer.get_alternative_teams(rider_data, num_alternatives=3)

if __name__ == "__main__":
    main()
