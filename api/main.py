"""
Savour Foods API — application entry point.

Start with:
    uvicorn api.main:app --reload --port 8001

Or from inside the api/ directory:
    uvicorn main:app --reload --port 8001
"""
from __future__ import annotations
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from .config import get_settings
from .database import get_db
from .routers import menu as menu_router
from .routers import orders as orders_router
from .routers import agent as agent_router


# ─────────────────────────────────────────────────────────────
# Logging — structured, goes to stdout for cloud-native deploys
# ─────────────────────────────────────────────────────────────

def _configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

_configure_logging(get_settings().log_level)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Lifespan — startup / shutdown hooks
# ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ──────────────────────────────────────────────
    logger.info("Starting Savour Foods API…")
    try:
        db = get_db()
        # Ping the DB with a lightweight query to catch mis-config early
        db.table("categories").select("id").limit(1).execute()
        logger.info("Supabase connectivity check: OK")
    except Exception as exc:
        logger.critical("Supabase connectivity check FAILED: %s", exc)
        raise

    yield   # application is running

    # ── Shutdown ─────────────────────────────────────────────
    logger.info("Savour Foods API shutting down.")


# ─────────────────────────────────────────────────────────────
# Application factory
# ─────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Savour Foods — Menu & Orders API",
        description="""
## Savour Foods Production API

A fully normalized food-ordering backend built on Supabase (PostgreSQL).

### Menu hierarchy
`categories` → `sub_categories` → `dishes` → `dish_options` → `dish_sub_options`

### Ordering
`orders` → `order_items`

### Key concepts
- **Fixed-price dishes** (`dish.price > 0`): unit price = shelf price ± add-on sub-options.
- **Variant-price dishes** (`dish.price = 0`): a priced sub-option **must** be selected — that price becomes the unit price.
- **Required options**: dish_options with `required=1` must be satisfied before an order is accepted.
- **JSONB snapshots**: selected options are snapshotted at order time — menu changes won't corrupt order history.
- **Status machine**: `pending → confirmed → preparing → ready → out_for_delivery → delivered` (any state → `cancelled`).
        """,
        version="4.0.0",
        contact={"name": "Savour Foods Engineering"},
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ─────────────────────────────────────────────────
    origins = (
        [o.strip() for o in settings.cors_origins.split(",")]
        if settings.cors_origins != "*"
        else ["*"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global error handler ──────────────────────────────────
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception on %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected server error occurred. Please try again later."},
        )

    # ── Root redirect → Swagger ───────────────────────────────
    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    # ── Health check (for load-balancers / k8s probes) ────────
    @app.get("/health", tags=["Health"], summary="Health check")
    def health():
        return {"status": "ok", "service": "savour-foods-api", "version": "4.0.0"}

    # ── Routers ───────────────────────────────────────────────
    API_PREFIX = "/api/v1"
    app.include_router(menu_router.router,   prefix=API_PREFIX)
    app.include_router(orders_router.router, prefix=API_PREFIX)
    app.include_router(agent_router.router,  prefix=API_PREFIX)

    logger.info(
        "Routes registered — menu prefix: %s/menu | orders prefix: %s/orders",
        API_PREFIX,
        API_PREFIX,
    )
    return app


app = create_app()
