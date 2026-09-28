"""
StormFusion AI — Health Endpoints
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str


@router.get("/", response_model=HealthResponse)
async def get_health():
    """
    Basic health check for the API.
    """
    return HealthResponse(status="ok", version="0.1.0")
