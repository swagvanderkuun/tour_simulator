# 🏆 Tier Maker - Tour de France Simulator

## Overview

The Tier Maker is a powerful feature in the Tour de France Simulator dashboard that allows you to visually manage and adjust rider abilities using a tier-based system. Similar to tier list makers like TierMaker.com, you can drag and drop riders between different ability tiers to fine-tune their performance in the simulation.

## How to Access

1. Open the Tour de France Simulator Dashboard
2. Navigate to **👥 Rider Management** in the sidebar
3. Click on the **🏆 Tier Maker** tab

## Features

### 🎯 Skill Categories
You can edit rider abilities for five different skill categories:
- **Sprint**: Sprinting ability for flat stages and bunch sprints
- **Individual Time Trial (ITT)**: Time trial performance
- **Mountain**: Climbing ability for mountain stages
- **Break Away**: Performance in break away situations
- **Punch**: Short, explosive efforts and punchy climbs

### 🏅 Tier System
The tier system uses six levels with corresponding ability scores:

| Tier | Score | Description |
|------|-------|-------------|
| **S** | 98 | Exceptional - The very best in this skill |
| **A** | 95 | Elite - Among the top performers |
| **B** | 90 | Very Good - Strong performers |
| **C** | 80 | Good - Above average |
| **D** | 70 | Average - Competent level |
| **E** | 40 | Below Average - Limited ability |

### 🔍 Search and Filter
- **Search by name**: Type a rider's name to quickly find them
- **Filter by team**: Select a specific team to focus on their riders
- **Real-time filtering**: Results update as you type or change filters

### 📊 Visual Interface
- **Color-coded tiers**: Each tier has a distinct color for easy identification
- **Rider cards**: Each rider displays their name, team, and current ability score
- **Tier statistics**: Real-time count of riders in each tier
- **Distribution chart**: Visual bar chart showing tier distribution

## How to Use

### Moving Riders Between Tiers

1. **Select a skill category** from the dropdown menu
2. **Find the rider** you want to modify (use search/filter if needed)
3. **Use the arrow buttons**:
   - ⬆️ **Up arrow**: Move rider to a higher tier
   - ⬇️ **Down arrow**: Move rider to a lower tier
4. **Changes are applied immediately** to the rider database

### Example Workflow

1. Select "Mountain" as the skill category
2. Find Tadej Pogačar (currently in S tier)
3. Click the ⬇️ button to move him to A tier
4. His mountain ability will change from 98 to 95
5. The tier statistics and chart will update automatically

## Advanced Features

### 🎯 Auto-Balance Tiers
Automatically distributes riders more evenly across tiers based on their current abilities. This is useful for:
- Creating more balanced competition
- Ensuring no tier is too crowded or empty
- Quick rebalancing after major changes

### 📊 Export Tier Data
Export the current tier assignments to a CSV file containing:
- Rider names and teams
- Selected skill category
- Current tier and score
- Actual ability value

### 🔄 Reset to Original
Revert all changes back to the original tier assignments. Useful for:
- Undoing experimental changes
- Starting fresh with the default configuration
- Comparing modified vs. original setups

### 💾 Save Changes
Confirm that all tier changes are saved to the rider database. Changes are automatically applied, but this button provides confirmation.

## Tips for Effective Tier Management

### 1. **Start with the Big Names**
Focus on the top riders first (Pogačar, Vingegaard, Evenepoel, etc.) as their tier changes will have the most impact on simulation results.

### 2. **Consider Team Balance**
When adjusting tiers, consider how changes affect team dynamics. A team with multiple S-tier climbers might dominate mountain stages.

### 3. **Use the Statistics**
Monitor the tier distribution chart to ensure you're not creating an unbalanced field. Too many riders in S-tier can make competition less interesting.

### 4. **Test Incrementally**
Make small changes and run simulations to see the impact before making major adjustments.

### 5. **Export Before Major Changes**
Use the export feature to save your current tier setup before making significant modifications.

## Integration with Simulation

All tier changes made in the Tier Maker are immediately reflected in:
- **Single simulations**: Individual race simulations
- **Multi-simulations**: Batch simulations for statistical analysis
- **Team optimization**: AI-powered team selection
- **Results analysis**: Performance comparisons and statistics

## Technical Details

### Data Persistence
- Tier assignments are stored in Streamlit's session state
- Rider ability changes are applied directly to the rider database
- Changes persist for the duration of the dashboard session

### Performance
- The interface updates in real-time as you make changes
- Large rider databases (100+ riders) are handled efficiently
- Search and filtering are optimized for quick response

### Compatibility
- Works with all rider databases in the simulator
- Compatible with custom rider additions
- Supports all skill categories and tier levels

## Troubleshooting

### Common Issues

**Q: Changes aren't appearing in simulations?**
A: Make sure to click "💾 Save Changes" and that you're using the same rider database instance.

**Q: Can't find a specific rider?**
A: Use the search function or check if the team filter is active. Some riders might be filtered out.

**Q: Tier assignments seem incorrect?**
A: Use "🔄 Reset to Original" to restore default assignments, then make your changes.

**Q: Performance is slow with many riders?**
A: Use the team filter to focus on specific teams, or use the search function to find specific riders.

### Getting Help

If you encounter issues with the Tier Maker:
1. Check the console for error messages
2. Try refreshing the dashboard
3. Reset to original settings and try again
4. Export your current setup before making changes

## Future Enhancements

Planned improvements for the Tier Maker:
- **Bulk operations**: Move multiple riders at once
- **Custom tier scores**: Adjust the ability scores for each tier
- **Tier templates**: Save and load tier configurations
- **Comparison mode**: Compare different tier setups side-by-side
- **Historical tracking**: Track changes over time

---

**Happy tier making! 🏆🚴‍♂️** 