"""Page monitor for continuous live odds monitoring"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup

from .live_extractor import LiveGamesExtractor, GameInfo
from .drop_detector import EnhancedDropDetector, DropInfo
from v2.core.event_bus import event_bus, EventPriority
from v2.core.exceptions import ScrapingError, ConfigurationError
from v2.core.utils import get_timestamp, setup_logging


class MonitorStatus(Enum):
    """Monitor status states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    STOPPING = "stopping"


@dataclass
class MonitorConfig:
    """Configuration for page monitor"""
    url: str = "https://dropping-odds.com/index.php?view=live"
    refresh_interval: int = 30  # seconds
    max_retries: int = 3
    retry_delay: int = 5  # seconds
    timeout: int = 10  # seconds
    headless: bool = True
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # Detection settings
    enable_drop_detection: bool = True
    drop_detection_tables: List[str] = field(default_factory=lambda: ["1x2", "total", "handicap"])
    
    # Performance settings
    max_games_per_cycle: int = 100
    enable_caching: bool = True
    cache_duration: int = 60  # seconds
    
    # Notification settings
    notify_on_drops: bool = True
    notify_on_errors: bool = True
    min_confidence_for_notification: str = "medium"


@dataclass
class MonitorStats:
    """Monitor statistics"""
    start_time: Optional[datetime] = None
    total_cycles: int = 0
    successful_cycles: int = 0
    failed_cycles: int = 0
    total_games_processed: int = 0
    total_drops_detected: int = 0
    last_cycle_time: Optional[datetime] = None
    last_error: Optional[str] = None
    average_cycle_duration: float = 0.0
    
    def update_cycle(self, success: bool, games_count: int = 0, 
                    drops_count: int = 0, duration: float = 0.0, error: str = None):
        """Update cycle statistics"""
        self.total_cycles += 1
        self.last_cycle_time = datetime.now()
        
        if success:
            self.successful_cycles += 1
            self.total_games_processed += games_count
            self.total_drops_detected += drops_count
        else:
            self.failed_cycles += 1
            self.last_error = error
        
        # Update average duration
        if duration > 0:
            total_duration = self.average_cycle_duration * (self.total_cycles - 1) + duration
            self.average_cycle_duration = total_duration / self.total_cycles
    
    def get_uptime(self) -> Optional[timedelta]:
        """Get monitor uptime"""
        if self.start_time:
            return datetime.now() - self.start_time
        return None
    
    def get_success_rate(self) -> float:
        """Get success rate percentage"""
        if self.total_cycles == 0:
            return 0.0
        return (self.successful_cycles / self.total_cycles) * 100


