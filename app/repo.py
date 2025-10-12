"""Repository layer for database operations - CITADEL."""

from datetime import datetime
from typing import List
from sqlmodel import Session, select
from app.models import CrowdfundingProject


def upsert_project(session: Session, project_data: dict) -> CrowdfundingProject:
    """Insert or update a crowdfunding project.
    
    Args:
        session: Database session
        project_data: Project data dictionary
        
    Returns:
        The created or updated CrowdfundingProject
    """
    project_id = project_data.get("id")
    project = session.get(CrowdfundingProject, project_id)
    
    if project:
        # Update existing
        for key, value in project_data.items():
            if hasattr(project, key):
                setattr(project, key, value)
    else:
        # Create new
        project = CrowdfundingProject(**project_data)
        session.add(project)
    
    session.commit()
    session.refresh(project)
    return project


def get_all_projects(session: Session) -> List[CrowdfundingProject]:
    """Get all crowdfunding projects."""
    statement = select(CrowdfundingProject).order_by(CrowdfundingProject.created_at.desc())
    return list(session.exec(statement).all())


def get_projects_by_source(session: Session, source: str) -> List[CrowdfundingProject]:
    """Get projects filtered by source (e.g., 'angor_indexer')."""
    statement = select(CrowdfundingProject).where(CrowdfundingProject.source == source).order_by(CrowdfundingProject.created_at.desc())
    return list(session.exec(statement).all())
