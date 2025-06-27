import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
from datetime import datetime
import io
import base64
import matplotlib.pyplot as plt

# Import our custom modules
from simulator import TourSimulator
from team_optimization import TeamOptimizer
from riders import RiderDatabase, Rider
from rider_parameters import RiderParameters, get_tier_parameters, update_tier_parameters
from multi_simulator import MultiSimulationAnalyzer
from versus_mode import VersusMode

# Page configuration
st.set_page_config(
    page_title="Tour de France Simulator Dashboard",
    page_icon="🚴‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .metric-card h3 {
        color: white;
        margin-bottom: 0.5rem;
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-card p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0;
        line-height: 1.4;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.3s ease;
    }
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        font-weight: bold;
    }
    .stButton > button:hover {
        background-color: #0d5aa7;
    }
    .stMetric {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 1rem;
        border-radius: 8px;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .stMetric > div {
        color: white !important;
    }
    .stMetric label {
        color: rgba(255, 255, 255, 0.9) !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'simulation_results' not in st.session_state:
    st.session_state.simulation_results = None
if 'multi_simulation_results' not in st.session_state:
    st.session_state.multi_simulation_results = None
if 'optimization_results' not in st.session_state:
    st.session_state.optimization_results = None
if 'rider_db' not in st.session_state:
    st.session_state.rider_db = RiderDatabase()

def inject_rider_database(simulator, rider_db):
    """Helper function to inject a modified rider database into a simulator"""
    simulator.rider_db = rider_db
    # Recalculate youth riders and other dependent data
    simulator.youth_rider_names = set(r.name for r in simulator.rider_db.get_all_riders() if r.age < 25)
    simulator.rider_db_records = []
    for rider in simulator.rider_db.get_all_riders():
        simulator.rider_db_records.append({
            "name": rider.name,
            "team": rider.team,
            "age": rider.age,
            "sprint_ability": rider.parameters.sprint_ability,
            "punch_ability": rider.parameters.punch_ability,
            "itt_ability": rider.parameters.itt_ability,
            "mountain_ability": rider.parameters.mountain_ability,
            "hills_ability": rider.parameters.hills_ability,
            "is_youth": rider.name in simulator.youth_rider_names,
            "price": rider.price,
            "chance_of_abandon": rider.chance_of_abandon
        })

def main():
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .metric-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card h3 {
        margin: 0 0 10px 0;
        font-size: 18px;
    }
    .metric-card p {
        margin: 0;
        font-size: 14px;
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'rider_db' not in st.session_state:
        st.session_state.rider_db = rider_db
    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = None
    if 'multi_simulation_results' not in st.session_state:
        st.session_state.multi_simulation_results = None
    if 'optimization_results' not in st.session_state:
        st.session_state.optimization_results = None
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["📊 Overview", "🎯 Single Simulation", "📈 Multi Simulation", "⚡ Team Optimization", "🆚 Versus Mode", "👥 Rider Management", "🏁 Stage Types"]
    )
    
    if page == "📊 Overview":
        show_overview()
    elif page == "🎯 Single Simulation":
        show_single_simulation()
    elif page == "📈 Multi Simulation":
        show_multi_simulation()
    elif page == "⚡ Team Optimization":
        show_team_optimization()
    elif page == "🆚 Versus Mode":
        show_versus_mode()
    elif page == "👥 Rider Management":
        show_rider_management()
    elif page == "🏁 Stage Types":
        show_stage_types_management()

def show_overview():
    st.header("🏆 Tour de France Scorito Team Optimizer")
    st.markdown("""
    **🎯 Your Mission**: Build the ultimate Scorito team to dominate the Tour de France! 
    
    This dashboard is your secret weapon for creating the perfect fantasy cycling team using advanced simulation and optimization algorithms.
    """)
    
    # Main Goal & Getting Started
    st.markdown("---")
    st.subheader("🎯 Your Goal: Optimize Your Scorito Team")
    
    st.markdown("""
    **🏁 The Challenge**: Select 20 riders within a €48 budget to maximize your Scorito points across the entire Tour de France.
    
    **⚡ Our Solution**: Advanced simulation technology that runs hundreds of Tour de France scenarios to predict rider performance and find your optimal team.
    """)
    
    # Quick Start Guide
    st.markdown("---")
    st.subheader("🚀 Quick Start Guide")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📋 5-Step Process:**
        
        1. **👥 Rider Management** - Adjust rider abilities based on recent form
        2. **🎯 Single Simulation** - Test your settings with one quick simulation  
        3. **📈 Multi Simulation** - Run 100+ simulations for reliable predictions
        4. **⚡ Team Optimization** - Let AI find your perfect team
        5. **🏁 Stage Types** - Fine-tune stage configurations (optional)
        """)
    
    with col2:
        st.markdown("""
        **💡 Pro Tips:**
        
        • **Tier Maker Magic**: Use the visual tier system to adjust rider abilities
        • **Export Everything**: Download results for external analysis
        • **Test Scenarios**: Run different rider configurations to find hidden gems
        """)
    
    # System Capabilities Summary
    st.markdown("---")
    st.subheader("🎯 What This System Can Do")
    
    capabilities = [
        "🏁 **Complete Tour Simulation**: 21 stages with realistic time gaps and point distributions",
        "👥 **200+ Rider Database**: Real riders with tier-based abilities (S/A/B/C/D/E)",
        "⚡ **AI Team Optimization**: Integer Linear Programming finds your optimal €48 team",
        "📊 **Statistical Predictions**: Monte Carlo simulation with confidence intervals",
        "💥 **Realistic Racing**: Crash/abandonment system based on rider risk profiles",
        "📈 **Multiple Classifications**: GC, Sprint, Mountain, and Youth point tracking",
        "🎮 **Interactive Tier Maker**: Drag-and-drop rider ability adjustments",
        "📊 **Data Export**: Excel files with detailed stage-by-stage analysis"
    ]
    
    for capability in capabilities:
        st.markdown(f"• {capability}")
    
    # Dashboard Pages Overview
    st.markdown("---")
    st.subheader("📋 Dashboard Pages")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **🎯 Single Simulation**
        
        Run one complete Tour de France simulation to see how your current settings perform.
        
        **Key Features:**
        • Stage-by-stage results
        • Classification standings
        • Visual performance charts
        • Export to Excel
        """)
    
    with col2:
        st.markdown("""
        **📈 Multi Simulation**
        
        Run hundreds of simulations to get reliable performance predictions for optimization.
        
        **Key Features:**
        • 10-500 simulation runs
        • Expected points calculation
        • Performance variance analysis
        • Statistical confidence intervals
        """)
    
    with col3:
        st.markdown("""
        **⚡ Team Optimization**
        
        AI-powered team selection using advanced optimization algorithms.
        
        **Key Features:**
        • Integer Linear Programming solver
        • Budget and constraint management
        • Abandonment risk management
        • Alternative team suggestions
        """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        **👥 Rider Management**
        
        Comprehensive rider data management with interactive tier system.
        
        **Key Features:**
        • Visual Tier Maker (drag & drop)
        • Real-time ability adjustments
        • Rider database viewer
        • Add/edit individual riders
        """)
    
    with col2:
        st.markdown("""
        **🏁 Stage Types**
        
        Configure the 21 Tour de France stages (Sprint, ITT, Mountain, Hills, Punch).
        
        **Key Features:**
        • Visual stage type grid
        • Performance impact analysis
        • Export configurations
        • Reset to defaults
        """)
    
    with col3:
        st.markdown("""
        **📊 Results Analysis**
        
        Deep dive into simulation results and optimization outcomes.
        
        **Key Features:**
        • Performance visualizations
        • Team composition analysis
        • Statistical breakdowns
        • Comparative analysis
        """)
    
    # System Statistics
    st.markdown("---")
    st.subheader("📊 System Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_riders = len(st.session_state.rider_db.get_all_riders())
        st.metric("Total Riders", total_riders)
        st.caption("Available for selection")
    
    with col2:
        teams = len(set(rider.team for rider in st.session_state.rider_db.get_all_riders()))
        st.metric("Teams", teams)
        st.caption("Professional teams")
    
    with col3:
        youth_riders = len([r for r in st.session_state.rider_db.get_all_riders() if r.age < 25])
        st.metric("Youth Riders", youth_riders)
        st.caption("Youth classification eligible")
    
    with col4:
        avg_price = np.mean([rider.price for rider in st.session_state.rider_db.get_all_riders()])
        st.metric("Average Price", f"€{avg_price:.2f}")
        st.caption("Mean rider cost")
    
    # Advanced Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Calculate tier distribution
        tier_counts = {"S": 0, "A": 0, "B": 0, "C": 0, "D": 0, "E": 0}
        for rider in st.session_state.rider_db.get_all_riders():
            abilities = [
                rider.parameters.sprint_ability,
                rider.parameters.itt_ability,
                rider.parameters.mountain_ability,
                rider.parameters.hills_ability,
                rider.parameters.punch_ability
            ]
            max_ability = max(abilities)
            if max_ability >= 98:
                tier_counts["S"] += 1
            elif max_ability >= 95:
                tier_counts["A"] += 1
            elif max_ability >= 90:
                tier_counts["B"] += 1
            elif max_ability >= 80:
                tier_counts["C"] += 1
            elif max_ability >= 70:
                tier_counts["D"] += 1
            else:
                tier_counts["E"] += 1
        
        top_tier_riders = tier_counts["S"] + tier_counts["A"]
        st.metric("Top Tier Riders", top_tier_riders)
        st.caption("S & A tier performers")
    
    with col2:
        total_abandon_risk = sum(rider.chance_of_abandon for rider in st.session_state.rider_db.get_all_riders())
        st.metric("Total Abandon Risk", f"{total_abandon_risk:.1f}")
        st.caption("Combined crash probability")
    
    with col3:
        if st.session_state.multi_simulation_results is not None:
            st.metric("Optimization Ready", "✅")
            st.caption("Multi-sim data available")
        else:
            st.metric("Optimization Ready", "⏳")
            st.caption("Run multi-simulation first")
    
    with col4:
        if st.session_state.optimization_results is not None:
            st.metric("Team Selected", "✅")
            st.caption("Optimal team ready")
        else:
            st.metric("Team Selected", "⏳")
            st.caption("Run optimization")
    
    # System Status
    st.markdown("---")
    st.subheader("🕒 System Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.session_state.simulation_results is not None:
            st.success("✅ Single Simulation Complete")
            st.caption("Test run successful")
        else:
            st.info("⏳ No Test Simulation")
            st.caption("Run a quick test first")
    
    with col2:
        if st.session_state.multi_simulation_results is not None:
            st.success("✅ Multi-Simulation Complete")
            st.caption("Ready for optimization")
        else:
            st.info("⏳ No Multi-Simulation")
            st.caption("Generate predictions")
    
    with col3:
        if st.session_state.optimization_results is not None:
            st.success("✅ Team Optimization Complete")
            st.caption("Optimal team found!")
        else:
            st.info("⏳ No Optimization")
            st.caption("Find your perfect team")
    
    # Technical Deep Dive (Condensed)
    st.markdown("---")
    st.subheader("🔬 How It Works (Technical)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🎯 Core Technology:**
        
        **Simulation Engine**: 21-stage Tour simulation with realistic time gaps and point distributions
        
        **Optimization Algorithm**: Integer Linear Programming (ILP) with budget constraints
        
        **Probability Models**: Tier-based triangular distributions for position predictions
        
        **Abandonment Management**: Crash probability adjustment
        """)
    
    with col2:
        st.markdown("""
        **📊 Data Flow:**
        
        1. **Rider Database** → **Stage Simulation** → **Results**
        2. **Multiple Simulations** → **Expected Points** → **Optimization**
        3. **Constraints Applied** → **Optimal Team** → **Export**
        
        **🎮 Interactive Features:**
        • Real-time tier adjustments
        • Visual stage type management
        • Export capabilities
        • Statistical analysis
        """)
    
    # Call to Action
    st.markdown("---")
    st.markdown("""
    ### 🚀 Ready to Build Your Champion Team?
    
    **Start here**: Use the sidebar navigation to go to **Rider Management** to adjust rider abilities, then run a **Single Simulation** to test your settings!
    
    **💪 Your Scorito domination starts now!**
    """)

def show_single_simulation():
    st.header("🎯 Single Tour Simulation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Simulation Settings")
        
        # Simulation options
        show_progress = st.checkbox("Show simulation progress", value=True, key="single_sim_progress")
        export_results = st.checkbox("Export results to Excel", value=True, key="single_sim_export")
        
        if st.button("🚀 Run Single Simulation", type="primary", key="run_single_sim"):
            with st.spinner("Running simulation..."):
                # Create progress bar
                if show_progress:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                # Run simulation using the session state rider database
                simulator = TourSimulator()
                inject_rider_database(simulator, st.session_state.rider_db)
                
                # Complete simulation
                simulator.simulate_tour()
                
                if show_progress:
                    progress_bar.progress(1.0)
                    status_text.text("Simulation completed!")
                
                # Store results
                st.session_state.simulation_results = simulator
                
                # Export if requested
                if export_results:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"tour_simulation_results_{timestamp}.xlsx"
                    simulator.write_results_to_excel(filename)
                    st.success(f"Results exported to {filename}")
                
                st.success("✅ Simulation completed successfully!")
    
    with col2:
        st.subheader("Quick Actions")
        
        if st.button("📊 View Results", key="view_single_results"):
            if st.session_state.simulation_results is not None:
                show_simulation_results(st.session_state.simulation_results)
            else:
                st.warning("No simulation results available. Run a simulation first.")
        
        if st.button("📥 Export Results", key="export_single_results"):
            if st.session_state.simulation_results is not None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"tour_simulation_results_{timestamp}.xlsx"
                st.session_state.simulation_results.write_results_to_excel(filename)
                st.success(f"Results exported to {filename}")
            else:
                st.warning("No simulation results available.")

def show_multi_simulation():
    st.header("📊 Multi-Simulation Analysis")
    
    st.subheader("Simulation Parameters")
    
    num_simulations = st.slider("Number of simulations", 10, 500, 100, 10, key="multi_sim_count")
    show_progress = st.checkbox("Show progress", value=True, key="multi_sim_progress")
    
    if st.button("🔄 Run Multi-Simulation", type="primary", key="run_multi_sim"):
        with st.spinner(f"Running {num_simulations} simulations..."):
            if show_progress:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            # Run multi-simulation using the new analyzer
            analyzer = MultiSimulationAnalyzer(num_simulations)
            
            def progress_callback(current, total):
                if show_progress:
                    progress = current / total
                    progress_bar.progress(progress)
                    status_text.text(f"Simulation {current}/{total}")
            
            metrics = analyzer.run_simulations(st.session_state.rider_db, progress_callback)
            
            if show_progress:
                progress_bar.empty()
                status_text.empty()
            
            st.success(f"✅ Completed {num_simulations} simulations!")
            
            # Store results in session state
            st.session_state.multi_sim_results = metrics
            
            # Display the analysis
            show_scorito_analysis_dashboard(metrics)
    
    # Show results if available
    if 'multi_sim_results' in st.session_state:
        show_scorito_analysis_dashboard(st.session_state.multi_sim_results)

def show_team_optimization():
    st.header("⚡ Team Optimization")
    
    st.subheader("Optimization Parameters")
    
    budget = st.slider("Budget", 30.0, 60.0, 48.0, 0.5, key="opt_budget")
    team_size = st.slider("Team size", 15, 25, 20, 1, key="opt_team_size")
    num_simulations = st.slider("Simulations for expected points", 50, 200, 100, 10, key="opt_sim_count")
    abandon_penalty = st.slider("Abandon penalty", 0.0, 1.0, 1.0, 0.1, key="opt_abandon_penalty")
    
    if st.button("🎯 Optimize Team", type="primary", key="run_optimization"):
        with st.spinner("Running optimization..."):
            optimizer = TeamOptimizer(budget=budget, team_size=team_size)
            # Replace the optimizer's rider database with our modified one
            optimizer.rider_db = st.session_state.rider_db
            inject_rider_database(optimizer.simulator, st.session_state.rider_db)
            
            # Get expected points using our custom method
            rider_data = run_optimizer_simulation(optimizer, num_simulations, st.session_state.rider_db)
            
            # Optimize team (with stage-by-stage selection)
            team_selection = optimizer.optimize_with_stage_selection(
                rider_data,
                num_simulations=num_simulations,
                risk_aversion=0.0,  # You can expose this as a parameter if desired
                abandon_penalty=abandon_penalty
            )
            
            st.session_state.optimization_results = {
                'team_selection': team_selection,
                'rider_data': rider_data,
                'optimizer': optimizer
            }
            
            st.success("✅ Team optimization completed!")
    
    # Display results below the button
    if hasattr(st.session_state, 'optimization_results') and st.session_state.optimization_results is not None:
        st.subheader("📊 Optimization Results")
        
        team_selection = st.session_state.optimization_results['team_selection']
        rider_data = st.session_state.optimization_results['rider_data']
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cost", f"{team_selection.total_cost:.2f}")
        
        with col2:
            st.metric("Expected Points", f"{team_selection.expected_points:.1f}")
        
        with col3:
            st.metric("Team Size", len(team_selection.riders))
        
        with col4:
            efficiency = team_selection.expected_points / team_selection.total_cost if team_selection.total_cost > 0 else 0
            st.metric("Points per Euro", f"{efficiency:.2f}")
        
        # Team composition chart
        st.subheader("🏢 Team Composition")
        team_counts = {}
        for rider in team_selection.riders:
            team_counts[rider.team] = team_counts.get(rider.team, 0) + 1
        
        fig = px.pie(
            values=list(team_counts.values()),
            names=list(team_counts.keys()),
            title="Riders per Team"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Points scored per rider
        st.subheader("📊 Points Scored per Rider")
        
        # Calculate points per rider from rider_data
        rider_points = []
        for rider in team_selection.riders:
            rider_row = rider_data[rider_data['rider_name'] == rider.name]
            if not rider_row.empty:
                expected_points = rider_row.iloc[0]['expected_points']
                rider_points.append({
                    'Rider': rider.name,
                    'Team': rider.team,
                    'Price': rider.price,
                    'Expected Points': expected_points,
                    'Points per Euro': expected_points / rider.price if rider.price > 0 else 0
                })
        
        # Sort by expected points
        rider_points.sort(key=lambda x: x['Expected Points'], reverse=True)
        
        # Display as a table
        points_df = pd.DataFrame(rider_points)
        st.dataframe(points_df, use_container_width=True)
        
        # Bar chart of points per rider
        fig = px.bar(
            points_df,
            x='Rider',
            y='Expected Points',
            color='Team',
            title="Expected Points per Rider",
            text='Expected Points'
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Stage selections
        if hasattr(team_selection, 'stage_selections') and team_selection.stage_selections:
            st.subheader("🏁 Stage-by-Stage Rider Selections")
            
            # Create stage selection summary
            stage_summary = []
            for stage in sorted(team_selection.stage_selections.keys()):
                selected_riders = team_selection.stage_selections[stage]
                stage_points = team_selection.stage_points.get(stage, {})
                total_stage_points = sum(stage_points.values())
                
                stage_summary.append({
                    'Stage': stage,
                    'Riders Selected': len(selected_riders),
                    'Total Points': total_stage_points,
                    'Selected Riders': ', '.join(selected_riders)
                })
            
            # Display stage summary
            stage_df = pd.DataFrame(stage_summary)
            st.dataframe(stage_df, use_container_width=True)
            
            # Detailed stage-by-stage breakdown
            st.subheader("📋 Detailed Stage Breakdown")
            
            # Create tabs for each stage
            stage_tabs = st.tabs([f"Stage {stage}" for stage in sorted(team_selection.stage_selections.keys())])
            
            for i, stage in enumerate(sorted(team_selection.stage_selections.keys())):
                with stage_tabs[i]:
                    selected_riders = team_selection.stage_selections[stage]
                    stage_points = team_selection.stage_points.get(stage, {})
                    
                    # Get all riders and their points for this stage
                    stage_rider_data = []
                    for _, rider_row in rider_data.iterrows():
                        rider_name = rider_row['rider_name']
                        points = stage_points.get(rider_name, 0)
                        is_selected = rider_name in selected_riders
                        
                        stage_rider_data.append({
                            'Rider': rider_name,
                            'Team': rider_row['team'],
                            'Price': rider_row['price'],
                            'Points': points,
                            'Selected': '✓' if is_selected else '✗'
                        })
                    
                    # Sort by points (descending)
                    stage_rider_data.sort(key=lambda x: x['Points'], reverse=True)
                    stage_rider_df = pd.DataFrame(stage_rider_data)
                    
                    # Show selected riders first
                    selected_df = stage_rider_df[stage_rider_df['Selected'] == '✓']
                    unselected_df = stage_rider_df[stage_rider_df['Selected'] == '✗']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Selected Riders:**")
                        st.dataframe(selected_df, use_container_width=True)
                    
                    with col2:
                        st.write("**Top Unselected Riders:**")
                        st.dataframe(unselected_df.head(10), use_container_width=True)
                    
                    # Stage points chart
                    fig = px.bar(
                        stage_rider_df.head(20),  # Top 20 riders
                        x='Rider',
                        y='Points',
                        color='Selected',
                        title=f"Stage {stage} - Points per Rider (Top 20)",
                        color_discrete_map={'✓': 'green', '✗': 'red'}
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("⚠️ Stage-by-stage selection data not available. This may be from a basic optimization run.")
            
            # Fallback: show basic team information
            st.subheader("👥 Selected Team")
            team_info = []
            for i, rider in enumerate(team_selection.riders, 1):
                rider_row = rider_data[rider_data['rider_name'] == rider.name]
                expected_points = rider_row.iloc[0]['expected_points'] if not rider_row.empty else 0
                team_info.append({
                    'Position': i,
                    'Rider': rider.name,
                    'Team': rider.team,
                    'Price': rider.price,
                    'Expected Points': expected_points
                })
            
            team_df = pd.DataFrame(team_info)
            st.dataframe(team_df, use_container_width=True)
    
    # Show detailed results if available
    if hasattr(st.session_state, 'optimization_results') and st.session_state.optimization_results is not None:
        show_optimization_results(st.session_state.optimization_results)

def show_rider_management():
    st.header("👥 Rider Management")
    
    # Add custom CSS for better styling
    st.markdown("""
    <style>
    .rider-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #4CAF50;
    }
    .rider-card h4 {
        color: white;
        margin: 0 0 5px 0;
        font-size: 16px;
        font-weight: bold;
    }
    .rider-card p {
        color: #f0f0f0;
        margin: 2px 0;
        font-size: 12px;
    }
    .tier-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .tier-s {
        border-left-color: #FFD700 !important;
    }
    .tier-a {
        border-left-color: #C0C0C0 !important;
    }
    .tier-b {
        border-left-color: #CD7F32 !important;
    }
    .tier-c {
        border-left-color: #8B4513 !important;
    }
    .tier-d {
        border-left-color: #654321 !important;
    }
    .tier-e {
        border-left-color: #2F2F2F !important;
    }
    .price-badge {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        display: inline-block;
        margin: 2px 0;
    }
    .team-badge {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 3px 6px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
        display: inline-block;
        margin: 2px 0;
    }
    .move-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 5px 10px;
        font-size: 12px;
        cursor: pointer;
        margin: 2px;
        transition: all 0.3s ease;
    }
    .move-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    .move-btn:disabled {
        background: #ccc;
        cursor: not-allowed;
        transform: none;
    }
    .tier-stats-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .tier-controls {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .skill-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 Tier Maker", "🎯 Winning Probabilities", "📋 View Riders", "✏️ Edit Rider", "➕ Add Rider"])
    
    with tab1:
        show_tier_maker()
    
    with tab2:
        show_tier_parameters_management()
    
    with tab3:
        st.subheader("📋 Current Riders")
        
        # Get all riders
        riders = st.session_state.rider_db.get_all_riders()
        
        # Define tier scores for conversion
        tier_scores = {
            "S": 98,
            "A": 95, 
            "B": 90,
            "C": 80,
            "D": 70,
            "E": 40
        }
        
        # Function to convert ability to tier
        def ability_to_tier(ability: int) -> str:
            for tier, score in tier_scores.items():
                if ability >= score:
                    return tier
            return "E"
        
        # Create DataFrame with tiers instead of numerical values
        rider_data = []
        for rider in riders:
            rider_data.append({
                'Name': rider.name,
                'Team': rider.team,
                'Price': rider.price,
                'Sprint': ability_to_tier(rider.parameters.sprint_ability),
                'ITT': ability_to_tier(rider.parameters.itt_ability),
                'Mountain': ability_to_tier(rider.parameters.mountain_ability),
                'Hills': ability_to_tier(rider.parameters.hills_ability),
                'Punch': ability_to_tier(rider.parameters.punch_ability),
                'Abandon Chance': f"{rider.chance_of_abandon:.2%}"
            })
        
        df = pd.DataFrame(rider_data)
        
        # Fancy filters section
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.write("**🔍 Filter Options**")
        col1, col2, col3 = st.columns(3)
        with col1:
            team_filter = st.selectbox("🏢 Filter by team", ["All"] + sorted(df['Team'].unique()), key="view_team_filter")
        with col2:
            price_filter = st.slider("💰 Price range", float(df['Price'].min()), float(df['Price'].max()), (0.0, 10.0), key="view_price_filter")
        with col3:
            ability_filter = st.selectbox("⚡ Filter by ability", ["All", "Sprint", "ITT", "Mountain", "Hills", "Punch"], key="view_ability_filter")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Export riders - MOVED TO TOP
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("📥 Export Riders", key="export_riders", type="primary"):
                # Apply filters first to get the correct data for export
                export_df = df.copy()
                if team_filter != "All":
                    export_df = export_df[export_df['Team'] == team_filter]
                export_df = export_df[
                    (export_df['Price'] >= price_filter[0]) & 
                    (export_df['Price'] <= price_filter[1])
                ]
                if ability_filter != "All":
                    ability_col = ability_filter
                    if ability_filter == "ITT":
                        ability_col = "ITT"
                    export_df = export_df[export_df[ability_col].isin(['S', 'A', 'B'])]
                
                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="riders_export.csv",
                    mime="text/csv"
                )
        
        # Apply filters
        filtered_df = df.copy()
        if team_filter != "All":
            filtered_df = filtered_df[filtered_df['Team'] == team_filter]
        filtered_df = filtered_df[
            (filtered_df['Price'] >= price_filter[0]) & 
            (filtered_df['Price'] <= price_filter[1])
        ]
        
        # Apply ability filter if selected
        if ability_filter != "All":
            ability_col = ability_filter
            if ability_filter == "ITT":
                ability_col = "ITT"
            # Show riders with S, A, or B tier in that category
            filtered_df = filtered_df[filtered_df[ability_col].isin(['S', 'A', 'B'])]
        
        # Display fancy statistics
        st.markdown('<div class="stats-card">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Riders", len(filtered_df))
        with col2:
            avg_price = filtered_df['Price'].mean()
            st.metric("💰 Avg Price", f"${avg_price:.2f}")
        with col3:
            teams_count = filtered_df['Team'].nunique()
            st.metric("🏢 Teams", teams_count)
        with col4:
            top_tier_count = len(filtered_df[filtered_df[['Sprint', 'ITT', 'Mountain', 'Hills', 'Punch']].isin(['S', 'A']).any(axis=1)])
            st.metric("⭐ Top Tier", top_tier_count)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Fancy data display
        st.write("**📋 Rider Details**")
        
        # Style the dataframe
        def style_tier(val):
            colors = {
                'S': 'background-color: #FFD700; color: #000; font-weight: bold;',
                'A': 'background-color: #C0C0C0; color: #000; font-weight: bold;',
                'B': 'background-color: #CD7F32; color: #fff; font-weight: bold;',
                'C': 'background-color: #8B4513; color: #fff; font-weight: bold;',
                'D': 'background-color: #654321; color: #fff; font-weight: bold;',
                'E': 'background-color: #2F2F2F; color: #fff; font-weight: bold;'
            }
            return colors.get(val, '')
        
        # Apply styling
        styled_df = filtered_df.style.applymap(style_tier, subset=['Sprint', 'ITT', 'Mountain', 'Hills', 'Punch'])
        
        # Display with custom styling
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=400
        )
    
    with tab4:
        st.subheader("✏️ Edit Rider Parameters")
        
        # Select rider
        rider_names = [rider.name for rider in riders]
        selected_rider = st.selectbox("Select rider to edit", rider_names, key="edit_rider_select")
        
        if selected_rider:
            rider = st.session_state.rider_db.get_rider(selected_rider)
            
            # Fancy rider info card
            st.markdown(f"""
            <div class="rider-card">
                <h4>🏆 {rider.name}</h4>
                <p><span class="team-badge">{rider.team}</span></p>
                <p><span class="price-badge">💰 ${rider.price:.2f}</span></p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**💰 Basic Info**")
                new_price = st.number_input("Price", value=float(rider.price), step=0.1, key="edit_price")
                new_abandon = st.slider("Abandon chance", 0.0, 1.0, float(rider.chance_of_abandon), 0.01, key="edit_abandon")
            
            with col2:
                st.write("**⚡ Current Abilities**")
                current_abilities = {
                    "Sprint": rider.parameters.sprint_ability,
                    "ITT": rider.parameters.itt_ability,
                    "Mountain": rider.parameters.mountain_ability,
                    "Hills": rider.parameters.hills_ability,
                    "Punch": rider.parameters.punch_ability
                }
                
                for skill, ability in current_abilities.items():
                    tier = ability_to_tier(ability)
                    st.write(f"{skill}: **{tier}** ({ability})")
                
                # Ability sliders
                st.write("**🎯 New Abilities**")
                new_sprint = st.slider("Sprint", 0, 100, rider.parameters.sprint_ability, key="edit_sprint")
                new_itt = st.slider("ITT", 0, 100, rider.parameters.itt_ability, key="edit_itt")
                new_mountain = st.slider("Mountain", 0, 100, rider.parameters.mountain_ability, key="edit_mountain")
                new_hills = st.slider("Hills", 0, 100, rider.parameters.hills_ability, key="edit_hills")
                new_punch = st.slider("Punch", 0, 100, rider.parameters.punch_ability, key="edit_punch")
            
            # Save Changes button - MOVED TO AFTER FORM FIELDS
            if st.button("💾 Save Changes", key="save_rider_changes", type="primary"):
                # Update rider parameters
                rider.price = new_price
                rider.chance_of_abandon = new_abandon
                rider.parameters.sprint_ability = new_sprint
                rider.parameters.itt_ability = new_itt
                rider.parameters.mountain_ability = new_mountain
                rider.parameters.hills_ability = new_hills
                rider.parameters.punch_ability = new_punch
                
                st.success("✅ Rider parameters updated!")
    
    with tab5:
        st.subheader("➕ Add New Rider")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📝 Basic Information**")
            new_name = st.text_input("Rider name", key="add_name")
            new_team = st.text_input("Team", key="add_team")
            new_age = st.number_input("Age", min_value=18, max_value=50, value=25, key="add_age")
            new_price = st.number_input("Price", min_value=0.0, value=1.0, step=0.1, key="add_price")
            new_abandon = st.slider("Abandon chance", 0.0, 1.0, 0.0, 0.01, key="add_abandon")
        
        with col2:
            st.write("**⚡ Abilities**")
            new_sprint = st.slider("Sprint ability", 0, 100, 50, key="add_sprint")
            new_itt = st.slider("ITT ability", 0, 100, 50, key="add_itt")
            new_mountain = st.slider("Mountain ability", 0, 100, 50, key="add_mountain")
            new_hills = st.slider("Hills ability", 0, 100, 50, key="add_hills")
            new_punch = st.slider("Punch ability", 0, 100, 50, key="add_punch")
        
        # Add Rider button - MOVED TO TOP AFTER FORM FIELDS
        if st.button("➕ Add Rider", key="add_rider_button", type="primary"):
            if new_name and new_team:
                # Create new rider parameters
                new_parameters = RiderParameters(
                    sprint_ability=new_sprint,
                    itt_ability=new_itt,
                    mountain_ability=new_mountain,
                    hills_ability=new_hills,
                    punch_ability=new_punch
                )
                
                # Create new rider
                new_rider = Rider(
                    name=new_name,
                    team=new_team,
                    parameters=new_parameters,
                    age=new_age,
                    price=new_price,
                    chance_of_abandon=new_abandon
                )
                
                # Add to database
                st.session_state.rider_db.riders.append(new_rider)
                
                st.success(f"✅ Added rider: {new_name}")
            else:
                st.error("Please fill in all required fields")

def show_tier_maker():
    st.subheader("🏆 Tier Maker")
    st.write("Drag and drop riders between tiers to adjust their abilities. Changes are applied immediately.")
    
    # Add custom CSS for tier maker styling
    st.markdown("""
    <style>
    .tier-maker-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #4CAF50;
    }
    .tier-maker-card h4 {
        color: white;
        margin: 0 0 5px 0;
        font-size: 16px;
        font-weight: bold;
    }
    .tier-maker-card p {
        color: #f0f0f0;
        margin: 2px 0;
        font-size: 12px;
    }
    .tier-column {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border: 2px solid #dee2e6;
    }
    .tier-s {
        border-color: #FFD700 !important;
        background: linear-gradient(135deg, #fff8dc 0%, #fffacd 100%) !important;
    }
    .tier-a {
        border-color: #C0C0C0 !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
    }
    .tier-b {
        border-color: #CD7F32 !important;
        background: linear-gradient(135deg, #f4e4bc 0%, #e6d7a3 100%) !important;
    }
    .tier-c {
        border-color: #8B4513 !important;
        background: linear-gradient(135deg, #e6d7a3 0%, #d4c4a3 100%) !important;
    }
    .tier-d {
        border-color: #654321 !important;
        background: linear-gradient(135deg, #d4c4a3 0%, #c4b4a3 100%) !important;
    }
    .tier-e {
        border-color: #2F2F2F !important;
        background: linear-gradient(135deg, #c4b4a3 0%, #b4a4a3 100%) !important;
    }
    .tier-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        font-weight: bold;
        font-size: 14px;
    }
    .rider-item {
        background: white;
        border-radius: 8px;
        padding: 10px;
        margin: 8px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        border-left: 3px solid #4CAF50;
        transition: all 0.3s ease;
    }
    .rider-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    .rider-name {
        font-weight: bold;
        color: #333;
        font-size: 14px;
        margin-bottom: 3px;
    }
    .rider-team {
        color: #666;
        font-size: 11px;
        margin-bottom: 3px;
    }
    .rider-price {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        color: #333;
        padding: 3px 6px;
        border-radius: 10px;
        font-size: 10px;
        font-weight: bold;
        display: inline-block;
        margin: 2px 0;
    }
    .move-buttons {
        display: flex;
        gap: 5px;
        margin-top: 8px;
    }
    .move-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 5px;
        padding: 4px 8px;
        font-size: 11px;
        cursor: pointer;
        transition: all 0.3s ease;
        flex: 1;
    }
    .move-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .move-btn:disabled {
        background: #ccc;
        cursor: not-allowed;
        transform: none;
    }
    .tier-stats-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .tier-controls {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .skill-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 15px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Skill category selector with fancy styling
    st.markdown('<div class="skill-selector">', unsafe_allow_html=True)
    st.write("**🎯 Select Skill Category**")
    skill_categories = ["Sprint", "ITT", "Mountain", "Hills", "Punch"]
    selected_skill = st.selectbox("Choose the skill to manage tiers for:", skill_categories, key="tier_skill_select")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get all riders
    riders = st.session_state.rider_db.get_all_riders()
    
    # Define tier scores for conversion
    tier_scores = {
        "S": 98,
        "A": 95, 
        "B": 90,
        "C": 80,
        "D": 70,
        "E": 40
    }
    
    # Function to convert ability to tier
    def ability_to_tier(ability: int) -> str:
        for tier, score in tier_scores.items():
            if ability >= score:
                return tier
        return "E"
    
    # Function to convert tier to ability
    def tier_to_ability(tier: str) -> int:
        return tier_scores.get(tier, 40)
    
    # Get current tiers for selected skill
    def get_skill_ability(rider, skill):
        if skill == "Sprint":
            return rider.parameters.sprint_ability
        elif skill == "ITT":
            return rider.parameters.itt_ability
        elif skill == "Mountain":
            return rider.parameters.mountain_ability
        elif skill == "Hills":
            return rider.parameters.hills_ability
        elif skill == "Punch":
            return rider.parameters.punch_ability
        return 0
    
    def set_skill_ability(rider, skill, ability):
        if skill == "Sprint":
            rider.parameters.sprint_ability = ability
        elif skill == "ITT":
            rider.parameters.itt_ability = ability
        elif skill == "Mountain":
            rider.parameters.mountain_ability = ability
        elif skill == "Hills":
            rider.parameters.hills_ability = ability
        elif skill == "Punch":
            rider.parameters.punch_ability = ability
    
    # Group riders by current tier
    tier_groups = {"S": [], "A": [], "B": [], "C": [], "D": [], "E": []}
    
    for rider in riders:
        current_ability = get_skill_ability(rider, selected_skill)
        current_tier = ability_to_tier(current_ability)
        tier_groups[current_tier].append(rider)
    
    # Search and team filters with fancy styling
    st.markdown('<div class="tier-controls">', unsafe_allow_html=True)
    st.write("**🔍 Filter Options**")
    col1, col2 = st.columns(2)
    with col1:
        search_term = st.text_input("Search riders", key="tier_search", placeholder="Enter rider name...")
    with col2:
        team_filter = st.selectbox("Filter by team", ["All"] + sorted(list(set([r.team for r in riders]))), key="tier_team_filter")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Filter riders based on search and team
    def filter_rider(rider):
        if search_term and search_term.lower() not in rider.name.lower():
            return False
        if team_filter != "All" and rider.team != team_filter:
            return False
        return True
    
    # Apply filters to tier groups
    filtered_tier_groups = {}
    for tier, rider_list in tier_groups.items():
        filtered_tier_groups[tier] = [r for r in rider_list if filter_rider(r)]
    
    # Fancy controls section - MOVED TO TOP AFTER VARIABLE DEFINITIONS
    st.markdown('<div class="tier-controls">', unsafe_allow_html=True)
    st.write("**⚙️ Tier Controls**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset to Default", key="reset_tiers", type="primary"):
            # Reset all riders to their original tiers for this skill
            for rider in riders:
                # Get original ability from rider data
                original_ability = get_skill_ability(rider, selected_skill)
                set_skill_ability(rider, selected_skill, original_ability)
            st.success("Tiers reset to default!")
            st.rerun()
    
    with col2:
        if st.button("📥 Export Tiers", key="export_tiers", type="primary"):
            # Create export data
            export_data = []
            tier_names = ["S", "A", "B", "C", "D", "E"]
            for tier in tier_names:
                for rider in filtered_tier_groups[tier]:
                    export_data.append({
                        'Rider': rider.name,
                        'Team': rider.team,
                        'Tier': tier,
                        'Price': rider.price,
                        'Skill': selected_skill
                    })
            
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"tier_maker_{selected_skill.lower()}.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("💾 Save Changes", key="save_tier_changes", type="primary"):
            st.success("✅ Tier changes saved!")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create tier columns with fancy styling
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    tier_columns = [col1, col2, col3, col4, col5, col6]
    tier_names = ["S", "A", "B", "C", "D", "E"]
    tier_colors = ["#FFD700", "#C0C0C0", "#CD7F32", "#8B4513", "#654321", "#2F2F2F"]
    
    # Track changes
    changes_made = False
    
    for i, (tier, col) in enumerate(zip(tier_names, tier_columns)):
        with col:
            # Fancy tier header
            st.markdown(f"""
            <div class="tier-header" style="border-left: 4px solid {tier_colors[i]};">
                🏆 {tier} Tier
                <br><small>({len(filtered_tier_groups[tier])} riders)</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Show riders in this tier with fancy cards
            for rider in filtered_tier_groups[tier]:
                # Create a unique key for each rider
                rider_key = f"{rider.name}_{selected_skill}_{tier}"
                
                # Fancy rider card
                st.markdown(f"""
                <div class="rider-item">
                    <div class="rider-name">{rider.name}</div>
                    <div class="rider-team">{rider.team}</div>
                    <div class="rider-price">💰 ${rider.price:.2f}</div>
                    <div class="move-buttons">
                """, unsafe_allow_html=True)
                
                # Move buttons
                col_move1, col_move2 = st.columns(2)
                
                with col_move1:
                    if tier != "S":  # Can't move up from S tier
                        if st.button("⬆️ Up", key=f"up_{rider_key}", help=f"Move {rider.name} to {tier_names[i-1]} tier"):
                            # Move rider up one tier
                            new_tier = tier_names[i-1]
                            new_ability = tier_to_ability(new_tier)
                            set_skill_ability(rider, selected_skill, new_ability)
                            changes_made = True
                            st.rerun()
                    else:
                        st.button("⬆️ Up", key=f"up_{rider_key}", disabled=True, help="Already at top tier")
                
                with col_move2:
                    if tier != "E":  # Can't move down from E tier
                        if st.button("⬇️ Down", key=f"down_{rider_key}", help=f"Move {rider.name} to {tier_names[i+1]} tier"):
                            # Move rider down one tier
                            new_tier = tier_names[i+1]
                            new_ability = tier_to_ability(new_tier)
                            set_skill_ability(rider, selected_skill, new_ability)
                            changes_made = True
                            st.rerun()
                    else:
                        st.button("⬇️ Down", key=f"down_{rider_key}", disabled=True, help="Already at bottom tier")
                
                st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Fancy tier statistics
    st.markdown('<div class="tier-stats-card">', unsafe_allow_html=True)
    st.write("**📊 Tier Statistics**")
    
    # Calculate statistics
    total_riders = sum(len(riders) for riders in filtered_tier_groups.values())
    tier_stats = {}
    
    for tier in tier_names:
        riders_in_tier = filtered_tier_groups[tier]
        tier_stats[tier] = {
            'count': len(riders_in_tier),
            'percentage': (len(riders_in_tier) / total_riders * 100) if total_riders > 0 else 0,
            'avg_price': sum(r.price for r in riders_in_tier) / len(riders_in_tier) if riders_in_tier else 0
        }
    
    # Display statistics in a fancy layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**📈 Distribution:**")
        for tier in tier_names:
            stats = tier_stats[tier]
            st.write(f"🏆 {tier} Tier: **{stats['count']}** riders ({stats['percentage']:.1f}%)")
            st.write(f"💰 Avg Price: **${stats['avg_price']:.2f}**")
            st.divider()
    
    with col2:
        # Create distribution chart
        fig, ax = plt.subplots(figsize=(8, 6))
        tiers = list(tier_stats.keys())
        counts = [tier_stats[tier]['count'] for tier in tiers]
        colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#8B4513', '#654321', '#2F2F2F']
        
        bars = ax.bar(tiers, counts, color=colors, edgecolor='white', linewidth=2)
        ax.set_title(f'{selected_skill} Tier Distribution', fontsize=14, fontweight='bold')
        ax.set_ylabel('Number of Riders', fontsize=12)
        ax.set_xlabel('Tier', fontsize=12)
        
        # Add value labels on bars
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{count}', ha='center', va='bottom', fontweight='bold')
        
        # Style the chart
        ax.grid(axis='y', alpha=0.3)
        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('#f8f9fa')
        
        st.pyplot(fig)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if changes_made:
        st.info("ℹ️ Changes have been applied. Use 'Save Changes' to persist them.")

def show_tier_parameters_management():
    st.subheader("🏆 Winning Probabilities Management")
    st.markdown("""
    **Adjust the probability parameters that determine rider performance based on their tier levels.**
    These parameters affect how likely riders are to achieve different positions in stage results.
    """)
    
    # Import rider parameters
    from rider_parameters import get_tier_parameters, update_tier_parameters
    
    # Initialize tier parameters in session state
    if 'tier_parameters' not in st.session_state:
        st.session_state.tier_parameters = get_tier_parameters()
    
    # Tier descriptions
    tier_descriptions = {
        "exceptional": "S Tier (98+) - The very best riders",
        "world_class": "A Tier (95-97) - Elite performers", 
        "elite": "B Tier (90-94) - Very strong riders",
        "very_good": "C Tier (80-89) - Above average",
        "good": "D Tier (70-79) - Competent level",
        "average": "E Tier (50-69) - Standard performance",
        "below_average": "E Tier (<50) - Limited ability"
    }
    
    # Controls - MOVED TO TOP
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset to Default", key="reset_tier_params"):
            st.session_state.tier_parameters = get_tier_parameters()
            st.rerun()
    
    with col2:
        if st.button("📊 Export Parameters", key="export_tier_params"):
            # Create export data
            export_data = []
            for tier_name, params in st.session_state.tier_parameters.items():
                export_data.append({
                    'Tier': tier_descriptions[tier_name].split('(')[0].strip(),
                    'Min_Position': params["min"],
                    'Mode_Position': params["mode"],
                    'Max_Position': params["max"],
                    'Range_Position': params["max"] - params["min"]
                })
            
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Parameters CSV",
                data=csv,
                file_name="tier_parameters.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("💾 Apply Changes", key="apply_tier_changes"):
            # Update the actual rider parameters
            update_tier_parameters(st.session_state.tier_parameters)
            st.success("✅ Tier parameters updated! Changes will apply to new simulations.")
    
    # Create a grid for parameter editing
    tier_names = list(st.session_state.tier_parameters.keys())
    
    for i, tier_name in enumerate(tier_names):
        st.markdown(f"---")
        st.markdown(f"**{tier_descriptions[tier_name]}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_val = st.number_input(
                "Min (position)",
                value=st.session_state.tier_parameters[tier_name]["min"],
                min_value=1,
                max_value=200,
                key=f"min_{tier_name}"
            )
            st.session_state.tier_parameters[tier_name]["min"] = min_val
        
        with col2:
            mode_val = st.number_input(
                "Mode (position)", 
                value=st.session_state.tier_parameters[tier_name]["mode"],
                min_value=1,
                max_value=200,
                key=f"mode_{tier_name}"
            )
            st.session_state.tier_parameters[tier_name]["mode"] = mode_val
        
        with col3:
            max_val = st.number_input(
                "Max (position)",
                value=st.session_state.tier_parameters[tier_name]["max"], 
                min_value=1,
                max_value=200,
                key=f"max_{tier_name}"
            )
            st.session_state.tier_parameters[tier_name]["max"] = max_val
    
    # Visual representation
    st.markdown("---")
    st.markdown("### Parameter Visualization")
    
    # Create a chart showing the probability distributions
    fig = go.Figure()
    
    colors = ['#FF6B6B', '#FFA500', '#FFD93D', '#6BCF7F', '#4ECDC4', '#45B7D1', '#9B59B6']
    
    for i, (tier_name, params) in enumerate(st.session_state.tier_parameters.items()):
        # Create triangular distribution visualization
        min_val, mode_val, max_val = params["min"], params["mode"], params["max"]
        
        # Generate points for triangular distribution
        x = [min_val, mode_val, max_val]
        y = [0, 1, 0]  # Triangular shape
        
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines+markers',
            name=tier_descriptions[tier_name].split('(')[0].strip(),
            line=dict(color=colors[i % len(colors)], width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Probability Distributions by Tier",
        xaxis_title="Position/Result (1 = winner)",
        yaxis_title="Probability Density",
        height=500,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Parameter summary table
    st.markdown("### Current Parameters Summary")
    
    summary_data = []
    for tier_name, params in st.session_state.tier_parameters.items():
        summary_data.append({
            'Tier': tier_descriptions[tier_name].split('(')[0].strip(),
            'Min (pos)': params["min"],
            'Mode (pos)': params["mode"], 
            'Max (pos)': params["max"],
            'Range (pos)': params["max"] - params["min"]
        })
    
    df = pd.DataFrame(summary_data)
    st.dataframe(df, use_container_width=True)

def show_results_analysis():
    st.header("📈 Results Analysis")
    
    if st.session_state.simulation_results is None and st.session_state.multi_simulation_results is None:
        st.warning("No simulation results available. Run a simulation first.")
        return
    
    tab1, tab2, tab3 = st.tabs(["📊 Single Simulation", "📈 Multi-Simulation", "🎯 Optimization"])
    
    with tab1:
        if st.session_state.simulation_results is not None:
            show_simulation_results(st.session_state.simulation_results)
        else:
            st.info("No single simulation results available")
    
    with tab2:
        if st.session_state.multi_simulation_results is not None:
            show_multi_simulation_analysis(st.session_state.multi_simulation_results)
        else:
            st.info("No multi-simulation results available")
    
    with tab3:
        if st.session_state.optimization_results is not None:
            show_optimization_results(st.session_state.optimization_results)
        else:
            st.info("No optimization results available")

def show_simulation_results(simulator):
    st.subheader("📊 Simulation Results")
    
    # Final classifications
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.write("**🏆 General Classification**")
        gc_results = [(rider, time) for rider, time in simulator.get_final_gc() if rider not in simulator.abandoned_riders]
        for i, (rider, time) in enumerate(gc_results[:5]):
            st.write(f"{i+1}. {rider} ({time/3600:.2f}h)")
    
    with col2:
        st.write("**🏁 Sprint Classification**")
        sprint_results = [(rider, points) for rider, points in simulator.get_final_sprint() if rider not in simulator.abandoned_riders]
        for i, (rider, points) in enumerate(sprint_results[:5]):
            st.write(f"{i+1}. {rider} ({points} pts)")
    
    with col3:
        st.write("**⛰️ Mountain Classification**")
        mountain_results = [(rider, points) for rider, points in simulator.get_final_mountain() if rider not in simulator.abandoned_riders]
        for i, (rider, points) in enumerate(mountain_results[:5]):
            st.write(f"{i+1}. {rider} ({points} pts)")
    
    with col4:
        st.write("**👶 Youth Classification**")
        youth_results = [(rider, time) for rider, time in simulator.get_final_youth() if rider not in simulator.abandoned_riders]
        for i, (rider, time) in enumerate(youth_results[:5]):
            st.write(f"{i+1}. {rider} ({time/3600:.2f}h)")
    
    # Stage-by-stage analysis
    st.subheader("📈 Stage-by-Stage Analysis")
    
    # Create stage results DataFrame
    stage_df = pd.DataFrame(simulator.stage_results_records)
    
    if not stage_df.empty:
        # Plot stage winners
        stage_winners = stage_df[stage_df['position'] == 1]
        
        fig = px.bar(
            stage_winners, 
            x='stage', 
            y='rider',
            title="Stage Winners",
            labels={'stage': 'Stage', 'rider': 'Winner'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Team performance
        team_performance = stage_df.groupby('team')['position'].mean().sort_values()
        
        fig2 = px.bar(
            x=team_performance.index,
            y=team_performance.values,
            title="Average Team Performance (Lower is better)",
            labels={'x': 'Team', 'y': 'Average Position'}
        )
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, use_container_width=True)

def show_multi_simulation_analysis(results):
    st.subheader("📈 Comprehensive Multi-Simulation Analysis")
    
    # Create tabs for different analysis sections
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Overview", "🏁 Stage Analysis", "🏆 Classifications", "💰 Scorito Points", 
        "👥 Rider Insights", "🏢 Team Performance", "📈 Advanced Metrics"
    ])
    
    with tab1:
        show_overview_metrics(results)
    
    with tab2:
        show_stage_analysis(results)
    
    with tab3:
        show_classification_analysis(results)
    
    with tab4:
        show_scorito_analysis(results)
    
    with tab5:
        show_rider_insights(results)
    
    with tab6:
        show_team_performance_analysis(results)
    
    with tab7:
        show_advanced_metrics(results)

def show_overview_metrics(results):
    """Display overview metrics and summary statistics"""
    st.subheader("📊 Simulation Overview")
    
    summary = results['simulation_summary']
    
    # Key metrics cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Simulations", 
            f"{summary['total_simulations']:,}",
            help="Number of Tour de France simulations run"
        )
    
    with col2:
        st.metric(
            "Total Riders", 
            f"{summary['total_riders']:,}",
            help="Number of riders in the simulation"
        )
    
    with col3:
        st.metric(
            "Avg Abandonments", 
            f"{summary['avg_abandonments']:.1f}",
            help="Average number of riders who abandon per simulation"
        )
    
    with col4:
        st.metric(
            "Avg Total Points", 
            f"{summary['avg_total_points']:.0f}",
            help="Average total Scorito points per simulation"
        )
    
    # Abandonment analysis
    st.subheader("💥 Abandonment Analysis")
    abandonment_data = results['abandonment_analysis']
    
    # Top riders by abandonment rate
    high_risk_riders = {k: v for k, v in abandonment_data.items() if v['abandonment_rate'] > 0.1}
    if high_risk_riders:
        st.warning("⚠️ High-risk riders (abandonment rate > 10%):")
        for rider, data in sorted(high_risk_riders.items(), key=lambda x: x[1]['abandonment_rate'], reverse=True)[:10]:
            st.write(f"• {rider}: {data['abandonment_rate']:.1%} chance of abandoning")
    
    # Stage type impact
    st.subheader("🏁 Stage Type Impact")
    stage_type_data = results['stage_type_impact']
    
    if stage_type_data:
        stage_type_df = pd.DataFrame([
            {
                'Stage Type': stage_type,
                'Avg Position': data['avg_position'],
                'Position Std': data['position_std'],
                'Unique Riders': data['unique_riders']
            }
            for stage_type, data in stage_type_data.items()
        ])
        
        fig = px.bar(
            stage_type_df, 
            x='Stage Type', 
            y='Avg Position',
            title="Average Position by Stage Type",
            color='Position Std',
            color_continuous_scale='viridis'
        )
        st.plotly_chart(fig, use_container_width=True)

def show_stage_analysis(results):
    """Display detailed stage-by-stage analysis"""
    st.subheader("🏁 Stage-by-Stage Analysis")
    
    stage_analysis = results['stage_analysis']
    
    # Stage selector
    selected_stage = st.selectbox(
        "Select Stage to Analyze",
        options=list(range(1, 22)),
        format_func=lambda x: f"Stage {x}"
    )
    
    if selected_stage in stage_analysis:
        stage_data = stage_analysis[selected_stage]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Finishers", stage_data['total_finishers'])
            
            # Stage winners frequency
            if stage_data['stage_winner_frequency']:
                st.subheader("🏆 Most Frequent Stage Winners")
                winners_df = pd.DataFrame([
                    {'Rider': rider, 'Wins': wins}
                    for rider, wins in stage_data['stage_winner_frequency'].items()
                ]).sort_values('Wins', ascending=False).head(10)
                
                fig = px.bar(winners_df, x='Rider', y='Wins', title=f"Stage {selected_stage} Winners")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Team dominance
            if stage_data['avg_position_by_team']:
                st.subheader("🏢 Team Performance")
                team_df = pd.DataFrame([
                    {'Team': team, 'Avg Position': pos}
                    for team, pos in stage_data['avg_position_by_team'].items()
                ]).sort_values('Avg Position')
                
                fig = px.bar(team_df, x='Team', y='Avg Position', title=f"Stage {selected_stage} Team Performance")
                st.plotly_chart(fig, use_container_width=True)
    
    # Stage consistency analysis
    st.subheader("📈 Stage Consistency Analysis")
    
    # Calculate consistency across all stages
    all_stages_data = []
    for stage_num in range(1, 22):
        if stage_num in stage_analysis:
            stage_data = stage_analysis[stage_num]
            if stage_data['position_volatility']:
                avg_volatility = np.mean(list(stage_data['position_volatility'].values()))
                all_stages_data.append({
                    'Stage': stage_num,
                    'Avg Volatility': avg_volatility,
                    'Total Finishers': stage_data['total_finishers']
                })
    
    if all_stages_data:
        stages_df = pd.DataFrame(all_stages_data)
        
        fig = px.line(
            stages_df, 
            x='Stage', 
            y='Avg Volatility',
            title="Position Volatility by Stage",
            markers=True
        )
        st.plotly_chart(fig, use_container_width=True)

def show_classification_analysis(results):
    """Display classification analysis"""
    st.subheader("🏆 Classification Analysis")
    
    classification_analysis = results['classification_analysis']
    
    # Classification selector
    classification = st.selectbox(
        "Select Classification",
        options=['gc', 'sprint', 'mountain', 'youth'],
        format_func=lambda x: x.upper()
    )
    
    if classification in classification_analysis:
        class_data = classification_analysis[classification]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Winner frequency
            if class_data['winner_frequency']:
                st.subheader(f"🏆 {classification.upper()} Winners")
                winners_df = pd.DataFrame([
                    {'Rider': rider, 'Wins': wins}
                    for rider, wins in class_data['winner_frequency'].items()
                ]).sort_values('Wins', ascending=False).head(10)
                
                fig = px.bar(winners_df, x='Rider', y='Wins', title=f"{classification.upper()} Winners")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Podium frequency
            if class_data['podium_frequency']:
                st.subheader(f"🥇🥈🥉 {classification.upper()} Podium")
                podium_data = []
                for rider, positions in class_data['podium_frequency'].items():
                    for pos, count in positions.items():
                        podium_data.append({
                            'Rider': rider,
                            'Position': f"{pos}{'st' if pos==1 else 'nd' if pos==2 else 'rd' if pos==3 else 'th'}",
                            'Count': count
                        })
                
                if podium_data:
                    podium_df = pd.DataFrame(podium_data)
                    fig = px.bar(
                        podium_df, 
                        x='Rider', 
                        y='Count', 
                        color='Position',
                        title=f"{classification.upper()} Podium Frequency"
                    )
                    st.plotly_chart(fig, use_container_width=True)
        
        # Classification volatility
        if class_data['classification_volatility']:
            st.subheader(f"📊 {classification.upper()} Volatility")
            volatility_df = pd.DataFrame([
                {'Rider': rider, 'Volatility': vol}
                for rider, vol in class_data['classification_volatility'].items()
            ]).sort_values('Volatility').head(15)
            
            fig = px.bar(volatility_df, x='Rider', y='Volatility', title=f"{classification.upper()} Position Volatility")
            st.plotly_chart(fig, use_container_width=True)

def show_scorito_analysis(results):
    """Display Scorito points analysis"""
    st.subheader("💰 Scorito Points Analysis")
    
    scorito_analysis = results['scorito_analysis']
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Top scorers
        if scorito_analysis['top_scorers']:
            st.subheader("🏆 Top Scorito Scorers")
            top_scorers_df = pd.DataFrame([
                {'Rider': rider, 'Points': points}
                for rider, points in scorito_analysis['top_scorers'].items()
            ])
            
            fig = px.bar(top_scorers_df, x='Rider', y='Points', title="Top Scorito Scorers")
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Points by team
        if scorito_analysis['points_by_team']:
            st.subheader("🏢 Points by Team")
            team_points_df = pd.DataFrame([
                {'Team': team, 'Points': points}
                for team, points in scorito_analysis['points_by_team'].items()
            ]).sort_values('Points', ascending=False)
            
            fig = px.pie(team_points_df, values='Points', names='Team', title="Scorito Points by Team")
            st.plotly_chart(fig, use_container_width=True)
    
    # Points distribution
    if scorito_analysis['total_points_distribution']:
        st.subheader("📊 Points Distribution")
        dist_data = scorito_analysis['total_points_distribution']
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Points", f"{dist_data.get('mean', 0):.1f}")
        with col2:
            st.metric("Median Points", f"{dist_data.get('50%', 0):.1f}")
        with col3:
            st.metric("Std Dev", f"{dist_data.get('std', 0):.1f}")
        with col4:
            st.metric("Max Points", f"{dist_data.get('max', 0):.1f}")
    
    # Stage points volatility
    if scorito_analysis['stage_points_volatility']:
        st.subheader("📈 Stage Points Volatility")
        stage_volatility_df = pd.DataFrame([
            {'Stage': stage, 'Volatility': vol}
            for stage, vol in scorito_analysis['stage_points_volatility'].items()
        ])
        
        fig = px.line(stage_volatility_df, x='Stage', y='Volatility', title="Points Volatility by Stage")
        st.plotly_chart(fig, use_container_width=True)

def show_rider_insights(results):
    """Display rider-specific insights"""
    st.subheader("👥 Rider Insights")
    
    rider_consistency = results['rider_consistency']
    price_value = results['price_value_analysis']
    youth_analysis = results['youth_analysis']
    
    # Rider selector
    all_riders = list(rider_consistency.keys())
    selected_rider = st.selectbox("Select Rider", all_riders)
    
    if selected_rider in rider_consistency:
        rider_data = rider_consistency[selected_rider]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Avg Position", f"{rider_data['avg_position']:.1f}")
        with col2:
            st.metric("Consistency Score", f"{rider_data['consistency_score']:.3f}")
        with col3:
            st.metric("Top 10 Rate", f"{rider_data['top_10_rate']:.1%}")
        with col4:
            st.metric("Stages Completed", rider_data['stages_completed'])
        
        # Price value analysis
        if selected_rider in price_value:
            price_data = price_value[selected_rider]
            
            st.subheader("💰 Price-Value Analysis")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Price", f"€{price_data['price']:.1f}")
            with col2:
                st.metric("Avg Points", f"{price_data['avg_points']:.1f}")
            with col3:
                st.metric("Points/€", f"{price_data['points_per_euro']:.2f}")
        
        # Youth analysis if applicable
        if selected_rider in youth_analysis:
            youth_data = youth_analysis[selected_rider]
            st.subheader("🌱 Youth Performance")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Youth Consistency", f"{youth_data['youth_consistency']:.3f}")
            with col2:
                st.metric("Avg GC Time", f"{youth_data['avg_gc_time']/3600:.1f}h")
    
    # Top value riders
    st.subheader("💎 Best Value Riders")
    if price_value:
        value_df = pd.DataFrame([
            {
                'Rider': rider,
                'Price': data['price'],
                'Avg Points': data['avg_points'],
                'Points/€': data['points_per_euro'],
                'Value Score': data['value_score'],
                'Team': data['team']
            }
            for rider, data in price_value.items()
        ]).sort_values('Value Score', ascending=False).head(15)
        
        fig = px.scatter(
            value_df, 
            x='Price', 
            y='Avg Points',
            size='Value Score',
            color='Team',
            hover_data=['Rider', 'Points/€'],
            title="Price vs Points (Size = Value Score)"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_team_performance_analysis(results):
    """Display team performance analysis"""
    st.subheader("🏢 Team Performance Analysis")
    
    team_performance = results['team_performance']
    
    if team_performance:
        team_df = pd.DataFrame([
            {
                'Team': team,
                'Riders': data['riders_count'],
                'Avg Position': data['avg_position'],
                'Total Points': data['total_points'],
                'Avg Points/Rider': data['avg_points_per_rider'],
                'Consistency': data['team_consistency']
            }
            for team, data in team_performance.items()
        ])
        
        # Team performance overview
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                team_df.sort_values('Total Points', ascending=False),
                x='Team', 
                y='Total Points',
                title="Total Scorito Points by Team"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.scatter(
                team_df,
                x='Avg Position', 
                y='Total Points',
                size='Riders',
                color='Team',
                hover_data=['Avg Points/Rider', 'Consistency'],
                title="Team Performance: Position vs Points"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Team consistency
        st.subheader("📊 Team Consistency")
        consistency_df = team_df.sort_values('Consistency', ascending=False)
        
        fig = px.bar(
            consistency_df,
            x='Team', 
            y='Consistency',
            title="Team Consistency Score (Higher = More Consistent)"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_advanced_metrics(results):
    """Display advanced analytical metrics"""
    st.subheader("📈 Advanced Analytics")
    
    # Correlation analysis
    st.subheader("🔗 Performance Correlations")
    
    # Combine rider data for correlation analysis
    rider_consistency = results['rider_consistency']
    price_value = results['price_value_analysis']
    
    correlation_data = []
    for rider in rider_consistency:
        if rider in price_value:
            correlation_data.append({
                'Rider': rider,
                'Consistency': rider_consistency[rider]['consistency_score'],
                'Avg Position': rider_consistency[rider]['avg_position'],
                'Top 10 Rate': rider_consistency[rider]['top_10_rate'],
                'Price': price_value[rider]['price'],
                'Avg Points': price_value[rider]['avg_points'],
                'Value Score': price_value[rider]['value_score']
            })
    
    if correlation_data:
        corr_df = pd.DataFrame(correlation_data)
        
        # Correlation matrix
        numeric_cols = ['Consistency', 'Avg Position', 'Top 10 Rate', 'Price', 'Avg Points', 'Value Score']
        correlation_matrix = corr_df[numeric_cols].corr()
        
        fig = px.imshow(
            correlation_matrix,
            title="Performance Metrics Correlation Matrix",
            color_continuous_scale='RdBu',
            aspect='auto'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Key insights
        st.subheader("💡 Key Insights")
        
        # Price vs Performance correlation
        price_perf_corr = correlation_matrix.loc['Price', 'Avg Points']
        st.metric(
            "Price-Performance Correlation", 
            f"{price_perf_corr:.3f}",
            help="Correlation between rider price and average points"
        )
        
        # Consistency vs Performance correlation
        consistency_perf_corr = correlation_matrix.loc['Consistency', 'Avg Points']
        st.metric(
            "Consistency-Performance Correlation", 
            f"{consistency_perf_corr:.3f}",
            help="Correlation between rider consistency and average points"
        )
    
    # Risk analysis
    st.subheader("⚠️ Risk Analysis")
    abandonment_analysis = results['abandonment_analysis']
    
    if abandonment_analysis:
        # High-risk riders
        high_risk = {k: v for k, v in abandonment_analysis.items() if v['abandonment_rate'] > 0.05}
        if high_risk:
            st.warning(f"Found {len(high_risk)} riders with >5% abandonment risk")
            
            risk_df = pd.DataFrame([
                {
                    'Rider': rider,
                    'Abandonment Rate': data['abandonment_rate'],
                    'Survival Rate': data['survival_rate']
                }
                for rider, data in high_risk.items()
            ]).sort_values('Abandonment Rate', ascending=False)
            
            fig = px.bar(
                risk_df,
                x='Rider',
                y='Abandonment Rate',
                title="High-Risk Riders (Abandonment Rate > 5%)"
            )
            st.plotly_chart(fig, use_container_width=True)

def show_optimization_results(optimization_data):
    st.subheader("🎯 Optimization Results")
    
    team_selection = optimization_data['team_selection']
    rider_data = optimization_data['rider_data']
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Selected Team:**")
        for i, rider in enumerate(team_selection.riders, 1):
            st.write(f"{i}. {rider.name} ({rider.team}) - {rider.price:.1f}")
        
        st.write(f"**Total Cost:** {team_selection.total_cost:.2f}")
        st.write(f"**Expected Points:** {team_selection.expected_points:.1f}")
    
    with col2:
        # Team composition by team
        team_counts = {}
        for rider in team_selection.riders:
            team_counts[rider.team] = team_counts.get(rider.team, 0) + 1
        
        fig = px.pie(
            values=list(team_counts.values()),
            names=list(team_counts.keys()),
            title="Team Composition"
        )
        st.plotly_chart(fig, use_container_width=True)

def run_optimizer_simulation(optimizer, num_simulations, rider_db):
    """
    Custom run_simulation method that uses the modified rider database
    """
    print(f"Running {num_simulations} simulations to calculate expected points...")
    
    # Store points from all simulations
    all_points = []
    
    for i in range(num_simulations):
        if i % 10 == 0:
            print(f"Simulation {i+1}/{num_simulations}")
        
        # Run simulation
        optimizer.simulator.simulate_tour()
        
        # Get final points for each rider
        for rider_name, points in optimizer.simulator.scorito_points.items():
            all_points.append({
                'rider_name': rider_name,
                'points': points,
                'simulation': i
            })
        
        # Reset simulator for next run but keep the modified rider database
        optimizer.simulator = TourSimulator()
        inject_rider_database(optimizer.simulator, rider_db)
    
    # Calculate expected points for each rider
    points_df = pd.DataFrame(all_points)
    expected_points = points_df.groupby('rider_name')['points'].agg(['mean', 'std']).reset_index()
    expected_points.columns = ['rider_name', 'expected_points', 'points_std']
    
    # Add rider information
    rider_info = []
    for rider in rider_db.get_all_riders():
        rider_info.append({
            'rider_name': rider.name,
            'price': rider.price,
            'team': rider.team,
            'age': rider.age,
            'chance_of_abandon': rider.chance_of_abandon
        })
    
    rider_info_df = pd.DataFrame(rider_info)
    
    # Merge with expected points
    final_df = rider_info_df.merge(expected_points, on='rider_name', how='left')
    final_df['expected_points'] = final_df['expected_points'].fillna(0)
    final_df['points_std'] = final_df['points_std'].fillna(0)
    
    return final_df

def show_stage_types_management():
    st.header("🏁 Stage Types Management")
    st.markdown("""
    **Manage the stage types for each stage of the Tour de France.**
    Changes here will affect how riders perform in simulations.
    """)
    
    # Import stage profiles
    from stage_profiles import STAGE_PROFILES, StageType
    
    # Create a copy of stage profiles for editing
    if 'stage_profiles_edit' not in st.session_state:
        st.session_state.stage_profiles_edit = STAGE_PROFILES.copy()
    
    # Stage type options - use the actual enum values
    stage_type_options = {
        StageType.SPRINT: "Sprint",
        StageType.PUNCH: "Punch", 
        StageType.ITT: "Individual Time Trial",
        StageType.MOUNTAIN: "Mountain",
        StageType.HILLS: "Hills"
    }
    
    # Display current stage types
    st.markdown("### Current Stage Types")
    
    # Create a list layout for stages
    for i in range(21):  # 21 stages
        stage_num = i + 1
        
        # Create a container for each stage
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            
            with col1:
                st.markdown(f"**Stage {stage_num}**")
            
            with col2:
                # Get current stage type
                current_type = st.session_state.stage_profiles_edit.get(stage_num, StageType.SPRINT)
                
                # Create selectbox for stage type
                # Handle the case where current_type might not be in the options
                try:
                    current_index = list(stage_type_options.keys()).index(current_type)
                except ValueError:
                    # If current_type is not in options, default to first option
                    current_index = 0
                    current_type = list(stage_type_options.keys())[0]
                    st.session_state.stage_profiles_edit[stage_num] = current_type
                
                new_type = st.selectbox(
                    f"Select stage type for Stage {stage_num}",
                    options=list(stage_type_options.keys()),
                    format_func=lambda x: stage_type_options[x],
                    index=current_index,
                    key=f"stage_type_{stage_num}",
                    label_visibility="collapsed"
                )
                
                # Update if changed
                if new_type != current_type:
                    st.session_state.stage_profiles_edit[stage_num] = new_type
                    st.success(f"✅ Updated to {stage_type_options[new_type]}")
            
            with col3:
                # Show current selection
                st.markdown(f"*{stage_type_options[current_type]}*")
            
            # Add a small divider between stages
            if stage_num < 21:
                st.divider()
    
    # Stage type summary
    st.markdown("---")
    st.markdown("### Stage Type Summary")
    
    type_counts = {}
    for stage_type in stage_type_options.keys():
        type_counts[stage_type] = sum(1 for st in st.session_state.stage_profiles_edit.values() if st == stage_type)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Current Distribution:**")
        for stage_type, count in type_counts.items():
            st.write(f"• {stage_type_options[stage_type]}: {count} stages")
    
    with col2:
        # Create pie chart
        fig = go.Figure(data=[go.Pie(
            labels=[stage_type_options[st] for st in type_counts.keys()],
            values=list(type_counts.values()),
            hole=0.3
        )])
        
        fig.update_layout(
            title="Stage Type Distribution",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Controls
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Reset to Default", key="reset_stage_types"):
            st.session_state.stage_profiles_edit = STAGE_PROFILES.copy()
            st.rerun()
    
    with col2:
        if st.button("📊 Export Stage Types", key="export_stage_types"):
            # Create export data
            export_data = []
            for stage_num in range(1, 22):
                stage_type = st.session_state.stage_profiles_edit.get(stage_num, StageType.SPRINT)
                export_data.append({
                    'Stage': stage_num,
                    'Type': stage_type_options[stage_type],
                    'Type_Value': stage_type.value
                })
            
            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download Stage Types CSV",
                data=csv,
                file_name="stage_types.csv",
                mime="text/csv"
            )
    
    with col3:
        if st.button("💾 Apply Changes", key="apply_stage_changes"):
            # Update the actual stage profiles
            import stage_profiles
            stage_profiles.STAGE_PROFILES.update(st.session_state.stage_profiles_edit)
            st.success("✅ Stage types updated! Changes will apply to new simulations.")

def show_scorito_analysis_dashboard(metrics):
    """Display comprehensive Scorito points analysis"""
    st.subheader("💰 Scorito Points Analysis")
    
    scorito_data = metrics['scorito_analysis']
    
    # Generate a unique identifier for this dashboard instance
    unique_id = int(time.time() * 1000000)  # Microsecond timestamp
    
    # Create tabs for different analysis sections
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", "📈 Variance & Outliers", "🏁 Stage Analysis", "💰 Price Value", "📋 Detailed Stats"
    ])
    
    with tab1:
        show_scorito_overview(scorito_data, unique_id)
    
    with tab2:
        show_variance_outlier_analysis(scorito_data, unique_id)
    
    with tab3:
        show_stage_by_stage_analysis(scorito_data, unique_id)
    
    with tab4:
        show_price_value_analysis(scorito_data, unique_id)
    
    with tab5:
        show_detailed_scorito_stats(scorito_data)

def show_scorito_overview(scorito_data, unique_id):
    """Show overview of Scorito points analysis"""
    st.subheader("📊 Overview")
    
    summary = scorito_data['overall_summary']
    basic_stats = scorito_data['basic_stats']
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Simulations", summary['total_simulations'])
    
    with col2:
        st.metric("Total Points Scored", f"{summary['total_points_scored']:,.0f}")
    
    with col3:
        st.metric("Avg Points/Stage", f"{summary['avg_points_per_stage']:.1f}")
    
    with col4:
        st.metric("Unique Riders", summary['unique_riders'])
    
    # Top scorers chart
    st.subheader("🏆 Top Scorers")
    top_scorers = basic_stats['top_scorers']
    
    if top_scorers:
        # Create DataFrame for plotting
        df_top = pd.DataFrame(list(top_scorers.items()), columns=['Rider', 'Total Points'])
        df_top = df_top.head(15)  # Show top 15
        
        fig = px.bar(df_top, x='Total Points', y='Rider', orientation='h',
                    title="Top 15 Scorers by Total Points",
                    color='Total Points', color_continuous_scale='viridis')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True, key=f"top_scorers_chart_{unique_id}")
    
    # Points by team
    st.subheader("🏢 Points by Team")
    team_points = basic_stats['points_by_team']
    
    if team_points:
        df_team = pd.DataFrame(list(team_points.items()), columns=['Team', 'Total Points'])
        df_team = df_team.sort_values('Total Points', ascending=False)
        
        fig = px.bar(df_team, x='Team', y='Total Points',
                    title="Total Scorito Points by Team",
                    color='Total Points', color_continuous_scale='plasma')
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True, key=f"team_points_chart_{unique_id}")

def show_variance_outlier_analysis(scorito_data, unique_id):
    """Show variance and outlier analysis"""
    st.subheader("📈 Variance & Outlier Analysis")
    
    variance_data = scorito_data['variance_analysis']
    outlier_data = scorito_data['outlier_analysis']
    
    # Variance overview
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Overall Variance", f"{variance_data['overall_variance']:.2f}")
        
        st.subheader("🔍 High Variance Riders")
        high_var = variance_data['high_variance_riders']
        if high_var:
            df_high = pd.DataFrame(list(high_var.items()), columns=['Rider', 'Standard Deviation'])
            df_high = df_high.sort_values('Standard Deviation', ascending=False).head(10)
            st.dataframe(df_high, use_container_width=True)
    
    with col2:
        st.metric("Outlier Threshold", f"{outlier_data['outlier_threshold']:.1f}")
        st.metric("Outlier Percentage", f"{outlier_data['outlier_percentage']:.1f}%")
        
        st.subheader("🎯 Low Variance Riders")
        low_var = variance_data['low_variance_riders']
        if low_var:
            df_low = pd.DataFrame(list(low_var.items()), columns=['Rider', 'Standard Deviation'])
            df_low = df_low.sort_values('Standard Deviation').head(10)
            st.dataframe(df_low, use_container_width=True)
    
    # Top outliers
    st.subheader("🚀 Top Outliers")
    top_outliers = outlier_data['top_outliers']
    
    if top_outliers:
        df_outliers = pd.DataFrame(top_outliers)
        st.dataframe(df_outliers, use_container_width=True)
        
        # Outlier distribution chart
        outlier_riders = outlier_data['outlier_riders']
        if outlier_riders:
            df_outlier_counts = pd.DataFrame(list(outlier_riders.items()), 
                                           columns=['Rider', 'Outlier Count'])
            df_outlier_counts = df_outlier_counts.sort_values('Outlier Count', ascending=False).head(10)
            
            fig = px.bar(df_outlier_counts, x='Rider', y='Outlier Count',
                        title="Riders with Most Outlier Performances",
                        color='Outlier Count', color_continuous_scale='reds')
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True, key=f"outlier_riders_chart_{unique_id}")

def show_stage_by_stage_analysis(scorito_data, unique_id):
    """Show stage-by-stage analysis"""
    st.subheader("🏁 Stage-by-Stage Analysis")
    
    stage_data = scorito_data['stage_analysis']
    
    if not stage_data:
        st.info("No stage data available")
        return
    
    # Stage overview metrics
    stages = list(stage_data.keys())
    total_points = [stage_data[s]['total_points'] for s in stages]
    avg_points = [stage_data[s]['avg_points'] for s in stages]
    max_points = [stage_data[s]['max_points'] for s in stages]
    
    # Stage points chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=stages, y=total_points, mode='lines+markers', 
                            name='Total Points', line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=stages, y=avg_points, mode='lines+markers', 
                            name='Average Points', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=stages, y=max_points, mode='lines+markers', 
                            name='Max Points', line=dict(color='red')))
    
    fig.update_layout(title="Stage Points Overview", xaxis_title="Stage", yaxis_title="Points",
                     height=400)
    st.plotly_chart(fig, use_container_width=True, key=f"stage_overview_chart_{unique_id}")
    
    # Stage selector for detailed view
    selected_stage = st.selectbox("Select Stage for Detailed View:", stages, key=f"stage_selector_{unique_id}")
    
    if selected_stage:
        stage_info = stage_data[selected_stage]
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Points", f"{stage_info['total_points']:,.0f}")
        
        with col2:
            st.metric("Average Points", f"{stage_info['avg_points']:.1f}")
        
        with col3:
            st.metric("Max Points", f"{stage_info['max_points']:.1f}")
        
        with col4:
            st.metric("Standard Deviation", f"{stage_info['points_std']:.1f}")
        
        # Top scorers for this stage
        st.subheader(f"🏆 Top Scorers - Stage {selected_stage}")
        top_scorers = stage_info['top_scorers']
        
        if top_scorers:
            df_stage = pd.DataFrame(top_scorers)
            st.dataframe(df_stage, use_container_width=True)
        
        # Points distribution for this stage
        st.subheader(f"📊 Points Distribution - Stage {selected_stage}")
        distribution = stage_info['points_distribution']
        
        if distribution:
            df_dist = pd.DataFrame(list(distribution.items()), columns=['Range', 'Count'])
            fig = px.pie(df_dist, values='Count', names='Range', 
                        title=f"Points Distribution - Stage {selected_stage}")
            st.plotly_chart(fig, use_container_width=True, key=f"stage_{selected_stage}_distribution_{unique_id}")

def show_price_value_analysis(scorito_data, unique_id):
    """Show price value analysis"""
    st.subheader("💰 Price Value Analysis")
    
    price_data = scorito_data['price_value_analysis']
    top_value = scorito_data['top_value_riders']
    consistency = scorito_data['consistency_analysis']
    
    if not price_data:
        st.info("No price data available")
        return
    
    # Convert to DataFrame for easier manipulation
    df_price = pd.DataFrame.from_dict(price_data, orient='index')
    df_price['rider'] = df_price.index
    
    # Top value riders
    st.subheader("💎 Top Value Riders (Points per Euro)")
    
    if top_value:
        df_top_value = pd.DataFrame.from_dict(top_value, orient='index')
        df_top_value['rider'] = df_top_value.index
        df_top_value = df_top_value.sort_values('points_per_euro', ascending=False).head(15)
        
        fig = px.bar(df_top_value, x='rider', y='points_per_euro',
                    title="Top 15 Value Riders (Points per Euro)",
                    color='avg_total_points', color_continuous_scale='viridis',
                    hover_data=['price', 'avg_total_points', 'team'])
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True, key=f"top_value_riders_chart_{unique_id}")
    
    # Consistency analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Most Consistent Riders")
        most_consistent = consistency['most_consistent']
        if most_consistent:
            df_consistent = pd.DataFrame(most_consistent, columns=['rider', 'data'])
            df_consistent['consistency'] = df_consistent['data'].apply(lambda x: x['consistency'])
            df_consistent['avg_points'] = df_consistent['data'].apply(lambda x: x['avg_total_points'])
            df_consistent['team'] = df_consistent['data'].apply(lambda x: x['team'])
            
            st.dataframe(df_consistent[['rider', 'consistency', 'avg_points', 'team']], 
                        use_container_width=True)
    
    with col2:
        st.subheader("🎲 Least Consistent Riders")
        least_consistent = consistency['least_consistent']
        if least_consistent:
            df_inconsistent = pd.DataFrame(least_consistent, columns=['rider', 'data'])
            df_inconsistent['consistency'] = df_inconsistent['data'].apply(lambda x: x['consistency'])
            df_inconsistent['avg_points'] = df_inconsistent['data'].apply(lambda x: x['avg_total_points'])
            df_inconsistent['team'] = df_inconsistent['data'].apply(lambda x: x['team'])
            
            st.dataframe(df_inconsistent[['rider', 'consistency', 'avg_points', 'team']], 
                        use_container_width=True)
    
    # Price vs Points scatter plot
    st.subheader("📊 Price vs Average Points")
    
    fig = px.scatter(df_price, x='price', y='avg_total_points', 
                    color='team', size='points_per_euro',
                    hover_data=['rider', 'consistency'],
                    title="Price vs Average Points (Size = Points per Euro)")
    st.plotly_chart(fig, use_container_width=True, key=f"price_vs_points_scatter_{unique_id}")

def show_detailed_scorito_stats(scorito_data):
    """Show detailed Scorito statistics"""
    st.subheader("📋 Detailed Statistics")
    
    basic_stats = scorito_data['basic_stats']
    
    # Rider statistics
    st.subheader("👥 Rider Statistics")
    
    if 'total_points_by_rider' in basic_stats:
        df_riders = pd.DataFrame.from_dict(basic_stats['total_points_by_rider'], 
                                         orient='index', columns=['Total Points'])
        df_riders['rider'] = df_riders.index
        
        # Add average points
        if 'avg_points_by_rider' in basic_stats:
            df_riders['avg_points'] = df_riders['rider'].map(basic_stats['avg_points_by_rider'])
        
        # Add standard deviation
        if 'points_std_by_rider' in basic_stats:
            df_riders['std_points'] = df_riders['rider'].map(basic_stats['points_std_by_rider'])
        
        # Sort by total points
        df_riders = df_riders.sort_values('Total Points', ascending=False)
        
        st.dataframe(df_riders, use_container_width=True)
    
    # Team statistics
    st.subheader("🏢 Team Statistics")
    
    if 'points_by_team' in basic_stats:
        df_teams = pd.DataFrame.from_dict(basic_stats['points_by_team'], 
                                        orient='index', columns=['Total Points'])
        df_teams['team'] = df_teams.index
        df_teams = df_teams.sort_values('Total Points', ascending=False)
        
        st.dataframe(df_teams, use_container_width=True)

def show_versus_mode():
    st.header('🆚 Versus Mode')
    st.markdown('''
    **Versus Mode** allows you to select your own team of 20 riders (budget 48, max 4/team), run simulations, and compare your team against the optimal team.
    ''')

    versus = VersusMode()
    available_riders = versus.get_available_riders()

    # Initialize session state for selected riders
    if 'versus_selected_riders' not in st.session_state:
        st.session_state['versus_selected_riders'] = []

    # Team selection section
    st.subheader('1. Select Your Team')
    st.caption('Pick up to 20 riders. Budget: 48. Max 4 per team.')

    # Show current selection stats
    selected_df = available_riders[available_riders['name'].isin(st.session_state['versus_selected_riders'])]
    total_cost = selected_df['price'].sum()
    team_counts = selected_df['team'].value_counts().to_dict()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Selected", f"{len(st.session_state['versus_selected_riders'])}/20")
    with col2:
        st.metric("Budget Used", f"{total_cost:.1f}/48")
    with col3:
        st.metric("Remaining", f"{48 - total_cost:.1f}")
    with col4:
        st.metric("Teams", len(team_counts))

    # Show selected riders with remove option
    if st.session_state['versus_selected_riders']:
        st.subheader("Selected Riders")
        selected_display = selected_df[['name', 'team', 'age', 'price', 'sprint_ability', 'punch_ability', 'itt_ability', 'mountain_ability', 'hills_ability']].copy()
        selected_display['Remove'] = [f"❌ {name}" for name in selected_display['name']]
        
        # Create a simple display with remove buttons
        for idx, row in selected_display.iterrows():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{row['name']}** ({row['team']}) - Age: {row['age']}, Price: {row['price']:.1f}")
            with col2:
                sprint_tier = ability_to_tier(row['sprint_ability'])
                punch_tier = ability_to_tier(row['punch_ability'])
                st.write(f"Sprint: {tier_to_color(sprint_tier)} {sprint_tier}")
                st.write(f"Punch: {tier_to_color(punch_tier)} {punch_tier}")
            with col3:
                itt_tier = ability_to_tier(row['itt_ability'])
                mountain_tier = ability_to_tier(row['mountain_ability'])
                st.write(f"ITT: {tier_to_color(itt_tier)} {itt_tier}")
                st.write(f"Mountain: {tier_to_color(mountain_tier)} {mountain_tier}")
                if st.button(f"Remove {row['name']}", key=f"selected_remove_{row['name']}"):
                    st.session_state['versus_selected_riders'].remove(row['name'])
                    st.rerun()

    # Rider selection by team
    st.subheader("Available Riders by Team")
    
    # Search/filter
    search = st.text_input('🔍 Search riders (name/team):', '')
    
    # Specialty filter
    specialty_filter = st.selectbox(
        "Filter by specialty:",
        ["All", "Sprint", "Punch", "ITT", "Mountain", "Hills"]
    )
    
    # Group by team
    teams = available_riders.groupby('team')
    
    # Create tabs for each team
    team_names = sorted(teams.groups.keys())
    if len(team_names) > 10:  # If too many teams, use selectbox
        selected_team = st.selectbox("Select Team:", team_names)
        team_tabs = [selected_team]
    else:
        team_tabs = team_names
    
    for team_name in team_tabs:
        team_riders = teams.get_group(team_name)
        if search:
            team_riders = team_riders[team_riders.apply(lambda row: search.lower() in row['name'].lower() or search.lower() in row['team'].lower(), axis=1)]
        
        # Apply specialty filter
        if specialty_filter != "All":
            team_riders['max_ability'] = team_riders[['sprint_ability', 'punch_ability', 'itt_ability', 'mountain_ability', 'hills_ability']].max(axis=1)
            team_riders['specialty'] = team_riders[['sprint_ability', 'punch_ability', 'itt_ability', 'mountain_ability', 'hills_ability']].idxmax(axis=1)
            team_riders = team_riders[team_riders['specialty'] == specialty_filter.lower() + '_ability']
        
        if len(team_riders) == 0:
            continue
            
        # Count selected riders from this team
        team_selected = [r for r in st.session_state['versus_selected_riders'] if r in team_riders['name'].values]
        team_selected_count = len(team_selected)
        
        # Create expandable section for each team
        with st.expander(f"🏢 {team_name} ({team_selected_count}/4 riders selected)", expanded=team_selected_count > 0):
            if team_selected_count >= 4:
                st.warning(f"Maximum 4 riders already selected from {team_name}")
            
            # Sort riders by specialty (highest ability first)
            team_riders['max_ability'] = team_riders[['sprint_ability', 'punch_ability', 'itt_ability', 'mountain_ability', 'hills_ability']].max(axis=1)
            team_riders = team_riders.sort_values('max_ability', ascending=False)
            
            # Group riders by specialty for better organization
            team_riders['specialty'] = team_riders[['sprint_ability', 'punch_ability', 'itt_ability', 'mountain_ability', 'hills_ability']].idxmax(axis=1)
            specialty_groups = team_riders.groupby('specialty')
            
            for specialty, specialty_riders in specialty_groups:
                specialty_name = specialty.replace('_ability', '').title()
                st.markdown(f"**{specialty_name} Riders:**")
                
                # Display riders in a grid
                for idx, rider in specialty_riders.iterrows():
                    rider_name = rider['name']
                    is_selected = rider_name in st.session_state['versus_selected_riders']
                    
                    # Determine specialty
                    abilities = {
                        'Sprint': rider['sprint_ability'],
                        'Punch': rider['punch_ability'],
                        'ITT': rider['itt_ability'],
                        'Mountain': rider['mountain_ability'],
                        'Hills': rider['hills_ability']
                    }
                    specialty = max(abilities, key=abilities.get)
                    specialty_value = abilities[specialty]
                    
                    # Create a card-like display for each rider
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                        
                        with col1:
                            status = "✅" if is_selected else "⭕"
                            st.markdown(f"{status} **{rider_name}** (Age: {rider['age']})")
                            specialty_tier = ability_to_tier(specialty_value)
                            specialty_icon = tier_to_color(specialty_tier)
                            st.markdown(f"💰 **Price:** {rider['price']:.1f} | 🎯 **{specialty}:** {specialty_icon} {specialty_tier}")
                        
                        with col2:
                            sprint_tier = ability_to_tier(rider['sprint_ability'])
                            punch_tier = ability_to_tier(rider['punch_ability'])
                            st.markdown(f"**Sprint:** {tier_to_color(sprint_tier)} {sprint_tier}")
                            st.markdown(f"**Punch:** {tier_to_color(punch_tier)} {punch_tier}")
                        
                        with col3:
                            itt_tier = ability_to_tier(rider['itt_ability'])
                            mountain_tier = ability_to_tier(rider['mountain_ability'])
                            st.markdown(f"**ITT:** {tier_to_color(itt_tier)} {itt_tier}")
                            st.markdown(f"**Mountain:** {tier_to_color(mountain_tier)} {mountain_tier}")
                        
                        with col4:
                            if is_selected:
                                if st.button(f"❌ Remove", key=f"team_remove_{team_name}_{rider_name}", help="Remove from team"):
                                    st.session_state['versus_selected_riders'].remove(rider_name)
                                    st.rerun()
                            else:
                                # Check if we can add this rider
                                can_add = (len(st.session_state['versus_selected_riders']) < 20 and 
                                         total_cost + rider['price'] <= 48 and 
                                         team_selected_count < 4)
                                
                                if can_add:
                                    if st.button(f"➕ Add", key=f"team_add_{team_name}_{rider_name}", help="Add to team"):
                                        st.session_state['versus_selected_riders'].append(rider_name)
                                        st.rerun()
                                else:
                                    reason = ""
                                    if len(st.session_state['versus_selected_riders']) >= 20:
                                        reason = "Team full"
                                    elif total_cost + rider['price'] > 48:
                                        reason = "Budget exceeded"
                                    elif team_selected_count >= 4:
                                        reason = "Team limit reached"
                                    
                                    st.button(f"➕ Add", key=f"team_add_{team_name}_{rider_name}", disabled=True, help=f"Cannot add: {reason}")
                        
                        # Add a subtle divider between riders
                        st.markdown("---")

    # Validation
    is_valid, error_message = versus.validate_team_selection(st.session_state['versus_selected_riders'])
    if is_valid:
        st.success('✅ Team selection is valid!')
    else:
        st.warning(f'⚠️ {error_message}')

    # Step 2: Run simulation and show results
    if is_valid:
        if 'versus_results' not in st.session_state:
            st.session_state['versus_results'] = None
        run_sim = st.button('Run Versus Simulation', type='primary')
        if run_sim:
            with st.spinner('Running simulations and optimizing... (this may take a minute)'):
                # Run the full versus mode pipeline
                user_team = versus.create_user_team(st.session_state['versus_selected_riders'])
                rider_data = versus.team_optimizer.run_simulation(num_simulations=30)
                user_team = versus.optimize_stage_selection(user_team, rider_data, num_simulations=30)
                simulation_results = versus.run_user_team_simulations(user_team, num_simulations=50)
                optimal_team = versus.get_optimal_team(num_simulations=30)
                comparison = versus.compare_teams(user_team, optimal_team)
                st.session_state['versus_results'] = {
                    'user_team': user_team,
                    'optimal_team': optimal_team,
                    'comparison': comparison,
                    'rider_data': rider_data
                }
                st.success('Simulation complete! See results below.')
        # Show results if available
        if st.session_state['versus_results']:
            comparison = st.session_state['versus_results']['comparison']
            user_team = st.session_state['versus_results']['user_team']
            optimal_team = st.session_state['versus_results']['optimal_team']
            rider_data = st.session_state['versus_results']['rider_data']
            
            st.subheader('2. Results Summary')
            col1, col2 = st.columns(2)
            with col1:
                st.markdown('**Your Team**')
                st.write(f"Cost: {comparison['user_team']['total_cost']:.2f}")
                st.write(f"Average Points: {comparison['user_team']['avg_simulation_points']:.2f} ± {comparison['user_team']['simulation_std']:.2f}")
                st.write(f"Riders: {', '.join(comparison['user_team']['riders'])}")
            with col2:
                st.markdown('**Optimal Team**')
                st.write(f"Cost: {comparison['optimal_team']['total_cost']:.2f}")
                st.write(f"Expected Points: {comparison['optimal_team']['expected_points']:.2f}")
                st.write(f"Riders: {', '.join(comparison['optimal_team']['riders'])}")
            st.markdown('---')
            st.write(f"**Cost Difference:** {comparison['comparison']['cost_difference']:.2f}")
            st.write(f"**Performance Difference:** {comparison['comparison']['performance_difference']:.2f}")
            st.write(f"**Common Riders:** {len(comparison['comparison']['common_riders'])}")
            st.write(f"**Your Unique Riders:** {len(comparison['comparison']['user_only_riders'])}")
            st.write(f"**Optimal Unique Riders:** {len(comparison['comparison']['optimal_only_riders'])}")
            if comparison['comparison']['common_riders']:
                st.write(f"Common Riders: {', '.join(comparison['comparison']['common_riders'])}")
            if comparison['comparison']['user_only_riders']:
                st.write(f"Your Unique Riders: {', '.join(comparison['comparison']['user_only_riders'])}")
            if comparison['comparison']['optimal_only_riders']:
                st.write(f"Optimal Unique Riders: {', '.join(comparison['comparison']['optimal_only_riders'])}")
            
            # Stage-by-stage comparison
            if user_team.stage_selections and optimal_team.stage_selections:
                st.subheader('3. Stage-by-Stage Comparison')
                stages = list(range(1, 23))
                stage_comparison_data = []
                for stage in stages:
                    user_stage_points = sum(user_team.stage_points.get(stage, {}).values())
                    optimal_stage_points = sum(optimal_team.stage_points.get(stage, {}).values())
                    stage_comparison_data.append({
                        'Stage': stage,
                        'User_Team_Points': user_stage_points,
                        'Optimal_Team_Points': optimal_stage_points,
                        'Difference': user_stage_points - optimal_stage_points
                    })
                
                stage_df = pd.DataFrame(stage_comparison_data)
                
                # Stage comparison chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=stage_df['Stage'], y=stage_df['User_Team_Points'], 
                                       mode='lines+markers', name='Your Team', line=dict(color='blue')))
                fig.add_trace(go.Scatter(x=stage_df['Stage'], y=stage_df['Optimal_Team_Points'], 
                                       mode='lines+markers', name='Optimal Team', line=dict(color='red')))
                fig.update_layout(title='Stage-by-Stage Points Comparison', 
                                xaxis_title='Stage', yaxis_title='Points',
                                height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Stage difference chart
                fig2 = go.Figure()
                colors = ['green' if x >= 0 else 'red' for x in stage_df['Difference']]
                fig2.add_trace(go.Bar(x=stage_df['Stage'], y=stage_df['Difference'], 
                                    marker_color=colors, name='Difference'))
                fig2.update_layout(title='Stage-by-Stage Difference (Your Team - Optimal Team)', 
                                 xaxis_title='Stage', yaxis_title='Points Difference',
                                 height=400)
                st.plotly_chart(fig2, use_container_width=True)
                
                # Stage comparison table
                st.dataframe(stage_df, use_container_width=True)
            
            # Rider-by-rider comparison
            st.subheader('4. Rider-by-Rider Comparison')
            all_riders = set(user_team.rider_names + optimal_team.rider_names)
            rider_comparison_data = []
            
            for rider_name in sorted(all_riders):
                in_user = rider_name in user_team.rider_names
                in_optimal = rider_name in optimal_team.rider_names
                
                # Get rider info
                rider_info = rider_data[rider_data['rider_name'] == rider_name]
                if not rider_info.empty:
                    rider_row = rider_info.iloc[0]
                    rider_comparison_data.append({
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
            
            rider_comp_df = pd.DataFrame(rider_comparison_data)
            st.dataframe(rider_comp_df, use_container_width=True)
            
            # Download Excel report
            st.subheader('5. Download Results')
            if st.button('Download Excel Report'):
                try:
                    filename = versus.save_versus_results(user_team, optimal_team, comparison, rider_data)
                    with open(filename, 'rb') as f:
                        excel_data = f.read()
                    
                    st.download_button(
                        label='Click to download Excel file',
                        data=excel_data,
                        file_name=filename,
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                    st.success(f'Excel report saved as {filename}')
                except Exception as e:
                    st.error(f'Error generating Excel report: {e}')
    else:
        st.button('Run Versus Simulation', disabled=True)

def ability_to_tier(ability: int) -> str:
    """Convert ability score to tier name"""
    if ability >= 98:
        return "Exceptional"
    elif ability >= 95:
        return "World Class"
    elif ability >= 90:
        return "Elite"
    elif ability >= 80:
        return "Very Good"
    elif ability >= 70:
        return "Good"
    elif ability >= 50:
        return "Average"
    else:
        return "Below Average"

def tier_to_color(tier: str) -> str:
    """Get color for tier display"""
    colors = {
        "Exceptional": "💎",
        "World Class": "🟢", 
        "Elite": "🟢",
        "Very Good": "🟢",
        "Good": "🟡",
        "Average": "🟠",
        "Below Average": "🔴"
    }
    return colors.get(tier, "⚪")

if __name__ == "__main__":
    main() 