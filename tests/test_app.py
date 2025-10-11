"""Unit tests for BTC Crowdfund Analytics."""

import hmac
import hashlib
import json
from datetime import datetime, timedelta
import pytest
from app.webhook import verify_signature, map_invoice_status, parse_timestamp
from app.analytics import aggregate_invoices, bucket_by_day
from app.models import Invoice


class TestWebhookVerification:
    """Test webhook signature verification."""
    
    def test_verify_signature_valid(self):
        """Test that valid signature passes verification."""
        body = b'{"test": "payload"}'
        secret = "my_webhook_secret"
        
        # Compute expected signature
        expected_sig = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        assert verify_signature(body, expected_sig, secret) is True
    
    def test_verify_signature_invalid(self):
        """Test that invalid signature fails verification."""
        body = b'{"test": "payload"}'
        secret = "my_webhook_secret"
        wrong_signature = "0" * 64  # Wrong signature
        
        assert verify_signature(body, wrong_signature, secret) is False
    
    def test_verify_signature_empty(self):
        """Test that empty signature fails verification."""
        body = b'{"test": "payload"}'
        secret = "my_webhook_secret"
        
        assert verify_signature(body, "", secret) is False
    
    def test_verify_signature_case_insensitive(self):
        """Test that signature comparison is case-insensitive."""
        body = b'{"test": "payload"}'
        secret = "my_webhook_secret"
        
        sig_lower = hmac.new(
            secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest().lower()
        
        sig_upper = sig_lower.upper()
        
        assert verify_signature(body, sig_upper, secret) is True


class TestInvoiceStatusMapping:
    """Test invoice status mapping."""
    
    def test_map_settled_status(self):
        """Test mapping InvoiceSettled event."""
        assert map_invoice_status("InvoiceSettled") == "Settled"
    
    def test_map_expired_status(self):
        """Test mapping InvoiceExpired event."""
        assert map_invoice_status("InvoiceExpired") == "Expired"
    
    def test_map_invalid_status(self):
        """Test mapping InvoiceInvalid event."""
        assert map_invoice_status("InvoiceInvalid") == "Invalid"
    
    def test_map_unknown_status(self):
        """Test mapping unknown event."""
        assert map_invoice_status("UnknownEvent") == "Unknown"


class TestTimestampParsing:
    """Test timestamp parsing."""
    
    def test_parse_iso_timestamp(self):
        """Test parsing ISO format timestamp."""
        timestamp_str = "2024-10-11T12:30:00+00:00"
        result = parse_timestamp(timestamp_str)
        assert isinstance(result, datetime)
        assert result.hour == 12
        assert result.minute == 30
    
    def test_parse_timestamp_with_z(self):
        """Test parsing timestamp with Z suffix."""
        timestamp_str = "2024-10-11T12:30:00Z"
        result = parse_timestamp(timestamp_str)
        assert isinstance(result, datetime)
    
    def test_parse_empty_timestamp(self):
        """Test parsing empty timestamp returns current time."""
        result = parse_timestamp("")
        assert isinstance(result, datetime)
        # Should be close to now
        assert (datetime.utcnow() - result).total_seconds() < 1


class TestAnalytics:
    """Test analytics functions."""
    
    def create_test_invoice(self, invoice_id, status, amount_btc, created_at, paid_at=None):
        """Helper to create test invoice."""
        return Invoice(
            id=invoice_id,
            store_id="test_store",
            status=status,
            currency="USD",
            amount=amount_btc * 50000,  # Rough conversion
            amount_btc=amount_btc,
            created_at=created_at,
            paid_at=paid_at
        )
    
    def test_aggregate_empty_invoices(self):
        """Test aggregating empty invoice list."""
        result = aggregate_invoices([])
        assert result["total_raised_btc"] == 0.0
        assert result["count"] == 0
        assert result["paid_count"] == 0
    
    def test_aggregate_single_invoice(self):
        """Test aggregating single invoice."""
        now = datetime.utcnow()
        invoices = [
            self.create_test_invoice("inv1", "Settled", 0.01, now, now)
        ]
        
        result = aggregate_invoices(invoices)
        assert result["total_raised_btc"] == 0.01
        assert result["count"] == 1
        assert result["paid_count"] == 1
        assert result["expired_count"] == 0
    
    def test_aggregate_multiple_invoices(self):
        """Test aggregating multiple invoices with different statuses."""
        now = datetime.utcnow()
        invoices = [
            self.create_test_invoice("inv1", "Settled", 0.01, now, now),
            self.create_test_invoice("inv2", "Settled", 0.02, now, now),
            self.create_test_invoice("inv3", "Expired", 0.01, now),
            self.create_test_invoice("inv4", "New", 0.01, now)
        ]
        
        result = aggregate_invoices(invoices)
        assert result["total_raised_btc"] == 0.05
        assert result["count"] == 4
        assert result["paid_count"] == 2
        assert result["expired_count"] == 1
        assert result["pending_count"] == 1
    
    def test_bucket_by_day(self):
        """Test bucketing invoices by day."""
        base_date = datetime.utcnow() - timedelta(days=5)
        invoices = [
            self.create_test_invoice(
                f"inv{i}",
                "Settled",
                0.01,
                base_date + timedelta(days=i),
                base_date + timedelta(days=i, hours=1)
            )
            for i in range(5)
        ]
        
        result = bucket_by_day(invoices, days=30)
        assert len(result) == 31  # 30 days + 1
        assert all("date" in item and "amount_btc" in item for item in result)
        
        # Check that some buckets have data
        total_in_buckets = sum(item["amount_btc"] for item in result)
        assert total_in_buckets == 0.05


class TestBTCPayHeaderBuilder:
    """Test BTCPay API header building."""
    
    def test_auth_header_format(self):
        """Test that Authorization header is formatted correctly."""
        from app.btcpay_client import BTCPayClient
        
        client = BTCPayClient()
        # Mock the API key
        client.api_key = "test_api_key_12345"
        
        headers = client._add_auth_header()
        assert "Authorization" in headers
        assert headers["Authorization"] == "token test_api_key_12345"
    
    def test_url_building(self):
        """Test URL construction."""
        from app.btcpay_client import BTCPayClient
        from app.config import config
        
        client = BTCPayClient()
        # Mock the base URL
        client.base_url = "https://mainnet.demo.btcpayserver.org"
        
        url = client._build_url("stores/my_store/invoices")
        assert url == "https://mainnet.demo.btcpayserver.org/api/v1/stores/my_store/invoices"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
