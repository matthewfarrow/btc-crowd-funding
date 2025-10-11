"""Analytics functions for aggregating invoice and project data."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any
from app.models import Invoice, SourceProject


def aggregate_invoices(invoices: List[Invoice]) -> Dict[str, Any]:
    """Aggregate invoice statistics.
    
    Args:
        invoices: List of Invoice objects
        
    Returns:
        Dictionary with KPIs and chart data
    """
    if not invoices:
        return {
            "total_raised_btc": 0.0,
            "total_raised_fiat": 0.0,
            "count": 0,
            "average_contribution_btc": 0.0,
            "paid_count": 0,
            "expired_count": 0,
            "pending_count": 0,
            "status_distribution": {},
            "daily_totals": []
        }
    
    # Calculate totals
    total_btc = sum(inv.amount_btc or 0 for inv in invoices)
    total_fiat = sum(inv.amount for inv in invoices if inv.status == "Settled")
    count = len(invoices)
    
    # Status counts
    status_counts = defaultdict(int)
    for inv in invoices:
        status_counts[inv.status] += 1
    
    paid_count = status_counts.get("Settled", 0)
    expired_count = status_counts.get("Expired", 0) + status_counts.get("Invalid", 0)
    pending_count = count - paid_count - expired_count
    
    # Average
    avg_btc = total_btc / count if count > 0 else 0
    
    # Daily bucketing
    daily_buckets = defaultdict(float)
    for inv in invoices:
        if inv.paid_at and inv.status == "Settled":
            day_key = inv.paid_at.strftime("%Y-%m-%d")
            daily_buckets[day_key] += (inv.amount_btc or 0)
    
    # Sort daily data
    daily_totals = [
        {"date": date, "amount_btc": amount}
        for date, amount in sorted(daily_buckets.items())
    ]
    
    return {
        "total_raised_btc": round(total_btc, 8),
        "total_raised_fiat": round(total_fiat, 2),
        "count": count,
        "average_contribution_btc": round(avg_btc, 8),
        "paid_count": paid_count,
        "expired_count": expired_count,
        "pending_count": pending_count,
        "status_distribution": dict(status_counts),
        "daily_totals": daily_totals
    }


def aggregate_projects(projects: List[SourceProject]) -> Dict[str, Any]:
    """Aggregate project statistics.
    
    Args:
        projects: List of SourceProject objects
        
    Returns:
        Dictionary with project KPIs
    """
    if not projects:
        return {
            "total_target": 0.0,
            "total_raised": 0.0,
            "count": 0,
            "average_raised": 0.0,
            "projects": []
        }
    
    total_target = sum(p.amount_target for p in projects)
    total_raised = sum(p.amount_raised for p in projects)
    count = len(projects)
    avg_raised = total_raised / count if count > 0 else 0
    
    # Build project list
    project_list = [
        {
            "id": p.id,
            "title": p.title,
            "target": p.amount_target,
            "raised": p.amount_raised,
            "percentage": (p.amount_raised / p.amount_target * 100) if p.amount_target > 0 else 0,
            "source": p.source
        }
        for p in projects
    ]
    
    return {
        "total_target": round(total_target, 8),
        "total_raised": round(total_raised, 8),
        "count": count,
        "average_raised": round(avg_raised, 8),
        "projects": project_list
    }


def bucket_by_day(invoices: List[Invoice], days: int = 30) -> List[Dict[str, Any]]:
    """Bucket invoices by day for time series charts.
    
    Args:
        invoices: List of Invoice objects
        days: Number of days to include
        
    Returns:
        List of daily bucket dictionaries
    """
    # Initialize buckets
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days)
    
    buckets = {}
    current_date = start_date
    while current_date <= end_date:
        buckets[current_date.isoformat()] = 0.0
        current_date += timedelta(days=1)
    
    # Fill buckets
    for inv in invoices:
        if inv.paid_at and inv.status == "Settled":
            day_key = inv.paid_at.date().isoformat()
            if day_key in buckets:
                buckets[day_key] += (inv.amount_btc or 0)
    
    # Convert to list
    return [
        {"date": date, "amount_btc": amount}
        for date, amount in sorted(buckets.items())
    ]
