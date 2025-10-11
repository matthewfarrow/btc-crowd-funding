"""Webhook handler for BTCPay Server events."""

import hmac
import hashlib
import json
from datetime import datetime
from fastapi import Request, HTTPException
from sqlmodel import Session
from app.config import config
from app.models import Invoice
from app.repo import upsert_invoice, log_webhook_event


def verify_signature(body: bytes, signature: str, secret: str) -> bool:
    """Verify BTCPay webhook signature using HMAC-SHA256.
    
    Args:
        body: Raw request body bytes
        signature: BTCPay-Sig header value
        secret: Webhook secret
        
    Returns:
        True if signature is valid
    """
    if not signature or not secret:
        return False
    
    # Compute HMAC
    expected_sig = hmac.new(
        secret.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(signature.lower(), expected_sig.lower())


async def handle_webhook(request: Request, session: Session) -> dict:
    """Handle incoming BTCPay webhook.
    
    Args:
        request: FastAPI request object
        session: Database session
        
    Returns:
        Response dictionary
        
    Raises:
        HTTPException: If signature verification fails
    """
    # Read raw body
    body = await request.body()
    signature = request.headers.get("BTCPay-Sig", "")
    
    # Verify signature
    if not config.BTCPAY_WEBHOOK_SECRET:
        log_webhook_event(
            session,
            signature,
            False,
            "unknown",
            body.decode('utf-8')
        )
        raise HTTPException(status_code=400, detail="Webhook secret not configured")
    
    is_valid = verify_signature(body, signature, config.BTCPAY_WEBHOOK_SECRET)
    
    # Parse payload
    try:
        payload = json.loads(body)
        event_type = payload.get("type", "unknown")
    except json.JSONDecodeError:
        event_type = "unknown"
        payload = {}
    
    # Log the event
    log_webhook_event(
        session,
        signature,
        is_valid,
        event_type,
        body.decode('utf-8')
    )
    
    if not is_valid:
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process invoice event
    if event_type in ["InvoiceSettled", "InvoiceExpired", "InvoiceInvalid"]:
        invoice_data = extract_invoice_from_webhook(payload)
        if invoice_data:
            upsert_invoice(session, invoice_data)
    
    return {"status": "ok", "event": event_type}


def extract_invoice_from_webhook(payload: dict) -> dict:
    """Extract invoice data from webhook payload.
    
    Args:
        payload: Webhook payload dictionary
        
    Returns:
        Invoice data dictionary suitable for upsert
    """
    # BTCPay webhook structure varies, adapt as needed
    invoice_id = payload.get("invoiceId")
    if not invoice_id:
        return {}
    
    # Map webhook fields to our Invoice model
    invoice_data = {
        "id": invoice_id,
        "store_id": payload.get("storeId", ""),
        "status": map_invoice_status(payload.get("type", "")),
        "currency": payload.get("currency", "USD"),
        "amount": float(payload.get("price", 0)),
        "amount_btc": float(payload.get("cryptoPrice", 0)) if payload.get("cryptoPrice") else None,
        "created_at": parse_timestamp(payload.get("createdTime")),
        "paid_at": parse_timestamp(payload.get("paidTime")) if payload.get("type") == "InvoiceSettled" else None,
        "payer_email": payload.get("buyerEmail"),
        "invoice_metadata": json.dumps(payload.get("metadata", {}))
    }
    
    return invoice_data


def map_invoice_status(event_type: str) -> str:
    """Map webhook event type to invoice status.
    
    Args:
        event_type: BTCPay webhook event type
        
    Returns:
        Status string
    """
    mapping = {
        "InvoiceSettled": "Settled",
        "InvoiceExpired": "Expired",
        "InvoiceInvalid": "Invalid"
    }
    return mapping.get(event_type, "Unknown")


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO timestamp string.
    
    Args:
        timestamp_str: ISO format timestamp
        
    Returns:
        datetime object, or current time if parsing fails
    """
    if not timestamp_str:
        return datetime.utcnow()
    
    try:
        # Handle different timestamp formats
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return datetime.utcnow()
