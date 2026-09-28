"""
StormFusion AI — FastAPI Application Entrypoint
"""

from contextlib import asynccontextmanager

import structlog
from backend.app.api.router import api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the FastAPI app."""
    # Startup
    logger.info("Starting up StormFusion AI Backend...")
    yield
    # Shutdown
    logger.info("Shutting down StormFusion AI Backend...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="StormFusion AI API",
        description="Nowcasting of thunderstorm and lightning using atmospheric observation data.",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Configure CORS (allow all for prototype, restrict for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
