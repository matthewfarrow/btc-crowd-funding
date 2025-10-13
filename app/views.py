"""View routes for CITADEL - Bitcoin Crowdfunding Analytics."""

import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.aggregator import fetch_all_projects
from app.analytics import aggregate_projects


router = APIRouter()

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_path)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """CITADEL Dashboard - Bitcoin Crowdfunding Analytics.
    
    Shows ALL Bitcoin crowdfunding projects from multiple sources:
    - Geyser Fund (GraphQL API)
    - Angor Protocol (Indexer API)
    """
    projects = await fetch_all_projects()
    
    # Calculate platform distribution
    platform_counts = {}
    platform_stats_dict = {}
    
    for proj in projects:
        platform = proj.get("platform", "unknown")
        platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        if platform not in platform_stats_dict:
            platform_stats_dict[platform] = {
                "name": platform,
                "count": 0,
                "total_raised_sats": 0,
                "total_backers": 0
            }
        
        platform_stats_dict[platform]["count"] += 1
        platform_stats_dict[platform]["total_raised_sats"] += proj.get("raised_sats", 0)
        platform_stats_dict[platform]["total_backers"] += proj.get("backer_count", 0)
    
    # Calculate averages
    platform_stats = []
    for platform, stats in platform_stats_dict.items():
        stats["total_raised_btc"] = stats["total_raised_sats"] / 100_000_000
        stats["avg_raised_btc"] = stats["total_raised_btc"] / stats["count"] if stats["count"] > 0 else 0
        stats["avg_backers"] = int(stats["total_backers"] / stats["count"]) if stats["count"] > 0 else 0
        platform_stats.append(stats)
    
    # Calculate analytics
    analytics = aggregate_projects(projects)
    
    return templates.TemplateResponse(
        "index_analytics.html",
        {
            "request": request,
            "analytics": analytics,
            "projects": projects,
            "platform_counts": platform_counts,
            "platform_stats": platform_stats,
            "is_demo": False
        }
    )
