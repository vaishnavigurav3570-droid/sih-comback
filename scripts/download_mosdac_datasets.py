import os
import sys
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.app.providers.mosdac import MOSDACSatelliteProvider

def check_disk_space(path):
    try:
        total, used, free = shutil.disk_usage(path)
        # We need about 500MB per file (12 files = ~6GB). Let's check for at least 10GB.
        return free > 10 * 1024 * 1024 * 1024
    except Exception:
        return True

def run_download():
    print("========================================")
    print(" StormFusion AI — MOSDAC Live Download")
    print("========================================")
    
    load_dotenv()
    
    if not os.getenv("MOSDAC_USERNAME") or not os.getenv("MOSDAC_PASSWORD"):
        print("ERROR: MOSDAC_USERNAME and MOSDAC_PASSWORD must be set in .env")
        sys.exit(1)
        
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "mosdac"
    
    if not check_disk_space(data_dir.parent if data_dir.parent.exists() else project_root):
        print("ERROR: Insufficient disk space (Need > 10GB).")
        sys.exit(1)
        
    print(f"Date: 2025-05-29")
    print("\n3SIMG_L1B_STD: 6 files")
    print("3SIMG_L2B_CTP: 6 files")
    print("\nTotal files: 12")
    print(f"\nDownload destination:\n{data_dir}")
    print("\nCredentials: configured\n")
    
    # Do not prompt for input as per instructions, but we print confirmation summary
    print("Starting download process...\n")
    
    provider = MOSDACSatelliteProvider()
    
    start_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)
    
    l1b_files = [
        "3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1230_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1300_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1330_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1400_L1B_STD_V01R00.h5",
        "3SIMG_29MAY2025_1430_L1B_STD_V01R00.h5",
    ]
    
    l2b_files = [
        "3SIMG_29MAY2025_1200_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1230_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1300_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1330_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1400_L2B_CTP_V01R00.h5",
        "3SIMG_29MAY2025_1430_L2B_CTP_V01R00.h5",
    ]
    
    all_results = []
    
    l1b_dir = data_dir / "2025-05-29" / "3SIMG_L1B_STD"
    print(f"Downloading L1B files to {l1b_dir}...")
    res = provider.download_files("3SIMG_L1B_STD", l1b_files, start_time, end_time, l1b_dir)
    all_results.extend(res)
    
    l2b_dir = data_dir / "2025-05-29" / "3SIMG_L2B_CTP"
    print(f"Downloading L2B files to {l2b_dir}...")
    res = provider.download_files("3SIMG_L2B_CTP", l2b_files, start_time, end_time, l2b_dir)
    all_results.extend(res)
    
    # Save Manifest
    manifest_path = data_dir / "manifest.json"
    manifest_data = []
    for r in all_results:
        manifest_data.append({
            "dataset_id": r.dataset_id,
            "file_name": r.file_name,
            "status": r.status,
            "local_path": r.local_path,
            "file_size": r.file_size_bytes,
            "checksum": r.sha256_checksum,
            "error": r.error_message,
        })
        
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=4)
        
    print("\n================================================================================================")
    print(f"{'Dataset':<16} {'Filename':<42} {'Status':<12} {'Size'}")
    print("-" * 96)
    
    verified = 0
    failed = 0
    total_bytes = 0
    
    for r in all_results:
        size_mb = f"{r.file_size_bytes / (1024*1024):.1f}MB" if r.file_size_bytes else "0MB"
        print(f"{r.dataset_id:<16} {r.file_name:<42} {r.status:<12} {size_mb}")
        if r.status == "VERIFIED":
            verified += 1
            if r.file_size_bytes:
                total_bytes += r.file_size_bytes
        else:
            failed += 1
            
    print("\nSummary:")
    print(f"Total files requested: 12")
    print(f"Total verified: {verified}")
    print(f"Total failed: {failed}")
    print(f"Total bytes downloaded: {total_bytes}")
    print(f"Manifest location: {manifest_path}")

if __name__ == "__main__":
    run_download()
