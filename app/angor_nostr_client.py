"""Angor Nostr client for fetching real crowdfunding projects."""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from nostr_sdk import Client, Filter, Kind, init_logger, LogLevel, Keys, EventBuilder, PublicKey
import logging

logger = logging.getLogger(__name__)

# Angor uses NIP-3030 (custom event kind 3030) for project information
ANGOR_PROJECT_KIND = 3030

# Angor relay endpoints
ANGOR_RELAYS = [
    "wss://relay.angor.io",
    "wss://relay.damus.io",
    "wss://relay.primal.net",
    "wss://nos.lol"
]


async def fetch_angor_projects_from_nostr() -> List[Dict[str, Any]]:
    """
    Fetch real Angor crowdfunding projects from Nostr relays.
    
    Returns:
        List of normalized project dictionaries with:
        - id: Project identifier
        - title: Project name
        - amount_target: Target funding amount in BTC
        - amount_raised: Amount raised so far in BTC
        - created_at: Project creation date
        - source: "angor_nostr"
    """
    try:
        # Initialize Nostr client
        client = Client()
        
        # Add Angor relays
        for relay in ANGOR_RELAYS:
            try:
                await client.add_relay(relay)
                logger.info(f"Connected to relay: {relay}")
            except Exception as e:
                logger.warning(f"Failed to connect to {relay}: {e}")
        
        # Connect to relays
        await client.connect()
        
        # Create filter for Angor projects (Kind 3030)
        # Looking for events from the last year
        since_timestamp = int((datetime.now().timestamp() - (365 * 24 * 60 * 60)))
        
        project_filter = Filter().kind(Kind(ANGOR_PROJECT_KIND)).since(since_timestamp)
        
        # Also look for metadata (Kind 0) to get project names/descriptions
        metadata_filter = Filter().kind(Kind(0)).since(since_timestamp)
        
        # Subscribe and fetch events
        logger.info("Fetching Angor projects from Nostr relays...")
        events = await client.get_events_of([project_filter], timeout=10)
        
        logger.info(f"Received {len(events)} project events from Nostr")
        
        # Parse projects
        projects = []
        for event in events:
            try:
                project_data = parse_angor_event(event)
                if project_data:
                    projects.append(project_data)
            except Exception as e:
                logger.error(f"Error parsing project event: {e}")
        
        logger.info(f"Successfully parsed {len(projects)} Angor projects")
        
        return projects
        
    except Exception as e:
        logger.error(f"Error fetching Angor projects from Nostr: {e}")
        return []


def parse_angor_event(event) -> Dict[str, Any] | None:
    """
    Parse a Nostr event containing Angor project information.
    
    Args:
        event: Nostr event object
        
    Returns:
        Dictionary with normalized project data or None if parsing fails
    """
    try:
        # The content should be JSON with ProjectInfo structure
        content = event.content()
        project_info = json.loads(content)
        
        # Extract relevant fields
        project_id = project_info.get("ProjectIdentifier", event.id().to_hex())
        
        # Convert satoshis to BTC
        target_sats = project_info.get("TargetAmount", 0)
        target_btc = target_sats / 100_000_000 if target_sats else 0
        
        # Parse dates
        start_date_str = project_info.get("StartDate", "")
        created_at = parse_date(start_date_str) if start_date_str else datetime.fromtimestamp(event.created_at().as_secs())
        
        # Extract founder key for identification
        founder_key = project_info.get("FounderKey", "")
        nostr_pubkey = project_info.get("NostrPubKey", event.author().to_hex())
        
        return {
            "id": f"angor_nostr_{project_id[:16]}",
            "title": f"Angor Project {project_id[:8]}",  # Will be enriched with metadata later
            "amount_target": target_btc,
            "amount_raised": 0,  # Would need to query blockchain/indexer for actual raised amount
            "created_at": created_at,
            "source": "angor_nostr",
            "founder_key": founder_key,
            "nostr_pubkey": nostr_pubkey,
            "stages": len(project_info.get("Stages", [])),
            "penalty_days": project_info.get("PenaltyDays", 0)
        }
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse project JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing Angor event: {e}")
        return None


def parse_date(date_str: str) -> datetime:
    """Parse ISO date string to datetime."""
    try:
        # Try ISO format with 'Z'
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        # Fallback to current time
        return datetime.utcnow()


async def get_angor_projects_with_stats() -> List[Dict[str, Any]]:
    """
    Fetch Angor projects and enrich with blockchain statistics.
    
    This queries:
    1. Nostr relays for project information
    2. Bitcoin indexer (optional) for investment amounts
    3. Metadata for project names/descriptions
    
    Returns:
        List of complete project dictionaries
    """
    # Fetch base project data from Nostr
    projects = await fetch_angor_projects_from_nostr()
    
    # TODO: Enhance with:
    # - Query Angor indexer API for raised amounts
    # - Fetch Nostr kind 0 (metadata) events for project names
    # - Calculate time-series data for daily raised capital
    
    logger.info(f"Returning {len(projects)} Angor projects with stats")
    return projects


async def fetch_project_metadata_by_event_id(event_id: str) -> Dict[str, Any] | None:
    """
    Fetch project metadata from Nostr using the event ID.
    
    This queries Nostr relays for the NIP-3030 (Kind 3030) event that contains
    the project information (name, description, funding goals, etc.).
    
    Args:
        event_id: The Nostr event ID (hex string) from the Angor indexer
        
    Returns:
        Dictionary with project metadata (name, description, etc.) or None if not found
    """
    if not event_id:
        logger.warning("No event_id provided to fetch_project_metadata_by_event_id")
        return None
        
    try:
        # Initialize Nostr client
        client = Client()
        
        # Add Angor relays
        for relay in ANGOR_RELAYS:
            try:
                await client.add_relay(relay)
            except Exception as e:
                logger.debug(f"Failed to add relay {relay}: {e}")
        
        # Connect to relays
        await client.connect()
        
        # Create filter for specific event ID
        from nostr_sdk import EventId
        event_filter = Filter().id(EventId.from_hex(event_id))
        
        # Fetch the event
        logger.info(f"Fetching Nostr event {event_id[:16]}... for project metadata")
        events = await client.get_events_of([event_filter], timeout=10)
        
        if not events:
            logger.warning(f"No event found for ID {event_id[:16]}...")
            return None
            
        # Parse the event content (should be ProjectInfo JSON)
        event = list(events)[0]
        content = event.content()
        
        try:
            project_info = json.loads(content)
            
            # Extract project name and description
            metadata = {
                "name": project_info.get("ProjectIdentifier", "")[:12] + "...",  # Default to ID prefix
                "description": "",
                "target_amount": project_info.get("TargetAmount", 0) / 100_000_000,  # sats to BTC
                "founder_key": project_info.get("FounderKey", ""),
                "nostr_pubkey": project_info.get("NostrPubKey", ""),
                "start_date": project_info.get("StartDate", ""),
                "penalty_days": project_info.get("PenaltyDays", 0),
                "stages": len(project_info.get("Stages", []))
            }
            
            logger.info(f"Successfully fetched metadata for event {event_id[:16]}...")
            return metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse project info JSON: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Error fetching project metadata from Nostr: {e}")
        return None

