import pandas as pd
import numpy as np
from pulp import *
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from simulator import TourSimulator
from riders import RiderDatabase, Rider
import warnings
warnings.filterwarnings('ignore')

@dataclass
class TeamSelection:
    """Represents a team selection with riders and their expected performance."""
    riders: List[Rider]
    total_cost: float
    expected_points: float
    rider_names: List[str]
    
    def __str__(self):
        return f"Team Selection:\n" \
               f"Total Cost: {self.total_cost:.2f}\n" \
               f"Expected Points: {self.expected_points:.2f}\n" \
               f"Riders: {', '.join(self.rider_names)}"

class TeamOptimizer:
    """
    Optimizes team selection for maximum Scorito points using Integer Linear Programming.
    
    Constraints:
    - Exactly 20 riders
    - Total cost <= 48
    - Each stage: select 9 riders (except stage 22: all 20 riders)
    """
    
    def __init__(self, budget: float = 48.0, team_size: int = 20, 
                 riders_per_stage: int = 9, final_stage_riders: int = 20):
        self.budget = budget
        self.team_size = team_size
        self.riders_per_stage = riders_per_stage
        self.final_stage_riders = final_stage_riders
        self.simulator = TourSimulator()
        self.rider_db = RiderDatabase()
        
    def run_simulation(self, num_simulations: int = 100) -> pd.DataFrame:
        """
        Run multiple simulations to get expected points for each rider.
        
        Args:
            num_simulations: Number of simulations to run
            
        Returns:
            DataFrame with rider names and their expected points
        """
        print(f"Running {num_simulations} simulations to calculate expected points...")
        
        # Store points from all simulations
        all_points = []
        
        for i in range(num_simulations):
            if i % 10 == 0:
                print(f"Simulation {i+1}/{num_simulations}")
            
            # Run simulation
            self.simulator.simulate_tour()
            
            # Get final points for each rider
            for rider_name, points in self.simulator.scorito_points.items():
                all_points.append({
                    'rider_name': rider_name,
                    'points': points,
                    'simulation': i
                })
            
            # Reset simulator for next run
            self.simulator = TourSimulator()
        
        # Calculate expected points for each rider
        points_df = pd.DataFrame(all_points)
        expected_points = points_df.groupby('rider_name')['points'].agg(['mean', 'std']).reset_index()
        expected_points.columns = ['rider_name', 'expected_points', 'points_std']
        
        # Add rider information
        rider_info = []
        for rider in self.rider_db.get_all_riders():
            rider_info.append({
                'rider_name': rider.name,
                'price': rider.price,
                'team': rider.team,
                'age': rider.age
            })
        
        rider_info_df = pd.DataFrame(rider_info)
        
        # Merge with expected points
        final_df = rider_info_df.merge(expected_points, on='rider_name', how='left')
        final_df['expected_points'] = final_df['expected_points'].fillna(0)
        final_df['points_std'] = final_df['points_std'].fillna(0)
        
        return final_df
    
    def optimize_team(self, rider_data: pd.DataFrame, 
                     risk_aversion: float = 0.0,
                     min_riders_per_team: Optional[Dict[str, int]] = None) -> TeamSelection:
        """
        Optimize team selection using Integer Linear Programming.
        
        Args:
            rider_data: DataFrame with rider information and expected points
            risk_aversion: Factor to penalize high variance (0 = no penalty, 1 = high penalty)
            min_riders_per_team: Minimum riders required from each team
            
        Returns:
            TeamSelection object with optimal team
        """
        print("Optimizing team selection...")
        
        # Create optimization problem
        prob = LpProblem("Team_Optimization", LpMaximize)
        
        # Decision variables: 1 if rider is selected, 0 otherwise
        riders = list(rider_data['rider_name'])
        rider_vars = LpVariable.dicts("Rider", riders, cat='Binary')
        
        # Objective function: maximize expected points
        # If risk_aversion > 0, penalize high variance
        objective_terms = []
        for _, row in rider_data.iterrows():
            rider_name = row['rider_name']
            expected_points = row['expected_points']
            points_std = row['points_std']
            
            # Risk-adjusted expected points
            risk_adjusted_points = expected_points - (risk_aversion * points_std)
            objective_terms.append(rider_vars[rider_name] * risk_adjusted_points)
        
        prob += lpSum(objective_terms)
        
        # Constraint 1: Exactly team_size riders
        prob += lpSum(rider_vars[rider] for rider in riders) == self.team_size
        
        # Constraint 2: Total cost <= budget
        cost_terms = []
        for _, row in rider_data.iterrows():
            rider_name = row['rider_name']
            price = row['price']
            cost_terms.append(rider_vars[rider_name] * price)
        prob += lpSum(cost_terms) <= self.budget
        
        # Constraint 3: Minimum riders per team (if specified)
        if min_riders_per_team:
            for team, min_riders in min_riders_per_team.items():
                team_riders = rider_data[rider_data['team'] == team]['rider_name'].tolist()
                if team_riders:
                    prob += lpSum(rider_vars[rider] for rider in team_riders) >= min_riders
        
        # Solve the problem
        prob.solve()
        
        if prob.status != LpStatusOptimal:
            raise ValueError(f"Optimization failed with status: {LpStatus[prob.status]}")
        
        # Extract solution
        selected_riders = []
        total_cost = 0
        total_points = 0
        
        for rider_name in riders:
            if rider_vars[rider_name].value() == 1:
                rider_row = rider_data[rider_data['rider_name'] == rider_name].iloc[0]
                rider_obj = self.rider_db.get_rider(rider_name)
                selected_riders.append(rider_obj)
                total_cost += rider_row['price']
                total_points += rider_row['expected_points']
        
        return TeamSelection(
            riders=selected_riders,
            total_cost=total_cost,
            expected_points=total_points,
            rider_names=[r.name for r in selected_riders]
        )
    
    def optimize_with_stage_selection(self, rider_data: pd.DataFrame,
                                    num_simulations: int = 50) -> TeamSelection:
        """
        Advanced optimization that considers stage-by-stage rider selection.
        This is more complex as it optimizes both team selection and stage selections.
        
        Args:
            rider_data: DataFrame with rider information and expected points
            num_simulations: Number of simulations for stage analysis
            
        Returns:
            TeamSelection object with optimal team
        """
        print("Running advanced optimization with stage selection...")
        
        # First, get stage-by-stage performance data
        stage_performance = self._get_stage_performance_data(num_simulations)
        
        # Create optimization problem
        prob = LpProblem("Advanced_Team_Optimization", LpMaximize)
        
        riders = list(rider_data['rider_name'])
        stages = list(range(1, 23))  # 22 stages
        
        # Decision variables
        # x[i] = 1 if rider i is selected for the team
        rider_vars = LpVariable.dicts("Rider", riders, cat='Binary')
        
        # y[i,j] = 1 if rider i is selected for stage j
        stage_vars = LpVariable.dicts("Stage", 
                                    [(r, s) for r in riders for s in stages], 
                                    cat='Binary')
        
        # Objective: maximize total points across all stages
        objective_terms = []
        for rider in riders:
            for stage in stages:
                if (rider, stage) in stage_performance:
                    points = stage_performance[(rider, stage)]
                    objective_terms.append(stage_vars[(rider, stage)] * points)
        
        prob += lpSum(objective_terms)
        
        # Constraint 1: Exactly team_size riders in team
        prob += lpSum(rider_vars[rider] for rider in riders) == self.team_size
        
        # Constraint 2: Budget constraint
        cost_terms = []
        for _, row in rider_data.iterrows():
            rider_name = row['rider_name']
            price = row['price']
            cost_terms.append(rider_vars[rider_name] * price)
        prob += lpSum(cost_terms) <= self.budget
        
        # Constraint 3: Can only select riders for stages if they're in the team
        for rider in riders:
            for stage in stages:
                prob += stage_vars[(rider, stage)] <= rider_vars[rider]
        
        # Constraint 4: Stage selection limits
        for stage in stages:
            if stage == 22:  # Final stage: all riders
                prob += lpSum(stage_vars[(rider, stage)] for rider in riders) == self.final_stage_riders
            else:  # Regular stages: riders_per_stage
                prob += lpSum(stage_vars[(rider, stage)] for rider in riders) == self.riders_per_stage
        
        # Solve
        prob.solve()
        
        if prob.status != LpStatusOptimal:
            raise ValueError(f"Advanced optimization failed with status: {LpStatus[prob.status]}")
        
        # Extract solution
        selected_riders = []
        total_cost = 0
        total_points = 0
        
        for rider_name in riders:
            if rider_vars[rider_name].value() == 1:
                rider_row = rider_data[rider_data['rider_name'] == rider_name].iloc[0]
                rider_obj = self.rider_db.get_rider(rider_name)
                selected_riders.append(rider_obj)
                total_cost += rider_row['price']
                
                # Calculate total points for this rider across all stages
                rider_stage_points = 0
                for stage in stages:
                    if stage_vars[(rider_name, stage)].value() == 1:
                        if (rider_name, stage) in stage_performance:
                            rider_stage_points += stage_performance[(rider_name, stage)]
                total_points += rider_stage_points
        
        return TeamSelection(
            riders=selected_riders,
            total_cost=total_cost,
            expected_points=total_points,
            rider_names=[r.name for r in selected_riders]
        )
    
    def _get_stage_performance_data(self, num_simulations: int) -> Dict[Tuple[str, int], float]:
        """
        Get expected points for each rider on each stage.
        
        Args:
            num_simulations: Number of simulations to run
            
        Returns:
            Dictionary mapping (rider_name, stage) to expected points
        """
        stage_points = {}
        
        for sim in range(num_simulations):
            if sim % 10 == 0:
                print(f"Stage analysis simulation {sim+1}/{num_simulations}")
            
            # Run simulation and collect stage-by-stage points
            self.simulator.simulate_tour()
            
            # Extract stage points from the records
            stage_records = self.simulator.scorito_points_records
            for record in stage_records:
                rider_name = record['rider']
                stage = record['stage']
                points = record['points']
                
                key = (rider_name, stage)
                if key not in stage_points:
                    stage_points[key] = []
                stage_points[key].append(points)
            
            # Reset simulator
            self.simulator = TourSimulator()
        
        # Calculate expected points for each rider-stage combination
        expected_stage_points = {}
        for key, points_list in stage_points.items():
            expected_stage_points[key] = np.mean(points_list)
        
        return expected_stage_points
    
    def analyze_team_diversity(self, team_selection: TeamSelection) -> Dict:
        """
        Analyze the diversity of the selected team.
        
        Args:
            team_selection: The selected team
            
        Returns:
            Dictionary with diversity metrics
        """
        teams = [r.team for r in team_selection.riders]
        ages = [r.age for r in team_selection.riders]
        
        team_counts = pd.Series(teams).value_counts()
        
        return {
            'unique_teams': len(team_counts),
            'team_distribution': team_counts.to_dict(),
            'avg_age': np.mean(ages),
            'age_std': np.std(ages),
            'min_age': min(ages),
            'max_age': max(ages)
        }
    
    def get_alternative_teams(self, rider_data: pd.DataFrame, 
                            num_alternatives: int = 5) -> List[TeamSelection]:
        """
        Generate alternative team selections by adding constraints.
        
        Args:
            rider_data: DataFrame with rider information
            num_alternatives: Number of alternative teams to generate
            
        Returns:
            List of alternative team selections
        """
        alternatives = []
        
        for i in range(num_alternatives):
            print(f"Generating alternative team {i+1}/{num_alternatives}")
            
            # Add random constraints to get different solutions
            min_riders_per_team = {}
            if i > 0:
                # Require at least 1 rider from some random teams
                teams = rider_data['team'].unique()
                selected_teams = np.random.choice(teams, size=min(3, len(teams)), replace=False)
                for team in selected_teams:
                    min_riders_per_team[team] = 1
            
            try:
                team = self.optimize_team(rider_data, min_riders_per_team=min_riders_per_team)
                alternatives.append(team)
            except ValueError:
                continue
        
        return alternatives

