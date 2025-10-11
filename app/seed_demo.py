"""Seed demo data for testing."""

import random
from datetime import datetime, timedelta
from sqlmodel import Session, create_engine
from app.config import config
from app.models import Invoice, SQLModel
from app.repo import upsert_invoice


def seed_demo_invoices(session: Session, days: int = 14, count: int = 30):
    """Generate synthetic invoices for demo mode.
    
    Args:
        session: Database session
        days: Number of days to spread invoices over
        count: Number of invoices to generate
    """
    statuses = ["Settled", "Expired", "New", "Processing"]
    currencies = ["USD", "EUR", "GBP"]
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    print(f"🌱 Seeding {count} demo invoices...")
    
    for i in range(count):
        # Random date within range
        random_days = random.uniform(0, days)
        created_at = start_date + timedelta(days=random_days)
        
        # Random status weighted toward Settled
        status = random.choices(
            statuses,
            weights=[0.6, 0.2, 0.1, 0.1],
            k=1
        )[0]
        
        # Random amounts
        amount = round(random.uniform(10, 500), 2)
        btc_price = random.uniform(40000, 70000)
        amount_btc = round(amount / btc_price, 8)
        
        # Paid date for settled invoices
        paid_at = None
        if status == "Settled":
            paid_at = created_at + timedelta(minutes=random.randint(5, 60))
        
        invoice_data = {
            "id": f"demo_invoice_{i+1:04d}",
            "store_id": "demo_store",
            "status": status,
            "currency": random.choice(currencies),
            "amount": amount,
            "amount_btc": amount_btc,
            "created_at": created_at,
            "paid_at": paid_at,
            "payer_email": f"user{i+1}@example.com" if random.random() > 0.3 else None,
            "invoice_metadata": "{}"
        }
        
        upsert_invoice(session, invoice_data)
    
    print(f"✅ Seeded {count} invoices successfully!")


def main():
    """Main entry point for seeding."""
    # Create engine and tables
    engine = create_engine(config.DATABASE_URL, echo=False)
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        seed_demo_invoices(session)


if __name__ == "__main__":
    main()
