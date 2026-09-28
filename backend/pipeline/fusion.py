"""
StormFusion AI — Data Fusion Module

PURPOSE:
    Combines all selected predictors and extracted features into a single,
    ML-ready tensor. This is the final stage of the data pipeline before
    the machine learning model takes over.

WHAT IT DOES:
    1. Feature Selection: Picks only the variables designated for the ML model.
    2. Missing Value Imputation: Fills NaNs (e.g., with 0 or the variable mean)
       so the neural network doesn't crash.
    3. Stacking: Stacks the 2D spatial grids into a 3D tensor
       (Channels, Latitude, Longitude).

OUTPUT:
    A numpy multi-dimensional array (tensor) and metadata about the
    channels (which index corresponds to which feature).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
from backend.pipeline.feature_extraction import FeatureExtractionResult

logger = logging.getLogger(__name__)


@dataclass
class FusionResult:
    """Result of the data fusion stage."""

    # Shape: (num_features, nlat, nlon)
    feature_tensor: np.ndarray | None = None
    feature_names: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DataFuser:
    """
    Fuses the xarray dataset into an ML-ready numerical tensor.
    """

    def __init__(self, selected_features: list[str] | None = None) -> None:
        """
        Args:
            selected_features: List of variable names to include in the tensor.
                               If None, includes all variables in the dataset.
        """
        self.selected_features = selected_features
        logger.info("DataFuser initialized")

    def run(self, extraction_result: FeatureExtractionResult) -> FusionResult:
        """
        Fuse the dataset into a single tensor.

        Args:
            extraction_result: Output from the Feature Extraction stage.

        Returns:
            FusionResult containing the ML-ready numpy array.
        """
        logger.info("Starting data fusion")

        result = FusionResult()

        if extraction_result.dataset is None:
            result.warnings.append("No dataset provided for fusion")
            return result

        ds = extraction_result.dataset

        # Determine which features to use
        if self.selected_features is not None:
            features_to_use = [f for f in self.selected_features if f in ds.data_vars]
            missing = set(self.selected_features) - set(features_to_use)
            if missing:
                result.warnings.append(
                    f"Requested features missing from dataset: {missing}"
                )
        else:
            features_to_use = list(ds.data_vars)

        if not features_to_use:
            result.warnings.append("No valid features found to fuse")
            return result

        # Stack into a tensor (Channels, Latitude, Longitude)
        tensor_channels = []
        for feat_name in features_to_use:
            data = ds[feat_name].values

            # Impute NaNs (simple 0-fill for now; a robust pipeline might use mean or spatial interpolation)
            if np.isnan(data).any():
                data = np.nan_to_num(data, nan=0.0)

            tensor_channels.append(data)
            result.feature_names.append(feat_name)

        result.feature_tensor = np.stack(tensor_channels, axis=0)

        logger.info(
            "Fusion complete: produced tensor of shape %s with %d features",
            result.feature_tensor.shape,
            len(result.feature_names),
        )

        return result
