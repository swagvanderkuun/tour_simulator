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
        print("Optimizing stage selection for user team...")
        
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
            print(f"Warning: Stage optimization failed with status: {LpStatus[prob.status]}")
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
        print(f"Running {num_simulations} simulations with user team...")
        
        simulation_results = []
        
        for i in range(num_simulations):
            if i % 10 == 0:
                print(f"Simulation {i+1}/{num_simulations}")
            
            # Create a new simulator for this simulation
            simulator = TourSimulator()
            
            # Run simulation
            simulator.simulate_tour()
            
            # Calculate total points for user's team
            team_points = 0
            for rider_name in user_team.rider_names:
                if rider_name in simulator.scorito_points:
                    team_points += simulator.scorito_points[rider_name]
            
            simulation_results.append({
                'simulation': i + 1,
                'team_points': team_points,
                'rider_points': {name: simulator.scorito_points.get(name, 0) 
                               for name in user_team.rider_names}
            })
        
        user_team.simulation_results = simulation_results
        return simulation_results
    
    def get_optimal_team(self, num_simulations: int = 50) -> TeamSelection:
        """
        Get the optimal team using the team optimizer.
        
        Args:
            num_simulations: Number of simulations for optimization
            
        Returns:
            Optimal team selection
        """
        print("Generating optimal team for comparison...")
        
        # Run simulations to get expected points
        rider_data = self.team_optimizer.run_simulation(num_simulations)
        
        # Optimize team with stage selection
        optimal_team = self.team_optimizer.optimize_with_stage_selection(
            rider_data, num_simulations, risk_aversion=0.0, abandon_penalty=1.0
        )
        
        return optimal_team
    
    def compare_teams(self, user_team: UserTeam, optimal_team: TeamSelection) -> Dict:
        """
        Compare user team against optimal team.
        
        Args:
            user_team: User's team
            optimal_team: Optimal team from optimization
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'user_team': {
                'total_cost': user_team.total_cost,
                'rider_count': len(user_team.rider_names),
                'riders': user_team.rider_names,
                'avg_simulation_points': 0,
                'simulation_std': 0
            },
            'optimal_team': {
                'total_cost': optimal_team.total_cost,
                'rider_count': len(optimal_team.rider_names),
                'riders': optimal_team.rider_names,
                'expected_points': optimal_team.expected_points
            },
            'comparison': {
                'cost_difference': user_team.total_cost - optimal_team.total_cost,
                'performance_difference': 0,
                'common_riders': [],
                'user_only_riders': [],
                'optimal_only_riders': []
            }
        }
        
        # Calculate simulation statistics for user team
        if user_team.simulation_results:
            points_list = [result['team_points'] for result in user_team.simulation_results]
            comparison['user_team']['avg_simulation_points'] = np.mean(points_list)
            comparison['user_team']['simulation_std'] = np.std(points_list)
            
            # Calculate performance difference
            comparison['comparison']['performance_difference'] = (
                comparison['user_team']['avg_simulation_points'] - optimal_team.expected_points
            )
        
        # Find common and unique riders
        user_rider_set = set(user_team.rider_names)
        optimal_rider_set = set(optimal_team.rider_names)
        
        comparison['comparison']['common_riders'] = list(user_rider_set & optimal_rider_set)
        comparison['comparison']['user_only_riders'] = list(user_rider_set - optimal_rider_set)
        comparison['comparison']['optimal_only_riders'] = list(optimal_rider_set - user_rider_set)
        
        return comparison
    
    def save_versus_results(self, user_team: UserTeam, optimal_team: TeamSelection,
                          comparison: Dict, rider_data: pd.DataFrame,
                          filename: str = None) -> str:
        """
        Save versus mode results to Excel file.
        
        Args:
            user_team: User's team
            optimal_team: Optimal team
            comparison: Comparison results
            rider_data: Rider performance data
            filename: Output filename
            
        Returns:
            Filename of saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"versus_mode_results_{timestamp}.xlsx"
        
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
                ['Expected Points', comparison['user_team']['avg_simulation_points'], 
                 comparison['optimal_team']['expected_points'], 
                 comparison['comparison']['performance_difference']],
                ['Points Std Dev', comparison['user_team']['simulation_std'], 'N/A', 'N/A']
            ]
            
            summary_df = pd.DataFrame(summary_data[1:], columns=summary_data[0])
            summary_df.to_excel(writer, sheet_name='Team_Comparison', index=False)
            
            # Sheet 2: Rider Comparison
            rider_comparison = []
            all_riders = set(user_team.rider_names + optimal_team.rider_names)
            
            for rider_name in sorted(all_riders):
                in_user = rider_name in user_team.rider_names
                in_optimal = rider_name in optimal_team.rider_names
                
                # Get rider info
                rider_info = rider_data[rider_data['rider_name'] == rider_name]
                if not rider_info.empty:
                    rider_row = rider_info.iloc[0]
                    rider_comparison.append({
                        'Rider': rider_name,
                        'Team': rider_row['team'],
                        'Age': rider_row['age'],
                        'Price': rider_row['price'],
                        'Expected_Points': rider_row['expected_points'],
                        'In_User_Team': 'Yes' if in_user else 'No',
                        'In_Optimal_Team': 'Yes' if in_optimal else 'No',
                        'Selection': 'Both' if in_user and in_optimal else 
                                   ('User Only' if in_user else 'Optimal Only')
                    })
            
            rider_comp_df = pd.DataFrame(rider_comparison)
            rider_comp_df.to_excel(writer, sheet_name='Rider_Comparison', index=False)
            
            # Sheet 3: User Team Stage Analysis
            if user_team.stage_selections:
                user_stage_data = []
                for stage in sorted(user_team.stage_selections.keys()):
                    selected_riders = user_team.stage_selections[stage]
                    stage_points = user_team.stage_points.get(stage, {})
                    
                    for rider_name in user_team.rider_names:
                        is_selected = rider_name in selected_riders
                        points = stage_points.get(rider_name, 0)
                        
                        user_stage_data.append({
                            'Stage': stage,
                            'Rider': rider_name,
                            'Selected': 'Yes' if is_selected else 'No',
                            'Points_Per_Stage': points
                        })
                
                user_stage_df = pd.DataFrame(user_stage_data)
                user_stage_df.to_excel(writer, sheet_name='User_Team_Stages', index=False)
            
            # Sheet 4: Optimal Team Stage Analysis
            if optimal_team.stage_selections:
                optimal_stage_data = []
                for stage in sorted(optimal_team.stage_selections.keys()):
                    selected_riders = optimal_team.stage_selections[stage]
                    stage_points = optimal_team.stage_points.get(stage, {})
                    
                    for rider_name in optimal_team.rider_names:
                        is_selected = rider_name in selected_riders
                        points = stage_points.get(rider_name, 0)
                        
                        optimal_stage_data.append({
                            'Stage': stage,
                            'Rider': rider_name,
                            'Selected': 'Yes' if is_selected else 'No',
                            'Points_Per_Stage': points
                        })
                
                optimal_stage_df = pd.DataFrame(optimal_stage_data)
                optimal_stage_df.to_excel(writer, sheet_name='Optimal_Team_Stages', index=False)
            
            # Sheet 5: Simulation Results
            if user_team.simulation_results:
                sim_data = []
                for result in user_team.simulation_results:
                    sim_data.append({
                        'Simulation': result['simulation'],
                        'Total_Points': result['team_points']
                    })
                
                sim_df = pd.DataFrame(sim_data)
                sim_df.to_excel(writer, sheet_name='Simulation_Results', index=False)
            
            # Sheet 6: Stage-by-Stage Comparison
            if user_team.stage_selections and optimal_team.stage_selections:
                stage_comparison = []
                for stage in range(1, 23):
                    user_stage_points = sum(user_team.stage_points.get(stage, {}).values())
                    optimal_stage_points = sum(optimal_team.stage_points.get(stage, {}).values())
                    
                    stage_comparison.append({
                        'Stage': stage,
                        'User_Team_Points': user_stage_points,
                        'Optimal_Team_Points': optimal_stage_points,
                        'Difference': user_stage_points - optimal_stage_points
                    })
                
                stage_comp_df = pd.DataFrame(stage_comparison)
                stage_comp_df.to_excel(writer, sheet_name='Stage_Comparison', index=False)
        
        return filename

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
            print(f"Removed {rider_name}")
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
            print(f"Added {rider_name}")
        
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
    
    # Get rider performance data
    print("\nStep 2: Analyzing rider performance...")
    rider_data = versus.team_optimizer.run_simulation(num_simulations=50)
    
    # Optimize stage selection for user team
    print("\nStep 3: Optimizing stage selection for your team...")
    user_team = versus.optimize_stage_selection(user_team, rider_data, num_simulations=50)
    
    # Run simulations with user team
    print("\nStep 4: Running simulations with your team...")
    simulation_results = versus.run_user_team_simulations(user_team, num_simulations=100)
    
    # Get optimal team for comparison
    print("\nStep 5: Generating optimal team for comparison...")
    optimal_team = versus.get_optimal_team(num_simulations=50)
    
    # Compare teams
    print("\nStep 6: Comparing teams...")
    comparison = versus.compare_teams(user_team, optimal_team)
    
    # Print comparison results
    print("\n=== COMPARISON RESULTS ===")
    print(f"Your Team:")
    print(f"  Cost: {comparison['user_team']['total_cost']:.2f}")
    print(f"  Average Points: {comparison['user_team']['avg_simulation_points']:.2f} ± {comparison['user_team']['simulation_std']:.2f}")
    print(f"  Riders: {', '.join(comparison['user_team']['riders'])}")
    
    print(f"\nOptimal Team:")
    print(f"  Cost: {comparison['optimal_team']['total_cost']:.2f}")
    print(f"  Expected Points: {comparison['optimal_team']['expected_points']:.2f}")
    print(f"  Riders: {', '.join(comparison['optimal_team']['riders'])}")
    
    print(f"\nComparison:")
    print(f"  Cost Difference: {comparison['comparison']['cost_difference']:.2f}")
    print(f"  Performance Difference: {comparison['comparison']['performance_difference']:.2f}")
    print(f"  Common Riders: {len(comparison['comparison']['common_riders'])}")
    print(f"  Your Unique Riders: {len(comparison['comparison']['user_only_riders'])}")
    print(f"  Optimal Unique Riders: {len(comparison['comparison']['optimal_only_riders'])}")
    
    if comparison['comparison']['common_riders']:
        print(f"  Common Riders: {', '.join(comparison['comparison']['common_riders'])}")
    
    if comparison['comparison']['user_only_riders']:
        print(f"  Your Unique Riders: {', '.join(comparison['comparison']['user_only_riders'])}")
    
    if comparison['comparison']['optimal_only_riders']:
        print(f"  Optimal Unique Riders: {', '.join(comparison['comparison']['optimal_only_riders'])}")
    
    # Save results
    print("\nStep 7: Saving results...")
    filename = versus.save_versus_results(user_team, optimal_team, comparison, rider_data)
    print(f"Results saved to '{filename}'")
    
    print("\n=== VERSUS MODE COMPLETE ===")
    print("Check the Excel file for detailed stage-by-stage analysis!")

if __name__ == "__main__":
    main() 