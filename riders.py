import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict
from stage_profiles import StageType, get_stage_type, get_stage_profile
from rider_parameters import RiderParameters

# Define ability tiers and their corresponding scores
ABILITY_TIERS = {
    "S": 98,  # Exceptional
    "A": 95,  # Elite
    "B": 90,  # Very Good
    "C": 80,  # Good
    "D": 70,  # Average
    "E": 40   # Below Average
}

# Initialize rider abilities dictionary
rider_abilities: Dict[str, Dict[str, int]] = {}

# Helper to assign abilities based on tiers
def assign_abilities_by_tier(rider_tiers: Dict[str, str], skill: str):
    for rider, tier in rider_tiers.items():
        if rider not in rider_abilities:
            rider_abilities[rider] = {}
        rider_abilities[rider][skill] = ABILITY_TIERS[tier]

@dataclass
class Rider:
    name: str
    team: str
    parameters: RiderParameters
    age: int
    price: float = 0.0  # New: price in whatever unit you want
    chance_of_abandon: float = 0.0  # New: probability (0.0-1.0)

    def get_stage_probability(self, stage_number: int) -> Tuple[float, float, float]:
        """Get probability range for a specific stage based on rider's parameters."""
        stage_profile = get_stage_profile(stage_number)
        return self.parameters.get_weighted_probability_range(stage_profile)

