import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.ingestion.insat3ds import INSAT3DSParser, INSAT3DSParserError
import numpy as np

def report_dataset(name, da):
    total_count = da.size
    
    # Fast paths for huge arrays to avoid 10-second blocking per channel
    if total_count > 10_000_000:
        sample = da.values[::100, ::100]
        finite_count = np.sum(np.isfinite(sample))
        nan_count = sample.size - finite_count
        finite_pct = (finite_count / sample.size) * 100
        nan_pct = (nan_count / sample.size) * 100
        if finite_count > 0:
            dmin, dmax = float(np.nanmin(sample)), float(np.nanmax(sample))
        else:
            dmin, dmax = None, None
        print(f"  - {name}:")
        print(f"      Shape: {da.shape}")
        print(f"      Units: {da.attrs.get('units', 'unknown')}")
        print(f"      Valid Data (sampled): {finite_pct:.1f}% | NaN: {nan_pct:.1f}%")
        print(f"      Range (sampled): [{dmin}, {dmax}]")
    else:
        finite_count = np.sum(np.isfinite(da.values))
        nan_count = total_count - finite_count
        finite_pct = (finite_count / total_count) * 100
        nan_pct = (nan_count / total_count) * 100
        if finite_count > 0:
            dmin, dmax = float(np.nanmin(da.values)), float(np.nanmax(da.values))
        else:
            dmin, dmax = None, None
            
        print(f"  - {name}:")
        print(f"      Shape: {da.shape}")
        print(f"      Units: {da.attrs.get('units', 'unknown')}")
        print(f"      Valid Data: {finite_pct:.1f}% ({finite_count}) | NaN: {nan_pct:.1f}% ({nan_count})")
        print(f"      Range: [{dmin}, {dmax}]")

def test_single_pair(l1b_path, ctp_path):
    print(f"\n--- Testing Pair ---")
    print(f"L1B: {l1b_path.name}")
    try:
        payload = INSAT3DSParser.parse_l1b_file(l1b_path)
        print(f"  Status: SUCCESS")
        print(f"  Timestamp: {payload.metadata.time_start}")
        print(f"  Source: {payload.metadata.source_name} ({payload.metadata.source_type})")
        print(f"  Synthetic: {payload.metadata.is_synthetic}")
        for var in payload.data.data_vars:
            report_dataset(var, payload.data[var])
    except INSAT3DSParserError as e:
        print(f"  Status: FAILED - {e}")
        
    print(f"CTP: {ctp_path.name}")
    try:
        payload = INSAT3DSParser.parse_ctp_file(ctp_path)
        print(f"  Status: SUCCESS")
        print(f"  Timestamp: {payload.metadata.time_start}")
        print(f"  Source: {payload.metadata.source_name} ({payload.metadata.source_type})")
        print(f"  Synthetic: {payload.metadata.is_synthetic}")
        for var in payload.data.data_vars:
            report_dataset(var, payload.data[var])
    except INSAT3DSParserError as e:
        print(f"  Status: FAILED - {e}")

def main():
    parser = argparse.ArgumentParser(description="Smoke test for REAL INSAT-3DS parser")
    parser.add_argument("data_dir", type=str, help="Path to directory containing .h5 files")
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Directory {data_dir} does not exist.")
        sys.exit(1)
        
    times = ["1200", "1230", "1300", "1330", "1400", "1430"]
    
    print("========================================")
    print(" StormFusion AI - Real INSAT-3DS Test")
    print("========================================")
    
    # 1. Smoke test on the 1200 pair
    print("Phase 1: Detailed Smoke Test (12:00)")
    l1b_1200 = data_dir / "3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5"
    ctp_1200 = data_dir / "3SIMG_29MAY2025_1200_L2B_CTP_V01R00.h5"
    test_single_pair(l1b_1200, ctp_1200)
    
    # 2. Iterate remaining
    print("\nPhase 2: Remaining 5 Pairs Check")
    for t in times[1:]:
        l1b_file = data_dir / f"3SIMG_29MAY2025_{t}_L1B_STD_V01R00.h5"
        ctp_file = data_dir / f"3SIMG_29MAY2025_{t}_L2B_CTP_V01R00.h5"
        
        print(f"Checking {t}...")
        try:
            p_l1b = INSAT3DSParser.parse_l1b_file(l1b_file)
            p_ctp = INSAT3DSParser.parse_ctp_file(ctp_file)
            print(f"  [OK] L1B ({len(p_l1b.data.data_vars)} vars) | CTP ({len(p_ctp.data.data_vars)} vars)")
        except INSAT3DSParserError as e:
            print(f"  [FAIL] {e}")

if __name__ == "__main__":
    main()
