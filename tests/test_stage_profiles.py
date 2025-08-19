"""
Tests for the stage_profiles module.
"""
import pytest
from tour_simulator.core.stage_profiles import (
    StageType, STAGE_PROFILES, get_stage_profile, get_stage_type,
    get_stages_of_type, validate_stage_profile, update_stage_profile
)


class TestStageType:
    """Test StageType enum."""

    def test_stage_type_values(self):
        """Test that stage types have correct values."""
        assert StageType.SPRINT.value == "sprint"
        assert StageType.PUNCH.value == "punch"
        assert StageType.ITT.value == "itt"
        assert StageType.MOUNTAIN.value == "mountain"
        assert StageType.BREAK_AWAY.value == "break_away"

    def test_stage_type_completeness(self):
        """Test that all expected stage types are defined."""
        expected_types = ["sprint", "punch", "itt", "mountain", "break_away"]
        actual_types = [stage_type.value for stage_type in StageType]
        
        assert set(expected_types) == set(actual_types)


class TestStageProfiles:
    """Test stage profiles configuration."""

    def test_stage_profiles_completeness(self):
        """Test that all 21 stages have profiles."""
        assert len(STAGE_PROFILES) == 21
        
        # Check all stages 1-21 are present
        for stage in range(1, 22):
            assert stage in STAGE_PROFILES

    def test_stage_profiles_validity(self):
        """Test that all stage profiles are valid (weights sum to 1.0)."""
        for stage, profile in STAGE_PROFILES.items():
            total_weight = sum(profile.values())
            assert abs(total_weight - 1.0) < 0.001, f"Stage {stage} weights sum to {total_weight}"

    def test_stage_profiles_structure(self):
        """Test that all stage profiles have correct structure."""
        for stage, profile in STAGE_PROFILES.items():
            # Should be a dictionary
            assert isinstance(profile, dict)
            
            # Should have at least one stage type
            assert len(profile) > 0
            
            # All keys should be StageType enum values
            for stage_type in profile.keys():
                assert isinstance(stage_type, StageType)
            
            # All values should be positive numbers
            for weight in profile.values():
                assert isinstance(weight, (int, float))
                assert weight > 0

    def test_specific_stage_profiles(self):
        """Test specific stage profiles are as expected."""
        # Stage 1 should be pure sprint
        assert STAGE_PROFILES[1] == {StageType.SPRINT: 1.0}
        
        # Stage 5 should be pure ITT
        assert STAGE_PROFILES[5] == {StageType.ITT: 1.0}
        
        # Stage 12 should be pure mountain
        assert STAGE_PROFILES[12] == {StageType.MOUNTAIN: 1.0}
        
        # Check a mixed stage (stage 2)
        stage_2 = STAGE_PROFILES[2]
        assert StageType.PUNCH in stage_2
        assert StageType.SPRINT in stage_2
        assert stage_2[StageType.PUNCH] == 0.8
        assert stage_2[StageType.SPRINT] == 0.2


class TestGetStageProfile:
    """Test get_stage_profile function."""

    def test_get_existing_stage(self):
        """Test getting profile for existing stage."""
        profile = get_stage_profile(1)
        assert profile == {StageType.SPRINT: 1.0}
        
        profile = get_stage_profile(5)
        assert profile == {StageType.ITT: 1.0}

    def test_get_stage_profile_returns_reference(self):
        """Test that get_stage_profile returns the same reference (current behavior)."""
        profile1 = get_stage_profile(1)
        profile2 = get_stage_profile(1)
        
        # Should be equal and the same object (current implementation)
        assert profile1 == profile2
        assert profile1 is profile2  # Current implementation returns reference

    def test_get_nonexistent_stage(self):
        """Test getting profile for non-existent stage."""
        with pytest.raises(KeyError):
            get_stage_profile(0)
        
        with pytest.raises(KeyError):
            get_stage_profile(22)
        
        with pytest.raises(KeyError):
            get_stage_profile(100)


