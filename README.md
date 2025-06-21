# Tour de France Cycling Simulator

A comprehensive cycling simulation and team optimization tool for Tour de France fantasy cycling games.

## Features

- **Tour Simulation**: Complete 21-stage Tour de France simulation with realistic stage types and classifications
- **Multi-Simulation Analysis**: Run hundreds of simulations to analyze performance patterns and probabilities
- **Team Optimization**: Advanced optimization algorithms to select optimal teams within budget constraints
- **Rider Management**: View, edit, and add riders with their performance parameters
- **Results Analysis**: Comprehensive analysis and visualization of simulation results
- **Data Export**: Export results to Excel for further analysis

## Dashboard

The project includes a comprehensive Streamlit dashboard (`dashboard.py`) that provides:

- **Overview**: Project summary and quick access to all features
- **Single Simulation**: Run individual tour simulations with customizable parameters
- **Multi-Simulation**: Run multiple simulations for statistical analysis
- **Team Optimization**: Optimize team selection with various constraints
- **Rider Management**: View, edit, and add riders with real-time parameter updates
- **Results Analysis**: Analyze and visualize simulation results

### Dashboard Features

- **Real-time Rider Updates**: Changes made in Rider Management are immediately reflected in simulations and optimizations
- **Interactive Visualizations**: Charts and graphs for performance analysis
- **Export Capabilities**: Download results in various formats
- **Progress Tracking**: Real-time progress bars for long-running operations

### Running the Dashboard

```bash
# Option 1: Use the launcher script
python run_dashboard.py

# Option 2: Run directly with Streamlit
streamlit run dashboard.py
```

The dashboard will open in your default web browser at `http://localhost:8501`.

## Core Components

### Simulator (`simulator.py`)
- Complete Tour de France simulation engine
- Realistic stage types (sprint, mountain, hills, punch, ITT)
- Multiple classifications (GC, Sprint, Mountain, Youth)
- Crash and abandonment simulation
- Scorito points calculation

### Multi-Simulator (`multi_simulator.py`)
- Statistical analysis of multiple simulation runs
- Performance distribution analysis
- Confidence intervals and probability calculations

### Team Optimization (`team_optimization.py`)
- Integer Linear Programming optimization
- Budget and team size constraints
- Risk aversion and abandon penalty parameters
- Alternative team suggestions

### Rider Database (`riders.py`)
- Comprehensive rider database with realistic parameters
- Performance attributes (sprint, ITT, mountain, hills, punch)
- Team affiliations and pricing
- Age-based youth classification

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd tour_simulator
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Simulation
```python
from simulator import TourSimulator

# Create and run simulation
simulator = TourSimulator()
simulator.simulate_tour()

# Get results
gc_results = simulator.get_final_gc()
sprint_results = simulator.get_final_sprint()
mountain_results = simulator.get_final_mountain()
```

### Multi-Simulation Analysis
```python
from multi_simulator import run_multi_simulation

# Run 100 simulations
results = run_multi_simulation(100)

# Analyze results
for rider, stats in results.items():
    print(f"{rider}: {stats['mean']:.1f} ± {stats['std']:.1f} points")
```

### Team Optimization
```python
from team_optimization import TeamOptimizer

# Create optimizer
optimizer = TeamOptimizer(budget=48.0, team_size=20)

# Get expected points
rider_data = optimizer.run_simulation(100)

# Optimize team
team_selection = optimizer.optimize_team(rider_data)

print(f"Optimal team: {team_selection.rider_names}")
print(f"Expected points: {team_selection.expected_points:.1f}")
print(f"Total cost: {team_selection.total_cost:.2f}")
```

## Rider Management

The dashboard includes comprehensive rider management capabilities:

- **View Riders**: Browse all riders with filtering by team, age, and price
- **Edit Riders**: Modify rider parameters (abilities, price, abandon chance)
- **Add Riders**: Create new riders with custom parameters

**Important**: All rider changes made in the dashboard are immediately reflected in subsequent simulations and optimizations. The system maintains a consistent rider database across all operations.

## Data Export

Simulation results can be exported to Excel files containing:
- Stage-by-stage results
- Final classifications
- Rider performance data
- Team optimization results

## Configuration

Key parameters can be adjusted in the respective modules:
- Stage types and points in `simulator.py`
- Optimization constraints in `team_optimization.py`
- Rider parameters in `riders.py`

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- NumPy
- Plotly
- PuLP (for optimization)
- OpenPyXL (for Excel export)

## License

This project is licensed under the MIT License - see the LICENSE file for details. 