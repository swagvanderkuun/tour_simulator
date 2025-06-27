import pandas as pd
import numpy as np
from simulator import TourSimulator
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple
import json
from datetime import datetime

class MultiSimulationAnalyzer:
    def __init__(self, num_simulations=100):
        self.num_simulations = num_simulations
        self.num_stages = 21
        self.results = []
        self.metrics = {}
        
    def run_simulations(self, rider_db, progress_callback=None):
        """Run multiple simulations and collect comprehensive data"""
        print(f"Running {self.num_simulations} simulations...")
        
        for sim in range(self.num_simulations):
            if progress_callback:
                progress_callback(sim + 1, self.num_simulations)
            
            # Create simulator with custom rider database
            sim_obj = TourSimulator()
            sim_obj.rider_db = rider_db
            sim_obj.youth_rider_names = set(r.name for r in rider_db.get_all_riders() if r.age < 25)
            
            # Run simulation
            sim_obj.simulate_tour()
            self.results.append(sim_obj)
            
        self._calculate_comprehensive_metrics()
        return self.metrics
    
    def _calculate_comprehensive_metrics(self):
        """Calculate all comprehensive metrics from simulation results"""
        print("Calculating comprehensive metrics...")
        
        # Initialize data structures
        self.metrics = {
            'scorito_analysis': self._analyze_scorito_points(),
            'simulation_summary': self._create_simulation_summary()
        }
    
    def _analyze_scorito_points(self) -> Dict:
        """Analyze Scorito points distribution and patterns"""
        
        # 1. Calculate total points per rider per simulation (for overall rankings)
        # Use the final stage (stage 22) which contains the total cumulative points
        rider_total_points = {}  # {rider_name: [points_sim1, points_sim2, ...]}
        
        for sim in self.results:
            # Get final cumulative points for each rider (stage 22 or last stage)
            sim_totals = {}
            for record in sim.scorito_points_records:
                rider = record['rider']
                stage = record['stage']
                points = record['scorito_points']
                
                # For final stage (22), this is the total cumulative points
                if stage == 22:
                    sim_totals[rider] = points
            
            # Store this simulation's totals
            for rider, total in sim_totals.items():
                if rider not in rider_total_points:
                    rider_total_points[rider] = []
                rider_total_points[rider].append(total)
        
        # Calculate average total points per rider across all simulations
        total_points_by_rider = {}
        avg_points_by_rider = {}
        points_std_by_rider = {}
        
        for rider, points_list in rider_total_points.items():
            total_points_by_rider[rider] = np.mean(points_list)  # Average total points per simulation
            avg_points_by_rider[rider] = np.mean(points_list) / 21  # Average points per stage per simulation (21 stages)
            points_std_by_rider[rider] = np.std(points_list)  # Standard deviation of total points
        
        # 2. Calculate stage-by-stage points per rider per simulation
        stage_analysis = {}
        
        for stage in range(1, 23):  # Stages 1-22 (including final stage)
            stage_points = {}  # {rider_name: [points_sim1, points_sim2, ...]}
            
            for sim in self.results:
                # Calculate points earned in this specific stage
                if stage == 1:
                    # For stage 1, use the points directly
                    for record in sim.scorito_points_records:
                        if record['stage'] == 1:
                            rider = record['rider']
                            if rider not in stage_points:
                                stage_points[rider] = []
                            stage_points[rider].append(record['scorito_points'])
                else:
                    # For stages 2-22, calculate the difference
                    prev_stage_points = {}
                    curr_stage_points = {}
                    
                    # Get points for previous stage and current stage
                    for record in sim.scorito_points_records:
                        rider = record['rider']
                        record_stage = record['stage']
                        points = record['scorito_points']
                        
                        if record_stage == stage - 1:
                            prev_stage_points[rider] = points
                        elif record_stage == stage:
                            curr_stage_points[rider] = points
                    
                    # Calculate difference for each rider
                    for rider in curr_stage_points:
                        if rider in prev_stage_points:
                            points_earned = curr_stage_points[rider] - prev_stage_points[rider]
                            if rider not in stage_points:
                                stage_points[rider] = []
                            stage_points[rider].append(points_earned)
            
            # Calculate statistics for this stage
            stage_rider_stats = []
            for rider, points_list in stage_points.items():
                if points_list:  # Only include riders who scored points in this stage
                    stage_rider_stats.append({
                        'rider': rider,
                        'mean': np.mean(points_list),  # Average points for this stage per simulation
                        'std': np.std(points_list),
                        'count': len(points_list)
                    })
            
            stage_analysis[stage] = {
                'rider_stats': stage_rider_stats,
                'total_points': sum([np.mean(points) for points in stage_points.values()]) if stage_points else 0,
                'avg_points': np.mean([np.mean(points) for points in stage_points.values()]) if stage_points else 0
            }
        
        return {
            'basic_stats': {
                'total_points_by_rider': total_points_by_rider,
                'avg_points_by_rider': avg_points_by_rider,
                'points_std_by_rider': points_std_by_rider,
                'top_scorers': dict(sorted(total_points_by_rider.items(), key=lambda x: x[1], reverse=True)[:20])
            },
            'stage_analysis': stage_analysis
        }
    
    def _create_simulation_summary(self) -> Dict:
        """Create overall simulation summary statistics"""
        total_riders = len(self.results[0].rider_db.get_all_riders()) if self.results else 0
        
        # Calculate average abandonments
        avg_abandonments = np.mean([len(sim.abandoned_riders) for sim in self.results])
        
        # Calculate average Scorito points per simulation
        avg_total_points = np.mean([
            sum([record['scorito_points'] for record in sim.scorito_points_records])
            for sim in self.results
        ])
        
        return {
            'total_simulations': self.num_simulations,
            'total_riders': total_riders,
            'avg_abandonments': avg_abandonments,
            'avg_total_points': avg_total_points,
            'simulation_date': datetime.now().isoformat()
        }
    
    # Helper methods for calculating specific metrics
    def _calculate_points_efficiency(self, df):
        """Calculate points efficiency (points per stage)"""
        efficiency = df.groupby('rider').agg({
            'points': ['sum', 'mean', 'std'],
            'stage': 'count'
        }).round(2)
        efficiency.columns = ['total_points', 'avg_points_per_stage', 'points_std', 'stages_ridden']
        efficiency['efficiency_score'] = efficiency['total_points'] / efficiency['stages_ridden']
        return efficiency.to_dict('index')

# Legacy function for backward compatibility
def run_multi_simulation(num_simulations, rider_db, progress_callback=None):
    """Run multiple simulations and return comprehensive metrics"""
    analyzer = MultiSimulationAnalyzer(num_simulations)
    return analyzer.run_simulations(rider_db, progress_callback)

if __name__ == "__main__":
    # Example usage
    from riders import RiderDatabase
    
    rider_db = RiderDatabase()
    analyzer = MultiSimulationAnalyzer(100)
    metrics = analyzer.run_simulations(rider_db)
    
    # Save metrics to JSON for inspection
    with open('multi_simulation_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    print("Multi-simulation metrics saved to multi_simulation_metrics.json") 