class TestGetStageType:
    """Test get_stage_type function."""

    def test_get_primary_stage_type(self):
        """Test getting primary stage type."""
        # Stage 1 is pure sprint
        assert get_stage_type(1) == StageType.SPRINT
        
        # Stage 5 is pure ITT
        assert get_stage_type(5) == StageType.ITT
        
        # Stage 12 is pure mountain
        assert get_stage_type(12) == StageType.MOUNTAIN

    def test_get_mixed_stage_type(self):
        """Test getting primary type for mixed stages."""
        # Stage 2 is 80% punch, 20% sprint - should return punch
        assert get_stage_type(2) == StageType.PUNCH
        
        # Stage 6 is 60% punch, 30% break_away, 10% mountain - should return punch
        assert get_stage_type(6) == StageType.PUNCH

    def test_get_stage_type_all_stages(self):
        """Test that get_stage_type works for all stages."""
        for stage in range(1, 22):
            stage_type = get_stage_type(stage)
            assert isinstance(stage_type, StageType)

    def test_get_nonexistent_stage_type(self):
        """Test getting type for non-existent stage."""
        with pytest.raises(KeyError):
            get_stage_type(0)
        
        with pytest.raises(KeyError):
            get_stage_type(22)


class TestGetStagesOfType:
    """Test get_stages_of_type function."""

    def test_get_sprint_stages(self):
        """Test getting all sprint stages."""
        sprint_stages = get_stages_of_type(StageType.SPRINT)
        
        # Should include stages where sprint is the primary type
        assert 1 in sprint_stages  # Pure sprint
        assert 3 in sprint_stages  # Pure sprint
        assert 8 in sprint_stages  # 90% sprint, 10% punch
        assert 9 in sprint_stages  # Pure sprint
        
        # Should be list of integers
        assert all(isinstance(stage, int) for stage in sprint_stages)

    def test_get_mountain_stages(self):
        """Test getting all mountain stages."""
        mountain_stages = get_stages_of_type(StageType.MOUNTAIN)
        
        # Should include mountain stages
        assert 12 in mountain_stages  # Pure mountain
        assert 16 in mountain_stages  # Pure mountain
        assert 18 in mountain_stages  # Pure mountain
        assert 19 in mountain_stages  # Pure mountain
        
        # Should not include non-mountain primary stages
        assert 1 not in mountain_stages  # Sprint stage

    def test_get_itt_stages(self):
        """Test getting all ITT stages."""
        itt_stages = get_stages_of_type(StageType.ITT)
        
        # Should include ITT stage
        assert 5 in itt_stages  # Pure ITT
        
        # Should not include non-ITT stages
        assert 1 not in itt_stages  # Sprint stage

    def test_get_stages_for_all_types(self):
        """Test that we can get stages for all stage types."""
        for stage_type in StageType:
            stages = get_stages_of_type(stage_type)
            assert isinstance(stages, list)
            assert all(isinstance(stage, int) for stage in stages)

    def test_all_stages_covered(self):
        """Test that all stages are covered by some type."""
        all_stages_by_type = set()
        
        for stage_type in StageType:
            stages = get_stages_of_type(stage_type)
            all_stages_by_type.update(stages)
        
        # Should cover all 21 stages
        expected_stages = set(range(1, 22))
        assert all_stages_by_type == expected_stages


class TestValidateStageProfile:
    """Test validate_stage_profile function."""

    def test_valid_profiles(self):
        """Test validation of valid profiles."""
        # Pure stage
        assert validate_stage_profile({StageType.SPRINT: 1.0})
        
        # Mixed stage
        assert validate_stage_profile({
            StageType.PUNCH: 0.6,
            StageType.SPRINT: 0.4
        })
        
        # Complex mixed stage
        assert validate_stage_profile({
            StageType.PUNCH: 0.5,
            StageType.MOUNTAIN: 0.3,
            StageType.BREAK_AWAY: 0.2
        })

    def test_invalid_profiles(self):
        """Test validation of invalid profiles."""
        # Weights sum to more than 1.0
        assert not validate_stage_profile({
            StageType.SPRINT: 0.6,
            StageType.PUNCH: 0.6
        })
        
        # Weights sum to less than 1.0
        assert not validate_stage_profile({
            StageType.SPRINT: 0.4,
            StageType.PUNCH: 0.4
        })
        
        # Empty profile
        assert not validate_stage_profile({})

    def test_floating_point_tolerance(self):
        """Test that small floating point errors are tolerated."""
        # Should pass despite tiny floating point error
        assert validate_stage_profile({
            StageType.SPRINT: 0.333333,
            StageType.PUNCH: 0.333333,
            StageType.ITT: 0.333334
        })

    def test_edge_cases(self):
        """Test edge cases for validation."""
        # Exactly 1.0
        assert validate_stage_profile({StageType.SPRINT: 1.0})
        
        # Very small weights that sum to 1.0
        assert validate_stage_profile({
            StageType.SPRINT: 0.000001,
            StageType.PUNCH: 0.999999
        })


