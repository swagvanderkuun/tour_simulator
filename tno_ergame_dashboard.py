import streamlit as st
import pandas as pd
from riders import RiderDatabase

st.set_page_config(
    page_title="T(n)oer Game Team Optimizer",
    page_icon="🚴‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚴‍♂️ T(n)oer Game Team Optimizer")
st.markdown("""
Welcome to the T(n)oer Game Team Optimizer! This comprehensive dashboard helps you build and analyze your fantasy cycling team.

## Available Pages:

### 🎯 **Single Simulation**
Demonstrate the functionality of the simulation engine. Run a single tour simulation with your selected team and see detailed results.

### 📊 **Multi-Simulation Analysis** 
Explore statistics and performance metrics by running multiple simulations. Get insights into expected performance and variance.

### ⚡ **Team Optimization**
Find the optimal team selection and rider order for maximum points using advanced optimization algorithms.

### 🔄 **Compare Strategies**
Compare different optimization strategies and see how they perform against each other.

### 🥊 **VS Mode**
Test your manually selected team against optimal teams and see how you stack up!

---

**How to use:**
1. Start with **Single Simulation** to understand how the game works
2. Use **Multi-Simulation** to explore your team's expected performance
3. Try **Team Optimization** to find the best possible team
4. Compare different approaches in **Compare Strategies**
5. Challenge yourself in **VS Mode**

Select a page from the sidebar to get started!
""")

# Load rider database for quick stats
rider_db = RiderDatabase()
all_riders = rider_db.get_all_riders()

# Display some quick stats
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Riders Available", len(all_riders))
    
with col2:
    teams = len(set(r.team for r in all_riders))
    st.metric("Teams Represented", teams)
    
with col3:
    avg_age = sum(r.age for r in all_riders) / len(all_riders)
    st.metric("Average Rider Age", f"{avg_age:.1f}")

# Show top riders by price
st.subheader("🏆 Top Riders by Price")
top_riders = sorted(all_riders, key=lambda x: x.price, reverse=True)[:10]
top_riders_df = pd.DataFrame([
    {
        "Rider": r.name,
        "Team": r.team,
        "Price": r.price,
        "Age": r.age,
        "Sprint": r.parameters.sprint_ability,
        "Mountain": r.parameters.mountain_ability,
        "ITT": r.parameters.itt_ability
    }
    for r in top_riders
])
st.dataframe(top_riders_df, hide_index=True)

st.info("💡 **Tip**: Use the sidebar to navigate between different functionalities and explore the full potential of your T(n)oer Game team!") 