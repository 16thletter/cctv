"""
Webhook Service for Rails API Integration
Handles event-based callbacks to external Rails backend
"""
import logging
import requests
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from queue import Queue
import threading
import time


class WebhookService:
    """
    Service for sending webhook events to Rails API
    
    Features:
    - Async webhook delivery
    - Retry logic
    - Configurable endpoints
    - Event filtering
    """
    
    def __init__(self, config: Dict[str, Any], logger: Optional[logging.Logger] = None):
        """
        Initialize webhook service
        
        Args:
            config: Configuration dictionary with webhook settings
            logger: Optional logger instance
        """
        self.config = config.get('webhooks', {})
        self.logger = logger or logging.getLogger(__name__)
        
        # Webhook configuration
        self.enabled = self.config.get('enabled', False)
        self.base_url = self.config.get('base_url', '')
        self.timeout = self.config.get('timeout', 5)
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 1.0)
        
        # Event endpoint mapping
        self.endpoints = self.config.get('endpoints', {})
        
        # Async queue for webhook delivery
        self.queue = Queue()
        self.worker_thread = None
        self.running = False
        
        if self.enabled:
            self._start_worker()
            self.logger.info(f"WebhookService initialized - Base URL: {self.base_url}")
        else:
            self.logger.info("WebhookService disabled in configuration")
    
    def _start_worker(self):
        """Start background worker thread for async webhook delivery"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        self.logger.info("Webhook worker thread started")
    
    def _worker_loop(self):
        """Background worker loop for processing webhook queue"""
        while self.running:
            try:
                # Get webhook from queue (with timeout)
                webhook_data = self.queue.get(timeout=1.0)
                self._send_webhook(webhook_data)
                self.queue.task_done()
            except:
                continue
    
    def send_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        camera_id: Optional[str] = None,
        organization_id: Optional[int] = None
    ):
        """
        Send webhook event to Rails API
        
        Args:
            event_type: Type of event (e.g., 'person_in', 'person_out', 'fire_detected')
            data: Event data dictionary
            camera_id: Optional camera identifier
            organization_id: Optional organization identifier
        """
        if not self.enabled:
            return
        
        # Get endpoint for event type
        endpoint = self.endpoints.get(event_type)
        if not endpoint:
            self.logger.debug(f"No webhook endpoint configured for event: {event_type}")
            return
        
        # Build webhook payload
        payload = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            'camera_id': camera_id,
            'organization_id': organization_id,
            'data': data
        }
        
        # Add to queue for async delivery
        self.queue.put({
            'url': f"{self.base_url}{endpoint}",
            'payload': payload,
            'event_type': event_type
        })
    
    def _send_webhook(self, webhook_data: Dict[str, Any]):
        """
        Send webhook HTTP request with retry logic
        
        Args:
            webhook_data: Dictionary with 'url', 'payload', 'event_type'
        """
        url = webhook_data['url']
        payload = webhook_data['payload']
        event_type = webhook_data['event_type']
        
        # Retry logic
        for attempt in range(self.retry_attempts):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    timeout=self.timeout,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code in [200, 201, 202]:
                    self.logger.debug(
                        f"Webhook sent successfully: {event_type} -> {url} "
                        f"(Status: {response.status_code})"
                    )
                    return
                else:
                    self.logger.warning(
                        f"Webhook returned non-2xx status: {event_type} -> {url} "
                        f"(Status: {response.status_code}, Attempt: {attempt + 1})"
                    )
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(
                    f"Webhook request failed: {event_type} -> {url} "
                    f"(Error: {e}, Attempt: {attempt + 1})"
                )
            
            # Wait before retry
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay * (attempt + 1))
        
        # All retries failed
        self.logger.error(
            f"Failed to send webhook after {self.retry_attempts} attempts: "
            f"{event_type} -> {url}"
        )
    
    def send_batch(self, events: List[Dict[str, Any]]):
        """
        Send multiple events in batch
        
        Args:
            events: List of event dictionaries with 'event_type' and 'data' keys
        """
        for event in events:
            self.send_event(
                event_type=event['event_type'],
                data=event.get('data', {}),
                camera_id=event.get('camera_id'),
                organization_id=event.get('organization_id')
            )
    
    def stop(self):
        """Stop webhook service and wait for queue to empty"""
        if self.running:
            self.logger.info("Stopping webhook service...")
            self.running = False
            
            # Wait for queue to empty
            self.queue.join()
            
            if self.worker_thread:
                self.worker_thread.join(timeout=5.0)
            
            self.logger.info("Webhook service stopped")
    
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.queue.qsize()
    
    def flush(self):
        """Flush all pending webhooks (blocking)"""
        self.queue.join()


