"""Multi-source Bitcoin crowdfunding data aggregator."""

import asyncio
import hashlib
import logging
from typing import List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


async def fetch_all_projects() -> List[Dict[str, Any]]:
    """
    Fetch projects from all sources in parallel and deduplicate.
    
    Returns:
        List of unified project dictionaries
    """
    logger.info("🔄 Fetching projects from multiple sources...")
    start_time = datetime.now()
    
    # Fetch from all sources in parallel
    try:
        from app.connectors.geyser import fetch_geyser_projects
        from app.angor_adapter import get_angor_projects
        
        results = await asyncio.gather(
            fetch_geyser_projects(),
            get_angor_projects(),
            return_exceptions=True
        )
        
        geyser_projects = results[0] if not isinstance(results[0], Exception) else []
        angor_raw_projects = results[1] if not isinstance(results[1], Exception) else []
        
        # Normalize Angor projects to unified schema
        angor_projects = []
        for proj in angor_raw_projects:
            normalized = {
                "id": f"angor_{proj.get('project_identifier', proj.get('id', ''))}",
                "name": proj.get("title", "Unknown Project"),
                "platform": "angor",
                "url": f"https://angor.io/project/{proj.get('project_identifier', '')}",
                "creator_display": proj.get("founder_key", "")[:16] + "..." if proj.get("founder_key") else "Unknown",
                "status": "active" if proj.get("amount_raised", 0) > 0 else "inactive",
                "goal_sats": proj.get("amount_target", 0),
                "raised_sats": proj.get("amount_raised", 0),
                "backer_count": proj.get("investor_count", 0),
                "project_type": "crowdfund",
                "started_at": proj.get("created_at"),
                "provenance": {
                    "source": "angor_indexer",
                    "fetched_at": datetime.now().isoformat(),
                    "raw_id": proj.get("project_identifier")
                }
            }
            angor_projects.append(normalized)
        
        # Combine all projects
        all_projects = geyser_projects + angor_projects
        
        # Deduplicate by URL
        seen_urls = set()
        deduplicated = []
        for proj in all_projects:
            url = proj.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(proj)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Successfully fetched {len(deduplicated)} projects in {duration:.2f}s")
        logger.info(f"   Geyser: {len(geyser_projects)} projects")
        logger.info(f"   Angor: {len(angor_projects)} projects")
        
        return deduplicated
        
    except Exception as e:
        logger.error(f"❌ Error fetching projects: {e}")
        return []


async def get_projects_summary() -> Dict[str, Any]:
    """
    Get summary statistics for all projects.
    
    Returns:
        Dictionary with summary statistics
    """
    projects = await fetch_all_projects()
    
    total_raised = sum(p.get("raised_sats", 0) for p in projects)
    total_backers = sum(p.get("backer_count", 0) for p in projects)
    
    by_platform = {}
    for proj in projects:
        platform = proj.get("platform", "unknown")
        if platform not in by_platform:
            by_platform[platform] = {
                "count": 0,
                "raised_sats": 0,
                "backers": 0
            }
        by_platform[platform]["count"] += 1
        by_platform[platform]["raised_sats"] += proj.get("raised_sats", 0)
        by_platform[platform]["backers"] += proj.get("backer_count", 0)
    
    return {
        "total_projects": len(projects),
        "total_raised_btc": total_raised / 100_000_000,
        "total_backers": total_backers,
        "by_platform": by_platform
    }


if __name__ == "__main__":
    # Test the aggregator
    import sys
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        summary = await get_projects_summary()
        print("\n📊 CITADEL Multi-Source Summary:")
        print(f"   Total Projects: {summary['total_projects']}")
        print(f"   Total Raised: {summary['total_raised_btc']:.4f} BTC")
        print(f"   Total Backers: {summary['total_backers']:,}")
        print("\n   By Platform:")
        for platform, stats in summary['by_platform'].items():
            print(f"     {platform}: {stats['count']} projects, {stats['raised_sats']/100_000_000:.4f} BTC")
    
    asyncio.run(test())
