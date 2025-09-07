"""Live games extractor for dropping-odds.com live page"""

import asyncio
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

from v2.core.exceptions import ScrapingError, ElementNotFoundError, ScrapingTimeoutError
from v2.core.utils import get_timestamp, sanitize_filename


@dataclass
class GameInfo:
    """Game information structure"""
    row_index: int
    country: str
    league: str
    home_team: str
    score: str
    away_team: str
    time: str
    game_url: Optional[str] = None
    game_id: Optional[str] = None
    extracted_at: datetime = None
    
    def __post_init__(self):
        if self.extracted_at is None:
            self.extracted_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "row_index": self.row_index,
            "country": self.country,
            "league": self.league,
            "home_team": self.home_team,
            "score": self.score,
            "away_team": self.away_team,
            "time": self.time,
            "game_url": self.game_url,
            "game_id": self.game_id,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None
        }
    
    def get_game_id(self) -> str:
        """Generate unique game ID"""
        game_string = f"{self.country}_{self.league}_{self.home_team}_{self.away_team}_{self.time}"
        return sanitize_filename(game_string.replace(" ", "_").lower())


class LiveGamesExtractor:
    """Extractor for live games from dropping-odds.com"""
    
    def __init__(self, headless: bool = True, timeout: int = 30):
        """
        Initialize live games extractor
        
        Args:
            headless: Run browser in headless mode
            timeout: Page load timeout in seconds
        """
        self.headless = headless
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.driver: Optional[webdriver.Chrome] = None
        self.base_url = "https://dropping-odds.com/index.php?view=live"
        
        # Statistics
        self.stats = {
            "total_extractions": 0,
            "successful_extractions": 0,
            "failed_extractions": 0,
            "games_found": 0,
            "last_extraction": None
        }
    
    def setup_driver(self) -> webdriver.Chrome:
        """Setup Chrome WebDriver
        
        Returns:
            Configured Chrome WebDriver
        """
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Performance and stability options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
            
            # Set page load strategy
            chrome_options.page_load_strategy = 'eager'
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(self.timeout)
            driver.implicitly_wait(10)
            
            self.logger.info("Chrome WebDriver initialized successfully")
            return driver
            
        except Exception as e:
            self.logger.error(f"Failed to setup Chrome WebDriver: {e}")
            raise ScrapingError(f"WebDriver setup failed: {e}", "SCRAPING_009")
    
    def extract_live_games(self) -> List[GameInfo]:
        """Extract live games from the main page
        
        Returns:
            List of GameInfo objects
        """
        self.stats["total_extractions"] += 1
        
        try:
            self.logger.info("Starting live games extraction...")
            
            # Setup driver if not already done
            if self.driver is None:
                self.driver = self.setup_driver()
            
            # Navigate to live page
            self.logger.debug(f"Navigating to: {self.base_url}")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            
            try:
                # Wait for the main table to be present
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
                self.logger.debug("Page loaded successfully")
            except TimeoutException:
                raise ScrapingTimeoutError("page_load", self.timeout)
            
            # Extract games from table
            games = self._extract_games_from_table()
            
            self.stats["successful_extractions"] += 1
            self.stats["games_found"] = len(games)
            self.stats["last_extraction"] = datetime.now().isoformat()
            
            self.logger.info(f"Successfully extracted {len(games)} games")
            return games
            
        except Exception as e:
            self.stats["failed_extractions"] += 1
            self.logger.error(f"Failed to extract live games: {e}")
            raise
    
    def _extract_games_from_table(self) -> List[GameInfo]:
        """Extract games from the main table
        
        Returns:
            List of GameInfo objects
        """
        games = []
        
        try:
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Find the main table (based on analysis: 1 table found)
            tables = soup.find_all('table')
            
            if not tables:
                raise ElementNotFoundError("table", self.base_url)
            
            main_table = tables[0]  # First table is the games table
            rows = main_table.find_all('tr')
            
            self.logger.debug(f"Found {len(rows)} rows in main table")
            
            # Process each row (skip first row which is header)
            for row_index, row in enumerate(rows[1:], start=1):
                try:
                    game_info = self._parse_game_row(row, row_index)
                    if game_info:
                        games.append(game_info)
                except Exception as e:
                    self.logger.warning(f"Failed to parse row {row_index}: {e}")
                    continue
            
            self.logger.info(f"Parsed {len(games)} valid games from {len(rows)} rows")
            return games
            
        except Exception as e:
            self.logger.error(f"Failed to extract games from table: {e}")
            raise ScrapingError(f"Table extraction failed: {e}", "SCRAPING_003")
    
    def _parse_game_row(self, row, row_index: int) -> Optional[GameInfo]:
        """Parse individual game row
        
        Args:
            row: BeautifulSoup row element
            row_index: Row index in table
            
        Returns:
            GameInfo object or None if invalid row
        """
        try:
            cells = row.find_all(['td', 'th'])
            
            # Skip header rows or rows with insufficient cells
            if len(cells) < 6:
                return None
            
            # Check if this is a header row
            if row.find('th') or any('header' in cell.get('class', []) for cell in cells):
                return None
            
            # Extract game_id from row attribute
            game_id = row.get('game_id')
            if not game_id:
                self.logger.debug(f"Row {row_index} has no game_id attribute")
            
            # Extract cell contents (based on 6-column structure from analysis)
            country = self._clean_text(cells[0].get_text(strip=True) if cells[0] else "")
            league = self._clean_text(cells[1].get_text(strip=True) if cells[1] else "")
            home_team = self._clean_text(cells[2].get_text(strip=True) if cells[2] else "")
            score = self._clean_text(cells[3].get_text(strip=True) if cells[3] else "")
            away_team = self._clean_text(cells[4].get_text(strip=True) if cells[4] else "")
            time = self._clean_text(cells[5].get_text(strip=True) if cells[5] else "")
            
            # Skip empty or invalid rows (country pode estar vazio)
            if not all([league, home_team, away_team]):
                return None
            
            # Extract game URL if available
            game_url = None
            for cell in cells:
                link = cell.find('a')
                if link and link.get('href'):
                    href = link.get('href')
                    if 'game' in href or 'match' in href:
                        game_url = self._resolve_url(href)
                        break
            
            game_info = GameInfo(
                row_index=row_index,
                country=country,
                league=league,
                home_team=home_team,
                score=score,
                away_team=away_team,
                time=time,
                game_url=game_url,
                game_id=game_id
            )
            
            self.logger.debug(f"Parsed game: {home_team} vs {away_team} ({league}) - ID: {game_id}")
            return game_info
            
        except Exception as e:
            self.logger.warning(f"Failed to parse row {row_index}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove extra whitespace and newlines
        cleaned = ' '.join(text.strip().split())
        
        # Remove common unwanted characters
        cleaned = cleaned.replace('\n', ' ').replace('\t', ' ')
        
        return cleaned.strip()
    
    def _resolve_url(self, href: str) -> str:
        """Resolve relative URL to absolute
        
        Args:
            href: Relative or absolute URL
            
        Returns:
            Absolute URL
        """
        if href.startswith('http'):
            return href
        
        base_domain = "https://dropping-odds.com"
        
        if href.startswith('/'):
            return f"{base_domain}{href}"
        else:
            return f"{base_domain}/{href}"
    
    def get_game_details_url(self, game_info: GameInfo) -> Optional[str]:
        """Get detailed game URL for further analysis
        
        Args:
            game_info: Game information
            
        Returns:
            Game details URL or None
        """
        if game_info.game_url:
            return game_info.game_url
        
        # Try to construct URL based on team names (fallback)
        try:
            # This would need to be implemented based on the site's URL structure
            # For now, return None as we need the actual URL pattern
            return None
        except Exception as e:
            self.logger.warning(f"Failed to construct game URL: {e}")
            return None
    
    def refresh_page(self) -> None:
        """Refresh the current page"""
        try:
            if self.driver:
                self.driver.refresh()
                # Wait for page to reload
                WebDriverWait(self.driver, self.timeout).until(
                    EC.presence_of_element_located((By.TAG_NAME, "table"))
                )
                self.logger.debug("Page refreshed successfully")
        except Exception as e:
            self.logger.error(f"Failed to refresh page: {e}")
            raise ScrapingError(f"Page refresh failed: {e}", "SCRAPING_008")
    
    def get_stats(self) -> Dict:
        """Get extraction statistics
        
        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
    
    def close(self) -> None:
        """Close the WebDriver"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.logger.info("WebDriver closed successfully")
        except Exception as e:
            self.logger.warning(f"Error closing WebDriver: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.close()


# Async wrapper for the extractor
class AsyncLiveGamesExtractor:
    """Async wrapper for LiveGamesExtractor"""
    
    def __init__(self, *args, **kwargs):
        self.extractor = LiveGamesExtractor(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
    
    async def extract_live_games(self) -> List[GameInfo]:
        """Async version of extract_live_games
        
        Returns:
            List of GameInfo objects
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Run the synchronous extraction in a thread pool
            games = await loop.run_in_executor(
                None, self.extractor.extract_live_games
            )
            return games
        except Exception as e:
            self.logger.error(f"Async extraction failed: {e}")
            raise
    
    async def close(self) -> None:
        """Async close method"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.extractor.close)
    
    def get_stats(self) -> Dict:
        """Get extraction statistics"""
        return self.stats.copy()
    
    async def extract_games_from_url_async(self, url: str) -> List[GameInfo]:
        """Async method to extract games from a specific URL
        
        Args:
            url: URL to extract games from
            
        Returns:
            List of GameInfo objects
        """
        loop = asyncio.get_event_loop()
        
        def _extract_sync():
            # Temporarily change base_url
            original_url = self.base_url
            self.base_url = url
            try:
                return self.extract_live_games()
            finally:
                self.base_url = original_url
        
        try:
            games = await loop.run_in_executor(None, _extract_sync)
            return games
        except Exception as e:
            self.logger.error(f"Async URL extraction failed: {e}")
            raise
    
    async def extract_games_async(self, soup: BeautifulSoup) -> List[GameInfo]:
        """Async method to extract games from BeautifulSoup object
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of GameInfo objects
        """
        loop = asyncio.get_event_loop()
        
        def _extract_from_soup():
            games = []
            # Find the main table
            tables = soup.find_all('table')
            
            if not tables:
                return games
            
            main_table = tables[0]
            rows = main_table.find_all('tr')
            
            # Process each row
            for row_index, row in enumerate(rows):
                try:
                    game_info = self._parse_game_row(row, row_index)
                    if game_info:
                        games.append(game_info)
                except Exception as e:
                    self.logger.warning(f"Failed to parse row {row_index}: {e}")
                    continue
            
            return games
        
        try:
            games = await loop.run_in_executor(None, _extract_from_soup)
            self.stats["total_extractions"] += 1
            self.stats["successful_extractions"] += 1
            self.stats["games_found"] = len(games)
            self.stats["last_extraction"] = datetime.now().isoformat()
            return games
        except Exception as e:
             self.stats["failed_extractions"] += 1
             self.logger.error(f"Async soup extraction failed: {e}")
             raise
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()