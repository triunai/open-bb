"""
FastAPI Application Factory

Creates and configures the FastAPI application with all routes,
middleware, and event handlers.
"""

import sys
import asyncio

# Fix for Windows asyncio/asyncpg issues (in worker process)
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ofac_scanner.presentation.api.middleware import PrivateNetworkAccessMiddleware

from ofac_scanner import __version__
from ofac_scanner.config import get_settings
from ofac_scanner.infrastructure.database import get_engine
from ofac_scanner.infrastructure.database.models import Base
from ofac_scanner.infrastructure.scheduler import PollingScheduler
from ofac_scanner.presentation.api.routes import health, ofac, widgets
from ofac_scanner.presentation.api.state import set_scheduler


logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.
    """
    print("DEBUG: LIFESPAN START")
    settings = get_settings()
    
    logger.info(
        "Application starting",
        version=__version__,
        environment="dev" if settings.is_development else "prod",
    )
    
    # Create database tables (dev only - use migrations in prod)
    if settings.is_development:
        print("DEBUG: Creating tables...")
        try:
            engine = get_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
            print("DEBUG: Tables created.")
        except Exception as e:
            print(f"DEBUG: Table creation failed: {e}")
            logger.warning(
                "Failed to create database tables - DB may not be available",
                error=str(e),
            )
            import traceback
            traceback.print_exc()

    # Scheduler commented out...
    
    print("DEBUG: LIFESPAN YIELD")
    yield  # Application runs here
    
    # Shutdown
    print("DEBUG: LIFESPAN SHUTDOWN")
    from ofac_scanner.presentation.api.state import get_scheduler
    scheduler = get_scheduler()
    if scheduler:
        scheduler.stop()
        set_scheduler(None)
        logger.info("Background scheduler stopped")
    
    logger.info("Application shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI app instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title="OFAC Scanner Service",
        description="Venezuela sanctions monitoring for OpenBB Workspace",
        version=__version__,
        lifespan=lifespan,
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )
    
    # CORS middleware - allow all in dev, configured origins in prod
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Private Network Access middleware (for Chrome accessing localhost from public sites)
    if settings.is_development:
        app.add_middleware(PrivateNetworkAccessMiddleware)
    
    # Include routers
    app.include_router(health.router)
    app.include_router(widgets.router)
    app.include_router(ofac.router)
    
    return app
