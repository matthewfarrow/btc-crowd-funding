"""CITADEL - Bitcoin Crowdfunding Analytics Platform."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print("⚡ CITADEL starting...")
    print("🏰 Bitcoin Crowdfunding Analytics Aggregator")
    print("📊 Data Sources: Geyser Fund + Angor Protocol")
    print("🌐 Fetching from multiple Bitcoin crowdfunding platforms...")
    yield
    # Shutdown
    print("👋 CITADEL shutting down...")


# Create FastAPI app
app = FastAPI(
    title="CITADEL - Bitcoin Crowdfunding Analytics",
    description="Public analytics dashboard for Bitcoin-native crowdfunding protocols",
    version="2.0.0",
    lifespan=lifespan
)

# Mount static files
import os
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers
from app import views
app.include_router(views.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "citadel",
        "data_sources": ["geyser", "angor"]
    }


@app.get("/api/projects")
async def api_projects():
    """API endpoint for fetching all crowdfunding projects from multiple sources."""
    from app.aggregator import fetch_all_projects
    projects = await fetch_all_projects()
    return projects
