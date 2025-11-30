"""
Unified time utilities for the Smart Irrigation System.

Ensures consistent timestamp handling across:
- CircuitStateManager (persistent snapshot JSON)
- IrrigationCircuit (runtime)
- IrrigationResult logging
"""

from datetime import datetime, timezone


def now(utc: bool = False) -> datetime:
    """Return current datetime without microseconds."""
    if utc:
        return datetime.now(timezone.utc).replace(microsecond=0)
    return datetime.now().replace(microsecond=0)


def now_iso(utc: bool = False) -> str:
    """Return current time as ISO8601 string without microseconds."""
    return now(utc=utc).isoformat()


def to_iso(dt: datetime) -> str:
    """Convert datetime to ISO8601 without microseconds."""
    if dt is None:
        return None
    return dt.replace(microsecond=0).isoformat()


def from_iso(iso_str: str) -> datetime:
    """Convert ISO8601 string to datetime."""
    if iso_str is None:
        return None
    return datetime.fromisoformat(iso_str)

def elapsed_seconds(start: datetime, end: datetime) -> int:
    """
    Calculate elapsed seconds between two datetimes.

    :param start: Start datetime.
    :param end: End datetime.
    :return: Elapsed time in seconds as an integer.
    :raises ValueError: if either start or end is None.
    """
    if start is None or end is None:
        raise ValueError("Both 'start' and 'end' must be valid datetime objects.")
    delta = end - start
    return int(delta.total_seconds())

def is_same_day(dt1: datetime, dt2: datetime) -> bool:
    """
    Check if two datetimes fall on the same calendar day.

    :param dt1: First datetime.
    :param dt2: Second datetime.
    :return: True if both datetimes are on the same day, False otherwise.
    :raises ValueError: if either dt1 or dt2 is None.
    """
    if dt1 is None or dt2 is None:
        raise ValueError("Both 'dt1' and 'dt2' must be valid datetime objects.")
    return dt1.date() == dt2.date()
