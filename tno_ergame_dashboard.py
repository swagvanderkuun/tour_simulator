import streamlit as st
import pandas as pd
from riders import RiderDatabase
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
from tno_optimizer import TNOTeamOptimizer
from tno_ergame_multi_simulator import TNOMultiSimulationAnalyzer

st.set_page_config(
    page_title="TNO-Ergame Team Optimizer",
    page_icon="🚴‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚴‍♂️ TNO-Ergame Team Optimizer Dashboard")
st.markdown("""
This dashboard allows you to build and analyze your TNO-Ergame fantasy cycling team. Select 20 riders, set their order, run simulations, and optimize your team!
""")

# Load rider database
rider_db = RiderDatabase()
all_riders = rider_db.get_all_riders()
rider_names = [r.name for r in all_riders]

# --- Sidebar: Team Selection ---
st.sidebar.header("1. Select Your 20 Riders")
selected_riders = st.sidebar.multiselect(
    "Choose 20 unique riders (no budget)",
    options=rider_names,
    default=rider_names[:20],
    max_selections=20
)

if len(selected_riders) != 20:
    st.warning("Please select exactly 20 unique riders.")
    st.stop()

# --- Sidebar: Rider Order ---
st.sidebar.header("2. Set Rider Order (Drag or Select)")
order_indices = list(range(1, 21))
def_order = {i: selected_riders[i-1] for i in order_indices}

# Use a simple selectbox for each position (drag-and-drop would require a custom component)
ordered_riders = []
used = set()
for i in order_indices:
    options = [r for r in selected_riders if r not in used]
    rider = st.sidebar.selectbox(f"{i}. Rider", options, key=f"order_{i}")
    ordered_riders.append(rider)
    used.add(rider)

# --- Main: Show Team Table ---
st.subheader("Your Team & Order")
team_df = pd.DataFrame({
    "Order": list(range(1, 21)),
    "Rider": ordered_riders
})
st.dataframe(team_df, hide_index=True)

# --- Main: Actions ---
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Run Single Simulation"):
        team_objs = [rider_db.get_rider(name) for name in ordered_riders]
        team = TNOTeamSelection(team_objs)
        simulator = TNOSimulator(team)
        simulator.simulate_tour()
        team_perf = simulator.get_team_performance()
        st.success(f"Total Points: {team_perf['total_points']}")
        st.write("Top Performers:", team_perf['top_performers'])
        st.write("Abandonments:", team_perf['abandonments'])
        st.write("Riders Remaining:", team_perf['riders_remaining'])
        st.write("Team Cost (for info):", team_perf['team_cost'])
        st.dataframe(pd.DataFrame(simulator.stage_results_records))

with col2:
    num_sims = st.number_input("Number of Simulations", min_value=10, max_value=200, value=50)
    if st.button("Run Multi-Simulation Analysis"):
        team_objs = [rider_db.get_rider(name) for name in ordered_riders]
        team = TNOTeamSelection(team_objs)
        analyzer = TNOMultiSimulationAnalyzer(num_sims)
        metrics = analyzer.run_simulations(team)
        st.success(f"Average Points: {metrics['team_performance']['total_points']['mean']:.1f} ± {metrics['team_performance']['total_points']['std']:.1f}")
        st.write("Abandonments (avg):", metrics['team_performance']['abandonments']['mean'])
        st.write("Top Expected Performers:")
        top_scorers = metrics['tno_analysis']['top_scorers']
        st.dataframe(pd.DataFrame([
            {"Rider": k, **v} for k, v in list(top_scorers.items())[:10]
        ]))

with col3:
    if st.button("Optimize Team & Order"):
        optimizer = TNOTeamOptimizer(team_size=20)
        rider_data = optimizer.run_simulation_for_riders(num_simulations=30)
        optimization = optimizer.optimize_team_with_order(rider_data, num_simulations=30)
        st.success(f"Optimized Expected Points: {optimization.expected_points:.1f}")
        st.write("Optimized Rider Order:")
        st.dataframe(pd.DataFrame({
            "Order": list(range(1, 21)),
            "Rider": optimization.rider_order
        }))
        st.write("Top 5 Bonus Riders:", optimization.rider_order[:5])
        st.write("Scoring Riders:", optimization.rider_order[:15])
        st.write("Reserves:", optimization.rider_order[15:])

st.info("""
- **Single Simulation**: Simulate your team for one Tour.
- **Multi-Simulation**: Run many simulations to see average performance.
- **Optimize**: Find the best team and order for maximum points.
""") 