"""
Procyclingstats.com scraper for extracting race starting lists.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
from typing import List, Dict, Optional, Tuple
import re
import time
import random
from urllib.parse import urljoin, urlparse
from dataclasses import dataclass

from ..config.scraper_config import ScraperConfig
from .rider_database import RiderData


@dataclass
class ScrapedRider:
    """Basic rider information scraped from procyclingstats."""
    name: str
    team: str
    nationality: str
    age: Optional[int] = None
    pcs_id: Optional[str] = None
    profile_url: Optional[str] = None


class ProcyclingStatsScraper:
    """Scraper for procyclingstats.com starting lists."""
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """Initialize the scraper."""
        self.config = config or ScraperConfig()
        self.session = requests.Session()
        self.session.headers.update(self.config.headers)
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        return random.choice(self.config.user_agents)
    
    def _make_request(self, url: str, retries: int = None) -> Optional[requests.Response]:
        """Make a HTTP request with retry logic."""
        retries = retries or self.config.max_retries
        
        for attempt in range(retries):
            try:
                # Rotate user agent
                self.session.headers['User-Agent'] = self._get_random_user_agent()
                
                # Add delay between requests
                if attempt > 0:
                    self.config.delay_request()
                
                response = self.session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                print(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    print(f"All {retries} attempts failed for URL: {url}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _extract_rider_info(self, rider_row) -> Optional[ScrapedRider]:
        """Extract rider information from a table row."""
        try:
            # Find rider name and profile link
            name_cell = rider_row.find('a')
            if not name_cell:
                return None
            
            name = name_cell.get_text(strip=True)
            profile_url = urljoin(self.config.base_url, name_cell.get('href', ''))
            
            # Extract PCS ID from URL
            pcs_id = None
            if profile_url:
                match = re.search(r'/rider/([^/]+)', profile_url)
                if match:
                    pcs_id = match.group(1)
            
            # Find team
            team_cell = rider_row.find('td', class_='cu600')
            team = team_cell.get_text(strip=True) if team_cell else "Unknown"
            
            # Find nationality (usually has a flag image)
            nationality = "Unknown"
            flag_img = rider_row.find('img')
            if flag_img and flag_img.get('title'):
                nationality = flag_img.get('title')
            
            return ScrapedRider(
                name=name,
                team=team,
                nationality=nationality,
                pcs_id=pcs_id,
                profile_url=profile_url
            )
            
        except Exception as e:
            print(f"Error extracting rider info: {e}")
            return None
    
    def _get_rider_age_from_profile(self, profile_url: str) -> Optional[int]:
        """Get rider age from their profile page."""
        try:
            response = self._make_request(profile_url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for birth date in various formats
            info_elements = soup.find_all(['div', 'span', 'td'])
            for element in info_elements:
                text = element.get_text(strip=True)
                
                # Look for age patterns
                age_match = re.search(r'Age:\s*(\d+)', text, re.IGNORECASE)
                if age_match:
                    return int(age_match.group(1))
                
                # Look for birth year
                birth_year_match = re.search(r'Born:\s*\d+[/-]\d+[/-](\d{4})', text)
                if birth_year_match:
                    birth_year = int(birth_year_match.group(1))
                    current_year = 2025  # Adjust as needed
                    return current_year - birth_year
            
            return None
            
        except Exception as e:
            print(f"Error getting rider age from {profile_url}: {e}")
            return None
    
    def scrape_race_startlist(self, race_name: str, year: int, 
                            fetch_ages: bool = False) -> List[ScrapedRider]:
        """Scrape starting list for a specific race."""
        print(f"Scraping {race_name} {year} starting list...")
        
        # Generate URL
        url = self.config.get_race_url(race_name, year)
        print(f"URL: {url}")
        
        # Make request
        response = self._make_request(url)
        if not response:
            raise Exception(f"Failed to fetch starting list from {url}")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the startlist table
        riders = []
        
        # Look for different table structures
        startlist_tables = soup.find_all('table')
        
        for table in startlist_tables:
            rows = table.find_all('tr')
            
            for row in rows:
                # Skip header rows
                if row.find('th'):
                    continue
                
                rider = self._extract_rider_info(row)
                if rider and rider.name:
                    riders.append(rider)
        
        print(f"Found {len(riders)} riders")
        
        # Fetch ages if requested (this will be slow)
        if fetch_ages:
            print("Fetching rider ages from profiles...")
            for i, rider in enumerate(riders):
                if rider.profile_url:
                    print(f"  {i+1}/{len(riders)}: {rider.name}")
                    rider.age = self._get_rider_age_from_profile(rider.profile_url)
                    self.config.delay_request()  # Be respectful
        
        return riders
    
    def convert_to_rider_data(self, scraped_riders: List[ScrapedRider], 
                            default_abilities: Optional[Dict[str, str]] = None) -> List[RiderData]:
        """Convert scraped riders to RiderData objects."""
        if default_abilities is None:
            default_abilities = {
                "sprint": "E",
                "punch": "E", 
                "itt": "E",
                "mountain": "E",
                "break_away": "E"
            }
        
        rider_data_list = []
        
        for scraped in scraped_riders:
            rider_data = RiderData(
                name=scraped.name,
                team=scraped.team,
                age=scraped.age or 25,  # Default age
                nationality=scraped.nationality,
                tier_abilities=default_abilities.copy(),
                price=0.5,  # Default price
                chance_of_abandon=0.05,  # Default abandon chance
                pcs_id=scraped.pcs_id
            )
            rider_data_list.append(rider_data)
        
        return rider_data_list
    
    def scrape_and_create_starting_list(self, race_name: str, year: int, 
                                      fetch_ages: bool = False) -> Tuple[List[RiderData], Dict[str, int]]:
        """Scrape a race and return RiderData list with statistics."""
        scraped_riders = self.scrape_race_startlist(race_name, year, fetch_ages)
        rider_data_list = self.convert_to_rider_data(scraped_riders)
        
        # Generate statistics
        stats = {
            "total_riders": len(rider_data_list),
            "teams": len(set(r.team for r in rider_data_list)),
            "nationalities": len(set(r.nationality for r in rider_data_list)),
            "riders_with_age": sum(1 for r in rider_data_list if r.age and r.age != 25)
        }
        
        return rider_data_list, stats
    
    def search_race_urls(self, race_name: str, year: int) -> List[str]:
        """Search for possible race URLs on procyclingstats."""
        possible_urls = []
        
        # Generate variations of race name
        variations = [
            race_name.lower().replace(" ", "-"),
            race_name.lower().replace(" ", "_"),
            race_name.lower().replace(" ", ""),
            race_name.lower()
        ]
        
        for variation in variations:
            urls = [
                f"{self.config.base_url}/race/{variation}/{year}/startlist",
                f"{self.config.base_url}/race/{variation}/{year}",
                f"{self.config.base_url}/race/{variation}-{year}/startlist",
                f"{self.config.base_url}/race/{variation}{year}/startlist"
            ]
            possible_urls.extend(urls)
        
        # Test which URLs exist
        valid_urls = []
        for url in possible_urls:
            try:
                response = self._make_request(url)
                if response and response.status_code == 200:
                    valid_urls.append(url)
                    break  # Found a working URL
            except:
                continue
        
        return valid_urls


def create_default_rider_abilities() -> Dict[str, str]:
    """Create default rider abilities for scraped riders."""
    return {
        "sprint": "E",
        "punch": "E",
        "itt": "E", 
        "mountain": "E",
        "break_away": "E"
    }


def estimate_rider_abilities(rider_name: str, team: str) -> Dict[str, str]:
    """Estimate rider abilities based on name and team (basic heuristics)."""
    abilities = create_default_rider_abilities()
    
    # Basic heuristics - this could be expanded with ML or more data
    name_lower = rider_name.lower()
    team_lower = team.lower()
    
    # Sprint specialists (very basic pattern matching)
    sprint_keywords = ["sprint", "fast", "leadout"]
    if any(keyword in name_lower or keyword in team_lower for keyword in sprint_keywords):
        abilities["sprint"] = "C"
    
    # Climbers
    mountain_keywords = ["climb", "mountain", "hill"]
    if any(keyword in name_lower or keyword in team_lower for keyword in mountain_keywords):
        abilities["mountain"] = "C"
    
    # Time trialists
    tt_keywords = ["time", "trial", "chrono"]
    if any(keyword in name_lower or keyword in team_lower for keyword in tt_keywords):
        abilities["itt"] = "C"
    
    return abilities 