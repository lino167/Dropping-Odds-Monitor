"""Event page extractor for individual game odds tables"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import re

from v2.core.exceptions import ScrapingError, ElementNotFoundError, ScrapingTimeoutError
from v2.core.utils import get_timestamp, sanitize_filename

@dataclass
class OddsRecord:
    """Single odds record from event table"""
    date: str
    time: str
    score: str
    home_odds: float
    draw_odds: float
    away_odds: float
    home_percentage: str
    away_percentage: str
    penalty: str
    red_card: str
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'date': self.date,
            'time': self.time,
            'score': self.score,
            'home_odds': self.home_odds,
            'draw_odds': self.draw_odds,
            'away_odds': self.away_odds,
            'home_percentage': self.home_percentage,
            'away_percentage': self.away_percentage,
            'penalty': self.penalty,
            'red_card': self.red_card,
            'timestamp': self.timestamp
        }

@dataclass
class EventData:
    """Complete event data with odds history"""
    game_id: str
    bet_type: str
    url: str
    title: str
    total_records: int
    odds_records: List[OddsRecord]
    extraction_timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'game_id': self.game_id,
            'bet_type': self.bet_type,
            'url': self.url,
            'title': self.title,
            'total_records': self.total_records,
            'odds_records': [record.to_dict() for record in self.odds_records],
            'extraction_timestamp': self.extraction_timestamp
        }

class EventExtractor:
    """Extractor for individual event pages with odds tables"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize event extractor
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.driver: Optional[webdriver.Chrome] = None
        
        # Statistics
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "records_extracted": 0,
            "last_extraction": None
        }
    
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver with optimal settings"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        # Performance optimizations
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-extensions')
        
        # User agent
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            self.logger.debug("Chrome WebDriver initialized successfully")
            return driver
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise ScrapingError(f"WebDriver initialization failed: {e}", "DRIVER_001")
    
    def extract_event_data(self, game_id: str, bet_type: str = "1x2") -> EventData:
        """
        Extract odds data from event page
        
        Args:
            game_id: Game ID from the live page
            bet_type: Type of bet (1x2, ou, ah, etc.)
            
        Returns:
            EventData object with complete odds history
        """
        self.stats["total_extractions"] += 1
        
        url = f"https://dropping-odds.com/event.php?id={game_id}&t={bet_type}"
        
        try:
            self.logger.info(f"Extracting event data: {url}")
            
            # Setup driver if not already done
            if self.driver is None:
                self.driver = self.setup_driver()
            
            # Navigate to event page
            self.logger.debug(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            
            try:
                # Wait for the main table to be present
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                self.logger.debug("Event page loaded successfully")
            except TimeoutException:
                raise ScrapingTimeoutError("event_page_load", self.timeout)
            
            # Extract data from page
            event_data = self._extract_odds_table(game_id, bet_type, url)
            
            self.stats["successful_extractions"] += 1
            self.stats["records_extracted"] += event_data.total_records
            self.stats["last_extraction"] = datetime.now().isoformat()
            
            self.logger.info(f"Successfully extracted {event_data.total_records} odds records")
            return event_data
            
        except Exception as e:
            self.stats["failed_extractions"] += 1
            self.logger.error(f"Failed to extract event data: {e}")
            raise
    
    def _extract_odds_table(self, game_id: str, bet_type: str, url: str) -> EventData:
        """
        Extract odds table from the current page
        
        Returns:
            EventData object
        """
        try:
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Get page title
            title = soup.title.string.strip() if soup.title else f"Game {game_id}"
            
            # Find the odds table
            tables = soup.find_all('table')
            
            if not tables:
                raise ElementNotFoundError("odds_table", url)
            
            # Based on analysis: there's typically 1 main table
            odds_table = tables[0]
            rows = odds_table.find_all('tr')
            
            self.logger.debug(f"Found odds table with {len(rows)} rows")
            
            # Parse table rows
            odds_records = []
            
            # Skip header row (index 0)
            for row_index, row in enumerate(rows[1:], start=1):
                try:
                    record = self._parse_odds_row(row, row_index)
                    if record:
                        odds_records.append(record)
                except Exception as e:
                    self.logger.warning(f"Failed to parse odds row {row_index}: {e}")
                    continue
            
            event_data = EventData(
                game_id=game_id,
                bet_type=bet_type,
                url=url,
                title=title,
                total_records=len(odds_records),
                odds_records=odds_records,
                extraction_timestamp=get_timestamp()
            )
            
            self.logger.info(f"Parsed {len(odds_records)} odds records from {len(rows)} rows")
            return event_data
            
        except Exception as e:
            self.logger.error(f"Failed to extract odds table: {e}")
            raise ScrapingError(f"Odds table extraction failed: {e}", "SCRAPING_004")
    
    def _parse_odds_row(self, row, row_index: int) -> Optional[OddsRecord]:
        """
        Parse a single odds table row
        
        Args:
            row: BeautifulSoup row element
            row_index: Row index for logging
            
        Returns:
            OddsRecord object or None if invalid
        """
        try:
            cells = row.find_all('td')
            
            if len(cells) < 6:  # Minimum required columns
                return None
            
            # Extract data based on identified structure:
            # [Date, Time, Score, Home, Draw, Away, Home%, Away%, Penalty, Red]
            date = self._clean_text(cells[0].get_text(strip=True))
            time = self._clean_text(cells[1].get_text(strip=True))
            score = self._clean_text(cells[2].get_text(strip=True))
            
            # Parse odds (convert to float)
            home_odds = self._parse_odds_value(cells[3].get_text(strip=True))
            draw_odds = self._parse_odds_value(cells[4].get_text(strip=True))
            away_odds = self._parse_odds_value(cells[5].get_text(strip=True))
            
            # Optional columns
            home_percentage = self._clean_text(cells[6].get_text(strip=True)) if len(cells) > 6 else "-"
            away_percentage = self._clean_text(cells[7].get_text(strip=True)) if len(cells) > 7 else "-"
            penalty = self._clean_text(cells[8].get_text(strip=True)) if len(cells) > 8 else "-"
            red_card = self._clean_text(cells[9].get_text(strip=True)) if len(cells) > 9 else "-"
            
            # Skip rows with invalid odds
            if home_odds == 0.0 and draw_odds == 0.0 and away_odds == 0.0:
                return None
            
            record = OddsRecord(
                date=date,
                time=time,
                score=score,
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                home_percentage=home_percentage,
                away_percentage=away_percentage,
                penalty=penalty,
                red_card=red_card,
                timestamp=get_timestamp()
            )
            
            return record
            
        except Exception as e:
            self.logger.warning(f"Failed to parse odds row {row_index}: {e}")
            return None
    
    def _parse_odds_value(self, text: str) -> float:
        """
        Parse odds value from text
        
        Args:
            text: Raw text from cell
            
        Returns:
            Float odds value or 0.0 if invalid
        """
        try:
            # Clean text
            cleaned = text.strip().replace(',', '.')
            
            # Skip empty or dash values
            if not cleaned or cleaned == '-' or cleaned == '':
                return 0.0
            
            # Parse float
            return float(cleaned)
            
        except (ValueError, TypeError):
            return 0.0
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned
    
    def extract_multiple_bet_types(self, game_id: str, bet_types: List[str] = None) -> Dict[str, EventData]:
        """
        Extract data for multiple bet types for the same game
        
        Args:
            game_id: Game ID
            bet_types: List of bet types to extract
            
        Returns:
            Dictionary mapping bet_type to EventData
        """
        if bet_types is None:
            bet_types = ["1x2", "ou", "ah"]  # Common bet types
        
        results = {}
        
        for bet_type in bet_types:
            try:
                self.logger.info(f"Extracting {bet_type} data for game {game_id}")
                event_data = self.extract_event_data(game_id, bet_type)
                results[bet_type] = event_data
            except Exception as e:
                self.logger.error(f"Failed to extract {bet_type} for game {game_id}: {e}")
                continue
        
        return results
    
    def close(self) -> None:
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.debug("WebDriver closed successfully")
            except Exception as e:
                self.logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    def get_stats(self) -> Dict:
        """Get extraction statistics"""
        return self.stats.copy()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()