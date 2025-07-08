import pytest
from unittest.mock import MagicMock, patch
from smart_irrigation_system.drippers import Drippers


def test_add_dripper_increases_total_consumption():
    drippers = Drippers()
    initial_consumption = drippers.get_consumption()
    
    drippers.add_dripper(5)
    assert drippers.get_consumption() == initial_consumption + 5

    drippers.add_dripper(10)
    assert drippers.get_consumption() == initial_consumption + 15

    drippers.add_dripper(42)
    assert drippers.get_consumption() == initial_consumption + 57


def test_remove_dripper_decreases_total_consumption():
    drippers = Drippers()
    drippers.add_dripper(5)
    drippers.add_dripper(10)
    initial_consumption = drippers.get_consumption()
    
    drippers.remove_dripper(5)
    assert drippers.get_consumption() == initial_consumption - 5

    drippers.remove_dripper(10)
    assert drippers.get_consumption() == initial_consumption - 15


def test_remove_dripper_does_not_decrease_below_zero():
    drippers = Drippers()
    drippers.add_dripper(5)
    initial_consumption = drippers.get_consumption()
    
    drippers.remove_dripper(5)
    assert drippers.get_consumption() == initial_consumption - 5
    
    # Attempt to remove again should not decrease below zero
    drippers.remove_dripper(5)
    assert drippers.get_consumption() == 0

def test_get_minimum_dripper_flow():
    drippers = Drippers()
    assert drippers.get_minimum_dripper_flow() == 0  # No drippers added yet

    drippers.add_dripper(10)
    assert drippers.get_minimum_dripper_flow() == 10

    drippers.add_dripper(5)
    assert drippers.get_minimum_dripper_flow() == 5

    drippers.add_dripper(15)
    assert drippers.get_minimum_dripper_flow() == 5  # Minimum should still be 5

    drippers.remove_dripper(5)
    assert drippers.get_minimum_dripper_flow() == 10  # Now minimum is 10

    drippers.add_dripper(2)
    assert drippers.get_minimum_dripper_flow() == 2  # New minimum should be 2

    drippers.remove_dripper(2)
    assert drippers.get_minimum_dripper_flow() == 10  # Back to previous minimum of 10


def test_add_remove_dripper_changes_count():
    drippers = Drippers()
    
    # Adding a dripper with 5 liters/hour
    drippers.add_dripper(5)
    assert drippers.drippers[5] == 1
    
    # Adding another dripper with the same flow rate
    drippers.add_dripper(5)
    assert drippers.drippers[5] == 2
    
    # Adding a different flow rate
    drippers.add_dripper(10)
    assert drippers.drippers[10] == 1
    
    # Adding another dripper with the same flow rate
    drippers.add_dripper(10)
    assert drippers.drippers[10] == 2

    # Removing one dripper with 5 liters/hour
    drippers.remove_dripper(5)
    assert drippers.drippers[5] == 1

    # Removing the last dripper with 5 liters/hour
    drippers.remove_dripper(5)
    assert 5 not in drippers.drippers  # Should be removed completely
