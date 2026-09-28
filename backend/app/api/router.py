"""
StormFusion AI — API Router Configuration
"""

from backend.app.api.endpoints import forecast, health
from fastapi import APIRouter

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
