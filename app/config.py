"""Application configuration."""

import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration from environment variables."""
    
    # BTCPay Server settings
    BTCPAY_HOST: Optional[str] = os.getenv("BTCPAY_HOST")
    BTCPAY_API_KEY: Optional[str] = os.getenv("BTCPAY_API_KEY")
    BTCPAY_STORE_ID: Optional[str] = os.getenv("BTCPAY_STORE_ID")
    BTCPAY_WEBHOOK_SECRET: Optional[str] = os.getenv("BTCPAY_WEBHOOK_SECRET")
    
    # Angor settings
    ANGOR_ENABLE: bool = os.getenv("ANGOR_ENABLE", "false").lower() == "true"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./btc_crowdfund.db")
    
    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode (no BTCPay configured)."""
        return not (self.BTCPAY_HOST and self.BTCPAY_STORE_ID)
    
    @property
    def btcpay_base_url(self) -> str:
        """Build BTCPay base URL."""
        if not self.BTCPAY_HOST:
            return ""
        return f"https://{self.BTCPAY_HOST}"


config = Config()
