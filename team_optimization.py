import pandas as pd
import numpy as np
from pulp import *
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from simulator import TourSimulator
from riders import RiderDatabase, Rider
import warnings
import logging
from joblib import Parallel, delayed
import time
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        
    def _run_single_simulation(self) -> Dict[str, float]:
        """
        Run a single simulation and return rider points.
        This method is designed for parallel processing.
        """
        # Create a new simulator instance for this simulation
        simulator = TourSimulator()
        simulator.rider_db = self.rider_db  # Use the same rider database
        
        # Run simulation
        simulator.simulate_tour()
        
        # Return the scorito points
        return dict(simulator.scorito_points)
    
    def _run_single_simulation_with_teammate_analysis(self) -> Dict[str, Dict]:
        """
        Run a single simulation and return detailed analysis including teammate bonuses.
        This method is designed for parallel processing and teammate bonus analysis.
        """
        # Create a new simulator instance for this simulation
        simulator = TourSimulator()
        simulator.rider_db = self.rider_db  # Use the same rider database
        
        # Run simulation
        simulator.simulate_tour()
        
        # Analyze teammate bonuses from the simulation
        teammate_bonus_analysis = self._analyze_teammate_bonuses_from_simulation(simulator)
        
        return {
            'scorito_points': dict(simulator.scorito_points),
            'teammate_bonus_analysis': teammate_bonus_analysis
        }
    
    def _analyze_teammate_bonuses_from_simulation(self, simulator) -> Dict:
        """
        Analyze teammate bonuses from a simulation run.
        
        Args:
            simulator: TourSimulator instance that has completed a simulation
            
        Returns:
            Dictionary with teammate bonus analysis
        """
        # Extract teammate bonus information from the simulation
        # This is a simplified analysis - in a full implementation, we'd track
        # teammate bonuses throughout the simulation
        
        teammate_bonus_data = {}
        
        # Group riders by team
        team_riders = {}
        for rider in self.rider_db.get_all_riders():
            if rider.name not in simulator.abandoned_riders:
                if rider.team not in team_riders:
                    team_riders[rider.team] = []
                team_riders[rider.team].append(rider.name)
        
        # Calculate potential teammate bonus opportunities
        for team, riders in team_riders.items():
            if len(riders) >= 2:  # Only teams with multiple riders can get teammate bonuses
                # Estimate teammate bonus potential based on team size
                # This is a simplified approach - in reality, it depends on which riders win stages/classifications
                teammate_bonus_data[team] = {
                    'riders': riders,
                    'team_size': len(riders),
                    'potential_bonus_riders': len(riders) - 1,  # All riders except the winner
                    'estimated_bonus_per_rider': self._estimate_teammate_bonus_per_rider(len(riders))
                }
        
        return teammate_bonus_data
    
    def _estimate_teammate_bonus_per_rider(self, team_size: int) -> float:
        """
        Estimate average teammate bonus points per rider based on team size.
        This is a simplified estimation - in reality, it depends on team performance.
        
        Args:
            team_size: Number of riders in the team
            
        Returns:
            Estimated teammate bonus points per rider
        """
        if team_size < 2:
            return 0.0
        
        # Base estimation: larger teams have more potential for teammate bonuses
        # This is a simplified model - in reality, it depends on which riders win stages/classifications
        
        # Average teammate bonus points per stage (simplified)
        # Stage winner bonus: 10 points, GC leader: 8, Sprint: 6, Mountain: 6, Youth: 4
        # Assuming 1-2 classification leaders per team on average
        avg_stage_bonus = 15.0  # Conservative estimate
        
        # Over 21 stages (excluding final stage which has different bonuses)
        total_stage_bonuses = avg_stage_bonus * 21
        
        # Final classification bonuses (GC: 24, Sprint: 18, Mountain: 18, Youth: 9)
        # Assuming teams might win 1-2 final classifications
        final_bonuses = 30.0  # Conservative estimate
        
        total_potential_bonus = total_stage_bonuses + final_bonuses
        
        # Distribute among non-winning riders (team_size - 1)
        bonus_per_rider = total_potential_bonus / (team_size - 1)
        
        # Apply a probability factor (not every team wins stages/classifications)
        probability_factor = 0.3  # 30% chance of significant teammate bonuses
        
        return bonus_per_rider * probability_factor
    
    def run_simulation_with_teammate_analysis(self, num_simulations: int = 100, metric: str = 'mean') -> pd.DataFrame:
        """
        Run multiple simulations to get expected points for each rider, including teammate bonus analysis.
        
        Args:
            num_simulations: Number of simulations to run
            metric: Metric to use for expected points ('mean', 'median', 'mode')
            
        Returns:
            DataFrame with rider names and their expected points including teammate bonuses
        """
        logger.info(f"Running {num_simulations} simulations with teammate bonus analysis using {metric}...")
        start_time = time.time()
        
        # Use parallel processing for simulations with teammate analysis
        try:
            # Run simulations in parallel
            simulation_results = Parallel(n_jobs=-1, verbose=1)(
                delayed(self._run_single_simulation_with_teammate_analysis)()
                for _ in range(num_simulations)
            )
        except Exception as e:
            logger.warning(f"Parallel processing failed, falling back to sequential: {e}")
            # Fallback to sequential processing
            simulation_results = []
            for i in range(num_simulations):
                if i % 10 == 0:
                    logger.info(f"Simulation {i+1}/{num_simulations}")
                simulation_results.append(self._run_single_simulation_with_teammate_analysis())
        
        # Process results
        all_points = []
        teammate_bonus_data = {}
        
        for i, sim_result in enumerate(simulation_results):
            # Process scorito points
            for rider_name, points in sim_result['scorito_points'].items():
                all_points.append({
                    'rider_name': rider_name,
                    'points': points,
                    'simulation': i
                })
            
            # Aggregate teammate bonus data
            for team, bonus_info in sim_result['teammate_bonus_analysis'].items():
                if team not in teammate_bonus_data:
                    teammate_bonus_data[team] = {
                        'riders': bonus_info['riders'],
                        'team_size': bonus_info['team_size'],
                        'potential_bonus_riders': bonus_info['potential_bonus_riders'],
                        'estimated_bonus_per_rider': bonus_info['estimated_bonus_per_rider'],
                        'simulation_count': 0
                    }
                teammate_bonus_data[team]['simulation_count'] += 1
        
        # Calculate expected points for each rider using the specified metric
        points_df = pd.DataFrame(all_points)
        
        # Group by rider and calculate multiple statistics using vectorized operations
        rider_stats = points_df.groupby('rider_name')['points'].agg([
            'mean', 'median', 'std', 'count'
        ]).reset_index()
        
        # Calculate mode more efficiently
        mode_values = []
        for rider_name in rider_stats['rider_name']:
            rider_points = points_df[points_df['rider_name'] == rider_name]['points'].values
            # Use numpy's histogram for mode calculation
            hist, bins = np.histogram(rider_points, bins='auto')
            mode_idx = np.argmax(hist)
            mode_values.append((bins[mode_idx] + bins[mode_idx + 1]) / 2)
        
        rider_stats['mode'] = mode_values
        
        # Select the expected points based on the metric
        if metric == 'mean':
            expected_points = rider_stats['mean']
        elif metric == 'median':
            expected_points = rider_stats['median']
        elif metric == 'mode':
            expected_points = rider_stats['mode']
        else:
            raise ValueError(f"Unknown metric: {metric}. Must be 'mean', 'median', or 'mode'")
        
        # Create the final expected points dataframe
        expected_points_df = pd.DataFrame({
            'rider_name': rider_stats['rider_name'],
            'expected_points': expected_points,
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
        
        # Merge with expected points
        final_df = rider_info_df.merge(expected_points_df, on='rider_name', how='left')
        final_df['expected_points'] = final_df['expected_points'].fillna(0)
        final_df['points_std'] = final_df['points_std'].fillna(0)
        final_df['points_mean'] = final_df['points_mean'].fillna(0)
        final_df['points_median'] = final_df['points_median'].fillna(0)
        final_df['points_mode'] = final_df['points_mode'].fillna(0)
        final_df['simulation_count'] = final_df['simulation_count'].fillna(0)
        
        # Add teammate bonus analysis
        final_df['teammate_bonus_potential'] = 0.0
        final_df['teammate_bonus_team_size'] = 0
        
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
        
        elapsed_time = time.time() - start_time
        logger.info(f"Simulation with teammate analysis completed in {elapsed_time:.2f} seconds")
        
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
        logger.info("Optimizing team selection...")
        
        # Create optimization problem
        prob = LpProblem("Team_Optimization", LpMaximize)
        
        # Decision variables: 1 if rider is selected, 0 otherwise
        riders = list(rider_data['rider_name'])
        rider_vars = LpVariable.dicts("Rider", riders, cat='Binary')
        
        # Objective function: maximize expected points with improved risk modeling
        objective_terms = []
        for _, row in rider_data.iterrows():
            rider_name = row['rider_name']
            expected_points = row['expected_points']
            points_std = row['points_std']
            abandon_prob = row.get('chance_of_abandon', 0.0)
            
            # Improved risk modeling using Sharpe ratio-like approach
            if risk_aversion > 0 and points_std > 0:
                # Sharpe ratio-like: reward / (1 + risk_penalty * risk)
                risk_adjusted_points = expected_points / (1 + risk_aversion * points_std)
            else:
                risk_adjusted_points = expected_points
            
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
        
        # Constraint 4: Maximum 4 riders per team (Scorito rule)
        teams = rider_data['team'].unique()
        for team in teams:
            team_riders = rider_data[rider_data['team'] == team]['rider_name'].tolist()
            if team_riders:
                prob += lpSum(rider_vars[rider] for rider in team_riders) <= 4
        
        # Solve the problem with improved error handling
        prob.solve()
        
        # Better status checking
        if LpStatus[prob.status] not in {"Optimal", "Feasible"}:
            logger.error(f"Optimization failed with status: {LpStatus[prob.status]}")
            raise ValueError(f"Optimization failed with status: {LpStatus[prob.status]}")
        
        logger.info(f"Optimization completed with status: {LpStatus[prob.status]}")
        
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
        
        logger.info(f"Selected team with {len(selected_riders)} riders, cost: {total_cost:.2f}, expected points: {total_points:.2f}")
        
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
        logger.info("Running advanced optimization with stage selection...")
        
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
        
        # Objective: maximize total points across all stages with improved risk modeling
        objective_terms = []
        for rider in riders:
            for stage in stages:
                if (rider, stage) in stage_performance:
                    points = stage_performance[(rider, stage)]
                    
                    # Apply improved risk aversion if specified
                    if risk_aversion > 0:
                        # Get rider's variance from the rider_data
                        rider_row = rider_data[rider_data['rider_name'] == rider]
                        if not rider_row.empty and 'points_std' in rider_row.columns:
                            points_std = rider_row.iloc[0]['points_std']
                            # Sharpe ratio-like risk adjustment
                            if points_std > 0:
                                points = points / (1 + risk_aversion * points_std)
                    
                    # Apply abandon penalty if specified
                    if abandon_penalty > 0:
                        # Get rider's abandon probability from the rider_data
                        abandon_prob = rider_row.iloc[0]['chance_of_abandon']
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
        
        # Constraint 5: Maximum 4 riders per team (Scorito rule)
        teams = rider_data['team'].unique()
        for team in teams:
            team_riders = rider_data[rider_data['team'] == team]['rider_name'].tolist()
            if team_riders:
                prob += lpSum(rider_vars[rider] for rider in team_riders) <= 4
        
        # Solve with improved error handling
        prob.solve()
        
        # Better status checking
        if LpStatus[prob.status] not in {"Optimal", "Feasible"}:
            logger.error(f"Advanced optimization failed with status: {LpStatus[prob.status]}")
            raise ValueError(f"Advanced optimization failed with status: {LpStatus[prob.status]}")
        
        logger.info(f"Advanced optimization completed with status: {LpStatus[prob.status]}")
        
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
        
        logger.info(f"Selected team with {len(selected_riders)} riders, cost: {total_cost:.2f}, expected points: {total_points:.2f}")
        
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
        Now uses memory-efficient incremental mean calculation.
        
        Args:
            num_simulations: Number of simulations to run
            
        Returns:
            Dictionary mapping (rider_name, stage) to expected points
        """
        logger.info(f"Running {num_simulations} simulations for stage performance analysis...")
        start_time = time.time()
        
        # Use incremental mean calculation to save memory
        mean_dict = {}  # (rider_name, stage) -> (mean, count)
        
        for sim in range(num_simulations):
            if sim % 10 == 0:
                logger.info(f"Stage analysis simulation {sim+1}/{num_simulations}")
            
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
            
            # Calculate per-stage points by taking differences and update incremental mean
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
                    
                    # Incremental mean calculation
                    if key in mean_dict:
                        current_mean, count = mean_dict[key]
                        new_count = count + 1
                        new_mean = (current_mean * count + points_earned) / new_count
                        mean_dict[key] = (new_mean, new_count)
                    else:
                        mean_dict[key] = (points_earned, 1)
            
            # Reset simulator
            self.simulator = TourSimulator()
        
        # Extract final means
        expected_stage_points = {key: mean for key, (mean, count) in mean_dict.items()}
        
        elapsed_time = time.time() - start_time
        logger.info(f"Stage performance analysis completed in {elapsed_time:.2f} seconds")
        
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

    def generate_pareto_optimal_teams(self, rider_data: pd.DataFrame, 
                                    num_teams: int = 5,
                                    num_simulations: int = 50) -> List[TeamSelection]:
        """
        Generate multiple Pareto-optimal teams with different risk/reward profiles.
        
        Args:
            rider_data: DataFrame with rider information
            num_teams: Number of alternative teams to generate
            num_simulations: Number of simulations for analysis
            
        Returns:
            List of alternative team selections
        """
        logger.info(f"Generating {num_teams} Pareto-optimal teams...")
        
        teams = []
        
        # Generate teams with different risk profiles
        risk_profiles = [
            (0.0, 1.0),   # No risk aversion, full abandon penalty
            (0.2, 1.0),   # Low risk aversion
            (0.5, 1.0),   # Medium risk aversion
            (0.8, 1.0),   # High risk aversion
            (0.0, 0.5),   # No risk aversion, low abandon penalty
        ]
        
        for i, (risk_aversion, abandon_penalty) in enumerate(risk_profiles[:num_teams]):
            logger.info(f"Generating team {i+1}/{num_teams} with risk_aversion={risk_aversion}, abandon_penalty={abandon_penalty}")
            
            try:
                team = self.optimize_with_stage_selection(
                    rider_data, 
                    num_simulations=num_simulations,
                    risk_aversion=risk_aversion, 
                    abandon_penalty=abandon_penalty
                )
                teams.append(team)
            except ValueError as e:
                logger.warning(f"Failed to generate team {i+1}: {e}")
                continue
        
        logger.info(f"Successfully generated {len(teams)} Pareto-optimal teams")
        return teams
    
    def get_team_diagnostics(self, team_selection: TeamSelection, 
                           rider_data: pd.DataFrame) -> Dict:
        """
        Get comprehensive diagnostics for a team selection.
        
        Args:
            team_selection: The team selection to analyze
            rider_data: DataFrame with rider information
            
        Returns:
            Dictionary with team diagnostics
        """
        diagnostics = {
            'team_size': len(team_selection.riders),
            'total_cost': team_selection.total_cost,
            'expected_points': team_selection.expected_points,
            'cost_efficiency': team_selection.expected_points / team_selection.total_cost if team_selection.total_cost > 0 else 0,
            'budget_utilization': team_selection.total_cost / self.budget,
            'team_composition': {},
            'risk_metrics': {},
            'abandon_risk': 0.0
        }
        
        # Team composition analysis
        teams = [r.team for r in team_selection.riders]
        team_counts = pd.Series(teams).value_counts()
        diagnostics['team_composition'] = {
            'unique_teams': len(team_counts),
            'team_distribution': team_counts.to_dict(),
            'teammate_bonus_potential': len([team for team, count in team_counts.items() if count >= 2])
        }
        
        # Risk metrics
        total_std = 0
        total_abandon_risk = 0
        
        for rider in team_selection.riders:
            rider_row = rider_data[rider_data['rider_name'] == rider.name]
            if not rider_row.empty:
                total_std += rider_row.iloc[0]['points_std'] ** 2
                total_abandon_risk += rider.chance_of_abandon
        
        diagnostics['risk_metrics'] = {
            'total_std': total_std ** 0.5,
            'avg_std_per_rider': (total_std ** 0.5) / len(team_selection.riders),
            'risk_percentage': (total_std ** 0.5) / team_selection.expected_points if team_selection.expected_points > 0 else 0
        }
        
        diagnostics['abandon_risk'] = total_abandon_risk / len(team_selection.riders)
        
        return diagnostics

    def optimize_team_with_teammate_bonuses(self, rider_data: pd.DataFrame, 
                                          risk_aversion: float = 0.0,
                                          abandon_penalty: float = 1.0,
                                          teammate_bonus_weight: float = 1.0,
                                          min_riders_per_team: Optional[Dict[str, int]] = None) -> TeamSelection:
        """
        Optimize team selection using Integer Linear Programming with teammate bonus consideration.
        
        Args:
            rider_data: DataFrame with rider information and expected points (including teammate bonus columns)
            risk_aversion: Factor to penalize high variance (0 = no penalty, 1 = high penalty)
            abandon_penalty: Factor to penalize high abandon probability (0 = no penalty, 1 = high penalty)
            teammate_bonus_weight: Weight for teammate bonus potential (0 = ignore, 1 = full weight)
            min_riders_per_team: Minimum riders required from each team
            
        Returns:
            TeamSelection object with optimal team
        """
        logger.info("Optimizing team selection with teammate bonus consideration...")
        
        # Create optimization problem
        prob = LpProblem("Team_Optimization_With_Teammate_Bonuses", LpMaximize)
        
        # Decision variables: 1 if rider is selected, 0 otherwise
        riders = list(rider_data['rider_name'])
        rider_vars = LpVariable.dicts("Rider", riders, cat='Binary')
        
        # Objective function: maximize expected points including teammate bonuses
        objective_terms = []
        for _, row in rider_data.iterrows():
            rider_name = row['rider_name']
            expected_points = row['expected_points']
            teammate_bonus = row.get('teammate_bonus_potential', 0.0)
            points_std = row['points_std']
            abandon_prob = row.get('chance_of_abandon', 0.0)
            
            # Calculate total expected points including teammate bonuses
            total_expected_points = expected_points + (teammate_bonus_weight * teammate_bonus)
            
            # Improved risk modeling using Sharpe ratio-like approach
            if risk_aversion > 0 and points_std > 0:
                # Sharpe ratio-like: reward / (1 + risk_penalty * risk)
                risk_adjusted_points = total_expected_points / (1 + risk_aversion * points_std)
            else:
                risk_adjusted_points = total_expected_points
            
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
        
        # Constraint 4: Maximum 4 riders per team (Scorito rule)
        teams = rider_data['team'].unique()
        for team in teams:
            team_riders = rider_data[rider_data['team'] == team]['rider_name'].tolist()
            if team_riders:
                prob += lpSum(rider_vars[rider] for rider in team_riders) <= 4
        
        # Solve the problem with improved error handling
        prob.solve()
        
        # Better status checking
        if LpStatus[prob.status] not in {"Optimal", "Feasible"}:
            logger.error(f"Optimization failed with status: {LpStatus[prob.status]}")
            raise ValueError(f"Optimization failed with status: {LpStatus[prob.status]}")
        
        logger.info(f"Optimization completed with status: {LpStatus[prob.status]}")
        
        # Extract solution
        selected_riders = []
        total_cost = 0
        total_points = 0
        total_teammate_bonus = 0
        
        for rider_name in riders:
            if rider_vars[rider_name].value() == 1:
                rider_row = rider_data[rider_data['rider_name'] == rider_name].iloc[0]
                rider_obj = self.rider_db.get_rider(rider_name)
                selected_riders.append(rider_obj)
                total_cost += rider_row['price']
                total_points += rider_row['expected_points']
                total_teammate_bonus += rider_row.get('teammate_bonus_potential', 0.0)
        
        logger.info(f"Selected team with {len(selected_riders)} riders, cost: {total_cost:.2f}, expected points: {total_points:.2f}, teammate bonus: {total_teammate_bonus:.2f}")
        
        return TeamSelection(
            riders=selected_riders,
            total_cost=total_cost,
            expected_points=total_points + total_teammate_bonus,
            rider_names=[r.name for r in selected_riders]
        )
    
    def optimize_with_stage_selection_and_teammate_bonuses(self, rider_data: pd.DataFrame,
                                                         num_simulations: int = 50,
                                                         risk_aversion: float = 0.0,
                                                         abandon_penalty: float = 1.0,
                                                         teammate_bonus_weight: float = 1.0) -> TeamSelection:
        """
        Advanced optimization that considers stage-by-stage rider selection and teammate bonuses.
        
        Args:
            rider_data: DataFrame with rider information and expected points (including teammate bonus columns)
            num_simulations: Number of simulations for stage analysis
            risk_aversion: Factor to penalize high variance (0 = no penalty, 1 = high penalty)
            abandon_penalty: Factor to penalize high abandon probability (0 = no penalty, 1 = high penalty)
            teammate_bonus_weight: Weight for teammate bonus potential (0 = ignore, 1 = full weight)
            
        Returns:
            TeamSelection object with optimal team
        """
        logger.info("Running advanced optimization with stage selection and teammate bonuses...")
        
        # First, get stage-by-stage performance data
        stage_performance = self._get_stage_performance_data(num_simulations)
        
        # Create optimization problem
        prob = LpProblem("Advanced_Team_Optimization_With_Teammate_Bonuses", LpMaximize)
        
        riders = list(rider_data['rider_name'])
        stages = list(range(1, 23))  # 22 stages
        
        # Decision variables
        # x[i] = 1 if rider i is selected for the team
        rider_vars = LpVariable.dicts("Rider", riders, cat='Binary')
        
        # y[i,j] = 1 if rider i is selected for stage j
        stage_vars = LpVariable.dicts("Stage", 
                                    [(r, s) for r in riders for s in stages], 
                                    cat='Binary')
        
        # Objective: maximize total points across all stages including teammate bonuses
        objective_terms = []
        for rider in riders:
            for stage in stages:
                if (rider, stage) in stage_performance:
                    points = stage_performance[(rider, stage)]
                    
                    # Get teammate bonus potential for this rider
                    rider_row = rider_data[rider_data['rider_name'] == rider]
                    teammate_bonus = 0.0
                    if not rider_row.empty:
                        teammate_bonus = rider_row.iloc[0].get('teammate_bonus_potential', 0.0)
                    
                    # Add teammate bonus to stage points (distributed across stages)
                    total_points = points + (teammate_bonus_weight * teammate_bonus / 22)  # Distribute across 22 stages
                    
                    # Apply improved risk aversion if specified
                    if risk_aversion > 0:
                        # Get rider's variance from the rider_data
                        if not rider_row.empty and 'points_std' in rider_row.columns:
                            points_std = rider_row.iloc[0]['points_std']
                            # Sharpe ratio-like risk adjustment
                            if points_std > 0:
                                total_points = total_points / (1 + risk_aversion * points_std)
                    
                    # Apply abandon penalty if specified
                    if abandon_penalty > 0:
                        # Get rider's abandon probability from the rider_data
                        abandon_prob = rider_row.iloc[0]['chance_of_abandon']
                        # Penalize points based on abandon probability
                        total_points = total_points * (1 - abandon_penalty * abandon_prob)
                    
                    objective_terms.append(stage_vars[(rider, stage)] * total_points)
        
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
        
        # Constraint 5: Maximum 4 riders per team (Scorito rule)
        teams = rider_data['team'].unique()
        for team in teams:
            team_riders = rider_data[rider_data['team'] == team]['rider_name'].tolist()
            if team_riders:
                prob += lpSum(rider_vars[rider] for rider in team_riders) <= 4
        
        # Solve with improved error handling
        prob.solve()
        
        # Better status checking
        if LpStatus[prob.status] not in {"Optimal", "Feasible"}:
            logger.error(f"Advanced optimization failed with status: {LpStatus[prob.status]}")
            raise ValueError(f"Advanced optimization failed with status: {LpStatus[prob.status]}")
        
        logger.info(f"Advanced optimization completed with status: {LpStatus[prob.status]}")
        
        # Extract solution
        selected_riders = []
        total_cost = 0
        total_points = 0
        total_teammate_bonus = 0
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
                total_teammate_bonus += rider_row.get('teammate_bonus_potential', 0.0)
        
        logger.info(f"Selected team with {len(selected_riders)} riders, cost: {total_cost:.2f}, expected points: {total_points:.2f}, teammate bonus: {total_teammate_bonus:.2f}")
        
        return TeamSelection(
            riders=selected_riders,
            total_cost=total_cost,
            expected_points=total_points + total_teammate_bonus,
            rider_names=[r.name for r in selected_riders],
            stage_selections=stage_selections,
            stage_points=stage_points
        )

def main():
    """Example usage of the TeamOptimizer."""
    print("Tour de France Team Optimizer")
    print("=" * 40)
    
    # Initialize optimizer
    optimizer = TeamOptimizer(budget=48.0, team_size=20)
    
    # Test different metrics with teammate bonus analysis
    metrics = ['mean', 'median', 'mode']
    
    for metric in metrics:
        print(f"\n{'='*20} Testing {metric.upper()} metric with teammate bonus analysis {'='*20}")
        
        # Run simulations to get expected points with teammate bonus analysis
        rider_data = optimizer.run_simulation_with_teammate_analysis(num_simulations=50, metric=metric)
        
        print(f"\nAnalyzed {len(rider_data)} riders using {metric}")
        print(f"Average expected points: {rider_data['expected_points'].mean():.2f}")
        print(f"Average teammate bonus potential: {rider_data['teammate_bonus_potential'].mean():.2f}")
        print(f"Total budget available: {optimizer.budget}")
        
        # Show top riders by teammate bonus potential
        top_teammate_bonus = rider_data.nlargest(10, 'teammate_bonus_potential')
        print(f"\nTop 10 riders by teammate bonus potential ({metric}):")
        for _, row in top_teammate_bonus.iterrows():
            print(f"  {row['rider_name']} ({row['team']}): {row['teammate_bonus_potential']:.2f} bonus points")
        
        # Optimize team with teammate bonuses
        print(f"\nOptimizing team selection with teammate bonus consideration using {metric}...")
        optimal_team = optimizer.optimize_team_with_teammate_bonuses(
            rider_data, 
            risk_aversion=0.0, 
            abandon_penalty=1.0,
            teammate_bonus_weight=1.0
        )
        
        print(f"\nOptimal Team with Teammate Bonuses ({metric}):")
        print(optimal_team)
        
        # Get comprehensive diagnostics
        diagnostics = optimizer.get_team_diagnostics(optimal_team, rider_data)
        print(f"\nTeam Diagnostics with Teammate Bonuses ({metric}):")
        print(f"  - Cost Efficiency: {diagnostics['cost_efficiency']:.2f} points per euro")
        print(f"  - Budget Utilization: {diagnostics['budget_utilization']:.1%}")
        print(f"  - Total Risk (Std): {diagnostics['risk_metrics']['total_std']:.2f}")
        print(f"  - Average Abandon Risk: {diagnostics['abandon_risk']:.1%}")
        print(f"  - Teammate Bonus Potential: {diagnostics['team_composition']['teammate_bonus_potential']} teams")
        
        # Show some key statistics
        print(f"\nKey Statistics for {metric} metric with teammate bonuses:")
        print(f"  - Total Expected Points: {optimal_team.expected_points:.2f}")
        print(f"  - Total Cost: {optimal_team.total_cost:.2f}")
        print(f"  - Points per Euro: {optimal_team.expected_points / optimal_team.total_cost:.2f}")
        
        # Show top 5 riders by expected points with teammate bonuses
        rider_points = []
        for rider in optimal_team.riders:
            rider_row = rider_data[rider_data['rider_name'] == rider.name]
            if not rider_row.empty:
                expected_points = rider_row.iloc[0]['expected_points']
                teammate_bonus = rider_row.iloc[0].get('teammate_bonus_potential', 0.0)
                total_points = expected_points + teammate_bonus
                rider_points.append((rider.name, expected_points, teammate_bonus, total_points))
        
        rider_points.sort(key=lambda x: x[3], reverse=True)  # Sort by total points
        print(f"\nTop 5 riders by total expected points (including teammate bonuses):")
        for i, (rider_name, base_points, teammate_bonus, total_points) in enumerate(rider_points[:5], 1):
            print(f"  {i}. {rider_name}: {base_points:.2f} base + {teammate_bonus:.2f} bonus = {total_points:.2f} total")
    
    # For the main example, use mean metric with teammate bonus analysis
    print(f"\n{'='*20} Main Example (using MEAN metric with teammate bonus analysis) {'='*20}")
    
    # Run simulations to get expected points with teammate bonus analysis
    rider_data = optimizer.run_simulation_with_teammate_analysis(num_simulations=50, metric='mean')
    
    print(f"\nAnalyzed {len(rider_data)} riders")
    print(f"Average expected points: {rider_data['expected_points'].mean():.2f}")
    print(f"Average teammate bonus potential: {rider_data['teammate_bonus_potential'].mean():.2f}")
    print(f"Total budget available: {optimizer.budget}")
    
    # Generate Pareto-optimal teams with teammate bonus consideration
    print(f"\n{'='*20} Generating Pareto-Optimal Teams with Teammate Bonus Analysis {'='*20}")
    
    # Test different teammate bonus weights
    teammate_bonus_weights = [0.0, 0.5, 1.0, 1.5, 2.0]
    pareto_teams = []
    
    for weight in teammate_bonus_weights:
        print(f"\nGenerating team with teammate bonus weight: {weight}")
        try:
            team = optimizer.optimize_team_with_teammate_bonuses(
                rider_data, 
                num_simulations=30,
                risk_aversion=0.0, 
                abandon_penalty=1.0,
                teammate_bonus_weight=weight
            )
            pareto_teams.append((weight, team))
        except ValueError as e:
            print(f"Failed to generate team with weight {weight}: {e}")
            continue
    
    print(f"\nGenerated {len(pareto_teams)} Pareto-optimal teams with different teammate bonus weights:")
    for weight, team in pareto_teams:
        diagnostics = optimizer.get_team_diagnostics(team, rider_data)
        print(f"\nTeam (Teammate Bonus Weight: {weight}):")
        print(f"  - Expected Points: {team.expected_points:.2f}")
        print(f"  - Total Cost: {team.total_cost:.2f}")
        print(f"  - Cost Efficiency: {diagnostics['cost_efficiency']:.2f} points/euro")
        print(f"  - Risk Level: {diagnostics['risk_metrics']['risk_percentage']:.1%}")
        print(f"  - Abandon Risk: {diagnostics['abandon_risk']:.1%}")
        print(f"  - Teammate Bonus Teams: {diagnostics['team_composition']['teammate_bonus_potential']}")
        print(f"  - Riders: {', '.join(team.rider_names[:5])}{'...' if len(team.rider_names) > 5 else ''}")
    
    # Optimize team with advanced stage selection and teammate bonuses
    print("\nOptimizing team selection with stage-by-stage analysis and teammate bonuses...")
    optimal_team = optimizer.optimize_with_stage_selection_and_teammate_bonuses(
        rider_data, 
        num_simulations=50, 
        risk_aversion=0.0, 
        abandon_penalty=1.0,
        teammate_bonus_weight=1.0
    )
    
    print(f"\nOptimal Team with Stage Selection and Teammate Bonuses:")
    print(optimal_team)
    
    # Get comprehensive diagnostics
    diagnostics = optimizer.get_team_diagnostics(optimal_team, rider_data)
    print(f"\nComprehensive Team Diagnostics with Teammate Bonuses:")
    print(f"  - Team Size: {diagnostics['team_size']}")
    print(f"  - Total Cost: {diagnostics['total_cost']:.2f}")
    print(f"  - Expected Points: {diagnostics['expected_points']:.2f}")
    print(f"  - Cost Efficiency: {diagnostics['cost_efficiency']:.2f} points per euro")
    print(f"  - Budget Utilization: {diagnostics['budget_utilization']:.1%}")
    print(f"  - Total Risk (Std): {diagnostics['risk_metrics']['total_std']:.2f}")
    print(f"  - Average Risk per Rider: {diagnostics['risk_metrics']['avg_std_per_rider']:.2f}")
    print(f"  - Risk Percentage: {diagnostics['risk_metrics']['risk_percentage']:.1%}")
    print(f"  - Average Abandon Risk: {diagnostics['abandon_risk']:.1%}")
    print(f"  - Unique Teams: {diagnostics['team_composition']['unique_teams']}")
    print(f"  - Teammate Bonus Potential: {diagnostics['team_composition']['teammate_bonus_potential']} teams")
    
    # Analyze teammate bonus impact
    print(f"\nTeammate Bonus Impact Analysis:")
    
    # Calculate total teammate bonus potential for the selected team
    total_teammate_bonus = 0
    team_composition = {}
    
    for rider in optimal_team.riders:
        rider_row = rider_data[rider_data['rider_name'] == rider.name]
        if not rider_row.empty:
            teammate_bonus = rider_row.iloc[0].get('teammate_bonus_potential', 0.0)
            total_teammate_bonus += teammate_bonus
            
            # Track team composition
            if rider.team not in team_composition:
                team_composition[rider.team] = []
            team_composition[rider.team].append(rider.name)
    
    print(f"  - Total Teammate Bonus Potential: {total_teammate_bonus:.2f} points")
    print(f"  - Average Teammate Bonus per Rider: {total_teammate_bonus / len(optimal_team.riders):.2f} points")
    print(f"  - Percentage of Points from Teammate Bonuses: {(total_teammate_bonus / optimal_team.expected_points * 100):.1f}%")
    
    print(f"\nTeam composition for teammate bonus analysis:")
    for team, riders in sorted(team_composition.items()):
        team_bonus = sum(rider_data[rider_data['rider_name'] == rider].iloc[0].get('teammate_bonus_potential', 0.0) 
                        for rider in riders)
        print(f"  - {team}: {len(riders)} riders, {team_bonus:.2f} bonus points potential")
    
    # Print stage-by-stage information
    if optimal_team.stage_selections:
        print(f"\nStage-by-Stage Selections (with teammate bonus consideration):")
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
                teammate_bonus = rider_row.get('teammate_bonus_potential', 0.0)
                is_selected = rider_name in selected_riders
                all_rider_points.append((rider_name, points, teammate_bonus, is_selected, rider_row['team']))
            
            # Sort by points (descending) and show top 15
            all_rider_points.sort(key=lambda x: x[1], reverse=True)
            
            print(f"\nStage {stage} - Top 15 Expected Points:")
            print(f"{'Rank':<4} {'Rider':<20} {'Team':<15} {'Points':<8} {'Bonus':<8} {'Selected':<8}")
            print("-" * 70)
            for i, (rider_name, points, teammate_bonus, is_selected, team) in enumerate(all_rider_points[:15], 1):
                selected_mark = "✓" if is_selected else ""
                print(f"{i:<4} {rider_name:<20} {team:<15} {points:<8.2f} {teammate_bonus:<8.2f} {selected_mark:<8}")
            
            # Show total points for selected riders
            total_selected_points = sum(points for _, points, _, is_selected, _ in all_rider_points if is_selected)
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
                teammate_bonus = rider_row.get('teammate_bonus_potential', 0.0)
                print(f"  {rider} ({rider_row['team']}) - Stage {stage}: {points:.2f} points (bonus potential: {teammate_bonus:.2f})")
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
            team_bonus = sum(rider_data[rider_data['rider_name'] == rider].iloc[0].get('teammate_bonus_potential', 0.0) 
                            for rider in riders)
            print(f"  {team}: {len(riders)} riders - {', '.join(riders)} (bonus potential: {team_bonus:.2f})")
    
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
