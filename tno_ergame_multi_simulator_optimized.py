import pandas as pd
import numpy as np
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
from riders import RiderDatabase, Rider
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple
import json
from datetime import datetime

class TNOMultiSimulationAnalyzerOptimized:
    def __init__(self, num_simulations=100):
        self.num_simulations = num_simulations
        self.num_stages = 21
        self.results = []
        self.metrics = {}
        
    def run_simulations(self, team_selection: TNOTeamSelection, progress_callback=None):
        """Run multiple simulations efficiently without parallelization"""
        print(f"Running {self.num_simulations} TNO-Ergame simulations (optimized)...")
        
        self.results = []
        
        # Run simulations sequentially for better compatibility with Streamlit
        for sim in range(self.num_simulations):
            if progress_callback:
                progress_callback(sim + 1, self.num_simulations)
            
            # Create simulator with the team selection
            sim_obj = TNOSimulator(team_selection)
            
            # Run simulation
            sim_obj.simulate_tour()
            self.results.append(sim_obj)
        
        self._calculate_comprehensive_metrics()
        return self.metrics
    
    def _calculate_comprehensive_metrics(self):
        """Calculate all comprehensive metrics from simulation results"""
        print("Calculating comprehensive TNO-Ergame metrics...")
        
        # Initialize data structures
        self.metrics = {
            'tno_analysis': self._analyze_tno_points(),
            'team_performance': self._analyze_team_performance(),
            'rider_performance': self._analyze_rider_performance(),
            'simulation_summary': self._create_simulation_summary()
        }
    
    def _analyze_tno_points(self) -> Dict:
        """Analyze TNO points distribution and patterns"""
        
        # 1. Calculate total points per rider per simulation
        rider_total_points = {}  # {rider_name: [points_sim1, points_sim2, ...]}
        
        for sim in self.results:
            # Get final TNO points for each rider
            sim_totals = sim.tno_points.copy()
            
            # Store this simulation's totals
            for rider, total in sim_totals.items():
                if rider not in rider_total_points:
                    rider_total_points[rider] = []
                rider_total_points[rider].append(total)
        
        # Calculate statistics for each rider
        rider_stats = {}
        for rider, points_list in rider_total_points.items():
            rider_stats[rider] = {
                'mean': np.mean(points_list),
                'median': np.median(points_list),
                'std': np.std(points_list),
                'min': np.min(points_list),
                'max': np.max(points_list),
                'count': len(points_list)
            }
        
        # 2. Calculate stage-by-stage points per rider per simulation
        stage_analysis = {}
        
        for stage in range(1, 22):  # Stages 1-21
            stage_points = {}  # {rider_name: [points_sim1, points_sim2, ...]}
            
            for sim in self.results:
                # Get points earned in this specific stage
                stage_records = [r for r in sim.stage_results_records if r['stage'] == stage]
                
                for record in stage_records:
                    rider = record['rider']
                    points = record['tno_points']
                    
                    if rider not in stage_points:
                        stage_points[rider] = []
                    stage_points[rider].append(points)
            
            # Calculate statistics for this stage
            stage_rider_stats = []
            for rider, points_list in stage_points.items():
                if points_list:  # Only include riders who scored points in this stage
                    stage_rider_stats.append({
                        'rider': rider,
                        'mean': np.mean(points_list),
                        'std': np.std(points_list),
                        'count': len(points_list)
                    })
            
            stage_analysis[stage] = {
                'rider_stats': stage_rider_stats,
                'total_points': sum([np.mean(points) for points in stage_points.values()]) if stage_points else 0,
                'avg_points': np.mean([np.mean(points) for points in stage_points.values()]) if stage_points else 0
            }
        
        return {
            'rider_stats': rider_stats,
            'stage_analysis': stage_analysis,
            'top_scorers': dict(sorted(rider_stats.items(), key=lambda x: x[1]['mean'], reverse=True)[:20])
        }
    
    def _analyze_team_performance(self) -> Dict:
        """Analyze overall team performance across simulations"""
        team_performances = []
        
        for sim in self.results:
            team_perf = sim.get_team_performance()
            team_performances.append(team_perf)
        
        # Calculate team performance statistics
        total_points_list = [p['total_points'] for p in team_performances]
        abandonments_list = [p['abandonments'] for p in team_performances]
        scoring_riders_list = [p['scoring_riders'] for p in team_performances]
        bonus_riders_list = [p['bonus_riders'] for p in team_performances]
        
        # Calculate riders remaining (20 - abandonments)
        riders_remaining_list = [20 - p['abandonments'] for p in team_performances]
        
        return {
            'total_points': {
                'mean': np.mean(total_points_list),
                'median': np.median(total_points_list),
                'std': np.std(total_points_list),
                'min': np.min(total_points_list),
                'max': np.max(total_points_list)
            },
            'abandonments': {
                'mean': np.mean(abandonments_list),
                'median': np.median(abandonments_list),
                'std': np.std(abandonments_list),
                'min': np.min(abandonments_list),
                'max': np.max(abandonments_list)
            },
            'riders_remaining': {
                'mean': np.mean(riders_remaining_list),
                'median': np.median(riders_remaining_list),
                'std': np.std(riders_remaining_list),
                'min': np.min(riders_remaining_list),
                'max': np.max(riders_remaining_list)
            },
            'scoring_riders': {
                'mean': np.mean(scoring_riders_list),
                'median': np.median(scoring_riders_list),
                'std': np.std(scoring_riders_list),
                'min': np.min(scoring_riders_list),
                'max': np.max(scoring_riders_list)
            },
            'bonus_riders': {
                'mean': np.mean(bonus_riders_list),
                'median': np.median(bonus_riders_list),
                'std': np.std(bonus_riders_list),
                'min': np.min(bonus_riders_list),
                'max': np.max(bonus_riders_list)
            }
        }
    
    def _analyze_rider_performance(self) -> Dict:
        """Analyze individual rider performance within the team context"""
        rider_performances = defaultdict(list)
        
        for sim in self.results:
            # Get rider performance for this simulation
            for record in sim.stage_results_records:
                rider = record['rider']
                stage = record['stage']
                position = record['position']
                tno_points = record['tno_points']
                
                rider_performances[rider].append({
                    'stage': stage,
                    'position': position,
                    'tno_points': tno_points,
                    'simulation': len(rider_performances[rider]) // 21  # Approximate simulation number
                })
        
        # Calculate rider statistics
        rider_stats = {}
        for rider, performances in rider_performances.items():
            positions = [p['position'] for p in performances if p['position'] is not None]
            points = [p['tno_points'] for p in performances]
            
            rider_stats[rider] = {
                'avg_position': np.mean(positions) if positions else None,
                'best_position': np.min(positions) if positions else None,
                'worst_position': np.max(positions) if positions else None,
                'total_points': np.sum(points),
                'avg_points_per_stage': np.mean(points),
                'stages_ridden': len(performances),
                'top_10_finishes': sum(1 for p in positions if p <= 10),
                'top_5_finishes': sum(1 for p in positions if p <= 5),
                'stage_wins': sum(1 for p in positions if p == 1)
            }
        
        return rider_stats
    
    def _create_simulation_summary(self) -> Dict:
        """Create overall simulation summary statistics"""
        total_riders = len(self.results[0].team_selection.riders) if self.results else 0
        
        # Calculate average abandonments
        avg_abandonments = np.mean([len(sim.abandoned_riders) for sim in self.results])
        
        # Calculate average TNO points per simulation
        avg_total_points = np.mean([
            sum(sim.tno_points.values())
            for sim in self.results
        ])
        
        return {
            'total_simulations': self.num_simulations,
            'total_riders': total_riders,
            'avg_abandonments': avg_abandonments,
            'avg_total_points': avg_total_points,
            'simulation_date': datetime.now().isoformat()
        }
    
    def get_rider_expected_points(self) -> pd.DataFrame:
        """Get expected points for each rider (for optimization)"""
        if not self.results:
            return pd.DataFrame()
        
        # Calculate expected points for each rider
        rider_points = defaultdict(list)
        
        for sim in self.results:
            for rider, points in sim.tno_points.items():
                rider_points[rider].append(points)
        
        # Create DataFrame with expected points
        expected_points_data = []
        for rider, points_list in rider_points.items():
            expected_points_data.append({
                'rider': rider,
                'expected_points': np.mean(points_list),
                'std_points': np.std(points_list),
                'min_points': np.min(points_list),
                'max_points': np.max(points_list)
            })
        
        return pd.DataFrame(expected_points_data)
    
    def save_metrics_to_json(self, filename='tno_ergame_multi_simulation_metrics_optimized.json'):
        """Save metrics to JSON file"""
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)

# Legacy functions for backward compatibility
def run_tno_multi_simulation_optimized(team_selection: TNOTeamSelection, num_simulations: int, progress_callback=None):
    """Run multiple TNO simulations efficiently"""
    analyzer = TNOMultiSimulationAnalyzerOptimized(num_simulations)
    return analyzer.run_simulations(team_selection, progress_callback)

def analyze_rider_performance_for_optimization_optimized(team_selection: TNOTeamSelection, num_simulations: int = 100) -> pd.DataFrame:
    """Analyze rider performance for optimization (optimized version)"""
    analyzer = TNOMultiSimulationAnalyzerOptimized(num_simulations)
    analyzer.run_simulations(team_selection)
    return analyzer.get_rider_expected_points()

if __name__ == "__main__":
    # Example usage
    from riders import RiderDatabase
    
    rider_db = RiderDatabase()
    all_riders = rider_db.get_all_riders()
    team_selection = TNOTeamSelection(all_riders[:20])
    
    analyzer = TNOMultiSimulationAnalyzerOptimized(100)
    metrics = analyzer.run_simulations(team_selection)
    
    # Save metrics to JSON for inspection
    analyzer.save_metrics_to_json()
    
    print("Optimized TNO multi-simulation completed!") 