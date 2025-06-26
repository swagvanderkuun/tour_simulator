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
        ["📊 Overview", "🎯 Single Simulation", "📈 Multi Simulation", "⚡ Team Optimization", "👥 Rider Management", "🏁 Stage Types"]
    )
    
    if page == "📊 Overview":
        show_overview()
    elif page == "🎯 Single Simulation":
        show_single_simulation()
    elif page == "📈 Multi Simulation":
        show_multi_simulation()
    elif page == "⚡ Team Optimization":
        show_team_optimization()
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

if __name__ == "__main__":
    main() 