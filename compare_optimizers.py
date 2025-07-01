import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from tno_optimizer import TNOTeamOptimizer, TNOTeamOptimization
from tno_heuristic_optimizer import TNOHeuristicOptimizer, TNOHeuristicOptimization
import warnings
warnings.filterwarnings('ignore')

def compare_optimizers(num_simulations: int = 100):
    """
    Compare the original optimizer with the heuristic optimizer.
    
    Args:
        num_simulations: Number of simulations to run for both optimizers
    """
    print("="*80)
    print("COMPARING TNO-ERGAME OPTIMIZERS")
    print("="*80)
    
    # Run original optimizer
    print("\n1. Running Original Optimizer...")
    original_optimizer = TNOTeamOptimizer()
    original_rider_data = original_optimizer.run_simulation_for_riders(num_simulations)
    original_optimization = original_optimizer.optimize_team_with_order(
        original_rider_data, num_simulations
    )
    
    # Run heuristic optimizer
    print("\n2. Running Heuristic Optimizer...")
    heuristic_optimizer = TNOHeuristicOptimizer()
    heuristic_optimization = heuristic_optimizer.run_heuristic_optimization(num_simulations)
    
    # Compare results
    print("\n" + "="*80)
    print("COMPARISON RESULTS")
    print("="*80)
    
    # Summary comparison
    print(f"\nSUMMARY COMPARISON:")
    print(f"{'Metric':<25} {'Original':<15} {'Heuristic':<15} {'Difference':<15}")
    print("-" * 70)
    print(f"{'Expected Points':<25} {original_optimization.expected_points:<15.2f} "
          f"{heuristic_optimization.expected_points:<15.2f} "
          f"{heuristic_optimization.expected_points - original_optimization.expected_points:<15.2f}")
    print(f"{'Total Cost':<25} {original_optimization.total_cost:<15.2f} "
          f"{heuristic_optimization.total_cost:<15.2f} "
          f"{heuristic_optimization.total_cost - original_optimization.total_cost:<15.2f}")
    
    # Rider order comparison
    print(f"\nRIDER ORDER COMPARISON:")
    print(f"{'Position':<10} {'Original':<25} {'Heuristic':<25} {'Same?':<8}")
    print("-" * 68)
    
    max_positions = max(len(original_optimization.rider_order), len(heuristic_optimization.rider_order))
    
    for i in range(max_positions):
        original_rider = original_optimization.rider_order[i] if i < len(original_optimization.rider_order) else "N/A"
        heuristic_rider = heuristic_optimization.rider_order[i] if i < len(heuristic_optimization.rider_order) else "N/A"
        same = "YES" if original_rider == heuristic_rider else "NO"
        
        rider_type = ""
        if i < 5:
            rider_type = " (BONUS)"
        elif i < 15:
            rider_type = " (SCORING)"
        else:
            rider_type = " (RESERVE)"
        
        print(f"{i+1:<10} {original_rider:<25} {heuristic_rider:<25} {same:<8}{rider_type}")
    
    # Top 10 expectations comparison for first 15 riders
    print(f"\nTOP 10 EXPECTATIONS COMPARISON (First 15 Riders):")
    print(f"{'Position':<10} {'Rider':<20} {'Original Top10':<15} {'Heuristic Top10':<15} {'Diff':<10}")
    print("-" * 75)
    
    for i in range(min(15, len(original_optimization.rider_order))):
        original_rider = original_optimization.rider_order[i]
        heuristic_rider = heuristic_optimization.rider_order[i]
        
        # Get top 10 expectations from heuristic optimizer
        original_top10 = 0  # We don't have this in original optimizer
        heuristic_top10 = heuristic_optimization.rider_stats[heuristic_rider]['expected_top10_results']
        
        print(f"{i+1:<10} {heuristic_rider:<20} {original_top10:<15.2f} {heuristic_top10:<15.2f} "
              f"{heuristic_top10 - original_top10:<10.2f}")
    
    # Detailed rider statistics
    print(f"\nDETAILED RIDER STATISTICS (Heuristic Optimizer):")
    print(f"{'Position':<10} {'Rider':<20} {'Expected Points':<15} {'Expected Top10':<15} {'Cost':<8} {'Team':<12}")
    print("-" * 85)
    
    for i, rider_name in enumerate(heuristic_optimization.rider_order):
        stats = heuristic_optimization.rider_stats[rider_name]
        rider_type = "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE"
        print(f"{i+1:<10} {rider_name:<20} {stats['expected_points']:<15.2f} "
              f"{stats['expected_top10_results']:<15.2f} {stats['price']:<8.2f} {stats['team']:<12} {rider_type}")
    
    # Save comparison results
    save_comparison_results(original_optimization, heuristic_optimization)
    
    return original_optimization, heuristic_optimization

