"""View routes for the web interface."""

import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session
from app.main import get_session
from app.config import config
from app.btcpay_client import btcpay_client
from app.angor_adapter import get_angor_projects
from app.repo import (
    get_all_invoices,
    get_invoices_by_status,
    get_recent_event_logs,
    upsert_invoice,
    upsert_source_project
)
from app.analytics import aggregate_invoices, aggregate_projects, bucket_by_day
from app.webhook import handle_webhook


router = APIRouter()

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_path)


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    session: Session = Depends(get_session),
    source: str = "btcpay",
    status_filter: str = "all"
):
    """Main dashboard page."""
    # Determine data source
    show_angor = source == "angor" and config.ANGOR_ENABLE
    
    if show_angor:
        # Load Angor projects
        projects = await get_angor_projects()
        
        # Sync to database
        for p in projects:
            upsert_source_project(session, p)
        
        from app.repo import get_all_source_projects
        db_projects = get_all_source_projects(session)
        analytics = aggregate_projects(db_projects)
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "config": config,
                "source": "angor",
                "analytics": analytics,
                "is_demo": config.is_demo_mode
            }
        )
    else:
        # Load BTCPay invoices
        if status_filter and status_filter != "all":
            invoices = get_invoices_by_status(session, status_filter)
        else:
            invoices = get_all_invoices(session)
        
        analytics = aggregate_invoices(invoices)
        daily_data = bucket_by_day(invoices, days=30)
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "config": config,
                "source": "btcpay",
                "analytics": analytics,
                "daily_data": daily_data,
                "status_filter": status_filter,
                "is_demo": config.is_demo_mode
            }
        )


@router.post("/refresh")
async def refresh_data(
    request: Request,
    session: Session = Depends(get_session)
):
    """Refresh invoice data from BTCPay."""
    if not config.is_demo_mode:
        # Fetch recent invoices
        invoices = await btcpay_client.get_invoices(days=30)
        
        # Upsert to database
        for inv_data in invoices:
            # Map BTCPay invoice to our schema
            invoice_dict = {
                "id": inv_data.get("id"),
                "store_id": inv_data.get("storeId", ""),
                "status": inv_data.get("status", "Unknown"),
                "currency": inv_data.get("currency", "USD"),
                "amount": float(inv_data.get("amount", 0)),
                "amount_btc": float(inv_data.get("cryptoPrice", 0)) if inv_data.get("cryptoPrice") else None,
                "created_at": datetime.fromisoformat(inv_data.get("createdTime", datetime.utcnow().isoformat()).replace('Z', '+00:00')),
                "paid_at": None,
                "payer_email": inv_data.get("buyerEmail"),
                "invoice_metadata": str(inv_data.get("metadata", {}))
            }
            
            upsert_invoice(session, invoice_dict)
    
    return RedirectResponse(url="/", status_code=303)


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Settings page."""
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "config": config
        }
    )


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(
    request: Request,
    session: Session = Depends(get_session)
):
    """Webhook logs page."""
    logs = get_recent_event_logs(session, limit=50)
    
    return templates.TemplateResponse(
        "logs.html",
        {
            "request": request,
            "logs": logs,
            "config": config
        }
    )


@router.post("/webhook")
async def webhook_endpoint(
    request: Request,
    session: Session = Depends(get_session)
):
    """BTCPay webhook endpoint."""
    result = await handle_webhook(request, session)
    return result
