"""Utility functions for the Dropping Odds Analysis System 2.0"""

import os
import re
import logging
import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse
import json
from pathlib import Path


def setup_logging(level: str = "INFO", log_file: Optional[str] = None, 
                 format_string: Optional[str] = None) -> logging.Logger:
    """Setup logging configuration
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Custom format string
        
    Returns:
        Configured logger
    """
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    logger = logging.getLogger("DropAnalysis2.0")
    
    # Add file handler if specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, level.upper()))
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)
    
    logger.info(f"Logging initialized - Level: {level}, File: {log_file}")
    return logger


def get_timestamp(format_string: str = "%Y%m%d_%H%M%S") -> str:
    """Get current timestamp as formatted string
    
    Args:
        format_string: Timestamp format
        
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_string)


def get_iso_timestamp() -> str:
    """Get current timestamp in ISO format
    
    Returns:
        ISO formatted timestamp
    """
    return datetime.now(timezone.utc).isoformat()


def validate_url(url: str) -> bool:
    """Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    # Trim whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    # Truncate if too long
    if len(sanitized) > max_length:
        name, ext = os.path.splitext(sanitized)
        max_name_length = max_length - len(ext)
        sanitized = name[:max_name_length] + ext
    
    return sanitized


def generate_hash(data: Union[str, bytes, Dict], algorithm: str = "md5") -> str:
    """Generate hash for data
    
    Args:
        data: Data to hash
        algorithm: Hash algorithm (md5, sha1, sha256)
        
    Returns:
        Hex digest of hash
    """
    if isinstance(data, dict):
        data = json.dumps(data, sort_keys=True)
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data)
    return hash_obj.hexdigest()


def safe_get(dictionary: Dict, key_path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation
    
    Args:
        dictionary: Dictionary to search
        key_path: Dot-separated key path (e.g., 'level1.level2.key')
        default: Default value if key not found
        
    Returns:
        Value at key path or default
    """
    keys = key_path.split('.')
    value = dictionary
    
    try:
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    except (KeyError, TypeError, AttributeError):
        return default


def safe_set(dictionary: Dict, key_path: str, value: Any) -> None:
    """Safely set nested dictionary value using dot notation
    
    Args:
        dictionary: Dictionary to modify
        key_path: Dot-separated key path
        value: Value to set
    """
    keys = key_path.split('.')
    current = dictionary
    
    # Navigate to parent of target key
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    # Set the final value
    current[keys[-1]] = value


def flatten_dict(dictionary: Dict, parent_key: str = '', separator: str = '.') -> Dict:
    """Flatten nested dictionary
    
    Args:
        dictionary: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Key separator
        
    Returns:
        Flattened dictionary
    """
    items = []
    
    for key, value in dictionary.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))
    
    return dict(items)


def unflatten_dict(dictionary: Dict, separator: str = '.') -> Dict:
    """Unflatten dictionary with dot notation keys
    
    Args:
        dictionary: Flattened dictionary
        separator: Key separator
        
    Returns:
        Nested dictionary
    """
    result = {}
    
    for key, value in dictionary.items():
        safe_set(result, key, value)
    
    return result


def format_bytes(bytes_count: int) -> str:
    """Format bytes count to human readable string
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted string (e.g., '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., '2h 30m 15s')
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {remaining_seconds:.0f}s"
    
    hours = int(minutes // 60)
    remaining_minutes = minutes % 60
    
    if hours < 24:
        return f"{hours}h {remaining_minutes}m"
    
    days = int(hours // 24)
    remaining_hours = hours % 24
    
    return f"{days}d {remaining_hours}h"


def validate_config_schema(config: Dict, schema: Dict) -> List[str]:
    """Validate configuration against schema
    
    Args:
        config: Configuration to validate
        schema: Schema definition
        
    Returns:
        List of validation errors
    """
    errors = []
    
    def validate_value(value, expected_type, path):
        if expected_type == 'string' and not isinstance(value, str):
            errors.append(f"{path}: expected string, got {type(value).__name__}")
        elif expected_type == 'integer' and not isinstance(value, int):
            errors.append(f"{path}: expected integer, got {type(value).__name__}")
        elif expected_type == 'float' and not isinstance(value, (int, float)):
            errors.append(f"{path}: expected number, got {type(value).__name__}")
        elif expected_type == 'boolean' and not isinstance(value, bool):
            errors.append(f"{path}: expected boolean, got {type(value).__name__}")
        elif expected_type == 'list' and not isinstance(value, list):
            errors.append(f"{path}: expected list, got {type(value).__name__}")
        elif expected_type == 'dict' and not isinstance(value, dict):
            errors.append(f"{path}: expected dict, got {type(value).__name__}")
    
    def validate_recursive(config_part, schema_part, path=""):
        if isinstance(schema_part, dict):
            for key, expected in schema_part.items():
                current_path = f"{path}.{key}" if path else key
                
                if key not in config_part:
                    if isinstance(expected, dict) and expected.get('required', False):
                        errors.append(f"{current_path}: required field missing")
                    continue
                
                value = config_part[key]
                
                if isinstance(expected, dict):
                    if 'type' in expected:
                        validate_value(value, expected['type'], current_path)
                    
                    if 'min' in expected and isinstance(value, (int, float)):
                        if value < expected['min']:
                            errors.append(f"{current_path}: value {value} below minimum {expected['min']}")
                    
                    if 'max' in expected and isinstance(value, (int, float)):
                        if value > expected['max']:
                            errors.append(f"{current_path}: value {value} above maximum {expected['max']}")
                    
                    if 'choices' in expected and value not in expected['choices']:
                        errors.append(f"{current_path}: value '{value}' not in allowed choices {expected['choices']}")
                
                else:
                    validate_recursive(value, expected, current_path)
    
    validate_recursive(config, schema)
    return errors


def retry_on_exception(max_retries: int = 3, delay: float = 1.0, 
                      backoff_factor: float = 2.0, 
                      exceptions: tuple = (Exception,)):
    """Decorator for retrying function calls on exceptions
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        break
                    
                    # Log retry attempt
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Attempt {attempt + 1}/{max_retries + 1} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay}s..."
                    )
                    
                    import time
                    time.sleep(current_delay)
                    current_delay *= backoff_factor
            
            # All retries exhausted, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if necessary
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def load_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """Load JSON file with error handling
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Loaded JSON data or default
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return default


def save_json_file(data: Any, file_path: Union[str, Path], 
                  indent: int = 2, ensure_ascii: bool = False) -> bool:
    """Save data to JSON file
    
    Args:
        data: Data to save
        file_path: Path to save file
        indent: JSON indentation
        ensure_ascii: Whether to ensure ASCII encoding
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        path_obj = Path(file_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii, default=str)
        return True
    except (IOError, TypeError) as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate string to maximum length
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_time_string(time_str: str) -> Optional[int]:
    """Parse time string to seconds
    
    Args:
        time_str: Time string (e.g., '1h30m', '45s', '2d')
        
    Returns:
        Time in seconds or None if invalid
    """
    if not time_str:
        return None
    
    # Define time units in seconds
    units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    total_seconds = 0
    current_number = ""
    
    for char in time_str.lower():
        if char.isdigit():
            current_number += char
        elif char in units:
            if current_number:
                total_seconds += int(current_number) * units[char]
                current_number = ""
        else:
            return None  # Invalid character
    
    # Handle case where string ends with a number (assume seconds)
    if current_number:
        total_seconds += int(current_number)
    
    return total_seconds if total_seconds > 0 else None