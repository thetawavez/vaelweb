"""
VAEL Core - Time Utility Module
-------------------------------
Provides time-related functions for all VAEL entities.

This module offers current time access, date formatting, time conversions,
and duration calculations with token-efficient implementations.
"""

import datetime
import time
from typing import Dict, Any, Optional, Union, Tuple

# Symbolic time indicators for token efficiency
TIME_SYMBOLS = {
    'now': '⏱️',
    'past': '◀️',
    'future': '▶️',
    'duration': '⌛',
    'morning': '🌅',
    'afternoon': '☀️',
    'evening': '🌆',
    'night': '🌙',
    'sync': '🔄',
    'warning': '⚠️',
    'error': '❌',
}

def current_time(format_str: str = "%A %H:%M") -> str:
    """
    Get the current time in the specified format.
    
    Args:
        format_str: The format string (default: "Day HH:MM")
        
    Returns:
        str: Formatted current time
    """
    return datetime.datetime.now().strftime(format_str)

def current_time_full() -> str:
    """
    Get the current time with date in a detailed format.
    
    Returns:
        str: Full date and time (e.g., "Monday, May 30, 2025 14:30:45")
    """
    return datetime.datetime.now().strftime("%A, %B %d, %Y %H:%M:%S")

def current_timestamp() -> float:
    """
    Get the current Unix timestamp.
    
    Returns:
        float: Unix timestamp (seconds since epoch)
    """
    return time.time()

def format_timestamp(timestamp: float, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a Unix timestamp to a human-readable string.
    
    Args:
        timestamp: Unix timestamp to format
        format_str: The format string
        
    Returns:
        str: Formatted timestamp
    """
    return datetime.datetime.fromtimestamp(timestamp).strftime(format_str)

def get_time_parts() -> Dict[str, int]:
    """
    Get the individual components of the current time.
    
    Returns:
        Dict[str, int]: Dictionary with year, month, day, hour, minute, second
    """
    now = datetime.datetime.now()
    return {
        'year': now.year,
        'month': now.month,
        'day': now.day,
        'hour': now.hour,
        'minute': now.minute,
        'second': now.second,
        'weekday': now.weekday(),  # 0 = Monday, 6 = Sunday
    }

def time_since(timestamp: float) -> Dict[str, Union[float, str]]:
    """
    Calculate the time elapsed since a given timestamp.
    
    Args:
        timestamp: The reference Unix timestamp
        
    Returns:
        Dict[str, Union[float, str]]: Elapsed time in seconds and human-readable format
    """
    elapsed_seconds = time.time() - timestamp
    
    # Convert to human-readable format
    if elapsed_seconds < 60:
        human_readable = f"{int(elapsed_seconds)} seconds ago"
    elif elapsed_seconds < 3600:
        minutes = int(elapsed_seconds / 60)
        human_readable = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif elapsed_seconds < 86400:
        hours = int(elapsed_seconds / 3600)
        human_readable = f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(elapsed_seconds / 86400)
        human_readable = f"{days} day{'s' if days != 1 else ''} ago"
    
    return {
        'seconds': elapsed_seconds,
        'human_readable': human_readable,
        'symbol': TIME_SYMBOLS['past']
    }

def time_until(future_timestamp: float) -> Dict[str, Union[float, str]]:
    """
    Calculate the time remaining until a given timestamp.
    
    Args:
        future_timestamp: The target Unix timestamp
        
    Returns:
        Dict[str, Union[float, str]]: Remaining time in seconds and human-readable format
    """
    remaining_seconds = future_timestamp - time.time()
    
    if remaining_seconds <= 0:
        return {
            'seconds': 0,
            'human_readable': "Already passed",
            'symbol': TIME_SYMBOLS['past']
        }
    
    # Convert to human-readable format
    if remaining_seconds < 60:
        human_readable = f"{int(remaining_seconds)} seconds from now"
    elif remaining_seconds < 3600:
        minutes = int(remaining_seconds / 60)
        human_readable = f"{minutes} minute{'s' if minutes != 1 else ''} from now"
    elif remaining_seconds < 86400:
        hours = int(remaining_seconds / 3600)
        human_readable = f"{hours} hour{'s' if hours != 1 else ''} from now"
    else:
        days = int(remaining_seconds / 86400)
        human_readable = f"{days} day{'s' if days != 1 else ''} from now"
    
    return {
        'seconds': remaining_seconds,
        'human_readable': human_readable,
        'symbol': TIME_SYMBOLS['future']
    }

def get_day_period() -> Dict[str, str]:
    """
    Get the current period of the day with symbolic representation.
    
    Returns:
        Dict[str, str]: Period name and symbol
    """
    hour = datetime.datetime.now().hour
    
    if 5 <= hour < 12:
        return {'period': 'morning', 'symbol': TIME_SYMBOLS['morning']}
    elif 12 <= hour < 17:
        return {'period': 'afternoon', 'symbol': TIME_SYMBOLS['afternoon']}
    elif 17 <= hour < 21:
        return {'period': 'evening', 'symbol': TIME_SYMBOLS['evening']}
    else:
        return {'period': 'night', 'symbol': TIME_SYMBOLS['night']}

def format_duration(seconds: float) -> str:
    """
    Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    
    minutes, seconds = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)}m {int(seconds)}s"
    
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{int(hours)}h {int(minutes)}m"
    
    days, hours = divmod(hours, 24)
    return f"{int(days)}d {int(hours)}h"

def get_system_uptime() -> Dict[str, Union[float, str]]:
    """
    Get the system uptime information.
    
    Returns:
        Dict[str, Union[float, str]]: Uptime in seconds and formatted string
    """
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
        formatted = format_duration(uptime_seconds)
    except:
        # Fallback if /proc/uptime is not available
        uptime_seconds = time.time() - time.monotonic()
        formatted = format_duration(uptime_seconds)
    
    return {
        'seconds': uptime_seconds,
        'formatted': formatted,
        'symbol': TIME_SYMBOLS['duration']
    }

def get_symbolic_time() -> str:
    """
    Get a token-efficient symbolic representation of the current time.
    
    Returns:
        str: Symbolic time representation
    """
    now = datetime.datetime.now()
    day_period = get_day_period()
    
    return f"{day_period['symbol']}{now.strftime('%H:%M')}"

def time_context() -> Dict[str, Any]:
    """
    Get a complete time context for VAEL entities.
    
    Returns:
        Dict[str, Any]: Comprehensive time information
    """
    now = datetime.datetime.now()
    timestamp = time.time()
    
    return {
        'timestamp': timestamp,
        'iso': now.isoformat(),
        'formatted': now.strftime("%Y-%m-%d %H:%M:%S"),
        'readable': now.strftime("%A, %B %d, %Y %H:%M"),
        'day_period': get_day_period(),
        'symbolic': get_symbolic_time(),
        'parts': get_time_parts(),
        'uptime': get_system_uptime()
    }
