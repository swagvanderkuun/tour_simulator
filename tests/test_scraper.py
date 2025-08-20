"""
Tests for procyclingstats scraper (with mocked web requests).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
from pathlib import Path

from tour_simulator.config.scraper_config import ScraperConfig
from tour_simulator.services.procyclingstats_scraper import (
    ProcyclingStatsScraper, ScrapedRider, 
    create_default_rider_abilities, estimate_rider_abilities
)


class TestScraperConfig:
    """Test ScraperConfig class."""
    
    def test_scraper_config_defaults(self):
        """Test scraper configuration defaults."""
        config = ScraperConfig()
        
        assert config.base_url == "https://www.procyclingstats.com"
        assert config.request_delay == 1.0
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.headers is not None
        assert config.user_agents is not None
        assert len(config.user_agents) > 0
    
    def test_get_race_url(self):
        """Test race URL generation."""
        config = ScraperConfig()
        
        url = config.get_race_url("Tour de France", 2025)
        expected = "https://www.procyclingstats.com/race/tour-de-france/2025/startlist"
        assert url == expected
        
        url = config.get_race_url("Vuelta a España", 2024)
        expected = "https://www.procyclingstats.com/race/vuelta-a-españa/2024/startlist"
        assert url == expected


class TestScrapedRider:
    """Test ScrapedRider dataclass."""
    
    def test_scraped_rider_creation(self):
        """Test creating ScrapedRider object."""
        rider = ScrapedRider(
            name="Tadej POGAČAR",
            team="UAE Team Emirates",
            nationality="Slovenia",
            age=26,
            pcs_id="tadej-pogacar",
            profile_url="https://www.procyclingstats.com/rider/tadej-pogacar"
        )
        
        assert rider.name == "Tadej POGAČAR"
        assert rider.team == "UAE Team Emirates"
        assert rider.nationality == "Slovenia"
        assert rider.age == 26
        assert rider.pcs_id == "tadej-pogacar"
        assert rider.profile_url == "https://www.procyclingstats.com/rider/tadej-pogacar"
    
    def test_scraped_rider_defaults(self):
        """Test ScrapedRider with default values."""
        rider = ScrapedRider(
            name="Test Rider",
            team="Test Team",
            nationality="Test Country"
        )
        
        assert rider.age is None
        assert rider.pcs_id is None
        assert rider.profile_url is None


class TestProcyclingStatsScraper:
    """Test ProcyclingStatsScraper class."""
    
    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = ProcyclingStatsScraper()
        assert scraper.config is not None
        assert scraper.session is not None
    
    def test_scraper_with_custom_config(self):
        """Test scraper with custom configuration."""
        config = ScraperConfig(request_delay=2.0, max_retries=5)
        scraper = ProcyclingStatsScraper(config)
        
        assert scraper.config.request_delay == 2.0
        assert scraper.config.max_retries == 5
    
    def test_get_random_user_agent(self):
        """Test user agent rotation."""
        scraper = ProcyclingStatsScraper()
        
        user_agent = scraper._get_random_user_agent()
        assert user_agent in scraper.config.user_agents
    
    @patch('tour_simulator.services.procyclingstats_scraper.requests.Session.get')
    def test_make_request_success(self, mock_get):
        """Test successful HTTP request."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = ProcyclingStatsScraper()
        response = scraper._make_request("https://example.com")
        
        assert response == mock_response
        mock_get.assert_called_once()
    
    @patch('tour_simulator.services.procyclingstats_scraper.requests.Session.get')
    @patch('tour_simulator.services.procyclingstats_scraper.time.sleep')
    def test_make_request_retry(self, mock_sleep, mock_get):
        """Test request retry logic."""
        # Mock failed then successful response
        from requests.exceptions import RequestException
        
        successful_response = Mock()
        successful_response.status_code = 200
        successful_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [
            RequestException("Connection error"),
            RequestException("Connection error"),
            successful_response
        ]
        
        config = ScraperConfig(max_retries=3)
        scraper = ProcyclingStatsScraper(config)
        response = scraper._make_request("https://example.com")
        
        assert response is not None
        assert mock_get.call_count == 3
        # Sleep is called: once for delay_request, once for exponential backoff after first failure,
        # once for delay_request, once for exponential backoff after second failure = 4 times
        assert mock_sleep.call_count == 4
    
    def test_extract_rider_info_missing_data(self):
        """Test extracting rider info when data is missing."""
        scraper = ProcyclingStatsScraper()
        
        # Mock HTML row with no rider link
        mock_row = Mock()
        mock_row.find.return_value = None
        
        rider = scraper._extract_rider_info(mock_row)
        assert rider is None
    
    @patch('tour_simulator.services.procyclingstats_scraper.BeautifulSoup')
    @patch('tour_simulator.services.procyclingstats_scraper.requests.Session.get')
    def test_scrape_race_startlist_mock(self, mock_get, mock_soup):
        """Test scraping race startlist with mocked response."""
        # Mock HTML response
        mock_response = Mock()
        mock_response.content = "<html><body><table></table></body></html>"
        mock_get.return_value = mock_response
        
        # Mock parsed HTML
        mock_table = Mock()
        mock_row1 = Mock()
        mock_row2 = Mock()
        
        # Mock row 1 - valid rider
        mock_link1 = Mock()
        mock_link1.get_text.return_value = "Tadej POGAČAR"
        mock_link1.get.return_value = "/rider/tadej-pogacar"
        mock_row1.find.side_effect = lambda tag, **kwargs: mock_link1 if tag == 'a' else None
        mock_row1.find_all.return_value = []
        
        # Mock row 2 - header row (should be skipped)
        mock_th = Mock()
        mock_row2.find.return_value = mock_th  # Has th element
        
        mock_table.find_all.return_value = [mock_row1, mock_row2]
        
        mock_soup_instance = Mock()
        mock_soup_instance.find_all.return_value = [mock_table]
        mock_soup.return_value = mock_soup_instance
        
        scraper = ProcyclingStatsScraper()
        
        with patch.object(scraper, '_extract_rider_info') as mock_extract:
            mock_extract.return_value = ScrapedRider(
                name="Tadej POGAČAR",
                team="UAE Team Emirates", 
                nationality="Slovenia"
            )
            
            riders = scraper.scrape_race_startlist("Tour de France", 2025)
            
            assert len(riders) == 1
            assert riders[0].name == "Tadej POGAČAR"
    
    def test_convert_to_rider_data(self):
        """Test converting scraped riders to RiderData."""
        scraper = ProcyclingStatsScraper()
        
        scraped_riders = [
            ScrapedRider("Rider 1", "Team 1", "Country 1", age=25, pcs_id="rider-1"),
            ScrapedRider("Rider 2", "Team 2", "Country 2", age=26, pcs_id="rider-2")
        ]
        
        rider_data_list = scraper.convert_to_rider_data(scraped_riders)
        
        assert len(rider_data_list) == 2
        
        rider1 = rider_data_list[0]
        assert rider1.name == "Rider 1"
        assert rider1.team == "Team 1"
        assert rider1.nationality == "Country 1"
        assert rider1.age == 25
        assert rider1.pcs_id == "rider-1"
        assert rider1.tier_abilities["sprint"] == "E"  # Default ability
    
    def test_search_race_urls(self):
        """Test searching for race URLs."""
        scraper = ProcyclingStatsScraper()
        
        with patch.object(scraper, '_make_request') as mock_request:
            # Mock successful response for first URL
            mock_response = Mock()
            mock_response.status_code = 200
            mock_request.return_value = mock_response
            
            urls = scraper.search_race_urls("Tour de France", 2025)
            
            assert len(urls) == 1
            assert "tour-de-france/2025" in urls[0]


