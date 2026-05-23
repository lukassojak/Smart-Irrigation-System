"""Tests for the HistorySyncManager."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from smart_irrigation_system.node.core.history_sync import HistorySyncManager


@pytest.fixture
def temp_sync_queue():
    """Create a temporary file for sync queue."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_file = f.name
    yield temp_file
    # Cleanup
    Path(temp_file).unlink(missing_ok=True)


@pytest.fixture
def sync_manager(temp_sync_queue):
    """Create a HistorySyncManager instance."""
    return HistorySyncManager(
        server_url="http://localhost:8000",
        node_id=1,
        sync_queue_file=temp_sync_queue,
        max_retries=1,
        retry_delay_seconds=0.1,
    )


def test_init_sync_manager(sync_manager):
    """Test synchronization manager initialization."""
    assert sync_manager.node_id == 1
    assert sync_manager.server_url == "http://localhost:8000"
    assert Path(sync_manager.sync_queue_file).exists()


def test_add_record_to_queue(sync_manager):
    """Test adding a record to the sync queue."""
    record = {
        "circuit_id": 1,
        "start_time": "2024-04-30T10:00:00",
        "outcome": "COMPLETED",
        "completed_duration": 300,
        "actual_water_amount": 50.0,
    }

    sync_manager.add_record_to_queue(record)

    # Read queue file
    queue = sync_manager._read_queue()
    assert len(queue) == 1
    assert queue[0]["circuit_id"] == 1


def test_duplicate_record_prevention(sync_manager):
    """Test that duplicate records are not added to queue."""
    record = {
        "circuit_id": 1,
        "start_time": "2024-04-30T10:00:00",
        "outcome": "COMPLETED",
        "completed_duration": 300,
        "actual_water_amount": 50.0,
    }

    sync_manager.add_record_to_queue(record)
    sync_manager.add_record_to_queue(record)  # Add same record again

    queue = sync_manager._read_queue()
    assert len(queue) == 1


def test_multiple_records(sync_manager):
    """Test adding multiple records."""
    records = [
        {
            "circuit_id": 1,
            "start_time": "2024-04-30T10:00:00",
            "outcome": "COMPLETED",
            "completed_duration": 300,
            "actual_water_amount": 50.0,
        },
        {
            "circuit_id": 2,
            "start_time": "2024-04-30T11:00:00",
            "outcome": "SKIPPED",
        },
    ]

    for record in records:
        sync_manager.add_record_to_queue(record)

    queue = sync_manager._read_queue()
    assert len(queue) == 2


@patch('requests.post')
def test_sync_success(mock_post, sync_manager):
    """Test successful sync to server."""
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"uploaded_count": 2, "message": "Uploaded 2 records"}
    mock_post.return_value = mock_response

    # Add some records
    record1 = {
        "circuit_id": 1,
        "start_time": "2024-04-30T10:00:00",
        "outcome": "COMPLETED",
        "completed_duration": 300,
        "actual_water_amount": 50.0,
    }
    record2 = {
        "circuit_id": 2,
        "start_time": "2024-04-30T11:00:00",
        "outcome": "COMPLETED",
        "completed_duration": 250,
        "actual_water_amount": 42.0,
    }

    sync_manager.add_record_to_queue(record1)
    sync_manager.add_record_to_queue(record2)

    # Sync
    result = sync_manager.sync_to_server(blocking=False)
    assert result is True

    # Verify request was made
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert "history/upload" in call_args[0][0]
    assert call_args[1]["json"]["node_id"] == 1
    assert len(call_args[1]["json"]["records"]) == 2

    # Queue should be empty after successful sync
    queue = sync_manager._read_queue()
    assert len(queue) == 0


@patch('requests.post')
def test_sync_failure(mock_post, sync_manager):
    """Test sync failure handling."""
    # Mock failed response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Server error"
    mock_post.return_value = mock_response

    # Add a record
    record = {
        "circuit_id": 1,
        "start_time": "2024-04-30T10:00:00",
        "outcome": "COMPLETED",
    }
    sync_manager.add_record_to_queue(record)

    # Try to sync
    result = sync_manager.sync_to_server(blocking=False)
    assert result is False

    # Record should still be in queue
    queue = sync_manager._read_queue()
    assert len(queue) == 1


@patch('requests.post')
def test_sync_connection_error(mock_post, sync_manager):
    """Test sync with connection error."""
    import requests
    
    # Mock connection error
    mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

    record = {
        "circuit_id": 1,
        "start_time": "2024-04-30T10:00:00",
        "outcome": "COMPLETED",
    }
    sync_manager.add_record_to_queue(record)

    result = sync_manager.sync_to_server(blocking=False)
    assert result is False

    # Record should still be in queue for retry
    queue = sync_manager._read_queue()
    assert len(queue) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
