import streamlit as st
import pandas as pd
import plotly.express as px
from riders import RiderDatabase
from tno_optimizer import TNOTeamOptimizer, TNOTeamOptimization

st.set_page_config(
    page_title="Team Optimization - T(n)oer Game",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Team Optimization")
st.markdown("""
Find the optimal team selection and rider order for maximum points using advanced optimization algorithms.
The optimizer considers rider abilities, stage profiles, and T(n)oer Game scoring rules.
""")

# Optimization settings
st.header("1. Optimization Settings")

col1, col2, col3 = st.columns(3)

with col1:
    team_size = st.number_input(
        "Team Size",
        min_value=15,
        max_value=25,
        value=20,
        help="Number of riders to select (T(n)oer Game uses 20)"
    )

with col2:
    rider_simulations = st.number_input(
        "Rider Analysis Simulations",
        min_value=10,
        max_value=5000,
        value=30,
        help="Number of simulations to analyze individual rider performance"
    )

with col3:
    optimization_simulations = st.number_input(
        "Optimization Simulations",
        min_value=10,
        max_value=5000,
        value=30,
        help="Number of simulations to validate optimized team"
    )

# Advanced settings
with st.expander("🔧 Advanced Settings"):
    col1, col2 = st.columns(2)
    
    with col1:
        include_abandonment = st.checkbox("Include Abandonment Risk", value=True)
        weight_bonus_riders = st.checkbox("Optimize Bonus Rider Order", value=True)
    
    with col2:
        max_optimization_time = st.number_input(
            "Max Optimization Time (seconds)",
            min_value=30,
            max_value=300,
            value=120,
            help="Maximum time to spend on optimization"
        )

# Run optimization
st.header("2. Run Optimization")

if st.button("🚀 Start Optimization", type="primary"):
    with st.spinner("Running optimization... This may take a few minutes."):
        try:
            # Initialize optimizer
            optimizer = TNOTeamOptimizer(team_size=team_size)
            
            # Step 1: Analyze individual riders
            st.info("Step 1/3: Analyzing individual rider performance...")
            rider_data = optimizer.run_simulation_for_riders(num_simulations=rider_simulations)
            
            # Step 2: Optimize team selection and order
            st.info("Step 2/3: Optimizing team selection and rider order...")
            optimization = optimizer.optimize_team_with_order(
                rider_data, 
                num_simulations=optimization_simulations
            )
            
            # Step 3: Validate results
            st.info("Step 3/3: Validating optimized team...")
            
            # Store results
            st.session_state.optimization_results = {
                'optimization': optimization,
                'rider_data': rider_data,
                'settings': {
                    'team_size': team_size,
                    'rider_sims': rider_simulations,
                    'opt_sims': optimization_simulations
                }
            }
            
            st.success("✅ Optimization completed successfully!")
            
        except Exception as e:
            st.error(f"❌ Optimization failed: {str(e)}")
            st.exception(e)

# Display results
if 'optimization_results' in st.session_state:
    st.header("3. Optimization Results")
    
    results = st.session_state.optimization_results
    optimization = results['optimization']
    rider_data = results['rider_data']
    settings = results['settings']
    
    # Key metrics
    st.subheader("📊 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Expected Points", f"{optimization.expected_points:.1f}")
    
    with col2:
        st.metric("Team Size", optimization.team_size)
    
    with col3:
        team_cost = sum(rider_db.get_rider(name).price for name in optimization.rider_order)
        st.metric("Team Cost", f"${team_cost:.2f}")
    
    with col4:
        st.metric("Optimization Time", f"{settings.get('optimization_time', 'N/A')}")
    
    # Optimized team
    st.subheader("🏆 Optimized Team")
    
    # Create team summary
    team_summary = []
    for i, rider_name in enumerate(optimization.rider_order):
        rider_obj = rider_db.get_rider(rider_name)
        team_summary.append({
            "Position": i + 1,
            "Rider": rider_name,
            "Team": rider_obj.team,
            "Price": rider_obj.price,
            "Age": rider_obj.age,
            "Role": "BONUS" if i < 5 else "SCORING" if i < 15 else "RESERVE",
            "Expected Points": rider_data.get(rider_name, {}).get('expected_points', 0)
        })
    
    team_df = pd.DataFrame(team_summary)
    st.dataframe(team_df, hide_index=True)
    
    # Team composition analysis
    st.subheader("📈 Team Composition Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Role distribution
        role_counts = team_df['Role'].value_counts()
        fig = px.pie(
            values=role_counts.values,
            names=role_counts.index,
            title="Team Role Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Team distribution
        team_counts = team_df['Team'].value_counts().head(10)
        fig = px.bar(
            x=team_counts.index,
            y=team_counts.values,
            title="Top 10 Teams by Rider Count",
            labels={'x': 'Team', 'y': 'Number of Riders'}
        )
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)
    
    # Rider performance analysis
    st.subheader("🏃‍♂️ Rider Performance Analysis")
    
    # Top performers in optimized team
    top_performers = sorted(
        [(rider, data.get('expected_points', 0)) for rider, data in rider_data.items()],
        key=lambda x: x[1],
        reverse=True
    )[:15]
    
    top_df = pd.DataFrame([
        {
            "Rider": rider,
            "Expected Points": points,
            "In Optimized Team": rider in optimization.rider_order,
            "Position": optimization.rider_order.index(rider) + 1 if rider in optimization.rider_order else "Not Selected"
        }
        for rider, points in top_performers
    ])
    
    st.dataframe(top_df, hide_index=True)
    
    # Bonus riders analysis
    st.subheader("⭐ Bonus Riders Analysis")
    
    bonus_riders = optimization.rider_order[:5]
    bonus_data = []
    
    for i, rider in enumerate(bonus_riders):
        rider_obj = rider_db.get_rider(rider)
        bonus_potential = rider_data.get(rider, {}).get('bonus_potential', 0)
        bonus_data.append({
            "Position": i + 1,
            "Rider": rider,
            "Team": rider_obj.team,
            "Bonus Potential": bonus_potential,
            "Expected Points": rider_data.get(rider, {}).get('expected_points', 0)
        })
    
    bonus_df = pd.DataFrame(bonus_data)
    st.dataframe(bonus_df, hide_index=True)
    
    # Bonus potential chart
    fig = px.bar(
        bonus_df,
        x='Rider',
        y='Bonus Potential',
        title="Bonus Potential of Top 5 Riders",
        labels={'Bonus Potential': 'Expected Top 10 Finishes', 'Rider': 'Rider Name'}
    )
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Cost analysis
    st.subheader("💰 Cost Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Price distribution
        fig = px.histogram(
            team_df,
            x='Price',
            nbins=10,
            title="Price Distribution of Selected Riders"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Price vs Expected Points
        fig = px.scatter(
            team_df,
            x='Price',
            y='Expected Points',
            hover_data=['Rider', 'Team'],
            title="Price vs Expected Points"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Download results
    st.subheader("💾 Download Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Download Optimized Team"):
            # Create team CSV
            team_csv = team_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Team CSV",
                data=team_csv,
                file_name=f"tnoer_game_optimized_team_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("Download Full Analysis"):
            # Create comprehensive analysis
            analysis_data = []
            
            # Add team data
            for _, row in team_df.iterrows():
                analysis_data.append({
                    'Type': 'Team Selection',
                    'Position': row['Position'],
                    'Rider': row['Rider'],
                    'Team': row['Team'],
                    'Price': row['Price'],
                    'Role': row['Role'],
                    'Expected Points': row['Expected Points']
                })
            
            # Add rider analysis data
            for rider, data in rider_data.items():
                analysis_data.append({
                    'Type': 'Rider Analysis',
                    'Rider': rider,
                    'Expected Points': data.get('expected_points', 0),
                    'Bonus Potential': data.get('bonus_potential', 0),
                    'Abandonment Risk': data.get('abandonment_risk', 0)
                })
            
            analysis_df = pd.DataFrame(analysis_data)
            analysis_csv = analysis_df.to_csv(index=False)
            
            st.download_button(
                label="📥 Download Full Analysis",
                data=analysis_csv,
                file_name=f"tnoer_game_full_analysis_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

# Load rider database for reference
rider_db = RiderDatabase() 