class TestRiderAbilities:
    """Test rider ability estimation functions."""
    
    def test_create_default_rider_abilities(self):
        """Test creating default rider abilities."""
        abilities = create_default_rider_abilities()
        
        expected_keys = ["sprint", "punch", "itt", "mountain", "break_away"]
        assert all(key in abilities for key in expected_keys)
        assert all(abilities[key] == "E" for key in expected_keys)
    
    def test_estimate_rider_abilities_sprint(self):
        """Test estimating abilities for sprint specialist."""
        abilities = estimate_rider_abilities("Mark CAVENDISH", "Sprint Team")
        
        # Should upgrade sprint ability
        assert abilities["sprint"] == "C"
        assert abilities["mountain"] == "E"  # Should remain default
    
    def test_estimate_rider_abilities_climber(self):
        """Test estimating abilities for climber."""
        abilities = estimate_rider_abilities("Mountain CLIMBER", "Team Climb")
        
        # Should upgrade mountain ability
        assert abilities["mountain"] == "C"
        assert abilities["sprint"] == "E"  # Should remain default
    
    def test_estimate_rider_abilities_tter(self):
        """Test estimating abilities for time trialist."""
        abilities = estimate_rider_abilities("Time TRIAL", "Chrono Team")
        
        # Should upgrade ITT ability
        assert abilities["itt"] == "C"
        assert abilities["sprint"] == "E"  # Should remain default
    
    def test_estimate_rider_abilities_default(self):
        """Test estimating abilities for unknown rider."""
        abilities = estimate_rider_abilities("Unknown RIDER", "Unknown Team")
        
        # All abilities should remain default
        assert all(abilities[key] == "E" for key in abilities.keys())


class TestIntegration:
    """Integration tests for scraper functionality."""
    
    def test_full_scraping_workflow_mock(self):
        """Test complete scraping workflow with mocked data."""
        # Define realistic rider data
        riders_data = [
            ("Tadej POGAČAR", "UAE Team Emirates", "Slovenia"),
            ("Jonas VINGEGAARD", "Team Visma", "Denmark"),
            ("Primož ROGLIČ", "Bora-hansgrohe", "Slovenia")
        ]
        
        # Run the scraper with mocked extraction
        scraper = ProcyclingStatsScraper()
        
        with patch.object(scraper, 'scrape_race_startlist') as mock_scrape:
            # Return mock scraped riders
            mock_scraped_riders = [
                ScrapedRider(name, team, nationality)
                for name, team, nationality in riders_data
            ]
            mock_scrape.return_value = mock_scraped_riders
            
            rider_data_list, stats = scraper.scrape_and_create_starting_list(
                "Tour de France", 2025, fetch_ages=False
            )
            
            # Verify results
            assert len(rider_data_list) == 3
            assert stats["total_riders"] == 3
            assert stats["teams"] == 3  # All different teams
            assert stats["nationalities"] == 2  # Slovenia appears twice
            
            # Verify specific riders
            names = [r.name for r in rider_data_list]
            assert "Tadej POGAČAR" in names
            assert "Jonas VINGEGAARD" in names
            assert "Primož ROGLIČ" in names 