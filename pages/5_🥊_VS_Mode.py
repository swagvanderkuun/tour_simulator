import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from riders import RiderDatabase
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
from tno_optimizer import TNOTeamOptimizer, TNOTeamOptimization
from tno_ergame_multi_simulator import TNOMultiSimulationAnalyzer

st.set_page_config(
    page_title="VS Mode - T(n)oer Game",
    page_icon="🥊",
    layout="wide"
)

st.title("🥊 VS Mode")
st.markdown("""
Test your manually selected team against optimal teams and see how you stack up!
Challenge yourself and improve your team selection skills.
""")

# Load rider database
rider_db = RiderDatabase()
all_riders = rider_db.get_all_riders()
rider_names = [r.name for r in all_riders]

# User team selection
st.header("1. Build Your Team")

col1, col2 = st.columns([2, 1])

with col1:
    user_riders = st.multiselect(
        "Choose your 20 riders",
        options=rider_names,
        default=rider_names[:20],
        max_selections=20,
        help="Select exactly 20 riders for your team"
    )

with col2:
    st.info(f"**Selected:** {len(user_riders)}/20 riders")
    if len(user_riders) == 20:
        st.success("✅ Team complete!")
    else:
        st.warning("⚠️ Please select exactly 20 riders")

# User team ordering
if len(user_riders) == 20:
    st.header("2. Set Your Rider Order")
    st.markdown("The order is crucial! First 5 get bonus points, first 15 are scoring riders.")
    
    # Create ordering interface
    user_ordered_riders = []
    used = set()
    
    cols = st.columns(4)
    for i in range(20):
        col_idx = i % 4
        
        with cols[col_idx]:
            options = [r for r in user_riders if r not in used]
            if options:
                rider = st.selectbox(
                    f"{i+1}. Rider", 
                    options, 
                    key=f"user_order_{i}",
                    help=f"Position {i+1}: {'BONUS' if i < 5 else 'SCORING' if i < 15 else 'RESERVE'}"
                )
                user_ordered_riders.append(rider)
                used.add(rider)
    
    # Display user team
    st.header("3. Your Team Summary")
    
    user_team_summary = []
    for i, rider in enumerate(user_ordered_riders):
        rider_obj = rider_db.get_rider(rider)
        user_team_summary.append({
            "Position": i + 1,
            "Rider": rider,
            "Team": rider_obj.team,
            "Price": rider_obj.price,
            "Role": "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE"
        })
    
    user_team_df = pd.DataFrame(user_team_summary)
    st.dataframe(user_team_df, hide_index=True)
    
    # VS Mode settings
    st.header("4. VS Mode Settings")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_simulations = st.number_input(
            "Number of Simulations",
            min_value=10,
            max_value=200,
            value=50,
            step=10,
            help="More simulations = more accurate comparison"
        )
    
    with col2:
        include_optimal = st.checkbox("Include Optimal Team", value=True)
    
    with col3:
        include_heuristic = st.checkbox("Include Heuristic Team", value=True)
    
    # Run VS Mode
    st.header("5. Run VS Mode")
    
    if st.button("🥊 Start VS Mode Battle", type="primary"):
        with st.spinner("Running VS Mode... This may take a few minutes."):
            try:
                # Create user team
                user_team_objs = [rider_db.get_rider(name) for name in user_ordered_riders]
                user_team = TNOTeamSelection(user_team_objs)
                
                # Run user team analysis
                st.info("Analyzing your team...")
                user_analyzer = TNOMultiSimulationAnalyzer(num_simulations)
                user_metrics = user_analyzer.run_simulations(user_team)
                
                vs_results = {
                    'user_team': {
                        'team': user_team,
                        'metrics': user_metrics,
                        'name': 'Your Team'
                    }
                }
                
                # Generate optimal team if requested
                if include_optimal:
                    st.info("Generating optimal team...")
                    optimizer = TNOTeamOptimizer(team_size=20)
                    rider_data = optimizer.run_simulation_for_riders(num_simulations=30)
                    optimal_optimization = optimizer.optimize_team_with_order(rider_data, num_simulations=30)
                    
                    optimal_team_objs = [rider_db.get_rider(name) for name in optimal_optimization.rider_order]
                    optimal_team = TNOTeamSelection(optimal_team_objs)
                    
                    optimal_analyzer = TNOMultiSimulationAnalyzer(num_simulations)
                    optimal_metrics = optimal_analyzer.run_simulations(optimal_team)
                    
                    vs_results['optimal_team'] = {
                        'team': optimal_team,
                        'metrics': optimal_metrics,
                        'optimization': optimal_optimization,
                        'name': 'Optimal Team'
                    }
                
                # Generate heuristic team if requested
                if include_heuristic:
                    st.info("Generating heuristic team...")
                    from tno_heuristic_optimizer import TNOHeuristicOptimizer
                    heuristic_optimizer = TNOHeuristicOptimizer()
                    heuristic_optimization = heuristic_optimizer.optimize_team(
                        num_simulations=30,
                        validation_simulations=30
                    )
                    
                    heuristic_team_objs = [rider_db.get_rider(name) for name in heuristic_optimization.rider_order]
                    heuristic_team = TNOTeamSelection(heuristic_team_objs)
                    
                    heuristic_analyzer = TNOMultiSimulationAnalyzer(num_simulations)
                    heuristic_metrics = heuristic_analyzer.run_simulations(heuristic_team)
                    
                    vs_results['heuristic_team'] = {
                        'team': heuristic_team,
                        'metrics': heuristic_metrics,
                        'optimization': heuristic_optimization,
                        'name': 'Heuristic Team'
                    }
                
                # Store results
                st.session_state.vs_results = vs_results
                
                st.success("✅ VS Mode completed successfully!")
                
            except Exception as e:
                st.error(f"❌ VS Mode failed: {str(e)}")
                st.exception(e)

