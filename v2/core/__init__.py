"""Core infrastructure for Dropping Odds Analysis System 2.0"""

__version__ = "2.0.0"
__author__ = "Dropping Odds Analysis Team"

from .event_bus import EventBus, Event
from .base_module import BaseModule
from .exceptions import (
    DropAnalysisError,
    ScrapingError,
    ConfigurationError,
    DatabaseError,
    NotificationError
)
from .utils import (
    setup_logging,
    get_timestamp,
    validate_url,
    sanitize_filename
)

__all__ = [
    "EventBus",
    "Event", 
    "BaseModule",
    "DropAnalysisError",
    "ScrapingError",
    "ConfigurationError",
    "DatabaseError",
    "NotificationError",
    "setup_logging",
    "get_timestamp",
    "validate_url",
    "sanitize_filename"
]