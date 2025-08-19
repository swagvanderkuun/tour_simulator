# Weighted Stage Profiles

## Overview

The Tour Simulator now supports **weighted stage profiles**, allowing stages to be a mix of different types with weights that sum to 1.0. This creates more realistic and nuanced stage characteristics that better reflect the complex terrain and racing dynamics of real cycling stages.

## Key Features

### Mixed Stage Types
- **Pure Stages**: Traditional single-type stages (e.g., 100% sprint)
- **Mixed Stages**: Combination of multiple stage types with weights
- **Validation**: Ensures weights always sum to 1.0
- **Backward Compatibility**: Existing code continues to work unchanged

### Weighted Calculations
- **Rider Performance**: Combines rider abilities based on stage weights
- **Time Gaps**: Weighted time gaps between riders
- **Classification Points**: Weighted sprint and mountain points
- **Probability Distributions**: Weighted triangular distributions for results

## Implementation Details

### Stage Profile Structure

```python
# Pure stage (traditional)
{StageType.SPRINT: 1.0}

# Mixed stage (new)
{StageType.BREAK_AWAY: 0.3, StageType.MOUNTAIN: 0.7}
```

### Core Functions

#### `get_stage_profile(stage_number: int) -> Dict[StageType, float]`
Returns the weighted profile for a specific stage.

#### `validate_stage_profile(profile: Dict[StageType, float]) -> bool`
Validates that stage profile weights sum to 1.0.

#### `update_stage_profile(stage_number: int, profile: Dict[StageType, float])`
Updates a stage profile with validation.

#### `get_stage_type(stage_number: int) -> StageType` (Backward Compatibility)
Returns the primary stage type (highest weight) for compatibility.

## Usage Examples

### Creating Mixed Stages

```python
from stage_profiles import StageType, update_stage_profile, validate_stage_profile

# Hilly sprint stage: 60% punch, 40% sprint
hilly_sprint = {StageType.PUNCH: 0.6, StageType.SPRINT: 0.4}
update_stage_profile(4, hilly_sprint)

# Complex stage: 50% sprint, 30% punch, 20% break away
complex_stage = {StageType.SPRINT: 0.5, StageType.PUNCH: 0.3, StageType.BREAK_AWAY: 0.2}
update_stage_profile(8, complex_stage)

# Mountain with breakaway opportunities: 80% mountain, 20% break away
mountain_break = {StageType.MOUNTAIN: 0.8, StageType.BREAK_AWAY: 0.2}
update_stage_profile(16, mountain_break)
```

### Rider Performance Analysis

```python
from rider_parameters import RiderParameters
from stage_profiles import get_stage_profile

# Create a rider
rider = RiderParameters(
    sprint_ability=95,    # World Class
    punch_ability=85,     # Very Good
    mountain_ability=88,  # Very Good
    break_away_ability=82, # Very Good
    itt_ability=90        # Elite
)

# Get stage profile
stage_profile = get_stage_profile(13)  # Mixed stage: 30% break away, 70% mountain

# Get weighted performance
min_val, mode_val, max_val = rider.get_weighted_probability_range(stage_profile)
print(f"Expected position: {mode_val:.1f}")
```

### Database Integration

```python
from riders import RiderDatabase
from stage_profiles import get_stage_profile

rider_db = RiderDatabase()
rider = rider_db.get_rider("POGAČAR Tadej")

# Get performance on mixed stage
stage_profile = get_stage_profile(13)
min_val, mode_val, max_val = rider.get_stage_probability(13)
print(f"Pogačar on Stage 13: Expected position {mode_val:.1f}")
```

## Current Mixed Stages

The system includes several example mixed stages:

### Stage 13: Mountain with Breakaway Opportunities
```python
{StageType.BREAK_AWAY: 0.3, StageType.MOUNTAIN: 0.7}
```
- 30% break away characteristics
- 70% mountain characteristics
- Favors climbers but allows breakaway specialists to compete

## Performance Impact

