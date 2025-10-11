"""Database models for BTC Crowdfund Analytics."""

from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class Invoice(SQLModel, table=True):
    """BTCPay invoice cached in local database."""
    
    id: str = Field(primary_key=True)
    store_id: str
    status: str
    currency: str
    amount: float
    amount_btc: Optional[float] = None
    created_at: datetime
    paid_at: Optional[datetime] = None
    payer_email: Optional[str] = None
    invoice_metadata: Optional[str] = None  # JSON as text


class EventLog(SQLModel, table=True):
    """Log of webhook deliveries."""
    
    id: Optional[int] = Field(default=None, primary_key=True)
    received_at: datetime
    signature: str
    verified: bool
    event_type: str
    payload: str  # JSON as text


class SourceProject(SQLModel, table=True):
    """Normalized crowdfunding projects from Angor or demo."""
    
    id: str = Field(primary_key=True)
    title: str
    amount_target: float
    amount_raised: float
    created_at: datetime
    source: str  # "angor" or "demo"
