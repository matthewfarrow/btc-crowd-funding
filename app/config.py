"""Application configuration."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration - simplified for pure Angor crowdfunding analytics."""
    
    # Angor is ALWAYS enabled - that's what CITADEL is for!
    ANGOR_ENABLE: bool = True
    
    # Database (only used for caching, could be removed later)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./btc_crowdfund.db")


config = Config()
