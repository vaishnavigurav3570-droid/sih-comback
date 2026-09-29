"""
StormFusion AI — Prediction Module (ML Baseline)

PURPOSE:
    Takes the ML-ready tensor from the Fusion stage and passes it through
    a Spatiotemporal Machine Learning model to generate nowcasts.

WHAT IT DOES:
    1. Model Loading: Loads a PyTorch model (CNN/U-Net).
    2. Inference: Runs a forward pass on the fused tensor.
    3. Post-processing: Converts the model's raw output tensor back into
       georeferenced GridCellForecast objects.
    4. Product Generation: Packages everything into a ForecastProduct API response.

BASELINE PROTOTYPE:
    For the prototype, this uses a simple heuristic or an untrained CNN
    to demonstrate the end-to-end pipeline. It produces deterministic
    probabilities (e.g., higher CAPE -> higher thunderstorm probability).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from typing import TYPE_CHECKING

from backend.app.models.data_types import (
    ForecastLeadTime,
    StormMovementVector,
)
from backend.app.models.forecast import ForecastProduct, GridCellForecast

if TYPE_CHECKING:
    from backend.pipeline.orchestrator import PipelineResult

logger = logging.getLogger(__name__)


if TORCH_AVAILABLE:

    class BaselineCNN(nn.Module):
        """
        A simple baseline Convolutional Neural Network for nowcasting.
        Takes a multi-channel grid and predicts 2 channels per lead time:
        - Thunderstorm probability
        - Lightning probability
        """

        def __init__(self, in_channels: int, num_lead_times: int = 4):
            super().__init__()
            self.num_lead_times = num_lead_times

            # Simple 3-layer CNN
            self.conv1 = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
            self.conv2 = nn.Conv2d(16, 32, kernel_size=3, padding=1)
            # Output: 2 probability maps (thunderstorm, lightning) per lead time
            self.conv3 = nn.Conv2d(32, 2 * num_lead_times, kernel_size=3, padding=1)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x shape: (batch_size, in_channels, height, width)
            x = F.relu(self.conv1(x))
            x = F.relu(self.conv2(x))
            x = self.conv3(x)
            # Apply sigmoid to get probabilities in [0, 1]
            x = torch.sigmoid(x)
            return x


@dataclass
class PredictionResult:
    """Result of the prediction stage."""

    forecast_product: ForecastProduct | None = None
    warnings: list[str] = field(default_factory=list)


class Predictor:
    """
    Runs the ML model to generate forecasts.
    """

    def __init__(self, use_dummy_heuristic: bool = False):
        """
        Args:
            use_dummy_heuristic: If True, bypass PyTorch and use simple math heuristics.
                                 Useful if torch is not installed or for deterministic tests.
        """
        self.use_dummy_heuristic = use_dummy_heuristic or not TORCH_AVAILABLE
        self.model = None
        self.lead_times = [
            ForecastLeadTime.PLUS_15,
            ForecastLeadTime.PLUS_30,
            ForecastLeadTime.PLUS_60,
            ForecastLeadTime.PLUS_90,
        ]

        if not self.use_dummy_heuristic:
            # Initialize with random weights. In a real system, we'd load a state_dict here.
            # We don't know in_channels until we see the data, so we'll lazy-initialize it.
            logger.info("Predictor initialized with PyTorch CNN")
        else:
            logger.info(
                "Predictor initialized with Heuristic baseline (PyTorch unavailable or bypassed)"
            )

    def run(self, pipeline_result: PipelineResult) -> PredictionResult:
        """
        Generate a forecast product from the pipeline result.
        """
        logger.info("Starting prediction stage")
        result = PredictionResult()

        if (
            pipeline_result.fusion_result is None
            or pipeline_result.fusion_result.feature_tensor is None
        ):
            result.warnings.append("No fusion tensor available for prediction")
            return result

        fusion_res = pipeline_result.fusion_result
        tensor = fusion_res.feature_tensor  # Shape: (channels, lats, lons)
        assert tensor is not None

        # 1. Run Inference
        if self.use_dummy_heuristic:
            probs = self._run_heuristic(tensor, fusion_res.feature_names)
        else:
            probs = self._run_torch_model(tensor, fusion_res.feature_names)

        # 2. Convert raw arrays back to GridCellForecast objects
        # To do this, we need the grid coordinates
        grid_spec = pipeline_result.grid_spec
        if grid_spec is None:
            result.warnings.append("No grid specification available")
            return result
        
        lats = grid_spec.latitudes
        lons = grid_spec.longitudes

        grid_forecasts = []

        # Subsample the grid so we don't generate 100,000 objects in memory for the prototype.
        # In a real system, the API might serve the full grid as a NetCDF/GeoJSON or binary array.
        # Here we'll return a sparse selection or just the whole thing if it's small.
        # For prototype simplicity, we'll iterate all cells but we should be mindful of scale.

        # We have probs shape: (num_lead_times, 2, nlat, nlon)
        # where 2 channels are: 0=thunderstorm, 1=lightning

        for t_idx, lead_time in enumerate(self.lead_times):
            ts_probs = probs[t_idx, 0, :, :]
            lt_probs = probs[t_idx, 1, :, :]

            # Iterate through the grid
            for i, lat in enumerate(lats):
                for j, lon in enumerate(lons):
                    ts_p = float(ts_probs[i, j])
                    lt_p = float(lt_probs[i, j])

                    # Only include cells with notable probability to keep payload small
                    if ts_p > 0.1 or lt_p > 0.1:
                        cell_forecast = GridCellForecast(
                            latitude=float(lat),
                            longitude=float(lon),
                            lead_time=lead_time,
                            thunderstorm_probability=ts_p,
                            lightning_probability=lt_p,
                            storm_intensity=ts_p * 100.0,  # Proxy for intensity
                            storm_movement=StormMovementVector(
                                speed_kmh=25.0, direction_degrees=45.0
                            ),
                            confidence=0.85,
                            is_synthetic=pipeline_result.is_synthetic,
                            explanation=(
                                "High CAPE and strong spatial gradient detected"
                                if ts_p > 0.5
                                else None
                            ),
                        )
                        grid_forecasts.append(cell_forecast)

        # 3. Create the final ForecastProduct
        product = ForecastProduct(
            forecast_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            valid_from=pipeline_result.analysis_time or datetime.now(timezone.utc),
            region=grid_spec.bbox if grid_spec else [],
            lead_times=self.lead_times,
            grid_forecasts=grid_forecasts,
            sensor_health=[],  # Ideally populated from the ingestion/time sync stages
            data_sources_used=["SYNTHETIC" if pipeline_result.is_synthetic else "REAL"],
            model_version=(
                "baseline-cnn-v1.0"
                if not self.use_dummy_heuristic
                else "baseline-heuristic-v1.0"
            ),
            is_demo_mode=pipeline_result.is_synthetic,
            warnings=pipeline_result.warnings,
        )

        result.forecast_product = product
        logger.info(
            "Prediction complete: Generated %d cell forecasts", len(grid_forecasts)
        )
        return result

    def _run_torch_model(
        self, tensor_np: np.ndarray, feature_names: list[str]
    ) -> np.ndarray:
        """Run the PyTorch CNN model."""
        channels, nlat, nlon = tensor_np.shape

        if self.model is None:
            self.model = BaselineCNN(
                in_channels=channels, num_lead_times=len(self.lead_times)
            )
            self.model.eval()  # Set to evaluation mode

        # Convert numpy to torch tensor, add batch dimension
        # Shape: (1, channels, nlat, nlon)
        x = torch.from_numpy(tensor_np).float().unsqueeze(0)

        with torch.no_grad():
            out = self.model(x)

        # out shape: (1, 2 * num_lead_times, nlat, nlon)
        out_np = out.squeeze(0).numpy()

        # Reshape to (num_lead_times, 2, nlat, nlon)
        reshaped = out_np.reshape(len(self.lead_times), 2, nlat, nlon)
        return reshaped

    def _run_heuristic(
        self, tensor_np: np.ndarray, feature_names: list[str]
    ) -> np.ndarray:
        """Run a simple math heuristic for deterministic testing."""
        channels, nlat, nlon = tensor_np.shape
        num_lead = len(self.lead_times)

        # Output shape: (num_lead_times, 2, nlat, nlon)
        probs = np.zeros((num_lead, 2, nlat, nlon))

        # Try to find a predictor, e.g. CAPE
        cape_idx = -1
        if "cape" in feature_names:
            cape_idx = feature_names.index("cape")

        for t in range(num_lead):
            if cape_idx >= 0:
                cape_data = tensor_np[cape_idx, :, :]
                # Very simple proxy: normalize CAPE 0-5000 to 0-1 probability
                base_prob = np.clip(cape_data / 5000.0, 0.0, 1.0)
            else:
                base_prob = np.full((nlat, nlon), 0.2)

            # Thunderstorm probability
            probs[t, 0, :, :] = base_prob * (1.0 - t * 0.1)  # Decreases over time
            # Lightning probability
            probs[t, 1, :, :] = base_prob * 0.8 * (1.0 - t * 0.1)

        return probs
