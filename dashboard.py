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
from team_optimization import TeamOptimizer, TeamSelection
from riders import RiderDatabase, Rider
from rider_parameters import RiderParameters, get_tier_parameters, update_tier_parameters
from multi_simulator import MultiSimulationAnalyzer
from versus_mode import VersusMode
from stage_profiles import StageType, STAGE_PROFILES, validate_stage_profile, update_stage_profile

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
            "break_away_ability": rider.parameters.break_away_ability,
            "is_youth": rider.name in simulator.youth_rider_names,
            "price": rider.price,
            "chance_of_abandon": rider.chance_of_abandon
        })

def inject_stage_profiles(simulator):
    """Helper function to inject current stage profiles into a simulator"""
    # Import the stage profiles module
    import stage_profiles
    
    # Get current stage profiles from session state (if available) or use defaults
    if 'stage_profiles_edit' in st.session_state:
        # Update the actual STAGE_PROFILES with current dashboard settings
        stage_profiles.STAGE_PROFILES.update(st.session_state.stage_profiles_edit)
    
    # The simulator will now use the updated stage profiles since it imports from stage_profiles

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
        st.session_state.rider_db = RiderDatabase()
    if 'simulation_results' not in st.session_state:
        st.session_state.simulation_results = None
    if 'multi_simulation_results' not in st.session_state:
        st.session_state.multi_simulation_results = None
    if 'optimization_results' not in st.session_state:
        st.session_state.optimization_results = None
    if 'versus_selected_riders' not in st.session_state:
        st.session_state['versus_selected_riders'] = []
    
    # Sidebar navigation
    st.sidebar.title("🚴‍♂️ Tour de France Simulator")
    
    page = st.sidebar.selectbox(
        "Navigation",
        ["📊 Overview", "🎯 Single Simulation", "🔍 Exploration", "⚡ Team Optimization", "🆚 Versus Mode", "👥 Rider Management", "🏁 Stage Types"]
    )
    
    # Team overview in sidebar (fixed position, not affected by scrolling)
    if page == "🆚 Versus Mode" and 'versus_selected_riders' in st.session_state:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 Team Overview")
        
        # Calculate team statistics
        selected_count = len(st.session_state['versus_selected_riders'])
        if selected_count > 0:
            # Get rider database for calculations
            rider_db = st.session_state.rider_db
            selected_riders = [rider_db.get_rider(name) for name in st.session_state['versus_selected_riders'] if rider_db.get_rider(name)]
            total_cost = sum(rider.price for rider in selected_riders)
            budget_remaining = 48.0 - total_cost
            team_counts = {}
            for rider in selected_riders:
                if rider.team not in team_counts:
                    team_counts[rider.team] = 0
                team_counts[rider.team] += 1
            num_teams = len(team_counts)
            
            # Display team statistics in a compact format
            st.sidebar.markdown(f"""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 12px; border-radius: 8px; color: white; margin-bottom: 10px;">
                <div style="font-size: 13px; font-weight: bold; margin-bottom: 6px;">Team Status</div>
                <div style="font-size: 11px; margin-bottom: 3px;">👥 Riders: {selected_count}/20</div>
                <div style="font-size: 11px; margin-bottom: 3px;">💰 Budget: {total_cost:.1f}/48.0</div>
                <div style="font-size: 11px; margin-bottom: 3px;">💵 Remaining: {budget_remaining:.1f}</div>
                <div style="font-size: 11px;">🏢 Teams: {num_teams}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bars for visual feedback
            rider_progress = selected_count / 20
            budget_progress = total_cost / 48.0
            
            st.sidebar.write("**Rider Progress:**")
            st.sidebar.progress(rider_progress)
            st.sidebar.write("**Budget Usage:**")
            st.sidebar.progress(budget_progress)
        else:
            st.sidebar.info("No riders selected yet.")
        
        # Team action buttons
        st.sidebar.markdown("---")
        st.sidebar.subheader("⚡ Team Actions")
        
        # Generate optimized team button
        if st.sidebar.button('🔥 Generate Optimized Team', type='primary', help='Create an optimized team using 10 simulations'):
            with st.spinner('🔥 Creating spicy optimized team with 10 simulations...'):
                try:
                    # Temporarily suppress logging output
                    import logging
                    logging.getLogger('team_optimization').setLevel(logging.WARNING)
                    
                    # Create optimizer with current rider database
                    optimizer = TeamOptimizer(budget=48.0, team_size=20)
                    optimizer.rider_db = st.session_state.rider_db
                    inject_rider_database(optimizer.simulator, st.session_state.rider_db)
                    
                    # Run quick simulation to get rider data
                    rider_data = optimizer.run_simulation_with_teammate_analysis(10, metric='mean')
                    
                    # Optimize team
                    optimal_team = optimizer.optimize_team(rider_data, risk_aversion=0.0, abandon_penalty=1.0)
                    
                    # Set the optimized team as selection
                    st.session_state['versus_selected_riders'] = optimal_team.rider_names
                    
                    st.success(f'🎯 Generated optimized team with {len(optimal_team.rider_names)} riders!')
                    st.rerun()
                    
                except Exception as e:
                    st.error(f'Could not generate team: {str(e)}')
        
        # Clear team button
        if st.sidebar.button('🗑️ Clear Team', help='Remove all selected riders'):
            st.session_state['versus_selected_riders'] = []
            st.rerun()
    
    # Page routing
    if page == "📊 Overview":
        show_overview()
    elif page == "🎯 Single Simulation":
        show_single_simulation()
    elif page == "🔍 Exploration":
        show_exploration()
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
        **📋 6-Step Process:**
        
        1. **👥 Rider Management** - Adjust rider abilities based on recent form
        2. **🏁 Stage Types** - Configure the 21 Tour stages (optional)
        3. **🎯 Single Simulation** - Test your settings with one quick simulation  
        4. **🔍 Exploration** - Run 100+ simulations for reliable predictions
        5. **⚡ Team Optimization** - Let AI find your perfect team
        6. **🆚 Versus Mode** - Compare your team against the optimal team
        """)
    
    with col2:
        st.markdown("""
        **💡 Pro Tips:**
        
        • **Tier Maker Magic**: Use the visual tier system to adjust rider abilities
        • **Mixed Stage Types**: Create stages with multiple characteristics (e.g., 60% punch + 40% sprint)
        • **Export Everything**: Download results for external analysis
        • **Test Scenarios**: Run different rider configurations to find hidden gems
        • **Versus Mode**: Challenge yourself by selecting your own team and comparing it to the AI's choice
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
        "🏁 **Advanced Stage Types**: Mixed stage configurations with weighted characteristics",
        "🆚 **Versus Mode**: Compare your team selection against AI-optimized teams",
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
        **🔍 Exploration**
        
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
        
        Configure the 21 Tour de France stages with advanced mixed-type capabilities.
        
        **Key Features:**
        • Mixed stage types (e.g., 60% punch + 40% sprint)
        • Visual stage type grid
        • Performance impact analysis
        • Export configurations
        • Reset to defaults
        """)
    
    with col3:
        st.markdown("""
        **🆚 Versus Mode**
        
        Select your own team and compare it against the AI-optimized team.
        
        **Key Features:**
        • Interactive team selection
        • Stage-by-stage optimization
        • Performance comparison
        • Detailed Excel reports
        • Multiple simulation runs
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
                rider.parameters.punch_ability,
                rider.parameters.itt_ability,
                rider.parameters.mountain_ability,
                rider.parameters.break_away_ability
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
            st.caption("Exploration data available")
        else:
            st.metric("Optimization Ready", "⏳")
            st.caption("Run exploration first")
    
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
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.session_state.simulation_results is not None:
            st.success("✅ Single Simulation Complete")
            st.caption("Test run successful")
        else:
            st.info("⏳ No Test Simulation")
            st.caption("Run a quick test first")
    
    with col2:
        if st.session_state.multi_simulation_results is not None:
            st.success("✅ Exploration Complete")
            st.caption("Ready for optimization")
        else:
            st.info("⏳ No Exploration")
            st.caption("Generate predictions")
    
    with col3:
        if st.session_state.optimization_results is not None:
            st.success("✅ Team Optimization Complete")
            st.caption("Optimal team found!")
        else:
            st.info("⏳ No Optimization")
            st.caption("Find your perfect team")
    
    with col4:
        if 'versus_results' in st.session_state and st.session_state.versus_results is not None:
            st.success("✅ Versus Mode Complete")
            st.caption("Team comparison ready")
        else:
            st.info("⏳ No Versus Mode")
            st.caption("Compare your team")
    
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
        
        **Mixed Stage Types**: Weighted stage characteristics for realistic racing
        """)
    
    with col2:
        st.markdown("""
        **📊 Data Flow:**
        
        1. **Rider Database** → **Stage Simulation** → **Results**
        2. **Multiple Simulations** → **Expected Points** → **Optimization**
        3. **Constraints Applied** → **Optimal Team** → **Export**
        4. **Versus Mode** → **Team Comparison** → **Performance Analysis**
        
        **🎮 Interactive Features:**
        • Real-time tier adjustments
        • Visual stage type management
        • Interactive team selection
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

def show_exploration():
    st.header("🔍 Exploration Analysis")
    
    st.subheader("Simulation Parameters")
    
    num_simulations = st.slider("Number of simulations", 10, 500, 100, 10, key="multi_sim_count")
    show_progress = st.checkbox("Show progress", value=True, key="multi_sim_progress")
    
    if st.button("🔄 Run Exploration", type="primary", key="run_multi_sim"):
        with st.spinner(f"Running {num_simulations} simulations..."):
            if show_progress:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
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
    
    # Show results if available
    if 'multi_sim_results' in st.session_state:
        show_exploration_analysis(st.session_state.multi_sim_results)

def show_exploration_analysis(metrics):
    """Display comprehensive exploration analysis"""
    st.subheader("📊 Exploration Results")
    
    # Get the scorito analysis data
    scorito_data = metrics['scorito_analysis']
    basic_stats = scorito_data['basic_stats']
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🏆 Overall Rankings", "🏁 Stage-by-Stage Rankings"])
    
    with tab1:
        show_overall_rankings(basic_stats)
    
    with tab2:
        show_stage_rankings(scorito_data)

def show_overall_rankings(basic_stats):
    """Show top 50 riders by overall expected points"""
    st.subheader("🏆 Top 50 Riders - Expected Scorito Points (Entire Tour)")
    
    # Get rider data
    total_points_by_rider = basic_stats['total_points_by_rider']
    avg_points_by_rider = basic_stats['avg_points_by_rider']
    points_std_by_rider = basic_stats['points_std_by_rider']
    
    # Create comprehensive rider data
    rider_data = []
    for rider_name in total_points_by_rider.keys():
        # Get rider info from database
        rider = st.session_state.rider_db.get_rider(rider_name)
        if rider:
            rider_data.append({
                'Rider': rider_name,
                'Team': rider.team,
                'Price': rider.price,
                'Expected Points (Tour)': total_points_by_rider.get(rider_name, 0),
                'Avg Points (Tour)': avg_points_by_rider.get(rider_name, 0),
                'Standard Deviation': points_std_by_rider.get(rider_name, 0),
                'Points per Euro': total_points_by_rider.get(rider_name, 0) / rider.price if rider.price > 0 else 0
            })
    
    # Create DataFrame
    df = pd.DataFrame(rider_data)
    
    # Create two different rankings
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 By Expected Points")
        df_total = df.sort_values('Expected Points (Tour)', ascending=False).head(50)
        st.dataframe(df_total[['Rider', 'Team', 'Expected Points (Tour)', 'Points per Euro']], 
                    use_container_width=True)
    
    with col2:
        st.subheader("📊 By Average")
        df_avg = df.sort_values('Avg Points (Tour)', ascending=False).head(50)
        st.dataframe(df_avg[['Rider', 'Team', 'Avg Points (Tour)', 'Standard Deviation']], 
                    use_container_width=True)
    
    # Value-based ranking
    st.subheader("💰 By Value (Points per Euro)")
    df_value = df.sort_values('Points per Euro', ascending=False).head(50)
    st.dataframe(df_value[['Rider', 'Team', 'Points per Euro', 'Expected Points (Tour)', 'Price']], 
                use_container_width=True)
    
    # Detailed table with all metrics
    st.subheader("📋 Complete Rankings (Top 50)")
    df_complete = df.sort_values('Expected Points (Tour)', ascending=False).head(50)
    st.dataframe(df_complete, use_container_width=True)

def show_stage_rankings(scorito_data):
    """Show top riders for each stage"""
    st.subheader("🏁 Stage-by-Stage Rankings")
    
    stage_data = scorito_data['stage_analysis']
    
    if not stage_data:
        st.info("No stage data available")
        return
    
    # Stage selector
    selected_stage = st.selectbox("Select Stage:", sorted(stage_data.keys()), key="exploration_stage_selector_unique")
    
    if selected_stage:
        stage_info = stage_data[selected_stage]
        
        st.subheader(f"Stage {selected_stage} Rankings - Expected Scorito Points")
        
        # Stage statistics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Expected Points (Stage)", f"{stage_info['total_points']:,.0f}")
        with col2:
            st.metric("Average Points (Stage)", f"{stage_info['avg_points']:.1f}")
        
        # Get rider statistics for this stage
        rider_stats = stage_info.get('rider_stats', [])
        
        if rider_stats:
            # Create comprehensive stage data
            stage_rider_data = []
            for stat in rider_stats:
                rider_name = stat['rider']
                rider = st.session_state.rider_db.get_rider(rider_name)
                if rider:
                    stage_rider_data.append({
                        'Rider': rider_name,
                        'Team': rider.team,
                        'Price': rider.price,
                        'Expected Points (Stage)': stat['mean'],
                        'Standard Deviation': stat['std'],
                        'Simulations': stat['count'],
                        'Points per Euro': stat['mean'] / rider.price if rider.price > 0 else 0
                    })
            
            df_stage = pd.DataFrame(stage_rider_data)
            
            # Create two different rankings for this stage
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"📈 By Expected Points - Stage {selected_stage}")
                df_total = df_stage.sort_values('Expected Points (Stage)', ascending=False).head(50)
                st.dataframe(df_total[['Rider', 'Team', 'Expected Points (Stage)', 'Points per Euro']], 
                            use_container_width=True)
            
            with col2:
                st.subheader(f"📊 By Standard Deviation - Stage {selected_stage}")
                df_std = df_stage.sort_values('Standard Deviation', ascending=False).head(50)
                st.dataframe(df_std[['Rider', 'Team', 'Standard Deviation', 'Expected Points (Stage)']], 
                            use_container_width=True)
            
            # Value-based ranking for this stage
            st.subheader(f"💰 By Value (Points per Euro) - Stage {selected_stage}")
            df_value = df_stage.sort_values('Points per Euro', ascending=False).head(50)
            st.dataframe(df_value[['Rider', 'Team', 'Points per Euro', 'Expected Points (Stage)', 'Price']], 
                        use_container_width=True)
        else:
            st.info("No rider statistics available for this stage")

def show_team_optimization():
    st.header("⚡ Team Optimization")
    
    st.subheader("Optimization Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        budget = st.slider("Budget", 30.0, 60.0, 48.0, 0.5, key="opt_budget")
        team_size = st.slider("Team size", 15, 25, 20, 1, key="opt_team_size")
        num_simulations = st.slider("Simulations for expected points", 50, 200, 100, 10, key="opt_sim_count")
    
    with col2:
        risk_aversion = st.slider("Risk aversion", 0.0, 1.0, 0.0, 0.1, key="opt_risk_aversion")
        abandon_penalty = st.slider("Abandon penalty", 0.0, 1.0, 1.0, 0.1, key="opt_abandon_penalty")
        
        # Add metric selector
        metric_options = {
            'mean': 'Average (Mean)',
            'median': 'Median',
            'mode': 'Mode (Most Frequent)'
        }
        selected_metric = st.selectbox(
            "Expected Points Metric",
            options=list(metric_options.keys()),
            format_func=lambda x: metric_options[x],
            index=0,
            key="opt_metric"
        )
    
    # Parameter explanations
    st.subheader("Parameter Explanations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info("**🎯 Risk Aversion (0.0 - 1.0):**\n\n"
                "• **0.0**: No penalty for high variance riders\n"
                "• **0.5**: Moderate penalty for inconsistent performers\n"
                "• **1.0**: Heavy penalty for riders with high point variability\n\n"
                "Higher values favor consistent, predictable riders over high-risk, high-reward options.")
    
    with col2:
        st.info("**⚠️ Abandon Penalty (0.0 - 1.0):**\n\n"
                "• **0.0**: No penalty for high abandon probability\n"
                "• **0.5**: Moderate penalty for riders likely to abandon\n"
                "• **1.0**: Heavy penalty for riders with high crash/abandon risk\n\n"
                "Higher values favor riders with low abandon probability.")
    
    # Show explanation of the selected metric
    metric_explanations = {
        'mean': "Average of all simulation results. Good for normally distributed data.",
        'median': "Middle value when results are sorted. Less sensitive to outliers than mean.",
        'mode': "Most frequently occurring result. Good for discrete or skewed distributions."
    }
    st.info(f"**📈 Expected Points Metric - {metric_options[selected_metric]}**: {metric_explanations[selected_metric]}")
    
    if st.button("🎯 Optimize Team", type="primary", key="run_optimization"):
        with st.spinner("Running optimization..."):
            optimizer = TeamOptimizer(budget=budget, team_size=team_size)
            # Replace the optimizer's rider database with our modified one
            optimizer.rider_db = st.session_state.rider_db
            inject_rider_database(optimizer.simulator, st.session_state.rider_db)
            
            # Get expected points using our custom method with the selected metric
            rider_data = optimizer.run_simulation_with_teammate_analysis(num_simulations=num_simulations, metric=selected_metric)
            
            # Optimize team (with stage-by-stage selection)
            team_selection = optimize_with_stage_selection_with_injection(
                optimizer,
                rider_data,
                num_simulations=num_simulations,
                rider_db=st.session_state.rider_db,
                risk_aversion=risk_aversion,
                abandon_penalty=abandon_penalty
            )
            
            st.session_state.optimization_results = {
                'team_selection': team_selection,
                'rider_data': rider_data,
                'optimizer': optimizer,
                'metric_used': selected_metric,
                'metric_name': metric_options[selected_metric],
                'risk_aversion': risk_aversion,
                'abandon_penalty': abandon_penalty
            }
            
            st.success(f"✅ Team optimization completed using {metric_options[selected_metric]}!")
    
    # Display results below the button
    if hasattr(st.session_state, 'optimization_results') and st.session_state.optimization_results is not None:
        st.subheader("📊 Optimization Results")
        
        team_selection = st.session_state.optimization_results['team_selection']
        rider_data = st.session_state.optimization_results['rider_data']
        metric_used = st.session_state.optimization_results.get('metric_used', 'mean')
        metric_name = st.session_state.optimization_results.get('metric_name', 'Average (Mean)')
        risk_aversion = st.session_state.optimization_results.get('risk_aversion', 0.0)
        abandon_penalty = st.session_state.optimization_results.get('abandon_penalty', 1.0)
        
        # Show which metric was used and parameters
        st.info(f"📈 **Optimization performed using: {metric_name}**\n"
                f"🎯 **Risk Aversion:** {risk_aversion:.1f}\n"
                f"⚠️ **Abandon Penalty:** {abandon_penalty:.1f}")
        
        # Calculate total team standard deviation for +/- display
        team_std = 0
        for rider in team_selection.riders:
            rider_row = rider_data[rider_data['rider_name'] == rider.name]
            if not rider_row.empty:
                team_std += rider_row.iloc[0]['points_std'] ** 2  # Sum of variances
        team_std = team_std ** 0.5  # Square root to get standard deviation
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Cost", f"{team_selection.total_cost:.2f}")
        
        with col2:
            st.metric("Expected Points", f"{team_selection.expected_points:.1f} ± {team_std:.1f}")
        
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
                points_std = rider_row.iloc[0]['points_std']
                # Also get other metrics for comparison
                mean_points = rider_row.iloc[0]['points_mean']
                median_points = rider_row.iloc[0]['points_median']
                mode_points = rider_row.iloc[0]['points_mode']
                
                rider_points.append({
                    'Rider': rider.name,
                    'Team': rider.team,
                    'Price': rider.price,
                    'Expected Points': expected_points,
                    'Points Std': points_std,
                    'Expected ± Std': f"{expected_points:.1f} ± {points_std:.1f}",
                    'Mean': mean_points,
                    'Median': median_points,
                    'Mode': mode_points,
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
            title=f"Expected Points per Rider ({metric_name})",
            text='Expected Points'
        )
        fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Comparison of different metrics for selected riders
        st.subheader("📈 Metric Comparison for Selected Riders")
        
        # Create comparison chart
        comparison_data = []
        for rider in team_selection.riders:
            rider_row = rider_data[rider_data['rider_name'] == rider.name]
            if not rider_row.empty:
                comparison_data.append({
                    'Rider': rider.name,
                    'Mean': rider_row.iloc[0]['points_mean'],
                    'Median': rider_row.iloc[0]['points_median'],
                    'Mode': rider_row.iloc[0]['points_mode']
                })
        
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            
            # Melt the dataframe for plotting
            comparison_melted = comparison_df.melt(
                id_vars=['Rider'], 
                value_vars=['Mean', 'Median', 'Mode'],
                var_name='Metric', 
                value_name='Points'
            )
            
            fig = px.bar(
                comparison_melted,
                x='Rider',
                y='Points',
                color='Metric',
                title="Comparison of Different Metrics for Selected Riders",
                barmode='group'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        # Stage selections
        if hasattr(team_selection, 'stage_selections') and team_selection.stage_selections:
            st.subheader("🏁 Stage-by-Stage Rider Selections")
            
            # Create stage selection summary
            stage_summary = []
            total_selected_points = 0
            total_bench_points = 0
            
            for stage in sorted(team_selection.stage_selections.keys()):
                selected_riders = team_selection.stage_selections[stage]
                stage_points = team_selection.stage_points.get(stage, {})
                
                # Calculate selected points from stage selections
                selected_points = sum(stage_points.get(rider, 0) for rider in selected_riders)
                
                # Calculate bench points using actual stage performance data
                bench_points = 0
                for rider in team_selection.rider_names:
                    if rider not in selected_riders:
                        # Use actual stage performance data if available
                        if hasattr(team_selection, 'stage_performance_data') and (rider, stage) in team_selection.stage_performance_data:
                            stage_expected_points = team_selection.stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to estimated approach if stage data not available
                            rider_row = rider_data[rider_data['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                # Estimate stage-specific points based on total expected points
                                # Different stages have different point distributions
                                if stage <= 21:  # Regular stages
                                    # Most riders score points on regular stages, but not huge amounts
                                    # Estimate 3-8% of total expected points per stage
                                    stage_factor = 0.05  # 5% of total expected points per stage
                                else:  # Final stage (stage 22)
                                    # Final stage often has more points available
                                    stage_factor = 0.08  # 8% of total expected points
                                
                                stage_expected_points = total_expected_points * stage_factor
                            else:
                                stage_expected_points = 0
                            bench_points += stage_expected_points
                
                total_selected_points += selected_points
                total_bench_points += bench_points
                
                stage_summary.append({
                    'Stage': stage,
                    'Riders Selected': len(selected_riders),
                    'Selected Points': selected_points,
                    'Bench Points': bench_points,
                    'Total Stage Points': selected_points + bench_points,
                    'Selection Efficiency': selected_points / (selected_points + bench_points) if (selected_points + bench_points) > 0 else 0,
                    'Selected Riders': ', '.join(selected_riders)
                })
            
            # Display stage summary with bench points
            stage_df = pd.DataFrame(stage_summary)
            st.dataframe(stage_df, use_container_width=True)
            
            # Summary metrics for bench points
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Selected Points", f"{total_selected_points:.2f}")
            with col2:
                st.metric("Total Bench Points", f"{total_bench_points:.2f}")
            with col3:
                efficiency = total_selected_points / (total_selected_points + total_bench_points) if (total_selected_points + total_bench_points) > 0 else 0
                st.metric("Selection Efficiency", f"{efficiency:.1%}")
            with col4:
                st.metric("Bench Points Lost", f"{total_bench_points:.2f}")
            
            # Bench points analysis
            st.subheader("📊 Bench Points Analysis")
            
            # Create tabs for different views
            tab1, tab2 = st.tabs(["Stage-by-Stage Bench", "Top Bench Performers"])
            
            with tab1:
                st.write("**Stage-by-Stage Bench Points Breakdown:**")
                
                # Create detailed bench analysis per stage
                bench_analysis = []
                for stage in sorted(team_selection.stage_selections.keys()):
                    selected_riders = team_selection.stage_selections[stage]
                    stage_points = team_selection.stage_points.get(stage, {})
                    
                    # Get bench riders and their points
                    bench_riders = [rider for rider in team_selection.rider_names if rider not in selected_riders]
                    bench_rider_points = []
                    
                    for rider in bench_riders:
                        # Get rider's total expected points and distribute across stages
                        rider_row = rider_data[rider_data['rider_name'] == rider]
                        if not rider_row.empty:
                            total_expected_points = rider_row.iloc[0]['expected_points']
                            # Estimate stage-specific points based on total expected points
                            # Different stages have different point distributions
                            if stage <= 21:  # Regular stages
                                # Most riders score points on regular stages, but not huge amounts
                                # Estimate 3-8% of total expected points per stage
                                stage_factor = 0.05  # 5% of total expected points per stage
                            else:  # Final stage (stage 22)
                                # Final stage often has more points available
                                stage_factor = 0.08  # 8% of total expected points
                            
                            stage_expected_points = total_expected_points * stage_factor
                            
                            if stage_expected_points > 0:  # Only show riders who actually have expected points
                                bench_rider_points.append({
                                    'Stage': stage,
                                    'Rider': rider,
                                    'Team': next((r.team for r in team_selection.riders if r.name == rider), 'Unknown'),
                                    'Bench Points': stage_expected_points
                                })
                    
                    # Sort by points and add top bench performers
                    bench_rider_points.sort(key=lambda x: x['Bench Points'], reverse=True)
                    bench_analysis.extend(bench_rider_points[:5])  # Top 5 bench performers per stage
                
                if bench_analysis:
                    bench_df = pd.DataFrame(bench_analysis)
                    st.dataframe(bench_df, use_container_width=True)
                else:
                    st.info("No significant bench points found across stages")
            
            with tab2:
                st.write("**Top Bench Performers (Overall):**")
                
                # Aggregate bench points across all stages
                rider_bench_totals = {}
                for stage in sorted(team_selection.stage_selections.keys()):
                    selected_riders = team_selection.stage_selections[stage]
                    
                    for rider in team_selection.rider_names:
                        if rider not in selected_riders:
                            # Get rider's total expected points and distribute across stages
                            rider_row = rider_data[rider_data['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                # Estimate stage-specific points based on total expected points
                                # Different stages have different point distributions
                                if stage <= 21:  # Regular stages
                                    # Most riders score points on regular stages, but not huge amounts
                                    # Estimate 3-8% of total expected points per stage
                                    stage_factor = 0.05  # 5% of total expected points per stage
                                else:  # Final stage (stage 22)
                                    # Final stage often has more points available
                                    stage_factor = 0.08  # 8% of total expected points
                                
                                stage_expected_points = total_expected_points * stage_factor
                                
                                if rider not in rider_bench_totals:
                                    rider_bench_totals[rider] = 0
                                rider_bench_totals[rider] += stage_expected_points
                
                # Create summary of top bench performers
                top_bench_performers = []
                for rider, total_bench_points in rider_bench_totals.items():
                    if total_bench_points > 0:
                        rider_obj = next((r for r in team_selection.riders if r.name == rider), None)
                        top_bench_performers.append({
                            'Rider': rider,
                            'Team': rider_obj.team if rider_obj else 'Unknown',
                            'Total Bench Points': total_bench_points,
                            'Average Bench Points per Stage': total_bench_points / len(team_selection.stage_selections),
                            'Price': rider_obj.price if rider_obj else 0,
                            'Bench Points per Euro': total_bench_points / rider_obj.price if rider_obj and rider_obj.price > 0 else 0
                        })
                
                # Sort by total bench points
                top_bench_performers.sort(key=lambda x: x['Total Bench Points'], reverse=True)
                
                if top_bench_performers:
                    top_bench_df = pd.DataFrame(top_bench_performers)
                    st.dataframe(top_bench_df, use_container_width=True)
                    
                    # Chart of top bench performers
                    fig = px.bar(
                        top_bench_df.head(10),  # Top 10
                        x='Rider',
                        y='Total Bench Points',
                        color='Team',
                        title="Top 10 Bench Performers (Total Points)",
                        text='Total Bench Points'
                    )
                    fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No significant bench points found")
            
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
                    team_riders = set(team_selection.rider_names)
                    
                    for _, rider_row in rider_data.iterrows():
                        rider_name = rider_row['rider_name']
                        is_selected = rider_name in selected_riders
                        is_team_member = rider_name in team_riders
                        
                        # Calculate points: selected riders get stage points, unselected team members get stage-specific expected points
                        if is_selected:
                            points = stage_points.get(rider_name, 0)
                        elif is_team_member:
                            # Use actual stage performance data if available
                            if hasattr(team_selection, 'stage_performance_data') and (rider_name, stage) in team_selection.stage_performance_data:
                                points = team_selection.stage_performance_data[(rider_name, stage)]
                            else:
                                # Fallback to estimated approach if stage data not available
                                total_expected_points = rider_row['expected_points']
                                # Estimate stage-specific points based on total expected points
                                # Different stages have different point distributions
                                if stage <= 21:  # Regular stages
                                    # Most riders score points on regular stages, but not huge amounts
                                    # Estimate 3-8% of total expected points per stage
                                    stage_factor = 0.05  # 5% of total expected points per stage
                                else:  # Final stage (stage 22)
                                    # Final stage often has more points available
                                    stage_factor = 0.08  # 8% of total expected points
                                
                                points = total_expected_points * stage_factor
                        else:
                            # For non-team members, show 0
                            points = 0
                        
                        stage_rider_data.append({
                            'Rider': rider_name,
                            'Team': rider_row['team'],
                            'Price': rider_row['price'],
                            'Points': points,
                            'Selected': '✓' if is_selected else '✗',
                            'Team Member': 'Yes' if is_team_member else 'No'
                        })
                    
                    # Sort by points (descending)
                    stage_rider_data.sort(key=lambda x: x['Points'], reverse=True)
                    stage_rider_df = pd.DataFrame(stage_rider_data)
                    
                    # Show selected riders first
                    selected_df = stage_rider_df[stage_rider_df['Selected'] == '✓']
                    
                    # Organize unselected riders: team members first, then others
                    unselected_df = stage_rider_df[stage_rider_df['Selected'] == '✗']
                    unselected_df = unselected_df.sort_values(['Team Member', 'Points'], ascending=[False, False])
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Selected Riders:**")
                        st.dataframe(selected_df, use_container_width=True)
                        
                        # Calculate selected points
                        selected_points = selected_df['Points'].sum()
                        st.metric("Selected Points", f"{selected_points:.2f}")
                    
                    with col2:
                        st.write("**Top Unselected Riders (Bench):**")
                        st.dataframe(unselected_df.head(10), use_container_width=True)
                        
                        # Calculate bench points (sum of points for unselected team members)
                        bench_points = unselected_df[unselected_df['Team Member'] == 'Yes']['Points'].sum()
                        
                        st.metric("Bench Points", f"{bench_points:.2f}")
                    
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
                points_std = rider_row.iloc[0]['points_std'] if not rider_row.empty else 0
                team_info.append({
                    'Position': i,
                    'Rider': rider.name,
                    'Team': rider.team,
                    'Price': rider.price,
                    'Expected Points': expected_points,
                    'Points Std': points_std,
                    'Expected ± Std': f"{expected_points:.1f} ± {points_std:.1f}"
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
                'Break Away': ability_to_tier(rider.parameters.break_away_ability),
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
            ability_filter = st.selectbox("⚡ Filter by ability", ["All", "Sprint", "ITT", "Mountain", "Break Away", "Punch"], key="view_ability_filter")
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
            top_tier_count = len(filtered_df[filtered_df[['Sprint', 'ITT', 'Mountain', 'Break Away', 'Punch']].isin(['S', 'A']).any(axis=1)])
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
        styled_df = filtered_df.style.applymap(style_tier, subset=['Sprint', 'ITT', 'Mountain', 'Break Away', 'Punch'])
        
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
                    "Break Away": rider.parameters.break_away_ability,
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
                new_break_away = st.slider("Break Away", 0, 100, rider.parameters.break_away_ability, key="edit_break_away")
                
                new_punch = st.slider("Punch", 0, 100, rider.parameters.punch_ability, key="edit_punch")
            
            # Save Changes button - MOVED TO AFTER FORM FIELDS
            if st.button("💾 Save Changes", key="save_rider_changes", type="primary"):
                # Update rider parameters
                rider.price = new_price
                rider.chance_of_abandon = new_abandon
                rider.parameters.sprint_ability = new_sprint
                rider.parameters.itt_ability = new_itt
                rider.parameters.mountain_ability = new_mountain
                rider.parameters.break_away_ability = new_break_away
                
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
            new_break_away = st.slider("Break Away ability", 0, 100, 50, key="add_break_away")
            
            new_punch = st.slider("Punch ability", 0, 100, 50, key="add_punch")
        
        # Add Rider button - MOVED TO TOP AFTER FORM FIELDS
        if st.button("➕ Add Rider", key="add_rider_button", type="primary"):
            if new_name and new_team:
                # Create new rider parameters
                new_parameters = RiderParameters(
                    sprint_ability=new_sprint,
                    itt_ability=new_itt,
                    mountain_ability=new_mountain,
                    break_away_ability=new_break_away,
                    
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
    skill_categories = ["Sprint", "ITT", "Mountain", "Break Away", "Punch"]
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
        elif skill == "Break Away":
            return rider.parameters.break_away_ability
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
        elif skill == "Break Away":
            rider.parameters.break_away_ability = ability
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
        st.metric("Total Riders", 
                  f"{summary['total_riders']:,}",
                  help="Number of riders in the simulation")
    
    with col3:
        st.metric("Avg Abandonments", 
                  f"{summary['avg_abandonments']:.1f}",
                  help="Average number of riders who abandon per simulation")
    
    with col4:
        st.metric("Avg Points/Stage (per sim)", 
                  f"{summary['avg_points_per_stage']:.1f}")
    
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

def run_optimizer_simulation(optimizer, num_simulations, rider_db, metric='mean'):
    """
    Custom run_simulation method that uses the modified rider database and current stage profiles
    
    Args:
        optimizer: TeamOptimizer instance
        num_simulations: Number of simulations to run
        rider_db: RiderDatabase instance
        metric: Metric to use for expected points ('mean', 'median', 'mode')
    """
    # print(f"Running {num_simulations} simulations to calculate expected points using {metric}...")
    
    # Store points from all simulations
    all_points = []
    
    for i in range(num_simulations):
        if i % 10 == 0:
            pass  # removed print(f"Simulation {i+1}/{num_simulations}")
        
        # Ensure the simulator has the correct rider database and stage profiles
        inject_rider_database(optimizer.simulator, rider_db)
        inject_stage_profiles(optimizer.simulator)
        
        # Run simulation
        optimizer.simulator.simulate_tour()
        
        # Get final points for each rider
        for rider_name, points in optimizer.simulator.scorito_points.items():
            all_points.append({
                'rider_name': rider_name,
                'points': points,
                'simulation': i
            })
        
        # Reset simulator for next run but keep the modified rider database and stage profiles
        optimizer.simulator = TourSimulator()
        # Immediately inject the rider database and stage profiles after reset
        inject_rider_database(optimizer.simulator, rider_db)
        inject_stage_profiles(optimizer.simulator)
    
    # Calculate expected points for each rider using the specified metric
    points_df = pd.DataFrame(all_points)
    
    # Group by rider and calculate multiple statistics
    rider_stats = points_df.groupby('rider_name')['points'].agg([
        'mean', 'median', 'std', 'count'
    ]).reset_index()
    
    # Calculate mode (most frequent value) for each rider
    mode_values = []
    for rider_name in rider_stats['rider_name']:
        rider_points = points_df[points_df['rider_name'] == rider_name]['points'].values
        # Use numpy's mode function, but handle cases where there might be multiple modes
        try:
            from scipy import stats
            mode_result = stats.mode(rider_points, keepdims=False)
            mode_values.append(mode_result.mode if hasattr(mode_result, 'mode') else mode_result)
        except ImportError:
            # Fallback to manual mode calculation
            from collections import Counter
            counter = Counter(rider_points)
            mode_values.append(counter.most_common(1)[0][0])
    
    rider_stats['mode'] = mode_values
    
    # Select the expected points based on the metric
    if metric == 'mean':
        expected_points = rider_stats['mean']
    elif metric == 'median':
        expected_points = rider_stats['median']
    elif metric == 'mode':
        expected_points = rider_stats['mode']
    else:
        raise ValueError(f"Unknown metric: {metric}. Must be 'mean', 'median', or 'mode'")
    
    # Create the final expected points dataframe
    expected_points_df = pd.DataFrame({
        'rider_name': rider_stats['rider_name'],
        'expected_points': expected_points,
        'points_std': rider_stats['std'],
        'points_mean': rider_stats['mean'],
        'points_median': rider_stats['median'],
        'points_mode': rider_stats['mode'],
        'simulation_count': rider_stats['count']
    })
    
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
    final_df = rider_info_df.merge(expected_points_df, on='rider_name', how='left')
    final_df['expected_points'] = final_df['expected_points'].fillna(0)
    final_df['points_std'] = final_df['points_std'].fillna(0)
    final_df['points_mean'] = final_df['points_mean'].fillna(0)
    final_df['points_median'] = final_df['points_median'].fillna(0)
    final_df['points_mode'] = final_df['points_mode'].fillna(0)
    final_df['simulation_count'] = final_df['simulation_count'].fillna(0)
    
    return final_df

def get_stage_performance_data_with_injection(optimizer, num_simulations, rider_db):
    """
    Custom method to get stage performance data with proper rider database injection
    
    Args:
        optimizer: TeamOptimizer instance
        num_simulations: Number of simulations to run
        rider_db: RiderDatabase instance
        
    Returns:
        Dictionary mapping (rider_name, stage) to expected points
    """
    stage_points = {}
    
    for sim in range(num_simulations):
        if sim % 10 == 0:
            pass  # removed print(f"Stage analysis simulation {sim+1}/{num_simulations}")
        
        # Ensure the simulator has the correct rider database and stage profiles
        inject_rider_database(optimizer.simulator, rider_db)
        inject_stage_profiles(optimizer.simulator)
        
        # Run simulation and collect stage-by-stage points
        optimizer.simulator.simulate_tour()
        
        # Extract stage points from the records and calculate per-stage points
        stage_records = optimizer.simulator.scorito_points_records
        
        # Group records by rider and stage
        rider_stage_points = {}
        for record in stage_records:
            rider_name = record['rider']
            stage = record['stage']
            cumulative_points = record['scorito_points']
            
            if rider_name not in rider_stage_points:
                rider_stage_points[rider_name] = {}
            rider_stage_points[rider_name][stage] = cumulative_points
        
        # Calculate per-stage points by taking differences
        for rider_name, stage_data in rider_stage_points.items():
            stages = sorted(stage_data.keys())
            for i, stage in enumerate(stages):
                if i == 0:
                    # First stage: points earned = cumulative points
                    points_earned = stage_data[stage]
                else:
                    # Other stages: points earned = current cumulative - previous cumulative
                    points_earned = stage_data[stage] - stage_data[stages[i-1]]
                
                key = (rider_name, stage)
                if key not in stage_points:
                    stage_points[key] = []
                stage_points[key].append(points_earned)
        
        # Reset simulator and immediately inject the rider database and stage profiles
        optimizer.simulator = TourSimulator()
        inject_rider_database(optimizer.simulator, rider_db)
        inject_stage_profiles(optimizer.simulator)
    
    # Calculate expected points for each rider-stage combination
    expected_stage_points = {}
    for key, points_list in stage_points.items():
        expected_stage_points[key] = np.mean(points_list)
    
    return expected_stage_points

def optimize_with_stage_selection_with_injection(optimizer, rider_data, num_simulations, rider_db, risk_aversion=0.0, abandon_penalty=1.0):
    """
    Custom version of optimize_with_stage_selection that uses proper rider database injection
    
    Args:
        optimizer: TeamOptimizer instance
        rider_data: DataFrame with rider information and expected points
        num_simulations: Number of simulations for stage analysis
        rider_db: RiderDatabase instance
        risk_aversion: Factor to penalize high variance (0 = no penalty, 1 = high penalty)
        abandon_penalty: Factor to penalize high abandon probability (0 = no penalty, 1 = high penalty)
        
    Returns:
        TeamSelection object with optimal team
    """
    from team_optimization import TeamSelection
    from pulp import LpProblem, LpMaximize, LpVariable, lpSum, LpStatusOptimal, LpStatus
    
    # Use our custom method to get stage-by-stage performance data
    stage_performance = get_stage_performance_data_with_injection(optimizer, num_simulations, rider_db)
    
    # Create optimization problem
    prob = LpProblem("Advanced_Team_Optimization", LpMaximize)
    
    riders = list(rider_data['rider_name'])
    stages = list(range(1, 23))  # 22 stages
    
    # Decision variables
    # x[i] = 1 if rider i is selected for the team
    rider_vars = LpVariable.dicts("Rider", riders, cat='Binary')
    
    # y[i,j] = 1 if rider i is selected for stage j
    stage_vars = LpVariable.dicts("Stage", 
                                [(r, s) for r in riders for s in stages], 
                                cat='Binary')
    
    # Objective: maximize total points across all stages
    objective_terms = []
    for rider in riders:
        for stage in stages:
            if (rider, stage) in stage_performance:
                points = stage_performance[(rider, stage)]
                
                # Apply risk aversion if specified
                if risk_aversion > 0:
                    # Get rider's variance from the rider_data
                    rider_row = rider_data[rider_data['rider_name'] == rider]
                    if not rider_row.empty and 'points_std' in rider_row.columns:
                        points_std = rider_row.iloc[0]['points_std']
                        # Risk-adjusted points = expected points - (risk_aversion * standard deviation)
                        points = points - (risk_aversion * points_std)
                
                # Apply abandon penalty if specified
                if abandon_penalty > 0:
                    # Get rider's abandon probability from the rider_data
                    abandon_prob = rider_data[rider_data['rider_name'] == rider].iloc[0]['chance_of_abandon']
                    # Penalize points based on abandon probability
                    points = points * (1 - abandon_penalty * abandon_prob)
                
                objective_terms.append(stage_vars[(rider, stage)] * points)
    
    prob += lpSum(objective_terms)
    
    # Constraint 1: Exactly team_size riders in team
    prob += lpSum(rider_vars[rider] for rider in riders) == optimizer.team_size
    
    # Constraint 2: Budget constraint
    cost_terms = []
    for _, row in rider_data.iterrows():
        rider_name = row['rider_name']
        price = row['price']
        cost_terms.append(rider_vars[rider_name] * price)
    prob += lpSum(cost_terms) <= optimizer.budget
    
    # Constraint 3: Can only select riders for stages if they're in the team
    for rider in riders:
        for stage in stages:
            prob += stage_vars[(rider, stage)] <= rider_vars[rider]
    
    # Constraint 4: Stage selection limits
    for stage in stages:
        if stage == 22:  # Final stage: all riders
            prob += lpSum(stage_vars[(rider, stage)] for rider in riders) == optimizer.final_stage_riders
        else:  # Regular stages: riders_per_stage
            prob += lpSum(stage_vars[(rider, stage)] for rider in riders) == optimizer.riders_per_stage
    
    # Constraint 5: Maximum 4 riders per team (Scorito rule)
    teams = rider_data['team'].unique()
    for team in teams:
        team_riders = rider_data[rider_data['team'] == team]['rider_name'].tolist()
        if team_riders:
            prob += lpSum(rider_vars[rider] for rider in team_riders) <= 4
    
    # Solve
    prob.solve()
    
    if prob.status != LpStatusOptimal:
        raise ValueError(f"Advanced optimization failed with status: {LpStatus[prob.status]}")
    
    # Extract solution
    selected_riders = []
    total_cost = 0
    total_points = 0
    stage_selections = {}
    stage_points = {}
    
    for rider_name in riders:
        if rider_vars[rider_name].value() == 1:
            rider_row = rider_data[rider_data['rider_name'] == rider_name].iloc[0]
            rider_obj = optimizer.rider_db.get_rider(rider_name)
            selected_riders.append(rider_obj)
            total_cost += rider_row['price']
            
            # Calculate total points for this rider across all stages
            rider_stage_points = 0
            for stage in stages:
                if stage_vars[(rider_name, stage)].value() == 1:
                    if (rider_name, stage) in stage_performance:
                        points = stage_performance[(rider_name, stage)]
                        rider_stage_points += points
                        
                        # Store stage selections and points
                        if stage not in stage_selections:
                            stage_selections[stage] = []
                            stage_points[stage] = {}
                        stage_selections[stage].append(rider_name)
                        stage_points[stage][rider_name] = points
            
            total_points += rider_stage_points
    
    # Create a custom TeamSelection object that includes stage performance data
    team_selection = TeamSelection(
        riders=selected_riders,
        total_cost=total_cost,
        expected_points=total_points,
        rider_names=[r.name for r in selected_riders],
        stage_selections=stage_selections,
        stage_points=stage_points
    )
    
    # Add stage performance data as an attribute (since TeamSelection is a dataclass)
    team_selection.stage_performance_data = stage_performance
    
    return team_selection

def show_stage_types_management():
    st.header("🏁 Stage Types Management")
    st.markdown("""
    **Manage the stage types for each stage of the Tour de France.**
    
    **Create mixed stage types with weights!** For example, a stage can be 60% punch and 40% sprint.
    All weights must sum to 1.0 (100%).
    """)
    
    # Create a copy of stage profiles for editing
    if 'stage_profiles_edit' not in st.session_state:
        st.session_state.stage_profiles_edit = STAGE_PROFILES.copy()
    
    # Stage type options - use the actual enum values
    stage_type_options = {
        StageType.SPRINT: "Sprint",
        StageType.PUNCH: "Punch", 
        StageType.ITT: "Individual Time Trial",
        StageType.MOUNTAIN: "Mountain",
        StageType.BREAK_AWAY: "Break Away"
    }
    
    # Show advanced stage configuration
    show_advanced_stage_config(stage_type_options)
    
    # Stage type summary
    st.markdown("---")
    st.markdown("### Stage Type Summary")
    show_stage_summary(stage_type_options)
    
    # Controls
    st.markdown("---")
    show_stage_controls(stage_type_options)

def show_advanced_stage_config(stage_type_options):
    """Show advanced mixed-type stage configuration"""
    st.markdown("#### Stage Configuration")
    st.markdown("Create mixed stage types with weights. All weights must sum to 1.0 (100%).")
    
    # Create a list layout for stages
    for i in range(21):  # 21 stages
        stage_num = i + 1
        
        # Get current stage profile
        current_profile = st.session_state.stage_profiles_edit.get(stage_num, {StageType.SPRINT: 1.0})
        
        # Ensure it's a dict
        if not isinstance(current_profile, dict):
            current_profile = {current_profile: 1.0}
        
        # Create insightful expander title
        # Find primary type (highest weight)
        primary_type = max(current_profile.items(), key=lambda x: x[1])[0]
        primary_weight = current_profile[primary_type]
        
        # Count active types (weight > 0)
        active_types = [st for st, w in current_profile.items() if w > 0]
        
        if len(active_types) == 1:
            # Single type stage
            expander_title = f"Stage {stage_num} - {stage_type_options[primary_type]} (100%)"
        else:
            # Mixed stage
            profile_summary = ", ".join([f"{stage_type_options[st]}: {w:.0%}" for st, w in current_profile.items() if w > 0])
            expander_title = f"Stage {stage_num} - Mixed: {profile_summary}"
        
        with st.expander(expander_title, expanded=False):
            # Create weight inputs for each stage type
            new_profile = {}
            total_weight = 0.0
            
            st.markdown("**Set weights for each stage type (must sum to 1.0):**")
            
            cols = st.columns(len(stage_type_options))
            for idx, (stage_type, stage_name) in enumerate(stage_type_options.items()):
                with cols[idx]:
                    current_weight = current_profile.get(stage_type, 0.0)
                    weight = st.number_input(
                        f"{stage_name}",
                        min_value=0.0,
                        max_value=1.0,
                        value=float(current_weight),
                        step=0.05,  # Changed from 0.1 to 0.05 for finer control
                        key=f"weight_{stage_num}_{stage_type.value}"
                    )
                    new_profile[stage_type] = weight
                    total_weight += weight
            
            # Show total weight
            st.markdown(f"**Total Weight: {total_weight:.2f}**")
            
            # Validate and update
            if abs(total_weight - 1.0) < 0.001:  # Allow small floating point errors
                if new_profile != current_profile:
                    st.session_state.stage_profiles_edit[stage_num] = new_profile
                    st.success(f"✅ Stage {stage_num} updated with mixed profile")
                    st.rerun()  # Refresh to update the expander title
                
                # Show the profile
                profile_text = ", ".join([f"{stage_type_options[st]}: {w:.2f}" for st, w in new_profile.items() if w > 0])
                st.markdown(f"**Current Profile:** {profile_text}")
            else:
                st.error(f"❌ Weights must sum to 1.0 (currently {total_weight:.2f})")
                
                # Auto-normalize option
                if st.button(f"Auto-normalize Stage {stage_num}", key=f"normalize_{stage_num}"):
                    if total_weight > 0:
                        normalized_profile = {st: w/total_weight for st, w in new_profile.items()}
                        st.session_state.stage_profiles_edit[stage_num] = normalized_profile
                        st.success(f"✅ Stage {stage_num} normalized")
                        st.rerun()

def show_stage_summary(stage_type_options):
    """Show summary of stage types"""
    # Calculate type distribution
    type_counts = {}
    mixed_stages = []
    
    for stage_num in range(1, 22):
        profile = st.session_state.stage_profiles_edit.get(stage_num, {StageType.SPRINT: 1.0})
        
        if isinstance(profile, dict):
            # Count each type with its weight
            for stage_type, weight in profile.items():
                if stage_type not in type_counts:
                    type_counts[stage_type] = 0
                type_counts[stage_type] += weight
            
            # Check if it's a mixed stage
            if len([w for w in profile.values() if w > 0]) > 1:
                mixed_stages.append(stage_num)
        else:
            # Legacy single type
            if profile not in type_counts:
                type_counts[profile] = 0
            type_counts[profile] += 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Current Distribution:**")
        for stage_type, count in type_counts.items():
            st.write(f"• {stage_type_options[stage_type]}: {count:.1f} stages")
        
        if mixed_stages:
            st.markdown(f"**Mixed Stages:** {', '.join(map(str, mixed_stages))}")
        else:
            st.markdown("**Mixed Stages:** None")
    
    with col2:
        # Create pie chart
        if type_counts:
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

def show_stage_controls(stage_type_options):
    """Show stage management controls"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔄 Reset to Default", key="reset_stage_types"):
            st.session_state.stage_profiles_edit = STAGE_PROFILES.copy()
            st.rerun()
    
    with col2:
        if st.button("📊 Export Stage Types", key="export_stage_types"):
            # Create export data
            export_data = []
            for stage_num in range(1, 22):
                profile = st.session_state.stage_profiles_edit.get(stage_num, {StageType.SPRINT: 1.0})
                
                if isinstance(profile, dict):
                    # Mixed stage
                    for stage_type, weight in profile.items():
                        if weight > 0:
                            export_data.append({
                                'Stage': stage_num,
                                'Type': stage_type_options[stage_type],
                                'Weight': weight,
                                'Type_Value': stage_type.value
                            })
                else:
                    # Single type
                    export_data.append({
                        'Stage': stage_num,
                        'Type': stage_type_options[profile],
                        'Weight': 1.0,
                        'Type_Value': profile.value
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
            # Validate all profiles
            invalid_stages = []
            for stage_num in range(1, 22):
                profile = st.session_state.stage_profiles_edit.get(stage_num, {StageType.SPRINT: 1.0})
                if isinstance(profile, dict) and not validate_stage_profile(profile):
                    invalid_stages.append(stage_num)
            
            if invalid_stages:
                st.error(f"❌ Invalid profiles for stages: {invalid_stages}. Weights must sum to 1.0.")
            else:
                # Update the actual stage profiles
                import stage_profiles
                stage_profiles.STAGE_PROFILES.update(st.session_state.stage_profiles_edit)
                st.success("✅ Stage types updated! Changes will apply to new simulations.")
    
    with col4:
        if st.button("🎲 Quick Mix Examples", key="quick_mix_examples"):
            # Apply some example mixed stages
            examples = {
                4: {StageType.PUNCH: 0.6, StageType.SPRINT: 0.4},  # Hilly sprint
                8: {StageType.SPRINT: 0.5, StageType.PUNCH: 0.3, StageType.BREAK_AWAY: 0.2},  # Complex
                13: {StageType.BREAK_AWAY: 0.3, StageType.MOUNTAIN: 0.7},  # Mountain with breakaway
                16: {StageType.MOUNTAIN: 0.8, StageType.BREAK_AWAY: 0.2}  # Mountain with opportunities
            }
            
            for stage_num, profile in examples.items():
                st.session_state.stage_profiles_edit[stage_num] = profile
            
            st.success("✅ Applied example mixed stages to stages 4, 8, 13, and 16!")
            st.rerun()

def ability_to_tier(ability: int) -> str:
    """Convert ability score to tier name"""
    if ability >= 98:
        return "S"
    elif ability >= 95:
        return "A"
    elif ability >= 90:
        return "B"
    elif ability >= 80:
        return "C"
    elif ability >= 70:
        return "D"
    else:
        return "E"

def tier_to_color(tier: str) -> str:
    """Get color for tier display"""
    colors = {
        "S": "💎",
        "A": "🟢", 
        "B": "🟢",
        "C": "🟡",
        "D": "🟠",
        "E": "🔴"
    }
    return colors.get(tier, "⚪")

def show_versus_mode():
    st.header('🆚 Versus Mode')
    st.markdown('''
    **Versus Mode** allows you to select your own team of 20 riders (budget 48, max 4/team), run simulations, and compare your team against the optimal team.
    ''')

    # Debug output

    
    try:
        # Add custom CSS for compact versus mode
        st.markdown("""
        <style>
        .versus-rider-card {
            border: 2px solid #6c757d;
            border-radius: 8px;
            padding: 8px;
            margin: 4px 0;
            background-color: #f8f9fa;
            font-size: 12px;
            transition: all 0.2s ease;
            min-height: 80px;
        }
        .versus-rider-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .versus-rider-card.selected {
            border-color: #28a745;
            background-color: #d4edda;
        }
        .versus-rider-name {
            font-weight: bold;
            font-size: 13px;
            margin-bottom: 4px;
            color: #333;
        }
        .versus-rider-info {
            color: #666;
            font-size: 11px;
            margin-bottom: 4px;
        }
        .versus-rider-abilities {
            font-size: 11px;
            color: #333;
            line-height: 1.2;
        }
        .versus-team-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            margin: 15px 0 8px 0;
            font-weight: bold;
            font-size: 15px;
        }
        .versus-stats-row {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 10px;
            padding: 12px;
            margin: 12px 0;
            color: white;
        }
        .sidebar-rider-card {
            border: 1px solid #ddd;
            border-radius: 6px;
            padding: 6px;
            margin: 3px 0;
            background-color: #f9f9f9;
            font-size: 11px;
        }
        .sidebar-rider-card.selected {
            border-color: #28a745;
            background-color: #d4edda;
        }
        </style>
        """, unsafe_allow_html=True)
        
    
        
        versus = VersusMode()
    
        
        # Inject the session state rider database into the versus mode
        versus.rider_db = st.session_state.rider_db
        versus.team_optimizer.rider_db = st.session_state.rider_db
        inject_rider_database(versus.team_optimizer.simulator, st.session_state.rider_db)
        
    
        
        available_riders = versus.get_available_riders()
    

        # Session state already initialized in main function


        
        # Create two columns: main content and sidebar
        main_col, sidebar_col = st.columns([4, 1])
        
        with main_col:
            # Team selection section
            st.subheader('1. Select Your Team')
            st.caption('Pick up to 20 riders. Budget: 48. Max 4 per team.')

            # Show current selection stats
            selected_df = available_riders[available_riders['name'].isin(st.session_state['versus_selected_riders'])]
            total_cost = selected_df['price'].sum()
            team_counts = selected_df['team'].value_counts().to_dict()
            
            # Compact stats display
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Selected", f"{len(st.session_state['versus_selected_riders'])}/20")
            with col2:
                st.metric("Budget", f"{total_cost:.1f}/48")
            with col3:
                st.metric("Remaining", f"{48 - total_cost:.1f}")
            with col4:
                st.metric("Teams", len(team_counts))

            # Compact rider selection interface
            st.subheader("2. Available Riders")
            
            # Filters in a compact row
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                search = st.text_input('🔍 Search:', placeholder='Name or team...', key='versus_search')
            with col2:
                specialty_filter = st.selectbox("Specialty:", ["All", "Sprint", "Punch", "ITT", "Mountain", "Break Away"], key='versus_specialty')
            with col3:
                sort_by = st.selectbox("Sort by:", ["Best Ability", "Price", "Age", "Name"], key='versus_sort')
            
            # Apply filters
            filtered_riders = available_riders.copy()
            
            if search:
                filtered_riders = filtered_riders[
                    filtered_riders['name'].str.contains(search, case=False, na=False) |
                    filtered_riders['team'].str.contains(search, case=False, na=False)
                ]
            
            if specialty_filter != "All":
                specialty_col = specialty_filter.lower() + '_ability'
                filtered_riders = filtered_riders[filtered_riders[specialty_col] == filtered_riders[specialty_col].max()]
            
            # Sort riders
            if sort_by == "Best Ability":
                filtered_riders['max_ability'] = filtered_riders[['sprint_ability', 'punch_ability', 'itt_ability', 'mountain_ability', 'break_away_ability']].max(axis=1)
                filtered_riders = filtered_riders.sort_values('max_ability', ascending=False)
            elif sort_by == "Price":
                filtered_riders = filtered_riders.sort_values('price', ascending=False)
            elif sort_by == "Age":
                filtered_riders = filtered_riders.sort_values('age', ascending=True)
            elif sort_by == "Name":
                filtered_riders = filtered_riders.sort_values('name')
            
            # Group by team for compact display
            teams = filtered_riders.groupby('team')
            
            # Create a compact team selector
            team_names = sorted(teams.groups.keys())
            if len(team_names) > 6:
                # Use a multi-select for teams when there are many
                selected_teams = st.multiselect(
                    "Select Teams to Show:",
                    team_names,
                    default=team_names,  # Show all teams by default
                    key='versus_teams'
                )
            else:
                selected_teams = team_names
            
            # Display riders in a compact grid
            st.markdown("### Rider Selection Grid")
            
            # Create a compact table-like display
            for team_name in selected_teams:
                team_riders = teams.get_group(team_name)
                team_selected = [r for r in st.session_state['versus_selected_riders'] if r in team_riders['name'].values]
                team_selected_count = len(team_selected)
                
                # Team header with custom CSS
                st.markdown(f"""
                <div class="versus-team-header">
                    🏢 {team_name} ({team_selected_count}/4 selected)
                </div>
                """, unsafe_allow_html=True)
                
                # Create a compact grid for this team's riders
                cols = st.columns(4)  # 4 riders per row for better visibility
                
                for idx, (_, rider) in enumerate(team_riders.iterrows()):
                    rider_name = rider['name']
                    is_selected = rider_name in st.session_state['versus_selected_riders']
                    col_idx = idx % 4
                    
                    with cols[col_idx]:
                        # Determine if rider can be added
                        can_add = (len(st.session_state['versus_selected_riders']) < 20 and 
                                  total_cost + rider['price'] <= 48 and 
                                  team_selected_count < 4)
                        
                        # Compact rider card with custom CSS classes
                        status_icon = "✅" if is_selected else "⭕"
                        card_class = "versus-rider-card selected" if is_selected else "versus-rider-card"
                        
                        st.markdown(f"""
                        <div class="{card_class}">
                            <div class="versus-rider-name">{status_icon} {rider_name}</div>
                            <div class="versus-rider-info">{rider['team']} • {rider['age']}y • 💰 {rider['price']:.1f}</div>
                            <div class="versus-rider-abilities">
                                S:{ability_to_tier(rider['sprint_ability'])} P:{ability_to_tier(rider['punch_ability'])}<br>
                                I:{ability_to_tier(rider['itt_ability'])} M:{ability_to_tier(rider['mountain_ability'])}<br>
                                B:{ability_to_tier(rider['break_away_ability'])}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action button
                        if is_selected:
                            if st.button(f"❌ Remove", key=f"grid_remove_{team_name}_{rider_name}", help=f"Remove {rider_name}"):
                                st.session_state['versus_selected_riders'].remove(rider_name)
                                st.rerun()
                        else:
                            if can_add:
                                if st.button(f"➕ Add", key=f"grid_add_{team_name}_{rider_name}", help=f"Add {rider_name}"):
                                    st.session_state['versus_selected_riders'].append(rider_name)
                                    st.rerun()
                            else:
                                reason = "Team full" if len(st.session_state['versus_selected_riders']) >= 20 else "Budget exceeded" if total_cost + rider['price'] > 48 else "Team limit"
                                st.button(f"➕ Add", key=f"grid_add_{team_name}_{rider_name}", disabled=True, help=f"Cannot add: {reason}")
                
                st.markdown("---")  # Separator between teams

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
                
                # Add metric selector for versus mode
                st.subheader("3. Simulation Settings")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    metric_options = {
                        'mean': 'Average (Mean)',
                        'median': 'Median',
                        'mode': 'Mode (Most Frequent)'
                    }
                    selected_metric = st.selectbox(
                        "Expected Points Metric",
                        options=list(metric_options.keys()),
                        format_func=lambda x: metric_options[x],
                        index=0,
                        key="versus_metric"
                    )
                
                with col2:
                    # Add optimization parameter controls for versus mode
                    st.write("**Optimal Team Parameters:**")
                    versus_risk_aversion = st.slider("Risk aversion", 0.0, 1.0, 0.0, 0.1, key="versus_risk_aversion")
                    versus_abandon_penalty = st.slider("Abandon penalty", 0.0, 1.0, 1.0, 0.1, key="versus_abandon_penalty")
                
                # Show explanation of the selected metric
                metric_explanations = {
                    'mean': "Average of all simulation results. Good for normally distributed data.",
                    'median': "Middle value when results are sorted. Less sensitive to outliers than mean.",
                    'mode': "Most frequently occurring result. Good for discrete or skewed distributions."
                }
                st.info(f"**{metric_options[selected_metric]}**: {metric_explanations[selected_metric]}")
                
                # Parameter explanations for versus mode
                st.info("**🎯 Optimal Team Parameters:**\n\n"
                        f"• **Risk Aversion:** {versus_risk_aversion:.1f} - {'No penalty for high variance' if versus_risk_aversion == 0.0 else 'Penalizes inconsistent performers'}\n"
                        f"• **Abandon Penalty:** {versus_abandon_penalty:.1f} - {'No penalty for abandon risk' if versus_abandon_penalty == 0.0 else 'Penalizes riders likely to abandon'}")
                
                # Simulation settings
                st.subheader("🔧 Simulation Settings")
                num_simulations = st.slider(
                    "Number of simulations", 
                    min_value=1, 
                    max_value=2000, 
                    value=100, 
                    step=1,
                    help="More simulations provide more accurate results but take longer to run"
                )
                st.info(f"**Simulation Count:** {num_simulations} - {'Quick test' if num_simulations < 50 else 'Good accuracy' if num_simulations < 200 else 'High accuracy' if num_simulations < 500 else 'Very high accuracy'}")
                
                run_sim = st.button('Run Versus Simulation', type='primary')
                if run_sim:
                    with st.spinner('Running unified simulations for consistent results... (this may take a minute)'):
                        # Create user team
                        user_team = versus.create_user_team(st.session_state['versus_selected_riders'])
                        
                        # Ensure the versus optimizer has the correct rider database
                        versus.rider_db = st.session_state.rider_db
                        versus.team_optimizer.rider_db = st.session_state.rider_db
                        inject_rider_database(versus.team_optimizer.simulator, st.session_state.rider_db)
                        
                        # Run unified simulations for consistent results
                        unified_results = versus.run_unified_simulations(user_team, num_simulations=num_simulations)
                        
                        # Compare teams using the unified results
                        comparison = versus.compare_teams(
                            unified_results['user_team'], 
                            unified_results['optimal_team'],
                            user_simulation_results=unified_results['user_simulation_results'],
                            optimal_simulation_results=unified_results['optimal_simulation_results']
                        )
                        
                        st.session_state['versus_results'] = {
                            'user_team': unified_results['user_team'],
                            'optimal_team': unified_results['optimal_team'],
                            'comparison': comparison,
                            'rider_data': unified_results['rider_data'],
                            'user_simulation_results': unified_results['user_simulation_results'],
                            'optimal_simulation_results': unified_results['optimal_simulation_results']
                        }
                        st.rerun()

        with sidebar_col:
            # Selected riders sidebar
            st.subheader("📋 Selected Riders")
            
            if st.button("🔄 Clear All", help="Remove all selected riders"):
                st.session_state['versus_selected_riders'] = []
                st.rerun()
            
            if st.session_state['versus_selected_riders']:
                for rider_name in st.session_state['versus_selected_riders']:
                    rider = selected_df[selected_df['name'] == rider_name].iloc[0]
                    
                    st.markdown(f"""
                    <div class="sidebar-rider-card selected">
                        <div style="font-weight: bold; font-size: 12px;">{rider_name}</div>
                        <div style="font-size: 10px; color: #666;">{rider['team']} • {rider['age']}y</div>
                        <div style="font-size: 10px; color: #666;">💰 {rider['price']:.1f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"❌", key=f"sidebar_remove_{rider_name}", help=f"Remove {rider_name}"):
                        st.session_state['versus_selected_riders'].remove(rider_name)
                        st.rerun()
            else:
                st.info("No riders selected yet. Use the main area to select riders.")
            
            # Show results if available
            if 'versus_results' in st.session_state and st.session_state['versus_results'] is not None:
                st.subheader("📊 Results")
                results = st.session_state['versus_results']
                
                st.write("**Your Team:**")
                st.write(f"Points: {results['comparison']['user_team']['expected_points']:.1f}")
                
                st.write("**Optimal Team:**")
                st.write(f"Points: {results['comparison']['optimal_team']['expected_points']:.1f}")
                
                if st.button("View Full Results"):
                    st.session_state['show_versus_results'] = True
                    st.rerun()
    
    except Exception as e:
        st.error(f"Error in versus mode: {str(e)}")
        st.write("Debug: Exception occurred")
        import traceback
        st.code(traceback.format_exc())

    # Display versus mode results if available
    if 'versus_results' in st.session_state and st.session_state['versus_results'] is not None:
        st.subheader("📊 Versus Mode Results")
        
        results = st.session_state['versus_results']
        comparison = results['comparison']
        
        # Display comparison summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Your Team:**")
            st.write(f"**Riders:** {', '.join(comparison['user_team']['rider_names'])}")
            st.write(f"**Cost:** {comparison['user_team']['total_cost']:.2f}")
            st.write(f"**Expected Points:** {comparison['user_team']['expected_points']:.2f}")
            st.write(f"**Efficiency:** {comparison['comparison']['user_efficiency']:.2f} points/cost")
        
        with col2:
            st.write("**Optimal Team:**")
            st.write(f"**Riders:** {', '.join(comparison['optimal_team']['rider_names'])}")
            st.write(f"**Cost:** {comparison['optimal_team']['total_cost']:.2f}")
            st.write(f"**Expected Points:** {comparison['optimal_team']['expected_points']:.2f}")
            st.write(f"**Efficiency:** {comparison['comparison']['optimal_efficiency']:.2f} points/cost")
        
        # Performance comparison
        st.subheader("Performance Comparison")
        
        user_points = comparison['user_team']['expected_points']
        optimal_points = comparison['optimal_team']['expected_points']
        
        if user_points > optimal_points:
            st.success(f"🎉 Your team outperforms the optimal team by {user_points - optimal_points:.2f} points!")
        elif user_points < optimal_points:
            st.warning(f"📉 The optimal team outperforms your team by {optimal_points - user_points:.2f} points")
        else:
            st.info("🤝 Your team performs equally to the optimal team")
        
        # PART 1: Rider-by-Rider Points Comparison
        st.subheader("1. Rider-by-Rider Points Comparison")
        
        # Calculate actual points for each rider based on stage selections
        user_rider_points = {}
        optimal_rider_points = {}
        
        # User team rider points
        user_riders = results['user_team'].rider_names
        for rider in user_riders:
            user_rider_points[rider] = 0
            if hasattr(results['user_team'], 'stage_selections') and results['user_team'].stage_selections:
                for stage, selected_riders in results['user_team'].stage_selections.items():
                    if rider in selected_riders:
                        stage_points = results['user_team'].stage_points.get(stage, {}).get(rider, 0)
                        user_rider_points[rider] += stage_points
        
        # Optimal team rider points
        optimal_riders = results['optimal_team'].rider_names
        for rider in optimal_riders:
            optimal_rider_points[rider] = 0
            if hasattr(results['optimal_team'], 'stage_selections') and results['optimal_team'].stage_selections:
                for stage, selected_riders in results['optimal_team'].stage_selections.items():
                    if rider in selected_riders:
                        stage_points = results['optimal_team'].stage_points.get(stage, {}).get(rider, 0)
                        optimal_rider_points[rider] += stage_points
        
        # Create comparison dataframe
        import pandas as pd
        comparison_data = []
        
        # Add user team riders
        for rider in user_riders:
            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
            team_name = rider_row.iloc[0]['team'] if not rider_row.empty else "Unknown"
            comparison_data.append({
                'Rider': rider,
                'Team': team_name,
                'User_Team_Points': user_rider_points.get(rider, 0),
                'Optimal_Team_Points': optimal_rider_points.get(rider, 0),
                'Difference': user_rider_points.get(rider, 0) - optimal_rider_points.get(rider, 0),
                'Team_Type': 'User Team'
            })
        
        # Add optimal team riders not in user team
        for rider in optimal_riders:
            if rider not in user_riders:
                rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                team_name = rider_row.iloc[0]['team'] if not rider_row.empty else "Unknown"
                comparison_data.append({
                    'Rider': rider,
                    'Team': team_name,
                    'User_Team_Points': 0,
                    'Optimal_Team_Points': optimal_rider_points.get(rider, 0),
                    'Difference': -optimal_rider_points.get(rider, 0),
                    'Team_Type': 'Optimal Team Only'
                })
        
        comparison_df = pd.DataFrame(comparison_data)
        comparison_df = comparison_df.sort_values('User_Team_Points', ascending=False)
        
        # Display rider comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**User Team Riders:**")
            user_df = comparison_df[comparison_df['Team_Type'] == 'User Team'].copy()
            user_df = user_df[['Rider', 'Team', 'User_Team_Points']]
            user_df.columns = ['Rider', 'Team', 'Points']
            st.dataframe(user_df, use_container_width=True)
            
            total_user_points = user_df['Points'].sum()
            st.write(f"**Total User Team Points:** {total_user_points:.2f}")
        
        with col2:
            st.write("**Optimal Team Riders:**")
            optimal_df = comparison_df[comparison_df['Team_Type'].isin(['User Team', 'Optimal Team Only'])].copy()
            optimal_df = optimal_df[['Rider', 'Team', 'Optimal_Team_Points']]
            optimal_df.columns = ['Rider', 'Team', 'Points']
            optimal_df = optimal_df.sort_values('Points', ascending=False)
            st.dataframe(optimal_df, use_container_width=True)
            
            total_optimal_points = optimal_df['Points'].sum()
            st.write(f"**Total Optimal Team Points:** {total_optimal_points:.2f}")
        
        # PART 2: Stage-by-Stage Analysis
        st.subheader("2. Stage-by-Stage Analysis")
        
        # Create tabs for different stage analysis views
        tab1, tab2, tab3 = st.tabs(["Overall Stage Comparison", "Stage Selection Comparison", "Bench Points Analysis"])
        
        with tab1:
            st.write("**Overall Stage-by-Stage Performance Comparison:**")
            
            # Calculate stage points for both teams
            stage_comparison_data = []
            for stage in range(1, 23):
                # User team stage points
                user_stage_points = 0
                if hasattr(results['user_team'], 'stage_selections') and results['user_team'].stage_selections and stage in results['user_team'].stage_selections:
                    # Use actual stage performance data if available
                    selected_riders = results['user_team'].stage_selections[stage]
                    for rider in selected_riders:
                        # Use actual stage performance data if available (same approach as team optimization)
                        if hasattr(results['user_team'], 'stage_performance_data') and (rider, stage) in results['user_team'].stage_performance_data:
                            user_stage_points += results['user_team'].stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to stage points if available
                            user_stage_points += results['user_team'].stage_points.get(stage, {}).get(rider, 0)
                else:
                    # Estimate based on selected riders
                    if stage == 22:
                        selected_riders = user_riders
                    else:
                        rider_expected_points = []
                        for rider in user_riders:
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                expected_points = rider_row.iloc[0]['expected_points']
                                rider_expected_points.append((rider, expected_points))
                        
                        rider_expected_points.sort(key=lambda x: x[1], reverse=True)
                        selected_riders = [rider for rider, _ in rider_expected_points[:9]]
                    
                    for rider in selected_riders:
                        # Use actual stage performance data if available
                        if hasattr(results['user_team'], 'stage_performance_data') and (rider, stage) in results['user_team'].stage_performance_data:
                            user_stage_points += results['user_team'].stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to estimated approach
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                if stage <= 21:
                                    stage_points = total_expected_points * 0.05
                                else:
                                    stage_points = total_expected_points * 0.08
                                user_stage_points += stage_points
                
                # Optimal team stage points
                optimal_stage_points = 0
                if hasattr(results['optimal_team'], 'stage_selections') and results['optimal_team'].stage_selections and stage in results['optimal_team'].stage_selections:
                    # Use actual stage performance data if available
                    selected_riders = results['optimal_team'].stage_selections[stage]
                    for rider in selected_riders:
                        if hasattr(results['optimal_team'], 'stage_performance_data') and (rider, stage) in results['optimal_team'].stage_performance_data:
                            optimal_stage_points += results['optimal_team'].stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to stage points if available
                            optimal_stage_points += results['optimal_team'].stage_points.get(stage, {}).get(rider, 0)
                else:
                    # Estimate based on selected riders
                    if stage == 22:
                        selected_riders = optimal_riders
                    else:
                        rider_expected_points = []
                        for rider in optimal_riders:
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                expected_points = rider_row.iloc[0]['expected_points']
                                rider_expected_points.append((rider, expected_points))
                        
                        rider_expected_points.sort(key=lambda x: x[1], reverse=True)
                        selected_riders = [rider for rider, _ in rider_expected_points[:9]]
                    
                    for rider in selected_riders:
                        # Use actual stage performance data if available
                        if hasattr(results['optimal_team'], 'stage_performance_data') and (rider, stage) in results['optimal_team'].stage_performance_data:
                            optimal_stage_points += results['optimal_team'].stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to estimated approach
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                if stage <= 21:
                                    stage_points = total_expected_points * 0.05
                                else:
                                    stage_points = total_expected_points * 0.08
                                optimal_stage_points += stage_points
                
                difference = user_stage_points - optimal_stage_points
                stage_comparison_data.append({
                    'Stage': stage,
                    'User_Team_Points': user_stage_points,
                    'Optimal_Team_Points': optimal_stage_points,
                    'Difference': difference
                })
            
            # Create graphical analysis
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Stage-by-Stage Points Comparison', 'Cumulative Points Comparison'),
                vertical_spacing=0.1
            )
            
            stages = [row['Stage'] for row in stage_comparison_data]
            user_points = [row['User_Team_Points'] for row in stage_comparison_data]
            optimal_points = [row['Optimal_Team_Points'] for row in stage_comparison_data]
            
            # Stage-by-stage comparison
            fig.add_trace(
                go.Bar(x=stages, y=user_points, name='User Team', marker_color='blue'),
                row=1, col=1
            )
            fig.add_trace(
                go.Bar(x=stages, y=optimal_points, name='Optimal Team', marker_color='red'),
                row=1, col=1
            )
            
            # Cumulative comparison
            cumulative_user = []
            cumulative_optimal = []
            running_user = 0
            running_optimal = 0
            
            for user_pt, optimal_pt in zip(user_points, optimal_points):
                running_user += user_pt
                running_optimal += optimal_pt
                cumulative_user.append(running_user)
                cumulative_optimal.append(running_optimal)
            
            fig.add_trace(
                go.Scatter(x=stages, y=cumulative_user, name='User Team (Cumulative)', 
                          line=dict(color='blue', width=3), mode='lines+markers'),
                row=2, col=1
            )
            fig.add_trace(
                go.Scatter(x=stages, y=cumulative_optimal, name='Optimal Team (Cumulative)', 
                          line=dict(color='red', width=3), mode='lines+markers'),
                row=2, col=1
            )
            
            fig.update_layout(height=600, showlegend=True, title_text="Stage-by-Stage Performance Analysis")
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics
            total_user_stage_points = sum(user_points)
            total_optimal_stage_points = sum(optimal_points)
            total_difference = total_user_stage_points - total_optimal_stage_points
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total User Team Points", f"{total_user_stage_points:.2f}")
            with col2:
                st.metric("Total Optimal Team Points", f"{total_optimal_stage_points:.2f}")
            with col3:
                st.metric("Difference", f"{total_difference:.2f}", delta=f"{total_difference:.2f}")
        
        with tab2:
            st.write("**Stage Selection Comparison:**")
            
            # Stage selector
            selected_stage = st.selectbox("Select Stage to Compare:", range(1, 23), format_func=lambda x: f"Stage {x}")
            
            # Get stage selections for both teams
            user_stage_riders = []
            optimal_stage_riders = []
            
            if hasattr(results['user_team'], 'stage_selections') and results['user_team'].stage_selections and selected_stage in results['user_team'].stage_selections:
                user_stage_riders = results['user_team'].stage_selections[selected_stage]
            else:
                # Estimate user team selection
                if selected_stage == 22:
                    user_stage_riders = user_riders
                else:
                    rider_expected_points = []
                    for rider in user_riders:
                        rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                        if not rider_row.empty:
                            expected_points = rider_row.iloc[0]['expected_points']
                            rider_expected_points.append((rider, expected_points))
                    
                    rider_expected_points.sort(key=lambda x: x[1], reverse=True)
                    user_stage_riders = [rider for rider, _ in rider_expected_points[:9]]
            
            if hasattr(results['optimal_team'], 'stage_selections') and results['optimal_team'].stage_selections and selected_stage in results['optimal_team'].stage_selections:
                optimal_stage_riders = results['optimal_team'].stage_selections[selected_stage]
            else:
                # Estimate optimal team selection
                if selected_stage == 22:
                    optimal_stage_riders = optimal_riders
                else:
                    rider_expected_points = []
                    for rider in optimal_riders:
                        rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                        if not rider_row.empty:
                            expected_points = rider_row.iloc[0]['expected_points']
                            rider_expected_points.append((rider, expected_points))
                    
                    rider_expected_points.sort(key=lambda x: x[1], reverse=True)
                    optimal_stage_riders = [rider for rider, _ in rider_expected_points[:9]]
            
            # Display stage selections
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User Team - Stage {selected_stage}:**")
                user_stage_data = []
                for rider in user_stage_riders:
                    rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                    team_name = rider_row.iloc[0]['team'] if not rider_row.empty else "Unknown"
                    total_expected_points = rider_row.iloc[0]['expected_points'] if not rider_row.empty else 0
                    
                    # Calculate stage-specific expected points using proper stage performance data
                    rider_obj = next((r for r in results['user_team'].riders if r.name == rider), None)
                    
                    # Use optimal team's stage performance data for consistency across all stages
                    if hasattr(results['optimal_team'], 'stage_performance_data') and (rider, selected_stage) in results['optimal_team'].stage_performance_data:
                        stage_expected_points = results['optimal_team'].stage_performance_data[(rider, selected_stage)]
                    else:
                        # Fallback to estimated approach if stage data not available
                        total_expected_points = rider_row.iloc[0]['expected_points'] if not rider_row.empty else 0
                        # Estimate stage-specific points based on total expected points
                        if selected_stage <= 21:  # Regular stages
                            stage_factor = 0.05  # 5% of total expected points per stage
                        else:  # Final stage (stage 22)
                            stage_factor = 0.08  # 8% of total expected points
                        stage_expected_points = total_expected_points * stage_factor
                    
                    # Get rider abilities for context
                    if rider_obj:
                        sprint_ability = rider_obj.parameters.sprint_ability
                        mountain_ability = rider_obj.parameters.mountain_ability
                        itt_ability = rider_obj.parameters.itt_ability
                    else:
                        sprint_ability = mountain_ability = itt_ability = 0
                    
                    user_stage_data.append({
                        'Rider': rider,
                        'Team': team_name,
                        'Stage_Points': stage_expected_points,
                        'Sprint': sprint_ability,
                        'Mountain': mountain_ability,
                        'ITT': itt_ability
                    })
                
                user_stage_df = pd.DataFrame(user_stage_data)
                user_stage_df = user_stage_df.sort_values('Stage_Points', ascending=False)
                st.dataframe(user_stage_df, use_container_width=True)
                
                total_user_stage_points = user_stage_df['Stage_Points'].sum()
                st.write(f"**Total Stage Expected Points:** {total_user_stage_points:.2f}")
            
            with col2:
                st.write(f"**Optimal Team - Stage {selected_stage}:**")
                optimal_stage_data = []
                for rider in optimal_stage_riders:
                    rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                    team_name = rider_row.iloc[0]['team'] if not rider_row.empty else "Unknown"
                    total_expected_points = rider_row.iloc[0]['expected_points'] if not rider_row.empty else 0
                    
                    # Calculate stage-specific expected points using proper stage performance data
                    rider_obj = next((r for r in results['optimal_team'].riders if r.name == rider), None)
                    
                    # Use actual stage performance data if available
                    if hasattr(results['optimal_team'], 'stage_performance_data') and (rider, selected_stage) in results['optimal_team'].stage_performance_data:
                        stage_expected_points = results['optimal_team'].stage_performance_data[(rider, selected_stage)]
                    else:
                        # Fallback to estimated approach if stage data not available
                        total_expected_points = rider_row.iloc[0]['expected_points'] if not rider_row.empty else 0
                        # Estimate stage-specific points based on total expected points
                        if selected_stage <= 21:  # Regular stages
                            stage_factor = 0.05  # 5% of total expected points per stage
                        else:  # Final stage (stage 22)
                            stage_factor = 0.08  # 8% of total expected points
                        stage_expected_points = total_expected_points * stage_factor
                    
                    # Get rider abilities for context
                    if rider_obj:
                        sprint_ability = rider_obj.parameters.sprint_ability
                        mountain_ability = rider_obj.parameters.mountain_ability
                        itt_ability = rider_obj.parameters.itt_ability
                    else:
                        sprint_ability = mountain_ability = itt_ability = 0
                    
                    optimal_stage_data.append({
                        'Rider': rider,
                        'Team': team_name,
                        'Stage_Points': stage_expected_points,
                        'Sprint': sprint_ability,
                        'Mountain': mountain_ability,
                        'ITT': itt_ability
                    })
                
                optimal_stage_df = pd.DataFrame(optimal_stage_data)
                optimal_stage_df = optimal_stage_df.sort_values('Stage_Points', ascending=False)
                st.dataframe(optimal_stage_df, use_container_width=True)
                
                total_optimal_stage_points = optimal_stage_df['Stage_Points'].sum()
                st.write(f"**Total Stage Expected Points:** {total_optimal_stage_points:.2f}")
            
            # Show differences
            st.write("**Selection Differences:**")
            user_only = set(user_stage_riders) - set(optimal_stage_riders)
            optimal_only = set(optimal_stage_riders) - set(user_stage_riders)
            common = set(user_stage_riders) & set(optimal_stage_riders)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Common Riders ({len(common)}):**")
                for rider in sorted(common):
                    st.write(f"• {rider}")
            
            with col2:
                st.write(f"**User Team Only ({len(user_only)}):**")
                for rider in sorted(user_only):
                    st.write(f"• {rider}")
            
            with col3:
                st.write(f"**Optimal Team Only ({len(optimal_only)}):**")
                for rider in sorted(optimal_only):
                    st.write(f"• {rider}")
        
        with tab3:
            st.write("**Bench Points Analysis - Stage by Stage:**")
            
            # Calculate bench points for both teams stage by stage
            bench_data = []
            
            for stage in range(1, 23):
                # User team bench points
                if hasattr(results['user_team'], 'stage_selections') and results['user_team'].stage_selections and stage in results['user_team'].stage_selections:
                    selected_riders = results['user_team'].stage_selections[stage]
                else:
                    # Estimate selected riders
                    if stage == 22:
                        selected_riders = user_riders
                    else:
                        rider_expected_points = []
                        for rider in user_riders:
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                expected_points = rider_row.iloc[0]['expected_points']
                                rider_expected_points.append((rider, expected_points))
                        
                        rider_expected_points.sort(key=lambda x: x[1], reverse=True)
                        selected_riders = [rider for rider, _ in rider_expected_points[:9]]
                
                user_bench_points = 0
                for rider in user_riders:
                    if rider not in selected_riders:
                        # Use optimal team's stage performance data for consistency
                        if hasattr(results['optimal_team'], 'stage_performance_data') and (rider, stage) in results['optimal_team'].stage_performance_data:
                            stage_expected_points = results['optimal_team'].stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to estimated approach if stage data not available
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                if stage <= 21:
                                    stage_expected_points = total_expected_points * 0.05
                                else:
                                    stage_expected_points = total_expected_points * 0.08
                            else:
                                stage_expected_points = 0
                        user_bench_points += stage_expected_points
                
                # Optimal team bench points
                if hasattr(results['optimal_team'], 'stage_selections') and results['optimal_team'].stage_selections and stage in results['optimal_team'].stage_selections:
                    selected_riders = results['optimal_team'].stage_selections[stage]
                else:
                    # Estimate selected riders
                    if stage == 22:
                        selected_riders = optimal_riders
                    else:
                        rider_expected_points = []
                        for rider in optimal_riders:
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                expected_points = rider_row.iloc[0]['expected_points']
                                rider_expected_points.append((rider, expected_points))
                        
                        rider_expected_points.sort(key=lambda x: x[1], reverse=True)
                        selected_riders = [rider for rider, _ in rider_expected_points[:9]]
                
                optimal_bench_points = 0
                for rider in optimal_riders:
                    if rider not in selected_riders:
                        # Use actual stage performance data if available
                        if hasattr(results['optimal_team'], 'stage_performance_data') and (rider, stage) in results['optimal_team'].stage_performance_data:
                            stage_expected_points = results['optimal_team'].stage_performance_data[(rider, stage)]
                        else:
                            # Fallback to estimated approach if stage data not available
                            rider_row = results['rider_data'][results['rider_data']['rider_name'] == rider]
                            if not rider_row.empty:
                                total_expected_points = rider_row.iloc[0]['expected_points']
                                if stage <= 21:
                                    stage_expected_points = total_expected_points * 0.05
                                else:
                                    stage_expected_points = total_expected_points * 0.08
                            else:
                                stage_expected_points = 0
                        optimal_bench_points += stage_expected_points
                
                bench_data.append({
                    'Stage': stage,
                    'User_Team_Bench_Points': user_bench_points,
                    'Optimal_Team_Bench_Points': optimal_bench_points,
                    'Bench_Points_Difference': user_bench_points - optimal_bench_points
                })
            
            # Create bench points visualization
            bench_df = pd.DataFrame(bench_data)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=bench_df['Stage'],
                y=bench_df['User_Team_Bench_Points'],
                name='User Team Bench Points',
                marker_color='lightblue'
            ))
            fig.add_trace(go.Bar(
                x=bench_df['Stage'],
                y=bench_df['Optimal_Team_Bench_Points'],
                name='Optimal Team Bench Points',
                marker_color='lightcoral'
            ))
            
            fig.update_layout(
                title="Bench Points by Stage",
                xaxis_title="Stage",
                yaxis_title="Bench Points",
                barmode='group'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display bench points table
            st.write("**Bench Points Summary:**")
            st.dataframe(bench_df, use_container_width=True)
            
            # Summary statistics
            total_user_bench = bench_df['User_Team_Bench_Points'].sum()
            total_optimal_bench = bench_df['Optimal_Team_Bench_Points'].sum()
            total_bench_difference = total_user_bench - total_optimal_bench
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total User Team Bench Points", f"{total_user_bench:.2f}")
            with col2:
                st.metric("Total Optimal Team Bench Points", f"{total_optimal_bench:.2f}")
            with col3:
                st.metric("Bench Points Difference", f"{total_bench_difference:.2f}", delta=f"{total_bench_difference:.2f}")
        
        # Show rider performance comparison
        st.subheader("Rider Performance Comparison")
        
        # Get rider data for comparison
        rider_data = results['rider_data']
        
        # Compare selected riders
        user_riders = comparison['user_team']['rider_names']
        optimal_riders = comparison['optimal_team']['rider_names']
        
        # Find common riders
        common_riders = set(user_riders) & set(optimal_riders)
        user_only = set(user_riders) - set(optimal_riders)
        optimal_only = set(optimal_riders) - set(user_riders)
        
        if common_riders:
            st.write("**Riders in both teams:**")
            for rider in sorted(common_riders):
                rider_row = rider_data[rider_data['rider_name'] == rider]
                if not rider_row.empty:
                    expected_points = rider_row.iloc[0]['expected_points']
                    st.write(f"• {rider}: {expected_points:.2f} expected points")
        
        if user_only:
            st.write("**Riders only in your team:**")
            for rider in sorted(user_only):
                rider_row = rider_data[rider_data['rider_name'] == rider]
                if not rider_row.empty:
                    expected_points = rider_row.iloc[0]['expected_points']
                    st.write(f"• {rider}: {expected_points:.2f} expected points")
        
        if optimal_only:
            st.write("**Riders only in optimal team:**")
            for rider in sorted(optimal_only):
                rider_row = rider_data[rider_data['rider_name'] == rider]
                if not rider_row.empty:
                    expected_points = rider_row.iloc[0]['expected_points']
                    st.write(f"• {rider}: {expected_points:.2f} expected points")
        
        # Clear results button
        if st.button("Clear Results"):
            st.session_state['versus_results'] = None
            st.rerun()

if __name__ == "__main__":
    main() 