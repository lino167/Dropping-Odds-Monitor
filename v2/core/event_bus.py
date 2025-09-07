"""Event Bus system for inter-module communication"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid


class EventPriority(Enum):
    """Event priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """Event data structure"""
    name: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate event after initialization"""
        if not self.name:
            raise ValueError("Event name cannot be empty")
        if not isinstance(self.data, dict):
            raise ValueError("Event data must be a dictionary")


class EventBus:
    """Central event bus for system-wide communication"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._async_subscribers: Dict[str, List[Callable]] = {}
        self._event_history: List[Event] = []
        self._max_history_size = 1000
        self._logger = logging.getLogger(__name__)
        self._active_subscriptions: Set[str] = set()
        self._event_stats: Dict[str, int] = {}
        
    def subscribe(self, event_name: str, callback: Callable[[Event], None]) -> str:
        """Subscribe to synchronous events
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Function to call when event is published
            
        Returns:
            Subscription ID for unsubscribing
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
            
        self._subscribers[event_name].append(callback)
        subscription_id = f"{event_name}_{len(self._subscribers[event_name])}"
        self._active_subscriptions.add(subscription_id)
        
        self._logger.debug(f"Subscribed to event '{event_name}' with ID {subscription_id}")
        return subscription_id
    
    def subscribe_async(self, event_name: str, callback: Callable[[Event], Any]) -> str:
        """Subscribe to asynchronous events
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Async function to call when event is published
            
        Returns:
            Subscription ID for unsubscribing
        """
        if event_name not in self._async_subscribers:
            self._async_subscribers[event_name] = []
            
        self._async_subscribers[event_name].append(callback)
        subscription_id = f"{event_name}_async_{len(self._async_subscribers[event_name])}"
        self._active_subscriptions.add(subscription_id)
        
        self._logger.debug(f"Subscribed to async event '{event_name}' with ID {subscription_id}")
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events
        
        Args:
            subscription_id: ID returned from subscribe method
            
        Returns:
            True if successfully unsubscribed, False otherwise
        """
        if subscription_id not in self._active_subscriptions:
            return False
            
        # Parse subscription ID to find event and callback
        parts = subscription_id.split('_')
        if len(parts) < 2:
            return False
            
        event_name = '_'.join(parts[:-1])
        is_async = 'async' in subscription_id
        
        try:
            if is_async and event_name in self._async_subscribers:
                # Remove from async subscribers (simplified - in production, need better tracking)
                self._async_subscribers[event_name].clear()
            elif event_name in self._subscribers:
                # Remove from sync subscribers
                self._subscribers[event_name].clear()
                
            self._active_subscriptions.remove(subscription_id)
            self._logger.debug(f"Unsubscribed from {subscription_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Error unsubscribing {subscription_id}: {e}")
            return False
    
    def publish(self, event: Event) -> None:
        """Publish synchronous event
        
        Args:
            event: Event to publish
        """
        self._add_to_history(event)
        self._update_stats(event.name)
        
        # Call synchronous subscribers
        if event.name in self._subscribers:
            for callback in self._subscribers[event.name]:
                try:
                    callback(event)
                except Exception as e:
                    self._logger.error(f"Error in sync callback for {event.name}: {e}")
        
        self._logger.debug(f"Published sync event: {event.name} (ID: {event.event_id})")
    
    async def publish_async(self, event: Event) -> None:
        """Publish asynchronous event
        
        Args:
            event: Event to publish
        """
        self._add_to_history(event)
        self._update_stats(event.name)
        
        # Call asynchronous subscribers
        if event.name in self._async_subscribers:
            tasks = []
            for callback in self._async_subscribers[event.name]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        tasks.append(callback(event))
                    else:
                        # Handle sync callbacks in async context
                        callback(event)
                except Exception as e:
                    self._logger.error(f"Error in async callback for {event.name}: {e}")
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
        
        self._logger.debug(f"Published async event: {event.name} (ID: {event.event_id})")
    
    def publish_and_wait(self, event: Event, timeout: float = 5.0) -> List[Any]:
        """Publish event and wait for all subscribers to complete
        
        Args:
            event: Event to publish
            timeout: Maximum time to wait for completion
            
        Returns:
            List of results from subscribers
        """
        results = []
        self._add_to_history(event)
        self._update_stats(event.name)
        
        # Execute synchronous subscribers
        if event.name in self._subscribers:
            for callback in self._subscribers[event.name]:
                try:
                    result = callback(event)
                    results.append(result)
                except Exception as e:
                    self._logger.error(f"Error in sync callback for {event.name}: {e}")
                    results.append(e)
        
        return results
    
    def _add_to_history(self, event: Event) -> None:
        """Add event to history with size limit"""
        self._event_history.append(event)
        
        # Maintain history size limit
        if len(self._event_history) > self._max_history_size:
            self._event_history = self._event_history[-self._max_history_size:]
    
    def _update_stats(self, event_name: str) -> None:
        """Update event statistics"""
        if event_name not in self._event_stats:
            self._event_stats[event_name] = 0
        self._event_stats[event_name] += 1
    
    def get_event_history(self, event_name: Optional[str] = None, limit: int = 100) -> List[Event]:
        """Get event history
        
        Args:
            event_name: Filter by specific event name
            limit: Maximum number of events to return
            
        Returns:
            List of historical events
        """
        history = self._event_history
        
        if event_name:
            history = [e for e in history if e.name == event_name]
        
        return history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_events": sum(self._event_stats.values()),
            "event_counts": self._event_stats.copy(),
            "active_subscriptions": len(self._active_subscriptions),
            "sync_subscribers": {k: len(v) for k, v in self._subscribers.items()},
            "async_subscribers": {k: len(v) for k, v in self._async_subscribers.items()},
            "history_size": len(self._event_history)
        }
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history.clear()
        self._logger.info("Event history cleared")
    
    def clear_stats(self) -> None:
        """Clear event statistics"""
        self._event_stats.clear()
        self._logger.info("Event statistics cleared")


