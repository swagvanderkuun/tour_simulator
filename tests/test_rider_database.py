"""
Tests for flexible rider database system.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd

from tour_simulator.services.rider_database import (
    RiderData, StartingList, FlexibleRiderDatabase
)
from tour_simulator.core.riders import Rider


class TestRiderData:
    """Test RiderData class."""
    
    def test_rider_data_creation(self):
        """Test basic rider data creation."""
        rider = RiderData(
            name="Test Rider",
            team="Test Team",
            age=25,
            nationality="Test Country",
            tier_abilities={
                "sprint": "B",
                "punch": "C", 
                "itt": "A",
                "mountain": "D",
                "break_away": "E"
            },
            price=2.5,
            chance_of_abandon=0.08
        )
        
        assert rider.name == "Test Rider"
        assert rider.team == "Test Team"
        assert rider.age == 25
        assert rider.nationality == "Test Country"
        assert rider.tier_abilities["sprint"] == "B"
        assert rider.price == 2.5
        assert rider.chance_of_abandon == 0.08
    
    def test_rider_data_defaults(self):
        """Test rider data with default values."""
        rider = RiderData(
            name="Test Rider",
            team="Test Team",
            age=25,
            nationality="Test Country",
            tier_abilities={"sprint": "E", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}
        )
        
        assert rider.price == 0.0
        assert rider.chance_of_abandon == 0.05
        assert rider.pcs_id is None
        assert rider.uci_points is None
    
    def test_to_rider_conversion(self):
        """Test converting RiderData to Rider object."""
        rider_data = RiderData(
            name="Tadej POGAČAR",
            team="UAE Team Emirates",
            age=26,
            nationality="Slovenia",
            tier_abilities={
                "sprint": "E",
                "punch": "A", 
                "itt": "A",
                "mountain": "S",
                "break_away": "E"
            },
            price=7.5,
            chance_of_abandon=0.05
        )
        
        rider = rider_data.to_rider()
        
        assert isinstance(rider, Rider)
        assert rider.name == "Tadej POGAČAR"
        assert rider.team == "UAE Team Emirates"
        assert rider.age == 26
        assert rider.price == 7.5
        assert rider.chance_of_abandon == 0.05
        
        # Check that abilities were converted correctly
        assert rider.parameters.mountain_ability == 98  # S tier
        assert rider.parameters.itt_ability == 95  # A tier
        assert rider.parameters.punch_ability == 95  # A tier
        assert rider.parameters.sprint_ability == 40  # E tier
        assert rider.parameters.break_away_ability == 40  # E tier


class TestStartingList:
    """Test StartingList class."""
    
    def test_starting_list_creation(self):
        """Test basic starting list creation."""
        riders = [
            RiderData("Rider 1", "Team 1", 25, "Country 1", {"sprint": "A", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}),
            RiderData("Rider 2", "Team 2", 26, "Country 2", {"sprint": "E", "punch": "E", "itt": "E", "mountain": "A", "break_away": "E"})
        ]
        
        starting_list = StartingList(
            race_name="Test Race",
            year=2025,
            riders=riders,
            created_date=datetime.now(),
            source="manual"
        )
        
        assert starting_list.race_name == "Test Race"
        assert starting_list.year == 2025
        assert len(starting_list.riders) == 2
        assert starting_list.source == "manual"
    
    def test_starting_list_save_and_load(self):
        """Test saving and loading starting list."""
        with tempfile.TemporaryDirectory() as temp_dir:
            filepath = Path(temp_dir) / "test_startlist.json"
            
            # Create starting list
            riders = [
                RiderData(
                    name="Test Rider",
                    team="Test Team",
                    age=25,
                    nationality="Test Country",
                    tier_abilities={"sprint": "B", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"},
                    price=1.5,
                    pcs_id="test-rider-123"
                )
            ]
            
            starting_list = StartingList(
                race_name="Test Race",
                year=2025,
                riders=riders,
                created_date=datetime(2024, 1, 1, 12, 0, 0),
                source="procyclingstats"
            )
            
            # Save
            starting_list.save_to_file(filepath)
            
            # Load
            loaded_list = StartingList.load_from_file(filepath)
            
            assert loaded_list.race_name == "Test Race"
            assert loaded_list.year == 2025
            assert loaded_list.source == "procyclingstats"
            assert len(loaded_list.riders) == 1
            
            loaded_rider = loaded_list.riders[0]
            assert loaded_rider.name == "Test Rider"
            assert loaded_rider.team == "Test Team"
            assert loaded_rider.tier_abilities["sprint"] == "B"
            assert loaded_rider.price == 1.5
            assert loaded_rider.pcs_id == "test-rider-123"


class TestFlexibleRiderDatabase:
    """Test FlexibleRiderDatabase class."""
    
    def test_database_initialization(self):
        """Test database initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            assert db.data_dir == Path(temp_dir)
            assert db.current_starting_list is None
            assert len(db.master_database) == 0
    
    def test_add_and_get_rider(self):
        """Test adding and getting riders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            rider = RiderData(
                name="Test Rider",
                team="Test Team",
                age=25,
                nationality="Test Country",
                tier_abilities={"sprint": "A", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}
            )
            
            db.add_rider(rider)
            
            retrieved = db.get_rider("Test Rider")
            assert retrieved is not None
            assert retrieved.name == "Test Rider"
            assert retrieved.team == "Test Team"
            
            # Test non-existent rider
            assert db.get_rider("Non-existent") is None
    
    def test_update_rider(self):
        """Test updating rider information."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            # Add original rider
            rider = RiderData(
                name="Test Rider",
                team="Old Team",
                age=25,
                nationality="Test Country",
                tier_abilities={"sprint": "C", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}
            )
            db.add_rider(rider)
            
            # Update rider
            updated_rider = RiderData(
                name="Test Rider",
                team="New Team",
                age=26,
                nationality="Test Country",
                tier_abilities={"sprint": "B", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}
            )
            db.update_rider(updated_rider)
            
            # Verify update
            retrieved = db.get_rider("Test Rider")
            assert retrieved.team == "New Team"
            assert retrieved.age == 26
            assert retrieved.tier_abilities["sprint"] == "B"
    
    def test_search_riders(self):
        """Test searching for riders."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            # Add test riders
            riders = [
                RiderData("Jonas VINGEGAARD", "Team Visma", 27, "Denmark", {"sprint": "E", "punch": "E", "itt": "A", "mountain": "A", "break_away": "E"}),
                RiderData("Tadej POGAČAR", "UAE Emirates", 26, "Slovenia", {"sprint": "E", "punch": "A", "itt": "A", "mountain": "S", "break_away": "E"}),
                RiderData("Primož ROGLIČ", "Bora-hansgrohe", 34, "Slovenia", {"sprint": "E", "punch": "C", "itt": "A", "mountain": "B", "break_away": "E"}),
                RiderData("Remco EVENEPOEL", "Soudal Quick-Step", 24, "Belgium", {"sprint": "E", "punch": "B", "itt": "S", "mountain": "A", "break_away": "E"})
            ]
            
            for rider in riders:
                db.add_rider(rider)
            
            # Search by name pattern
            results = db.search_riders(name_pattern="POGA")
            assert len(results) == 1
            assert results[0].name == "Tadej POGAČAR"
            
            # Search by team
            results = db.search_riders(team="Visma")
            assert len(results) == 1
            assert results[0].name == "Jonas VINGEGAARD"
            
            # Search by nationality
            results = db.search_riders(nationality="Slovenia")
            assert len(results) == 2
            names = [r.name for r in results]
            assert "Tadej POGAČAR" in names
            assert "Primož ROGLIČ" in names
    
    def test_create_starting_list(self):
        """Test creating starting list from rider names."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            # Add riders to master database
            riders = [
                RiderData("Rider 1", "Team 1", 25, "Country 1", {"sprint": "A", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}),
                RiderData("Rider 2", "Team 2", 26, "Country 2", {"sprint": "E", "punch": "E", "itt": "E", "mountain": "A", "break_away": "E"}),
                RiderData("Rider 3", "Team 3", 27, "Country 3", {"sprint": "E", "punch": "E", "itt": "A", "mountain": "E", "break_away": "E"})
            ]
            
            for rider in riders:
                db.add_rider(rider)
            
            # Create starting list
            rider_names = ["Rider 1", "Rider 3", "Non-existent Rider"]
            starting_list = db.create_starting_list("Test Race", 2025, rider_names)
            
            assert starting_list.race_name == "Test Race"
            assert starting_list.year == 2025
            assert len(starting_list.riders) == 2  # Only found riders
            
            names = [r.name for r in starting_list.riders]
            assert "Rider 1" in names
            assert "Rider 3" in names
            assert "Non-existent Rider" not in names
    
    def test_get_simulation_riders(self):
        """Test getting riders for simulation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            # Add riders and create starting list
            riders = [
                RiderData("Rider 1", "Team 1", 25, "Country 1", {"sprint": "A", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}),
                RiderData("Rider 2", "Team 2", 26, "Country 2", {"sprint": "E", "punch": "E", "itt": "E", "mountain": "A", "break_away": "E"})
            ]
            
            for rider in riders:
                db.add_rider(rider)
            
            db.create_starting_list("Test Race", 2025, ["Rider 1", "Rider 2"])
            
            # Get simulation riders
            sim_riders = db.get_simulation_riders()
            
            assert len(sim_riders) == 2
            assert all(isinstance(r, Rider) for r in sim_riders)
            
            names = [r.name for r in sim_riders]
            assert "Rider 1" in names
            assert "Rider 2" in names
    
    def test_save_and_load_master_database(self):
        """Test saving and loading master database."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create database and add riders
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            riders = [
                RiderData("Rider 1", "Team 1", 25, "Country 1", {"sprint": "A", "punch": "E", "itt": "E", "mountain": "E", "break_away": "E"}),
                RiderData("Rider 2", "Team 2", 26, "Country 2", {"sprint": "E", "punch": "E", "itt": "E", "mountain": "A", "break_away": "E"})
            ]
            
            for rider in riders:
                db.add_rider(rider)
            
            # Save database
            db.save_master_database()
            
            # Create new database instance and verify it loads the data
            db2 = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            assert len(db2.master_database) == 2
            assert db2.get_rider("Rider 1") is not None
            assert db2.get_rider("Rider 2") is not None
    
    def test_import_from_dataframe(self):
        """Test importing riders from pandas DataFrame."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            # Create test DataFrame
            data = {
                "name": ["Rider 1", "Rider 2", "Rider 3"],
                "team": ["Team A", "Team B", "Team C"],
                "age": [25, 26, 27],
                "nationality": ["Country 1", "Country 2", "Country 3"],
                "sprint_tier": ["A", "E", "C"],
                "mountain_tier": ["E", "A", "E"],
                "itt_tier": ["E", "E", "B"],
                "price": [2.0, 3.5, 1.5],
                "uci_points": [100, 200, 150]
            }
            
            df = pd.DataFrame(data)
            
            # Import riders
            imported_count = db.import_from_dataframe(df)
            
            assert imported_count == 3
            assert len(db.master_database) == 3
            
            # Verify imported data
            rider1 = db.get_rider("Rider 1")
            assert rider1.team == "Team A"
            assert rider1.tier_abilities["sprint"] == "A"
            assert rider1.tier_abilities["mountain"] == "E"
            assert rider1.price == 2.0
            assert rider1.uci_points == 100
    
    def test_list_available_starting_lists(self):
        """Test listing available starting lists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            # Create some test starting list files
            test_files = [
                "tour_de_france_2025_startlist.json",
                "vuelta_a_espana_2025_startlist.json",
                "giro_d_italia_2024_startlist.json"
            ]
            
            for filename in test_files:
                filepath = Path(temp_dir) / filename
                filepath.touch()  # Create empty file
            
            # Also create a non-startlist file
            (Path(temp_dir) / "other_file.json").touch()
            
            available = db.list_available_starting_lists()
            
            # Should find the startlist files but not the other file
            assert len(available) == 3
            
            race_names = [item["race_name"] for item in available]
            assert "Tour De France" in race_names
            assert "Vuelta A Espana" in race_names
            assert "Giro D Italia" in race_names


