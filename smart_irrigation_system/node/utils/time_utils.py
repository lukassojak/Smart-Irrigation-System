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