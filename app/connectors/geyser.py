"""Geyser Fund connector - Bitcoin crowdfunding platform."""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import httpx


logger = logging.getLogger(__name__)

GEYSER_API_URL = "https://api.geyser.fund/graphql"
GEYSER_WEB_URL = "https://geyser.fund"

# Simple in-memory cache with 5-minute TTL
_geyser_cache: Optional[List[Dict[str, Any]]] = None
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_SECONDS = 300  # 5 minutes


async def fetch_geyser_projects() -> List[Dict[str, Any]]:
    """Fetch all public projects from Geyser Fund."""
    global _geyser_cache, _cache_timestamp
    
    # Check cache first
    if _geyser_cache and _cache_timestamp:
        age = (datetime.now() - _cache_timestamp).total_seconds()
        if age < CACHE_TTL_SECONDS:
            logger.info(f"📦 Returning cached Geyser data (age: {age:.1f}s, {len(_geyser_cache)} projects)")
            return _geyser_cache
    
    logger.info("🌊 Fetching projects from Geyser Fund...")
    
    try:
        projects = await fetch_via_graphql()
        logger.info(f"✅ Fetched {len(projects)} projects from Geyser")
        _geyser_cache = projects
        _cache_timestamp = datetime.now()
        return projects
    except Exception as e:
        logger.error(f"Failed to fetch from Geyser: {e}")
        # Return cached data even if expired, better than nothing
        if _geyser_cache:
            logger.info(f"⚠️  Returning expired cache ({len(_geyser_cache)} projects)")
            return _geyser_cache
        return []


async def fetch_via_graphql() -> List[Dict[str, Any]]:
    """Fetch projects using Geyser's GraphQL API."""
    projects = []
    
    async with httpx.AsyncClient(timeout=90.0) as client:
        # Fetch up to 200 projects - balance between completeness and speed
        query = {
            "query": """
            query {
                projectsGet(input: {
                    pagination: { take: 200 },
                    where: {}
                }) {
                    projects {
                        id
                        name
                        title
                        status
                        balance
                        balanceUsdCent
                        fundersCount
                        createdAt
                        owners {
                            user {
                                username
                            }
                        }
                    }
                }
            }
            """
        }
        
        response = await client.post(
            GEYSER_API_URL,
            json=query,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        data = response.json()
        
        if "errors" in data:
            logger.error(f"GraphQL errors: {data['errors']}")
            return []
        
        batch = data.get("data", {}).get("projectsGet", {}).get("projects", [])
        
        for raw_project in batch:
            normalized = normalize_geyser_project(raw_project)
            projects.append(normalized)
        
        logger.info(f"📦 Fetched {len(batch)} Geyser projects")
    
    return projects


def normalize_geyser_project(raw_project: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Geyser project data to CITADEL unified schema."""
    project_name = raw_project.get("name", "")
    project_url = f"{GEYSER_WEB_URL}/project/{project_name}"
    project_id = hashlib.sha256(project_url.encode()).hexdigest()[:16]
    
    raised_sats = raw_project.get("balance", 0)
    
    owners = raw_project.get("owners", [])
    creator_username = ""
    if owners and len(owners) > 0:
        creator_username = owners[0].get("user", {}).get("username", "")
    
    created_timestamp = raw_project.get("createdAt")
    started_at = None
    if created_timestamp:
        try:
            started_at = datetime.fromtimestamp(int(created_timestamp) / 1000)
        except (ValueError, TypeError):
            pass
    
    status_map = {
        "active": "active",
        "inactive": "completed",
        "deleted": "failed"
    }
    status = status_map.get(raw_project.get("status", "active").lower(), "unknown")
    
    return {
        "id": project_id,
        "name": raw_project.get("title", "Untitled Project"),
        "platform": "geyser",
        "url": project_url,
        "creator_display": creator_username,
        "status": status,
        "goal_sats": 0,
        "raised_sats": raised_sats,
        "currency_reported": "BTC",
        "backer_count": raw_project.get("fundersCount", 0),
        "started_at": started_at,
        "project_type": "crowdfund",
    }
