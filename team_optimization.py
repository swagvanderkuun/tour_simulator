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
    stage_selections: Optional[Dict[int, List[str]]] = None  # stage -> selected riders
    stage_points: Optional[Dict[int, Dict[str, float]]] = None  # stage -> {rider -> points}
    
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
                'age': rider.age,
                'chance_of_abandon': rider.chance_of_abandon
            })
        
        rider_info_df = pd.DataFrame(rider_info)
        
        # Merge with expected points
        final_df = rider_info_df.merge(expected_points, on='rider_name', how='left')
        final_df['expected_points'] = final_df['expected_points'].fillna(0)
        final_df['points_std'] = final_df['points_std'].fillna(0)
        
        return final_df
    
    def optimize_team(self, rider_data: pd.DataFrame, 
                     risk_aversion: float = 0.0,
                     abandon_penalty: float = 1.0,
                     min_riders_per_team: Optional[Dict[str, int]] = None) -> TeamSelection:
        """
        Optimize team selection using Integer Linear Programming.
        
        Args:
            rider_data: DataFrame with rider information and expected points
            risk_aversion: Factor to penalize high variance (0 = no penalty, 1 = high penalty)
            abandon_penalty: Factor to penalize high abandon probability (0 = no penalty, 1 = high penalty)
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
        # If abandon_penalty > 0, penalize high abandon probability
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
                                    num_simulations: int = 50,
                                    risk_aversion: float = 0.0,
                                    abandon_penalty: float = 1.0) -> TeamSelection:
        """
        Advanced optimization that considers stage-by-stage rider selection.
        This is more complex as it optimizes both team selection and stage selections.
        
        Args:
            rider_data: DataFrame with rider information and expected points
            num_simulations: Number of simulations for stage analysis
            risk_aversion: Factor to penalize high variance (0 = no penalty, 1 = high penalty)
            abandon_penalty: Factor to penalize high abandon probability (0 = no penalty, 1 = high penalty)
            
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
                    
                    # Apply risk aversion if specified
                    if risk_aversion > 0:
                        # Get rider's variance from the rider_data
                        rider_row = rider_data[rider_data['rider_name'] == rider]
                        if not rider_row.empty and 'points_std' in rider_row.columns:
                            points_std = rider_row.iloc[0]['points_std']
                            # Risk-adjusted points = expected points - (risk_aversion * standard deviation)
                            points = points - (risk_aversion * points_std)
                    
                    # Apply abandon penalty if specified
                    if abandon_penalty > 0:
                        # Get rider's abandon probability from the rider_data
                        abandon_prob = rider_data[rider_data['rider_name'] == rider].iloc[0]['chance_of_abandon']
                        # Penalize points based on abandon probability
                        points = points * (1 - abandon_penalty * abandon_prob)
                    
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
        stage_selections = {}
        stage_points = {}
        
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
                            points = stage_performance[(rider_name, stage)]
                            rider_stage_points += points
                            
                            # Store stage selections and points
                            if stage not in stage_selections:
                                stage_selections[stage] = []
                                stage_points[stage] = {}
                            stage_selections[stage].append(rider_name)
                            stage_points[stage][rider_name] = points
                
                total_points += rider_stage_points
        
        return TeamSelection(
            riders=selected_riders,
            total_cost=total_cost,
            expected_points=total_points,
            rider_names=[r.name for r in selected_riders],
            stage_selections=stage_selections,
            stage_points=stage_points
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
            
            # Extract stage points from the records and calculate per-stage points
            stage_records = self.simulator.scorito_points_records
            
            # Group records by rider and stage
            rider_stage_points = {}
            for record in stage_records:
                rider_name = record['rider']
                stage = record['stage']
                cumulative_points = record['scorito_points']
                
                if rider_name not in rider_stage_points:
                    rider_stage_points[rider_name] = {}
                rider_stage_points[rider_name][stage] = cumulative_points
            
            # Calculate per-stage points by taking differences
            for rider_name, stage_data in rider_stage_points.items():
                stages = sorted(stage_data.keys())
                for i, stage in enumerate(stages):
                    if i == 0:
                        # First stage: points earned = cumulative points
                        points_earned = stage_data[stage]
                    else:
                        # Other stages: points earned = current cumulative - previous cumulative
                        points_earned = stage_data[stage] - stage_data[stages[i-1]]
                    
                    key = (rider_name, stage)
                    if key not in stage_points:
                        stage_points[key] = []
                    stage_points[key].append(points_earned)
            
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
                team = self.optimize_team(rider_data, min_riders_per_team=min_riders_per_team, abandon_penalty=1.0)
                alternatives.append(team)
            except ValueError:
                continue
        
        return alternatives
    
    def save_results_with_stages(self, team_selection: TeamSelection, 
                                rider_data: pd.DataFrame, 
                                filename: str = 'optimal_team_selection.xlsx'):
        """
        Save team optimization results with multiple tabs including stage-by-stage information.
        
        Args:
            team_selection: The optimal team selection
            rider_data: DataFrame with rider information
            filename: Output filename
        """
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Tab 1: Team Overview
            team_overview = pd.DataFrame({
                'rider_name': team_selection.rider_names,
                'team': [r.team for r in team_selection.riders],
                'age': [r.age for r in team_selection.riders],
                'price': [r.price for r in team_selection.riders]
            })
            team_overview.to_excel(writer, sheet_name='Team_Overview', index=False)
            
            # Tab 2: Summary Statistics
            summary_stats = pd.DataFrame({
                'Metric': ['Total Cost', 'Expected Points', 'Number of Riders', 'Unique Teams'],
                'Value': [
                    f"{team_selection.total_cost:.2f}",
                    f"{team_selection.expected_points:.2f}",
                    len(team_selection.riders),
                    len(set(r.team for r in team_selection.riders))
                ]
            })
            summary_stats.to_excel(writer, sheet_name='Summary', index=False)
            
            # Tab 3: Stage-by-Stage Selections (only selected riders)
            if team_selection.stage_selections:
                stage_data = []
                for stage in sorted(team_selection.stage_selections.keys()):
                    selected_riders = team_selection.stage_selections[stage]
                    stage_points = team_selection.stage_points.get(stage, {})
                    
                    for rider in selected_riders:
                        rider_row = rider_data[rider_data['rider_name'] == rider].iloc[0]
                        stage_data.append({
                            'Stage': stage,
                            'Rider': rider,
                            'Team': rider_row['team'],
                            'Price': rider_row['price'],
                            'Points_Per_Stage': stage_points.get(rider, 0)
                        })
                
                stage_df = pd.DataFrame(stage_data)
                stage_df.to_excel(writer, sheet_name='Stage_Selections', index=False)
            
            # Tab 4: All Riders Per Stage (with selection indicators)
            if team_selection.stage_selections:
                all_stage_data = []
                for stage in sorted(team_selection.stage_selections.keys()):
                    selected_riders = team_selection.stage_selections[stage]
                    stage_points = team_selection.stage_points.get(stage, {})
                    
                    # Get all riders and their points for this stage
                    for _, rider_row in rider_data.iterrows():
                        rider_name = rider_row['rider_name']
                        is_selected = rider_name in selected_riders
                        points = stage_points.get(rider_name, 0)
                        
                        all_stage_data.append({
                            'Stage': stage,
                            'Rider': rider_name,
                            'Team': rider_row['team'],
                            'Age': rider_row['age'],
                            'Price': rider_row['price'],
                            'Points_Per_Stage': points,
                            'Selected': 'Yes' if is_selected else 'No'
                        })
                
                all_stage_df = pd.DataFrame(all_stage_data)
                all_stage_df.to_excel(writer, sheet_name='All_Riders_Per_Stage', index=False)
            
            # Tab 5: Stage Summary
            if team_selection.stage_selections:
                stage_summary = []
                for stage in sorted(team_selection.stage_selections.keys()):
                    selected_riders = team_selection.stage_selections[stage]
                    stage_points = team_selection.stage_points.get(stage, {})
                    total_stage_points = sum(stage_points.values())
                    
                    stage_summary.append({
                        'Stage': stage,
                        'Riders_Selected': len(selected_riders),
                        'Total_Points_Per_Stage': total_stage_points,
                        'Selected_Riders': ', '.join(selected_riders)
                    })
                
                stage_summary_df = pd.DataFrame(stage_summary)
                stage_summary_df.to_excel(writer, sheet_name='Stage_Summary', index=False)
            
            # Tab 6: Teammate Bonus Points Analysis
            if team_selection.stage_selections:
                # Check for high point values that might indicate teammate bonuses
                high_point_riders = []
                for stage in sorted(team_selection.stage_selections.keys()):
                    stage_points = team_selection.stage_points.get(stage, {})
                    for rider, points in stage_points.items():
                        if points > 30:  # Points > 30 might indicate teammate bonuses
                            rider_row = rider_data[rider_data['rider_name'] == rider].iloc[0]
                            high_point_riders.append({
                                'Rider': rider,
                                'Team': rider_row['team'],
                                'Stage': stage,
                                'Points_Per_Stage': points
                            })
                
                if high_point_riders:
                    # Sort by points descending
                    high_point_riders.sort(key=lambda x: x['Points_Per_Stage'], reverse=True)
                    high_points_df = pd.DataFrame(high_point_riders)
                    high_points_df.to_excel(writer, sheet_name='High_Points_Analysis', index=False)
                
                # Team composition analysis
                team_composition = {}
                for rider in team_selection.riders:
                    if rider.team not in team_composition:
                        team_composition[rider.team] = []
                    team_composition[rider.team].append(rider.name)
                
                team_comp_data = []
                for team, riders in sorted(team_composition.items()):
                    team_comp_data.append({
                        'Team': team,
                        'Number_of_Riders': len(riders),
                        'Riders': ', '.join(riders)
                    })
                
                team_comp_df = pd.DataFrame(team_comp_data)
                team_comp_df.to_excel(writer, sheet_name='Team_Composition', index=False)
            
            # Tab 7: All Rider Data
            rider_data.to_excel(writer, sheet_name='All_Riders', index=False)

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
    print("\nOptimizing team selection with stage-by-stage analysis...")
    optimal_team = optimizer.optimize_with_stage_selection(rider_data, num_simulations=50, risk_aversion=0.0, abandon_penalty=1.0)
    
    print(f"\nOptimal Team:")
    print(optimal_team)
    
    # Print stage-by-stage information
    if optimal_team.stage_selections:
        print(f"\nStage-by-Stage Selections:")
        for stage in sorted(optimal_team.stage_selections.keys()):
            selected_riders = optimal_team.stage_selections[stage]
            stage_points = optimal_team.stage_points.get(stage, {})
            total_stage_points = sum(stage_points.values())
            print(f"Stage {stage}: {', '.join(selected_riders)} (Points: {total_stage_points:.2f} per stage)")
        
        print(f"\nDetailed Stage-by-Stage Analysis (Top 15 riders per stage):")
        for stage in sorted(optimal_team.stage_selections.keys()):
            selected_riders = optimal_team.stage_selections[stage]
            stage_points = optimal_team.stage_points.get(stage, {})
            
            # Get all riders with their points for this stage, sorted by points
            all_rider_points = []
            for _, rider_row in rider_data.iterrows():
                rider_name = rider_row['rider_name']
                points = stage_points.get(rider_name, 0)
                is_selected = rider_name in selected_riders
                all_rider_points.append((rider_name, points, is_selected, rider_row['team']))
            
            # Sort by points (descending) and show top 15
            all_rider_points.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\nStage {stage} - Top 15 Expected Points:")
            print(f"{'Rank':<4} {'Rider':<20} {'Team':<15} {'Points':<8} {'Selected':<8}")
            print("-" * 60)
            for i, (rider_name, points, is_selected, team) in enumerate(all_rider_points[:15], 1):
                selected_mark = "✓" if is_selected else ""
                print(f"{i:<4} {rider_name:<20} {team:<15} {points:<8.2f} {selected_mark:<8}")
            
            # Show total points for selected riders
            total_selected_points = sum(points for _, points, is_selected, _ in all_rider_points if is_selected)
            print(f"Total points for selected riders: {total_selected_points:.2f}")
    
    # Analyze diversity
    diversity = optimizer.analyze_team_diversity(optimal_team)
    print(f"\nTeam Diversity Analysis:")
    print(f"Unique teams: {diversity['unique_teams']}")
    print(f"Average age: {diversity['avg_age']:.1f}")
    print(f"Age range: {diversity['min_age']}-{diversity['max_age']}")
    
    # Analyze teammate bonus points impact
    print(f"\nTeammate Bonus Points Analysis:")
    if optimal_team.stage_selections:
        # Check for high point values that might indicate teammate bonuses
        high_point_riders = {}
        for stage in sorted(optimal_team.stage_selections.keys()):
            stage_points = optimal_team.stage_points.get(stage, {})
            for rider, points in stage_points.items():
                if points > 30:  # Points > 30 might indicate teammate bonuses
                    high_point_riders[(rider, stage)] = points
        
        if high_point_riders:
            print("Riders with high per-stage points (likely including teammate bonuses):")
            for (rider, stage), points in sorted(high_point_riders.items(), key=lambda x: x[1], reverse=True)[:10]:
                rider_row = rider_data[rider_data['rider_name'] == rider].iloc[0]
                print(f"  {rider} ({rider_row['team']}) - Stage {stage}: {points:.2f} points")
        else:
            print("No riders with unusually high per-stage points found")
        
        # Check team composition for potential teammate bonus opportunities
        team_composition = {}
        for rider in optimal_team.riders:
            if rider.team not in team_composition:
                team_composition[rider.team] = []
            team_composition[rider.team].append(rider.name)
        
        print(f"\nTeam composition (potential for teammate bonuses):")
        for team, riders in sorted(team_composition.items()):
            print(f"  {team}: {len(riders)} riders - {', '.join(riders)}")
    
    # Get alternative teams (using basic optimization for alternatives)
    print(f"\nGenerating alternative teams...")
    alternatives = optimizer.get_alternative_teams(rider_data, num_alternatives=3)
    
    for i, alt_team in enumerate(alternatives, 1):
        print(f"\nAlternative Team {i}:")
        print(f"Expected Points: {alt_team.expected_points:.2f}")
        print(f"Total Cost: {alt_team.total_cost:.2f}")
        print(f"Riders: {', '.join(alt_team.rider_names)}")
    
    # Save results
    print(f"\nSaving results...")
    optimizer.save_results_with_stages(optimal_team, rider_data)
    print("Results saved to 'optimal_team_selection.xlsx'")

if __name__ == "__main__":
    main()
