import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from riders import RiderDatabase
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
from tno_ergame_multi_simulator import TNOMultiSimulationAnalyzer

st.set_page_config(
    page_title="Multi-Simulation Analysis - T(n)oer Game",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Multi-Simulation Analysis")
st.markdown("""
Explore team-independent statistics and performance patterns in TNO-Ergame simulations.
Analyze rider performance, stage characteristics, and game dynamics across multiple simulations.
""")

# Load rider database
rider_db = RiderDatabase()
all_riders = rider_db.get_all_riders()

# Analysis settings
st.header("1. Analysis Settings")

col1, col2, col3 = st.columns(3)

with col1:
    num_simulations = st.number_input(
        "Number of Simulations",
        min_value=10,
        max_value=5000,
        value=100,
        step=10,
        help="More simulations = more accurate statistics"
    )

with col2:
    analysis_type = st.selectbox(
        "Analysis Type",
        options=["Rider Performance", "Stage Analysis", "Game Dynamics", "All"],
        help="Choose what to analyze"
    )

with col3:
    if st.button("🚀 Run TNO Game Analysis", type="primary"):
        with st.spinner(f"Running {num_simulations} TNO game simulations..."):
            try:
                # Run comprehensive TNO game analysis using TourSimulator for rider performance
                from simulator import TourSimulator
                from collections import defaultdict
                import numpy as np
                
                # Initialize data collection
                rider_performance = defaultdict(list)
                stage_performance = defaultdict(list)
                points_history = []
                abandonment_counts = defaultdict(int)
                
                # Run simulations using TourSimulator
                for sim in range(num_simulations):
                    # Create and run tour simulation
                    tour_simulator = TourSimulator()
                    tour_result = tour_simulator.simulate_tour()
                    
                    # Collect rider performance data
                    for rider in all_riders:
                        rider_name = rider.name
                        
                        # Get rider's performance across all stages
                        rider_points = 0
                        rider_top_10_count = 0
                        rider_abandoned = False
                        
                        for stage_num in range(1, 22):  # Stages 1-21
                            if stage_num in tour_result.stage_results:
                                stage_result = tour_result.stage_results[stage_num]
                                
                                # Find rider's position in this stage
                                rider_position = None
                                for pos, stage_rider in enumerate(stage_result, 1):
                                    if stage_rider.name == rider_name:
                                        rider_position = pos
                                        break
                                
                                if rider_position is not None:
                                    # Count top 10 finishes
                                    if rider_position <= 10:
                                        rider_top_10_count += 1
                                    
                                    # Calculate TNO points for this stage
                                    is_special_stage = stage_num in {5, 13, 14, 17, 18}
                                    if rider_position <= 10:
                                        if is_special_stage:
                                            points = {1: 30, 2: 20, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}[rider_position]
                                        else:
                                            points = {1: 20, 2: 15, 3: 12, 4: 9, 5: 7, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1}[rider_position]
                                        rider_points += points
                                else:
                                    # Rider abandoned or didn't finish
                                    rider_abandoned = True
                        
                        # Store rider performance
                        rider_performance[rider_name].append({
                            'points': rider_points,
                            'top_10_count': rider_top_10_count,
                            'abandoned': rider_abandoned
                        })
                        
                        if rider_abandoned:
                            abandonment_counts[rider_name] += 1
                    
                    # Collect stage performance data
                    for stage_num in range(1, 22):
                        if stage_num in tour_result.stage_results:
                            stage_result = tour_result.stage_results[stage_num]
                            
                            # Calculate total points for this stage
                            stage_points = 0
                            is_special_stage = stage_num in {5, 13, 14, 17, 18}
                            
                            for pos, rider in enumerate(stage_result[:10], 1):  # Top 10 only
                                if is_special_stage:
                                    points = {1: 30, 2: 20, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}[pos]
                                else:
                                    points = {1: 20, 2: 15, 3: 12, 4: 9, 5: 7, 6: 5, 7: 4, 8: 3, 9: 2, 10: 1}[pos]
                                stage_points += points
                            
                            stage_performance[stage_num].append(stage_points)
                    
                    # Calculate total points for a sample team (first 20 riders)
                    sample_team_points = 0
                    for rider in all_riders[:20]:
                        rider_name = rider.name
                        if rider_name in rider_performance and rider_performance[rider_name]:
                            sample_team_points += rider_performance[rider_name][-1]['points']
                    
                    points_history.append(sample_team_points)
                
                # Process results into metrics format
                metrics = {
                    'team_performance': {
                        'total_points': {
                            'mean': np.mean(points_history),
                            'std': np.std(points_history),
                            'min': min(points_history),
                            'max': max(points_history)
                        },
                        'abandonments': {
                            'mean': np.mean([sum(1 for rider_data in rider_performance[rider] if rider_data['abandoned']) for rider in all_riders[:20]])
                        }
                    },
                    'points_history': points_history,
                    'tno_analysis': {
                        'top_scorers': {}
                    },
                    'stage_analysis': {},
                    'abandonment_analysis': {}
                }
                
                # Process rider performance data
                for rider_name, performances in rider_performance.items():
                    points_list = [p['points'] for p in performances]
                    top_10_counts = [p['top_10_count'] for p in performances]
                    abandonment_rate = sum(1 for p in performances if p['abandoned']) / len(performances) * 100
                    
                    metrics['tno_analysis']['top_scorers'][rider_name] = {
                        'mean': np.mean(points_list),
                        'std': np.std(points_list),
                        'min': min(points_list),
                        'max': max(points_list),
                        'top_10_count': np.mean(top_10_counts),
                        'abandonment_rate': abandonment_rate
                    }
                
                # Process stage performance data
                for stage_num, stage_points_list in stage_performance.items():
                    metrics['stage_analysis'][stage_num] = {
                        'mean': np.mean(stage_points_list),
                        'std': np.std(stage_points_list)
                    }
                
                # Process abandonment data
                for rider_name, abandon_count in abandonment_counts.items():
                    metrics['abandonment_analysis'][rider_name] = (abandon_count / num_simulations) * 100
                
                # Store results
                st.session_state.tno_analysis_results = {
                    'metrics': metrics,
                    'num_sims': num_simulations,
                    'analysis_type': analysis_type
                }
                
                st.success(f"Analysis completed! Ran {num_simulations} simulations.")
                
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.exception(e)

# Display results
if 'tno_analysis_results' in st.session_state:
    st.header("2. TNO Game Statistics")
    
    results = st.session_state.tno_analysis_results
    metrics = results['metrics']
    analysis_type = results['analysis_type']
    
    # General TNO Game Statistics
    st.subheader("📈 General TNO Game Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_points = metrics['team_performance']['total_points']['mean']
        std_points = metrics['team_performance']['total_points']['std']
        st.metric(
            "Avg Team Points", 
            f"{avg_points:.1f}",
            f"±{std_points:.1f}"
        )
    
    with col2:
        avg_abandonments = metrics['team_performance']['abandonments']['mean']
        st.metric("Avg Abandonments", f"{avg_abandonments:.1f}")
    
    with col3:
        total_riders = len(all_riders)
        st.metric("Total Riders", total_riders)
    
    with col4:
        special_stages = len({5, 13, 14, 17, 18})
        st.metric("Special Stages", special_stages)
    
    # Rider Performance Analysis
    if analysis_type in ["Rider Performance", "All"]:
        st.subheader("🏆 Rider Performance Analysis")
        
        if 'tno_analysis' in metrics and 'top_scorers' in metrics['tno_analysis']:
            top_scorers = metrics['tno_analysis']['top_scorers']
            
            # Create comprehensive rider analysis
            rider_analysis = []
            for rider, data in top_scorers.items():
                rider_obj = rider_db.get_rider(rider)
                rider_analysis.append({
                    "Rider": rider,
                    "Team": rider_obj.team,
                    "Avg Points": data['mean'],
                    "Std Points": data['std'],
                    "Min Points": data['min'],
                    "Max Points": data['max'],
                    "Top 10 Count": data.get('top_10_count', 0),
                    "Abandonment Rate": data.get('abandonment_rate', 0),
                    "Price": rider_obj.price,
                    "Age": rider_obj.age
                })
            
            rider_df = pd.DataFrame(rider_analysis).sort_values('Avg Points', ascending=False)
            
            # Top 20 riders
            st.write("**Top 20 Riders by Average Points:**")
            st.dataframe(rider_df.head(20), hide_index=True)
            
            # Rider performance chart
            fig = px.bar(
                rider_df.head(15),
                x='Rider',
                y='Avg Points',
                error_y='Std Points',
                title="Top 15 Riders by Average Points",
                labels={'Avg Points': 'Average Points', 'Rider': 'Rider Name'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            # Team performance analysis
            st.write("**Team Performance Analysis:**")
            team_performance = rider_df.groupby('Team').agg({
                'Avg Points': 'mean',
                'Rider': 'count'
            }).rename(columns={'Rider': 'Riders in Top 100'}).sort_values('Avg Points', ascending=False)
            
            st.dataframe(team_performance.head(10), hide_index=True)
    
    # Stage Analysis
    if analysis_type in ["Stage Analysis", "All"]:
        st.subheader("🏁 Stage Performance Analysis")
        
        if 'stage_analysis' in metrics:
            stage_data = metrics['stage_analysis']
            
            # Create stage performance chart
            stage_df = pd.DataFrame([
                {
                    "Stage": stage,
                    "Avg Points": data['mean'],
                    "Std Points": data['std'],
                    "Type": "Special" if stage in {5, 13, 14, 17, 18} else "Regular"
                }
                for stage, data in stage_data.items()
            ])
            
            # Stage performance by type
            fig = px.line(
                stage_df,
                x='Stage',
                y='Avg Points',
                color='Type',
                error_y='Std Points',
                title="Average Points per Stage (Regular vs Special)",
                labels={'Avg Points': 'Average Points', 'Stage': 'Stage Number'}
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Stage statistics
            col1, col2 = st.columns(2)
            
            with col1:
                regular_stages = stage_df[stage_df['Type'] == 'Regular']
                st.write("**Regular Stages Statistics:**")
                st.metric("Avg Points", f"{regular_stages['Avg Points'].mean():.2f}")
                st.metric("Std Points", f"{regular_stages['Std Points'].mean():.2f}")
            
            with col2:
                special_stages = stage_df[stage_df['Type'] == 'Special']
                st.write("**Special Stages Statistics:**")
                st.metric("Avg Points", f"{special_stages['Avg Points'].mean():.2f}")
                st.metric("Std Points", f"{special_stages['Std Points'].mean():.2f}")
    
    # Game Dynamics Analysis
    if analysis_type in ["Game Dynamics", "All"]:
        st.subheader("🎮 Game Dynamics Analysis")
        
        # Points distribution
        if 'points_history' in metrics:
            points_data = metrics['points_history']
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Points distribution histogram
                fig = px.histogram(
                    x=points_data,
                    nbins=20,
                    title="Distribution of Team Points Across Simulations",
                    labels={'x': 'Total Points', 'y': 'Frequency'}
                )
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Points statistics
                st.write("**Points Distribution Statistics:**")
                st.metric("Min Points", f"{min(points_data):.0f}")
                st.metric("Median Points", f"{pd.Series(points_data).median():.0f}")
                st.metric("Max Points", f"{max(points_data):.0f}")
                st.metric("95th Percentile", f"{pd.Series(points_data).quantile(0.95):.0f}")
        
        # Abandonment analysis
        if 'abandonment_analysis' in metrics:
            abandon_data = metrics['abandonment_analysis']
            
            # Create abandonment chart
            abandon_df = pd.DataFrame([
                {
                    "Rider": rider,
                    "Abandonment Rate": rate
                }
                for rider, rate in abandon_data.items()
            ]).sort_values('Abandonment Rate', ascending=False)
            
            st.write("**Top 15 Riders by Abandonment Rate:**")
            st.dataframe(abandon_df.head(15), hide_index=True)
            
            fig = px.bar(
                abandon_df.head(15),
                x='Rider',
                y='Abandonment Rate',
                title="Top 15 Riders by Abandonment Rate",
                labels={'Abandonment Rate': 'Abandonment Rate (%)', 'Rider': 'Rider Name'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
    
    # TNO Game Insights
    st.subheader("💡 TNO Game Insights")
    
    insights = []
    
    # Calculate insights based on the data
    if 'tno_analysis' in metrics and 'top_scorers' in metrics['tno_analysis']:
        top_scorers = metrics['tno_analysis']['top_scorers']
        
        # Best performing rider
        best_rider = max(top_scorers.items(), key=lambda x: x[1]['mean'])
        insights.append(f"🏆 **Best performing rider**: {best_rider[0]} with {best_rider[1]['mean']:.1f} avg points")
        
        # Most consistent rider (lowest std)
        most_consistent = min(top_scorers.items(), key=lambda x: x[1]['std'])
        insights.append(f"📊 **Most consistent rider**: {most_consistent[0]} with {most_consistent[1]['std']:.1f} std deviation")
        
        # Highest variance rider
        highest_variance = max(top_scorers.items(), key=lambda x: x[1]['std'])
        insights.append(f"🎲 **Highest variance rider**: {highest_variance[0]} with {highest_variance[1]['std']:.1f} std deviation")
    
    if 'stage_analysis' in metrics:
        stage_data = metrics['stage_analysis']
        
        # Highest scoring stage
        highest_stage = max(stage_data.items(), key=lambda x: x[1]['mean'])
        insights.append(f"🔥 **Highest scoring stage**: Stage {highest_stage[0]} with {highest_stage[1]['mean']:.1f} avg points")
        
        # Lowest scoring stage
        lowest_stage = min(stage_data.items(), key=lambda x: x[1]['mean'])
        insights.append(f"❄️ **Lowest scoring stage**: Stage {lowest_stage[0]} with {lowest_stage[1]['mean']:.1f} avg points")
    
    # Display insights
    for insight in insights:
        st.write(insight)
    
    # Download results
    st.subheader("💾 Download TNO Game Analysis")
    
    if st.button("Generate TNO Analysis Report"):
        # Create comprehensive TNO game analysis report
        report_data = []
        
        # Add rider performance data
        if 'tno_analysis' in metrics and 'top_scorers' in metrics['tno_analysis']:
            for rider, data in metrics['tno_analysis']['top_scorers'].items():
                rider_obj = rider_db.get_rider(rider)
                report_data.append({
                    'Type': 'Rider Performance',
                    'Rider': rider,
                    'Team': rider_obj.team,
                    'Avg Points': data['mean'],
                    'Std Points': data['std'],
                    'Min Points': data['min'],
                    'Max Points': data['max'],
                    'Price': rider_obj.price,
                    'Age': rider_obj.age
                })
        
        # Add stage analysis data
        if 'stage_analysis' in metrics:
            for stage, data in metrics['stage_analysis'].items():
                report_data.append({
                    'Type': 'Stage Analysis',
                    'Stage': stage,
                    'Avg Points': data['mean'],
                    'Std Points': data['std'],
                    'Stage Type': 'Special' if stage in {5, 13, 14, 17, 18} else 'Regular'
                })
        
        # Add game dynamics data
        if 'points_history' in metrics:
            for i, points in enumerate(metrics['points_history']):
                report_data.append({
                    'Type': 'Game Dynamics',
                    'Simulation': i + 1,
                    'Total Points': points
                })
        
        report_df = pd.DataFrame(report_data)
        report_csv = report_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download TNO Game Analysis Report",
            data=report_csv,
            file_name=f"tno_game_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

else:
    st.info("Click 'Run TNO Game Analysis' to explore team-independent statistics and performance patterns.") 