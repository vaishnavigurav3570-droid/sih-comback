import sys
from pathlib import Path
import xarray as xr
import numpy as np

def inspect_radar(file_path: Path):
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    print("="*60)
    print(f"INSPECTING: {file_path.name}")
    print("="*60)
    
    try:
        ds = xr.open_dataset(file_path, decode_times=False)
    except Exception as e:
        print(f"Failed to open with xarray: {e}")
        return
        
    print(f"Format: {file_path.suffix.lstrip('.')}")
    
    # Global attributes
    print("\nGLOBAL ATTRIBUTES:")
    for k, v in ds.attrs.items():
        if isinstance(v, np.ndarray):
            v = v.tolist()
        print(f"  {k}: {v}")
        
    print("\nDIMENSIONS:")
    for dim_name, dim_size in ds.dims.items():
        print(f"  {dim_name}: {dim_size}")
        
    print("\nCOORDINATES:")
    for coord_name, coord in ds.coords.items():
        attrs = coord.attrs
        print(f"  {coord_name} (shape: {coord.shape}, dtype: {coord.dtype})")
        for k, v in attrs.items():
            print(f"    {k}: {v}")
            
    print("\nVARIABLES:")
    for var_name, var in ds.data_vars.items():
        attrs = var.attrs
        print(f"  {var_name} (shape: {var.shape}, dtype: {var.dtype})")
        for k, v in attrs.items():
            print(f"    {k}: {v}")
            
        # Check fill values and stats
        vals = var.values
        if np.issubdtype(vals.dtype, np.number):
            valid_mask = np.isfinite(vals)
            
            # Identify extreme fill values typically ~9.96921e+36
            extreme_mask = vals > 1e30
            num_extreme = np.sum(extreme_mask)
            if num_extreme > 0:
                print(f"    DETECTED EXTREME FILL VALUES (>1e30): {num_extreme} pixels")
                valid_mask = valid_mask & (~extreme_mask)
                
            num_valid = np.sum(valid_mask)
            total = vals.size
            print(f"    Valid fraction: {num_valid/total:.2%}")
            if num_valid > 0:
                print(f"    Min: {np.nanmin(vals[valid_mask])}")
                print(f"    Max: {np.nanmax(vals[valid_mask])}")
                print(f"    Mean: {np.nanmean(vals[valid_mask])}")
                
if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_radar(Path(sys.argv[1]))
    else:
        print("Usage: python inspect_radar.py <path_to_radar.nc>")
