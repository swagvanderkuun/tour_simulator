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
        scorito_data = []
        
        for sim in self.results:
            for record in sim.scorito_points_records:
                # Get team for this rider
                team = None
                for rider in sim.rider_db.get_all_riders():
                    if rider.name == record['rider']:
                        team = rider.team
                        break
                
                scorito_data.append({
                    'rider': record['rider'],
                    'stage': record['stage'],
                    'points': record['scorito_points'],
                    'team': team
                })
        
        df = pd.DataFrame(scorito_data)
        
        # Basic statistics
        total_points_by_rider = df.groupby('rider')['points'].sum()
        avg_points_by_rider = df.groupby('rider')['points'].mean()
        points_std_by_rider = df.groupby('rider')['points'].std()
        
        # Variance analysis
        variance_analysis = {
            'overall_variance': df['points'].var(),
            'rider_variance': points_std_by_rider.to_dict(),
            'high_variance_riders': points_std_by_rider[points_std_by_rider > points_std_by_rider.quantile(0.75)].to_dict(),
            'low_variance_riders': points_std_by_rider[points_std_by_rider < points_std_by_rider.quantile(0.25)].to_dict()
        }
        
        # Outlier analysis
        q1 = df['points'].quantile(0.25)
        q3 = df['points'].quantile(0.75)
        iqr = q3 - q1
        outlier_threshold = q3 + 1.5 * iqr
        
        outliers = df[df['points'] > outlier_threshold]
        outlier_analysis = {
            'outlier_threshold': outlier_threshold,
            'outlier_count': len(outliers),
            'outlier_percentage': len(outliers) / len(df) * 100,
            'top_outliers': outliers.nlargest(10, 'points')[['rider', 'stage', 'points', 'team']].to_dict('records'),
            'outlier_riders': outliers.groupby('rider')['points'].count().to_dict()
        }
        
        # Stage-by-stage analysis
        stage_analysis = {}
        for stage in range(1, self.num_stages + 1):
            stage_data = df[df['stage'] == stage]
            if not stage_data.empty:
                stage_analysis[stage] = {
                    'total_points': stage_data['points'].sum(),
                    'avg_points': stage_data['points'].mean(),
                    'points_std': stage_data['points'].std(),
                    'max_points': stage_data['points'].max(),
                    'min_points': stage_data['points'].min(),
                    'top_scorers': stage_data.nlargest(5, 'points')[['rider', 'points', 'team']].to_dict('records'),
                    'points_distribution': {
                        '0-10': len(stage_data[stage_data['points'] <= 10]),
                        '11-25': len(stage_data[(stage_data['points'] > 10) & (stage_data['points'] <= 25)]),
                        '26-50': len(stage_data[(stage_data['points'] > 25) & (stage_data['points'] <= 50)]),
                        '51-100': len(stage_data[(stage_data['points'] > 50) & (stage_data['points'] <= 100)]),
                        '100+': len(stage_data[stage_data['points'] > 100])
                    }
                }
        
        # Points per price analysis
        price_data = {}
        for sim in self.results:
            for rider in sim.rider_db.get_all_riders():
                if rider.name not in price_data:
                    price_data[rider.name] = {
                        'price': rider.price,
                        'total_points': [],
                        'team': rider.team
                    }
                
                # Get total Scorito points for this rider in this simulation
                rider_points = sum([record['scorito_points'] for record in sim.scorito_points_records if record['rider'] == rider.name])
                price_data[rider.name]['total_points'].append(rider_points)
        
        price_value_analysis = {}
        for rider, data in price_data.items():
            if data['total_points']:
                avg_points = np.mean(data['total_points'])
                points_std = np.std(data['total_points'])
                
                price_value_analysis[rider] = {
                    'price': data['price'],
                    'avg_total_points': avg_points,
                    'points_std': points_std,
                    'points_per_euro': avg_points / data['price'] if data['price'] > 0 else 0,
                    'value_score': avg_points / (data['price'] * (1 + points_std/100)),  # Higher is better
                    'team': data['team'],
                    'consistency': 1 / (1 + points_std)  # Higher is more consistent
                }
        
        # Top value riders (high points per euro)
        value_riders = sorted(price_value_analysis.items(), key=lambda x: x[1]['points_per_euro'], reverse=True)
        top_value_riders = dict(value_riders[:20])
        
        # Consistency analysis
        consistency_analysis = {
            'most_consistent': sorted(price_value_analysis.items(), key=lambda x: x[1]['consistency'], reverse=True)[:10],
            'least_consistent': sorted(price_value_analysis.items(), key=lambda x: x[1]['consistency'])[:10]
        }
        
        return {
            'basic_stats': {
                'total_points_by_rider': total_points_by_rider.to_dict(),
                'avg_points_by_rider': avg_points_by_rider.to_dict(),
                'points_std_by_rider': points_std_by_rider.to_dict(),
                'top_scorers': total_points_by_rider.nlargest(20).to_dict(),
                'points_by_team': df.groupby('team')['points'].sum().to_dict()
            },
            'variance_analysis': variance_analysis,
            'outlier_analysis': outlier_analysis,
            'stage_analysis': stage_analysis,
            'price_value_analysis': price_value_analysis,
            'top_value_riders': top_value_riders,
            'consistency_analysis': consistency_analysis,
            'overall_summary': {
                'total_simulations': self.num_simulations,
                'total_points_scored': df['points'].sum(),
                'avg_points_per_stage': df['points'].mean(),
                'unique_riders': df['rider'].nunique(),
                'unique_teams': df['team'].nunique()
            }
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