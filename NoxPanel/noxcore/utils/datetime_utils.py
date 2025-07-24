"""
Enhanced DateTime Utilities for NoxPanel
Provides timezone-aware datetime operations and standardized formatting
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Union, Any
import calendar
import time

logger = logging.getLogger(__name__)


class DateTimeUtils:
    """Centralized datetime utilities with timezone awareness and comprehensive formatting."""

    # Standard format strings
    ISO_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
    DISPLAY_FORMAT = "%Y-%m-%d %H:%M:%S UTC"
    DATE_FORMAT = "%Y-%m-%d"
    TIME_FORMAT = "%H:%M:%S"
    FILENAME_FORMAT = "%Y%m%d_%H%M%S"
    
    @staticmethod
    def utc_now() -> datetime:
        """Get current UTC datetime with timezone awareness.
        
        Returns:
            Current UTC datetime
        """
        return datetime.now(timezone.utc)
    
    @staticmethod
    def utc_timestamp() -> float:
        """Get current UTC timestamp.
        
        Returns:
            Current UTC timestamp as float
        """
        return utc_now().timestamp()
    
    @staticmethod
    def from_timestamp(timestamp: Union[int, float], tz: Optional[timezone] = None) -> datetime:
        """Convert timestamp to timezone-aware datetime.
        
        Args:
            timestamp: Unix timestamp
            tz: Target timezone (defaults to UTC)
            
        Returns:
            Timezone-aware datetime object
        """
        if tz is None:
            tz = timezone.utc
        return datetime.fromtimestamp(timestamp, tz=tz)
    
    @staticmethod
    def to_timestamp(dt: datetime) -> float:
        """Convert datetime to Unix timestamp.
        
        Args:
            dt: Datetime object
            
        Returns:
            Unix timestamp as float
        """
        return dt.timestamp()
    
    @staticmethod
    def format_iso(dt: Optional[datetime] = None) -> str:
        """Format datetime as ISO string with UTC timezone.
        
        Args:
            dt: Datetime to format (defaults to current UTC time)
            
        Returns:
            ISO formatted datetime string
        """
        if dt is None:
            dt = DateTimeUtils.utc_now()
        
        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)
        
        return dt.strftime(DateTimeUtils.ISO_FORMAT)
    
    @staticmethod
    def format_display(dt: Optional[datetime] = None) -> str:
        """Format datetime for display purposes.
        
        Args:
            dt: Datetime to format (defaults to current UTC time)
            
        Returns:
            Display-formatted datetime string
        """
        if dt is None:
            dt = DateTimeUtils.utc_now()
        
        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)
        
        return dt.strftime(DateTimeUtils.DISPLAY_FORMAT)
    
    @staticmethod
    def format_filename(dt: Optional[datetime] = None) -> str:
        """Format datetime for use in filenames.
        
        Args:
            dt: Datetime to format (defaults to current UTC time)
            
        Returns:
            Filename-safe datetime string
        """
        if dt is None:
            dt = DateTimeUtils.utc_now()
        
        # Ensure UTC timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        elif dt.tzinfo != timezone.utc:
            dt = dt.astimezone(timezone.utc)
        
        return dt.strftime(DateTimeUtils.FILENAME_FORMAT)
    
    @staticmethod
    def parse_iso(iso_string: str) -> datetime:
        """Parse ISO datetime string to timezone-aware datetime.
        
        Args:
            iso_string: ISO formatted datetime string
            
        Returns:
            Timezone-aware datetime object
            
        Raises:
            ValueError: If string format is invalid
        """
        try:
            # Handle various ISO formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(iso_string, fmt)
                    # Ensure timezone awareness
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except ValueError:
                    continue
            
            # Try fromisoformat as fallback
            dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
            
        except Exception as e:
            logger.error(f"Failed to parse datetime string '{iso_string}': {e}")
            raise ValueError(f"Invalid datetime format: {iso_string}")
    
    @staticmethod
    def ensure_timezone_aware(dt: datetime, default_tz: timezone = timezone.utc) -> datetime:
        """Ensure datetime object is timezone-aware.
        
        Args:
            dt: Datetime object
            default_tz: Default timezone if none specified
            
        Returns:
            Timezone-aware datetime object
        """
        if dt.tzinfo is None:
            return dt.replace(tzinfo=default_tz)
        return dt
    
    @staticmethod
    def time_ago(dt: datetime, precision: int = 2) -> str:
        """Get human-readable time difference from now.
        
        Args:
            dt: Target datetime
            precision: Number of units to show (e.g., "2 hours, 30 minutes")
            
        Returns:
            Human-readable time difference string
        """
        try:
            now = DateTimeUtils.utc_now()
            dt = DateTimeUtils.ensure_timezone_aware(dt)
            
            if dt > now:
                delta = dt - now
                prefix = "in "
                suffix = ""
            else:
                delta = now - dt
                prefix = ""
                suffix = " ago"
            
            return prefix + DateTimeUtils._format_timedelta(delta, precision) + suffix
        except Exception as e:
            logger.error(f"Failed to calculate time ago for {dt}: {e}")
            return "unknown time"
    
    @staticmethod
    def _format_timedelta(delta: timedelta, precision: int = 2) -> str:
        """Format timedelta as human-readable string.
        
        Args:
            delta: Timedelta object
            precision: Number of units to show
            
        Returns:
            Human-readable timedelta string
        """
        total_seconds = int(delta.total_seconds())
        
        if total_seconds == 0:
            return "just now"
        
        units = [
            ('year', 31536000),
            ('month', 2592000),
            ('week', 604800),
            ('day', 86400),
            ('hour', 3600),
            ('minute', 60),
            ('second', 1)
        ]
        
        parts = []
        for unit_name, unit_seconds in units:
            if total_seconds >= unit_seconds:
                count = total_seconds // unit_seconds
                total_seconds %= unit_seconds
                
                if count == 1:
                    parts.append(f"1 {unit_name}")
                else:
                    parts.append(f"{count} {unit_name}s")
                
                if len(parts) >= precision:
                    break
        
        if not parts:
            return "less than a second"
        
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return ", ".join(parts[:-1]) + f", and {parts[-1]}"
    
    @staticmethod
    def is_recent(dt: datetime, threshold_minutes: int = 5) -> bool:
        """Check if datetime is within recent threshold.
        
        Args:
            dt: Datetime to check
            threshold_minutes: Threshold in minutes
            
        Returns:
            True if datetime is recent, False otherwise
        """
        try:
            now = DateTimeUtils.utc_now()
            dt = DateTimeUtils.ensure_timezone_aware(dt)
            delta = now - dt
            return delta.total_seconds() <= (threshold_minutes * 60)
        except Exception:
            return False
    
    @staticmethod
    def business_hours_offset(hours: int = 8) -> datetime:
        """Get datetime for business hours from now.
        
        Args:
            hours: Business hours to add
            
        Returns:
            Datetime offset by business hours
        """
        return DateTimeUtils.utc_now() + timedelta(hours=hours)
    
    @staticmethod
    def start_of_day(dt: Optional[datetime] = None) -> datetime:
        """Get start of day (00:00:00) for given datetime.
        
        Args:
            dt: Target datetime (defaults to current UTC time)
            
        Returns:
            Start of day datetime
        """
        if dt is None:
            dt = DateTimeUtils.utc_now()
        
        dt = DateTimeUtils.ensure_timezone_aware(dt)
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    
    @staticmethod
    def end_of_day(dt: Optional[datetime] = None) -> datetime:
        """Get end of day (23:59:59.999999) for given datetime.
        
        Args:
            dt: Target datetime (defaults to current UTC time)
            
        Returns:
            End of day datetime
        """
        if dt is None:
            dt = DateTimeUtils.utc_now()
        
        dt = DateTimeUtils.ensure_timezone_aware(dt)
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


# Convenience functions for backward compatibility and ease of use
def utc_now() -> datetime:
    """Get current UTC datetime - convenience function."""
    return DateTimeUtils.utc_now()


def format_iso(dt: Optional[datetime] = None) -> str:
    """Format datetime as ISO string - convenience function."""
    return DateTimeUtils.format_iso(dt)


def parse_iso(iso_string: str) -> datetime:
    """Parse ISO datetime string - convenience function."""
    return DateTimeUtils.parse_iso(iso_string)


def time_ago(dt: datetime) -> str:
    """Get human-readable time ago - convenience function."""
    return DateTimeUtils.time_ago(dt)


# Export main utilities
__all__ = [
    'DateTimeUtils',
    'utc_now', 
    'format_iso', 
    'parse_iso', 
    'time_ago'
]
