# Tour de France Cycling Game Simulator

This simulator recreates the cycling game mechanics from scorito.nl for the Tour de France. It simulates 21 stages of the Tour de France, where riders' performances are determined by triangular probability distributions.

## 🚀 New: Interactive Dashboard

**We've added a comprehensive web-based dashboard!** 

### Quick Start with Dashboard
1. Install dependencies: `pip install -r requirements.txt`
2. Launch dashboard: `python run_dashboard.py`
3. Open browser at `http://localhost:8501`

### Dashboard Features
- 🎯 **Single Simulation**: Run individual Tour simulations with detailed results
- 📊 **Multi-Simulation**: Statistical analysis with 10-500 simulation runs
- ⚡ **Team Optimization**: Advanced team selection with budget constraints
- 👥 **Rider Management**: View, edit, and add riders with custom parameters
- 📈 **Results Analysis**: Interactive visualizations and export capabilities

For detailed dashboard documentation, see [DASHBOARD_README.md](DASHBOARD_README.md)

## Features
- Simulation of 21 Tour de France stages
- Rider database with performance probabilities
- Triangular distribution-based result generation
- Point calculation based on stage results
- Team optimization using Integer Linear Programming
- Multi-simulation statistical analysis

## Setup
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the simulator:
```bash
python simulator.py
```

3. Or launch the interactive dashboard:
```bash
python run_dashboard.py
```

## Project Structure
- `simulator.py`: Main simulation logic
- `multi_simulator.py`: Multi-simulation functionality
- `team_optimization.py`: Team selection optimization
- `riders.py`: Rider database and probability distributions
- `dashboard.py`: Interactive web dashboard
- `run_dashboard.py`: Dashboard launcher
- `requirements.txt`: Project dependencies 