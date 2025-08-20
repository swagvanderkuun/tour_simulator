#!/usr/bin/env python3
"""
Demonstration of new flexible features in the Tour Simulator.

This script showcases:
1. Flexible race configuration system
2. TTT (Team Time Trial) support
3. Flexible rider database system
4. Starting list management
5. Procyclingstats scraper (mocked demo)

Run with: python demo_flexible_features.py
"""

import tempfile
from pathlib import Path
from datetime import datetime

# Import the new flexible components
from tour_simulator.config.race_config import (
    RaceConfig, StageConfig, StageCategory, 
    create_tour_de_france_2025
)
from tour_simulator.services.rider_database import (
    FlexibleRiderDatabase, RiderData, StartingList
)
from tour_simulator.services.procyclingstats_scraper import (
    ProcyclingStatsScraper, ScrapedRider, estimate_rider_abilities
)
from tour_simulator.config.scraper_config import ScraperConfig


def demo_race_configuration():
    """Demonstrate the flexible race configuration system."""
    print("🏁 DEMO: Flexible Race Configuration System")
    print("=" * 50)
    
    # Create a custom race configuration
    vuelta = RaceConfig(
        race_name="Vuelta a España",
        race_short_name="Vuelta",
        year=2025,
        total_stages=21
    )
    
    print(f"Created race: {vuelta.race_name} {vuelta.year}")
    print(f"UI Title: {vuelta.ui_texts['app_title']}")
    print(f"Welcome message: {vuelta.ui_texts['welcome_message']}")
    
    # Add some stages with different types including TTT
    stages_data = [
        ("Prologue", {StageCategory.ITT: 1.0}),
        ("Flat Stage", {StageCategory.SPRINT: 1.0}),
        ("Hilly Stage", {StageCategory.PUNCH: 0.7, StageCategory.SPRINT: 0.3}),
        ("Team Time Trial", {StageCategory.TTT: 1.0}),  # New TTT support!
        ("Mountain Stage", {StageCategory.MOUNTAIN: 0.9, StageCategory.BREAK_AWAY: 0.1})
    ]
    
    for i, (name, stage_type) in enumerate(stages_data, 1):
        stage = StageConfig(i, f"Stage {i}: {name}", stage_type)
        vuelta.add_stage(stage)
        
        stage_types = ", ".join([f"{cat.value}: {weight}" for cat, weight in stage_type.items()])
        print(f"  Stage {i}: {name} ({stage_types})")
    
    print(f"\nCreated Vuelta with {len(vuelta.stages)} stages")
    
    # Show TTT stage specifically
    ttt_stage = vuelta.get_stage(4)
    print(f"TTT Stage: {ttt_stage.stage_name}")
    print(f"TTT weights: {ttt_stage.stage_type}")
    
    # Save and load demonstration
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "vuelta_2025.json"
        vuelta.save_to_file(config_path)
        
        loaded_vuelta = RaceConfig.load_from_file(config_path)
        print(f"✅ Saved and loaded race configuration successfully!")
        print(f"Loaded race has {len(loaded_vuelta.stages)} stages")
    
    print("\n")


def demo_tour_de_france_with_ttt():
    """Demonstrate Tour de France 2025 with TTT support."""
    print("🚴‍♂️ DEMO: Tour de France 2025 with TTT Support")
    print("=" * 50)
    
    tdf = create_tour_de_france_2025()
    
    print(f"Created {tdf.race_name} {tdf.year}")
    print(f"Total stages: {tdf.total_stages}")
    
    # Find TTT stage
    ttt_stage = None
    for stage in tdf.stages:
        if StageCategory.TTT in stage.stage_type:
            ttt_stage = stage
            break
    
    if ttt_stage:
        print(f"\n🔥 TTT Stage found: {ttt_stage.stage_name}")
        print(f"Stage {ttt_stage.stage_number}: {dict(ttt_stage.stage_type)}")
    
    # Show stage type variety
    stage_types_count = {}
    for stage in tdf.stages:
        for stage_type in stage.stage_type.keys():
            stage_types_count[stage_type.value] = stage_types_count.get(stage_type.value, 0) + 1
    
    print(f"\nStage type distribution:")
    for stage_type, count in stage_types_count.items():
        print(f"  {stage_type}: {count} stages")
    
    print("\n")


