# 🏁 Stage Management - Tour de France Simulator

## Overview

The Stage Management feature allows you to customize both the stage types for each stage of the Tour de France and the probability parameters that determine rider performance based on their tier levels. This gives you complete control over how the simulation behaves.

## How to Access

1. Open the Tour de France Simulator Dashboard
2. Navigate to **🏁 Stage Management** in the sidebar
3. Choose between two tabs:
   - **🎯 Stage Types**: Manage stage types for each stage
   - **🏆 Winning Probabilities**: Adjust probability parameters for rider tiers

## 🎯 Stage Types Management

### Overview
This tab allows you to change the type of each stage in the Tour de France, which affects which rider abilities are most important for that stage.

### Stage Types Available
- **Sprint**: Flat stages favoring sprinters
- **Punch**: Short, explosive stages with punchy climbs
- **Individual Time Trial (ITT)**: Time trial stages
- **Mountain**: High mountain stages favoring climbers
- **Hills**: Hilly terrain stages

### How to Use

1. **View Current Stage Types**: The interface shows all 21 stages in a grid layout
2. **Change Stage Types**: Use the dropdown menus to select different stage types
3. **Monitor Distribution**: View the current distribution of stage types
4. **Visual Feedback**: See a pie chart showing the proportion of each stage type

### Features

#### Stage Grid Layout
- All 21 stages displayed in a 5-column grid
- Each stage shows its current type
- Dropdown menus for easy type selection
- Real-time updates when changes are made

#### Stage Type Summary
- **Current Distribution**: Text summary of how many stages of each type
- **Visual Chart**: Pie chart showing the proportion of each stage type
- **Export Functionality**: Download stage type data as CSV

#### Controls
- **🔄 Reset to Default**: Restore original stage types
- **📊 Export Stage Types**: Download current configuration as CSV
- **💾 Apply Changes**: Save changes to the simulation system

### Example Workflow

1. **Analyze Current Setup**: Look at the stage type distribution
2. **Make Strategic Changes**: 
   - Change Stage 5 from ITT to Mountain for more climbing
   - Convert Stage 8 from Sprint to Punch for more variety
3. **Monitor Impact**: Check the updated distribution chart
4. **Apply Changes**: Click "Apply Changes" to save modifications

## 🏆 Winning Probabilities Management

### Overview
This tab allows you to fine-tune the probability parameters that determine how riders perform based on their ability tiers. These parameters control the winning probabilities riders receive in simulations.

### Parameter Explanation

Each tier has three parameters that define a triangular probability distribution:

- **Min (position)**: Minimum position/result - the best possible result (1 = winner)
- **Mode (position)**: Most likely position/result - the expected result
- **Max (position)**: Maximum position/result - the worst possible result

**Lower values = Better performance (closer to winning)**

### Tier Levels

| Tier | Ability Range | Description |
|------|---------------|-------------|
| **Exceptional** | 98+ | The very best riders |
| **World Class** | 95-97 | Elite performers |
| **Elite** | 90-94 | Very strong riders |
| **Very Good** | 80-89 | Above average |
| **Good** | 70-79 | Competent level |
| **Average** | 50-69 | Standard performance |
| **Below Average** | <50 | Limited ability |

### How to Use

1. **View Current Parameters**: See the current settings for each tier
2. **Adjust Values**: Use number inputs to modify min, mode, and max values
3. **Visualize Changes**: See the probability distributions in the chart
4. **Monitor Impact**: Check the summary table for parameter ranges

### Features

#### Parameter Editors
- **Individual Controls**: Separate number inputs for min, mode, and max
- **Validation**: Values constrained to reasonable ranges (0-200 seconds)
- **Real-time Updates**: Changes reflected immediately in visualizations

#### Visual Representation
- **Probability Chart**: Shows triangular distributions for each tier
- **Color-coded Lines**: Each tier has a distinct color
- **Interactive Legend**: Click to show/hide specific tiers

#### Parameter Summary
- **Data Table**: Shows all current parameters in a table format
- **Range Calculation**: Automatically calculates the range (max - min)
- **Export Ready**: Data formatted for easy export

#### Controls
- **🔄 Reset to Default**: Restore original parameter values
- **📊 Export Parameters**: Download current settings as CSV
- **💾 Apply Changes**: Save changes to the simulation system

### Example Adjustments

#### Making Elite Riders More Dominant
- **Exceptional tier**: Reduce max from 10 to 5 positions
- **World Class tier**: Reduce mode from 3 to 2 positions
- **Elite tier**: Reduce max from 30 to 20 positions

#### Creating More Competitive Racing
- **Average tier**: Reduce min from 20 to 15 positions
- **Good tier**: Reduce mode from 20 to 15 positions
- **Very Good tier**: Reduce max from 40 to 30 positions

#### Making Lower Tiers More Varied
- **Below Average tier**: Increase max from 150 to 200 positions
- **Average tier**: Increase max from 60 to 80 positions

## Integration with Simulation

### Stage Types
- Changes affect which rider abilities are used for each stage
- Sprint stages favor riders with high sprint ability
- Mountain stages favor riders with high mountain ability
- Changes apply immediately to new simulations

### Tier Parameters
- Changes affect the probability distributions for rider performance
- Lower position values = better results (closer to winning)
- Changes apply to all new simulations
- No restart required for parameter changes

## Best Practices

### Stage Type Management
1. **Balance the Route**: Ensure a good mix of stage types
2. **Consider Rider Specialists**: Create opportunities for different rider types
3. **Strategic Placement**: Position key stages (TT, mountain) at appropriate points
4. **Test Changes**: Run simulations to see the impact of changes

### Tier Parameter Management
1. **Start Small**: Make incremental changes rather than large adjustments
2. **Test Impact**: Run simulations to see how changes affect results
3. **Consider Balance**: Ensure no tier becomes too dominant or weak
4. **Document Changes**: Export parameters for future reference

## Advanced Usage

### Creating Custom Tour Routes
1. **Design Stage Types**: Plan the perfect mix of stage types
2. **Fine-tune Parameters**: Adjust tier parameters for desired competitiveness
3. **Test Scenarios**: Run multiple simulations to validate changes
4. **Export Configurations**: Save successful setups for future use

### Balancing Competition
1. **Analyze Current Results**: Look at simulation outcomes
2. **Identify Issues**: Find if certain rider types are too dominant
3. **Adjust Parameters**: Fine-tune tier parameters to address issues
4. **Iterate**: Repeat until desired balance is achieved

## Troubleshooting

### Common Issues

**Q: Changes aren't appearing in simulations?**
A: Make sure to click "Apply Changes" and that you're running new simulations.

**Q: Stage types seem incorrect?**
A: Use "Reset to Default" to restore original stage types, then make your changes.

**Q: Parameters seem too extreme?**
A: Use "Reset to Default" to restore original parameters, then make smaller adjustments.

**Q: Performance is affected?**
A: Large parameter changes can affect simulation performance. Make incremental adjustments.

### Getting Help

If you encounter issues with Stage Management:
1. Check the console for error messages
2. Try resetting to default settings
3. Make smaller, incremental changes
4. Export your current setup before making major changes

## Future Enhancements

Planned improvements for Stage Management:
- **Stage Templates**: Save and load stage type configurations
- **Parameter Presets**: Pre-configured parameter sets for different scenarios
- **Impact Analysis**: Show how changes affect specific riders
- **Historical Tracking**: Track changes over time
- **Bulk Operations**: Apply changes to multiple stages at once

---

**Happy stage managing! 🏁🚴‍♂️** 