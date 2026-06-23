"""
Fluffy Wholesale Billing Module — FastAPI entry point.

Dependency direction: this app imports orderr_core. orderr_core NEVER imports this.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import JSONResponse



from app.database import engine, Base
# Import all models so Base.metadata has them registered before create_all()
import app.models  # noqa: F401

# ── Create billing-owned tables (idempotent) ─────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Fluffy Billing Module",
    description="Automates rate lookup, quantity capture, and invoice generation for Fluffy Wholesale.",
    version="0.1.0",
)


@app.get("/health")
def health():
    """Liveness check — also used by OrdeRR webhook to confirm billing is up."""
    return JSONResponse({"status": "ok", "service": "fluffy-billing"})


# ── Verify OrdeRR models are importable (architecture check) ─────────────
@app.get("/debug/orderr-check")
def orderr_check():
    """
    Confirms orderr_core is installed and DB is reachable.
    Remove or auth-gate before production.
    """
    try:
        from orderr_core.models.order import Order
        from orderr_core.models.customer import Customer
        from orderr_core.services.order_service import get_current_business_date_str
        from orderr_core.services.template_parser import PRODUCT_DEFINITIONS
        biz_date = get_current_business_date_str()
        product_count = len(PRODUCT_DEFINITIONS)
        return {
            "orderr_core": "✅ importable",
            "current_business_date": biz_date,
            "product_definitions_loaded": product_count,
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})



# ── Routers (added incrementally per build step) ─────────────────────────

from app.routes.rates import router as rates_router
app.include_router(rates_router)