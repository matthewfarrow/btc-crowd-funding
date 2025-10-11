"""FastAPI application setup."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, create_engine, Session
from app.config import config


# Database engine
engine = create_engine(config.DATABASE_URL, echo=False)


def create_db_and_tables():
    """Create database tables on startup."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    create_db_and_tables()
    print(f"🚀 BTC Crowdfund Analytics starting...")
    print(f"📊 Mode: {'Demo' if config.is_demo_mode else 'BTCPay Connected'}")
    yield
    # Shutdown
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="BTC Crowdfund Analytics",
    description="Bitcoin crowdfunding analytics dashboard",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
import os
static_path = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_path, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Include routers - Import here to avoid circular imports
from app import views
app.include_router(views.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mode": "demo" if config.is_demo_mode else "btcpay"
    }