def demo_flexible_rider_database():
    """Demonstrate the flexible rider database system."""
    print("👥 DEMO: Flexible Rider Database System") 
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create database
        db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
        
        # Add some riders
        riders = [
            RiderData(
                name="Tadej POGAČAR",
                team="UAE Team Emirates", 
                age=26,
                nationality="Slovenia",
                tier_abilities={
                    "sprint": "E", "punch": "A", "itt": "A", 
                    "mountain": "S", "break_away": "E"
                },
                price=7.5,
                pcs_id="tadej-pogacar"
            ),
            RiderData(
                name="Jonas VINGEGAARD",
                team="Team Visma",
                age=27,
                nationality="Denmark", 
                tier_abilities={
                    "sprint": "E", "punch": "E", "itt": "A",
                    "mountain": "A", "break_away": "E"
                },
                price=6.0,
                pcs_id="jonas-vingegaard"
            ),
            RiderData(
                name="Remco EVENEPOEL",
                team="Soudal Quick-Step",
                age=24,
                nationality="Belgium",
                tier_abilities={
                    "sprint": "E", "punch": "B", "itt": "S", 
                    "mountain": "A", "break_away": "E"
                },
                price=6.0,
                pcs_id="remco-evenepoel"
            )
        ]
        
        for rider in riders:
            db.add_rider(rider)
            print(f"Added rider: {rider.name} ({rider.team})")
        
        print(f"\nMaster database has {len(db.master_database)} riders")
        
        # Search functionality
        print("\n🔍 Search capabilities:")
        slovenian_riders = db.search_riders(nationality="Slovenia")
        print(f"Slovenian riders: {[r.name for r in slovenian_riders]}")
        
        visma_riders = db.search_riders(team="Visma")
        print(f"Team Visma riders: {[r.name for r in visma_riders]}")
        
        pogacar_search = db.search_riders(name_pattern="POGA")
        print(f"Name contains 'POGA': {[r.name for r in pogacar_search]}")
        
        # Create starting list
        print("\n📋 Creating starting list...")
        starting_list = db.create_starting_list(
            "Tour de France",
            2025,
            ["Tadej POGAČAR", "Jonas VINGEGAARD", "Remco EVENEPOEL"]
        )
        
        print(f"Starting list created with {len(starting_list.riders)} riders")
        print(f"Race: {starting_list.race_name} {starting_list.year}")
        
        # Save and load starting list
        db.save_current_starting_list()
        
        # Create new DB instance and load
        db2 = FlexibleRiderDatabase(data_dir=Path(temp_dir))
        success = db2.load_starting_list("Tour de France", 2025)
        print(f"✅ Starting list loaded successfully: {success}")
        
        # Get simulation riders
        sim_riders = db2.get_simulation_riders()
        print(f"Simulation riders ready: {len(sim_riders)} riders")
        for rider in sim_riders:
            print(f"  {rider.name}: MTN={rider.parameters.mountain_ability}, ITT={rider.parameters.itt_ability}")
    
    print("\n")


def demo_scraper_functionality():
    """Demonstrate the procyclingstats scraper (mocked)."""
    print("🌐 DEMO: Procyclingstats Scraper (Mocked)")
    print("=" * 50)
    
    # Create scraper with custom config
    config = ScraperConfig(request_delay=0.5, max_retries=2)
    scraper = ProcyclingStatsScraper(config)
    
    print(f"Scraper initialized with {len(config.user_agents)} user agents")
    print(f"Base URL: {config.base_url}")
    
    # Show URL generation
    tdf_url = config.get_race_url("Tour de France", 2025)
    vuelta_url = config.get_race_url("Vuelta a España", 2024)
    print(f"TDF 2025 URL: {tdf_url}")
    print(f"Vuelta 2024 URL: {vuelta_url}")
    
    # Mock some scraped data
    print("\n🕷️ Mock scraping demo:")
    mock_scraped_riders = [
        ScrapedRider("Tadej POGAČAR", "UAE Team Emirates", "Slovenia", 26, "tadej-pogacar"),
        ScrapedRider("Jonas VINGEGAARD", "Team Visma", "Denmark", 27, "jonas-vingegaard"),
        ScrapedRider("Primož ROGLIČ", "Bora-hansgrohe", "Slovenia", 34, "primoz-roglic")
    ]
    
    print(f"Mock scraped {len(mock_scraped_riders)} riders:")
    for rider in mock_scraped_riders:
        print(f"  {rider.name} ({rider.team}, {rider.nationality})")
    
    # Convert to RiderData
    rider_data_list = scraper.convert_to_rider_data(mock_scraped_riders)
    print(f"\nConverted to {len(rider_data_list)} RiderData objects")
    
    # Show ability estimation
    print("\n🧠 Ability estimation examples:")
    test_cases = [
        ("Mark CAVENDISH", "Sprint Team"),
        ("Chris FROOME", "Sky Team"),
        ("Tony MARTIN", "Time Trial Specialist"),
        ("Unknown RIDER", "Generic Team")
    ]
    
    for name, team in test_cases:
        abilities = estimate_rider_abilities(name, team)
        enhanced = [k for k, v in abilities.items() if v != "E"]
        print(f"  {name}: Enhanced abilities: {enhanced if enhanced else 'None (all E)'}")
    
    print("\n")


