"""BTCPay Server Greenfield API client."""

import httpx
from typing import Dict, List, Optional, Any
from app.config import config


class BTCPayClient:
    """Simple wrapper for BTCPay Greenfield API calls."""
    
    def __init__(self):
        self.base_url = config.btcpay_base_url
        self.api_key = config.BTCPAY_API_KEY
        self.store_id = config.BTCPAY_STORE_ID
        self.timeout = httpx.Timeout(10.0)
    
    def _build_url(self, path: str) -> str:
        """Build full API URL."""
        return f"{self.base_url}/api/v1/{path}"
    
    def _add_auth_header(self) -> Dict[str, str]:
        """Build Authorization header."""
        return {"Authorization": f"token {self.api_key}"}
    
    async def get_invoices(self, days: int = 30) -> List[Dict[str, Any]]:
        """Fetch invoices for the configured store.
        
        Args:
            days: Number of days to look back (default 30)
            
        Returns:
            List of invoice dictionaries
        """
        if not self.store_id:
            return []
        
        url = self._build_url(f"stores/{self.store_id}/invoices")
        headers = self._add_auth_header()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching invoices: {e}")
            return []
    
    async def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single invoice by ID.
        
        Args:
            invoice_id: The invoice ID
            
        Returns:
            Invoice dictionary or None
        """
        if not self.store_id:
            return None
        
        url = self._build_url(f"stores/{self.store_id}/invoices/{invoice_id}")
        headers = self._add_auth_header()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching invoice {invoice_id}: {e}")
            return None
    
    async def ensure_webhook(self, webhook_url: str) -> bool:
        """Ensure webhook is registered for this store.
        
        Checks existing webhooks and registers one if not found.
        
        Args:
            webhook_url: Full URL for webhook endpoint
            
        Returns:
            True if webhook exists or was created successfully
        """
        if not self.store_id or not config.BTCPAY_WEBHOOK_SECRET:
            return False
        
        # List existing webhooks
        list_url = self._build_url(f"stores/{self.store_id}/webhooks")
        headers = self._add_auth_header()
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Check existing webhooks
                response = await client.get(list_url, headers=headers)
                response.raise_for_status()
                webhooks = response.json()
                
                # Check if our webhook already exists
                for webhook in webhooks:
                    if webhook.get("url") == webhook_url:
                        print(f"Webhook already registered: {webhook_url}")
                        return True
                
                # Create new webhook
                create_data = {
                    "url": webhook_url,
                    "secret": config.BTCPAY_WEBHOOK_SECRET,
                    "automaticRedelivery": True,
                    "events": ["InvoiceSettled", "InvoiceExpired", "InvoiceInvalid"]
                }
                
                response = await client.post(list_url, headers=headers, json=create_data)
                response.raise_for_status()
                print(f"Webhook created successfully: {webhook_url}")
                return True
                
        except httpx.HTTPError as e:
            print(f"Error managing webhooks: {e}")
            return False


# Singleton instance
btcpay_client = BTCPayClient()
