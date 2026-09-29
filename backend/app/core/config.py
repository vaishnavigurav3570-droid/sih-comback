"""
StormFusion AI — Application Configuration

Loads all settings from environment variables (via .env file).
This is the ONLY place credentials and configuration are read.
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class AppMode(str, Enum):
    """Application operating mode."""

    DEMO = "DEMO"
    LIVE = "LIVE"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Priority: environment variables > .env file > defaults here.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application Mode ---
    stormfusion_mode: AppMode = Field(
        default=AppMode.DEMO,
        description="DEMO = fully offline with synthetic data. LIVE = real data sources.",
    )

    # --- MOSDAC Credentials (server-side only, NEVER expose to frontend) ---
    mosdac_username: str = Field(
        default="",
        description="MOSDAC SSO username. Required only in LIVE mode.",
    )
    mosdac_password: str = Field(
        default="",
        description="MOSDAC SSO password. Required only in LIVE mode.",
    )
    mosdac_local_data_root: str = Field(
        default="",
        description="Path to local real INSAT-3DS data. Bypasses mdapi if set.",
    )

    # --- Data Directories ---
    data_dir: Path = Field(default=Path("./data"))
    raw_data_dir: Path = Field(default=Path("./data/raw"))
    processed_data_dir: Path = Field(default=Path("./data/processed"))
    synthetic_data_dir: Path = Field(default=Path("./data/synthetic"))

    # --- Backend ---
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)
    backend_debug: bool = Field(default=True)

    # --- Database ---
    database_url: str = Field(default="sqlite:///./data/stormfusion.db")

    # --- Logging ---
    log_level: str = Field(default="INFO")

    # --- Region of Interest ---
    default_bbox: str = Field(
        default="68.0,6.0,98.0,38.0",
        description="Default bounding box [west,south,east,north] for India.",
    )

    # --- Forecast ---
    forecast_lead_times: str = Field(
        default="15,30,60,90",
        description="Comma-separated lead times in minutes.",
    )

    @property
    def is_demo_mode(self) -> bool:
        """Check if running in demo mode."""
        return self.stormfusion_mode == AppMode.DEMO

    @property
    def lead_times_list(self) -> list[int]:
        """Parse forecast lead times into a list of integers."""
        return [int(t.strip()) for t in self.forecast_lead_times.split(",")]

    @property
    def default_bounding_box(self) -> tuple[float, float, float, float]:
        """Parse default bounding box into (west, south, east, north)."""
        parts = [float(x.strip()) for x in self.default_bbox.split(",")]
        if len(parts) != 4:
            raise ValueError(
                f"default_bbox must have 4 values (west,south,east,north), got {len(parts)}"
            )
        return (parts[0], parts[1], parts[2], parts[3])

    def ensure_directories(self) -> None:
        """Create data directories if they don't exist."""
        for dir_path in [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.synthetic_data_dir,
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info("Ensured directory exists: %s", dir_path)


def get_settings() -> Settings:
    """
    Create and return application settings.

    This function is the single entry point for configuration.
    """
    settings = Settings()
    settings.ensure_directories()
    return settings
