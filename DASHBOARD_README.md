# 🚴‍♂️ Tour de France Simulator Dashboard

A comprehensive web-based dashboard for running cycling simulations, optimizing team selections, and analyzing results for the Tour de France cycling game.

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Launch the dashboard:**
   ```bash
   python run_dashboard.py
   ```
   
   Or directly with Streamlit:
   ```bash
   streamlit run dashboard.py
   ```

3. **Open your browser:**
   The dashboard will automatically open at `http://localhost:8501`

## 📊 Dashboard Features

### 🏠 Overview Page
- Quick statistics about riders and teams
- Recent activity tracking
- Navigation to all dashboard features

### 🎯 Single Simulation
- Run individual Tour de France simulations
- View detailed stage-by-stage results
- Export results to Excel format
- Real-time progress tracking

### 📊 Multi-Simulation Analysis
- Run multiple simulations (10-500 runs)
- Statistical analysis of results
- Average performance calculations
- Confidence intervals and probability distributions

### ⚡ Team Optimization
- Advanced team selection optimization
- Budget constraints (30-60 points)
- Risk aversion settings
- Abandonment probability penalties
- Multiple optimization strategies

### 👥 Rider Management
- **View Riders:** Browse all riders with filtering options
- **Edit Rider:** Modify rider parameters and abilities
- **Add Rider:** Create new riders with custom parameters
- Export rider data to CSV

### 📈 Results Analysis
- Interactive visualizations with Plotly
- Stage-by-stage performance analysis
- Team performance comparisons
- Classification standings
- Export capabilities

## 🎮 How to Use

### Running Simulations

1. **Single Simulation:**
   - Go to "🎯 Single Simulation"
   - Configure options (progress tracking, export)
   - Click "🚀 Run Single Simulation"
   - View results and export if needed

2. **Multi-Simulation:**
   - Go to "📊 Multi Simulation"
   - Set number of simulations (10-500)
   - Click "🔄 Run Multi-Simulation"
   - Analyze statistical results

### Team Optimization

1. **Configure Parameters:**
   - Set budget (default: 48 points)
   - Choose team size (default: 20 riders)
   - Adjust risk aversion (0-1)
   - Set abandonment penalty (0-1)

2. **Run Optimization:**
   - Click "🎯 Optimize Team"
   - View optimal team selection
   - Analyze team composition

### Managing Riders

1. **View Current Riders:**
   - Filter by team, age, or price
   - Sort by any column
   - Export filtered data

2. **Edit Rider Parameters:**
   - Select rider from dropdown
   - Adjust abilities (0-100 scale)
   - Modify price and abandonment chance
   - Save changes

3. **Add New Riders:**
   - Enter rider details
   - Set abilities and parameters
   - Add to database

## 📁 File Structure

```
tour_simulator/
├── dashboard.py              # Main dashboard application
├── run_dashboard.py          # Dashboard launcher script
├── simulator.py              # Core simulation logic
├── multi_simulator.py        # Multi-simulation functionality
├── team_optimization.py      # Team optimization algorithms
├── riders.py                 # Rider database and management
├── rider_parameters.py       # Rider ability parameters
├── stage_profiles.py         # Stage type definitions
├── requirements.txt          # Python dependencies
├── README.md                 # Original project README
└── DASHBOARD_README.md       # This file
```

## 🔧 Configuration

### Dashboard Settings
- **Port:** Default 8501 (configurable in `run_dashboard.py`)
- **Host:** localhost
- **Theme:** Light mode with custom styling

### Simulation Parameters
- **Stages:** 21 Tour de France stages
- **Riders:** ~100+ professional cyclists
- **Classifications:** GC, Sprint, Mountain, Youth
- **Points System:** Scorito-style scoring

## 📊 Data Export

### Supported Formats
- **Excel (.xlsx):** Complete simulation results
- **CSV:** Rider data and filtered results
- **Interactive Charts:** Plotly visualizations

### Export Features
- Timestamped filenames
- Multiple sheets per Excel file
- Stage-by-stage results
- Final classifications
- Statistical summaries

## 🎯 Advanced Features

### Optimization Algorithms
- **Integer Linear Programming:** Optimal team selection
- **Risk Management:** Variance and abandonment penalties
- **Budget Constraints:** Flexible budget allocation
- **Team Diversity:** Minimum riders per team

### Statistical Analysis
- **Confidence Intervals:** Performance predictions
- **Probability Distributions:** Result likelihoods
- **Correlation Analysis:** Rider performance relationships
- **Trend Analysis:** Stage-by-stage patterns

## 🐛 Troubleshooting

### Common Issues

1. **Streamlit not found:**
   ```bash
   pip install streamlit
   ```

2. **Missing dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Port already in use:**
   - Change port in `run_dashboard.py`
   - Or kill existing process: `lsof -ti:8501 | xargs kill`

4. **Import errors:**
   - Ensure all Python files are in the same directory
   - Check Python version (3.8+ required)

### Performance Tips

- **Large simulations:** Use multi-simulation for statistical analysis
- **Memory usage:** Close browser tabs when not needed
- **Export size:** Large Excel files may take time to generate

## 🤝 Contributing

To contribute to the dashboard:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. See the main README.md for license details.

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Open an issue on GitHub

---

**Happy simulating! 🚴‍♂️🏆** 