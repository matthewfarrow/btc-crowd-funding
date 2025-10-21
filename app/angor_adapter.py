"""Angor adapter with Indexer API and Nostr integration."""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
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

# Simple in-memory cache with 5-minute TTL
_angor_cache: Optional[Dict[str, Any]] = None
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_SECONDS = 300  # 5 minutes


async def get_angor_projects() -> List[Dict[str, Any]]:
    """Fetch Angor projects using the best available strategy.
    
    The strategies are attempted in order:
    1. Angor Indexer API (live blockchain-backed data)
    2. Nostr relays (requires nostr-sdk to be installed)
    3. Local demo data (offline fallback so the dashboard still works)
    """
    global _angor_cache, _cache_timestamp
    
    # Check cache first
    if _angor_cache and _cache_timestamp:
        age = (datetime.now() - _cache_timestamp).total_seconds()
        if age < CACHE_TTL_SECONDS:
            logging.info(f"� Returning cached Angor data (age: {age:.1f}s)")
            return _angor_cache
    
    logging.info("�🚀 get_angor_projects() called - starting data fetch strategies")
    
    # Strategy 1: Angor Indexer API
    indexer_projects = await fetch_from_angor_indexer()
    if indexer_projects:
        logging.info("✅ Returning projects from Angor Indexer API")
        _angor_cache = indexer_projects
        _cache_timestamp = datetime.now()
        return indexer_projects
    
    # Strategy 2: Nostr relays (optional)
    if NOSTR_AVAILABLE:
        try:
            projects = await get_angor_projects_with_stats()
            if projects:
                logging.info("✅ Returning projects from Nostr relays")
                _angor_cache = projects
                _cache_timestamp = datetime.now()
                return projects
        except Exception as exc:
            logging.warning("Failed to fetch from Nostr relays: %s", exc)
    
    # Strategy 3: Demo data fallback
    demo_projects = load_demo_projects()
    if demo_projects:
        logging.info("⚠️ Falling back to bundled demo projects")
        return demo_projects
    
    logging.error("❌ No crowdfunding projects available from any source")
    return []


