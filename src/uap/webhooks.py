"""Webhook Management System for UAP"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from uuid import uuid4

import httpx

from .logging_config import get_logger
from .retry import retry_async, RetryConfig
from .exceptions import UAPException

logger = get_logger(__name__)


class Webhook:
    """Webhook configuration"""
    
    def __init__(
        self,
        webhook_id: str,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        retry_config: Optional[RetryConfig] = None
    ):
        self.webhook_id = webhook_id
        self.url = url
        self.events = events
        self.secret = secret
        self.retry_config = retry_config or RetryConfig(max_attempts=3)
        self.enabled = True
        self.delivery_count = 0
        self.success_count = 0
        self.failure_count = 0


class WebhookManager:
    """Manages webhook subscriptions and deliveries"""
    
    def __init__(self):
        self._webhooks: Dict[str, Webhook] = {}
        self._client: Optional[httpx.AsyncClient] = None
    
    async def start(self) -> None:
        """Start webhook manager"""
        self._client = httpx.AsyncClient(timeout=30)
        logger.info("Webhook manager started")
    
    async def stop(self) -> None:
        """Stop webhook manager"""
        if self._client:
            await self._client.aclose()
            self._client = None
        logger.info("Webhook manager stopped")
    
    def register(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        webhook_id: Optional[str] = None
    ) -> str:
        """Register a webhook"""
        webhook_id = webhook_id or str(uuid4())
        
        webhook = Webhook(
            webhook_id=webhook_id,
            url=url,
            events=events,
            secret=secret
        )
        
        self._webhooks[webhook_id] = webhook
        
        logger.info("Webhook registered",
                   webhook_id=webhook_id,
                   url=url,
                   events=events)
        
        return webhook_id
    
    def unregister(self, webhook_id: str) -> None:
        """Unregister a webhook"""
        if webhook_id in self._webhooks:
            del self._webhooks[webhook_id]
            logger.info("Webhook unregistered", webhook_id=webhook_id)
    
    async def deliver(self, event_type: str, data: Dict[str, Any]) -> None:
        """Deliver event to all subscribed webhooks"""
        tasks = []
        
        for webhook in self._webhooks.values():
            if webhook.enabled and event_type in webhook.events:
                task = asyncio.create_task(
                    self._deliver_to_webhook(webhook, event_type, data)
                )
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _deliver_to_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Deliver event to a single webhook"""
        if not self._client:
            await self.start()
        
        webhook.delivery_count += 1
        
        payload = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "webhook_id": webhook.webhook_id
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-UAP-Event": event_type,
            "X-UAP-Webhook-ID": webhook.webhook_id,
        }
        
        if webhook.secret:
            import hmac
            import hashlib
            
            signature = hmac.new(
                webhook.secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            
            headers["X-UAP-Signature"] = signature
        
        async def send_webhook():
            response = await self._client.post(
                webhook.url,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response
        
        try:
            await retry_async(send_webhook, config=webhook.retry_config)
            webhook.success_count += 1
            
            logger.info("Webhook delivered",
                       webhook_id=webhook.webhook_id,
                       event_type=event_type,
                       url=webhook.url)
            
        except Exception as e:
            webhook.failure_count += 1
            
            logger.error("Webhook delivery failed",
                        webhook_id=webhook.webhook_id,
                        event_type=event_type,
                        url=webhook.url,
                        error=str(e))
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get webhook by ID"""
        return self._webhooks.get(webhook_id)
    
    def list_webhooks(self) -> List[Webhook]:
        """List all webhooks"""
        return list(self._webhooks.values())
    
    def get_stats(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get webhook statistics"""
        webhook = self._webhooks.get(webhook_id)
        if not webhook:
            return None
        
        return {
            "webhook_id": webhook.webhook_id,
            "url": webhook.url,
            "events": webhook.events,
            "enabled": webhook.enabled,
            "delivery_count": webhook.delivery_count,
            "success_count": webhook.success_count,
            "failure_count": webhook.failure_count,
            "success_rate": webhook.success_count / webhook.delivery_count if webhook.delivery_count > 0 else 0
        }


# Global webhook manager
_webhook_manager: Optional[WebhookManager] = None


def get_webhook_manager() -> WebhookManager:
    """Get global webhook manager"""
    if _webhook_manager is None:
        return WebhookManager()
    return _webhook_manager


def set_webhook_manager(manager: WebhookManager) -> None:
    """Set global webhook manager"""
    global _webhook_manager
    _webhook_manager = manager

