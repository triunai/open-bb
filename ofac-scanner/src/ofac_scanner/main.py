"""
OFAC Scanner Service - Main Entry Point

This module provides the entry point for running the service.
It can be run directly or via the CLI command.
"""

import sys
import asyncio
from pathlib import Path

# =============================================================================
# CRITICAL: Load .env FIRST with override=True to prevent stale env vars
# =============================================================================
# This ensures the .env file takes precedence over any environment variables
# that might be set in parent shell sessions (VSCode terminal, etc.)
# =============================================================================
from dotenv import load_dotenv

# Find .env relative to this file (goes up to project root)
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path, override=True)
print(f"DEBUG MAIN: Loaded .env from {env_path} (exists: {env_path.exists()})")
# =============================================================================

import uvicorn
import structlog

# Fix for Windows asyncio/asyncpg issues
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


from ofac_scanner.config import get_settings
from ofac_scanner.presentation.api import create_app


def configure_logging() -> None:
    """Configure structured logging."""
    import logging
    
    settings = get_settings()
    
    # Map string level to logging constant
    level = getattr(logging, settings.log_level, logging.INFO)
    
    # Configure structlog
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]
    
    if True: # Force console for debugging
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    # if settings.log_format == "json":
    #     processors.append(structlog.processors.JSONRenderer())
    # else:
    #     processors.append(structlog.dev.ConsoleRenderer(colors=True))
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def main() -> None:
    """
    Main entry point for the OFAC Scanner service.
    
    Configures logging and starts the Uvicorn server.
    """
    configure_logging()
    settings = get_settings()
    
    # Create the FastAPI app
    app = create_app()
    
    # Run with Uvicorn
    import traceback
    try:
        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=settings.reload,
            log_level=settings.log_level.lower(),
            loop="asyncio",
        )
    except Exception:
        print("CRITICAL STARTUP ERROR:")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
