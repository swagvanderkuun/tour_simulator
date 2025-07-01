import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from riders import RiderDatabase
from tno_optimizer import TNOTeamOptimizer, TNOTeamOptimization
from tno_heuristic_optimizer import TNOHeuristicOptimizer, TNOHeuristicOptimization

st.set_page_config(
    page_title="Compare Strategies - T(n)oer Game",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Compare Optimization Strategies")
st.markdown("""
Compare different optimization strategies and see how they perform against each other.
Analyze the strengths and weaknesses of each approach.
""")

# Strategy selection
st.header("1. Select Strategies to Compare")

strategies = {
    "Original Optimizer": {
        "description": "Advanced mathematical optimization using Integer Linear Programming",
        "icon": "🧮"
    },
    "Heuristic Optimizer": {
        "description": "Rule-based approach using simulation results and expected values",
        "icon": "📊"
    }
}

selected_strategies = st.multiselect(
    "Choose strategies to compare",
    options=list(strategies.keys()),
    default=list(strategies.keys()),
    help="Select at least two strategies for comparison"
)

# Display strategy descriptions
if selected_strategies:
    st.subheader("Selected Strategies")
    
    for strategy in selected_strategies:
        info = strategies[strategy]
        st.markdown(f"""
        **{info['icon']} {strategy}**
        {info['description']}
        """)

# Comparison settings
st.header("2. Comparison Settings")

col1, col2, col3 = st.columns(3)

with col1:
    team_size = st.number_input(
        "Team Size",
        min_value=15,
        max_value=25,
        value=20,
        help="Number of riders to select"
    )

with col2:
    rider_simulations = st.number_input(
        "Rider Analysis Simulations",
        min_value=10,
        max_value=100,
        value=30,
        help="Number of simulations for rider analysis"
    )

with col3:
    validation_simulations = st.number_input(
        "Validation Simulations",
        min_value=10,
        max_value=200,
        value=50,
        help="Number of simulations to validate each strategy"
    )

# Run comparison
st.header("3. Run Comparison")

if len(selected_strategies) >= 2:
    if st.button("🚀 Start Comparison", type="primary"):
        with st.spinner("Running comparison... This may take several minutes."):
            try:
                comparison_results = {}
                
                # Run each selected strategy
                for strategy in selected_strategies:
                    st.info(f"Running {strategy}...")
                    
                    if strategy == "Original Optimizer":
                        optimizer = TNOTeamOptimizer(team_size=team_size)
                        rider_data = optimizer.run_simulation_for_riders(num_simulations=rider_simulations)
                        optimization = optimizer.optimize_team_with_order(rider_data, num_simulations=validation_simulations)
                        
                        comparison_results[strategy] = {
                            'optimization': optimization,
                            'rider_data': rider_data,
                            'type': 'original'
                        }
                    
                    elif strategy == "Heuristic Optimizer":
                        heuristic_optimizer = TNOHeuristicOptimizer()
                        optimization = heuristic_optimizer.optimize_team(
                            num_simulations=rider_simulations,
                            validation_simulations=validation_simulations
                        )
                        
                        comparison_results[strategy] = {
                            'optimization': optimization,
                            'type': 'heuristic'
                        }
                
                # Store results
                st.session_state.comparison_results = {
                    'results': comparison_results,
                    'settings': {
                        'team_size': team_size,
                        'rider_sims': rider_simulations,
                        'validation_sims': validation_simulations
                    }
                }
                
                st.success("✅ Comparison completed successfully!")
                
            except Exception as e:
                st.error(f"❌ Comparison failed: {str(e)}")
                st.exception(e)
else:
    st.warning("Please select at least 2 strategies to compare.")

# Display comparison results
if 'comparison_results' in st.session_state:
    st.header("4. Comparison Results")
    
    results = st.session_state.comparison_results
    comparison_results = results['results']
    settings = results['settings']
    
    # Performance comparison
    st.subheader("📊 Performance Comparison")
    
    performance_data = []
    for strategy, data in comparison_results.items():
        optimization = data['optimization']
        performance_data.append({
            'Strategy': strategy,
            'Expected Points': optimization.expected_points,
            'Team Size': optimization.team_size,
            'Team Cost': sum(rider_db.get_rider(name).price for name in optimization.rider_order)
        })
    
    perf_df = pd.DataFrame(performance_data)
    
    # Performance metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        best_strategy = perf_df.loc[perf_df['Expected Points'].idxmax()]
        st.metric("Best Strategy", best_strategy['Strategy'])
    
    with col2:
        best_points = best_strategy['Expected Points']
        st.metric("Best Expected Points", f"{best_points:.1f}")
    
    with col3:
        points_range = perf_df['Expected Points'].max() - perf_df['Expected Points'].min()
        st.metric("Performance Range", f"{points_range:.1f} points")
    
    # Performance chart
    fig = px.bar(
        perf_df,
        x='Strategy',
        y='Expected Points',
        title="Expected Points by Strategy",
        labels={'Expected Points': 'Expected Points', 'Strategy': 'Optimization Strategy'}
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Team comparison
    st.subheader("🏆 Team Comparison")
    
    # Create comparison table
    comparison_data = []
    max_riders = max(len(data['optimization'].rider_order) for data in comparison_results.values())
    
    for i in range(max_riders):
        row = {'Position': i + 1}
        for strategy, data in comparison_results.items():
            riders = data['optimization'].rider_order
            if i < len(riders):
                rider_name = riders[i]
                rider_obj = rider_db.get_rider(rider_name)
                row[f"{strategy}"] = f"{rider_name} ({rider_obj.team})"
            else:
                row[f"{strategy}"] = ""
        comparison_data.append(row)
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, hide_index=True)
    
    # Rider overlap analysis
    st.subheader("🔄 Rider Overlap Analysis")
    
    # Calculate overlaps
    overlap_data = []
    strategies_list = list(comparison_results.keys())
    
    for i, strategy1 in enumerate(strategies_list):
        for j, strategy2 in enumerate(strategies_list[i+1:], i+1):
            riders1 = set(comparison_results[strategy1]['optimization'].rider_order)
            riders2 = set(comparison_results[strategy2]['optimization'].rider_order)
            
            overlap = len(riders1.intersection(riders2))
            overlap_pct = (overlap / len(riders1)) * 100
            
            overlap_data.append({
                'Strategy 1': strategy1,
                'Strategy 2': strategy2,
                'Overlap Count': overlap,
                'Overlap %': overlap_pct
            })
    
    if overlap_data:
        overlap_df = pd.DataFrame(overlap_data)
        st.dataframe(overlap_df, hide_index=True)
        
        # Overlap heatmap
        pivot_df = overlap_df.pivot(index='Strategy 1', columns='Strategy 2', values='Overlap %')
        fig = px.imshow(
            pivot_df,
            title="Rider Selection Overlap (%)",
            labels=dict(x="Strategy 2", y="Strategy 1", color="Overlap %")
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Detailed strategy analysis
    st.subheader("📈 Detailed Strategy Analysis")
    
    for strategy, data in comparison_results.items():
        with st.expander(f"{strategies[strategy]['icon']} {strategy} - Detailed Analysis"):
            optimization = data['optimization']
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Expected Points", f"{optimization.expected_points:.1f}")
                st.metric("Team Size", optimization.team_size)
                
                team_cost = sum(rider_db.get_rider(name).price for name in optimization.rider_order)
                st.metric("Team Cost", f"${team_cost:.2f}")
            
            with col2:
                # Team composition
                team_counts = {}
                for rider_name in optimization.rider_order:
                    team = rider_db.get_rider(rider_name).team
                    team_counts[team] = team_counts.get(team, 0) + 1
                
                top_teams = sorted(team_counts.items(), key=lambda x: x[1], reverse=True)[:5]
                st.write("**Top Teams:**")
                for team, count in top_teams:
                    st.write(f"- {team}: {count} riders")
            
            # Rider list
            st.write("**Selected Riders:**")
            rider_list = []
            for i, rider_name in enumerate(optimization.rider_order):
                rider_obj = rider_db.get_rider(rider_name)
                role = "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE"
                rider_list.append({
                    "Position": i + 1,
                    "Rider": rider_name,
                    "Team": rider_obj.team,
                    "Price": rider_obj.price,
                    "Role": role
                })
            
            rider_df = pd.DataFrame(rider_list)
            st.dataframe(rider_df, hide_index=True)
    
    # Download comparison results
    st.subheader("💾 Download Comparison Results")
    
    if st.button("Generate Comparison Report"):
        # Create comprehensive comparison report
        report_data = []
        
        # Add performance data
        for _, row in perf_df.iterrows():
            report_data.append({
                'Type': 'Performance',
                'Strategy': row['Strategy'],
                'Expected Points': row['Expected Points'],
                'Team Size': row['Team Size'],
                'Team Cost': row['Team Cost']
            })
        
        # Add team comparison data
        for _, row in comparison_df.iterrows():
            for strategy in comparison_results.keys():
                report_data.append({
                    'Type': 'Team Selection',
                    'Position': row['Position'],
                    'Strategy': strategy,
                    'Rider': row.get(strategy, '')
                })
        
        # Add overlap data
        for _, row in overlap_df.iterrows():
            report_data.append({
                'Type': 'Overlap Analysis',
                'Strategy 1': row['Strategy 1'],
                'Strategy 2': row['Strategy 2'],
                'Overlap Count': row['Overlap Count'],
                'Overlap %': row['Overlap %']
            })
        
        report_df = pd.DataFrame(report_data)
        report_csv = report_df.to_csv(index=False)
        
        st.download_button(
            label="📥 Download Comparison Report",
            data=report_csv,
            file_name=f"tnoer_game_comparison_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Load rider database for reference
rider_db = RiderDatabase() 