class TestIntegration:
    """Integration tests for rider database system."""
    
    def test_full_rider_database_workflow(self):
        """Test complete workflow of rider database operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            
            # Step 1: Add riders to master database
            riders = [
                RiderData("Jonas VINGEGAARD", "Team Visma", 27, "Denmark", 
                         {"sprint": "E", "punch": "E", "itt": "A", "mountain": "A", "break_away": "E"},
                         price=5.0, chance_of_abandon=0.05),
                RiderData("Tadej POGAČAR", "UAE Emirates", 26, "Slovenia",
                         {"sprint": "E", "punch": "A", "itt": "A", "mountain": "S", "break_away": "E"},
                         price=7.5, chance_of_abandon=0.05),
                RiderData("Remco EVENEPOEL", "Soudal Quick-Step", 24, "Belgium",
                         {"sprint": "E", "punch": "B", "itt": "S", "mountain": "A", "break_away": "E"},
                         price=6.0, chance_of_abandon=0.05)
            ]
            
            for rider in riders:
                db.add_rider(rider)
            
            # Step 2: Save master database
            db.save_master_database()
            
            # Step 3: Create starting list
            starting_list = db.create_starting_list(
                "Tour de France", 
                2025, 
                ["Jonas VINGEGAARD", "Tadej POGAČAR", "Remco EVENEPOEL"]
            )
            
            # Step 4: Save starting list
            db.save_current_starting_list()
            
            # Step 5: Create new database instance and load starting list
            db2 = FlexibleRiderDatabase(data_dir=Path(temp_dir))
            success = db2.load_starting_list("Tour de France", 2025)
            
            assert success
            assert db2.current_starting_list is not None
            assert len(db2.current_starting_list.riders) == 3
            
            # Step 6: Get simulation riders
            sim_riders = db2.get_simulation_riders()
            
            assert len(sim_riders) == 3
            assert all(isinstance(r, Rider) for r in sim_riders)
            
            # Verify rider conversion worked correctly
            pogacar = next(r for r in sim_riders if r.name == "Tadej POGAČAR")
            assert pogacar.parameters.mountain_ability == 98  # S tier
            assert pogacar.price == 7.5 