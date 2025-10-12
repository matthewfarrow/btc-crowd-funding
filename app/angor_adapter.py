"""Angor adapter with Indexer API and Nostr integration."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import httpx
import logging

# Import the Nostr client
try:
    from app.angor_nostr_client import get_angor_projects_with_stats, fetch_project_metadata_by_event_id
    NOSTR_AVAILABLE = True
except ImportError:
    NOSTR_AVAILABLE = False
    logging.warning("Nostr SDK not available, will use basic project data")

# Angor Indexer API endpoints
ANGOR_INDEXER_MAINNET = "https://btc.indexer.angor.io/api/query/Angor/projects"
ANGOR_INDEXER_TESTNET = "https://tbtc.indexer.angor.io/api/query/Angor/projects"


async def get_angor_projects() -> List[Dict[str, Any]]:
    """Fetch ALL Angor projects using the indexer API.
    
    Strategies:
    1. Try fetching from Angor Indexer API (PRIMARY - gets ALL projects)
    2. Try fetching real projects from Nostr relays (SECONDARY)
    3. Return empty list if both fail (NO DEMO FALLBACK - we have real data now!)
    
    Returns:
        List of normalized project dictionaries
    """
    logging.info("🚀 get_angor_projects() called - starting data fetch strategies")
    
    # Strategy 1: Try Angor Indexer API first (THIS GETS ALL PROJECTS!)
    indexer_projects = await fetch_from_angor_indexer()
    if indexer_projects:
        logging.info(f"✅ Fetched {len(indexer_projects)} projects from Angor Indexer API")
        return indexer_projects
    
    # Strategy 2: Try to fetch from Nostr
    if NOSTR_AVAILABLE:
        try:
            projects = await get_angor_projects_with_stats()
            if projects:
                logging.info(f"✅ Fetched {len(projects)} real Angor projects from Nostr")
                return projects
        except Exception as e:
            logging.warning(f"Failed to fetch from Nostr: {e}")
    
    # No demo fallback - if both real sources fail, return empty list
    logging.error("❌ Failed to fetch from Angor Indexer AND Nostr - no projects available")
    return []


async def fetch_from_angor_indexer() -> List[Dict[str, Any]]:
    """
    Fetch ALL projects from Angor Indexer API and enrich with Nostr metadata.
    
    This is the PRIMARY data source - it has:
    - Complete list of all crowdfunding projects
    - Investment amounts
    - Investor counts
    - Real blockchain data
    
    Returns:
        List of normalized project dictionaries with enriched names from Nostr
    """
    try:
        print(f"🌐 Fetching projects from Angor Indexer: {ANGOR_INDEXER_TESTNET}", flush=True)
        logging.info(f"Fetching projects from Angor Indexer: {ANGOR_INDEXER_TESTNET}")
        async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout - indexer can be slow
            # Use mainnet indexer
            # Use testnet for now (has more test projects)
            response = await client.get(ANGOR_INDEXER_TESTNET)
            print(f"✅ Indexer response status: {response.status_code}", flush=True)
            logging.info(f"Indexer response status: {response.status_code}")
            response.raise_for_status()
            
            projects_data = response.json()
            logging.info(f"Received {len(projects_data)} projects from indexer")
            
            # Normalize the data
            projects = []
            for item in projects_data:
                try:
                    proj_id = item.get('projectIdentifier', '')
                    nostr_event_id = item.get('nostrEventId', '')
                    
                    # Try to fetch real project name from Nostr
                    project_title = f"Project {proj_id[:12]}..."  # Default
                    
                    if NOSTR_AVAILABLE and nostr_event_id:
                        try:
                            metadata = await fetch_project_metadata_by_event_id(nostr_event_id)
                            if metadata and metadata.get('name'):
                                # Use the project identifier or construct a better name
                                project_title = f"Angor Project {proj_id[:12]}"
                                logging.info(f"✅ Enriched project {proj_id[:12]} with Nostr metadata")
                        except Exception as e:
                            logging.warning(f"Failed to fetch metadata for {proj_id[:12]}: {e}")
                    
                    projects.append({
                        "id": f"angor_{proj_id}",
                        "title": project_title,
                        "amount_target": 0,  # Would need ProjectInfo from Nostr for this
                        "amount_raised": 0,  # Would need /stats endpoint to get investment amounts
                        "created_at": parse_block_time(item.get('createdOnBlock', 0)),
                        "source": "angor_indexer",
                        "founder_key": item.get('founderKey', ''),
                        "nostr_event_id": nostr_event_id,
                        "project_identifier": proj_id,
                        "transaction_id": item.get('trxId', ''),
                        "created_block": item.get('createdOnBlock', 0)
                    })
                except Exception as e:
                    logging.error(f"Error parsing project {item}: {e}")
                    continue
            
            print(f"✅ Successfully parsed {len(projects)} projects (with Nostr enrichment attempts)", flush=True)
            return projects
            
    except httpx.HTTPError as e:
        logging.error(f"HTTP error fetching from Angor indexer: {type(e).__name__}: {e}")
        return []
    except Exception as e:
        logging.error(f"Error fetching from Angor indexer: {type(e).__name__}: {e}")
        return []


def parse_block_time(block_height: int) -> datetime:
    """
    Estimate datetime from Bitcoin block height.
    Bitcoin block time is approximately 10 minutes.
    Genesis block was Jan 3, 2009.
    """
    if block_height == 0:
        return datetime.utcnow()
    
    # Bitcoin genesis block: 2009-01-03
    genesis_time = datetime(2009, 1, 3)
    
    # Approximate: 10 minutes per block
    estimated_time = genesis_time + timedelta(minutes=block_height * 10)
    
    return estimated_time


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
