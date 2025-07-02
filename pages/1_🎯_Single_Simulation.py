import warnings
import logging
import os

# Suppress Streamlit ScriptRunContext warnings
warnings.filterwarnings("ignore", message=".*ScriptRunContext.*")
warnings.filterwarnings("ignore", category=UserWarning)

# Configure logging to suppress warnings
logging.getLogger('streamlit').setLevel(logging.ERROR)
logging.getLogger('streamlit.runtime.scriptrunner_utils').setLevel(logging.ERROR)

# Set environment variables to suppress warnings
os.environ['PYTHONWARNINGS'] = 'ignore'

import streamlit as st
import pandas as pd
from riders import RiderDatabase
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection

st.set_page_config(
    page_title="Single Simulation - T(n)oer Game",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Single Simulation")
st.markdown("""
Demonstrate the functionality of the T(n)oer Game simulation engine. 
Run a single tour simulation with your selected team and see detailed results.
""")

# Load rider database
rider_db = RiderDatabase()
all_riders = rider_db.get_all_riders()
rider_names = [r.name for r in all_riders]

# Team selection
st.header("1. Select Your Team")

col1, col2 = st.columns([2, 1])

with col1:
    selected_riders = st.multiselect(
        "Choose 20 unique riders",
        options=rider_names,
        default=rider_names[:20],
        max_selections=20,
        help="Select exactly 20 riders for your team"
    )

with col2:
    st.info(f"**Selected:** {len(selected_riders)}/20 riders")
    if len(selected_riders) == 20:
        st.success("✅ Team complete!")
    else:
        st.warning("⚠️ Please select exactly 20 riders")

# Rider ordering
if len(selected_riders) == 20:
    st.header("2. Set Rider Order")
    st.markdown("The order is crucial for T(n)oer Game! The first 5 riders get bonus points, first 15 are scoring riders.")
    
    # Create a clearer ordering interface with place numbers
    st.subheader("Select riders in order (1-20):")
    
    ordered_riders = []
    used = set()
    
    # Create a more organized layout
    for row in range(5):  # 5 rows
        cols = st.columns(4)
        for col in range(4):  # 4 columns
            position = row * 4 + col + 1
            if position <= 20:
                with cols[col]:
                    options = [r for r in selected_riders if r not in used]
                    if options:
                        # Add place number to the label
                        role = "BONUS" if position <= 5 else "SCORING" if position <= 15 else "RESERVE"
                        rider = st.selectbox(
                            f"#{position} ({role})", 
                            options, 
                            key=f"order_{position-1}",
                            help=f"Position {position}: {role} rider"
                        )
                        ordered_riders.append(rider)
                        used.add(rider)
    
    # Display the ordered list
    if len(ordered_riders) == 20:
        st.subheader("Your Rider Order:")
        order_list = []
        for i, rider in enumerate(ordered_riders):
            role = "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE"
            order_list.append(f"**{i+1}.** {rider} ({role})")
        
        # Display in columns for better readability
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Bonus Riders (1-5):**")
            for item in order_list[:5]:
                st.markdown(item)
            st.markdown("**Scoring Riders (6-15):**")
            for item in order_list[5:15]:
                st.markdown(item)
        with col2:
            st.markdown("**Reserve Riders (16-20):**")
            for item in order_list[15:]:
                st.markdown(item)
    
    # Display team summary
    st.header("3. Your Team Summary")
    
    team_summary = []
    for i, rider in enumerate(ordered_riders):
        rider_obj = rider_db.get_rider(rider)
        team_summary.append({
            "Position": i + 1,
            "Rider": rider,
            "Team": rider_obj.team,
            "Role": "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE"
        })
    
    team_df = pd.DataFrame(team_summary)
    st.dataframe(team_df, hide_index=True)
    
    # Simulation controls
    st.header("4. Run Simulation")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Run Single Simulation", type="primary"):
            with st.spinner("Running simulation..."):
                # Create team
                team_objs = [rider_db.get_rider(name) for name in ordered_riders]
                team = TNOTeamSelection(team_objs)
                
                # Run simulation
                simulator = TNOSimulator(team)
                simulator.simulate_tour()
                
                # Get results
                team_perf = simulator.get_team_performance()
                
                # Store results in session state
                st.session_state.simulation_results = {
                    'team_perf': team_perf,
                    'simulator': simulator,
                    'team': team
                }
                
                st.success("Simulation completed!")
    
    # Display results
    if 'simulation_results' in st.session_state:
        st.header("5. Simulation Results")
        
        results = st.session_state.simulation_results
        team_perf = results['team_perf']
        simulator = results['simulator']
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Points", f"{team_perf['total_points']}")
        
        with col2:
            riders_remaining = 20 - team_perf['abandonments']
            st.metric("Riders Remaining", riders_remaining)
        
        with col3:
            st.metric("Abandonments", team_perf['abandonments'])
        
        with col4:
            st.metric("Team Cost", f"${team_perf['team_cost']:.2f}")
        
        # Top performers
        st.subheader("🏆 Top Performers")
        
        # Get top performers from TNO points
        final_tno_points = simulator.get_final_tno_points()
        team_riders_set = set(ordered_riders)
        
        # Filter to only show team riders
        team_top_performers = [(rider, points) for rider, points in final_tno_points if rider in team_riders_set]
        
        if team_top_performers:
            top_df = pd.DataFrame([
                {
                    "Rider": rider,
                    "Points": points,
                    "Position": i + 1
                }
                for i, (rider, points) in enumerate(team_top_performers[:10])
            ])
            st.dataframe(top_df, hide_index=True)
        
        # Stage-by-stage results
        st.subheader("📊 Stage-by-Stage Results")
        if hasattr(simulator, 'stage_results_records') and simulator.stage_results_records:
            stage_df = pd.DataFrame(simulator.stage_results_records)
            st.dataframe(stage_df, hide_index=True)
        
        # Abandonments
        if team_perf['abandonments'] > 0:
            st.subheader("💥 Abandonments")
            st.warning(f"{team_perf['abandonments']} riders abandoned during the tour")
            
            # Show which riders abandoned
            abandoned_team_riders = []
            for rider_name in ordered_riders:
                if rider_name in simulator.abandoned_riders:
                    abandoned_team_riders.append(rider_name)
            
            if abandoned_team_riders:
                st.write("**Abandoned riders:**")
                for rider in abandoned_team_riders:
                    st.write(f"- {rider}")
        else:
            st.success("✅ No riders abandoned during the tour!")
        
        # Download results
        st.subheader("💾 Download Results")
        if st.button("Download Simulation Results"):
            # Create comprehensive results DataFrame
            results_data = []
            for record in simulator.stage_results_records:
                results_data.append(record)
            
            results_df = pd.DataFrame(results_data)
            
            # Convert to CSV
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name=f"tnoer_game_simulation_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

else:
    st.info("Please select exactly 20 riders to proceed with the simulation.") 