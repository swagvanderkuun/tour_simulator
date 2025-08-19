# Dashboard Stage Management - Weighted Profiles

## Overview

The Tour Simulator dashboard has been enhanced to support the new **weighted stage profiles** functionality. Users can now create mixed stage types with weights through an intuitive web interface.

## New Features

### 🎯 Dual Mode Interface

The dashboard now offers two configuration modes:

#### 1. Simple Mode (Single Type)
- Traditional single-stage-type selection
- Dropdown menus for each stage
- Quick and easy for basic configurations

#### 2. Advanced Mode (Mixed Types with Weights)
- Create complex mixed stage profiles
- Weight sliders for each stage type
- Real-time validation and auto-normalization
- Visual feedback for weight totals

### 🎨 Enhanced User Interface

#### Stage Configuration
- **Expandable sections** for each stage in advanced mode
- **Real-time validation** with visual feedback
- **Auto-normalization** option for invalid weights
- **Quick examples** button for common mixed stages

#### Visual Feedback
- ✅ Success messages for valid configurations
- ❌ Error messages for invalid weights
- 📊 Live weight total display
- 🎯 Current profile summary

### 📊 Advanced Analytics

#### Stage Summary
- **Weighted distribution** showing fractional stage counts
- **Mixed stage identification** with stage numbers
- **Interactive pie chart** of stage type distribution
- **Export functionality** for data analysis

#### Export Features
- **CSV export** with stage, type, weight, and value columns
- **Comprehensive data** including all mixed stage combinations
- **Ready for analysis** in external tools

## How to Use

### Accessing Stage Management

1. **Navigate to Stage Types**: Use the sidebar to select "🏁 Stage Types"
2. **Choose Mode**: Select between Simple and Advanced configuration
3. **Configure Stages**: Set up your desired stage profiles
4. **Apply Changes**: Click "Apply Changes" to save modifications

### Simple Mode Usage

1. **Select Stage Type**: Use dropdown menus for each stage
2. **View Current Selection**: See the current type displayed
3. **Apply Changes**: Save your modifications

### Advanced Mode Usage

1. **Expand Stage Sections**: Click on stage expanders to configure
2. **Set Weights**: Use number inputs to set weights (0.0 to 1.0)
3. **Monitor Total**: Watch the total weight display
4. **Auto-Normalize**: Use the normalize button if weights don't sum to 1.0
5. **View Profile**: See the current mixed profile summary

### Quick Examples

The dashboard includes a "Quick Mix Examples" button that applies common mixed stage configurations:

- **Stage 4**: 60% Punch, 40% Sprint (Hilly Sprint)
- **Stage 8**: 50% Sprint, 30% Punch, 20% Break Away (Complex)
- **Stage 13**: 30% Break Away, 70% Mountain (Mountain with Breakaway)
- **Stage 16**: 80% Mountain, 20% Break Away (Mountain with Opportunities)

## Technical Implementation

### Backend Integration

The dashboard seamlessly integrates with the new weighted stage profiles system:

```python
# Dashboard imports the new functions
from stage_profiles import (
    StageType, get_stage_profile, validate_stage_profile, 
    update_stage_profile, STAGE_PROFILES
)
```

### Session State Management

The dashboard maintains stage configurations in session state:

```python
if 'stage_profiles_edit' not in st.session_state:
    st.session_state.stage_profiles_edit = STAGE_PROFILES.copy()
```

### Validation System

Real-time validation ensures data integrity:

```python
# Validate all profiles before applying
invalid_stages = []
for stage_num in range(1, 22):
    profile = st.session_state.stage_profiles_edit.get(stage_num, {StageType.SPRINT: 1.0})
    if isinstance(profile, dict) and not validate_stage_profile(profile):
        invalid_stages.append(stage_num)
```

## User Experience Features

### 🎯 Intuitive Design

- **Clear labeling** for all stage types
- **Visual hierarchy** with proper spacing
- **Consistent styling** matching the dashboard theme
- **Responsive layout** for different screen sizes

### 🔄 Interactive Elements

- **Real-time updates** as users make changes
- **Immediate feedback** for validation results
- **Smooth transitions** between configuration modes
- **Persistent state** across dashboard sessions

### 📱 Accessibility

- **Keyboard navigation** support
- **Screen reader** friendly labels
- **High contrast** visual elements
- **Clear error messages** for all validation issues

## Benefits

### 1. Enhanced Flexibility
- Create realistic mixed stage characteristics
- Fine-tune stage profiles for specific scenarios
- Support complex racing dynamics

### 2. Improved User Experience
- Intuitive interface for complex configurations
- Real-time validation prevents errors
- Visual feedback enhances understanding

### 3. Better Data Management
- Export functionality for analysis
- Comprehensive stage type tracking
- Integration with simulation system

### 4. Educational Value
- Learn about stage characteristics
- Understand racing dynamics
- Experiment with different configurations

## Example Workflows

### Creating a Hilly Sprint Stage

1. **Select Advanced Mode**
2. **Expand Stage 4**
3. **Set Punch weight to 0.6**
4. **Set Sprint weight to 0.4**
5. **Verify total is 1.0**
6. **Apply changes**

### Setting Up a Mountain Stage with Breakaway Opportunities

1. **Select Advanced Mode**
2. **Expand desired mountain stage**
3. **Set Mountain weight to 0.8**
4. **Set Break Away weight to 0.2**
5. **Apply changes**

### Exporting Stage Configuration

1. **Configure all stages as desired**
2. **Click "Export Stage Types"**
3. **Download CSV file**
4. **Use in external analysis tools**

## Troubleshooting

### Common Issues

**Q: Weights don't sum to 1.0?**
A: Use the "Auto-normalize" button or manually adjust weights.

**Q: Changes not applying?**
A: Make sure to click "Apply Changes" after configuration.

**Q: Dashboard not loading?**
A: Ensure all dependencies are installed and stage_profiles module is accessible.

**Q: Export not working?**
A: Check that all stage configurations are valid before exporting.

### Getting Help

If you encounter issues with the dashboard:

1. **Check validation messages** for specific errors
2. **Use the reset button** to restore default settings
3. **Try simple mode** for basic configurations
4. **Export current settings** before making major changes

## Future Enhancements

### Planned Improvements

1. **Visual Stage Editor**: Drag-and-drop interface for stage configuration
2. **Template System**: Pre-built stage profile templates
3. **Performance Preview**: Real-time simulation preview of changes
4. **Collaborative Features**: Share and import stage configurations

### Integration Opportunities

1. **Weather Integration**: Weather-based stage characteristic adjustments
2. **Historical Data**: Import real Tour de France stage profiles
3. **AI Suggestions**: Machine learning recommendations for optimal mixes
4. **Advanced Analytics**: Detailed performance impact analysis

## Conclusion

The enhanced dashboard stage management system provides a powerful and user-friendly interface for creating complex stage profiles. The dual-mode approach ensures accessibility for both novice and advanced users, while the comprehensive validation and export features support professional analysis workflows.

The integration with the weighted stage profiles system creates a seamless experience from configuration to simulation, enabling users to create more realistic and nuanced Tour de France scenarios. 