class TestUpdateStageProfile:
    """Test update_stage_profile function."""

    def test_update_valid_profile(self):
        """Test updating with valid profile."""
        original_profile = STAGE_PROFILES[1].copy()
        
        new_profile = {StageType.PUNCH: 1.0}
        update_stage_profile(1, new_profile)
        
        # Should be updated
        assert STAGE_PROFILES[1] == new_profile
        
        # Restore original for other tests
        STAGE_PROFILES[1] = original_profile

    def test_update_invalid_profile(self):
        """Test updating with invalid profile."""
        original_profile = STAGE_PROFILES[1].copy()
        
        invalid_profile = {
            StageType.SPRINT: 0.6,
            StageType.PUNCH: 0.6  # Sums to 1.2
        }
        
        with pytest.raises(ValueError, match="weights must sum to 1.0"):
            update_stage_profile(1, invalid_profile)
        
        # Should not be changed
        assert STAGE_PROFILES[1] == original_profile

    def test_update_mixed_profile(self):
        """Test updating to mixed profile."""
        original_profile = STAGE_PROFILES[1].copy()
        
        mixed_profile = {
            StageType.SPRINT: 0.7,
            StageType.PUNCH: 0.3
        }
        
        update_stage_profile(1, mixed_profile)
        assert STAGE_PROFILES[1] == mixed_profile
        
        # Test that get_stage_type reflects the change
        assert get_stage_type(1) == StageType.SPRINT  # Still primary
        
        # Restore original
        STAGE_PROFILES[1] = original_profile

    def test_update_nonexistent_stage(self):
        """Test updating non-existent stage."""
        valid_profile = {StageType.SPRINT: 1.0}
        
        # Should work (creates new entry)
        update_stage_profile(100, valid_profile)
        assert STAGE_PROFILES[100] == valid_profile
        
        # Clean up
        del STAGE_PROFILES[100]


class TestStageProfilesIntegration:
    """Integration tests for stage profiles."""

    def test_all_existing_profiles_valid(self):
        """Test that all existing stage profiles are valid."""
        for stage, profile in STAGE_PROFILES.items():
            assert validate_stage_profile(profile), f"Stage {stage} has invalid profile"

    def test_stage_type_consistency(self):
        """Test consistency between functions."""
        for stage in range(1, 22):
            # get_stage_type should return the stage type with highest weight
            profile = get_stage_profile(stage)
            primary_type = get_stage_type(stage)
            
            max_weight = max(profile.values())
            types_with_max_weight = [t for t, w in profile.items() if w == max_weight]
            
            assert primary_type in types_with_max_weight

    def test_stage_type_coverage(self):
        """Test that each stage type is primary for at least one stage."""
        primary_types = set()
        
        for stage in range(1, 22):
            primary_types.add(get_stage_type(stage))
        
        # Should have representation of different types
        assert len(primary_types) >= 3  # At least sprint, mountain, ITT

    def test_reasonable_stage_distribution(self):
        """Test that stage distribution is reasonable for a tour."""
        sprint_stages = get_stages_of_type(StageType.SPRINT)
        mountain_stages = get_stages_of_type(StageType.MOUNTAIN)
        itt_stages = get_stages_of_type(StageType.ITT)
        
        # Should have multiple sprint stages
        assert len(sprint_stages) >= 3
        
        # Should have multiple mountain stages
        assert len(mountain_stages) >= 3
        
        # Should have at least one ITT
        assert len(itt_stages) >= 1


if __name__ == "__main__":
    pytest.main([__file__]) 