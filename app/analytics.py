"""Analytics functions for Bitcoin crowdfunding projects - CITADEL."""

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Any


SATOSHIS_PER_BTC = 100_000_000


def _sats(value: Any) -> int:
    """Safely convert a numeric value to satoshis (int)."""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str) and value.strip():
        try:
            return int(float(value))
        except ValueError:
            return 0
    return 0


def _parse_datetime(value: Any) -> datetime | None:
    """Accept either datetime objects or ISO strings."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _sat_to_btc(value: int) -> float:
    return value / SATOSHIS_PER_BTC


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
    total_target = sum(_sats(p.get("amount_target", 0)) for p in projects)
    total_raised = sum(_sats(p.get("amount_raised", 0)) for p in projects)
    total_spent = sum(_sats(p.get("amount_spent", 0)) for p in projects)
    total_investors = sum(int(p.get("investor_count", 0) or 0) for p in projects)
    count = len(projects)
    
    # Convert satoshis to BTC for display
    total_raised_btc = _sat_to_btc(total_raised)
    total_spent_btc = _sat_to_btc(total_spent)
    avg_raised = total_raised / count if count > 0 else 0
    avg_raised_btc = _sat_to_btc(avg_raised)
    avg_target = total_target / count if count > 0 else 0
    completion_rate = (total_raised / total_target * 100) if total_target > 0 else 0
    
    # Daily totals grouped by project creation date (UTC)
    daily_totals_accumulator: defaultdict[str, int] = defaultdict(int)
    for project in projects:
        created_at = _parse_datetime(project.get("created_at"))
        if not created_at:
            continue
        day_key = created_at.date().isoformat()
        daily_totals_accumulator[day_key] += _sats(project.get("amount_raised", 0))
    
    daily_totals = [
        {
            "date": day,
            "amount_raised": amount,
            "amount_raised_btc": round(_sat_to_btc(amount), 8)
        }
        for day, amount in sorted(daily_totals_accumulator.items())
    ]
    
    # Build project list with enhanced data
    project_list = []
    for p in projects:
        amount_raised_sat = _sats(p.get("amount_raised", 0))
        amount_raised_btc = _sat_to_btc(amount_raised_sat)
        amount_spent_sat = _sats(p.get("amount_spent", 0))
        amount_spent_btc = _sat_to_btc(amount_spent_sat)
        investor_count = int(p.get("investor_count", 0) or 0)
        amount_target_sat = _sats(p.get("amount_target", 0))
        
        project_list.append({
            "id": p.get("id"),
            "title": p.get("title"),
            "amount_target": amount_target_sat,
            "amount_raised": amount_raised_sat,
            "amount_raised_btc": round(amount_raised_btc, 8),
            "amount_spent": amount_spent_sat,
            "amount_spent_btc": round(amount_spent_btc, 8),
            "investor_count": investor_count,
            "progress_percent": round(amount_raised_sat / amount_target_sat * 100, 2) if amount_target_sat > 0 else 0,
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
        "total_target": total_target,
        "total_target_btc": round(_sat_to_btc(total_target), 8),
        "total_raised": total_raised,
        "total_raised_btc": round(total_raised_btc, 8),
        "total_spent": total_spent,
        "total_spent_btc": round(total_spent_btc, 8),
        "count": count,
        "total_investors": total_investors,
        "average_raised": avg_raised,
        "average_raised_btc": round(avg_raised_btc, 8),
        "average_target": avg_target,
        "average_target_btc": round(_sat_to_btc(avg_target), 8),
        "funding_completion_rate": round(completion_rate, 2),
        "projects": project_list,
        "top_funded": top_funded,
        "most_investors": most_investors,
        "daily_totals": daily_totals
    }