class RiderDatabase:
    def __init__(self):
        self.riders = []
        self._initialize_riders()

    def _initialize_riders(self):
        # Initialize all riders from the 2025 Tour de France startlist
        rider_data = [
            {"name": "PITHIE Laurence", "team": "Red Bull - BORA - hansgrohe (WT)", "age": 24, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "VAN DIJKE Mick", "team": "Red Bull - BORA - hansgrohe (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "MOSCON Gianni", "team": "Red Bull - BORA - hansgrohe (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "MEEUS Jordi", "team": "Red Bull - BORA - hansgrohe (WT)", 
            "age": 25, "tiers": {'sprint': 'B', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "BRAET Vito", "team": "Intermarché - Wanty (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "RUTSCH Jonas", "team": "Intermarché - Wanty (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "VAN SINTMAARTENSDIJK Roel", "team": "Intermarché - Wanty (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "GRADEK Kamil", "team": "Bahrain - Victorious (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "HAIG Jack", "team": "Bahrain - Victorious (WT)", 
           "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'D', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "STANNARD Robert", "team": "Bahrain - Victorious (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "WRIGHT Fred", "team": "Bahrain - Victorious (WT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BOIVIN Guillaume", "team": "Israel - Premier Tech (PRT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "LOUVEL Matis", "team": "Israel - Premier Tech (PRT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "NEILANDS Krists", "team": "Israel - Premier Tech (PRT)", 
            "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'D', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "SWEENY Harry", "team": "EF Education - EasyPost (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "POWLESS Neilson", "team": "EF Education - EasyPost (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "break_away": "B", "punch": "D"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "HEALY Ben", "team": "EF Education - EasyPost (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "C", "mountain": "D", "break_away": "B", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "POGA\u010cAR Tadej", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "A", "mountain": "S", "break_away": "E", "punch": "A"}, "price": 7.5, "chance_of_abandon": 0.05},
            {"name": "ALMEIDA Jo\u00e3o", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "B", "mountain": "B", "break_away": "E", "punch": "B"}, "price": 4.5, "chance_of_abandon": 0.05},
            {"name": "YATES Adam", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "break_away": "E", "punch": "E"}, "price": 2.5, "chance_of_abandon": 0.05},
            {"name": "SIVAKOV Pavel", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "E", "punch": "E"}, "price": 2, "chance_of_abandon": 0.05},
            {"name": "SOLER Marc", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 2, "chance_of_abandon": 0.05},
            {"name": "WELLENS Tim", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "NARV\u00c1EZ Jhonatan", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "C"}, "price": 2, "chance_of_abandon": 0.05},
            {"name": "POLITT Nils", "team": "UAE Team Emirates - XRG (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "GALL Felix", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "break_away": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "ROGLI\u010c Primo\u017e", "team": "Red Bull - BORA - hansgrohe (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "A", "mountain": "B", "break_away": "E", "punch": "C"}, "price": 3.5, "chance_of_abandon": 0.05},
            {"name": "VLASOV Aleksandr", "team": "Red Bull - BORA - hansgrohe (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "D"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "VAN POPPEL Danny", "team": "Red Bull - BORA - hansgrohe (WT)", "age": 25, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "LIPOWITZ Florian", "team": "Red Bull - BORA - hansgrohe (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "B", "mountain": "B", "break_away": "E", "punch": "D"}, "price": 3, "chance_of_abandon": 0.05},
            {"name": "EVENEPOEL Remco", "team": "Soudal Quick-Step (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "S", "mountain": "B", "break_away": "E", "punch": "B"}, "price": 6, "chance_of_abandon": 0.05},
            {"name": "MERLIER Tim", "team": "Soudal Quick-Step (WT)", "age": 25, "tiers": {"sprint": "S", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 3.5, "chance_of_abandon": 0.05},
            {"name": "VAN LERBERGHE Bert", "team": "Soudal Quick-Step (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "EENKHOORN Pascal", "team": "Soudal Quick-Step (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "PARET-PEINTRE Valentin", "team": "Soudal Quick-Step (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "VAN WILDER Ilan", "team": "Soudal Quick-Step (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "SCHACHMANN Maximilian", "team": "Soudal Quick-Step (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "CATTANEO Mattia", "team": "Soudal Quick-Step (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "B", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "ARANBURU Alex", "team": "Cofidis (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "IZAGIRRE Ion", "team": "Cofidis (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "THOMAS Benjamin", "team": "Cofidis (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BUCHMANN Emanuel", "team": "Cofidis (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "VAN DER POEL Mathieu", "team": "Alpecin - Deceuninck (WT)", "age": 25, "tiers": {"sprint": "D", "itt": "C", "mountain": "E", "break_away": "A", "punch": "A"}, "price": 2.5, "chance_of_abandon": 0.05},
            {"name": "PHILIPSEN Jasper", "team": "Alpecin - Deceuninck (WT)", "age": 25, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "break_away": "E", "punch": "D"}, "price": 4, "chance_of_abandon": 0.05},
            {"name": "GROVES Kaden", "team": "Alpecin - Deceuninck (WT)", "age": 25, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 2, "chance_of_abandon": 0.05},
            {"name": "VAUQUELIN K\u00e9vin", "team": "Ark\u00e9a - B&B Hotels (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "C", "mountain": "D", "break_away": "B", "punch": "B"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "VINGEGAARD Jonas", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "A", "mountain": "A", "break_away": "E", "punch": "B"}, "price": 6, "chance_of_abandon": 0.05},
            {"name": "VAN AERT Wout", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "C", "itt": "A", "mountain": "E", "break_away": "A", "punch": "B"}, "price": 3.5, "chance_of_abandon": 0.05},
            {"name": "YATES Simon", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "break_away": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "JORGENSON Matteo", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "B", "mountain": "C", "break_away": "E", "punch": "C"}, "price": 3, "chance_of_abandon": 0.05},
            {"name": "AFFINI Edoardo", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "B", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "BENOOT Tiesj", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "KUSS Sepp", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "break_away": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "CAMPENAERTS Victor", "team": "Team Visma | Lease a Bike (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "RODR\u00cdGUEZ Carlos", "team": "INEOS Grenadiers (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "break_away": "E", "punch": "D"}, "price": 2.5, "chance_of_abandon": 0.05},
            {"name": "GANNA Filippo", "team": "INEOS Grenadiers (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "A", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "THOMAS Geraint", "team": "INEOS Grenadiers (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "ARENSMAN Thymen", "team": "INEOS Grenadiers (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "B", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "DE PLUS Laurens", "team": "INEOS Grenadiers (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "FOSS Tobias", "team": "INEOS Grenadiers (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "GIRMAY Biniam", "team": "Intermarch\u00e9 - Wanty (WT)", "age": 25, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "break_away": "C", "punch": "C"}, "price": 2.5, "chance_of_abandon": 0.05},
            {"name": "PAGE Hugo", "team": "Intermarch\u00e9 - Wanty (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "REX Laurenz", "team": "Intermarch\u00e9 - Wanty (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "ZIMMERMANN Georg", "team": "Intermarch\u00e9 - Wanty (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BARR\u00c9 Louis", "team": "Intermarch\u00e9 - Wanty (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "MILAN Jonathan", "team": "Lidl - Trek (WT)", "age": 25, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 4, "chance_of_abandon": 0.05},
            {"name": "SKJELMOSE Mattias", "team": "Lidl - Trek (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "C", "mountain": "C", "break_away": "D", "punch": "C"}, "price": 2.5, "chance_of_abandon": 0.05},
            {"name": "STUYVEN Jasper", "team": "Lidl - Trek (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "THEUNS Edward", "team": "Lidl - Trek (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "CONSONNI Simone", "team": "Lidl - Trek (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "NYS Thibau", "team": "Lidl - Trek (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "B", "punch": "B"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "MARTIN Guillaume", "team": "Groupama - FDJ (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "C", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "MADOUAS Valentin", "team": "Groupama - FDJ (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "C", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "GR\u00c9GOIRE Romain", "team": "Groupama - FDJ (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "break_away": "C", "punch": "B"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "PACHER Quentin", "team": "Groupama - FDJ (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "CASTRILLO Pablo", "team": "Movistar Team (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "MAS Enric", "team": "Movistar Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "break_away": "E", "punch": "D"}, "price": 2, "chance_of_abandon": 0.05},
            {"name": "OLIVEIRA Nelson", "team": "Movistar Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "RUBIO Einer", "team": "Movistar Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "ROMEO Iv\u00e1n", "team": "Movistar Team (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "ONLEY Oscar", "team": "Team Picnic PostNL (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "C", "punch": "D"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "VAN DEN BROEK Frank", "team": "Team Picnic PostNL (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "ANDRESEN Tobias Lund", "team": "Team Picnic PostNL (WT)", "age": 25, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "O'CONNOR Ben", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "break_away": "D", "punch": "D"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "DUNBAR Eddie", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "SCHMID Mauro", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "GROENEWEGEN Dylan", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "MEZGEC Luka", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "REINDERS Elmar", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "MARTINEZ Lenny", "team": "Bahrain - Victorious (WT)", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "break_away": "D", "punch": "D"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "BUITRAGO Santiago", "team": "Bahrain - Victorious (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "break_away": "D", "punch": "D"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "MOHORI\u010c Matej", "team": "Bahrain - Victorious (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BAUHAUS Phil", "team": "Bahrain - Victorious (WT)", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "VELASCO Simone", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "TEJADA Harold", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "CHAMPOUSSIN Cl\u00e9ment", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "C", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "HIGUITA Sergio", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "DE LIE Arnaud", "team": "Lotto (PRT)", "age": 25, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "VAN EETVELT Lennert", "team": "Lotto (PRT)", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "break_away": "D", "punch": "D"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "DE BUYST Jasper", "team": "Lotto (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BERCKMOES Jenno", "team": "Lotto (PRT)", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "DRIZNERS Jarrad", "team": "Lotto (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "SEP\u00daLVEDA Eduardo", "team": "Lotto (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "VAN MOER Brent", "team": "Lotto (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "ACKERMANN Pascal", "team": "Israel - Premier Tech (PRT)", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.05},
            {"name": "BLACKMORE Joseph", "team": "Israel - Premier Tech (PRT)", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "WOODS Michael", "team": "Israel - Premier Tech (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "LUTSENKO Alexey", "team": "Israel - Premier Tech (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "break_away": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "STEWART Jake", "team": "Israel - Premier Tech (PRT)", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "BURGAUDEAU Mathieu", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "ALAPHILIPPE Julian", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "C"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "CORT Magnus", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "W\u00c6RENSKJOLD S\u00f8ren", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "LEKNESSUND Andreas", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "JOHANNESSEN Tobias Halland", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "break_away": "C", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "JOHANNESSEN Anders Halland", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "ABRAHAMSEN Jonas", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "C", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "HOELGAARD Markus", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "FREDHEIM Stian", "team": "Uno-X Mobility (PRT)", "age": 25, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "ARMIRAIL Bruno", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "BISSEGGER Stefan", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "BERTHET Clément", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "NAESEN Oliver", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "PARET-PEINTRE Aurélien", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "SCOTSON Callum", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "TRONCHON Bastien", "team": "Decathlon AG2R La Mondiale Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "COQUARD Bryan", "team": "Cofidis (WT)", "age": 25, "tiers": {'sprint': 'C', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "RENARD Alexis", "team": "Cofidis (WT)", "age": 25, "tiers": {'sprint': 'D', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "TOUZÉ Damien", "team": "Cofidis (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "TEUNS Dylan", "team": "Cofidis (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'D'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "GARCÍA PIERNA Raúl", "team": "Arkéa - B&B Hotels (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "DÉMARE Arnaud", "team": "Arkéa - B&B Hotels (WT)", "age": 25, "tiers": {'sprint': 'C', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "CAPIOT Amaury", "team": "Arkéa - B&B Hotels (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "RODRÍGUEZ Cristián", "team": "Arkéa - B&B Hotels (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'D', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "COSTIOU Ewen", "team": "Arkéa - B&B Hotels (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'D'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "LE BERRE Mathis", "team": "Arkéa - B&B Hotels (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "VENTURINI Clément", "team": "Arkéa - B&B Hotels (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'D'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "SKUJIŅŠ Toms", "team": "Lidl - Trek (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "SIMMONS Quinn", "team": "Lidl - Trek (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "ASKEY Lewis", "team": "Groupama - FDJ (WT)", "age": 25, "tiers": {'sprint': 'D', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BARTHE Cyril", "team": "Groupama - FDJ (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "PENHOËT Paul", "team": "Groupama - FDJ (WT)", "age": 25, "tiers": {'sprint': 'D', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "RUSSO Clément", "team": "Groupama - FDJ (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "MÜHLBERGER Gregor", "team": "Movistar Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BARTA Will", "team": "Movistar Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "GARCÍA CORTINA Iván", "team": "Movistar Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "NABERMAN Tim", "team": "Team Picnic PostNL (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BARGUIL Warren", "team": "Team Picnic PostNL (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'D', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "FLYNN Sean", "team": "Team Picnic PostNL (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "BITTNER Pavel", "team": "Team Picnic PostNL (WT)", "age": 25, "tiers": {'sprint': 'D', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "MÄRKL Niklas", "team": "Team Picnic PostNL (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "PLAPP Luke", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'C', 'mountain': 'E', 'break_away': 'D', 'punch': 'D'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "DURBRIDGE Luke", "team": "Team Jayco AlUla (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'D', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "TEUNISSEN Mike", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "FEDOROV Yevgeniy", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "BALLERINI Davide", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {'sprint': 'D', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "BOL Cees", "team": "XDS Astana Team (WT)", "age": 25, "tiers": {'sprint': 'D', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "JEANNIÈRE Emilien", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {'sprint': 'C', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "TURGIS Anthony", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'D'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "JEGAT Jordan", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'D', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "DELETTRE Alexandre", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "CRAS Steff", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'D', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "VERCHER Mattéo", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "GACHIGNARD Thomas", "team": "Team TotalEnergies (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "DAINESE Alberto", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {'sprint': 'C', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 1, "chance_of_abandon": 0.05},
            {"name": "HALLER Marco", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "HIRSCHI Marc", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'C', 'punch': 'C'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "LIENHARD Fabian", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "MAYRHOFER Marius", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'E', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {"name": "STORER Michael", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'C', 'break_away': 'D', 'punch': 'E'}, "price": 0.75, "chance_of_abandon": 0.05},
            {"name": "TRENTIN Matteo", "team": "Tudor Pro Cycling Team (PRT)", "age": 25, "tiers": {'sprint': 'E', 'itt': 'E', 'mountain': 'E', 'break_away': 'D', 'punch': 'E'}, "price": 0.5, "chance_of_abandon": 0.05},
            {
                "name": "ASGREEN Kasper",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "C",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VAN DEN BERG Marijn",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "C",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.75,
                "chance_of_abandon": 0.05
            },
            {
                "name": "BAUDIN Alex",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "D",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VALGREN Michael",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "D",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "ALBANESE Vincenzo",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "D",
                "punch": "D"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "RICKAERT Jonas",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VERSTRYNGE Emiel",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "D",
                "break_away": "D",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "MEURISSE Xandro",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "D",
                "break_away": "D",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "DILLIER Silvan",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VERMEERSCH Gianni",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "LAURANCE Axel",
                "team": "INEOS Grenadiers (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "D",
                "punch": "D"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "SWIFT Connor",
                "team": "INEOS Grenadiers (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "SWIFT Ben",
                "team": "INEOS Grenadiers (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "GRIGNARD S\u00e9bastien",
                "team": "Lotto (PRT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            }
            {
                "name": "ASGREEN Kasper",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "C",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VAN DEN BERG Marijn",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "D",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "D"
                },
                "price": 0.75,
                "chance_of_abandon": 0.05
            },
            {
                "name": "BAUDIN Alex",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VALGREN Michael",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "ALBANESE Vincenzo",
                "team": "EF Education - EasyPost (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "D",
                "punch": "D"
                },
                "price": 0.75,
                "chance_of_abandon": 0.05
            },
            {
                "name": "RICKAERT Jonas",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VERSTRYNGE Emiel",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "D",
                "break_away": "D",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "MEURISSE Xandro",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "DILLIER Silvan",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "VERMEERSCH Gianni",
                "team": "Alpecin - Deceuninck (WT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "D",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            },
            {
                "name": "GRIGNARD S\u00e9bastien",
                "team": "Lotto (PRT)",
                "age": 25,
                "tiers": {
                "sprint": "E",
                "itt": "E",
                "mountain": "E",
                "break_away": "E",
                "punch": "E"
                },
                "price": 0.5,
                "chance_of_abandon": 0.05
            }
        ]

        # Create Rider objects with their parameters
        self.riders = []
        for rider_info in rider_data:
            # Convert tier letters to numerical values using ABILITY_TIERS
            parameters = RiderParameters(
                sprint_ability=ABILITY_TIERS[rider_info["tiers"]["sprint"]],
                punch_ability=ABILITY_TIERS[rider_info["tiers"]["punch"]],
                itt_ability=ABILITY_TIERS[rider_info["tiers"]["itt"]],
                mountain_ability=ABILITY_TIERS[rider_info["tiers"]["mountain"]],
                break_away_ability=ABILITY_TIERS[rider_info["tiers"]["break_away"]]
            )
            self.riders.append(Rider(
                rider_info["name"],
                rider_info["team"],
                parameters,
                rider_info["age"],
                price=rider_info["price"],
                chance_of_abandon=rider_info["chance_of_abandon"]
            ))

    def get_rider(self, name: str) -> Rider:
        """Get a rider by name."""
        for rider in self.riders:
            if rider.name == name:
                return rider
        raise ValueError(f"Rider {name} not found")

    def get_all_riders(self) -> List[Rider]:
        """Get all riders in the database."""
        return self.riders

    def generate_stage_result(self, rider: Rider, stage: int) -> float:
        """Generate a result for a rider in a specific stage using triangular distribution."""
        # Stage numbers in STAGE_PROFILES are 1-based, but stage parameter is already 1-based
        min_val, mode, max_val = rider.get_stage_probability(stage)
        return np.random.triangular(min_val, mode, max_val)

    def get_youth_riders(self, age_limit: int = 25) -> List[Rider]:
        return [r for r in self.riders if r.age <= age_limit]

# Create a global instance of the rider database
rider_db = RiderDatabase() 