### Rider Performance Comparison

| Stage Type | Sprinter | Climber | All-Rounder |
|------------|----------|---------|-------------|
| Pure Sprint | 1.0 | 75.0 | 15.0 |
| Hilly Sprint (60% Punch, 40% Sprint) | 12.4 | 42.0 | 9.6 |
| Mixed Mountain (30% Break Away, 70% Mountain) | 30.0 | 6.6 | 15.0 |
| Pure Mountain | 30.0 | 3.0 | 15.0 |

### Key Observations
- **Mixed stages create more competitive racing** for different rider types
- **All-rounders perform consistently** across various stage types
- **Specialists still excel** on their preferred terrain but face more competition
- **Realistic stage characteristics** better reflect actual cycling stages

## Technical Implementation

### Weighted Calculations

#### Rider Performance
```python
def get_weighted_probability_range(self, stage_profile: Dict[StageType, float]):
    weighted_min = 0.0
    weighted_mode = 0.0
    weighted_max = 0.0
    
    for stage_type, weight in stage_profile.items():
        ability = ability_map[stage_type]
        min_val, mode_val, max_val = ability_to_prob(ability)
        
        weighted_min += min_val * weight
        weighted_mode += mode_val * weight
        weighted_max += max_val * weight
    
    return (weighted_min, weighted_mode, weighted_max)
```

#### Time Gaps
```python
weighted_time_gap = 0.0
for stage_type, weight in stage_profile.items():
    weighted_time_gap += STAGE_TIME_GAPS[stage_type.value] * weight
```

#### Classification Points
```python
for stage_type, weight in stage_profile.items():
    if stage_type == StageType.SPRINT:
        for idx, result in enumerate(stage.results[:len(SPRINT_SPRINT_POINTS)]):
            self.sprint_points[result.rider.name] += int(SPRINT_SPRINT_POINTS[idx] * weight)
```

## Benefits

### 1. Realistic Stage Representation
- Stages often have mixed characteristics in real cycling
- Hilly sprints, mountain stages with breakaway opportunities
- More nuanced racing dynamics

### 2. Better Rider Competition
- All-rounders become more valuable
- Specialists face more competition on mixed stages
- More strategic team selection required

### 3. Flexible System
- Easy to create custom stage profiles
- Validation ensures mathematical consistency
- Backward compatibility maintained

### 4. Enhanced Simulation Accuracy
- More realistic race outcomes
- Better representation of cycling's complexity
- Improved strategic depth

## Future Enhancements

### Potential Improvements
1. **Dynamic Stage Profiles**: Stage characteristics that change during the race
2. **Weather Integration**: Weather affecting stage characteristics
3. **Historical Data**: Stage profiles based on historical race data
4. **AI-Generated Profiles**: Machine learning to create optimal stage mixes

### Dashboard Integration
- Visual stage profile editor
- Real-time stage characteristic visualization
- Performance impact analysis tools

## Troubleshooting

### Common Issues

**Q: Weights don't sum to 1.0?**
A: Use `validate_stage_profile()` to check before updating.

**Q: Performance seems wrong?**
A: Ensure you're using `get_weighted_probability_range()` for mixed stages.

**Q: Backward compatibility issues?**
A: Use `get_stage_type()` for existing code that expects single stage types.

### Validation Examples

```python
# Valid profile
valid = {StageType.SPRINT: 0.6, StageType.PUNCH: 0.4}
print(validate_stage_profile(valid))  # True

# Invalid profile
invalid = {StageType.SPRINT: 0.6, StageType.PUNCH: 0.3}  # Sum = 0.9
print(validate_stage_profile(invalid))  # False
```

## Conclusion

The weighted stage profiles system significantly enhances the Tour Simulator's realism and strategic depth. By allowing stages to have mixed characteristics, the simulation better reflects the complex nature of professional cycling and creates more engaging and competitive racing scenarios.

The system maintains full backward compatibility while providing a flexible foundation for future enhancements and more sophisticated stage modeling. 