import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, List
import time

class CyclingOracleScraper:
    def __init__(self):
        self.base_url = "https://www.cyclingoracle.com/nl/renners"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_rider_data(self) -> List[Dict]:
        """
        Scrape rider data from cyclingoracle.com
        Returns a list of dictionaries containing rider information
        """
        try:
            # Make the request
            response = requests.get(self.base_url, headers=self.headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the rider table
            rider_table = soup.find('table', {'class': 'rider-table'})  # Update class name based on actual website
            if not rider_table:
                raise ValueError("Could not find rider table on the page")
            
            riders = []
            # Process each row in the table
            for row in rider_table.find_all('tr')[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 4:  # Ensure we have enough columns
                    rider = {
                        'name': cols[0].text.strip(),
                        'team': cols[1].text.strip(),
                        'age': int(cols[2].text.strip()),
                        'abilities': {
                            'sprint': self._parse_ability(cols[3].text.strip()),
                            'punch': self._parse_ability(cols[4].text.strip()),
                            'itt': self._parse_ability(cols[5].text.strip()),
                            'mountain': self._parse_ability(cols[6].text.strip()),
                            'hills': self._parse_ability(cols[7].text.strip())
                        }
                    }
                    riders.append(rider)
            
            return riders
            
        except requests.RequestException as e:
            print(f"Error making request: {e}")
            return []
        except Exception as e:
            print(f"Error parsing data: {e}")
            return []

    def _parse_ability(self, ability_text: str) -> str:
        """
        Parse the ability text into a tier (S, A, B, C, D, E)
        """
        # This is a placeholder - update based on actual website format
        ability_map = {
            'Exceptional': 'S',
            'Elite': 'A',
            'Very Good': 'B',
            'Good': 'C',
            'Average': 'D',
            'Below Average': 'E'
        }
        return ability_map.get(ability_text, 'E')

    def save_to_json(self, riders: List[Dict], filename: str = 'rider_data.json'):
        """
        Save the scraped rider data to a JSON file
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(riders, f, indent=4, ensure_ascii=False)
            print(f"Successfully saved rider data to {filename}")
        except Exception as e:
            print(f"Error saving data to file: {e}")

def main():
    scraper = CyclingOracleScraper()
    print("Starting to scrape rider data...")
    riders = scraper.get_rider_data()
    
    if riders:
        print(f"Successfully scraped data for {len(riders)} riders")
        scraper.save_to_json(riders)
    else:
        print("No rider data was scraped")

if __name__ == "__main__":
    main() 