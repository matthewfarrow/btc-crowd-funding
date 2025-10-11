"""Repository layer for database operations."""

from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select
from app.models import Invoice, EventLog, SourceProject


def upsert_invoice(session: Session, invoice_data: dict) -> Invoice:
    """Insert or update an invoice.
    
    Args:
        session: Database session
        invoice_data: Invoice data dictionary
        
    Returns:
        The created or updated Invoice
    """
    invoice_id = invoice_data.get("id")
    invoice = session.get(Invoice, invoice_id)
    
    if invoice:
        # Update existing
        for key, value in invoice_data.items():
            if hasattr(invoice, key):
                setattr(invoice, key, value)
    else:
        # Create new
        invoice = Invoice(**invoice_data)
        session.add(invoice)
    
    session.commit()
    session.refresh(invoice)
    return invoice


def get_all_invoices(session: Session) -> List[Invoice]:
    """Get all invoices."""
    statement = select(Invoice).order_by(Invoice.created_at.desc())
    return list(session.exec(statement).all())


def get_invoices_by_status(session: Session, status: str) -> List[Invoice]:
    """Get invoices filtered by status."""
    statement = select(Invoice).where(Invoice.status == status).order_by(Invoice.created_at.desc())
    return list(session.exec(statement).all())


def log_webhook_event(
    session: Session,
    signature: str,
    verified: bool,
    event_type: str,
    payload: str
) -> EventLog:
    """Log a webhook delivery.
    
    Args:
        session: Database session
        signature: The BTCPay-Sig header value
        verified: Whether signature verification passed
        event_type: Type of webhook event
        payload: Raw JSON payload
        
    Returns:
        The created EventLog
    """
    event = EventLog(
        received_at=datetime.utcnow(),
        signature=signature,
        verified=verified,
        event_type=event_type,
        payload=payload
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def get_recent_event_logs(session: Session, limit: int = 50) -> List[EventLog]:
    """Get recent webhook event logs."""
    statement = select(EventLog).order_by(EventLog.received_at.desc()).limit(limit)
    return list(session.exec(statement).all())


def upsert_source_project(session: Session, project_data: dict) -> SourceProject:
    """Insert or update a source project.
    
    Args:
        session: Database session
        project_data: Project data dictionary
        
    Returns:
        The created or updated SourceProject
    """
    project_id = project_data.get("id")
    project = session.get(SourceProject, project_id)
    
    if project:
        # Update existing
        for key, value in project_data.items():
            if hasattr(project, key):
                setattr(project, key, value)
    else:
        # Create new
        project = SourceProject(**project_data)
        session.add(project)
    
    session.commit()
    session.refresh(project)
    return project


def get_all_source_projects(session: Session) -> List[SourceProject]:
    """Get all source projects."""
    statement = select(SourceProject).order_by(SourceProject.created_at.desc())
    return list(session.exec(statement).all())