async def fetch_from_angor_indexer() -> List[Dict[str, Any]]:
    """
    Fetch ALL projects from Angor Indexer API with optimized performance.
    
    This is the PRIMARY data source - it has:
    - Complete list of all crowdfunding projects
    - Investment amounts (from /stats endpoint)
    - Investor counts
    - Real blockchain data
    
    Optimized for speed:
    - Try mainnet first, fallback to testnet
    - Batch API calls with shorter timeouts
    - Skip detailed stats if they timeout
    - Use parallel fetching where possible
    
    Returns:
        List of normalized project dictionaries with full financial data
    """
    try:
        # Try mainnet first, then testnet
        api_endpoints = [
            ("mainnet", ANGOR_INDEXER_MAINNET),
            ("testnet", ANGOR_INDEXER_TESTNET)
        ]
        
        projects_data = None
        api_url = None
        
        for network, url in api_endpoints:
            try:
                print(f"🌐 Trying {network} indexer: {url}", flush=True)
                async with httpx.AsyncClient(timeout=15.0) as client:  # Shorter timeout
                    response = await client.get(url)
                    print(f"✅ {network} response status: {response.status_code}", flush=True)
                    response.raise_for_status()
                    
                    projects_data = response.json()
                    api_url = url
                    print(f"📊 Found {len(projects_data)} projects from {network}", flush=True)
                    break
                    
            except Exception as e:
                print(f"❌ {network} failed: {e}", flush=True)
                continue
        
        if not projects_data or not api_url:
            print("❌ No Angor indexer available", flush=True)
            return []
        
        # Process projects with optimized fetching
        print(f"📊 Processing {len(projects_data)} projects with optimized fetching...", flush=True)
        
        projects = []
        async with httpx.AsyncClient(timeout=5.0) as client:  # Very short timeout for details
            for idx, item in enumerate(projects_data, 1):
                try:
                    proj_id = item.get('projectIdentifier', '')
                    nostr_event_id = item.get('nostrEventId', '')
                    
                    # Basic project data (always available)
                    project = {
                        "id": f"angor_{proj_id}",
                        "title": f"Project {proj_id[:12]}...",  # Default, will be enriched later
                        "amount_target": 0,  # Would need ProjectInfo from Nostr NIP-3030
                        "amount_raised": 0,  # Will try to fetch from stats
                        "amount_spent": 0,
                        "amount_penalties": 0,
                        "investor_count": 0,  # Will try to fetch from stats
                        "created_at": parse_block_time(item.get('createdOnBlock', 0)),
                        "source": "angor_indexer",
                        "founder_key": item.get('founderKey', ''),
                        "nostr_event_id": nostr_event_id,
                        "project_identifier": proj_id,
                        "transaction_id": item.get('trxId', ''),
                        "created_block": item.get('createdOnBlock', 0)
                    }
                    
                    # Try to fetch stats (but don't fail if it times out)
                    try:
                        stats_url = f"{api_url}/{proj_id}/stats"
                        stats_response = await client.get(stats_url)
                        if stats_response.status_code == 200:
                            stats_data = stats_response.json()
                            project.update({
                                "amount_raised": stats_data.get('amountInvested', 0),
                                "investor_count": stats_data.get('investorCount', 0) or stats_data.get('totalInvestmentsCount', 0),
                                "amount_spent": stats_data.get('amountSpentSoFarByFounder', 0),
                                "amount_penalties": stats_data.get('amountInPenalties', 0)
                            })
                    except Exception as e:
                        # Stats fetch failed, but we still have the basic project
                        logging.debug(f"Could not fetch stats for {proj_id[:12]}: {e}")
                    
                    # Try to enrich with Nostr metadata (but don't fail if it times out)
                    if NOSTR_AVAILABLE and nostr_event_id:
                        try:
                            metadata = await fetch_project_metadata_by_event_id(nostr_event_id)
                            if metadata and metadata.get('name'):
                                project["title"] = metadata['name']
                                logging.info(f"✅ Enriched project {proj_id[:12]} with Nostr name: {project['title']}")
                        except Exception as e:
                            logging.debug(f"Could not fetch Nostr metadata for {proj_id[:12]}: {e}")
                    
                    projects.append(project)
                    
                    if idx % 5 == 0:  # Progress logging
                        print(f"  📈 Processed {idx}/{len(projects_data)} projects...", flush=True)
                        
                except Exception as e:
                    logging.error(f"Error parsing project {item.get('projectIdentifier', 'unknown')}: {e}")
                    continue
        
        print(f"✅ Successfully processed {len(projects)} projects from Angor indexer", flush=True)
        return projects
        
    except Exception as e:
        import traceback
        logging.error(f"Failed to fetch from Angor Indexer: {e}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        print(f"❌ ERROR: {e}", flush=True)
        print(f"❌ TRACEBACK: {traceback.format_exc()}", flush=True)
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
            normalized_projects = []
            for project in projects:
                try:
                    target_btc = float(project.get("target_btc", 0))
                    raised_btc = float(project.get("raised_btc", 0))
                    created_at = parse_angor_date(project.get("created_at"))
                    
                    normalized_projects.append(
                        {
                            "id": f"angor_demo_{project.get('id')}",
                            "title": project.get("title", "Demo Project"),
                            "amount_target": int(target_btc * 100_000_000),
                            "amount_raised": int(raised_btc * 100_000_000),
                            "amount_spent": 0,
                            "amount_spent_btc": 0.0,
                            "amount_penalties": 0,
                            "investor_count": project.get("investor_count", 0),
                            "created_at": created_at,
                            "source": "demo",
                            "founder_key": "",
                            "nostr_event_id": "",
                            "project_identifier": str(project.get("id", "")),
                            "transaction_id": "",
                            "created_block": 0
                        }
                    )
                except Exception as exc:
                    logging.warning("Skipping malformed demo project: %s", exc)
            
            return normalized_projects
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
