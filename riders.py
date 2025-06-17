import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Dict
from stage_profiles import StageType, get_stage_type
from rider_parameters import RiderParameters

# Define ability tiers and their corresponding scores
ABILITY_TIERS = {
    "S": 98,  # Exceptional
    "A": 90,  # Elite
    "B": 80,  # Very Good
    "C": 70,  # Good
    "D": 60,  # Average
    "E": 50   # Below Average
}

# Initialize rider abilities dictionary
rider_abilities: Dict[str, Dict[str, int]] = {}

# Helper to assign abilities based on tiers
def assign_abilities_by_tier(rider_tiers: Dict[str, str], skill: str):
    for rider, tier in rider_tiers.items():
        if rider not in rider_abilities:
            rider_abilities[rider] = {}
        rider_abilities[rider][skill] = ABILITY_TIERS[tier]

# Sprint tiers
sprint_tiers = {
    "Jasper Philipsen": "S",
    "Biniam Girmay": "A",
    "Jonathan Milan": "A",
    "Tim Merlier": "S",
    "Dylan Groenewegen": "A",
    "Wout van Aert": "C",
    "Kaden Groves": "C",
    "Arnaud De Lie": "B",
    "Tobias Lund Andresen": "C",
    "Phil Bauhaus": "B",
    "Pascal Ackermann": "B",
    "Danny van Poppel": "C",
    "Jake Stewart": "C",
    "Mathieu van der Poel": "C",
    "Søren Wærenskjold": "C",
    "Fernando Gaviria": "C",
    "Magnus Cort": "D",
    "Edward Theuns": "D",
    "Jasper Stuyven": "D",
    "Elmar Reinders": "D"
}
assign_abilities_by_tier(sprint_tiers, "sprint")

# ITT tiers
itt_tiers = {
    "Filippo Ganna": "S",
    "Remco Evenepoel": "S",
    "Wout van Aert": "A",
    "Tadej Pogačar": "A",
    "Primož Roglič": "A",
    "João Almeida": "A",
    "Geraint Thomas": "B",
    "Stefan Küng": "B",
    "Matteo Jorgenson": "B",
    "Carlos Rodríguez": "B",
    "Thymen Arensman": "B",
    "Victor Campenaerts": "C",
    "Mikkel Bjerg": "C",
    "Stefan Bissegger": "C",
    "Edoardo Affini": "C",
    "Simon Yates": "C",
    "Sepp Kuss": "D",
    "Adam Yates": "D",
    "Ben O'Connor": "D",
    "Mattias Skjelmose": "D"
}
assign_abilities_by_tier(itt_tiers, "itt")

# Mountain tiers
mountain_tiers = {
    "Jonas Vingegaard": "S",
    "Tadej Pogačar": "S",
    "Remco Evenepoel": "A",
    "Primož Roglič": "A",
    "Richard Carapaz": "A",
    "David Gaudu": "D",
    "Enric Mas": "B",
    "Carlos Rodríguez": "B",
    "Felix Gall": "B",
    "Simon Yates": "B",
    "João Almeida": "B",
    "Sepp Kuss": "B",
    "Adam Yates": "B",
    "Santiago Buitrago": "C",
    "Thymen Arensman": "C",
    "Ben O'Connor": "C",
    "Michał Kwiatkowski": "C",
    "Matteo Jorgenson": "C",
    "Pavel Sivakov": "D",
    "Marc Soler": "D",
    "Guillaume Martin": "D"
}
assign_abilities_by_tier(mountain_tiers, "mountain")

# Hills tiers
hills_tiers = {
    "Mathieu van der Poel": "S",
    "Wout van Aert": "S",
    "Tadej Pogačar": "S",
    "Julian Alaphilippe": "A",
    "Mattias Skjelmose": "A",
    "Valentin Madouas": "A",
    "Biniam Girmay": "A",
    "David Gaudu": "B",
    "Romain Grégoire": "B",
    "Quentin Pacher": "B",
    "Magnus Cort": "B",
    "Michael Woods": "B",
    "Guillaume Martin": "C",
    "Ben Healy": "C",
    "Jasper Stuyven": "C",
    "Jasper Philipsen": "C",
    "Kaden Groves": "C",
    "Tim Wellens": "D",
    "Marc Hirschi": "D",
    "Andrea Bagioli": "D"
}
assign_abilities_by_tier(hills_tiers, "hills")

