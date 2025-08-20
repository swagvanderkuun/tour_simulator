"""
Flexible rider database system for multiple stage races.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Set
import json
from pathlib import Path
import pandas as pd
from datetime import datetime

from ..core.riders import Rider, ABILITY_TIERS
from ..models.rider_parameters import RiderParameters


@dataclass
class RiderData:
    """Extended rider data with additional metadata."""
    name: str
    team: str
    age: int
    nationality: str
    tier_abilities: Dict[str, str]  # ability_name -> tier (S, A, B, C, D, E)
    price: float = 0.0
    chance_of_abandon: float = 0.05
    pcs_id: Optional[str] = None  # procyclingstats ID
    uci_points: Optional[int] = None
    
    def to_rider(self) -> Rider:
        """Convert to Rider object for simulation."""
        # Convert tier letters to numerical values
        parameters = RiderParameters(
            sprint_ability=ABILITY_TIERS[self.tier_abilities.get("sprint", "E")],
            punch_ability=ABILITY_TIERS[self.tier_abilities.get("punch", "E")],
            itt_ability=ABILITY_TIERS[self.tier_abilities.get("itt", "E")],
            mountain_ability=ABILITY_TIERS[self.tier_abilities.get("mountain", "E")],
            break_away_ability=ABILITY_TIERS[self.tier_abilities.get("break_away", "E")]
        )
        
        return Rider(
            name=self.name,
            team=self.team,
            parameters=parameters,
            age=self.age,
            price=self.price,
            chance_of_abandon=self.chance_of_abandon
        )


@dataclass
class StartingList:
    """Starting list for a specific race."""
    race_name: str
    year: int
    riders: List[RiderData]
    created_date: datetime
    source: str = "manual"  # "manual", "procyclingstats", etc.
    
    def save_to_file(self, filepath: Path) -> None:
        """Save starting list to JSON file."""
        data = {
            "race_name": self.race_name,
            "year": self.year,
            "created_date": self.created_date.isoformat(),
            "source": self.source,
            "riders": [
                {
                    "name": rider.name,
                    "team": rider.team,
                    "age": rider.age,
                    "nationality": rider.nationality,
                    "tier_abilities": rider.tier_abilities,
                    "price": rider.price,
                    "chance_of_abandon": rider.chance_of_abandon,
                    "pcs_id": rider.pcs_id,
                    "uci_points": rider.uci_points
                }
                for rider in self.riders
            ]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: Path) -> 'StartingList':
        """Load starting list from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        riders = []
        for rider_data in data["riders"]:
            rider = RiderData(
                name=rider_data["name"],
                team=rider_data["team"],
                age=rider_data["age"],
                nationality=rider_data["nationality"],
                tier_abilities=rider_data["tier_abilities"],
                price=rider_data.get("price", 0.0),
                chance_of_abandon=rider_data.get("chance_of_abandon", 0.05),
                pcs_id=rider_data.get("pcs_id"),
                uci_points=rider_data.get("uci_points")
            )
            riders.append(rider)
        
        return cls(
            race_name=data["race_name"],
            year=data["year"],
            riders=riders,
            created_date=datetime.fromisoformat(data["created_date"]),
            source=data.get("source", "manual")
        )


