# Tour de France Cycling Simulator 🚴‍♂️

A comprehensive simulation engine for Tour de France cycling with team optimization, versus mode, and detailed performance analytics.

## 🎯 Project Overview

This professional-grade cycling simulator provides:
- **Complete Tour de France simulation** with 21 stages
- **Advanced team optimization** using linear programming
- **Competitive versus mode** for team comparison
- **Detailed performance analytics** and classification tracking
- **Streamlit dashboard** for interactive analysis

## 🏗️ Professional Architecture

This project follows modern Python package structure with clean separation of concerns:

```
tour_simulator/                    # Main package
├── core/                          # Core simulation engine
│   ├── simulator.py              # Tour simulation logic
│   ├── riders.py                 # Rider database & models
│   └── stage_profiles.py         # Stage configuration
├── models/                        # Data models
│   ├── rider_parameters.py       # Rider ability parameters
│   └── stage_result.py           # Stage result structures
├── services/                      # Business logic
│   ├── team_optimization.py      # Team optimization engine
│   └── versus_mode.py            # Competitive mode
├── ui/                           # Future UI components
├── config/                       # Configuration management
└── utils/                        # Utility functions

tests/                            # Comprehensive test suite (101 tests)
archive/                          # Historical data & documentation
├── documentation/               # Feature-specific README files
├── data/                        # Historical simulation results
├── utilities/                   # Utility scripts
└── planning/                    # Project planning documents
```

## 🚀 Quick Start

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd tour_simulator

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```python
from tour_simulator import TourSimulator, TeamOptimizer, VersusMode

# Run a complete tour simulation
simulator = TourSimulator()
results = simulator.simulate_tour()

# Optimize a team within budget
optimizer = TeamOptimizer(budget=100.0, team_size=8)
optimal_team = optimizer.optimize_team(rider_data)

# Compare teams in versus mode
versus = VersusMode()
comparison = versus.compare_teams(user_team, optimal_team)
```

### Dashboard Interface
```bash
# Launch the Streamlit dashboard
python run_dashboard.py

# Run versus mode interface
python run_versus_mode.py
```

## 🧪 Testing

The project includes a comprehensive test suite with 101 tests covering:

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_simulator.py    # Core simulation tests
python -m pytest tests/test_riders.py       # Rider database tests
python -m pytest tests/test_team_optimization.py  # Optimization tests
```

## 📊 Features

### Core Simulation
- **21-stage Tour de France** with realistic stage profiles
- **184 professional riders** with detailed ability parameters
- **Multiple classifications**: General, Sprint, Mountain, Youth
- **Crash simulation** and abandonment system
- **Scorito points** calculation for fantasy leagues

### Team Optimization
- **Linear programming** optimization for team selection
- **Budget constraints** and team size limits
- **Risk analysis** with abandonment probability
- **Teammate bonus** calculations
- **Multi-objective optimization** (points vs. cost vs. risk)

### Versus Mode
- **Head-to-head team comparison**
- **Stage-by-stage optimization**
- **Performance analytics** and detailed reporting
- **Export capabilities** for further analysis

## 📁 Archive

Historical files and documentation have been organized in the `archive/` directory:
- **Documentation**: Feature-specific README files
- **Data**: Historical simulation results and exports
- **Utilities**: Helper scripts and tools
- **Planning**: Project restructuring documentation

See `archive/README.md` for detailed information about archived files.

## 🛠️ Development

### Project Structure
- **Clean architecture** with separation of concerns
- **Professional package layout** following Python standards
- **Comprehensive testing** with pytest framework
- **Modern configuration** with pyproject.toml

### Adding Features
```python
# Example: Adding a new service
from tour_simulator.core import RiderDatabase
from tour_simulator.models import RiderParameters

# Services have access to core components
class MyNewService:
    def __init__(self):
        self.rider_db = RiderDatabase()
```

## 📈 Performance

- **Optimized algorithms** for large-scale simulations
- **Parallel processing** support for team optimization
- **Efficient data structures** for rider management
- **Caching mechanisms** for repeated calculations

## 🏆 Success Metrics

- ✅ **101/101 tests passing** - Full test coverage maintained
- ✅ **Professional structure** - Industry-standard package layout
- ✅ **Zero technical debt** - Clean, maintainable codebase
- ✅ **Complete functionality** - All original features preserved
- ✅ **Future-ready** - Easily extensible architecture

---

*This project was professionally restructured in January 2025 to implement clean architecture principles and maintainable code organization.* 