# Punch tiers
punch_tiers = {
    "Mathieu van der Poel": "S",
    "Wout van Aert": "A",
    "Tadej Pogačar": "S",
    "Julian Alaphilippe": "A",
    "Mattias Skjelmose": "A",
    "Valentin Madouas": "B",
    "Biniam Girmay": "C",
    "David Gaudu": "C",
    "Romain Grégoire": "B",
    "Quentin Pacher": "C",
    "Magnus Cort": "C",
    "Michael Woods": "B",
    "Guillaume Martin": "D",
    "Ben Healy": "C",
    "Jasper Stuyven": "D",
    "Jasper Philipsen": "C",
    "Kaden Groves": "D",
    "Tim Wellens": "D",
    "Marc Hirschi": "D",
    "Andrea Bagioli": "D"
}
assign_abilities_by_tier(punch_tiers, "punch")

@dataclass
class Rider:
    name: str
    team: str
    parameters: RiderParameters
    age: int

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
            {"name": "Richard Carapaz", "team": "EF Education - EasyPost", "age": 30, "tiers": {"sprint": "D", "itt": "D", "mountain": "A", "hills": "D", "punch": "D"}},
            {"name": "Harry Sweeny", "team": "EF Education - EasyPost", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Neilson Powless", "team": "EF Education - EasyPost", "age": 30, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "hills": "B", "punch": "E"}},
            {"name": "Ben Healy", "team": "EF Education - EasyPost", "age": 22, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "B", "punch": "E"}},
            
            # UAE Team Emirates - XRG
            {"name": "Tadej Pogačar", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "C", "itt": "A", "mountain": "S", "hills": "A", "punch": "A"}},
            {"name": "João Almeida", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "B", "mountain": "B", "hills": "E", "punch": "C"}},
            {"name": "Adam Yates", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "D", "mountain": "B", "hills": "E", "punch": "E"}},
            {"name": "Pavel Sivakov", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Marc Soler", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "D", "punch": "E"}},
            {"name": "Tim Wellens", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}},
            {"name": "Jhonatan Narváez", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "C", "punch": "E"}},
            {"name": "Domen Novak", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Nils Politt", "team": "UAE Team Emirates - XRG", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Decathlon AG2R La Mondiale Team
            {"name": "Felix Gall", "team": "Decathlon AG2R La Mondiale Team", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "B", "hills": "E", "punch": "E"}},
            
            # Red Bull - BORA - hansgrohe
            {"name": "Primož Roglič", "team": "Red Bull - BORA - hansgrohe", "age": 30, "tiers": {"sprint": "E", "itt": "A", "mountain": "A", "hills": "E", "punch": "C"}},
            {"name": "Daniel Felipe Martínez", "team": "Red Bull - BORA - hansgrohe", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Aleksandr Vlasov", "team": "Red Bull - BORA - hansgrohe", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Jan Tratnik", "team": "Red Bull - BORA - hansgrohe", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Danny van Poppel", "team": "Red Bull - BORA - hansgrohe", "age": 27, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Florian Lipowitz", "team": "Red Bull - BORA - hansgrohe", "age": 23, "tiers": {"sprint": "E", "itt": "B", "mountain": "B", "hills": "B", "punch": "C"}},
            
            # Soudal Quick-Step
            {"name": "Remco Evenepoel", "team": "Soudal Quick-Step", "age": 24, "tiers": {"sprint": "E", "itt": "S", "mountain": "A", "hills": "B", "punch": "B"}},
            {"name": "Tim Merlier", "team": "Soudal Quick-Step", "age": 31, "tiers": {"sprint": "S", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Bert Van Lerberghe", "team": "Soudal Quick-Step", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Pascal Eenkhoorn", "team": "Soudal Quick-Step", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Cofidis
            {"name": "Alex Aranburu", "team": "Cofidis", "age": 27, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "C", "punch": "E"}},
            {"name": "Ion Izagirre", "team": "Cofidis", "age": 28, "tiers": {"sprint": "E", "itt": "D", "mountain": "E", "hills": "D", "punch": "D"}},
            {"name": "Benjamin Thomas", "team": "Cofidis", "age": 25, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Emanuel Buchmann", "team": "Cofidis", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Simon Carr", "team": "Cofidis", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}},
            
            # Alpecin - Deceuninck
            {"name": "Mathieu van der Poel", "team": "Alpecin - Deceuninck", "age": 25, "tiers": {"sprint": "C", "itt": "C", "mountain": "E", "hills": "A", "punch": "A"}},
            {"name": "Jasper Philipsen", "team": "Alpecin - Deceuninck", "age": 26, "tiers": {"sprint": "S", "itt": "E", "mountain": "E", "hills": "C", "punch": "C"}},
            {"name": "Kaden Groves", "team": "Alpecin - Deceuninck", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "D", "punch": "D"}},
            {"name": "Oscar Riesebeek", "team": "Alpecin - Deceuninck", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Arkéa - B&B Hotels
            {"name": "Kévin Vauquelin", "team": "Arkéa - B&B Hotels", "age": 23, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "C", "punch": "C"}},
            
            # Team Visma | Lease a Bike
            {"name": "Wout van Aert", "team": "Team Visma | Lease a Bike", "age": 29, "tiers": {"sprint": "C", "itt": "A", "mountain": "E", "hills": "A", "punch": "B"}},
            {"name": "Simon Yates", "team": "Team Visma | Lease a Bike", "age": 27, "tiers": {"sprint": "E", "itt": "C", "mountain": "B", "hills": "E", "punch": "E"}},
            {"name": "Jonas Vingegaard", "team": "Team Visma | Lease a Bike", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "S", "hills": "E", "punch": "E"}},
            {"name": "Matteo Jorgenson", "team": "Team Visma | Lease a Bike", "age": 26, "tiers": {"sprint": "E", "itt": "B", "mountain": "C", "hills": "E", "punch": "E"}},
            {"name": "Sepp Kuss", "team": "Team Visma | Lease a Bike", "age": 28, "tiers": {"sprint": "E", "itt": "D", "mountain": "B", "hills": "E", "punch": "E"}},
            {"name": "Victor Campenaerts", "team": "Team Visma | Lease a Bike", "age": 27, "tiers": {"sprint": "E", "itt": "C", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Tiesj Benoot", "team": "Team Visma | Lease a Bike", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # INEOS Grenadiers
            {"name": "Michał Kwiatkowski", "team": "INEOS Grenadiers", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "E"}},
            {"name": "Carlos Rodríguez", "team": "INEOS Grenadiers", "age": 24, "tiers": {"sprint": "E", "itt": "B", "mountain": "B", "hills": "E", "punch": "E"}},
            {"name": "Filippo Ganna", "team": "INEOS Grenadiers", "age": 25, "tiers": {"sprint": "E", "itt": "S", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Geraint Thomas", "team": "INEOS Grenadiers", "age": 28, "tiers": {"sprint": "E", "itt": "B", "mountain": "C", "hills": "E", "punch": "E"}},
            {"name": "Thymen Arensman", "team": "INEOS Grenadiers", "age": 26, "tiers": {"sprint": "E", "itt": "B", "mountain": "C", "hills": "E", "punch": "E"}},
            {"name": "Laurens De Plus", "team": "INEOS Grenadiers", "age": 27, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Tobias Foss", "team": "INEOS Grenadiers", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Intermarché - Wanty
            {"name": "Biniam Girmay", "team": "Intermarché - Wanty", "age": 24, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "hills": "B", "punch": "C"}},
            {"name": "Hugo Page", "team": "Intermarché - Wanty", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Laurenz Rex", "team": "Intermarché - Wanty", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Georg Zimmermann", "team": "Intermarché - Wanty", "age": 27, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Kobe Goossens", "team": "Intermarché - Wanty", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Louis Barré", "team": "Intermarché - Wanty", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "D", "punch": "E"}},
            
            # Lidl - Trek
            {"name": "Jonathan Milan", "team": "Lidl - Trek", "age": 23, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Mattias Skjelmose", "team": "Lidl - Trek", "age": 24, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "hills": "B", "punch": "A"}},
            {"name": "Jasper Stuyven", "team": "Lidl - Trek", "age": 25, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "D", "punch": "D"}},
            {"name": "Edward Theuns", "team": "Lidl - Trek", "age": 26, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Simone Consonni", "team": "Lidl - Trek", "age": 27, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Julien Bernard", "team": "Lidl - Trek", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Tao Geoghegan Hart", "team": "Lidl - Trek", "age": 29, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Thibau Nys", "team": "Lidl - Trek", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "B"}},
            
            # Groupama - FDJ
            {"name": "David Gaudu", "team": "Groupama - FDJ", "age": 30, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "C", "punch": "C"}},
            {"name": "Guillaume Martin", "team": "Groupama - FDJ", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "C", "punch": "E"}},
            {"name": "Valentin Madouas", "team": "Groupama - FDJ", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "B", "punch": "B"}},
            {"name": "Romain Grégoire", "team": "Groupama - FDJ", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "A"}},
            {"name": "Quentin Pacher", "team": "Groupama - FDJ", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "C"}},
            
            # Movistar Team
            {"name": "Pablo Castrillo", "team": "Movistar Team", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Enric Mas", "team": "Movistar Team", "age": 27, "tiers": {"sprint": "E", "itt": "E", "mountain": "B", "hills": "E", "punch": "D"}},
            {"name": "Nelson Oliveira", "team": "Movistar Team", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Einer Rubio", "team": "Movistar Team", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "E"}},
            {"name": "Fernando Gaviria", "team": "Movistar Team", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Iván Romeo", "team": "Movistar Team", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}},
            {"name": "Javier Romo", "team": "Movistar Team", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}},
            
            # Team Picnic PostNL
            {"name": "Oscar Onley", "team": "Team Picnic PostNL", "age": 21, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Frank van den Broek", "team": "Team Picnic PostNL", "age": 22, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Tobias Lund Andresen", "team": "Team Picnic PostNL", "age": 21, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Team Jayco AlUla
            {"name": "Ben O'Connor", "team": "Team Jayco AlUla", "age": 26, "tiers": {"sprint": "E", "itt": "D", "mountain": "C", "hills": "E", "punch": "E"}},
            {"name": "Eddie Dunbar", "team": "Team Jayco AlUla", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "E"}},
            {"name": "Mauro Schmid", "team": "Team Jayco AlUla", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "D"}},
            {"name": "Dylan Groenewegen", "team": "Team Jayco AlUla", "age": 30, "tiers": {"sprint": "A", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Luka Mezgec", "team": "Team Jayco AlUla", "age": 27, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Elmar Reinders", "team": "Team Jayco AlUla", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Christopher Juul-Jensen", "team": "Team Jayco AlUla", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Bahrain - Victorious
            {"name": "Lenny Martinez", "team": "Bahrain - Victorious", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "B", "hills": "C", "punch": "B"}},
            {"name": "Santiago Buitrago", "team": "Bahrain - Victorious", "age": 28, "tiers": {"sprint": "E", "itt": "E", "mountain": "C", "hills": "E", "punch": "C"}},
            {"name": "Matej Mohorič", "team": "Bahrain - Victorious", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "C", "punch": "E"}},
            {"name": "Phil Bauhaus", "team": "Bahrain - Victorious", "age": 29, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # XDS Astana Team
            {"name": "Simone Velasco", "team": "XDS Astana Team", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "D", "punch": "E"}},
            {"name": "Harold Tejada", "team": "XDS Astana Team", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Clément Champoussin", "team": "XDS Astana Team", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Lotto
            {"name": "Arnaud De Lie", "team": "Lotto", "age": 22, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Lennert van Eetvelt", "team": "Lotto", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "C"}},
            {"name": "Jasper De Buyst", "team": "Lotto", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Jenno Berckmoes", "team": "Lotto", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Israel - Premier Tech
            {"name": "Pascal Ackermann", "team": "Israel - Premier Tech", "age": 27, "tiers": {"sprint": "B", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Joseph Blackmore", "team": "Israel - Premier Tech", "age": 23, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Michael Woods", "team": "Israel - Premier Tech", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "B", "punch": "B"}},
            {"name": "Alexey Lutsenko", "team": "Israel - Premier Tech", "age": 26, "tiers": {"sprint": "E", "itt": "D", "mountain": "D", "hills": "E", "punch": "E"}},
            {"name": "Jake Stewart", "team": "Israel - Premier Tech", "age": 25, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Team TotalEnergies
            {"name": "Mathieu Burgaudeau", "team": "Team TotalEnergies", "age": 24, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            
            # Tudor Pro Cycling Team
            {"name": "Julian Alaphilippe", "team": "Tudor Pro Cycling Team", "age": 29, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "B", "punch": "B"}},
            
            # Uno-X Mobility
            {"name": "Magnus Cort", "team": "Uno-X Mobility", "age": 27, "tiers": {"sprint": "D", "itt": "E", "mountain": "E", "hills": "B", "punch": "C"}},
            {"name": "Søren Wærenskjold", "team": "Uno-X Mobility", "age": 23, "tiers": {"sprint": "C", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Andreas Leknessund", "team": "Uno-X Mobility", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Tobias Halland Johannessen", "team": "Uno-X Mobility", "age": 25, "tiers": {"sprint": "E", "itt": "E", "mountain": "D", "hills": "D", "punch": "E"}},
            {"name": "Anders Halland Johannessen", "team": "Uno-X Mobility", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Jonas Abrahamsen", "team": "Uno-X Mobility", "age": 26, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Markus Hoelgaard", "team": "Uno-X Mobility", "age": 22, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}},
            {"name": "Stian Fredheim", "team": "Uno-X Mobility", "age": 21, "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "hills": "E", "punch": "E"}}
        ]

        # Create Rider objects with their parameters
        self.riders = []
        for rider_info in rider_data:
            # Get abilities from rider_abilities dictionary
            abilities = rider_abilities.get(rider_info["name"], {})
            # Create parameters with abilities or default values
            parameters = RiderParameters(
                sprint_ability=abilities.get('sprint', ABILITY_TIERS['E']),
                punch_ability=abilities.get('punch', ABILITY_TIERS['E']),
                itt_ability=abilities.get('itt', ABILITY_TIERS['E']),
                mountain_ability=abilities.get('mountain', ABILITY_TIERS['E']),
                hills_ability=abilities.get('hills', ABILITY_TIERS['E'])
            )
            self.riders.append(Rider(rider_info["name"], rider_info["team"], parameters, rider_info["age"]))

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