class PageMonitor:
    """Monitor for continuous live odds page monitoring"""
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        """
        Initialize page monitor
        
        Args:
            config: Monitor configuration
        """
        self.config = config or MonitorConfig()
        self.logger = logging.getLogger(__name__)
        
        # Components
        self.extractor = LiveGamesExtractor()
        self.drop_detector = EnhancedDropDetector() if self.config.enable_drop_detection else None
        
        # State
        self.status = MonitorStatus.STOPPED
        self.stats = MonitorStats()
        self.driver: Optional[webdriver.Chrome] = None
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Data storage
        self.previous_games_data: Dict[str, GameInfo] = {}
        self.cache: Dict[str, Any] = {}
        self.cache_timestamps: Dict[str, datetime] = {}
        
        # Callbacks
        self.on_games_extracted: Optional[Callable[[List[GameInfo]], None]] = None
        self.on_drops_detected: Optional[Callable[[List[DropInfo]], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        self.on_status_change: Optional[Callable[[MonitorStatus], None]] = None
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions"""
        event_bus.subscribe("monitor.start", self._handle_start_event)
        event_bus.subscribe("monitor.stop", self._handle_stop_event)
        event_bus.subscribe("monitor.pause", self._handle_pause_event)
        event_bus.subscribe("monitor.resume", self._handle_resume_event)
    
    async def start(self) -> bool:
        """
        Start monitoring
        
        Returns:
            True if started successfully
        """
        if self.status == MonitorStatus.RUNNING:
            self.logger.warning("Monitor is already running")
            return True
        
        try:
            self.logger.info("Starting page monitor...")
            self._set_status(MonitorStatus.STARTING)
            
            # Initialize WebDriver
            if not await self._initialize_driver():
                raise ScrapingError("Failed to initialize WebDriver", "SCRAPING_001")
            
            # Start monitoring task
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Update stats
            self.stats.start_time = datetime.now()
            
            self._set_status(MonitorStatus.RUNNING)
            self.logger.info("Page monitor started successfully")
            
            # Publish event
            from v2.core.event_bus import Event
            start_event = Event(
                name="monitor.started",
                data={
                    "timestamp": get_timestamp(),
                    "config": self.config.__dict__
                },
                priority=EventPriority.HIGH
            )
            await event_bus.publish_async(start_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitor: {e}")
            self._set_status(MonitorStatus.ERROR)
            
            if self.on_error:
                self.on_error(e)
            
            return False
    
    async def stop(self) -> bool:
        """
        Stop monitoring
        
        Returns:
            True if stopped successfully
        """
        if self.status == MonitorStatus.STOPPED:
            self.logger.warning("Monitor is already stopped")
            return True
        
        try:
            self.logger.info("Stopping page monitor...")
            self._set_status(MonitorStatus.STOPPING)
            
            # Cancel monitoring task
            if self.monitoring_task and not self.monitoring_task.done():
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Close WebDriver
            await self._cleanup_driver()
            
            self._set_status(MonitorStatus.STOPPED)
            self.logger.info("Page monitor stopped")
            
            # Publish event
            from v2.core.event_bus import Event
            stop_event = Event(
                name="monitor.stopped",
                data={
                    "timestamp": get_timestamp(),
                    "stats": self.get_stats()
                },
                priority=EventPriority.HIGH
            )
            await event_bus.publish_async(stop_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping monitor: {e}")
            return False
    
    async def pause(self) -> bool:
        """
        Pause monitoring
        
        Returns:
            True if paused successfully
        """
        if self.status != MonitorStatus.RUNNING:
            self.logger.warning("Monitor is not running")
            return False
        
        self._set_status(MonitorStatus.PAUSED)
        self.logger.info("Monitor paused")
        return True
    
    async def resume(self) -> bool:
        """
        Resume monitoring
        
        Returns:
            True if resumed successfully
        """
        if self.status != MonitorStatus.PAUSED:
            self.logger.warning("Monitor is not paused")
            return False
        
        self._set_status(MonitorStatus.RUNNING)
        self.logger.info("Monitor resumed")
        return True
    
    async def _initialize_driver(self) -> bool:
        """
        Initialize WebDriver
        
        Returns:
            True if successful
        """
        try:
            options = Options()
            
            if self.config.headless:
                options.add_argument("--headless")
            
            options.add_argument(f"--user-agent={self.config.user_agent}")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(self.config.timeout)
            
            # Test navigation
            self.driver.get(self.config.url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.config.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            self.logger.info("WebDriver initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            return False
    
    async def _cleanup_driver(self):
        """Cleanup WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.debug("WebDriver closed")
            except Exception as e:
                self.logger.warning(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        self.logger.info("Starting monitoring loop")
        
        while self.status in [MonitorStatus.RUNNING, MonitorStatus.PAUSED]:
            try:
                # Skip cycle if paused
                if self.status == MonitorStatus.PAUSED:
                    await asyncio.sleep(1)
                    continue
                
                cycle_start = datetime.now()
                
                # Perform monitoring cycle
                success, games_count, drops_count = await self._perform_cycle()
                
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                
                # Update statistics
                self.stats.update_cycle(
                    success=success,
                    games_count=games_count,
                    drops_count=drops_count,
                    duration=cycle_duration
                )
                
                # Wait for next cycle
                await asyncio.sleep(self.config.refresh_interval)
                
            except asyncio.CancelledError:
                self.logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                self.stats.update_cycle(success=False, error=str(e))
                
                if self.on_error:
                    self.on_error(e)
                
                # Wait before retrying
                await asyncio.sleep(self.config.retry_delay)
    
    async def _perform_cycle(self) -> tuple[bool, int, int]:
        """
        Perform one monitoring cycle
        
        Returns:
            Tuple of (success, games_count, drops_count)
        """
        try:
            # Refresh page
            if not await self._refresh_page():
                return False, 0, 0
            
            # Extract games data
            games = await self._extract_games()
            if not games:
                self.logger.warning("No games extracted")
                return False, 0, 0
            
            games_count = len(games)
            drops_count = 0
            
            # Detect drops if enabled
            if self.config.enable_drop_detection and self.drop_detector:
                drops = await self._detect_drops(games)
                drops_count = len(drops)
                
                if drops and self.config.notify_on_drops:
                    await self._notify_drops(drops)
            
            # Update previous data
            self._update_previous_data(games)
            
            # Notify games extracted
            if self.on_games_extracted:
                self.on_games_extracted(games)
            
            # Publish events
            await event_bus.publish("games.extracted", {
                "timestamp": get_timestamp(),
                "games_count": games_count,
                "games": [game.to_dict() for game in games[:10]]  # Limit for performance
            })
            
            if drops_count > 0:
                from v2.core.event_bus import Event
                drops_event = Event(
                    name="drops.detected",
                    data={
                        "timestamp": get_timestamp(),
                        "drops_count": drops_count
                    },
                    priority=EventPriority.NORMAL
                )
                await event_bus.publish_async(drops_event)
            
            self.logger.debug(f"Cycle completed: {games_count} games, {drops_count} drops")
            return True, games_count, drops_count
            
        except Exception as e:
            self.logger.error(f"Cycle failed: {e}")
            return False, 0, 0
    
    async def _refresh_page(self) -> bool:
        """
        Refresh the page
        
        Returns:
            True if successful
        """
        try:
            if not self.driver:
                return False
            
            self.driver.refresh()
            
            # Wait for table to load
            WebDriverWait(self.driver, self.config.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            return True
            
        except TimeoutException:
            self.logger.warning("Page refresh timeout")
            return False
        except WebDriverException as e:
            self.logger.error(f"WebDriver error during refresh: {e}")
            return False
    
    async def _extract_games(self) -> List[GameInfo]:
        """
        Extract games from current page
        
        Returns:
            List of extracted games
        """
        try:
            if not self.driver:
                return []
            
            # Get page source
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Use extractor to get games
            games = await self.extractor.extract_games_async(soup)
            
            # Limit games if configured
            if self.config.max_games_per_cycle > 0:
                games = games[:self.config.max_games_per_cycle]
            
            return games
            
        except Exception as e:
            self.logger.error(f"Game extraction failed: {e}")
            return []
    
    async def _detect_drops(self, games: List[GameInfo]) -> List[DropInfo]:
        """
        Detect drops in extracted games
        
        Args:
            games: List of extracted games
            
        Returns:
            List of detected drops
        """
        try:
            if not self.drop_detector or not self.driver:
                return []
            
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            all_drops = []
            
            # Detect drops for each configured table type
            for table_type in self.config.drop_detection_tables:
                # Prepare previous data for comparison
                previous_data = self._get_previous_data_for_table(table_type)
                
                drops = self.drop_detector.detect_drops(soup, table_type, previous_data)
                all_drops.extend(drops)
            
            return all_drops
            
        except Exception as e:
            self.logger.error(f"Drop detection failed: {e}")
            return []
    
    def _get_previous_data_for_table(self, table_type: str) -> Dict:
        """
        Get previous data for table comparison
        
        Args:
            table_type: Table type
            
        Returns:
            Previous data dictionary
        """
        # This would need to be implemented based on how data is stored
        # For now, return empty dict
        return {}
    
    def _update_previous_data(self, games: List[GameInfo]):
        """Update previous games data for comparison
        
        Args:
            games: Current games data
        """
        # Update previous data with current games
        for game in games:
            if game.game_id:
                self.previous_games_data[game.game_id] = game
        
        # Clean old data (keep only recent games)
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(hours=2)
        
        self.previous_games_data = {
            game_id: game for game_id, game in self.previous_games_data.items()
            if game.extracted_at and game.extracted_at > cutoff_time
        }
    
    async def _notify_drops(self, drops: List[DropInfo]):
        """Notify about detected drops
        
        Args:
            drops: List of detected drops
        """
        try:
            # Filter drops by confidence level
            confidence_levels = ["low", "medium", "high", "very_high"]
            min_level_index = confidence_levels.index(self.config.min_confidence_for_notification)
            
            filtered_drops = [
                drop for drop in drops
                if confidence_levels.index(drop.confidence.value) >= min_level_index
            ]
            
            if filtered_drops and self.on_drops_detected:
                self.on_drops_detected(filtered_drops)
            
            # Publish event
            if filtered_drops:
                from v2.core.event_bus import Event
                notification_event = Event(
                    name="drops.notification",
                    data={
                        "timestamp": get_timestamp(),
                        "drops": [drop.to_dict() for drop in filtered_drops]
                    },
                    priority=EventPriority.HIGH
                )
                await event_bus.publish_async(notification_event)
            
        except Exception as e:
            self.logger.error(f"Drop notification failed: {e}")
    
    def _set_status(self, status: MonitorStatus):
        """Set monitor status and notify
        
        Args:
            status: New status
        """
        old_status = self.status
        self.status = status
        
        if old_status != status:
            self.logger.info(f"Monitor status changed: {old_status.value} -> {status.value}")
            
            if self.on_status_change:
                self.on_status_change(status)
    
    async def _handle_start_event(self, data: Dict[str, Any]):
        """Handle start event from event bus"""
        await self.start()
    
    async def _handle_stop_event(self, data: Dict[str, Any]):
        """Handle stop event from event bus"""
        await self.stop()
    
    async def _handle_pause_event(self, data: Dict[str, Any]):
        """Handle pause event from event bus"""
        await self.pause()
    
    async def _handle_resume_event(self, data: Dict[str, Any]):
        """Handle resume event from event bus"""
        await self.resume()
    
    def get_status(self) -> MonitorStatus:
        """Get current monitor status"""
        return self.status
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics"""
        stats_dict = {
            "status": self.status.value,
            "start_time": self.stats.start_time.isoformat() if self.stats.start_time else None,
            "uptime_seconds": self.stats.get_uptime().total_seconds() if self.stats.get_uptime() else 0,
            "total_cycles": self.stats.total_cycles,
            "successful_cycles": self.stats.successful_cycles,
            "failed_cycles": self.stats.failed_cycles,
            "success_rate": self.stats.get_success_rate(),
            "total_games_processed": self.stats.total_games_processed,
            "total_drops_detected": self.stats.total_drops_detected,
            "average_cycle_duration": self.stats.average_cycle_duration,
            "last_cycle_time": self.stats.last_cycle_time.isoformat() if self.stats.last_cycle_time else None,
            "last_error": self.stats.last_error
        }
        
        # Add drop detector stats if available
        if self.drop_detector:
            stats_dict["drop_detector_stats"] = self.drop_detector.get_stats()
        
        return stats_dict
    
    def configure(self, **kwargs):
        """Update monitor configuration
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self.logger.info(f"Updated config {key} = {value}")
            else:
                self.logger.warning(f"Unknown config parameter: {key}")
    
    def set_callbacks(self, **callbacks):
        """Set callback functions
        
        Args:
            **callbacks: Callback functions
        """
        for name, callback in callbacks.items():
            if hasattr(self, f"on_{name}"):
                setattr(self, f"on_{name}", callback)
                self.logger.info(f"Set callback: on_{name}")
            else:
                self.logger.warning(f"Unknown callback: on_{name}")