# Global event bus instance
_global_event_bus = None


def get_event_bus() -> EventBus:
    """Get global event bus instance
    
    Returns:
        Global EventBus instance
    """
    global _global_event_bus
    if _global_event_bus is None:
        _global_event_bus = EventBus()
    return _global_event_bus


# Create global event bus instance for direct import
event_bus = EventBus()


# Common event names
class Events:
    """Common event names used across the system"""
    
    # Scraper events
    SCRAPER_GAMES_DISCOVERED = "scraper.games.discovered"
    SCRAPER_DROP_DETECTED = "scraper.drop.detected"
    SCRAPER_PAGE_CHANGED = "scraper.page.changed"
    SCRAPER_ERROR = "scraper.error.occurred"
    SCRAPER_STARTED = "scraper.started"
    SCRAPER_STOPPED = "scraper.stopped"
    
    # Analyzer events
    ANALYZER_ANALYSIS_COMPLETED = "analyzer.analysis.completed"
    ANALYZER_PATTERN_FOUND = "analyzer.pattern.found"
    ANALYZER_RISK_CALCULATED = "analyzer.risk.calculated"
    ANALYZER_ERROR = "analyzer.error.occurred"
    
    # Notifier events
    NOTIFIER_ALERT_SENT = "notifier.alert.sent"
    NOTIFIER_NOTIFICATION_FAILED = "notifier.notification.failed"
    NOTIFIER_CONFIG_UPDATED = "notifier.config.updated"
    
    # Database events
    DATABASE_DATA_SAVED = "database.data.saved"
    DATABASE_CONNECTION_ERROR = "database.connection.error"
    DATABASE_MIGRATION_COMPLETED = "database.migration.completed"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_CONFIG_CHANGED = "system.config.changed"
    
    # Cache events
    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_CLEARED = "cache.cleared"