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

# Import our custom modules
from simulator import TourSimulator
from team_optimization import TeamOptimizer
from riders import RiderDatabase, Rider
from rider_parameters import RiderParameters

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
    
    /* Additional styling for better visibility */
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
    
    # Header
    st.title("🚴 Tour de France Cycling Simulator")
    st.markdown("---")
    
    # Navigation
    page = st.sidebar.selectbox(
        "Choose a page",
        ["📊 Overview", "🎯 Single Simulation", "📊 Multi Simulation", "⚡ Team Optimization", "👥 Rider Management", "📈 Results Analysis"]
    )
    
    # Page routing
    if page == "📊 Overview":
        show_overview()
    elif page == "🎯 Single Simulation":
        show_single_simulation()
    elif page == "📊 Multi Simulation":
        show_multi_simulation()
    elif page == "⚡ Team Optimization":
        show_team_optimization()
    elif page == "👥 Rider Management":
        show_rider_management()
    elif page == "📈 Results Analysis":
        show_results_analysis()

def show_overview():
    st.header("📊 Dashboard Overview")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>🎯 Single Simulation</h3>
            <p>Run a single Tour de France simulation and view detailed results for each stage.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>📊 Multi Simulation</h3>
            <p>Run multiple simulations to get statistical insights and average performance.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>⚡ Team Optimization</h3>
            <p>Optimize team selection using advanced algorithms and constraints.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Quick stats
    st.subheader("📈 Quick Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_riders = len(st.session_state.rider_db.get_all_riders())
        st.metric("Total Riders", total_riders)
    
    with col2:
        teams = len(set(rider.team for rider in st.session_state.rider_db.get_all_riders()))
        st.metric("Teams", teams)
    
    with col3:
        youth_riders = len([r for r in st.session_state.rider_db.get_all_riders() if r.age < 25])
        st.metric("Youth Riders", youth_riders)
    
    with col4:
        avg_age = np.mean([rider.age for rider in st.session_state.rider_db.get_all_riders()])
        st.metric("Average Age", f"{avg_age:.1f}")
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    
    if st.session_state.simulation_results is not None:
        st.success("✅ Single simulation completed")
    if st.session_state.multi_simulation_results is not None:
        st.success("✅ Multi-simulation completed")
    if st.session_state.optimization_results is not None:
        st.success("✅ Team optimization completed")

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
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Simulation Parameters")
        
        num_simulations = st.slider("Number of simulations", 10, 500, 100, 10, key="multi_sim_count")
        show_progress = st.checkbox("Show progress", value=True, key="multi_sim_progress")
        
        if st.button("🔄 Run Multi-Simulation", type="primary", key="run_multi_sim"):
            with st.spinner(f"Running {num_simulations} simulations..."):
                if show_progress:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                # Run multi-simulation using the session state rider database
                results = run_multi_simulation(num_simulations, progress_callback=progress_bar if show_progress else None)
                
                if show_progress:
                    progress_bar.progress(1.0)
                    status_text.text("Multi-simulation completed!")
                
                st.session_state.multi_simulation_results = results
                st.success(f"✅ {num_simulations} simulations completed!")
    
    with col2:
        st.subheader("Results")
        
        if st.session_state.multi_simulation_results is not None:
            st.success("Multi-simulation results available")
            
            if st.button("📊 View Analysis", key="view_multi_analysis"):
                show_multi_simulation_analysis(st.session_state.multi_simulation_results)
        else:
            st.info("Run a multi-simulation to see results")

def show_team_optimization():
    st.header("⚡ Team Optimization")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Optimization Parameters")
        
        budget = st.slider("Budget", 30.0, 60.0, 48.0, 0.5, key="opt_budget")
        team_size = st.slider("Team size", 15, 25, 20, 1, key="opt_team_size")
        num_simulations = st.slider("Simulations for expected points", 50, 200, 100, 10, key="opt_sim_count")
        risk_aversion = st.slider("Risk aversion", 0.0, 1.0, 0.0, 0.1, key="opt_risk_aversion")
        abandon_penalty = st.slider("Abandon penalty", 0.0, 1.0, 1.0, 0.1, key="opt_abandon_penalty")
        
        if st.button("🎯 Optimize Team", type="primary", key="run_optimization"):
            with st.spinner("Running optimization..."):
                optimizer = TeamOptimizer(budget=budget, team_size=team_size)
                # Replace the optimizer's rider database with our modified one
                optimizer.rider_db = st.session_state.rider_db
                inject_rider_database(optimizer.simulator, st.session_state.rider_db)
                
                # Get expected points using our custom method
                rider_data = run_optimizer_simulation(optimizer, num_simulations, st.session_state.rider_db)
                
                # Optimize team
                team_selection = optimizer.optimize_team(
                    rider_data, 
                    risk_aversion=risk_aversion,
                    abandon_penalty=abandon_penalty
                )
                
                st.session_state.optimization_results = {
                    'team_selection': team_selection,
                    'rider_data': rider_data,
                    'optimizer': optimizer
                }
                
                st.success("✅ Team optimization completed!")
    
    with col2:
        st.subheader("Results")
        
        if st.session_state.optimization_results is not None:
            team_selection = st.session_state.optimization_results['team_selection']
            
            st.metric("Total Cost", f"{team_selection.total_cost:.2f}")
            st.metric("Expected Points", f"{team_selection.expected_points:.1f}")
            st.metric("Team Size", len(team_selection.riders))
            
            if st.button("📋 View Team", key="view_optimization_team"):
                show_optimization_results(st.session_state.optimization_results)
        else:
            st.info("Run optimization to see results")

def show_rider_management():
    st.header("👥 Rider Management")
    
    tab1, tab2, tab3 = st.tabs(["📋 View Riders", "✏️ Edit Rider", "➕ Add Rider"])
    
    with tab1:
        st.subheader("Current Riders")
        
        # Get all riders
        riders = st.session_state.rider_db.get_all_riders()
        
        # Create DataFrame
        rider_data = []
        for rider in riders:
            rider_data.append({
                'Name': rider.name,
                'Team': rider.team,
                'Price': rider.price,
                'Sprint': rider.parameters.sprint_ability,
                'ITT': rider.parameters.itt_ability,
                'Mountain': rider.parameters.mountain_ability,
                'Hills': rider.parameters.hills_ability,
                'Punch': rider.parameters.punch_ability,
                'Abandon Chance': f"{rider.chance_of_abandon:.2%}"
            })
        
        df = pd.DataFrame(rider_data)
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            team_filter = st.selectbox("Filter by team", ["All"] + sorted(df['Team'].unique()), key="view_team_filter")
        with col2:
            price_filter = st.slider("Price range", float(df['Price'].min()), float(df['Price'].max()), (0.0, 10.0), key="view_price_filter")
        with col3:
            ability_filter = st.selectbox("Filter by ability", ["All", "Sprint", "ITT", "Mountain", "Hills", "Punch"], key="view_ability_filter")
        
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
            filtered_df = filtered_df[filtered_df[ability_col] > 0]  # Show riders with some ability in that category
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Export riders
        if st.button("📥 Export Riders", key="export_riders"):
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="riders_export.csv",
                mime="text/csv"
            )
    
    with tab2:
        st.subheader("Edit Rider Parameters")
        
        # Select rider
        rider_names = [rider.name for rider in riders]
        selected_rider = st.selectbox("Select rider to edit", rider_names, key="edit_rider_select")
        
        if selected_rider:
            rider = st.session_state.rider_db.get_rider(selected_rider)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Name:** {rider.name}")
                st.write(f"**Team:** {rider.team}")
                
                new_price = st.number_input("Price", value=float(rider.price), step=0.1, key="edit_price")
                new_abandon = st.slider("Abandon chance", 0.0, 1.0, float(rider.chance_of_abandon), 0.01, key="edit_abandon")
            
            with col2:
                st.write("**Current Abilities:**")
                st.write(f"Sprint: {rider.parameters.sprint_ability}")
                st.write(f"ITT: {rider.parameters.itt_ability}")
                st.write(f"Mountain: {rider.parameters.mountain_ability}")
                st.write(f"Hills: {rider.parameters.hills_ability}")
                st.write(f"Punch: {rider.parameters.punch_ability}")
                
                # Ability sliders
                st.write("**New Abilities:**")
                new_sprint = st.slider("Sprint", 0, 100, rider.parameters.sprint_ability, key="edit_sprint")
                new_itt = st.slider("ITT", 0, 100, rider.parameters.itt_ability, key="edit_itt")
                new_mountain = st.slider("Mountain", 0, 100, rider.parameters.mountain_ability, key="edit_mountain")
                new_hills = st.slider("Hills", 0, 100, rider.parameters.hills_ability, key="edit_hills")
                new_punch = st.slider("Punch", 0, 100, rider.parameters.punch_ability, key="edit_punch")
            
            if st.button("💾 Save Changes", key="save_rider_changes"):
                # Update rider parameters
                rider.price = new_price
                rider.chance_of_abandon = new_abandon
                rider.parameters.sprint_ability = new_sprint
                rider.parameters.itt_ability = new_itt
                rider.parameters.mountain_ability = new_mountain
                rider.parameters.hills_ability = new_hills
                rider.parameters.punch_ability = new_punch
                
                st.success("✅ Rider parameters updated!")
    
    with tab3:
        st.subheader("Add New Rider")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Rider name", key="add_name")
            new_team = st.text_input("Team", key="add_team")
            new_age = st.number_input("Age", min_value=18, max_value=50, value=25, key="add_age")
            new_price = st.number_input("Price", min_value=0.0, value=1.0, step=0.1, key="add_price")
            new_abandon = st.slider("Abandon chance", 0.0, 1.0, 0.0, 0.01, key="add_abandon")
        
        with col2:
            st.write("**Abilities:**")
            new_sprint = st.slider("Sprint ability", 0, 100, 50, key="add_sprint")
            new_itt = st.slider("ITT ability", 0, 100, 50, key="add_itt")
            new_mountain = st.slider("Mountain ability", 0, 100, 50, key="add_mountain")
            new_hills = st.slider("Hills ability", 0, 100, 50, key="add_hills")
            new_punch = st.slider("Punch ability", 0, 100, 50, key="add_punch")
        
        if st.button("➕ Add Rider", key="add_rider_button"):
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
    st.subheader("📈 Multi-Simulation Analysis")
    
    # This would show statistical analysis of multiple simulation runs
    st.write("Multi-simulation analysis would be displayed here")
    st.write("Features: confidence intervals, probability distributions, etc.")

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

def run_multi_simulation(num_simulations, progress_callback=None):
    """Run multiple simulations with progress tracking using the session state rider database"""
    results = []
    
    for i in range(num_simulations):
        if progress_callback:
            progress_callback.progress((i + 1) / num_simulations)
        
        simulator = TourSimulator()
        inject_rider_database(simulator, st.session_state.rider_db)
        
        simulator.simulate_tour()
        results.append(simulator)
    
    return results

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

if __name__ == "__main__":
    main() 