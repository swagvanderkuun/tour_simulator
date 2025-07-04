import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from simulator import TourSimulator
from riders import RiderDatabase, Rider
from team_optimization import TeamOptimizer, TeamSelection
from datetime import datetime
from pulp import *
import warnings
import time
warnings.filterwarnings('ignore')

@dataclass
class UserTeam:
    """Represents a user-selected team."""
    riders: List[Rider]
    total_cost: float
    rider_names: List[str]
    stage_selections: Optional[Dict[int, List[str]]] = None
    stage_points: Optional[Dict[int, Dict[str, float]]] = None
    simulation_results: Optional[List[Dict]] = None
    
    def __str__(self):
        return f"User Team:\n" \
               f"Total Cost: {self.total_cost:.2f}\n" \
               f"Riders: {', '.join(self.rider_names)}"

class VersusMode:
    """
    Versus Mode allows users to select a team and compare it against the optimal team.
    
    Features:
    - Team selection with budget constraint (48 points, 20 riders)
    - Multiple simulations with stage-by-stage optimization
    - Comparison against optimal team from team optimization
    - Detailed stage-by-stage analysis
    """
    
    def __init__(self, budget: float = 48.0, team_size: int = 20, 
                 riders_per_stage: int = 9, final_stage_riders: int = 20):
        self.budget = budget
        self.team_size = team_size
        self.riders_per_stage = riders_per_stage
        self.final_stage_riders = final_stage_riders
        self.rider_db = RiderDatabase()
        self.team_optimizer = TeamOptimizer(budget, team_size, riders_per_stage, final_stage_riders)
        
    def get_available_riders(self) -> pd.DataFrame:
        """
        Get all available riders with their information.
        
        Returns:
            DataFrame with rider information
        """
        riders_data = []
        for rider in self.rider_db.get_all_riders():
            riders_data.append({
                'name': rider.name,
                'team': rider.team,
                'age': rider.age,
                'price': rider.price,
                'sprint_ability': rider.parameters.sprint_ability,
                'punch_ability': rider.parameters.punch_ability,
                'itt_ability': rider.parameters.itt_ability,
                'mountain_ability': rider.parameters.mountain_ability,
                'break_away_ability': rider.parameters.break_away_ability,
                'chance_of_abandon': rider.chance_of_abandon
            })
        
        df = pd.DataFrame(riders_data)
        df = df.sort_values(['team', 'name'])
        return df
    
    def validate_team_selection(self, selected_rider_names: List[str]) -> Tuple[bool, str]:
        """
        Validate if the selected team meets all constraints.
        
        Args:
            selected_rider_names: List of selected rider names
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(selected_rider_names) != self.team_size:
            return False, f"Team must have exactly {self.team_size} riders. You selected {len(selected_rider_names)}."
        
        # Check budget constraint
        total_cost = 0
        team_counts = {}
        
        for rider_name in selected_rider_names:
            rider = self.rider_db.get_rider(rider_name)
            if not rider:
                return False, f"Rider '{rider_name}' not found in database."
            
            total_cost += rider.price
            
            # Count riders per team
            if rider.team not in team_counts:
                team_counts[rider.team] = 0
            team_counts[rider.team] += 1
        
        if total_cost > self.budget:
            return False, f"Team cost ({total_cost:.2f}) exceeds budget ({self.budget})."
        
        # Check maximum 4 riders per team
        for team, count in team_counts.items():
            if count > 4:
                return False, f"Team '{team}' has {count} riders. Maximum allowed is 4."
        
        return True, "Team selection is valid."
    
    def create_user_team(self, selected_rider_names: List[str]) -> UserTeam:
        """
        Create a UserTeam object from selected rider names.
        
        Args:
            selected_rider_names: List of selected rider names
            
        Returns:
            UserTeam object
        """
        riders = []
        total_cost = 0
        
        for rider_name in selected_rider_names:
            rider = self.rider_db.get_rider(rider_name)
            riders.append(rider)
            total_cost += rider.price
        
        return UserTeam(
            riders=riders,
            total_cost=total_cost,
            rider_names=selected_rider_names
        )
    
    def optimize_stage_selection(self, user_team: UserTeam, 
                               rider_data: pd.DataFrame,
                               num_simulations: int = 50) -> UserTeam:
        """
        Optimize stage selection for the user's team.
        
        Args:
            user_team: User's team
            rider_data: DataFrame with rider performance data
            num_simulations: Number of simulations for stage analysis
            
        Returns:
            Updated UserTeam with stage selections
        """
        # Get stage performance data for all riders
        stage_performance = self.team_optimizer._get_stage_performance_data(num_simulations)
        
        # Create optimization problem for stage selection only
        prob = LpProblem("User_Team_Stage_Optimization", LpMaximize)
        
        stages = list(range(1, 23))  # 22 stages
        
        # Decision variables: y[i,j] = 1 if rider i is selected for stage j
        stage_vars = LpVariable.dicts("Stage", 
                                    [(r, s) for r in user_team.rider_names for s in stages], 
                                    cat='Binary')
        
        # Objective: maximize total points across all stages
        objective_terms = []
        for rider in user_team.rider_names:
            for stage in stages:
                if (rider, stage) in stage_performance:
                    points = stage_performance[(rider, stage)]
                    objective_terms.append(stage_vars[(rider, stage)] * points)
        
        prob += lpSum(objective_terms)
        
        # Constraint: Stage selection limits
        for stage in stages:
            if stage == 22:  # Final stage: all riders
                prob += lpSum(stage_vars[(rider, stage)] for rider in user_team.rider_names) == self.final_stage_riders
            else:  # Regular stages: riders_per_stage
                prob += lpSum(stage_vars[(rider, stage)] for rider in user_team.rider_names) == self.riders_per_stage
        
        # Solve
        prob.solve()
        
        if prob.status != LpStatusOptimal:
            return user_team
        
        # Extract solution
        stage_selections = {}
        stage_points = {}
        
        for rider in user_team.rider_names:
            for stage in stages:
                if stage_vars[(rider, stage)].value() == 1:
                    if stage not in stage_selections:
                        stage_selections[stage] = []
                        stage_points[stage] = {}
                    stage_selections[stage].append(rider)
                    
                    if (rider, stage) in stage_performance:
                        stage_points[stage][rider] = stage_performance[(rider, stage)]
                    else:
                        stage_points[stage][rider] = 0
        
        user_team.stage_selections = stage_selections
        user_team.stage_points = stage_points
        
        return user_team
    
    def run_user_team_simulations(self, user_team: UserTeam, 
                                num_simulations: int = 100) -> List[Dict]:
        """
        Run multiple simulations with the user's team.
        
        Args:
            user_team: User's team
            num_simulations: Number of simulations to run
            
        Returns:
            List of simulation results
        """
        simulation_results = []
        
        for i in range(num_simulations):
            # Create a new simulator for this simulation
            simulator = TourSimulator()
            simulator.rider_db = self.rider_db  # Ensure rider database is set
            
            # Run simulation
            simulator.simulate_tour()
            
            # Calculate total points for user's team using stage-by-stage selection
            # This is the CORRECT way - only count points from riders selected for each stage
            team_points = 0
            
            if user_team.stage_selections:
                # Use the optimized stage selections and calculate stage-specific points
                for stage, selected_riders in user_team.stage_selections.items():
                    stage_points = 0
                    for rider_name in selected_riders:
                        if rider_name in simulator.scorito_points:
                            # Calculate points earned on this specific stage
                            # We need to extract stage-specific points from the simulation records
                            rider_stage_points = self._get_rider_stage_points(simulator, rider_name, stage)
                            stage_points += rider_stage_points
                    team_points += stage_points
            else:
                # Fallback: if no stage selections, use a more accurate approximation
                # Calculate what the optimal stage selection would be for this simulation
                optimal_stage_points = self._calculate_optimal_stage_points_for_simulation(
                    simulator, user_team.rider_names
                )
                team_points = optimal_stage_points
            
            simulation_results.append({
                'simulation': i + 1,
                'team_points': team_points,
                'rider_points': {name: simulator.scorito_points.get(name, 0) 
                               for name in user_team.rider_names}
            })
        
        user_team.simulation_results = simulation_results
        return simulation_results
    
    def _get_rider_stage_points(self, simulator, rider_name: str, stage: int) -> float:
        """
        Get the points earned by a rider on a specific stage from simulation records.
        
        Args:
            simulator: TourSimulator instance that has completed a simulation
            rider_name: Name of the rider
            stage: Stage number
            
        Returns:
            Points earned on the specific stage
        """
        # Extract stage points from the simulation records
        stage_records = simulator.scorito_points_records
        
        # Find records for this rider
        rider_records = [r for r in stage_records if r['rider'] == rider_name]
        
        if not rider_records:
            return 0.0
        
        # Find the record for this specific stage
        stage_record = None
        for record in rider_records:
            if record['stage'] == stage:
                stage_record = record
                break
        
        if not stage_record:
            return 0.0
        
        # Calculate points earned on this stage
        cumulative_points = stage_record['scorito_points']
        
        if stage == 1:
            # First stage: points earned = cumulative points
            return cumulative_points
        else:
            # Find the previous stage's cumulative points
            prev_stage_record = None
            for record in rider_records:
                if record['stage'] == stage - 1:
                    prev_stage_record = record
                    break
            
            if prev_stage_record:
                # Points earned = current cumulative - previous cumulative
                return cumulative_points - prev_stage_record['scorito_points']
            else:
                # Fallback: distribute evenly across 21 stages (not 22)
                return cumulative_points / 21
    
    def _calculate_optimal_stage_points_for_simulation(self, simulator, rider_names: List[str]) -> float:
        """
        Calculate optimal stage selection points for a given simulation.
        This is used as a fallback when no stage selections are available.
        
        Args:
            simulator: TourSimulator instance that has completed a simulation
            rider_names: List of rider names in the team
            
        Returns:
            Total points with optimal stage selection
        """
        total_points = 0
        
        # For each stage, select the best 9 riders (or all 20 for final stage)
        for stage in range(1, 22):  # Tour has 21 stages, not 22
            if stage == 21:
                # Final stage: all 20 riders
                selected_riders = rider_names
            else:
                # Regular stages: select best 9 riders
                rider_stage_points = []
                for rider_name in rider_names:
                    if rider_name in simulator.scorito_points:
                        stage_points = self._get_rider_stage_points(simulator, rider_name, stage)
                        rider_stage_points.append((rider_name, stage_points))
                
                # Sort by stage points and select top 9
                rider_stage_points.sort(key=lambda x: x[1], reverse=True)
                selected_riders = [rider for rider, _ in rider_stage_points[:9]]
            
            # Sum points for selected riders on this stage
            stage_points = 0
            for rider_name in selected_riders:
                if rider_name in simulator.scorito_points:
                    stage_points += self._get_rider_stage_points(simulator, rider_name, stage)
            
            total_points += stage_points
        
        return total_points
    
    def get_optimal_team(self, num_simulations: int = 50, metric: str = 'mean') -> TeamSelection:
        """
        Get the optimal team using the team optimizer.
        
        Args:
            num_simulations: Number of simulations for optimization
            metric: Metric to use for expected points ('mean', 'median', 'mode')
            
        Returns:
            Optimal team selection
        """
        # Run simulations to get expected points
        rider_data = self.team_optimizer.run_simulation(num_simulations, metric=metric)
        
        # Optimize team with stage selection
        optimal_team = self.team_optimizer.optimize_with_stage_selection(
            rider_data, num_simulations, risk_aversion=0.0, abandon_penalty=1.0
        )
        
        return optimal_team
    
    def compare_teams(self, user_team: UserTeam, optimal_team: TeamSelection, 
                     user_simulation_results: List[Dict] = None, 
                     optimal_simulation_results: List[Dict] = None) -> Dict:
        """
        Compare user team with optimal team using the same analysis methods as Team Optimization.
        
        Args:
            user_team: User's team
            optimal_team: Optimal team
            user_simulation_results: User team simulation results (optional)
            optimal_simulation_results: Optimal team simulation results (optional)
            
        Returns:
            Dictionary with comparison results
        """
        # Use the same rider data and analysis methods as Team Optimization
        rider_data = self.team_optimizer.run_simulation_with_teammate_analysis(100, metric='mean')
        
        # Get stage performance data using the same method as Team Optimization
        stage_performance = self.team_optimizer._get_stage_performance_data(50)
        
        # Calculate user team metrics using Team Optimization methods
        user_team_metrics = self._calculate_team_metrics_using_optimizer_methods(
            user_team, rider_data, stage_performance
        )
        
        # Calculate optimal team metrics using Team Optimization methods
        optimal_team_metrics = self._calculate_team_metrics_using_optimizer_methods(
            optimal_team, rider_data, stage_performance
        )
        
        # Calculate comparison metrics
        cost_difference = user_team_metrics['total_cost'] - optimal_team_metrics['total_cost']
        performance_difference = user_team_metrics['expected_points'] - optimal_team_metrics['expected_points']
        
        # Calculate efficiency metrics
        user_efficiency = user_team_metrics['expected_points'] / user_team_metrics['total_cost'] if user_team_metrics['total_cost'] > 0 else 0
        optimal_efficiency = optimal_team_metrics['expected_points'] / optimal_team_metrics['total_cost'] if optimal_team_metrics['total_cost'] > 0 else 0
        efficiency_difference = user_efficiency - optimal_efficiency
        
        comparison = {
            'user_team': user_team_metrics,
            'optimal_team': optimal_team_metrics,
            'comparison': {
                'cost_difference': cost_difference,
                'performance_difference': performance_difference,
                'efficiency_difference': efficiency_difference,
                'user_efficiency': user_efficiency,
                'optimal_efficiency': optimal_efficiency
            }
        }
        
        return comparison
    
    def _calculate_team_metrics_using_optimizer_methods(self, team, rider_data: pd.DataFrame, 
                                                       stage_performance: Dict) -> Dict:
        """
        Calculate team metrics using the same methods as Team Optimization.
        
        Args:
            team: Team to analyze (UserTeam or TeamSelection)
            rider_data: DataFrame with rider information from Team Optimization
            stage_performance: Stage performance data from Team Optimization
            
        Returns:
            Dictionary with team metrics
        """
        # Get team riders and names
        if hasattr(team, 'riders'):
            team_riders = team.riders
            team_names = team.rider_names
        else:
            team_riders = [self.rider_db.get_rider(name) for name in team.rider_names]
            team_names = team.rider_names
        
        # Calculate total cost
        total_cost = sum(rider.price for rider in team_riders)
        
        # Calculate expected points using Team Optimization data
        expected_points = 0
        rider_expected_points = {}
        
        for rider_name in team_names:
            rider_row = rider_data[rider_data['rider_name'] == rider_name]
            if not rider_row.empty:
                rider_exp_points = rider_row.iloc[0]['expected_points']
                expected_points += rider_exp_points
                rider_expected_points[rider_name] = rider_exp_points
            else:
                rider_expected_points[rider_name] = 0
        
        # Calculate stage-by-stage points using Team Optimization data
        stage_points = {}
        if hasattr(team, 'stage_selections') and team.stage_selections:
            for stage in range(1, 23):
                stage_points[stage] = {}
                selected_riders = team.stage_selections.get(stage, [])
                for rider_name in team_names:
                    if rider_name in selected_riders:
                        rider_stage_points = stage_performance.get((rider_name, stage), 0)
                        stage_points[stage][rider_name] = rider_stage_points
                    else:
                        stage_points[stage][rider_name] = 0
        
        # Calculate team diversity using Team Optimization method
        team_diversity = self.team_optimizer.analyze_team_diversity(team)
        
        # Calculate team diagnostics manually to avoid AttributeError
        # (since get_team_diagnostics expects TeamSelection object)
        team_diagnostics = {
            'team_size': len(team_riders),
            'total_cost': total_cost,
            'expected_points': expected_points,
            'cost_efficiency': expected_points / total_cost if total_cost > 0 else 0,
            'budget_utilization': total_cost / self.team_optimizer.budget,
            'team_composition': {},
            'risk_metrics': {},
            'abandon_risk': 0.0
        }
        
        # Team composition analysis
        teams = [r.team for r in team_riders]
        team_counts = pd.Series(teams).value_counts()
        team_diagnostics['team_composition'] = {
            'unique_teams': len(team_counts),
            'team_distribution': team_counts.to_dict(),
            'teammate_bonus_potential': len([team for team, count in team_counts.items() if count >= 2])
        }
        
        # Risk metrics
        total_std = 0
        total_abandon_risk = 0
        
        for rider in team_riders:
            rider_row = rider_data[rider_data['rider_name'] == rider.name]
            if not rider_row.empty:
                total_std += rider_row.iloc[0]['points_std'] ** 2
                total_abandon_risk += rider.chance_of_abandon
        
        team_diagnostics['risk_metrics'] = {
            'total_std': total_std ** 0.5,
            'avg_std_per_rider': (total_std ** 0.5) / len(team_riders),
            'risk_percentage': (total_std ** 0.5) / expected_points if expected_points > 0 else 0
        }
        
        team_diagnostics['abandon_risk'] = total_abandon_risk / len(team_riders)
        
        # Create result dictionary
        result = {
            'total_cost': total_cost,
            'expected_points': expected_points,
            'rider_count': len(team_riders),
            'rider_names': team_names,
            'rider_expected_points': rider_expected_points,
            'stage_points': stage_points,
            'stage_performance_data': stage_performance,  # Include stage performance data
            'team_diversity': team_diversity,
            'team_diagnostics': team_diagnostics,
            'avg_simulation_points': expected_points,  # Use expected points as simulation average
            'simulation_std': 0  # Will be calculated if needed
        }
        
        # Also attach stage_performance_data to the team object for dashboard access
        if hasattr(team, 'stage_performance_data'):
            team.stage_performance_data = stage_performance
        else:
            # For UserTeam objects, add the attribute
            setattr(team, 'stage_performance_data', stage_performance)
        
        return result
    
    def save_versus_results(self, user_team: UserTeam, optimal_team: TeamSelection,
                          comparison: Dict, rider_data: pd.DataFrame,
                          filename: str = None) -> str:
        """
        Save versus mode results to Excel file using Team Optimization analysis methods.
        
        Args:
            user_team: User's team
            optimal_team: Optimal team
            comparison: Comparison results
            rider_data: Rider performance data from Team Optimization
            filename: Output filename
            
        Returns:
            Filename of saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"versus_mode_results_{timestamp}.xlsx"
        
        # Get stage performance data using the same method as Team Optimization
        stage_performance = self.team_optimizer._get_stage_performance_data(50)
        
        with pd.ExcelWriter(filename) as writer:
            # Sheet 1: Team Comparison Summary
            summary_data = [
                ['Metric', 'User Team', 'Optimal Team', 'Difference'],
                ['Total Cost', comparison['user_team']['total_cost'], 
                 comparison['optimal_team']['total_cost'], 
                 comparison['comparison']['cost_difference']],
                ['Number of Riders', comparison['user_team']['rider_count'], 
                 comparison['optimal_team']['rider_count'], 
                 comparison['user_team']['rider_count'] - comparison['optimal_team']['rider_count']],
                ['Expected Points', comparison['user_team']['expected_points'], 
                 comparison['optimal_team']['expected_points'], 
                 comparison['comparison']['performance_difference']],
                ['Efficiency (Points/Cost)', comparison['comparison']['user_efficiency'], 
                 comparison['comparison']['optimal_efficiency'], 
                 comparison['comparison']['efficiency_difference']],
                ['Unique Teams', comparison['user_team']['team_diversity']['unique_teams'], 
                 comparison['optimal_team']['team_diversity']['unique_teams'], 
                 comparison['user_team']['team_diversity']['unique_teams'] - comparison['optimal_team']['team_diversity']['unique_teams']],
                ['Average Age', comparison['user_team']['team_diversity']['avg_age'], 
                 comparison['optimal_team']['team_diversity']['avg_age'], 
                 comparison['user_team']['team_diversity']['avg_age'] - comparison['optimal_team']['team_diversity']['avg_age']]
            ]
            
            summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            summary_df.to_excel(writer, sheet_name='Team_Comparison', index=False)
            
            # Sheet 2: Rider Comparison
            rider_comparison = []
            all_riders = set(user_team.rider_names + optimal_team.rider_names)
            
            for rider_name in sorted(all_riders):
                in_user = rider_name in user_team.rider_names
                in_optimal = rider_name in optimal_team.rider_names
                
                # Get rider info from Team Optimization data
                rider_info = rider_data[rider_data['rider_name'] == rider_name]
                if not rider_info.empty:
                    rider_row = rider_info.iloc[0]
                    rider_comparison.append({
                        'Rider': rider_name,
                        'Team': rider_row['team'],
                        'Age': rider_row['age'],
                        'Price': rider_row['price'],
                        'Expected_Points': rider_row['expected_points'],
                        'Points_Std': rider_row['points_std'],
                        'Teammate_Bonus_Potential': rider_row['teammate_bonus_potential'],
                        'Expected_Points_With_Bonus': rider_row['expected_points_with_teammate_bonus'],
                        'Chance_of_Abandon': rider_row['chance_of_abandon'],
                        'In_User_Team': 'Yes' if in_user else 'No',
                        'In_Optimal_Team': 'Yes' if in_optimal else 'No',
                        'Selection': 'Both' if in_user and in_optimal else 
                                   ('User Only' if in_user else 'Optimal Only')
                    })
            
            rider_comp_df = pd.DataFrame(rider_comparison)
            rider_comp_df.to_excel(writer, sheet_name='Rider_Comparison', index=False)
            
            # Sheet 3: Team Diversity Analysis
            diversity_data = []
            for team_type, team_data in [('User Team', comparison['user_team']), ('Optimal Team', comparison['optimal_team'])]:
                diversity = team_data['team_diversity']
                diversity_data.append({
                    'Team_Type': team_type,
                    'Unique_Teams': diversity['unique_teams'],
                    'Average_Age': diversity['avg_age'],
                    'Age_Std': diversity['age_std'],
                    'Min_Age': diversity['min_age'],
                    'Max_Age': diversity['max_age']
                })
            
            diversity_df = pd.DataFrame(diversity_data)
            diversity_df.to_excel(writer, sheet_name='Team_Diversity', index=False)
            
            # Sheet 4: Team Composition Analysis
            composition_data = []
            for team_type, team_data in [('User Team', comparison['user_team']), ('Optimal Team', comparison['optimal_team'])]:
                team_composition = {}
                for rider_name in team_data['rider_names']:
                    rider = self.rider_db.get_rider(rider_name)
                    if rider.team not in team_composition:
                        team_composition[rider.team] = []
                    team_composition[rider.team].append(rider_name)
                
                for team, riders in sorted(team_composition.items()):
                    composition_data.append({
                        'Team_Type': team_type,
                        'Team': team,
                        'Number_of_Riders': len(riders),
                        'Riders': ', '.join(riders)
                    })
            
            composition_df = pd.DataFrame(composition_data)
            composition_df.to_excel(writer, sheet_name='Team_Composition', index=False)
            
            # Sheet 5: Stage-by-Stage Comparison
            if user_team.stage_selections and optimal_team.stage_selections:
                stage_comparison = []
                
                # Calculate total team points per stage using Team Optimization data
                for stage in range(1, 23):
                    # User team stage points - sum selected riders' stage performance
                    user_stage_points = 0
                    selected_riders = user_team.stage_selections.get(stage, [])
                    for rider_name in selected_riders:
                        if (rider_name, stage) in stage_performance:
                            user_stage_points += stage_performance[(rider_name, stage)]
                    
                    # Optimal team stage points - sum selected riders' stage performance
                    optimal_stage_points = 0
                    selected_riders = optimal_team.stage_selections.get(stage, [])
                    for rider_name in selected_riders:
                        if (rider_name, stage) in stage_performance:
                            optimal_stage_points += stage_performance[(rider_name, stage)]
                    
                    stage_comparison.append({
                        'Stage': stage,
                        'User_Team_Points': user_stage_points,
                        'Optimal_Team_Points': optimal_stage_points,
                        'Difference': user_stage_points - optimal_stage_points
                    })
                
                stage_comp_df = pd.DataFrame(stage_comparison)
                stage_comp_df.to_excel(writer, sheet_name='Stage_Comparison', index=False)
                
                # Sheet 6: Detailed Stage-by-Stage Rider Performance
                detailed_stage_data = []
                for stage in range(1, 23):
                    # User team riders for this stage
                    user_riders = user_team.stage_selections.get(stage, [])
                    
                    for rider in user_riders:
                        # Use the same stage performance data as Team Optimization
                        rider_stage_points = stage_performance.get((rider, stage), 0)
                        detailed_stage_data.append({
                            'Stage': stage,
                            'Team_Type': 'User_Team',
                            'Rider': rider,
                            'Points_Per_Stage': rider_stage_points,
                            'Selected': 'Yes'
                        })
                    
                    # User team riders not selected for this stage
                    for rider in user_team.rider_names:
                        if rider not in user_riders:
                            detailed_stage_data.append({
                                'Stage': stage,
                                'Team_Type': 'User_Team',
                                'Rider': rider,
                                'Points_Per_Stage': 0,  # Not selected, so 0 points
                                'Selected': 'No'
                            })
                    
                    # Optimal team riders for this stage
                    optimal_riders = optimal_team.stage_selections.get(stage, [])
                    
                    for rider in optimal_riders:
                        # Use the same stage performance data as Team Optimization
                        rider_stage_points = stage_performance.get((rider, stage), 0)
                        detailed_stage_data.append({
                            'Stage': stage,
                            'Team_Type': 'Optimal_Team',
                            'Rider': rider,
                            'Points_Per_Stage': rider_stage_points,
                            'Selected': 'Yes'
                        })
                    
                    # Optimal team riders not selected for this stage
                    for rider in optimal_team.rider_names:
                        if rider not in optimal_riders:
                            detailed_stage_data.append({
                                'Stage': stage,
                                'Team_Type': 'Optimal_Team',
                                'Rider': rider,
                                'Points_Per_Stage': 0,  # Not selected, so 0 points
                                'Selected': 'No'
                            })
                
                detailed_stage_df = pd.DataFrame(detailed_stage_data)
                detailed_stage_df.to_excel(writer, sheet_name='Detailed_Stage_Performance', index=False)
                
                # Sheet 7: Rider Stage Performance Summary
                rider_stage_summary = []
                
                # Get all unique riders from both teams
                all_riders = set(user_team.rider_names + optimal_team.rider_names)
                
                for rider in all_riders:
                    # Calculate average points per stage for this rider using Team Optimization data
                    total_stage_points = 0
                    stages_counted = 0
                    
                    # Check user team stage selections
                    for stage in range(1, 23):
                        if rider in user_team.stage_selections.get(stage, []):
                            rider_stage_points = stage_performance.get((rider, stage), 0)
                            total_stage_points += rider_stage_points
                            stages_counted += 1
                    
                    # Check optimal team stage selections
                    for stage in range(1, 23):
                        if rider in optimal_team.stage_selections.get(stage, []):
                            rider_stage_points = stage_performance.get((rider, stage), 0)
                            total_stage_points += rider_stage_points
                            stages_counted += 1
                    
                    # Calculate averages
                    avg_points_per_stage = total_stage_points / stages_counted if stages_counted > 0 else 0
                    total_points = total_stage_points
                    
                    # Determine which team(s) this rider belongs to
                    in_user_team = rider in user_team.rider_names
                    in_optimal_team = rider in optimal_team.rider_names
                    
                    if in_user_team and in_optimal_team:
                        team_type = 'Both'
                    elif in_user_team:
                        team_type = 'User_Only'
                    else:
                        team_type = 'Optimal_Only'
                    
                    rider_stage_summary.append({
                        'Rider': rider,
                        'Team_Type': team_type,
                        'Total_Stage_Points': total_points,
                        'Stages_Selected': stages_counted,
                        'Avg_Points_Per_Stage': avg_points_per_stage,
                        'In_User_Team': in_user_team,
                        'In_Optimal_Team': in_optimal_team
                    })
                
                # Sort by average points per stage
                rider_summary_df = pd.DataFrame(rider_stage_summary)
                rider_summary_df = rider_summary_df.sort_values('Avg_Points_Per_Stage', ascending=False)
                rider_summary_df.to_excel(writer, sheet_name='Rider_Stage_Summary', index=False)
            
            # Sheet 8: All Rider Data (from Team Optimization)
            rider_data.to_excel(writer, sheet_name='All_Riders', index=False)
        
        return filename
    
    def calculate_individual_rider_sum(self, user_team: UserTeam, rider_data: pd.DataFrame) -> float:
        """
        Calculate the sum of individual rider expected points for comparison.
        This represents the theoretical maximum if all riders could be selected every stage.
        
        Args:
            user_team: User's team
            rider_data: DataFrame with rider performance data
            
        Returns:
            Sum of individual rider expected points
        """
        total_sum = 0.0
        for rider_name in user_team.rider_names:
            rider_row = rider_data[rider_data['rider_name'] == rider_name]
            if not rider_row.empty:
                total_sum += rider_row.iloc[0]['expected_points']
        return total_sum
    
    def calculate_bench_points_analysis(self, user_team: UserTeam, optimal_team: TeamSelection, rider_data: pd.DataFrame) -> Dict:
        """
        Calculate bench points analysis for both user team and optimal team.
        
        Args:
            user_team: User's team
            optimal_team: Optimal team
            rider_data: DataFrame with rider performance data
            
        Returns:
            Dictionary with bench points analysis
        """
        analysis = {
            'user_team': {
                'total_selected_points': 0,
                'total_bench_points': 0,
                'selection_efficiency': 0,
                'stage_breakdown': [],
                'top_bench_performers': []
            },
            'optimal_team': {
                'total_selected_points': 0,
                'total_bench_points': 0,
                'selection_efficiency': 0,
                'stage_breakdown': [],
                'top_bench_performers': []
            }
        }
        
        # Analyze user team bench points
        if user_team.stage_selections:
            user_total_selected = 0
            user_total_bench = 0
            user_stage_breakdown = []
            user_bench_totals = {}
            
            for stage in sorted(user_team.stage_selections.keys()):
                selected_riders = user_team.stage_selections[stage]
                stage_points = user_team.stage_points.get(stage, {})
                
                # Calculate selected points from stage selections
                selected_points = sum(stage_points.get(rider, 0) for rider in selected_riders)
                
                # Calculate bench points using actual stage performance data
                bench_points = 0
                for rider in user_team.rider_names:
                    if rider not in selected_riders:
                        # Use actual stage performance data if available
                        if hasattr(user_team, 'stage_performance_data') and (rider, stage) in user_team.stage_performance_data:
                            stage_expected_points = user_team.stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to estimated approach if stage data not available
                            rider_row = rider_data[rider_data['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                # Estimate stage-specific points based on total expected points
                                # Different stages have different point distributions
                                if stage <= 21:  # Regular stages
                                    # Most riders score points on regular stages, but not huge amounts
                                    # Estimate 3-8% of total expected points per stage
                                    stage_factor = 0.05  # 5% of total expected points per stage
                                else:  # Final stage (stage 22)
                                    # Final stage often has more points available
                                    stage_factor = 0.08  # 8% of total expected points
                                
                                stage_expected_points = total_expected_points * stage_factor
                            else:
                                stage_expected_points = 0
                        
                        bench_points += stage_expected_points
                        
                        # Track bench points per rider
                        if rider not in user_bench_totals:
                            user_bench_totals[rider] = 0
                        user_bench_totals[rider] += stage_expected_points
                
                user_total_selected += selected_points
                user_total_bench += bench_points
                
                user_stage_breakdown.append({
                    'stage': stage,
                    'selected_points': selected_points,
                    'bench_points': bench_points,
                    'total_stage_points': selected_points + bench_points,
                    'selection_efficiency': selected_points / (selected_points + bench_points) if (selected_points + bench_points) > 0 else 0
                })
            
            # Create top bench performers list for user team
            user_top_bench = []
            for rider, total_bench_points in user_bench_totals.items():
                if total_bench_points > 0:
                    rider_obj = next((r for r in user_team.riders if r.name == rider), None)
                    user_top_bench.append({
                        'rider': rider,
                        'team': rider_obj.team if rider_obj else 'Unknown',
                        'total_bench_points': total_bench_points,
                        'average_bench_points': total_bench_points / len(user_team.stage_selections)
                    })
            
            user_top_bench.sort(key=lambda x: x['total_bench_points'], reverse=True)
            
            analysis['user_team'].update({
                'total_selected_points': user_total_selected,
                'total_bench_points': user_total_bench,
                'selection_efficiency': user_total_selected / (user_total_selected + user_total_bench) if (user_total_selected + user_total_bench) > 0 else 0,
                'stage_breakdown': user_stage_breakdown,
                'top_bench_performers': user_top_bench
            })
        
        # Analyze optimal team bench points
        if optimal_team.stage_selections:
            optimal_total_selected = 0
            optimal_total_bench = 0
            optimal_stage_breakdown = []
            optimal_bench_totals = {}
            
            for stage in sorted(optimal_team.stage_selections.keys()):
                selected_riders = optimal_team.stage_selections[stage]
                stage_points = optimal_team.stage_points.get(stage, {})
                
                # Calculate selected points from stage selections
                selected_points = sum(stage_points.get(rider, 0) for rider in selected_riders)
                
                # Calculate bench points using actual stage performance data
                bench_points = 0
                for rider in optimal_team.rider_names:
                    if rider not in selected_riders:
                        # Use actual stage performance data if available
                        if hasattr(optimal_team, 'stage_performance_data') and (rider, stage) in optimal_team.stage_performance_data:
                            stage_expected_points = optimal_team.stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to estimated approach if stage data not available
                            rider_row = rider_data[rider_data['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                # Estimate stage-specific points based on total expected points
                                # Different stages have different point distributions
                                if stage <= 21:  # Regular stages
                                    # Most riders score points on regular stages, but not huge amounts
                                    # Estimate 3-8% of total expected points per stage
                                    stage_factor = 0.05  # 5% of total expected points per stage
                                else:  # Final stage (stage 22)
                                    # Final stage often has more points available
                                    stage_factor = 0.08  # 8% of total expected points
                                
                                stage_expected_points = total_expected_points * stage_factor
                            else:
                                stage_expected_points = 0
                        
                        bench_points += stage_expected_points
                        
                        # Track bench points per rider
                        if rider not in optimal_bench_totals:
                            optimal_bench_totals[rider] = 0
                        optimal_bench_totals[rider] += stage_expected_points
                
                optimal_total_selected += selected_points
                optimal_total_bench += bench_points
                
                optimal_stage_breakdown.append({
                    'stage': stage,
                    'selected_points': selected_points,
                    'bench_points': bench_points,
                    'total_stage_points': selected_points + bench_points,
                    'selection_efficiency': selected_points / (selected_points + bench_points) if (selected_points + bench_points) > 0 else 0
                })
            
            # Create top bench performers list for optimal team
            optimal_top_bench = []
            for rider, total_bench_points in optimal_bench_totals.items():
                if total_bench_points > 0:
                    rider_obj = next((r for r in optimal_team.riders if r.name == rider), None)
                    optimal_top_bench.append({
                        'rider': rider,
                        'team': rider_obj.team if rider_obj else 'Unknown',
                        'total_bench_points': total_bench_points,
                        'average_bench_points': total_bench_points / len(optimal_team.stage_selections)
                    })
            
            optimal_top_bench.sort(key=lambda x: x['total_bench_points'], reverse=True)
            
            analysis['optimal_team'].update({
                'total_selected_points': optimal_total_selected,
                'total_bench_points': optimal_total_bench,
                'selection_efficiency': optimal_total_selected / (optimal_total_selected + optimal_total_bench) if (optimal_total_selected + optimal_total_bench) > 0 else 0,
                'stage_breakdown': optimal_stage_breakdown,
                'top_bench_performers': optimal_top_bench
            })
        
        return analysis
    
    def run_unified_simulations(self, user_team: UserTeam, num_simulations: int = 500) -> Dict:
        """
        Run unified simulations that capture all necessary data in a single batch.
        Uses parallel processing and suppresses simulation output for better performance.
        
        Args:
            user_team: User's team
            num_simulations: Number of simulations to run (increased for better accuracy)
            
        Returns:
            Dictionary containing all simulation results and data
        """
        start_time = time.time()
        
        # Import parallel processing
        from joblib import Parallel, delayed
        import logging
        
        # Suppress simulation output
        logging.getLogger().setLevel(logging.ERROR)
        
        # Run all simulations in parallel with comprehensive data collection
        simulation_results = Parallel(n_jobs=-1, verbose=0)(
            delayed(self._run_comprehensive_simulation)(user_team, i)
            for i in range(num_simulations)
        )
        
        # Process all results to extract different data types
        teammate_bonus_data = self._process_teammate_bonus_data(simulation_results, num_simulations)
        rider_data = self._process_rider_performance_data(simulation_results, num_simulations, teammate_bonus_data)
        stage_performance = self._process_stage_performance_data(simulation_results, num_simulations)
        
        # Optimize stage selection for user team using the rider data
        user_team = self.optimize_stage_selection(user_team, rider_data, num_simulations=num_simulations)
        
        # Get optimal team using the same rider data
        optimal_team = self.team_optimizer.optimize_with_stage_selection(
            rider_data, num_simulations, risk_aversion=0.0, abandon_penalty=1.0
        )
        
        # Attach stage performance data to both team objects for dashboard access
        user_team.stage_performance_data = stage_performance
        optimal_team.stage_performance_data = stage_performance
        
        # Extract team simulation results from the comprehensive data
        user_simulation_results = self._extract_team_simulation_results(simulation_results, user_team)
        optimal_simulation_results = self._extract_team_simulation_results(simulation_results, optimal_team)
        
        elapsed_time = time.time() - start_time
        print(f"Unified simulations completed in {elapsed_time:.2f} seconds")
        
        return {
            'rider_data': rider_data,
            'user_team': user_team,
            'optimal_team': optimal_team,
            'user_simulation_results': user_simulation_results,
            'optimal_simulation_results': optimal_simulation_results,
            'teammate_bonus_data': teammate_bonus_data
        }
    
    def _run_comprehensive_simulation(self, user_team: UserTeam, simulation_id: int) -> Dict:
        """
        Run a single comprehensive simulation that captures all necessary data.
        
        Args:
            user_team: User's team
            simulation_id: ID of this simulation
            
        Returns:
            Dictionary with all simulation data
        """
        # Create a new simulator for this simulation
        simulator = TourSimulator()
        simulator.rider_db = self.rider_db
        
        # Suppress simulator output
        import sys
        from io import StringIO
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # Run simulation
            simulator.simulate_tour()
        finally:
            # Restore stdout
            sys.stdout = old_stdout
        
        # Extract all rider points
        rider_points = dict(simulator.scorito_points)
        
        # Extract stage-by-stage points for all riders
        stage_records = simulator.scorito_points_records
        rider_stage_points = {}
        
        # Group records by rider and stage
        for record in stage_records:
            rider_name = record['rider']
            stage = record['stage']
            cumulative_points = record['scorito_points']
            
            if rider_name not in rider_stage_points:
                rider_stage_points[rider_name] = {}
            rider_stage_points[rider_name][stage] = cumulative_points
        
        # Calculate per-stage points by taking differences
        stage_performance = {}
        for rider_name, stage_data in rider_stage_points.items():
            stages = sorted(stage_data.keys())
            for i, stage in enumerate(stages):
                if i == 0:
                    # First stage: points earned = cumulative points
                    points_earned = stage_data[stage]
                else:
                    # Other stages: points earned = current cumulative - previous cumulative
                    points_earned = stage_data[stage] - stage_data[stages[i-1]]
                
                stage_performance[(rider_name, stage)] = points_earned
        
        # Calculate user team points with optimal stage selection
        user_team_points = self._calculate_optimal_stage_points_for_simulation(
            simulator, user_team.rider_names
        )
        
        # Analyze teammate bonuses
        teammate_bonus_analysis = self._analyze_teammate_bonuses_from_simulation(simulator)
        
        return {
            'simulation_id': simulation_id,
            'rider_points': rider_points,
            'stage_performance': stage_performance,
            'user_team_points': user_team_points,
            'teammate_bonus_analysis': teammate_bonus_analysis
        }
    
    def _process_rider_performance_data(self, simulation_results: List[Dict], num_simulations: int, teammate_bonus_data: Dict = None) -> pd.DataFrame:
        """
        Process simulation results to create rider performance DataFrame.
        
        Args:
            simulation_results: List of simulation result dictionaries
            num_simulations: Number of simulations run
            
        Returns:
            DataFrame with rider performance data
        """
        # Collect all rider points
        all_points = []
        for sim_result in simulation_results:
            for rider_name, points in sim_result['rider_points'].items():
                all_points.append({
                    'rider_name': rider_name,
                    'points': points,
                    'simulation': sim_result['simulation_id']
                })
        
        # Calculate statistics
        points_df = pd.DataFrame(all_points)
        rider_stats = points_df.groupby('rider_name')['points'].agg([
            'mean', 'median', 'std', 'count'
        ]).reset_index()
        
        # Calculate mode
        mode_values = []
        for rider_name in rider_stats['rider_name']:
            rider_points = points_df[points_df['rider_name'] == rider_name]['points'].values
            hist, bins = np.histogram(rider_points, bins='auto')
            mode_idx = np.argmax(hist)
            mode_values.append((bins[mode_idx] + bins[mode_idx + 1]) / 2)
        
        rider_stats['mode'] = mode_values
        
        # Create final DataFrame
        expected_points_df = pd.DataFrame({
            'rider_name': rider_stats['rider_name'],
            'expected_points': rider_stats['mean'],
            'points_std': rider_stats['std'],
            'points_mean': rider_stats['mean'],
            'points_median': rider_stats['median'],
            'points_mode': rider_stats['mode'],
            'simulation_count': rider_stats['count']
        })
        
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
        final_df = rider_info_df.merge(expected_points_df, on='rider_name', how='left')
        
        # Fill missing values
        for col in ['expected_points', 'points_std', 'points_mean', 'points_median', 'points_mode', 'simulation_count']:
            final_df[col] = final_df[col].fillna(0)
        
        # Add teammate bonus analysis
        final_df['teammate_bonus_potential'] = 0.0
        final_df['teammate_bonus_team_size'] = 0
        
        # Add teammate bonus potential to riders based on team analysis
        for team, bonus_info in teammate_bonus_data.items():
            team_riders = bonus_info['riders']
            bonus_per_rider = bonus_info['estimated_bonus_per_rider']
            
            # Add teammate bonus potential to riders in this team
            team_mask = final_df['team'] == team
            final_df.loc[team_mask, 'teammate_bonus_potential'] = bonus_per_rider
            final_df.loc[team_mask, 'teammate_bonus_team_size'] = bonus_info['team_size']
        
        # Calculate adjusted expected points including teammate bonuses
        final_df['expected_points_with_teammate_bonus'] = (
            final_df['expected_points'] + final_df['teammate_bonus_potential']
        )
        
        return final_df
    
    def _process_stage_performance_data(self, simulation_results: List[Dict], num_simulations: int) -> Dict:
        """
        Process simulation results to create stage performance data.
        
        Args:
            simulation_results: List of simulation result dictionaries
            num_simulations: Number of simulations run
            
        Returns:
            Dictionary mapping (rider_name, stage) to expected points
        """
        # Collect all stage performance data
        stage_data = {}
        
        for sim_result in simulation_results:
            for (rider_name, stage), points in sim_result['stage_performance'].items():
                key = (rider_name, stage)
                if key not in stage_data:
                    stage_data[key] = []
                stage_data[key].append(points)
        
        # Calculate means
        expected_stage_points = {}
        for key, points_list in stage_data.items():
            expected_stage_points[key] = np.mean(points_list)
        
        return expected_stage_points
    
    def _process_teammate_bonus_data(self, simulation_results: List[Dict], num_simulations: int) -> Dict:
        """
        Process simulation results to create teammate bonus data.
        
        Args:
            simulation_results: List of simulation result dictionaries
            num_simulations: Number of simulations run
            
        Returns:
            Dictionary with teammate bonus analysis
        """
        # Aggregate teammate bonus data across all simulations
        team_bonus_data = {}
        
        for sim_result in simulation_results:
            for team, bonus_info in sim_result['teammate_bonus_analysis'].items():
                if team not in team_bonus_data:
                    team_bonus_data[team] = {
                        'riders': bonus_info['riders'],
                        'team_size': bonus_info['team_size'],
                        'potential_bonus_riders': bonus_info['potential_bonus_riders'],
                        'estimated_bonus_per_rider': bonus_info['estimated_bonus_per_rider'],
                        'simulation_count': 0
                    }
                team_bonus_data[team]['simulation_count'] += 1
        
        return team_bonus_data
    
    def _extract_team_simulation_results(self, simulation_results: List[Dict], team) -> List[Dict]:
        """
        Extract team-specific simulation results from comprehensive data.
        
        Args:
            simulation_results: List of comprehensive simulation results
            team: Team object (UserTeam or TeamSelection)
            
        Returns:
            List of team simulation results
        """
        team_results = []
        
        for sim_result in simulation_results:
            # Calculate team points using stage selections if available
            team_points = 0
            if hasattr(team, 'stage_selections') and team.stage_selections:
                for stage, selected_riders in team.stage_selections.items():
                    stage_points = 0
                    for rider_name in selected_riders:
                        stage_points += sim_result['stage_performance'].get((rider_name, stage), 0)
                    team_points += stage_points
            else:
                # Use the pre-calculated optimal stage points
                team_points = sim_result['user_team_points']
            
            team_results.append({
                'simulation': sim_result['simulation_id'] + 1,
                'team_points': team_points,
                'rider_points': {name: sim_result['rider_points'].get(name, 0) 
                               for name in team.rider_names}
            })
        
        return team_results
    
    def _analyze_teammate_bonuses_from_simulation(self, simulator) -> Dict:
        """
        Analyze teammate bonuses from a single simulation.
        This method replicates the functionality from team_optimization.py.
        
        Args:
            simulator: TourSimulator instance that has completed a simulation
            
        Returns:
            Dictionary with teammate bonus analysis
        """
        # Get all riders and their teams
        all_riders = self.rider_db.get_all_riders()
        team_riders = {}
        
        for rider in all_riders:
            if rider.team not in team_riders:
                team_riders[rider.team] = []
            team_riders[rider.team].append(rider.name)
        
        # Analyze each team
        team_bonus_analysis = {}
        
        for team_name, riders in team_riders.items():
            team_size = len(riders)
            
            # Count how many riders from this team scored points
            scoring_riders = [rider for rider in riders if rider in simulator.scorito_points and simulator.scorito_points[rider] > 0]
            potential_bonus_riders = len(scoring_riders)
            
            # Estimate bonus per rider based on team size
            estimated_bonus_per_rider = self._estimate_teammate_bonus_per_rider(team_size)
            
            team_bonus_analysis[team_name] = {
                'riders': riders,
                'team_size': team_size,
                'potential_bonus_riders': potential_bonus_riders,
                'estimated_bonus_per_rider': estimated_bonus_per_rider
            }
        
        return team_bonus_analysis
    
    def _estimate_teammate_bonus_per_rider(self, team_size: int) -> float:
        """
        Estimate teammate bonus per rider based on team size.
        This method replicates the functionality from team_optimization.py.
        
        Args:
            team_size: Number of riders in the team
            
        Returns:
            Estimated bonus points per rider
        """
        # Simple heuristic: more riders = more potential for bonuses
        if team_size >= 4:
            return 2.0  # High potential for bonuses
        elif team_size >= 3:
            return 1.5  # Medium potential
        elif team_size >= 2:
            return 1.0  # Low potential
        else:
            return 0.0  # No bonus for single riders

def interactive_team_selection() -> List[str]:
    """
    Interactive team selection interface.
    
    Returns:
        List of selected rider names
    """
    print("=== VERSUS MODE - TEAM SELECTION ===")
    print(f"Budget: {48.0} points")
    print(f"Team size: 20 riders")
    print(f"Maximum 4 riders per team")
    print()
    
    versus = VersusMode()
    available_riders = versus.get_available_riders()
    
    # Group riders by team
    teams = available_riders.groupby('team')
    
    selected_riders = []
    remaining_budget = 48.0
    team_counts = {}
    
    print("Available riders by team:")
    print("=" * 50)
    
    for team_name, team_riders in teams:
        print(f"\n{team_name}:")
        print(f"{'Name':<25} {'Age':<4} {'Price':<6} {'Sprint':<6} {'Punch':<6} {'ITT':<6} {'Mountain':<8} {'Break Away':<10}")
        print("-" * 75)
        
        for _, rider in team_riders.iterrows():
            selected_mark = "✓" if rider['name'] in selected_riders else " "
            print(f"{selected_mark} {rider['name']:<24} {rider['age']:<4} {rider['price']:<6.1f} "
                  f"{rider['sprint_ability']:<6.1f} {rider['punch_ability']:<6.1f} "
                  f"{rider['itt_ability']:<6.1f} {rider['mountain_ability']:<8.1f} {rider['break_away_ability']:<10.1f}")
    
    print(f"\nSelected riders: {len(selected_riders)}/20")
    print(f"Remaining budget: {remaining_budget:.1f}")
    print(f"Team counts: {dict(team_counts)}")
    
    while len(selected_riders) < 20:
        print(f"\nEnter rider name to add/remove (or 'done' to finish, 'list' to show current selection):")
        user_input = input("> ").strip()
        
        if user_input.lower() == 'done':
            if len(selected_riders) == 20:
                break
            else:
                print(f"You need to select exactly 20 riders. Currently have {len(selected_riders)}.")
                continue
        
        elif user_input.lower() == 'list':
            print("\nCurrent selection:")
            for i, rider_name in enumerate(selected_riders, 1):
                rider = versus.rider_db.get_rider(rider_name)
                print(f"{i:2d}. {rider_name} ({rider.team}) - {rider.price:.1f} points")
            continue
        
        # Find rider
        matching_riders = available_riders[available_riders['name'].str.contains(user_input, case=False, na=False)]
        
        if len(matching_riders) == 0:
            print("No riders found matching that name.")
            continue
        elif len(matching_riders) == 1:
            rider_name = matching_riders.iloc[0]['name']
        else:
            print("Multiple riders found:")
            for i, (_, rider) in enumerate(matching_riders.iterrows(), 1):
                print(f"{i}. {rider['name']} ({rider['team']}) - {rider['price']:.1f} points")
            try:
                choice = int(input("Select rider number: ")) - 1
                rider_name = matching_riders.iloc[choice]['name']
            except (ValueError, IndexError):
                print("Invalid selection.")
                continue
        
        # Check if rider is already selected
        if rider_name in selected_riders:
            # Remove rider
            selected_riders.remove(rider_name)
            rider = versus.rider_db.get_rider(rider_name)
            remaining_budget += rider.price
            team_counts[rider.team] -= 1
        else:
            # Add rider
            rider = versus.rider_db.get_rider(rider_name)
            
            # Check constraints
            if rider.price > remaining_budget:
                print(f"Cannot add {rider_name}: insufficient budget (need {rider.price:.1f}, have {remaining_budget:.1f})")
                continue
            
            if team_counts.get(rider.team, 0) >= 4:
                print(f"Cannot add {rider_name}: team {rider.team} already has 4 riders")
                continue
            
            selected_riders.append(rider_name)
            remaining_budget -= rider.price
            team_counts[rider.team] = team_counts.get(rider.team, 0) + 1
        
        print(f"Selected riders: {len(selected_riders)}/20")
        print(f"Remaining budget: {remaining_budget:.1f}")
        print(f"Team counts: {dict(team_counts)}")
    
    return selected_riders

def main():
    """Main function for Versus Mode."""
    print("=== TOUR DE FRANCE VERSUS MODE ===")
    print("Compare your team selection against the optimal team!")
    print()
    
    # Initialize versus mode
    versus = VersusMode()
    
    # Get user team selection
    print("Step 1: Select your team of 20 riders")
    print("You can type partial names to search for riders.")
    print("Type 'done' when you have selected 20 riders.")
    print()
    
    selected_rider_names = interactive_team_selection()
    
    # Validate team selection
    is_valid, error_message = versus.validate_team_selection(selected_rider_names)
    if not is_valid:
        print(f"Error: {error_message}")
        return
    
    print(f"\nTeam selection validated successfully!")
    
    # Create user team
    user_team = versus.create_user_team(selected_rider_names)
    print(f"User team created: {user_team}")
    
    # Get rider performance data using Team Optimization methods
            # print("\nStep 2: Analyzing rider performance using Team Optimization methods...")
    rider_data = versus.team_optimizer.run_simulation_with_teammate_analysis(num_simulations=100, metric='mean')
    
    # Optimize stage selection for user team
            # print("\nStep 3: Optimizing stage selection for your team...")
    user_team = versus.optimize_stage_selection(user_team, rider_data, num_simulations=50)
    
    # Get optimal team for comparison
    print("\nStep 4: Generating optimal team for comparison...")
    optimal_team = versus.get_optimal_team(num_simulations=50, metric='mean')
    
    # Compare teams using Team Optimization analysis methods
            # print("\nStep 5: Comparing teams using Team Optimization analysis...")
    comparison = versus.compare_teams(user_team, optimal_team)
    
    # Print comparison results
    print("\n=== COMPARISON RESULTS ===")
    print(f"Your Team:")
    print(f"  Cost: {comparison['user_team']['total_cost']:.2f}")
    print(f"  Expected Points: {comparison['user_team']['expected_points']:.2f}")
    print(f"  Efficiency: {comparison['comparison']['user_efficiency']:.2f} points/cost")
    print(f"  Unique Teams: {comparison['user_team']['team_diversity']['unique_teams']}")
    print(f"  Average Age: {comparison['user_team']['team_diversity']['avg_age']:.1f}")
    print(f"  Riders: {', '.join(comparison['user_team']['rider_names'])}")
    
    print(f"\nOptimal Team:")
    print(f"  Cost: {comparison['optimal_team']['total_cost']:.2f}")
    print(f"  Expected Points: {comparison['optimal_team']['expected_points']:.2f}")
    print(f"  Efficiency: {comparison['comparison']['optimal_efficiency']:.2f} points/cost")
    print(f"  Unique Teams: {comparison['optimal_team']['team_diversity']['unique_teams']}")
    print(f"  Average Age: {comparison['optimal_team']['team_diversity']['avg_age']:.1f}")
    print(f"  Riders: {', '.join(comparison['optimal_team']['rider_names'])}")
    
    print(f"\nComparison:")
    print(f"  Cost Difference: {comparison['comparison']['cost_difference']:.2f}")
    print(f"  Performance Difference: {comparison['comparison']['performance_difference']:.2f}")
    print(f"  Efficiency Difference: {comparison['comparison']['efficiency_difference']:.2f}")
    
    # Save results
    print("\nStep 6: Saving results...")
    filename = versus.save_versus_results(user_team, optimal_team, comparison, rider_data)
    print(f"Results saved to '{filename}'")
    
    print("\n=== VERSUS MODE COMPLETE ===")
    print("Check the Excel file for detailed analysis including:")
    print("- Team comparison summary")
    print("- Rider comparison with teammate bonuses")
    print("- Team diversity analysis")
    print("- Team composition analysis")
    print("- Stage-by-stage comparison")
    print("- Detailed stage performance")
    print("- Rider stage performance summary")
    print("- All rider data from Team Optimization")

if __name__ == "__main__":
    main() 