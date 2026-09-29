import logging
from datetime import datetime, timezone
import xarray as xr
import numpy as np

from backend.app.models.multimodal import MultimodalSample, ModalityStatus
from backend.app.models.data_types import DataSourceType
from backend.pipeline.common_grid import CommonGridResult

logger = logging.getLogger(__name__)

class MultimodalSynchronizer:
    """
    Synchronizes output from the CommonGridder into a unified MultimodalSample.
    Records provenance, missing-data statistics, and temporal offsets.
    """
    
    def run(self, grid_result: CommonGridResult, target_time: datetime) -> MultimodalSample:
        logger.info(f"Synchronizing multimodal data for {target_time}")
        
        sample = MultimodalSample(target_timestamp=target_time)
        ds = grid_result.dataset
        
        if ds is None:
            logger.warning("Grid result dataset is None. Returning empty sample.")
            return sample
            
        sample.dataset = ds
        
        # We need to deduce modality statuses from the dataset variables and attributes
        # Since variables come from different sources, we group them.
        
        modalities_found = set()
        is_mixed = False
        has_real = False
        has_synthetic = False
        
        for var_name in ds.data_vars:
            da = ds[var_name]
            
            # Extract metadata
            is_synthetic = da.attrs.get("is_synthetic", True)
            src_type = str(da.attrs.get("source_type", DataSourceType.SYNTHETIC.value))
            src_name = str(da.attrs.get("source", "Synthetic"))
            
            if is_synthetic:
                has_synthetic = True
            else:
                has_real = True
                
            total_cells = int(da.size)
            valid_cells = int((~np.isnan(da)).sum())
            missing_cells = total_cells - valid_cells
            
            status = ModalityStatus(
                is_available=True,
                source_name=src_name,
                is_synthetic=is_synthetic,
                time_offset_seconds=da.attrs.get("time_offset_seconds", 0.0),
                missing_cells_count=missing_cells,
                total_cells_count=total_cells
            )
            
            # Map back to specific modalities (simple heuristic based on variable names for now)
            if "IMG" in var_name or var_name in ["CTP", "CTT", "EFF_EMISS"]:
                sample.satellite_status = status
                modalities_found.add("satellite")
            elif "radar" in var_name.lower() or "reflectivity" in var_name.lower():
                sample.radar_status = status
                modalities_found.add("radar")
            elif "lightning" in var_name.lower():
                sample.lightning_status = status
                modalities_found.add("lightning")
            elif "nwp" in var_name.lower() or "forecast" in var_name.lower():
                sample.nwp_status = status
                modalities_found.add("nwp")

        if has_real and has_synthetic:
            sample.provenance = "MIXED"
        elif has_real:
            sample.provenance = "REAL"
        elif has_synthetic:
            sample.provenance = "SYNTHETIC"
            
        return sample
