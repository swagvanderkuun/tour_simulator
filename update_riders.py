import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def scrape_with_selenium():
    """Scrape rider data using Selenium to handle JavaScript"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Use webdriver-manager to automatically download and manage Chrome driver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"Error setting up Chrome driver: {e}")
        return []
    
    url = "https://www.procyclingstats.com/race/tour-de-france/2025/startlist"
    print(f"Loading: {url}")
    
    try:
        driver.get(url)
        
        # Wait for page to load
        time.sleep(5)
        
        # Wait for content to appear
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the page source after JavaScript has loaded
        page_source = driver.page_source
        
        # Save the rendered page for debugging
        with open("rendered_page.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print("Saved rendered page to rendered_page.html")
        
        # Now parse with BeautifulSoup
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_source, "html.parser")
        
        riders = []
        
        # Look for the startlist container
        startlist_container = soup.find("ul", class_="startlist_v4")
        if not startlist_container:
            print("No startlist_v4 container found")
            return []
        
        # Find all team entries
        team_entries = startlist_container.find_all("li")
        print(f"Found {len(team_entries)} team entries")
        
        for team_entry in team_entries:
            # Get team name
            team_name_elem = team_entry.find("a", class_="team")
            if not team_name_elem:
                continue
                
            team_name = team_name_elem.get_text(strip=True)
            print(f"Processing team: {team_name}")
            
            # Get riders list
            riders_list = team_entry.find("ul")
            if not riders_list:
                continue
                
            rider_items = riders_list.find_all("li")
            for rider_item in rider_items:
                # Get rider name from the link
                rider_link = rider_item.find("a")
                if rider_link:
                    rider_name = rider_link.get_text(strip=True)
                    
                    # Get age if available (look for age in the rider item)
                    age = 25  # Default age
                    
                    rider_data = {
                        "name": rider_name,
                        "team": team_name,
                        "age": age,
                        "tiers": {"sprint": "E", "itt": "E", "mountain": "E", "break_away": "E", "punch": "E"},
                        "price": 0.5,
                        "chance_of_abandon": 0.0
                    }
                    riders.append(rider_data)
                    print(f"  Added: {rider_name}")
        
        return riders
        
    except Exception as e:
        print(f"Error during scraping: {e}")
        return []
    
    finally:
        driver.quit()

def compare_with_current(scraped_riders):
    """Compare scraped riders with current database"""
    try:
        from riders import RiderDatabase
        current_riders = set(r.name for r in RiderDatabase().get_all_riders())
        print(f"Found {len(current_riders)} current riders in database")
    except Exception as e:
        print(f"Could not load current riders: {e}")
        current_riders = set()
    
    scraped_names = set(r["name"] for r in scraped_riders)
    missing = scraped_names - current_riders
    
    missing_riders = [r for r in scraped_riders if r["name"] in missing]
    
    return missing_riders

def main():
    print("Starting rider data update...")
    
    # Scrape with Selenium
    scraped_riders = scrape_with_selenium()
    
    if not scraped_riders:
        print("No riders scraped. Creating fallback list...")
        # Fallback to known riders
        scraped_riders = [
            {"name": "Tadej Pogačar", "team": "UAE Team Emirates", "age": 26},
            {"name": "Remco Evenepoel", "team": "Soudal Quick-Step", "age": 24},
            {"name": "Jonas Vingegaard", "team": "Team Visma | Lease a Bike", "age": 27},
            {"name": "João Almeida", "team": "UAE Team Emirates", "age": 25},
            {"name": "Primož Roglič", "team": "Red Bull - BORA - hansgrohe", "age": 34},
            {"name": "Carlos Rodríguez", "team": "INEOS Grenadiers", "age": 23},
            {"name": "Matteo Jorgenson", "team": "Team Visma | Lease a Bike", "age": 24},
            {"name": "Wout van Aert", "team": "Team Visma | Lease a Bike", "age": 29},
            {"name": "Mathieu van der Poel", "team": "Alpecin - Deceuninck", "age": 29},
            {"name": "Jasper Philipsen", "team": "Alpecin - Deceuninck", "age": 26},
        ]
    
    print(f"Scraped {len(scraped_riders)} riders")
    
    # Compare with current database
    missing_riders = compare_with_current(scraped_riders)
    
    print(f"\nMissing riders ({len(missing_riders)}):")
    for rider in missing_riders:
        print(f'{{"name": "{rider["name"]}", "team": "{rider["team"]}", "age": {rider["age"]}, "tiers": {rider["tiers"]}, "price": {rider["price"]}, "chance_of_abandon": {rider["chance_of_abandon"]}}}')
    
    # Save results
    with open("missing_riders.json", "w") as f:
        json.dump(missing_riders, f, indent=2)
    
    print(f"\nResults saved to missing_riders.json")
    print(f"Total missing riders: {len(missing_riders)}")
    
    return missing_riders

if __name__ == "__main__":
    main() 