# Display VS Mode results
if 'vs_results' in st.session_state:
    st.header("6. VS Mode Results")
    
    vs_results = st.session_state.vs_results
    
    # Performance comparison
    st.subheader("📊 Performance Comparison")
    
    performance_data = []
    for team_key, team_data in vs_results.items():
        metrics = team_data['metrics']
        avg_points = metrics['team_performance']['total_points']['mean']
        std_points = metrics['team_performance']['total_points']['std']
        
        performance_data.append({
            'Team': team_data['name'],
            'Avg Points': avg_points,
            'Std Points': std_points,
            'Min Points': metrics['team_performance']['total_points']['min'],
            'Max Points': metrics['team_performance']['total_points']['max'],
            'Avg Abandonments': metrics['team_performance']['abandonments']['mean']
        })
    
    perf_df = pd.DataFrame(performance_data)
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_team = perf_df.loc[perf_df['Avg Points'].idxmax()]
        st.metric("Best Team", best_team['Team'])
    
    with col2:
        best_points = best_team['Avg Points']
        st.metric("Best Avg Points", f"{best_points:.1f}")
    
    with col3:
        user_points = perf_df[perf_df['Team'] == 'Your Team']['Avg Points'].iloc[0]
        st.metric("Your Avg Points", f"{user_points:.1f}")
    
    # Performance chart
    fig = px.bar(
        perf_df,
        x='Team',
        y='Avg Points',
        error_y='Std Points',
        title="Average Points by Team",
        labels={'Avg Points': 'Average Points', 'Team': 'Team Name'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Points distribution comparison
    st.subheader("📈 Points Distribution Comparison")
    
    # Create violin plot if we have points history
    all_points_data = []
    for team_key, team_data in vs_results.items():
        if 'points_history' in team_data['metrics']:
            for points in team_data['metrics']['points_history']:
                all_points_data.append({
                    'Team': team_data['name'],
                    'Points': points
                })
    
    if all_points_data:
        points_df = pd.DataFrame(all_points_data)
        fig = px.violin(
            points_df,
            x='Team',
            y='Points',
            title="Points Distribution by Team",
            labels={'Points': 'Total Points', 'Team': 'Team Name'}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Team comparison table
    st.subheader("🏆 Team Comparison")
    
    # Create comparison table
    comparison_data = []
    max_riders = max(len(team_data['team'].riders) for team_data in vs_results.values())
    
    for i in range(max_riders):
        row = {'Position': i + 1}
        for team_key, team_data in vs_results.items():
            riders = [r.name for r in team_data['team'].riders]
            if i < len(riders):
                rider_name = riders[i]
                rider_obj = rider_db.get_rider(rider_name)
                row[f"{team_data['name']}"] = f"{rider_name} ({rider_obj.team})"
            else:
                row[f"{team_data['name']}"] = ""
        comparison_data.append(row)
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, hide_index=True)
    
    # Detailed team analysis
    st.subheader("📋 Detailed Team Analysis")
    
    for team_key, team_data in vs_results.items():
        with st.expander(f"📊 {team_data['name']} - Detailed Analysis"):
            metrics = team_data['metrics']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_points = metrics['team_performance']['total_points']['mean']
                std_points = metrics['team_performance']['total_points']['std']
                st.metric("Avg Points", f"{avg_points:.1f}", f"±{std_points:.1f}")
            
            with col2:
                avg_abandonments = metrics['team_performance']['abandonments']['mean']
                st.metric("Avg Abandonments", f"{avg_abandonments:.1f}")
            
            with col3:
                avg_remaining = metrics['team_performance']['riders_remaining']['mean']
                st.metric("Avg Riders Remaining", f"{avg_remaining:.1f}")
            
            with col4:
                team_cost = team_data['team'].total_cost
                st.metric("Team Cost", f"${team_cost:.2f}")
            
            # Top performers
            if 'tno_analysis' in metrics and 'top_scorers' in metrics['tno_analysis']:
                top_scorers = metrics['tno_analysis']['top_scorers']
                
                top_df = pd.DataFrame([
                    {
                        "Rider": rider,
                        "Avg Points": data['mean'],
                        "Std Points": data['std'],
                        "Min Points": data['min'],
                        "Max Points": data['max']
                    }
                    for rider, data in list(top_scorers.items())[:10]
                ])
                
                st.write("**Top 10 Performers:**")
                st.dataframe(top_df, hide_index=True)
    
    # Performance insights
    st.subheader("💡 Performance Insights")
    
    user_perf = perf_df[perf_df['Team'] == 'Your Team'].iloc[0]
    best_perf = perf_df.loc[perf_df['Avg Points'].idxmax()]
    
    if user_perf['Team'] == best_perf['Team']:
        st.success("🎉 Congratulations! Your team is the best performer!")
    else:
        points_diff = best_perf['Avg Points'] - user_perf['Avg Points']
        st.info(f"📊 Your team is {points_diff:.1f} points behind the best team ({best_perf['Team']})")
        
        # Provide suggestions
        st.write("**💡 Suggestions for improvement:**")
        
        # Compare team compositions
        user_riders_set = set(user_ordered_riders)
        for team_key, team_data in vs_results.items():
            if team_data['name'] != 'Your Team':
                other_riders_set = set([r.name for r in team_data['team'].riders])
                missing_riders = other_riders_set - user_riders_set
                extra_riders = user_riders_set - other_riders_set
                
                if missing_riders:
                    st.write(f"**Consider adding:** {', '.join(list(missing_riders)[:5])}")
                if extra_riders:
                    st.write(f"**Consider replacing:** {', '.join(list(extra_riders)[:5])}")
    
    # Download VS Mode results
    st.subheader("💾 Download VS Mode Results")
    
    if st.button("Generate VS Mode Report"):
        # Create comprehensive VS Mode report
        report_data = []
        
        # Add performance data
        for _, row in perf_df.iterrows():
            report_data.append({
                'Type': 'Performance',
                'Team': row['Team'],
                'Avg Points': row['Avg Points'],
                'Std Points': row['Std Points'],
                'Min Points': row['Min Points'],
                'Max Points': row['Max Points'],
                'Avg Abandonments': row['Avg Abandonments']
            })
        
        # Add team comparison data
        for _, row in comparison_df.iterrows():
            for team_key, team_data in vs_results.items():
                report_data.append({
                    'Type': 'Team Selection',
                    'Position': row['Position'],
                    'Team': team_data['name'],
                    'Rider': row.get(team_data['name'], '')
                })
        
        report_df = pd.DataFrame(report_data)
        report_csv = report_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download VS Mode Report",
            data=report_csv,
            file_name=f"tnoer_game_vs_mode_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

else:
    st.info("Please complete your team selection and run VS Mode to see results.") 