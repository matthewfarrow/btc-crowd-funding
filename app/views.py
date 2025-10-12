"""View routes for CITADEL - Bitcoin Crowdfunding Analytics."""

import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.angor_adapter import get_angor_projects
from app.analytics import aggregate_projects


router = APIRouter()

# Setup templates
templates_path = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=templates_path)


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """CITADEL Dashboard - Bitcoin Crowdfunding Analytics.
    
    Shows ALL Angor crowdfunding projects from the Angor Indexer API.
    No authentication, no API keys needed - fully public data!
    """
    # Fetch ALL Angor projects from the indexer
    projects = await get_angor_projects()
    
    # Calculate analytics
    analytics = aggregate_projects(projects)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "analytics": analytics,
            "projects": projects,
            "source": "angor"
        }
    )
