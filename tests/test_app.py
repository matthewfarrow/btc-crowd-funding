"""Tests for the CITADEL Angor-only analytics stack."""

from datetime import datetime, timedelta

from app.analytics import aggregate_projects
from app.angor_adapter import load_demo_projects, parse_block_time


def _project(amount_target_sat: int, amount_raised_sat: int, created_at: datetime, investors: int = 0):
    return {
        "id": f"test_{created_at.isoformat()}",
        "title": "Test Project",
        "amount_target": amount_target_sat,
        "amount_raised": amount_raised_sat,
        "amount_spent": 0,
        "investor_count": investors,
        "created_at": created_at,
        "source": "unit-test",
    }


def test_aggregate_projects_empty():
    result = aggregate_projects([])
    assert result["count"] == 0
    assert result["total_raised"] == 0
    assert result["total_raised_btc"] == 0.0
    assert result["projects"] == []


def test_aggregate_projects_totals_and_progress():
    created = datetime(2024, 1, 1)
    projects = [
        _project(200_000_000, 150_000_000, created, investors=10),
        _project(100_000_000, 75_000_000, created + timedelta(days=1), investors=5),
    ]
    
    result = aggregate_projects(projects)
    
    assert result["count"] == 2
    # Totals should be expressed in satoshis
    assert result["total_raised"] == 225_000_000
    assert result["total_raised_btc"] == 2.25
    assert result["total_investors"] == 15
    assert result["funding_completion_rate"] == 75.0
    
    # Project level calculations
    first = result["projects"][0]
    assert first["amount_raised_btc"] == 1.5
    assert first["progress_percent"] == 75.0


def test_aggregate_projects_daily_totals():
    base = datetime(2024, 5, 1)
    projects = [
        _project(100_000_000, 50_000_000, base),
        _project(150_000_000, 125_000_000, base),
        _project(80_000_000, 20_000_000, base + timedelta(days=1)),
    ]
    
    result = aggregate_projects(projects)
    daily_totals = {item["date"]: item["amount_raised"] for item in result["daily_totals"]}
    
    assert len(daily_totals) == 2
    assert daily_totals[base.date().isoformat()] == 175_000_000
    assert daily_totals[(base + timedelta(days=1)).date().isoformat()] == 20_000_000


def test_load_demo_projects_converts_units():
    projects = load_demo_projects()
    assert projects, "Demo projects should load from bundled JSON"
    
    sample = projects[0]
    # The JSON file uses BTC units so ensure we converted to satoshis
    assert isinstance(sample["amount_target"], int)
    assert isinstance(sample["amount_raised"], int)
    assert sample["source"] == "demo"


def test_parse_block_time_estimation():
    approximate = parse_block_time(840_000)
    assert isinstance(approximate, datetime)
    # Block timestamps should be after genesis but before far future
    assert approximate.year >= 2009
    assert approximate.year <= datetime.utcnow().year + 1
