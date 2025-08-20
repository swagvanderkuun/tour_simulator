"""
Scraper configuration for procyclingstats.com
"""

from dataclasses import dataclass
from typing import Dict, Optional
import time


@dataclass
class ScraperConfig:
    """Configuration for web scraping operations."""
    
    # Base URL for procyclingstats
    base_url: str = "https://www.procyclingstats.com"
    
    # Request configuration
    request_delay: float = 1.0  # Delay between requests (seconds)
    timeout: int = 30  # Request timeout (seconds)
    max_retries: int = 3  # Maximum number of retries
    
    # Headers to use for requests
    headers: Dict[str, str] = None
    
    # User agent rotation
    user_agents: list = None
    
    def __post_init__(self):
        """Initialize default configurations."""
        if self.headers is None:
            self.headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        
        if self.user_agents is None:
            self.user_agents = [
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15'
            ]
    
    def get_race_url(self, race_name: str, year: int) -> str:
        """Generate URL for race starting list."""
        # Example: https://www.procyclingstats.com/race/tour-de-france/2025/startlist
        race_slug = race_name.lower().replace(" ", "-")
        return f"{self.base_url}/race/{race_slug}/{year}/startlist"
    
    def delay_request(self) -> None:
        """Add delay between requests to be respectful."""
        time.sleep(self.request_delay) 