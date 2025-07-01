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

class TNOMultiSimulationAnalyzer:
    def __init__(self, num_simulations=100):
        self.num_simulations = num_simulations
        self.num_stages = 21
        self.results = []
        self.metrics = {}
        
    def run_simulations(self, team_selection: TNOTeamSelection, progress_callback=None):
        """Run multiple simulations and collect comprehensive data"""
        # Running TNO-Ergame simulations
        
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
        # Calculating comprehensive TNO-Ergame metrics
        
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
            'team_cost': team_performances[0]['team_cost'] if team_performances else 0
        }
    
    def _analyze_rider_performance(self) -> Dict:
        """Analyze individual rider performance within the team"""
        team_rider_names = set(self.results[0].team_selection.rider_names) if self.results else set()
        
        rider_performances = {}
        for rider_name in team_rider_names:
            rider_points = []
            rider_abandonments = 0
            
            for sim in self.results:
                points = sim.tno_points.get(rider_name, 0)
                rider_points.append(points)
                
                if rider_name in sim.abandoned_riders:
                    rider_abandonments += 1
            
            rider_performances[rider_name] = {
                'mean_points': np.mean(rider_points),
                'median_points': np.median(rider_points),
                'std_points': np.std(rider_points),
                'min_points': np.min(rider_points),
                'max_points': np.max(rider_points),
                'abandonment_rate': rider_abandonments / self.num_simulations,
                'total_abandonments': rider_abandonments
            }
        
        return rider_performances
    
    def _create_simulation_summary(self) -> Dict:
        """Create overall simulation summary statistics"""
        total_riders = len(self.results[0].rider_db.get_all_riders()) if self.results else 0
        
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
        """Get expected points for each rider based on simulations"""
        rider_stats = self.metrics['tno_analysis']['rider_stats']
        
        # Create DataFrame with rider information
        rider_data = []
        for rider_name, stats in rider_stats.items():
            rider_data.append({
                'rider_name': rider_name,
                'expected_points': stats['mean'],
                'points_std': stats['std'],
                'points_median': stats['median'],
                'points_min': stats['min'],
                'points_max': stats['max'],
                'simulation_count': stats['count']
            })
        
        return pd.DataFrame(rider_data)
    
    def save_metrics_to_json(self, filename='tno_ergame_multi_simulation_metrics.json'):
        """Save metrics to JSON file for inspection"""
        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2, default=str)

# Legacy function for backward compatibility
def run_tno_multi_simulation(team_selection: TNOTeamSelection, num_simulations: int, progress_callback=None):
    """Run multiple TNO-Ergame simulations and return comprehensive metrics"""
    analyzer = TNOMultiSimulationAnalyzer(num_simulations)
    return analyzer.run_simulations(team_selection, progress_callback)

def analyze_rider_performance_for_optimization(team_selection: TNOTeamSelection, num_simulations: int = 100) -> pd.DataFrame:
    """Analyze rider performance to get expected points for optimization"""
    analyzer = TNOMultiSimulationAnalyzer(num_simulations)
    analyzer.run_simulations(team_selection)
    return analyzer.get_rider_expected_points()

if __name__ == "__main__":
    # Example usage
    from riders import RiderDatabase
    
    # Create a sample team selection
    rider_db = RiderDatabase()
    all_riders = rider_db.get_all_riders()
    sample_team = TNOTeamSelection(all_riders[:20])
    
            # Sample team cost and riders for reference
    
    # Run multi-simulation analysis
    analyzer = TNOMultiSimulationAnalyzer(50)  # 50 simulations for testing
    metrics = analyzer.run_simulations(sample_team)
    
    # Save metrics to JSON
    analyzer.save_metrics_to_json()
    
    # Get expected points for optimization
    expected_points_df = analyzer.get_rider_expected_points() 