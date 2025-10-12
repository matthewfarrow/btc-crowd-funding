"""Database models for CITADEL - Bitcoin Crowdfunding Analytics."""

from datetime import datetime
from sqlmodel import Field, SQLModel


class CrowdfundingProject(SQLModel, table=True):
    """Bitcoin crowdfunding projects from Angor and other protocols."""
    
    id: str = Field(primary_key=True)
    title: str
    amount_target: float
    amount_raised: float
    created_at: datetime
    source: str  # "angor_indexer", "angor_nostr", etc.
    
    # Angor-specific fields
    founder_key: str = ""
    nostr_event_id: str = ""
    project_identifier: str = ""
    transaction_id: str = ""
    created_block: int = 0
