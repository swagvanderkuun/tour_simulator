# TNO-Ergame Team Optimizer

A comprehensive team optimization system for the TNO-Ergame fantasy cycling game, built on top of the Tour de France simulator.

## 🎯 Game Rules

TNO-Ergame is a fantasy cycling game with the following rules:

### Team Selection
- **Team Size**: 20 riders
- **Budget**: 48 points
- **Team Limit**: Maximum 4 riders per team

### Scoring System
- **Scoring Riders**: First 15 riders in your selection can score points
- **Reserve Riders**: Last 5 riders are reserves (cannot score points)
- **Bonus Points**: First 5 riders get bonus points when finishing top 10:
  - 1st rider: 5 bonus points
  - 2nd rider: 4 bonus points
  - 3rd rider: 3 bonus points
  - 4th rider: 2 bonus points
  - 5th rider: 1 bonus point

### Point System
**Regular Stages (1-4, 6-12, 15-16, 19-21):**
- 1st: 20 points
- 2nd: 15 points
- 3rd: 12 points
- 4th: 9 points
- 5th: 7 points
- 6th: 5 points
- 7th: 4 points
- 8th: 3 points
- 9th: 2 points
- 10th: 1 point

**Special Stages (5, 13, 14, 17, 18):**
- 1st: 30 points
- 2nd: 20 points
- 3rd: 15 points
- 4th: 12 points
- 5th: 10 points
- 6th: 8 points
- 7th: 6 points
- 8th: 4 points
- 9th: 2 points
- 10th: 1 point

### Abandonment Rules
- When a scoring rider abandons, the next reserve rider moves up to become a scoring rider
- When a bonus rider abandons, all riders below move up one position in the bonus system
- Example: If 3rd rider abandons, 6th rider becomes 5th, 5th becomes 4th, 4th becomes 3rd

## 🏗️ System Architecture

### Core Components

#### 1. TNO-Ergame Simulator (`tno_ergame_simulator.py`)
- **Complete Tour Simulation**: Simulates all 21 stages with TNO-Ergame rules
- **Team Management**: Handles rider order, scoring riders, and reserves
- **Abandonment Logic**: Manages rider replacements and bonus position shifts
- **Point Calculation**: Implements the TNO-Ergame point system
- **Special Stages**: Different point values for stages 5, 13, 14, 17, 18

#### 2. Multi-Simulation Analyzer (`tno_ergame_multi_simulator.py`)
- **Statistical Analysis**: Runs hundreds of simulations for probability analysis
- **Performance Metrics**: Calculates expected points, standard deviations, confidence intervals
- **Team Performance**: Analyzes overall team performance across simulations
- **Rider Analysis**: Individual rider performance within team context

#### 3. Team Optimizer (`tno_optimizer.py`)
- **Two-Phase Optimization**: 
  - Phase 1: Select optimal 20 riders using Integer Linear Programming
  - Phase 2: Optimize rider order for maximum bonus points
- **Budget Constraints**: Ensures team stays within 48-point budget
- **Risk Management**: Configurable risk aversion and abandon penalties
- **Alternative Teams**: Generates multiple optimal team suggestions

## 🚀 Usage

### Quick Start

```python
from tno_optimizer import TNOTeamOptimizer
from riders import RiderDatabase

# Create optimizer
optimizer = TNOTeamOptimizer(budget=48.0, team_size=20)

# Get rider performance data
rider_data = optimizer.run_simulation_for_riders(num_simulations=100)

# Optimize team
optimization = optimizer.optimize_team_with_order(rider_data, num_simulations=50)

# Print results
print(f"Expected Points: {optimization.expected_points:.1f}")
print(f"Total Cost: {optimization.total_cost:.2f}")
print(f"Rider Order: {optimization.rider_order}")
```

### Running Tests

```bash
# Run the test script
python test_tno_ergame.py
```

This will:
1. Test basic simulation functionality
2. Run multi-simulation analysis
3. Test the optimizer
4. Generate Excel files with results

### Individual Components

#### Basic Simulation
```python
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection
from riders import RiderDatabase

# Create team
rider_db = RiderDatabase()
all_riders = rider_db.get_all_riders()
team = TNOTeamSelection(all_riders[:20])

# Run simulation
simulator = TNOSimulator(team)
simulator.simulate_tour()

# Get results
final_points = simulator.get_final_tno_points()
team_performance = simulator.get_team_performance()
```

#### Multi-Simulation Analysis
```python
from tno_ergame_multi_simulator import TNOMultiSimulationAnalyzer

# Create analyzer
analyzer = TNOMultiSimulationAnalyzer(100)
metrics = analyzer.run_simulations(team)

# Get expected points for optimization
expected_points_df = analyzer.get_rider_expected_points()
```

