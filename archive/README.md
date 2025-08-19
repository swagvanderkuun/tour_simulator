# 📦 Tour Simulator Archive

This directory contains files that have been archived during the project restructuring to maintain a clean main directory structure while preserving important historical data and documentation.

## 📁 Archive Structure

### 📚 `/documentation/`
Contains all feature-specific README files that document various components of the application:

- **`DASHBOARD_README.md`** - Streamlit dashboard documentation
- **`DASHBOARD_STAGES_README.md`** - Stage management interface docs
- **`VERSUS_MODE_README.md`** - Competitive mode documentation  
- **`TIER_MAKER_README.md`** - Rider tier management docs
- **`STAGE_MANAGEMENT_README.md`** - Stage configuration docs
- **`WEIGHTED_STAGES_README.md`** - Weighted stage profile documentation

### 📊 `/data/`
Contains historical simulation results and data files:

#### Excel Export Files
- **`tour_simulation_results_20250627_223934.xlsx`** - Full tour simulation from June 27
- **`tour_simulation_results_20250625_145732.xlsx`** - Full tour simulation from June 25  
- **`versus_mode_results_20250630_213558.xlsx`** - Versus mode results from June 30
- **`versus_mode_results_20250627_150352.xlsx`** - Versus mode results from June 27
- **`optimal_team_selection.xlsx`** - Team optimization results

#### JSON Data Files
- **`missing_riders.json`** - Data about riders not in the main database
- **`scraped_debug.json`** - Debug data from web scraping operations

### 🔧 `/utilities/`
Contains utility scripts and miscellaneous files:

- **`update_riders.py`** - Script for updating rider database
- **`rendered_page.html`** - HTML export/render of dashboard
- **`github.pub`** - SSH public key
- **`github`** - SSH private key

### 📋 `/planning/`
Contains project planning and restructuring documentation:

- **`RESTRUCTURING_PLAN.md`** - Detailed plan for project restructuring
- **`RESTRUCTURING_COMPLETE.md`** - Summary of completed restructuring work

## 🎯 Purpose

This archive serves to:

1. **Maintain Clean Structure** - Keep the main project directory focused on active code
2. **Preserve History** - Retain important data exports and documentation
3. **Enable Reference** - Allow developers to reference historical implementations
4. **Support Debugging** - Keep debug data available for troubleshooting

## 📖 Usage

### Accessing Documentation
```bash
# View specific feature documentation
cat archive/documentation/VERSUS_MODE_README.md

# List all available docs
ls archive/documentation/
```

### Retrieving Historical Data
```bash
# Access simulation results
open archive/data/tour_simulation_results_20250627_223934.xlsx

# View data files
ls archive/data/
```

### Using Utility Scripts
```bash
# Run rider update utility
python archive/utilities/update_riders.py
```

## 🔄 Restoration

If any archived files are needed in the main project:

```bash
# Restore a specific file
cp archive/documentation/VERSUS_MODE_README.md ./

# Restore all data files
cp archive/data/*.xlsx ./
```

## 🗑️ Cleanup Guidelines

Files in this archive can be safely removed if:
- Data exports are older than 6 months
- Documentation has been superseded by newer versions
- Utility scripts are no longer compatible with current codebase

## 📅 Archive Date

**Created:** January 2025 during project restructuring  
**Last Updated:** January 2025

---

*This archive was created as part of the Tour Simulator professional restructuring to implement clean architecture and maintainable code organization.* 