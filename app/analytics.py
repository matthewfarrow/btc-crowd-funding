"""Analytics functions for Bitcoin crowdfunding projects - CITADEL."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Any


def aggregate_projects(projects: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate crowdfunding project statistics with rich insights."""
    if not projects:
        return {
            "total_target": 0.0,
            "total_raised": 0.0,
            "total_raised_btc": 0.0,
            "total_spent": 0.0,
            "total_spent_btc": 0.0,
            "count": 0,
            "total_investors": 0,
            "average_raised": 0.0,
            "average_raised_btc": 0.0,
            "average_target": 0.0,
            "funding_completion_rate": 0.0,
            "projects": [],
            "top_funded": [],
            "most_investors": [],
            "daily_totals": []
        }
    
    # Calculate totals (amounts in satoshis)
    total_target = sum(p.get("amount_target", 0) for p in projects)
    total_raised = sum(p.get("amount_raised", 0) for p in projects)
    total_spent = sum(p.get("amount_spent", 0) for p in projects)
    total_investors = sum(p.get("investor_count", 0) for p in projects)
    count = len(projects)
    
    # Convert satoshis to BTC for display
    total_raised_btc = total_raised / 100_000_000
    total_spent_btc = total_spent / 100_000_000
    avg_raised = total_raised / count if count > 0 else 0
    avg_raised_btc = avg_raised / 100_000_000
    avg_target = total_target / count if count > 0 else 0
    completion_rate = (total_raised / total_target * 100) if total_target > 0 else 0
    
    # Build project list with enhanced data
    project_list = []
    for p in projects:
        amount_raised_sat = p.get("amount_raised", 0)
        amount_raised_btc = amount_raised_sat / 100_000_000
        amount_spent_sat = p.get("amount_spent", 0)
        amount_spent_btc = amount_spent_sat / 100_000_000
        investor_count = p.get("investor_count", 0)
        
        project_list.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "amount_target": p.get("amount_target", 0),
            "amount_raised": amount_raised_sat,
            "amount_raised_btc": round(amount_raised_btc, 8),
            "amount_spent": amount_spent_sat,
            "amount_spent_btc": round(amount_spent_btc, 8),
            "investor_count": investor_count,
            "progress_percent": (amount_raised_sat / p.get("amount_target", 1) * 100) if p.get("amount_target", 0) > 0 else 0,
            "created_at": p.get("created_at"),
            "source": p.get("source"),
            "founder_key": p.get("founder_key", ""),
            "project_identifier": p.get("project_identifier", ""),
            "nostr_event_id": p.get("nostr_event_id", "")
        })
    
    # Sort for insights
    top_funded = sorted(project_list, key=lambda x: x["amount_raised"], reverse=True)[:5]
    most_investors = sorted(project_list, key=lambda x: x["investor_count"], reverse=True)[:5]
    
    return {
        "total_target": round(total_target, 8),
        "total_raised": total_raised,
        "total_raised_btc": round(total_raised_btc, 8),
        "total_spent": total_spent,
        "total_spent_btc": round(total_spent_btc, 8),
        "count": count,
        "total_investors": total_investors,
        "average_raised": avg_raised,
        "average_raised_btc": round(avg_raised_btc, 8),
        "average_target": round(avg_target, 8),
        "funding_completion_rate": round(completion_rate, 2),
        "projects": project_list,
        "top_funded": top_funded,
        "most_investors": most_investors,
        "daily_totals": []
    }