## 📊 Output Files

The system generates several output files:

### Simulation Results (`tno_ergame_simulation_results.xlsx`)
- **Stage_Results**: Stage-by-stage performance for each rider
- **GC_Standings**: General Classification standings
- **TNO_Points**: TNO-Ergame points for each rider
- **Team_Performance**: Overall team performance summary
- **Rider_Database**: Complete rider information

### Optimization Results (`tno_ergame_optimization_results.xlsx`)
- **Team_Summary**: Optimized team statistics
- **Rider_Order**: Complete rider order with bonus and scoring information
- **Rider_Performance**: Expected performance data for all riders

### Multi-Simulation Metrics (`tno_ergame_multi_simulation_metrics.json`)
- Statistical analysis results
- Performance distributions
- Confidence intervals

## 🎛️ Configuration

### Optimizer Parameters

```python
optimizer = TNOTeamOptimizer(
    budget=48.0,           # Team budget
    team_size=20,          # Number of riders
    scoring_riders=15,     # Number of scoring riders
    bonus_riders=5         # Number of bonus riders
)
```

### Optimization Parameters

```python
optimization = optimizer.optimize_team_with_order(
    rider_data,
    num_simulations=50,    # Simulations for analysis
    risk_aversion=0.0,     # Penalty for high variance (0-1)
    abandon_penalty=1.0    # Penalty for high abandon probability (0-1)
)
```

## 🔧 Advanced Features

### Risk Management
- **Risk Aversion**: Penalize riders with high performance variance
- **Abandon Penalty**: Reduce expected points based on abandon probability
- **Team Diversity**: Ensure balanced team composition

### Alternative Teams
```python
# Generate alternative team selections
alternatives = optimizer.get_alternative_teams(
    rider_data, 
    num_alternatives=5,
    num_simulations=50
)

for i, alt in enumerate(alternatives, 1):
    print(f"Alternative {i}: {alt.expected_points:.1f} points")
```

### Custom Team Analysis
```python
# Analyze a specific team
from tno_ergame_simulator import TNOSimulator, TNOTeamSelection

# Create custom team
custom_riders = [rider1, rider2, ...]  # Your selected riders
custom_team = TNOTeamSelection(custom_riders)

# Run analysis
simulator = TNOSimulator(custom_team)
simulator.simulate_tour()
performance = simulator.get_team_performance()
```

## 📈 Performance Monitoring

The system tracks:
- **Average Points**: Expected team performance
- **Abandonment Rate**: Risk assessment
- **Bonus Point Efficiency**: How well bonus positions are utilized
- **Stage Performance**: Performance across different stage types
- **Team Cost Efficiency**: Points per budget unit

## 🛠️ Dependencies

- **Python 3.8+**
- **Pandas**: Data manipulation
- **NumPy**: Numerical computations
- **PuLP**: Integer Linear Programming optimization
- **OpenPyXL**: Excel file generation
- **Tour Simulator**: Base simulation engine

## 🎯 Optimization Strategy

The optimizer uses a sophisticated two-phase approach:

### Phase 1: Rider Selection
- Uses Integer Linear Programming to select optimal 20 riders
- Considers expected points, risk, and abandon probability
- Ensures budget and team constraints are met

### Phase 2: Rider Ordering
- Optimizes rider order for maximum bonus points
- Considers bonus potential and scoring rider status
- Balances immediate performance with long-term strategy

## 🔮 Future Enhancements

- **Machine Learning**: Predict rider performance using historical data
- **Real-time Updates**: Live rider parameter updates during the tour
- **Web Interface**: Streamlit dashboard for TNO-Ergame
- **Advanced Analytics**: More sophisticated performance metrics
- **Team Comparison**: Head-to-head team analysis

## 📝 Notes

- The system uses the same rider database as the main Tour de France simulator
- All simulations include realistic crash and abandonment mechanics
- Special stages (5, 13, 14, 17, 18) have enhanced point values
- The optimizer considers the complex interaction between rider selection and order
- Results are saved in Excel format for easy analysis

## 🤝 Contributing

This system is built on top of the existing Tour de France simulator. To contribute:
1. Understand the base simulator architecture
2. Follow the established patterns for new features
3. Test thoroughly with the provided test scripts
4. Document any new functionality

---

**TNO-Ergame Team Optimizer** - Your secret weapon for dominating the TNO-Ergame fantasy cycling competition! 🚴‍♂️🏆 