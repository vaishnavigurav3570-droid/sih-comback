import logging
import numpy as np
from datetime import datetime
import xarray as xr
from scipy.ndimage import shift
from backend.app.models.features import MLFeatureBatch

logger = logging.getLogger(__name__)

class SatelliteNowcastPrototype:
    """
    Deterministic satellite-based storm-development indicator prototype.
    NOT A TRAINED ML MODEL. Uses physical relationships to estimate 
    storm development potential and apparent cloud motion.
    """
    
    def __init__(self):
        # Weights for the indicator
        # These are deterministic, uncalibrated weights to form a prototype indicator
        self.cooling_weight = 0.4
        self.spatial_weight = 0.3
        self.split_window_weight = 0.3

    def process(self, batch: MLFeatureBatch):
        """
        Process a batch of extracted features to produce nowcast indicators.
        """
        logger.info(f"Processing satellite nowcast prototype for {len(batch.timestamps)} timestamps.")
        
        # 1. extract relevant channels
        try:
            idx_tir1 = batch.feature_names.index("IMG_TIR1")
            idx_cooling = batch.feature_names.index("TIR1_TEMPORAL_DIFF")
            idx_spatial = batch.feature_names.index("TIR1_SPATIAL_GRAD")
            idx_diff = batch.feature_names.index("TIR1_TIR2_DIFF")
        except ValueError as e:
            raise ValueError(f"Missing required feature for nowcast: {e}")
            
        N, C, H, W = batch.tensor.shape
        
        results = []
        for t in range(N):
            tir1 = batch.tensor[t, idx_tir1]
            cooling = batch.tensor[t, idx_cooling]
            spatial = batch.tensor[t, idx_spatial]
            split_diff = batch.tensor[t, idx_diff]
            
            # Missingness mask (preserve original missing data)
            valid_mask = ~np.isnan(tir1)
            
            # Indicator Formulation
            # Normalize cooling (negative is stronger cooling/updraft)
            cooling_norm = self._normalize_cooling(cooling)
            
            # Normalize spatial (higher gradient implies structure)
            spatial_norm = self._normalize_spatial(spatial)
            
            # Normalize split window
            diff_norm = self._normalize_split_window(split_diff)
            
            # Combine indicators deterministically
            indicator = (
                self.cooling_weight * cooling_norm +
                self.spatial_weight * spatial_norm + 
                self.split_window_weight * diff_norm
            )
            # Mask out missing regions
            indicator[~valid_mask] = np.nan
            
            valid_comp_frac = self._calc_valid_fraction([cooling_norm, spatial_norm, diff_norm], valid_mask)
            
            # Apparent Cloud Motion Estimation (from t-1 to t)
            u, v, speed, direction, motion_quality = self._estimate_motion(batch.tensor, t, idx_tir1)
            
            # Short Horizon Extrapolation (+30 min)
            extrap_indicator, extrap_mask = self._extrapolate(indicator, valid_mask, u, v)
            
            result = {
                "input_timestamp": batch.timestamps[t],
                "storm_development_indicator": indicator,
                "indicator_validity_mask": valid_mask,
                "motion_u": u,
                "motion_v": v,
                "motion_speed": speed,
                "motion_direction": direction,
                "motion_quality": motion_quality,
                "valid_component_fraction": valid_comp_frac,
                "extrapolated_indicator": extrap_indicator,
                "extrapolated_validity_mask": extrap_mask,
                "provenance": "SATELLITE",
                "is_calibrated_probability": False
            }
            results.append(result)
            
        return results

    def _normalize_cooling(self, cooling: np.ndarray) -> np.ndarray:
        # cooling is roughly K/30min
        # Negative values are stronger. Cap at -10 to 0. 
        # So -10K/30min -> 1.0, 0K/30min -> 0.0
        norm = np.zeros_like(cooling)
        mask = ~np.isnan(cooling)
        val = np.clip(cooling[mask], -10.0, 0.0)
        norm[mask] = (0.0 - val) / 10.0
        norm[~mask] = np.nan
        return norm

    def _normalize_spatial(self, spatial: np.ndarray) -> np.ndarray:
        # spatial K/pixel
        # higher is more convective boundary
        norm = np.zeros_like(spatial)
        mask = ~np.isnan(spatial)
        val = np.clip(spatial[mask], 0, 5)
        norm[mask] = val / 5.0
        norm[~mask] = np.nan
        return norm

    def _normalize_split_window(self, diff: np.ndarray) -> np.ndarray:
        # split window difference K
        norm = np.zeros_like(diff)
        mask = ~np.isnan(diff)
        val = np.clip(diff[mask], 0, 5)
        norm[mask] = val / 5.0
        norm[~mask] = np.nan
        return norm
        
    def _calc_valid_fraction(self, components: list, valid_mask: np.ndarray) -> np.ndarray:
        total = np.zeros_like(valid_mask, dtype=float)
        valid = np.zeros_like(valid_mask, dtype=float)
        for comp in components:
            total += 1.0
            valid += (~np.isnan(comp)).astype(float)
            
        frac = valid / np.maximum(total, 1.0)
        frac[~valid_mask] = np.nan
        return frac
        
    def _estimate_motion(self, tensor: np.ndarray, t: int, idx_tir1: int):
        if t == 0:
            return 0.0, 0.0, 0.0, 0.0, 0.0
            
        prev_img = tensor[t-1, idx_tir1]
        curr_img = tensor[t, idx_tir1]
        
        if np.all(np.isnan(prev_img)) or np.all(np.isnan(curr_img)):
            return 0.0, 0.0, 0.0, 0.0, 0.0
            
        p = np.nan_to_num(prev_img, nan=np.nanmean(prev_img))
        c = np.nan_to_num(curr_img, nan=np.nanmean(curr_img))
        
        # Cross-power spectrum for phase correlation
        F_p = np.fft.fft2(p)
        F_c = np.fft.fft2(c)
        cross_power = (F_p * F_c.conj()) / np.abs(F_p * F_c.conj() + 1e-8)
        r = np.fft.ifft2(cross_power).real
        
        # Find peak
        peak_idx = np.unravel_index(np.argmax(r), r.shape)
        
        H, W = p.shape
        dy = peak_idx[0]
        dx = peak_idx[1]
        
        # shift adjustment for FFT
        if dy > H // 2: dy -= H
        if dx > W // 2: dx -= W
        
        u = -dx  # u is along X (longitude)
        v = -dy  # v is along Y (latitude)
        
        speed = np.sqrt(u**2 + v**2)
        direction = np.arctan2(v, u) * 180 / np.pi
        
        quality = float(np.max(r)) # correlation peak is a quality measure
        
        return float(u), float(v), float(speed), float(direction), quality
        
    def _extrapolate(self, indicator: np.ndarray, valid_mask: np.ndarray, u: float, v: float):
        # Shift indicator by (v, u) assuming 30 min step
        if np.all(np.isnan(indicator)):
            return indicator, valid_mask
            
        extrap = shift(indicator, shift=(v, u), mode='constant', cval=np.nan)
        extrap_mask = shift(valid_mask.astype(float), shift=(v, u), mode='constant', cval=0.0) > 0.5
        
        return extrap, extrap_mask
