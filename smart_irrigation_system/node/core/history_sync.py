"""History synchronization module for syncing irrigation records from node to server.

This module handles:
- Uploading irrigation history records to the server
- Retry logic for failed uploads
- Offline handling (local queueing)
- Deduplication and idempotency
"""

import json
import threading
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from smart_irrigation_system.node.utils.logger import get_logger


class HistorySyncManager:
    """Manages synchronization of irrigation history records to the server."""
    
    def __init__(
        self,
        server_url: str,
        node_id: int,
        sync_queue_file: str,
        max_retries: int = 3,
        retry_delay_seconds: float = 2.0,
    ):
        """
        Initialize the history sync manager.
        
        Args:
            server_url: Base URL of the server (e.g., http://localhost:8000)
            node_id: ID of this node
            sync_queue_file: Path to JSON file for storing unsent records
            max_retries: Maximum number of retry attempts per sync cycle
            retry_delay_seconds: Delay between retries
        """
        self.logger = get_logger("HistorySyncManager")
        self.server_url = server_url.rstrip('/')
        self.node_id = node_id
        self.sync_queue_file = Path(sync_queue_file)
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        
        # Thread safety
        self.queue_lock = threading.Lock()
        self.sync_in_progress = False
        
        # Ensure queue file exists
        self._ensure_queue_file()
        
        self.logger.info(f"HistorySyncManager initialized for node {node_id}")
    
    def _ensure_queue_file(self) -> None:
        """Ensure the sync queue file exists and is valid JSON."""
        if self.sync_queue_file.exists():
            try:
                with open(self.sync_queue_file, 'r') as f:
                    data = json.load(f)
                if not isinstance(data, dict) or 'records' not in data:
                    self._write_queue([])
            except (json.JSONDecodeError, IOError):
                self.logger.warning(f"Queue file corrupted, resetting: {self.sync_queue_file}")
                self._write_queue([])
        else:
            self.sync_queue_file.parent.mkdir(parents=True, exist_ok=True)
            self._write_queue([])
    
    def _read_queue(self) -> List[Dict[str, Any]]:
        """Read the sync queue from file."""
        with self.queue_lock:
            try:
                if not self.sync_queue_file.exists():
                    return []
                with open(self.sync_queue_file, 'r') as f:
                    data = json.load(f)
                return data.get('records', [])
            except Exception as e:
                self.logger.error(f"Failed to read queue file: {e}")
                return []
    
    def _write_queue(self, records: List[Dict[str, Any]]) -> None:
        """Write the sync queue to file."""
        with self.queue_lock:
            try:
                data = {
                    'records': records,
                    'last_updated': datetime.utcnow().isoformat()
                }
                with open(self.sync_queue_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                self.logger.error(f"Failed to write queue file: {e}")
    
    def add_record_to_queue(self, irrigation_record: Dict[str, Any]) -> None:
        """
        Add an irrigation record to the sync queue.
        
        Called after every irrigation attempt (IrrigationResult).
        
        Args:
            irrigation_record: Dictionary with irrigation result data
        """
        try:
            # Ensure minimal required fields
            if 'circuit_id' not in irrigation_record or 'start_time' not in irrigation_record:
                self.logger.error(f"Invalid irrigation record missing required fields: {irrigation_record}")
                return
            
            queue = self._read_queue()
            
            # Check for duplicates (node_id + circuit_id + start_time)
            for existing in queue:
                if (existing.get('circuit_id') == irrigation_record.get('circuit_id') and
                    existing.get('start_time') == irrigation_record.get('start_time')):
                    self.logger.debug(f"Record already in queue, skipping duplicate")
                    return
            
            queue.append(irrigation_record)
            self._write_queue(queue)
            self.logger.debug(f"Added record to sync queue (queue size: {len(queue)})")
            
        except Exception as e:
            self.logger.error(f"Failed to add record to queue: {e}")
    
    def sync_to_server(self, blocking: bool = False) -> bool:
        """
        Attempt to sync queued records to the server.
        
        Args:
            blocking: If True, blocks until sync completes (with retries)
                     If False, tries once and returns
        
        Returns:
            True if sync succeeded or queue empty, False if failed
        """
        if self.sync_in_progress:
            self.logger.debug("Sync already in progress, skipping")
            return False
        
        self.sync_in_progress = True
        try:
            queue = self._read_queue()
            
            if not queue:
                return True
            
            self.logger.info(f"Starting sync: {len(queue)} records to upload")
            
            if blocking:
                return self._sync_with_retries(queue)
            else:
                return self._sync_once(queue)
        
        finally:
            self.sync_in_progress = False
    
    def _sync_with_retries(self, queue: List[Dict[str, Any]]) -> bool:
        """Sync with retry logic."""
        for attempt in range(1, self.max_retries + 1):
            if self._sync_once(queue):
                return True
            
            if attempt < self.max_retries:
                self.logger.info(f"Sync attempt {attempt} failed, retrying in {self.retry_delay_seconds}s...")
                time.sleep(self.retry_delay_seconds)
        
        self.logger.error(f"Sync failed after {self.max_retries} attempts")
        return False
    
    def _sync_once(self, queue: List[Dict[str, Any]]) -> bool:
        """Try to sync once without retries."""
        try:
            url = f"{self.server_url}/api/v1/history/irrigation-history/upload"
            
            payload = {
                "node_id": self.node_id,
                "records": queue
            }
            
            self.logger.debug(f"Uploading {len(queue)} records to {url}")
            
            response = requests.post(
                url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                uploaded = result.get('uploaded_count', 0)
                self.logger.info(f"Sync successful: {result.get('message', 'uploaded')}")
                
                # Clear successfully uploaded records from queue
                if uploaded > 0:
                    remaining = queue[uploaded:]
                    self._write_queue(remaining)
                else:
                    # All were duplicates or failed validation, clear queue anyway
                    self._write_queue([])
                
                return True
            else:
                error_msg = response.text
                self.logger.warning(f"Sync failed with status {response.status_code}: {error_msg}")
                return False
                
        except requests.exceptions.ConnectionError:
            self.logger.warning(f"Connection error during sync: server not reachable at {self.server_url}")
            return False
        except requests.exceptions.Timeout:
            self.logger.warning(f"Timeout during sync to {self.server_url}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during sync: {e}")
            return False
    
    def start_background_sync_daemon(self, interval_seconds: float = 60.0):
        """
        Start a background daemon thread that periodically syncs to the server.
        
        Args:
            interval_seconds: How often to attempt sync (default: 60 seconds)
        """
        def sync_daemon():
            self.logger.info(f"Starting background sync daemon (interval: {interval_seconds}s)")
            while True:
                try:
                    time.sleep(interval_seconds)
                    self.sync_to_server(blocking=False)
                except Exception as e:
                    self.logger.error(f"Error in sync daemon: {e}")
        
        daemon = threading.Thread(target=sync_daemon, daemon=True)
        daemon.start()
        self.logger.debug("Background sync daemon started")
