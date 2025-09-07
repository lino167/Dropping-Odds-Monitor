"""Custom exceptions for the Dropping Odds Analysis System 2.0"""

from typing import Any, Dict, Optional


class DropAnalysisError(Exception):
    """Base exception for all dropping odds analysis errors"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize base exception
        
        Args:
            message: Error message
            error_code: Optional error code for categorization
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def __str__(self) -> str:
        base_msg = self.message
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        
        if self.context:
            context_str = ", ".join([f"{k}={v}" for k, v in self.context.items()])
            base_msg += f" (Context: {context_str})"
        
        return base_msg
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary
        
        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class ScrapingError(DropAnalysisError):
    """Exceptions related to web scraping operations"""
    
    class ErrorCodes:
        PAGE_NOT_FOUND = "SCRAPING_001"
        TIMEOUT = "SCRAPING_002"
        PARSING_FAILED = "SCRAPING_003"
        ELEMENT_NOT_FOUND = "SCRAPING_004"
        INVALID_DATA = "SCRAPING_005"
        RATE_LIMITED = "SCRAPING_006"
        CAPTCHA_DETECTED = "SCRAPING_007"
        CONNECTION_FAILED = "SCRAPING_008"
        BROWSER_ERROR = "SCRAPING_009"
        AUTHENTICATION_FAILED = "SCRAPING_010"


class PageNotFoundError(ScrapingError):
    """Page not found or inaccessible"""
    
    def __init__(self, url: str, status_code: Optional[int] = None):
        context = {"url": url}
        if status_code:
            context["status_code"] = status_code
        
        message = f"Page not found: {url}"
        if status_code:
            message += f" (Status: {status_code})"
        
        super().__init__(message, ScrapingError.ErrorCodes.PAGE_NOT_FOUND, context)


class ScrapingTimeoutError(ScrapingError):
    """Scraping operation timed out"""
    
    def __init__(self, operation: str, timeout_seconds: float):
        context = {"operation": operation, "timeout_seconds": timeout_seconds}
        message = f"Scraping timeout: {operation} (timeout: {timeout_seconds}s)"
        super().__init__(message, ScrapingError.ErrorCodes.TIMEOUT, context)


class ParsingError(ScrapingError):
    """HTML/Data parsing failed"""
    
    def __init__(self, element: str, reason: str):
        context = {"element": element, "reason": reason}
        message = f"Parsing failed for '{element}': {reason}"
        super().__init__(message, ScrapingError.ErrorCodes.PARSING_FAILED, context)


class ElementNotFoundError(ScrapingError):
    """Required HTML element not found"""
    
    def __init__(self, selector: str, page_url: Optional[str] = None):
        context = {"selector": selector}
        if page_url:
            context["page_url"] = page_url
        
        message = f"Element not found: {selector}"
        super().__init__(message, ScrapingError.ErrorCodes.ELEMENT_NOT_FOUND, context)


class RateLimitError(ScrapingError):
    """Rate limit exceeded"""
    
    def __init__(self, retry_after: Optional[int] = None):
        context = {}
        if retry_after:
            context["retry_after_seconds"] = retry_after
        
        message = "Rate limit exceeded"
        if retry_after:
            message += f" (retry after {retry_after}s)"
        
        super().__init__(message, ScrapingError.ErrorCodes.RATE_LIMITED, context)


class ConfigurationError(DropAnalysisError):
    """Configuration-related errors"""
    
    class ErrorCodes:
        MISSING_REQUIRED = "CONFIG_001"
        INVALID_VALUE = "CONFIG_002"
        INVALID_TYPE = "CONFIG_003"
        FILE_NOT_FOUND = "CONFIG_004"
        PARSING_FAILED = "CONFIG_005"
        VALIDATION_FAILED = "CONFIG_006"


class MissingConfigError(ConfigurationError):
    """Required configuration is missing"""
    
    def __init__(self, config_key: str, module: Optional[str] = None):
        context = {"config_key": config_key}
        if module:
            context["module"] = module
        
        message = f"Missing required configuration: {config_key}"
        if module:
            message += f" (module: {module})"
        
        super().__init__(message, ConfigurationError.ErrorCodes.MISSING_REQUIRED, context)


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid"""
    
    def __init__(self, config_key: str, value: Any, reason: str):
        context = {"config_key": config_key, "value": str(value), "reason": reason}
        message = f"Invalid configuration '{config_key}' = '{value}': {reason}"
        super().__init__(message, ConfigurationError.ErrorCodes.INVALID_VALUE, context)


class DatabaseError(DropAnalysisError):
    """Database-related errors"""
    
    class ErrorCodes:
        CONNECTION_FAILED = "DB_001"
        QUERY_FAILED = "DB_002"
        TRANSACTION_FAILED = "DB_003"
        MIGRATION_FAILED = "DB_004"
        CONSTRAINT_VIOLATION = "DB_005"
        TIMEOUT = "DB_006"
        DISK_FULL = "DB_007"
        PERMISSION_DENIED = "DB_008"


class DatabaseConnectionError(DatabaseError):
    """Database connection failed"""
    
    def __init__(self, database_url: str, original_error: Optional[Exception] = None):
        context = {"database_url": database_url}
        if original_error:
            context["original_error"] = str(original_error)
        
        message = f"Database connection failed: {database_url}"
        super().__init__(message, DatabaseError.ErrorCodes.CONNECTION_FAILED, context)


class QueryError(DatabaseError):
    """Database query failed"""
    
    def __init__(self, query: str, error_details: str):
        context = {"query": query, "error_details": error_details}
        message = f"Query failed: {error_details}"
        super().__init__(message, DatabaseError.ErrorCodes.QUERY_FAILED, context)