def main():
    """Example usage of the TeamOptimizer."""
    print("Tour de France Team Optimizer")
    print("=" * 40)
    
    # Initialize optimizer
    optimizer = TeamOptimizer(budget=48.0, team_size=20)
    
    # Run simulations to get expected points
    rider_data = optimizer.run_simulation(num_simulations=50)
    
    print(f"\nAnalyzed {len(rider_data)} riders")
    print(f"Average expected points: {rider_data['expected_points'].mean():.2f}")
    print(f"Total budget available: {optimizer.budget}")
    
    # Optimize team
    print("\nOptimizing team selection...")
    optimal_team = optimizer.optimize_team(rider_data)
    
    print(f"\nOptimal Team:")
    print(optimal_team)
    
    # Analyze diversity
    diversity = optimizer.analyze_team_diversity(optimal_team)
    print(f"\nTeam Diversity Analysis:")
    print(f"Unique teams: {diversity['unique_teams']}")
    print(f"Average age: {diversity['avg_age']:.1f}")
    print(f"Age range: {diversity['min_age']}-{diversity['max_age']}")
    
    # Get alternative teams
    print(f"\nGenerating alternative teams...")
    alternatives = optimizer.get_alternative_teams(rider_data, num_alternatives=3)
    
    for i, alt_team in enumerate(alternatives, 1):
        print(f"\nAlternative Team {i}:")
        print(f"Expected Points: {alt_team.expected_points:.2f}")
        print(f"Total Cost: {alt_team.total_cost:.2f}")
        print(f"Riders: {', '.join(alt_team.rider_names)}")
    
    # Save results
    print(f"\nSaving results...")
    results_df = pd.DataFrame({
        'rider_name': optimal_team.rider_names,
        'team': [r.team for r in optimal_team.riders],
        'age': [r.age for r in optimal_team.riders],
        'price': [r.price for r in optimal_team.riders]
    })
    
    results_df.to_excel('optimal_team_selection.xlsx', index=False)
    print("Results saved to 'optimal_team_selection.xlsx'")

if __name__ == "__main__":
    main()
