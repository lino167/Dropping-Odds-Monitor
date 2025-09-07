"""Main scraper module integrating all scraping components"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

from .live_extractor import LiveGamesExtractor, GameInfo
from .drop_detector import EnhancedDropDetector, DropInfo
from .page_monitor import PageMonitor, MonitorConfig, MonitorStatus
from v2.core.base_module import BaseModule, ModuleStatus
from v2.core.event_bus import event_bus, EventPriority, Event
from v2.core.exceptions import ModuleError, ConfigurationError
from v2.core.utils import get_timestamp, setup_logging, safe_get


@dataclass
class ScraperConfig:
    """Configuration for scraper module"""
    # Monitor settings
    monitor_url: str = "https://dropping-odds.com/index.php?view=live"
    refresh_interval: int = 30
    max_retries: int = 3
    timeout: int = 10
    headless: bool = True
    
    # Detection settings
    enable_drop_detection: bool = True
    drop_detection_tables: List[str] = None
    min_confidence_for_notification: str = "medium"
    
    # Performance settings
    max_games_per_cycle: int = 100
    enable_caching: bool = True
    cache_duration: int = 60
    
    # Data storage
    save_extracted_data: bool = True
    save_drop_data: bool = True
    data_retention_hours: int = 24
    
    def __post_init__(self):
        if self.drop_detection_tables is None:
            self.drop_detection_tables = ["1x2", "total", "handicap"]


class ScraperModule(BaseModule):
    """Main scraper module for live odds monitoring"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize scraper module
        
        Args:
            config: Module configuration
        """
        super().__init__("scraper", config)
        
        # Parse configuration
        self.scraper_config = self._parse_config(config or {})
        
        # Components
        self.extractor: Optional[LiveGamesExtractor] = None
        self.drop_detector: Optional[EnhancedDropDetector] = None
        self.monitor: Optional[PageMonitor] = None
        
        # Data storage
        self.extracted_games: List[GameInfo] = []
        self.detected_drops: List[DropInfo] = []
        self.extraction_history: Dict[str, List[GameInfo]] = {}
        
        # Statistics
        self.stats = {
            "total_extractions": 0,
            "total_games_extracted": 0,
            "total_drops_detected": 0,
            "extraction_errors": 0,
            "detection_errors": 0,
            "last_extraction": None,
            "last_detection": None,
            "average_games_per_extraction": 0.0
        }
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _parse_config(self, config: Dict[str, Any]) -> ScraperConfig:
        """Parse configuration dictionary into ScraperConfig
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Parsed ScraperConfig object
        """
        try:
            scraper_config = config.get('scraper', {})
            
            return ScraperConfig(
                monitor_url=scraper_config.get('monitor_url', ScraperConfig.monitor_url),
                refresh_interval=scraper_config.get('refresh_interval', ScraperConfig.refresh_interval),
                max_retries=scraper_config.get('max_retries', ScraperConfig.max_retries),
                timeout=scraper_config.get('timeout', ScraperConfig.timeout),
                headless=scraper_config.get('headless', ScraperConfig.headless),
                enable_drop_detection=scraper_config.get('enable_drop_detection', ScraperConfig.enable_drop_detection),
                drop_detection_tables=scraper_config.get('drop_detection_tables', ScraperConfig.drop_detection_tables),
                min_confidence_for_notification=scraper_config.get('min_confidence_for_notification', ScraperConfig.min_confidence_for_notification),
                max_games_per_cycle=scraper_config.get('max_games_per_cycle', ScraperConfig.max_games_per_cycle),
                enable_caching=scraper_config.get('enable_caching', ScraperConfig.enable_caching),
                cache_duration=scraper_config.get('cache_duration', ScraperConfig.cache_duration),
                save_extracted_data=scraper_config.get('save_extracted_data', ScraperConfig.save_extracted_data),
                save_drop_data=scraper_config.get('save_drop_data', ScraperConfig.save_drop_data),
                data_retention_hours=scraper_config.get('data_retention_hours', ScraperConfig.data_retention_hours)
            )
            
        except Exception as e:
            self.logger.error(f"Failed to parse scraper config: {e}")
            return ScraperConfig()
    
    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions"""
        event_bus.subscribe("scraper.start_monitoring", self._handle_start_monitoring)
        event_bus.subscribe("scraper.stop_monitoring", self._handle_stop_monitoring)
        event_bus.subscribe("scraper.extract_games", self._handle_extract_games)
        event_bus.subscribe("scraper.detect_drops", self._handle_detect_drops)
        event_bus.subscribe("scraper.get_stats", self._handle_get_stats)
        event_bus.subscribe("config.updated", self._handle_config_update)
    
    async def initialize(self) -> bool:
        """
        Initialize the scraper module
        
        Returns:
            True if initialization successful
        """
        try:
            self.logger.info("Initializing scraper module...")
            
            # Initialize components
            self.extractor = LiveGamesExtractor()
            
            if self.scraper_config.enable_drop_detection:
                self.drop_detector = EnhancedDropDetector()
            
            # Create monitor configuration
            monitor_config = MonitorConfig(
                url=self.scraper_config.monitor_url,
                refresh_interval=self.scraper_config.refresh_interval,
                max_retries=self.scraper_config.max_retries,
                timeout=self.scraper_config.timeout,
                headless=self.scraper_config.headless,
                enable_drop_detection=self.scraper_config.enable_drop_detection,
                drop_detection_tables=self.scraper_config.drop_detection_tables,
                max_games_per_cycle=self.scraper_config.max_games_per_cycle,
                enable_caching=self.scraper_config.enable_caching,
                cache_duration=self.scraper_config.cache_duration,
                notify_on_drops=True,
                min_confidence_for_notification=self.scraper_config.min_confidence_for_notification
            )
            
            # Initialize monitor
            self.monitor = PageMonitor(monitor_config)
            
            # Set monitor callbacks
            self.monitor.set_callbacks(
                games_extracted=self._on_games_extracted,
                drops_detected=self._on_drops_detected,
                error=self._on_monitor_error,
                status_change=self._on_monitor_status_change
            )
            
            self.logger.info("Scraper module initialized successfully")
            
            # Publish initialization event
            init_event = Event(
                name="scraper.initialized",
                data={
                    "timestamp": get_timestamp(),
                    "config": self.scraper_config.__dict__
                },
                priority=EventPriority.NORMAL
            )
            event_bus.publish(init_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scraper module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def start(self) -> bool:
        """
        Start the scraper module
        
        Returns:
            True if started successfully
        """
        try:
            if self.status == ModuleStatus.RUNNING:
                self.logger.warning("Scraper module is already running")
                return True
            
            self.logger.info("Starting scraper module...")
            self.status = ModuleStatus.STARTING
            
            # Start monitoring if monitor is available
            if self.monitor:
                success = await self.monitor.start()
                if not success:
                    raise ScrapingError("Failed to start page monitor", "SCRAPING_001")
            
            self.status = ModuleStatus.RUNNING
            self.logger.info("Scraper module started successfully")
            
            # Publish start event
            start_event = Event(
                name="scraper.started",
                data={"timestamp": get_timestamp()},
                priority=EventPriority.HIGH
            )
            await event_bus.publish_async(start_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scraper module: {e}")
            self.status = ModuleStatus.ERROR
            return False
    
    async def stop(self) -> bool:
        """
        Stop the scraper module
        
        Returns:
            True if stopped successfully
        """
        try:
            if self.status == ModuleStatus.STOPPED:
                self.logger.warning("Scraper module is already stopped")
                return True
            
            self.logger.info("Stopping scraper module...")
            self.status = ModuleStatus.STOPPING
            
            # Stop monitoring
            if self.monitor:
                await self.monitor.stop()
            
            # Clean up data if configured
            await self._cleanup_data()
            
            self.status = ModuleStatus.STOPPED
            self.logger.info("Scraper module stopped")
            
            # Publish stop event
            stop_event = Event(
                name="scraper.stopped",
                data={
                    "timestamp": get_timestamp(),
                    "final_stats": self.get_stats()
                },
                priority=EventPriority.NORMAL
            )
            await event_bus.publish_async(stop_event)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping scraper module: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Health check results
        """
        health = {
            "module": "scraper",
            "status": self.status.value,
            "healthy": True,
            "checks": {},
            "timestamp": get_timestamp()
        }
        
        try:
            # Check components
            health["checks"]["extractor"] = self.extractor is not None
            health["checks"]["drop_detector"] = self.drop_detector is not None if self.scraper_config.enable_drop_detection else True
            health["checks"]["monitor"] = self.monitor is not None
            
            # Check monitor status if available
            if self.monitor:
                monitor_status = self.monitor.get_status()
                health["checks"]["monitor_running"] = monitor_status == MonitorStatus.RUNNING
                health["monitor_status"] = monitor_status.value
            
            # Check recent activity
            health["checks"]["recent_extraction"] = self.stats["last_extraction"] is not None
            
            # Overall health
            health["healthy"] = all(health["checks"].values())
            
            # Add statistics
            health["stats"] = self.get_stats()
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            health["healthy"] = False
            health["error"] = str(e)
        
        return health
    
    async def extract_games_once(self) -> List[GameInfo]:
        """
        Extract games once (manual extraction)
        
        Returns:
            List of extracted games
        """
        try:
            if not self.extractor:
                raise ScrapingError("Extractor not initialized", "SCRAPING_002")
            
            self.logger.info("Performing manual game extraction...")
            
            # Use monitor's driver if available, otherwise create temporary one
            if self.monitor and self.monitor.driver:
                page_source = self.monitor.driver.page_source
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')
                games = await self.extractor.extract_games_async(soup)
            else:
                # Perform standalone extraction
                games = self.extractor.extract_live_games()
            
            # Update statistics
            self.stats["total_extractions"] += 1
            self.stats["total_games_extracted"] += len(games)
            self.stats["last_extraction"] = get_timestamp()
            
            # Calculate average
            if self.stats["total_extractions"] > 0:
                self.stats["average_games_per_extraction"] = self.stats["total_games_extracted"] / self.stats["total_extractions"]
            
            # Store data if configured
            if self.scraper_config.save_extracted_data:
                self.extracted_games.extend(games)
                self._store_extraction_history(games)
            
            # Publish event
            extract_event = Event(
                name="games.extracted_manual",
                data={
                    "timestamp": get_timestamp(),
                    "games_count": len(games),
                    "games": [game.to_dict() for game in games[:5]]  # Limit for performance
                },
                priority=EventPriority.NORMAL
            )
            await event_bus.publish_async(extract_event)
            
            self.logger.info(f"Manual extraction completed: {len(games)} games")
            return games
            
        except Exception as e:
            self.logger.error(f"Manual extraction failed: {e}")
            self.stats["extraction_errors"] += 1
            raise ScrapingError(f"Manual extraction failed: {e}", "SCRAPING_003")
    
    async def detect_drops_once(self, games: Optional[List[GameInfo]] = None) -> List[DropInfo]:
        """
        Detect drops once (manual detection)
        
        Args:
            games: Games to analyze (if None, uses last extracted games)
            
        Returns:
            List of detected drops
        """
        try:
            if not self.drop_detector:
                raise ScrapingError("Drop detector not initialized", "SCRAPING_004")
            
            if games is None:
                games = self.extracted_games[-self.scraper_config.max_games_per_cycle:] if self.extracted_games else []
            
            if not games:
                self.logger.warning("No games available for drop detection")
                return []
            
            self.logger.info(f"Performing manual drop detection on {len(games)} games...")
            
            # Get page source for detection
            if self.monitor and self.monitor.driver:
                page_source = self.monitor.driver.page_source
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page_source, 'html.parser')
                
                all_drops = []
                
                # Detect drops for each table type
                for table_type in self.scraper_config.drop_detection_tables:
                    drops = self.drop_detector.detect_drops(soup, table_type)
                    all_drops.extend(drops)
                
                # Update statistics
                self.stats["total_drops_detected"] += len(all_drops)
                self.stats["last_detection"] = get_timestamp()
                
                # Store data if configured
                if self.scraper_config.save_drop_data:
                    self.detected_drops.extend(all_drops)
                
                # Publish event
                drops_event = Event(
                    name="drops.detected_manual",
                    data={
                        "timestamp": get_timestamp(),
                        "drops_count": len(all_drops),
                        "drops": [drop.to_dict() for drop in all_drops[:5]]  # Limit for performance
                    },
                    priority=EventPriority.NORMAL
                )
                await event_bus.publish_async(drops_event)
                
                self.logger.info(f"Manual drop detection completed: {len(all_drops)} drops")
                return all_drops
            
            else:
                self.logger.warning("No page source available for drop detection")
                return []
            
        except Exception as e:
            self.logger.error(f"Manual drop detection failed: {e}")
            self.stats["detection_errors"] += 1
            raise ScrapingError(f"Manual drop detection failed: {e}", "SCRAPING_005")
    
    def _on_games_extracted(self, games: List[GameInfo]):
        """Handle games extracted callback from monitor
        
        Args:
            games: Extracted games
        """
        try:
            # Update statistics
            self.stats["total_extractions"] += 1
            self.stats["total_games_extracted"] += len(games)
            self.stats["last_extraction"] = get_timestamp()
            
            # Calculate average
            if self.stats["total_extractions"] > 0:
                self.stats["average_games_per_extraction"] = self.stats["total_games_extracted"] / self.stats["total_extractions"]
            
            # Store data if configured
            if self.scraper_config.save_extracted_data:
                self.extracted_games.extend(games)
                self._store_extraction_history(games)
            
            self.logger.debug(f"Processed {len(games)} extracted games")
            
        except Exception as e:
            self.logger.error(f"Error processing extracted games: {e}")
    
    def _on_drops_detected(self, drops: List[DropInfo]):
        """Handle drops detected callback from monitor
        
        Args:
            drops: Detected drops
        """
        try:
            # Update statistics
            self.stats["total_drops_detected"] += len(drops)
            self.stats["last_detection"] = get_timestamp()
            
            # Store data if configured
            if self.scraper_config.save_drop_data:
                self.detected_drops.extend(drops)
            
            self.logger.info(f"Processed {len(drops)} detected drops")
            
        except Exception as e:
            self.logger.error(f"Error processing detected drops: {e}")
    
    def _on_monitor_error(self, error: Exception):
        """Handle monitor error callback
        
        Args:
            error: Monitor error
        """
        self.logger.error(f"Monitor error: {error}")
        
        # Update error statistics
        if "extraction" in str(error).lower():
            self.stats["extraction_errors"] += 1
        elif "detection" in str(error).lower():
            self.stats["detection_errors"] += 1
    
    def _on_monitor_status_change(self, status: MonitorStatus):
        """Handle monitor status change callback
        
        Args:
            status: New monitor status
        """
        self.logger.info(f"Monitor status changed to: {status.value}")
        
        # Update module status based on monitor status
        if status == MonitorStatus.ERROR and self.status == ModuleStatus.RUNNING:
            self.status = ModuleStatus.ERROR
    
    def _store_extraction_history(self, games: List[GameInfo]):
        """Store extraction history
        
        Args:
            games: Games to store
        """
        timestamp = get_timestamp()
        self.extraction_history[timestamp] = games
        
        # Clean old history based on retention policy
        cutoff_time = datetime.now().timestamp() - (self.scraper_config.data_retention_hours * 3600)
        
        self.extraction_history = {
            ts: games for ts, games in self.extraction_history.items()
            if float(ts) > cutoff_time
        }
    
    async def _cleanup_data(self):
        """Clean up stored data"""
        try:
            # Clear in-memory data
            self.extracted_games.clear()
            self.detected_drops.clear()
            self.extraction_history.clear()
            
            self.logger.info("Data cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {e}")
    
    # Event handlers
    async def _handle_start_monitoring(self, data: Dict[str, Any]):
        """Handle start monitoring event"""
        if self.monitor:
            await self.monitor.start()
    
    async def _handle_stop_monitoring(self, data: Dict[str, Any]):
        """Handle stop monitoring event"""
        if self.monitor:
            await self.monitor.stop()
    
    async def _handle_extract_games(self, data: Dict[str, Any]):
        """Handle extract games event"""
        games = await self.extract_games_once()
        
        # Publish response
        response_event = Event(
            name="scraper.games_extracted",
            data={
                "timestamp": get_timestamp(),
                "games_count": len(games),
                "request_id": data.get("request_id")
            },
            priority=EventPriority.NORMAL
        )
        await event_bus.publish_async(response_event)
    
    async def _handle_detect_drops(self, data: Dict[str, Any]):
        """Handle detect drops event"""
        drops = await self.detect_drops_once()
        
        # Publish response
        drops_response_event = Event(
            name="scraper.drops_detected",
            data={
                "timestamp": get_timestamp(),
                "drops_count": len(drops),
                "request_id": data.get("request_id")
            },
            priority=EventPriority.NORMAL
        )
        await event_bus.publish_async(drops_response_event)
    
    async def _handle_get_stats(self, data: Dict[str, Any]):
        """Handle get stats event"""
        stats = self.get_stats()
        
        # Publish response
        stats_response_event = Event(
            name="scraper.stats_response",
            data={
                "timestamp": get_timestamp(),
                "stats": stats,
                "request_id": data.get("request_id")
            },
            priority=EventPriority.NORMAL
        )
        await event_bus.publish_async(stats_response_event)
    
    async def _handle_config_update(self, data: Dict[str, Any]):
        """Handle configuration update event"""
        try:
            new_config = data.get("config", {})
            self.scraper_config = self._parse_config(new_config)
            
            # Update monitor configuration if available
            if self.monitor:
                self.monitor.configure(
                    refresh_interval=self.scraper_config.refresh_interval,
                    max_retries=self.scraper_config.max_retries,
                    timeout=self.scraper_config.timeout,
                    max_games_per_cycle=self.scraper_config.max_games_per_cycle,
                    enable_caching=self.scraper_config.enable_caching,
                    cache_duration=self.scraper_config.cache_duration
                )
            
            self.logger.info("Configuration updated")
            
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics
        
        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()
        
        # Add monitor stats if available
        if self.monitor:
            stats["monitor"] = self.monitor.get_stats()
        
        # Add drop detector stats if available
        if self.drop_detector:
            stats["drop_detector"] = self.drop_detector.get_stats()
        
        # Add data counts
        stats["stored_games_count"] = len(self.extracted_games)
        stats["stored_drops_count"] = len(self.detected_drops)
        stats["history_entries_count"] = len(self.extraction_history)
        
        return stats
    
    def get_recent_games(self, limit: int = 50) -> List[GameInfo]:
        """Get recent extracted games
        
        Args:
            limit: Maximum number of games to return
            
        Returns:
            List of recent games
        """
        return self.extracted_games[-limit:] if self.extracted_games else []
    
    def get_recent_drops(self, limit: int = 50) -> List[DropInfo]:
        """Get recent detected drops
        
        Args:
            limit: Maximum number of drops to return
            
        Returns:
            List of recent drops
        """
        return self.detected_drops[-limit:] if self.detected_drops else []
    
    def get_extraction_history(self, hours: int = 1) -> Dict[str, List[GameInfo]]:
        """Get extraction history for specified hours
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary of timestamp -> games
        """
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        return {
            ts: games for ts, games in self.extraction_history.items()
            if float(ts) > cutoff_time
        }
    
    async def cleanup(self) -> None:
        """Cleanup module resources"""
        try:
            if self.monitor:
                await self.monitor.stop()
            
            if self.extractor:
                await self.extractor.cleanup()
            
            self.logger.info("ScraperModule cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")