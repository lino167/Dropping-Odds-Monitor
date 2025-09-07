"""Base module class for all system modules"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
import threading
from enum import Enum

from .event_bus import EventBus, Event, get_event_bus
from .exceptions import DropAnalysisError


class ModuleStatus(Enum):
    """Module status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class BaseModule(ABC):
    """Base class for all system modules
    
    Provides common functionality:
    - Event bus integration
    - Logging setup
    - Configuration management
    - Status tracking
    - Lifecycle management
    """
    
    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize base module
        
        Args:
            name: Module name
            config: Module configuration
        """
        self.name = name
        self.config = config or {}
        self.status = ModuleStatus.STOPPED
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.stopped_at: Optional[datetime] = None
        
        # Setup logging
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Event bus integration
        self.event_bus = get_event_bus()
        self._subscriptions: List[str] = []
        
        # Threading support
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        # Statistics
        self.stats = {
            "events_published": 0,
            "events_received": 0,
            "errors_count": 0,
            "last_activity": None
        }
        
        self.logger.info(f"Module '{self.name}' initialized")
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize module resources
        
        Override this method to implement module-specific initialization
        """
        pass
    
    @abstractmethod
    async def start(self) -> None:
        """Start module operations
        
        Override this method to implement module-specific startup logic
        """
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop module operations
        
        Override this method to implement module-specific shutdown logic
        """
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup module resources
        
        Override this method to implement module-specific cleanup
        """
        pass
    
    async def startup(self) -> None:
        """Complete startup sequence"""
        try:
            self.status = ModuleStatus.STARTING
            self.logger.info(f"Starting module '{self.name}'...")
            
            await self.initialize()
            await self.start()
            
            self.status = ModuleStatus.RUNNING
            self.started_at = datetime.now()
            
            self.logger.info(f"Module '{self.name}' started successfully")
            self.publish_event("module.started", {
                "module_name": self.name,
                "started_at": self.started_at.isoformat()
            })
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.logger.error(f"Failed to start module '{self.name}': {e}")
            self.publish_event("module.error", {
                "module_name": self.name,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise
    
    async def shutdown(self) -> None:
        """Complete shutdown sequence"""
        try:
            self.status = ModuleStatus.STOPPING
            self.logger.info(f"Stopping module '{self.name}'...")
            
            # Signal stop to any running threads
            self._stop_event.set()
            
            await self.stop()
            await self.cleanup()
            
            # Unsubscribe from all events
            self._unsubscribe_all()
            
            self.status = ModuleStatus.STOPPED
            self.stopped_at = datetime.now()
            
            self.logger.info(f"Module '{self.name}' stopped successfully")
            self.publish_event("module.stopped", {
                "module_name": self.name,
                "stopped_at": self.stopped_at.isoformat()
            })
            
        except Exception as e:
            self.status = ModuleStatus.ERROR
            self.logger.error(f"Error stopping module '{self.name}': {e}")
            raise
    
    def subscribe_to_event(self, event_name: str, callback) -> str:
        """Subscribe to an event
        
        Args:
            event_name: Name of the event
            callback: Callback function
            
        Returns:
            Subscription ID
        """
        subscription_id = self.event_bus.subscribe(event_name, self._wrap_callback(callback))
        self._subscriptions.append(subscription_id)
        
        self.logger.debug(f"Subscribed to event '{event_name}'")
        return subscription_id
    
    def subscribe_to_async_event(self, event_name: str, callback) -> str:
        """Subscribe to an async event
        
        Args:
            event_name: Name of the event
            callback: Async callback function
            
        Returns:
            Subscription ID
        """
        subscription_id = self.event_bus.subscribe_async(event_name, self._wrap_async_callback(callback))
        self._subscriptions.append(subscription_id)
        
        self.logger.debug(f"Subscribed to async event '{event_name}'")
        return subscription_id
    
    def publish_event(self, event_name: str, data: Dict[str, Any] = None) -> None:
        """Publish an event
        
        Args:
            event_name: Name of the event
            data: Event data
        """
        event = Event(
            name=event_name,
            data=data or {},
            source=self.name
        )
        
        self.event_bus.publish(event)
        self.stats["events_published"] += 1
        self.stats["last_activity"] = datetime.now().isoformat()
        
        self.logger.debug(f"Published event '{event_name}'")
    
    async def publish_async_event(self, event_name: str, data: Dict[str, Any] = None) -> None:
        """Publish an async event
        
        Args:
            event_name: Name of the event
            data: Event data
        """
        event = Event(
            name=event_name,
            data=data or {},
            source=self.name
        )
        
        await self.event_bus.publish_async(event)
        self.stats["events_published"] += 1
        self.stats["last_activity"] = datetime.now().isoformat()
        
        self.logger.debug(f"Published async event '{event_name}'")
    
    def _wrap_callback(self, callback):
        """Wrap callback to add error handling and statistics"""
        def wrapped_callback(event: Event):
            try:
                self.stats["events_received"] += 1
                self.stats["last_activity"] = datetime.now().isoformat()
                return callback(event)
            except Exception as e:
                self.stats["errors_count"] += 1
                self.logger.error(f"Error in event callback for '{event.name}': {e}")
                raise
        
        return wrapped_callback
    
    def _wrap_async_callback(self, callback):
        """Wrap async callback to add error handling and statistics"""
        async def wrapped_callback(event: Event):
            try:
                self.stats["events_received"] += 1
                self.stats["last_activity"] = datetime.now().isoformat()
                return await callback(event)
            except Exception as e:
                self.stats["errors_count"] += 1
                self.logger.error(f"Error in async event callback for '{event.name}': {e}")
                raise
        
        return wrapped_callback
    
    def _unsubscribe_all(self) -> None:
        """Unsubscribe from all events"""
        for subscription_id in self._subscriptions:
            try:
                self.event_bus.unsubscribe(subscription_id)
            except Exception as e:
                self.logger.warning(f"Error unsubscribing {subscription_id}: {e}")
        
        self._subscriptions.clear()
        self.logger.debug("Unsubscribed from all events")
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        
        self.logger.debug(f"Configuration updated: {key} = {value}")
        self.publish_event("module.config.updated", {
            "module_name": self.name,
            "key": key,
            "value": value
        })
    
    def is_running(self) -> bool:
        """Check if module is running
        
        Returns:
            True if module is running
        """
        return self.status == ModuleStatus.RUNNING
    
    def is_stopped(self) -> bool:
        """Check if module is stopped
        
        Returns:
            True if module is stopped
        """
        return self.status == ModuleStatus.STOPPED
    
    def has_error(self) -> bool:
        """Check if module has error
        
        Returns:
            True if module has error
        """
        return self.status == ModuleStatus.ERROR
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get detailed status information
        
        Returns:
            Status information dictionary
        """
        uptime = None
        if self.started_at and self.status == ModuleStatus.RUNNING:
            uptime = (datetime.now() - self.started_at).total_seconds()
        
        return {
            "name": self.name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "uptime_seconds": uptime,
            "subscriptions_count": len(self._subscriptions),
            "stats": self.stats.copy()
        }
    
    def run_in_thread(self, target_func, *args, **kwargs) -> threading.Thread:
        """Run function in a separate thread
        
        Args:
            target_func: Function to run
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Thread object
        """
        def wrapped_target():
            try:
                target_func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in thread: {e}")
                self.stats["errors_count"] += 1
        
        thread = threading.Thread(target=wrapped_target, daemon=True)
        thread.start()
        return thread
    
    def should_stop(self) -> bool:
        """Check if module should stop
        
        Returns:
            True if stop was requested
        """
        return self._stop_event.is_set()
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')>"