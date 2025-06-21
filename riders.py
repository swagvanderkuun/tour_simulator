import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict
from stage_profiles import StageType, get_stage_type
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
        stage_type = get_stage_type(stage_number)
        return self.parameters.get_probability_range(stage_type.value)

class RiderDatabase:
    def __init__(self):
        self.riders = []
        self._initialize_riders()

    def _initialize_riders(self):
        # Initialize all riders from the 2025 Tour de France startlist
        rider_data = [
            # EF Education - EasyPost
            {"name": "Richard Carapaz", "team": "EF Education - EasyPost", "age": 30, "tiers": {"sprint": "E", "itt": "D", "mountain": "B", "hills": "D", "punch": "C"}, "price": 1.5, "chance_of_abandon": 0.},
            {"name": "Harry Sweeny", "team": "EF Education - EasyPost", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Neilson Powless", "team": "EF Education - EasyPost", "age": 30, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "hills": "B", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Ben Healy", "team": "EF Education - EasyPost", "age": 22, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "B", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            
            # UAE Team Emirates - XRG
            {"name": "Tadej Pogačar", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "A", "mountain": "S", "hills": "A", "punch": "A"}, "price": 7.5, "chance_of_abandon": 0.0},
            {"name": "João Almeida", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "B", "mountain": "A", "hills": "E", "punch": "C"}, "price": 4.5, "chance_of_abandon": 0.0},
            {"name": "Adam Yates", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "hills": "E", "punch": "E"}, "price": 2.5, "chance_of_abandon": 0.0},
            {"name": "Pavel Sivakov", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}, "price": 2, "chance_of_abandon": 0.0},
            {"name": "Marc Soler", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "D", "punch": "E"}, "price": 2, "chance_of_abandon": 0.0},
            {"name": "Tim Wellens", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Jhonatan Narváez", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "C", "punch": "E"}, "price": 2, "chance_of_abandon": 0.0},
            {"name": "Domen Novak", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Nils Politt", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            
            # Decathlon AG2R La Mondiale Team
            {"name": "Felix Gall", "team": "Decathlon AG2R La Mondiale Team", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "B", "hills": "E", "punch": "E"}, "price": 1.500000, "chance_of_abandon": 0.0},
            
            # Red Bull - BORA - hansgrohe
            {"name": "Primož Roglič", "team": "Red Bull - BORA - hansgrohe", "age": 30, "tiers": {"sprint": "E", "itt": "A", "mountain": "A", "hills": "E", "punch": "C"}, "price": 3.500000, "chance_of_abandon": 0.0},
            {"name": "Daniel Felipe Martínez", "team": "Red Bull - BORA - hansgrohe", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1.000000, "chance_of_abandon": 0.0},
            {"name": "Aleksandr Vlasov", "team": "Red Bull - BORA - hansgrohe", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 7.50000, "chance_of_abandon": 0.0},
            {"name": "Jan Tratnik", "team": "Red Bull - BORA - hansgrohe", "age": 30, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "hills": "E", "punch": "E"}, "price": 5.00000, "chance_of_abandon": 0.0},
            {"name": "Danny van Poppel", "team": "Red Bull - BORA - hansgrohe", "age": 27, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.750000, "chance_of_abandon": 0.0},
            {"name": "Florian Lipowitz", "team": "Red Bull - BORA - hansgrohe", "age": 23, "tiers": {"sprint": "E", "itt": "B", "mountain": "B", "hills": "B", "punch": "C"}, "price": 3.000000, "chance_of_abandon": 0.0},
            
            # Soudal Quick-Step
            {"name": "Remco Evenepoel", "team": "Soudal Quick-Step", "age": 24, "tiers": {"sprint": "E", "itt": "S", "mountain": "A", "hills": "B", "punch": "B"}, "price": 6.000000, "chance_of_abandon": 0.0},
            {"name": "Tim Merlier", "team": "Soudal Quick-Step", "age": 31, "tiers": {"sprint": "S", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 3.500000, "chance_of_abandon": 0.0},
            {"name": "Bert Van Lerberghe", "team": "Soudal Quick-Step", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.500000, "chance_of_abandon": 0.0},
            {"name": "Pascal Eenkhoorn", "team": "Soudal Quick-Step", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.500000, "chance_of_abandon": 0.0},
            
            # Cofidis
            {"name": "Alex Aranburu", "team": "Cofidis", "age": 27, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "C", "punch": "E"}, "price": 0.750000, "chance_of_abandon": 0.0},
            {"name": "Ion Izagirre", "team": "Cofidis", "age": 28, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "hills": "D", "punch": "D"}, "price": 0.500000, "chance_of_abandon": 0.0},
            {"name": "Benjamin Thomas", "team": "Cofidis", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.500000, "chance_of_abandon": 0.0},
            {"name": "Emanuel Buchmann", "team": "Cofidis", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.500000, "chance_of_abandon": 0.0},
            {"name": "Simon Carr", "team": "Cofidis", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.500000, "chance_of_abandon": 0.0},
            
            # Alpecin - Deceuninck
            {"name": "Mathieu van der Poel", "team": "Alpecin - Deceuninck", "age": 25, "tiers": {"sprint": "C", "itt": "C", "mountain": "E", "hills": "A", "punch": "A"}, "price": 2.500000, "chance_of_abandon": 0.0},
            {"name": "Jasper Philipsen", "team": "Alpecin - Deceuninck", "age": 26, "tiers": {"sprint": "S", "itt": "E", "mountain": "E", "hills": "C", "punch": "C"}, "price": 4.000000, "chance_of_abandon": 0.0},
            {"name": "Kaden Groves", "team": "Alpecin - Deceuninck", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "D", "punch": "D"}, "price": 1.000000, "chance_of_abandon": 0.0},
            {"name": "Oscar Riesebeek", "team": "Alpecin - Deceuninck", "age": 27, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.500000, "chance_of_abandon": 0.0},
            
            # Arkéa - B&B Hotels
            {"name": "Kévin Vauquelin", "team": "Arkéa - B&B Hotels", "age": 23, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "C", "punch": "C"}, "price": 0.750000, "chance_of_abandon": 0.0},
            
            # Team Visma | Lease a Bike
            {"name": "Wout van Aert", "team": "Team Visma | Lease a Bike", "age": 29, "tiers": {"sprint": "C", "itt": "A", "mountain": "E", "hills": "A", "punch": "B"}, "price": 3.5, "chance_of_abandon": 0.0},
            {"name": "Simon Yates", "team": "Team Visma | Lease a Bike", "age": 27, "tiers": {"sprint": "E", "itt": "C", "mountain": "B", "hills": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Jonas Vingegaard", "team": "Team Visma | Lease a Bike", "age": 25, "tiers": {"sprint": "E", "itt": "A", "mountain": "S", "hills": "C", "punch": "C"}, "price": 6, "chance_of_abandon": 0.0},
            {"name": "Matteo Jorgenson", "team": "Team Visma | Lease a Bike", "age": 26, "tiers": {"sprint": "E", "itt": "B", "mountain": "C", "hills": "E", "punch": "E"}, "price": 3, "chance_of_abandon": 0.0},
            {"name": "Sepp Kuss", "team": "Team Visma | Lease a Bike", "age": 28, "tiers": {"sprint": "E", "itt": "D", "mountain": "B", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            {"name": "Victor Campenaerts", "team": "Team Visma | Lease a Bike", "age": 27, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            {"name": "Tiesj Benoot", "team": "Team Visma | Lease a Bike", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            
            # INEOS Grenadiers
            {"name": "Michał Kwiatkowski", "team": "INEOS Grenadiers", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Carlos Rodríguez", "team": "INEOS Grenadiers", "age": 24, "tiers": {"sprint": "E", "itt": "B", "mountain": "B", "hills": "E", "punch": "E"}, "price": 2.5, "chance_of_abandon": 0.0},
            {"name": "Filippo Ganna", "team": "INEOS Grenadiers", "age": 25, "tiers": {"sprint": "E", "itt": "S", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            {"name": "Geraint Thomas", "team": "INEOS Grenadiers", "age": 28, "tiers": {"sprint": "E", "itt": "B", "mountain": "C", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            {"name": "Thymen Arensman", "team": "INEOS Grenadiers", "age": 26, "tiers": {"sprint": "E", "itt": "B", "mountain": "C", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            {"name": "Laurens De Plus", "team": "INEOS Grenadiers", "age": 27, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Tobias Foss", "team": "INEOS Grenadiers", "age": 25, "tiers": {"sprint": "E", "itt": "B", "mountain": "D", "hills": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Intermarché - Wanty
            {"name": "Biniam Girmay", "team": "Intermarché - Wanty", "age": 24, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "hills": "B", "punch": "C"}, "price": 2.5, "chance_of_abandon": 0.0},
            {"name": "Hugo Page", "team": "Intermarché - Wanty", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Laurenz Rex", "team": "Intermarché - Wanty", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Georg Zimmermann", "team": "Intermarché - Wanty", "age": 27, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Kobe Goossens", "team": "Intermarché - Wanty", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Louis Barré", "team": "Intermarché - Wanty", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Lidl - Trek
            {"name": "Jonathan Milan", "team": "Lidl - Trek", "age": 23, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 4, "chance_of_abandon": 0.0},
            {"name": "Mattias Skjelmose", "team": "Lidl - Trek", "age": 24, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "hills": "B", "punch": "A"}, "price": 2.5, "chance_of_abandon": 0.0},
            {"name": "Jasper Stuyven", "team": "Lidl - Trek", "age": 25, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Edward Theuns", "team": "Lidl - Trek", "age": 26, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Simone Consonni", "team": "Lidl - Trek", "age": 27, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Julien Bernard", "team": "Lidl - Trek", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Tao Geoghegan Hart", "team": "Lidl - Trek", "age": 29, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Thibau Nys", "team": "Lidl - Trek", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "B"}, "price": 1, "chance_of_abandon": 0.0},
            
            # Groupama - FDJ
            {"name": "David Gaudu", "team": "Groupama - FDJ", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "C", "punch": "C"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Guillaume Martin", "team": "Groupama - FDJ", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "C", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Valentin Madouas", "team": "Groupama - FDJ", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "B", "punch": "B"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Romain Grégoire", "team": "Groupama - FDJ", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "A"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Quentin Pacher", "team": "Groupama - FDJ", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "C"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Movistar Team
            {"name": "Pablo Castrillo", "team": "Movistar Team", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Enric Mas", "team": "Movistar Team", "age": 27, "tiers": {"sprint": "E", "itt": "E", "mountain": "B", "hills": "E", "punch": "D"}, "price": 2, "chance_of_abandon": 0.0},
            {"name": "Nelson Oliveira", "team": "Movistar Team", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Einer Rubio", "team": "Movistar Team", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Fernando Gaviria", "team": "Movistar Team", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            {"name": "Iván Romeo", "team": "Movistar Team", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Javier Romo", "team": "Movistar Team", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Team Picnic PostNL
            {"name": "Oscar Onley", "team": "Team Picnic PostNL", "age": 21, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Frank van den Broek", "team": "Team Picnic PostNL", "age": 22, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Tobias Lund Andresen", "team": "Team Picnic PostNL", "age": 21, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            
            # Team Jayco AlUla
            {"name": "Ben O'Connor", "team": "Team Jayco AlUla", "age": 26, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "hills": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Eddie Dunbar", "team": "Team Jayco AlUla", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Mauro Schmid", "team": "Team Jayco AlUla", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "D"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Dylan Groenewegen", "team": "Team Jayco AlUla", "age": 30, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Luka Mezgec", "team": "Team Jayco AlUla", "age": 27, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Elmar Reinders", "team": "Team Jayco AlUla", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Christopher Juul-Jensen", "team": "Team Jayco AlUla", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Bahrain - Victorious
            {"name": "Lenny Martinez", "team": "Bahrain - Victorious", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "B", "hills": "C", "punch": "B"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Santiago Buitrago", "team": "Bahrain - Victorious", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "C"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Matej Mohorič", "team": "Bahrain - Victorious", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "C", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Phil Bauhaus", "team": "Bahrain - Victorious", "age": 29, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            
            # XDS Astana Team
            {"name": "Simone Velasco", "team": "XDS Astana Team", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Harold Tejada", "team": "XDS Astana Team", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Clément Champoussin", "team": "XDS Astana Team", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Lotto
            {"name": "Arnaud De Lie", "team": "Lotto", "age": 22, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Lennert van Eetvelt", "team": "Lotto", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "C"}, "price": 1, "chance_of_abandon": 0.0},
            {"name": "Jasper De Buyst", "team": "Lotto", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Jenno Berckmoes", "team": "Lotto", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Israel - Premier Tech
            {"name": "Pascal Ackermann", "team": "Israel - Premier Tech", "age": 27, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1.5, "chance_of_abandon": 0.0},
            {"name": "Joseph Blackmore", "team": "Israel - Premier Tech", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Michael Woods", "team": "Israel - Premier Tech", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "B", "punch": "B"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Alexey Lutsenko", "team": "Israel - Premier Tech", "age": 26, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Jake Stewart", "team": "Israel - Premier Tech", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0},
            
            # Team TotalEnergies
            {"name": "Mathieu Burgaudeau", "team": "Team TotalEnergies", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            
            # Tudor Pro Cycling Team
            {"name": "Julian Alaphilippe", "team": "Tudor Pro Cycling Team", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "B"}, "price": 0.75, "chance_of_abandon": 0.0},
            
            # Uno-X Mobility
            {"name": "Magnus Cort", "team": "Uno-X Mobility", "age": 27, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "B", "punch": "C"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Søren Wærenskjold", "team": "Uno-X Mobility", "age": 23, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.75, "chance_of_abandon": 0.0},
            {"name": "Andreas Leknessund", "team": "Uno-X Mobility", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Tobias Halland Johannessen", "team": "Uno-X Mobility", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "D", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Anders Halland Johannessen", "team": "Uno-X Mobility", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Jonas Abrahamsen", "team": "Uno-X Mobility", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Markus Hoelgaard", "team": "Uno-X Mobility", "age": 22, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 0.5, "chance_of_abandon": 0.0},
            {"name": "Stian Fredheim", "team": "Uno-X Mobility", "age": 21, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}, "price": 1, "chance_of_abandon": 0.0}
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
                hills_ability=ABILITY_TIERS[rider_info["tiers"]["hills"]]
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
        # Stage numbers in STAGE_PROFILES are 1-based
        min_val, mode, max_val = rider.get_stage_probability(stage + 1)
        return np.random.triangular(min_val, mode, max_val)

    def get_youth_riders(self, age_limit: int = 25) -> List[Rider]:
        return [r for r in self.riders if r.age <= age_limit]

# Create a global instance of the rider database
rider_db = RiderDatabase() 