def save_comparison_results(original_opt: TNOTeamOptimization, 
                           heuristic_opt: TNOHeuristicOptimization,
                           filename: str = 'tno_optimizer_comparison.xlsx'):
    """Save comparison results to Excel file."""
    
    # Create comparison DataFrame
    comparison_data = []
    
    max_positions = max(len(original_opt.rider_order), len(heuristic_opt.rider_order))
    
    for i in range(max_positions):
        original_rider = original_opt.rider_order[i] if i < len(original_opt.rider_order) else "N/A"
        heuristic_rider = heuristic_opt.rider_order[i] if i < len(heuristic_opt.rider_order) else "N/A"
        
        # Get heuristic stats
        heuristic_stats = heuristic_opt.rider_stats.get(heuristic_rider, {})
        
        comparison_data.append({
            'position': i + 1,
            'original_rider': original_rider,
            'heuristic_rider': heuristic_rider,
            'same_rider': original_rider == heuristic_rider,
            'expected_points': heuristic_stats.get('expected_points', 0),
            'expected_top10_results': heuristic_stats.get('expected_top10_results', 0),
            'price': heuristic_stats.get('price', 0),
            'team': heuristic_stats.get('team', ''),
            'chance_of_abandon': heuristic_stats.get('chance_of_abandon', 0),
            'rider_type': "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE"
        })
    
    df = pd.DataFrame(comparison_data)
    
    # Save to Excel
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Comparison', index=False)
        
        # Add summary sheet
        summary_data = {
            'Metric': [
                'Original Expected Points',
                'Heuristic Expected Points',
                'Points Difference',
                'Original Total Cost',
                'Heuristic Total Cost',
                'Cost Difference',
                'Same Riders in Top 5',
                'Same Riders in Top 15',
                'Same Riders in Reserves'
            ],
            'Value': [
                original_opt.expected_points,
                heuristic_opt.expected_points,
                heuristic_opt.expected_points - original_opt.expected_points,
                original_opt.total_cost,
                heuristic_opt.total_cost,
                heuristic_opt.total_cost - original_opt.total_cost,
                sum(1 for i in range(5) if original_opt.rider_order[i] == heuristic_opt.rider_order[i]),
                sum(1 for i in range(15) if original_opt.rider_order[i] == heuristic_opt.rider_order[i]),
                sum(1 for i in range(15, 20) if original_opt.rider_order[i] == heuristic_opt.rider_order[i])
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"\nComparison results saved to {filename}")

def main():
    """Run the optimizer comparison."""
    print("Starting TNO-Ergame Optimizer Comparison...")
    
    # Run comparison
    original_opt, heuristic_opt = compare_optimizers(num_simulations=100)
    
    print(f"\n" + "="*80)
    print("COMPARISON COMPLETED")
    print("="*80)
    
    # Key insights
    print(f"\nKEY INSIGHTS:")
    print(f"• Original Optimizer Expected Points: {original_opt.expected_points:.2f}")
    print(f"• Heuristic Optimizer Expected Points: {heuristic_opt.expected_points:.2f}")
    print(f"• Points Difference: {heuristic_opt.expected_points - original_opt.expected_points:.2f}")
    
    if heuristic_opt.expected_points > original_opt.expected_points:
        print(f"• Heuristic optimizer performs BETTER by {heuristic_opt.expected_points - original_opt.expected_points:.2f} points")
    elif heuristic_opt.expected_points < original_opt.expected_points:
        print(f"• Original optimizer performs BETTER by {original_opt.expected_points - heuristic_opt.expected_points:.2f} points")
    else:
        print(f"• Both optimizers perform EQUALLY")
    
    # Check if top riders are in expected positions
    expected_top_riders = ['Pogacar', 'Vingegaard', 'Evenepoel', 'Merlier', 'Philipsen']
    print(f"\nTOP RIDER POSITIONS (Heuristic):")
    for rider in expected_top_riders:
        if rider in heuristic_opt.rider_order:
            position = heuristic_opt.rider_order.index(rider) + 1
            rider_type = "BONUS" if position <= 5 else "SCORING" if position <= 15 else "RESERVE"
            print(f"• {rider}: Position {position} ({rider_type})")
        else:
            print(f"• {rider}: Not selected")

if __name__ == "__main__":
    main() 