def demo_integration():
    """Demonstrate integration of all flexible features."""
    print("🔗 DEMO: Integrated Workflow")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Step 1: Create custom race
        print("1️⃣ Creating custom race configuration...")
        race = RaceConfig("Demo Race", "DR", 2025, 5)
        
        stages = [
            StageConfig(1, "Stage 1: Prologue", {StageCategory.ITT: 1.0}),
            StageConfig(2, "Stage 2: Sprint", {StageCategory.SPRINT: 1.0}),
            StageConfig(3, "Stage 3: TTT", {StageCategory.TTT: 1.0}),
            StageConfig(4, "Stage 4: Mountain", {StageCategory.MOUNTAIN: 1.0}),
            StageConfig(5, "Stage 5: Mixed", {StageCategory.PUNCH: 0.6, StageCategory.SPRINT: 0.4})
        ]
        
        for stage in stages:
            race.add_stage(stage)
        
        print(f"Created {race.race_name} with {len(race.stages)} stages")
        
        # Step 2: Setup rider database
        print("\n2️⃣ Setting up rider database...")
        db = FlexibleRiderDatabase(data_dir=Path(temp_dir))
        
        # Add star riders
        star_riders = [
            RiderData("GC Contender", "Team GC", 26, "Country A", 
                     {"sprint": "D", "punch": "B", "itt": "A", "mountain": "A", "break_away": "C"}, 5.0),
            RiderData("Sprint King", "Team Sprint", 28, "Country B",
                     {"sprint": "S", "punch": "C", "itt": "E", "mountain": "E", "break_away": "E"}, 4.0),
            RiderData("TTT Specialist", "Team TTT", 30, "Country C",
                     {"sprint": "E", "punch": "D", "itt": "A", "mountain": "D", "break_away": "D"}, 2.5),
            RiderData("Climber", "Team Mountain", 25, "Country D",
                     {"sprint": "E", "punch": "C", "itt": "E", "mountain": "S", "break_away": "B"}, 3.5)
        ]
        
        for rider in star_riders:
            db.add_rider(rider)
        
        print(f"Added {len(star_riders)} riders to database")
        
        # Step 3: Create starting list
        print("\n3️⃣ Creating starting list...")
        starting_list = db.create_starting_list(
            race.race_name, 
            race.year,
            [r.name for r in star_riders]
        )
        
        print(f"Starting list created with {len(starting_list.riders)} riders")
        
        # Step 4: Get simulation-ready riders
        print("\n4️⃣ Preparing for simulation...")
        sim_riders = db.get_simulation_riders()
        
        print("Simulation riders:")
        for rider in sim_riders:
            best_ability = max([
                ("SPR", rider.parameters.sprint_ability),
                ("PUN", rider.parameters.punch_ability), 
                ("ITT", rider.parameters.itt_ability),
                ("MTN", rider.parameters.mountain_ability),
                ("BRK", rider.parameters.break_away_ability)
            ], key=lambda x: x[1])
            
            print(f"  {rider.name}: Best at {best_ability[0]} ({best_ability[1]})")
        
        # Step 5: Show stage compatibility
        print("\n5️⃣ Stage-Rider compatibility analysis:")
        for stage in race.stages:
            dominant_type = max(stage.stage_type.items(), key=lambda x: x[1])
            stage_type_name = dominant_type[0].value.upper()
            
            print(f"Stage {stage.stage_number} ({stage_type_name}):")
            
            # Find best rider for this stage type
            best_rider = None
            best_score = 0
            
            for rider in sim_riders:
                ability_map = {
                    StageCategory.SPRINT: rider.parameters.sprint_ability,
                    StageCategory.PUNCH: rider.parameters.punch_ability,
                    StageCategory.ITT: rider.parameters.itt_ability,
                    StageCategory.TTT: rider.parameters.itt_ability,  # TTT uses ITT ability
                    StageCategory.MOUNTAIN: rider.parameters.mountain_ability,
                    StageCategory.BREAK_AWAY: rider.parameters.break_away_ability
                }
                
                stage_score = sum(ability_map[stage_type] * weight 
                                 for stage_type, weight in stage.stage_type.items())
                
                if stage_score > best_score:
                    best_score = stage_score
                    best_rider = rider
            
            print(f"  Best rider: {best_rider.name} (score: {best_score:.1f})")
    
    print(f"\n✅ Complete flexible workflow demonstrated!")
    print("\n")


def main():
    """Run all demonstrations."""
    print("🎯 TOUR SIMULATOR - FLEXIBLE FEATURES DEMO")
    print("=" * 60)
    print("This demo showcases the new flexible, multi-race capabilities:")
    print("• Flexible race configuration with JSON save/load")
    print("• Team Time Trial (TTT) support")
    print("• Flexible rider database with search capabilities") 
    print("• Starting list management")
    print("• Procyclingstats scraper framework")
    print("• Full integration workflow")
    print("=" * 60)
    print()
    
    demo_race_configuration()
    demo_tour_de_france_with_ttt()
    demo_flexible_rider_database()
    demo_scraper_functionality()
    demo_integration()
    
    print("🎉 DEMO COMPLETE!")
    print("The tour simulator is now flexible and ready for any stage race!")
    print("Run the dashboard with: python run_dashboard.py")


if __name__ == "__main__":
    main() 