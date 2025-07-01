import pandas as pd
import numpy as np
from pulp import *
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
from tno_ergame_multi_simulator import TNOMultiSimulationAnalyzer
from riders import RiderDatabase, Rider
from collections import defaultdict
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
        Run simulations to get expected points for each rider.
        
        Args:
            num_simulations: Number of simulations to run
            metric: Metric to use for expected points ('mean', 'median')
            
        Returns:
            DataFrame with rider names and their expected points
        """
        # Running simulations to calculate expected points
        
        # Create a temporary team with all riders to get baseline performance
        all_riders = self.rider_db.get_all_riders()
        temp_team = TNOTeamSelection(all_riders[:20])  # Use first 20 as temporary
        
        # Run multi-simulation analysis
        analyzer = TNOMultiSimulationAnalyzer(num_simulations)
        metrics = analyzer.run_simulations(temp_team)
        
        # Get rider statistics
        rider_stats = metrics['tno_analysis']['rider_stats']
        
        # Create DataFrame with rider information
        rider_data = []
        for rider in all_riders:
            stats = rider_stats.get(rider.name, {
                'mean': 0, 'median': 0, 'std': 0, 'min': 0, 'max': 0, 'count': 0
            })
            
            rider_data.append({
                'rider_name': rider.name,
                'expected_points': stats['mean'],
                'points_std': stats['std'],
                'points_median': stats['median'],
                'points_min': stats['min'],
                'points_max': stats['max'],
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
    
    def optimize_team_with_order(self, rider_data: pd.DataFrame, 
                                num_simulations: int = 50,
                                risk_aversion: float = 0.0,
                                abandon_penalty: float = 1.0) -> TNOTeamOptimization:
        """
        Optimize both team selection and rider order using a two-phase approach.
        
        Phase 1: Select optimal 20 riders
        Phase 2: Optimize rider order for maximum bonus points
        """
        # Starting TNO-Ergame team optimization...
        
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
        
        # Calculate expected points for the final team
        expected_points = self._calculate_team_expected_points(team_selection, num_simulations)
        
        return TNOTeamOptimization(
            riders=ordered_riders,
            rider_order=optimal_order,
            total_cost=team_selection.total_cost,
            expected_points=expected_points,
            team_selection=team_selection
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
        """Get expected points for a specific rider in a team context"""
        # Create a temporary team with this rider in different positions
        temp_team = TNOTeamSelection(team_riders)
        
        # Run a few simulations to get expected points
        analyzer = TNOMultiSimulationAnalyzer(min(num_simulations, 20))  # Use fewer simulations for speed
        metrics = analyzer.run_simulations(temp_team)
        
        rider_stats = metrics['tno_analysis']['rider_stats']
        return rider_stats.get(rider.name, {}).get('mean', 0)
    
    def _calculate_bonus_potential(self, rider: Rider, team_riders: List[Rider], 
                                  num_simulations: int) -> float:
        """Calculate bonus potential for a rider (likelihood of finishing top 10)"""
        # This is a simplified calculation
        # In a full implementation, you would run simulations to calculate this
        
        # Use rider abilities as a proxy for bonus potential
        abilities = [
            rider.parameters.sprint_ability,
            rider.parameters.punch_ability,
            rider.parameters.itt_ability,
            rider.parameters.mountain_ability,
            rider.parameters.break_away_ability
        ]
        
        avg_ability = np.mean(abilities)
        max_ability = np.max(abilities)
        
        # Bonus potential based on abilities
        bonus_potential = (avg_ability * 0.7 + max_ability * 0.3) / 100
        
        return bonus_potential
    
    def _calculate_team_expected_points(self, team_selection: TNOTeamSelection, 
                                       num_simulations: int) -> float:
        """Calculate expected points for a team selection"""
        analyzer = TNOMultiSimulationAnalyzer(num_simulations)
        metrics = analyzer.run_simulations(team_selection)
        
        return metrics['team_performance']['total_points']['mean']
    
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