class NotificationError(DropAnalysisError):
    """Notification-related errors"""
    
    class ErrorCodes:
        SEND_FAILED = "NOTIFY_001"
        INVALID_RECIPIENT = "NOTIFY_002"
        RATE_LIMITED = "NOTIFY_003"
        AUTHENTICATION_FAILED = "NOTIFY_004"
        SERVICE_UNAVAILABLE = "NOTIFY_005"
        MESSAGE_TOO_LARGE = "NOTIFY_006"
        INVALID_FORMAT = "NOTIFY_007"


class NotificationSendError(NotificationError):
    """Failed to send notification"""
    
    def __init__(self, channel: str, recipient: str, reason: str):
        context = {"channel": channel, "recipient": recipient, "reason": reason}
        message = f"Failed to send notification via {channel} to {recipient}: {reason}"
        super().__init__(message, NotificationError.ErrorCodes.SEND_FAILED, context)


class InvalidRecipientError(NotificationError):
    """Invalid notification recipient"""
    
    def __init__(self, recipient: str, channel: str):
        context = {"recipient": recipient, "channel": channel}
        message = f"Invalid recipient '{recipient}' for channel '{channel}'"
        super().__init__(message, NotificationError.ErrorCodes.INVALID_RECIPIENT, context)


class AnalysisError(DropAnalysisError):
    """Analysis-related errors"""
    
    class ErrorCodes:
        INSUFFICIENT_DATA = "ANALYSIS_001"
        CALCULATION_FAILED = "ANALYSIS_002"
        INVALID_PARAMETERS = "ANALYSIS_003"
        MODEL_ERROR = "ANALYSIS_004"
        PATTERN_NOT_FOUND = "ANALYSIS_005"


class InsufficientDataError(AnalysisError):
    """Not enough data for analysis"""
    
    def __init__(self, required_points: int, available_points: int, analysis_type: str):
        context = {
            "required_points": required_points,
            "available_points": available_points,
            "analysis_type": analysis_type
        }
        message = f"Insufficient data for {analysis_type}: need {required_points}, have {available_points}"
        super().__init__(message, AnalysisError.ErrorCodes.INSUFFICIENT_DATA, context)


class CalculationError(AnalysisError):
    """Mathematical calculation failed"""
    
    def __init__(self, calculation_type: str, reason: str, input_data: Optional[Dict] = None):
        context = {"calculation_type": calculation_type, "reason": reason}
        if input_data:
            context["input_data"] = input_data
        
        message = f"Calculation failed for {calculation_type}: {reason}"
        super().__init__(message, AnalysisError.ErrorCodes.CALCULATION_FAILED, context)


class ModuleError(DropAnalysisError):
    """Module-related errors"""
    
    class ErrorCodes:
        INITIALIZATION_FAILED = "MODULE_001"
        START_FAILED = "MODULE_002"
        STOP_FAILED = "MODULE_003"
        DEPENDENCY_MISSING = "MODULE_004"
        INVALID_STATE = "MODULE_005"


class ModuleInitializationError(ModuleError):
    """Module initialization failed"""
    
    def __init__(self, module_name: str, reason: str):
        context = {"module_name": module_name, "reason": reason}
        message = f"Module '{module_name}' initialization failed: {reason}"
        super().__init__(message, ModuleError.ErrorCodes.INITIALIZATION_FAILED, context)


class DependencyError(ModuleError):
    """Module dependency missing or invalid"""
    
    def __init__(self, module_name: str, dependency: str, reason: str):
        context = {"module_name": module_name, "dependency": dependency, "reason": reason}
        message = f"Module '{module_name}' dependency '{dependency}' error: {reason}"
        super().__init__(message, ModuleError.ErrorCodes.DEPENDENCY_MISSING, context)


# Exception mapping for easy lookup
ERROR_CODE_MAP = {
    # Scraping errors
    ScrapingError.ErrorCodes.PAGE_NOT_FOUND: PageNotFoundError,
    ScrapingError.ErrorCodes.TIMEOUT: ScrapingTimeoutError,
    ScrapingError.ErrorCodes.PARSING_FAILED: ParsingError,
    ScrapingError.ErrorCodes.ELEMENT_NOT_FOUND: ElementNotFoundError,
    ScrapingError.ErrorCodes.RATE_LIMITED: RateLimitError,
    
    # Configuration errors
    ConfigurationError.ErrorCodes.MISSING_REQUIRED: MissingConfigError,
    ConfigurationError.ErrorCodes.INVALID_VALUE: InvalidConfigError,
    
    # Database errors
    DatabaseError.ErrorCodes.CONNECTION_FAILED: DatabaseConnectionError,
    DatabaseError.ErrorCodes.QUERY_FAILED: QueryError,
    
    # Notification errors
    NotificationError.ErrorCodes.SEND_FAILED: NotificationSendError,
    NotificationError.ErrorCodes.INVALID_RECIPIENT: InvalidRecipientError,
    
    # Analysis errors
    AnalysisError.ErrorCodes.INSUFFICIENT_DATA: InsufficientDataError,
    AnalysisError.ErrorCodes.CALCULATION_FAILED: CalculationError,
    
    # Module errors
    ModuleError.ErrorCodes.INITIALIZATION_FAILED: ModuleInitializationError,
    ModuleError.ErrorCodes.DEPENDENCY_MISSING: DependencyError,
}


def create_exception_from_code(error_code: str, *args, **kwargs) -> DropAnalysisError:
    """Create exception instance from error code
    
    Args:
        error_code: Error code string
        *args: Exception arguments
        **kwargs: Exception keyword arguments
        
    Returns:
        Exception instance
    """
    exception_class = ERROR_CODE_MAP.get(error_code, DropAnalysisError)
    return exception_class(*args, **kwargs)