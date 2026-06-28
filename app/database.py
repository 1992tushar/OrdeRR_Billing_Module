"""
Billing database setup.
Same DATABASE_URL as OrdeRR (shared Postgres instance).
Billing owns: daily_rates, customer_rate_overrides, order_item_actuals,
              invoices, invoice_items.
Billing NEVER writes to OrdeRR's tables.
"""
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
load_dotenv()  # reads .env from cwd by default

# Reuse OrdeRR's DATABASE_URL — same DB, billing just owns different tables.
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Render gives postgres:// but SQLAlchemy 2.x requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=3,
    max_overflow=1,
    connect_args={"sslmode": "require"},  # add this line
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
