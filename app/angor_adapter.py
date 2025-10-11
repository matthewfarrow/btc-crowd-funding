"""Angor adapter with demo fallback."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx


async def get_angor_projects() -> List[Dict[str, Any]]:
    """Fetch Angor projects using multi-strategy approach.
    
    Strategies:
    1. Load demo JSON from repo
    2. Try fetching from hub.angor.io (if CORS allows)
    3. Return normalized records
    
    Returns:
        List of normalized project dictionaries
    """
    # Strategy 1: Load demo data
    projects = load_demo_projects()
    
    # Strategy 2: Try to fetch from Angor hub (optional)
    # Note: This may fail due to CORS in browser, but works server-side
    hub_projects = await fetch_angor_hub()
    if hub_projects:
        projects.extend(hub_projects)
    
    return projects


def load_demo_projects() -> List[Dict[str, Any]]:
    """Load demo projects from angor_demo.json.
    
    Returns:
        List of normalized project dictionaries
    """
    demo_file = os.path.join(os.path.dirname(__file__), "..", "data", "angor_demo.json")
    
    try:
        with open(demo_file, 'r') as f:
            data = json.load(f)
            projects = data.get("projects", [])
            
            # Normalize to our schema
            return [
                {
                    "id": f"angor_demo_{p['id']}",
                    "title": p["title"],
                    "amount_target": p["target_btc"],
                    "amount_raised": p["raised_btc"],
                    "created_at": datetime.fromisoformat(p["created_at"]),
                    "source": "demo"
                }
                for p in projects
            ]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading demo projects: {e}")
        return []


async def fetch_angor_hub() -> List[Dict[str, Any]]:
    """Try to fetch projects from Angor hub.
    
    This is optional and may fail due to CORS or network issues.
    
    Returns:
        List of normalized project dictionaries, or empty list on failure
    """
    hub_url = "https://hub.angor.io/api/projects"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(hub_url)
            response.raise_for_status()
            data = response.json()
            
            # Normalize the response (adjust based on actual API structure)
            projects = []
            for item in data.get("projects", []):
                projects.append({
                    "id": f"angor_{item.get('projectId', '')}",
                    "title": item.get("title", "Unknown Project"),
                    "amount_target": float(item.get("targetAmount", 0)),
                    "amount_raised": float(item.get("amountRaised", 0)),
                    "created_at": parse_angor_date(item.get("createdAt")),
                    "source": "angor"
                })
            
            return projects
            
    except (httpx.HTTPError, json.JSONDecodeError, KeyError) as e:
        print(f"Could not fetch from Angor hub (this is optional): {e}")
        return []


def parse_angor_date(date_str: str) -> datetime:
    """Parse Angor timestamp.
    
    Args:
        date_str: Date string from Angor API
        
    Returns:
        datetime object
    """
    if not date_str:
        return datetime.utcnow()
    
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return datetime.utcnow()
