"""
StormFusion AI — Feature Extraction Module

PURPOSE:
    Computes derived meteorological features from the common grid dataset.
    This stage enriches the raw data with predictors that ML models
    find useful for identifying convection and severe weather.

WHAT IT DOES:
    1. Spatial Gradients: Areas of rapid change (e.g., temperature fronts,
       moisture boundaries) are often where storms initiate.
    2. Thresholding/Masking: Creating binary masks for specific conditions
       (e.g., CAPE > 1000 and CIN > -50).
    3. Normalization: Scaling features to standard ranges if needed (though
       often left to the ML model's preprocessing layer).

OUTPUT:
    An enriched xarray.Dataset that contains all the original variables
    plus the newly computed feature variables.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import xarray as xr
from backend.pipeline.common_grid import CommonGridResult

logger = logging.getLogger(__name__)


@dataclass
class FeatureExtractionResult:
    """Result of the feature extraction stage."""

    dataset: xr.Dataset | None = None
    original_variables: list[str] = field(default_factory=list)
    extracted_features: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class FeatureExtractor:
    """
    Computes derived features from the gridded data.
    """

    def __init__(self) -> None:
        logger.info("FeatureExtractor initialized")

    def run(self, grid_result: CommonGridResult) -> FeatureExtractionResult:
        """
        Extract features from the common grid dataset.

        Args:
            grid_result: Output from the Common Grid stage.

        Returns:
            FeatureExtractionResult containing the enriched dataset.
        """
        logger.info("Starting feature extraction")

        result = FeatureExtractionResult()

        if grid_result.dataset is None:
            result.warnings.append("No dataset provided for feature extraction")
            return result

        ds = grid_result.dataset.copy()
        result.original_variables = list(ds.data_vars)

        try:
            # 1. Spatial Gradients
            self._compute_spatial_gradients(ds, result)

            # 2. Convective Instability Indices
            self._compute_instability_indices(ds, result)

        except Exception as exc:
            warning = f"Error during feature extraction: {exc}"
            logger.warning(warning)
            result.warnings.append(warning)

        result.dataset = ds
        logger.info(
            "Feature extraction complete: generated %d new features",
            len(result.extracted_features),
        )

        return result

    def _compute_spatial_gradients(
        self, ds: xr.Dataset, result: FeatureExtractionResult
    ) -> None:
        """Compute spatial gradients (magnitude of change) for key variables."""
        variables_to_gradient = ["bt_tir1", "cape"]

        for var in variables_to_gradient:
            if var in ds.data_vars:
                data = ds[var].values

                # np.gradient returns a list of arrays (one for each dimension)
                # Since we have (latitude, longitude), grads[0] is lat grad, grads[1] is lon grad
                grads = np.gradient(data)

                # Magnitude of the gradient vector: sqrt((dx)^2 + (dy)^2)
                grad_mag = np.sqrt(grads[0] ** 2 + grads[1] ** 2)

                feat_name = f"{var}_spatial_grad"
                ds[feat_name] = (("latitude", "longitude"), grad_mag)
                ds[feat_name].attrs = {
                    "long_name": f"Spatial Gradient Magnitude of {var}",
                    "is_feature": True,
                }
                result.extracted_features.append(feat_name)
                logger.debug("Computed spatial gradient for %s", var)

    def _compute_instability_indices(
        self, ds: xr.Dataset, result: FeatureExtractionResult
    ) -> None:
        """Compute combined instability features."""

        # Example: Severe Convection Potential (Simple Proxy)
        # Needs CAPE and CIN. High CAPE and small absolute CIN is favorable.
        if "cape" in ds.data_vars and "cin" in ds.data_vars:
            cape = ds["cape"].values
            cin = ds["cin"].values

            # Simple combined feature: CAPE + CIN (where CIN is usually negative)
            # If CIN is highly negative (strong cap), potential is lower.
            # Mask out NaNs
            potential = np.where(
                np.isnan(cape) | np.isnan(cin),
                np.nan,
                np.maximum(cape + cin, 0.0),  # Floor at 0
            )

            feat_name = "severe_convection_potential"
            ds[feat_name] = (("latitude", "longitude"), potential)
            ds[feat_name].attrs = {
                "long_name": "Severe Convection Potential (CAPE + CIN)",
                "is_feature": True,
            }
            result.extracted_features.append(feat_name)
            logger.debug("Computed severe_convection_potential")