class FlexibleRiderDatabase:
    """Flexible rider database that can handle multiple races and starting lists."""
    
    def __init__(self, data_dir: Optional[Path] = None):
        """Initialize the database."""
        self.data_dir = data_dir or Path("data/riders")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Current active starting list
        self.current_starting_list: Optional[StartingList] = None
        
        # Master rider database (all known riders)
        self.master_database: Dict[str, RiderData] = {}
        
        # Load master database if it exists
        self._load_master_database()
    
    def _load_master_database(self) -> None:
        """Load master rider database from file."""
        master_file = self.data_dir / "master_riders.json"
        if master_file.exists():
            try:
                with open(master_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for rider_data in data["riders"]:
                    rider = RiderData(
                        name=rider_data["name"],
                        team=rider_data.get("team", "Unknown"),
                        age=rider_data["age"],
                        nationality=rider_data.get("nationality", "Unknown"),
                        tier_abilities=rider_data["tier_abilities"],
                        price=rider_data.get("price", 0.0),
                        chance_of_abandon=rider_data.get("chance_of_abandon", 0.05),
                        pcs_id=rider_data.get("pcs_id"),
                        uci_points=rider_data.get("uci_points")
                    )
                    self.master_database[rider.name] = rider
            except Exception as e:
                print(f"Warning: Could not load master database: {e}")
    
    def save_master_database(self) -> None:
        """Save master rider database to file."""
        master_file = self.data_dir / "master_riders.json"
        data = {
            "last_updated": datetime.now().isoformat(),
            "total_riders": len(self.master_database),
            "riders": [
                {
                    "name": rider.name,
                    "team": rider.team,
                    "age": rider.age,
                    "nationality": rider.nationality,
                    "tier_abilities": rider.tier_abilities,
                    "price": rider.price,
                    "chance_of_abandon": rider.chance_of_abandon,
                    "pcs_id": rider.pcs_id,
                    "uci_points": rider.uci_points
                }
                for rider in self.master_database.values()
            ]
        }
        
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_rider(self, rider: RiderData) -> None:
        """Add a rider to the master database."""
        self.master_database[rider.name] = rider
    
    def update_rider(self, rider: RiderData) -> None:
        """Update a rider in the master database."""
        self.master_database[rider.name] = rider
    
    def get_rider(self, name: str) -> Optional[RiderData]:
        """Get a rider from the master database."""
        return self.master_database.get(name)
    
    def search_riders(self, name_pattern: str = None, team: str = None, 
                     nationality: str = None) -> List[RiderData]:
        """Search for riders in the master database."""
        results = []
        for rider in self.master_database.values():
            if name_pattern and name_pattern.lower() not in rider.name.lower():
                continue
            if team and team.lower() not in rider.team.lower():
                continue
            if nationality and nationality.lower() != rider.nationality.lower():
                continue
            results.append(rider)
        return results
    
    def load_starting_list(self, race_name: str, year: int) -> bool:
        """Load starting list for a specific race."""
        filename = f"{race_name.lower().replace(' ', '_')}_{year}_startlist.json"
        filepath = self.data_dir / filename
        
        if filepath.exists():
            self.current_starting_list = StartingList.load_from_file(filepath)
            return True
        return False
    
    def create_starting_list(self, race_name: str, year: int, rider_names: List[str]) -> StartingList:
        """Create a new starting list from rider names."""
        riders = []
        missing_riders = []
        
        for name in rider_names:
            rider = self.get_rider(name)
            if rider:
                riders.append(rider)
            else:
                missing_riders.append(name)
        
        if missing_riders:
            print(f"Warning: {len(missing_riders)} riders not found in master database:")
            for name in missing_riders[:5]:  # Show first 5
                print(f"  - {name}")
            if len(missing_riders) > 5:
                print(f"  ... and {len(missing_riders) - 5} more")
        
        starting_list = StartingList(
            race_name=race_name,
            year=year,
            riders=riders,
            created_date=datetime.now()
        )
        
        self.current_starting_list = starting_list
        return starting_list
    
    def save_current_starting_list(self) -> None:
        """Save the current starting list to file."""
        if not self.current_starting_list:
            raise ValueError("No starting list loaded")
        
        filename = f"{self.current_starting_list.race_name.lower().replace(' ', '_')}_{self.current_starting_list.year}_startlist.json"
        filepath = self.data_dir / filename
        self.current_starting_list.save_to_file(filepath)
    
    def get_simulation_riders(self) -> List[Rider]:
        """Get riders for simulation from current starting list."""
        if not self.current_starting_list:
            raise ValueError("No starting list loaded")
        
        return [rider_data.to_rider() for rider_data in self.current_starting_list.riders]
    
    def list_available_starting_lists(self) -> List[Dict[str, str]]:
        """List all available starting lists."""
        starting_lists = []
        for file in self.data_dir.glob("*_startlist.json"):
            try:
                # Parse filename: race_name_year_startlist.json
                parts = file.stem.split("_")
                if len(parts) >= 3 and parts[-1] == "startlist":
                    year = parts[-2]
                    race_name = "_".join(parts[:-2]).replace("_", " ").title()
                    starting_lists.append({
                        "race_name": race_name,
                        "year": year,
                        "filename": file.name
                    })
            except Exception:
                continue
        
        return starting_lists
    
    def import_from_dataframe(self, df: pd.DataFrame) -> int:
        """Import riders from a pandas DataFrame."""
        imported_count = 0
        
        required_columns = ["name", "team", "age"]
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"DataFrame must contain columns: {required_columns}")
        
        for _, row in df.iterrows():
            # Default tier abilities (can be updated later)
            tier_abilities = {
                "sprint": row.get("sprint_tier", "E"),
                "punch": row.get("punch_tier", "E"),
                "itt": row.get("itt_tier", "E"),
                "mountain": row.get("mountain_tier", "E"),
                "break_away": row.get("break_away_tier", "E")
            }
            
            rider = RiderData(
                name=row["name"],
                team=row["team"],
                age=int(row["age"]),
                nationality=row.get("nationality", "Unknown"),
                tier_abilities=tier_abilities,
                price=float(row.get("price", 0.0)),
                chance_of_abandon=float(row.get("chance_of_abandon", 0.05)),
                pcs_id=row.get("pcs_id"),
                uci_points=int(row["uci_points"]) if pd.notna(row.get("uci_points")) else None
            )
            
            self.add_rider(rider)
            imported_count += 1
        
        return imported_count 