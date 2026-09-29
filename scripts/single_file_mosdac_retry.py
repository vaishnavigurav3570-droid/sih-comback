import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.app.providers.mosdac import MOSDACSatelliteProvider

def run_single_retry():
    print("========================================")
    print(" Single-File MOSDAC Retry")
    print("========================================")
    
    load_dotenv()
    
    if not os.getenv("MOSDAC_USERNAME") or not os.getenv("MOSDAC_PASSWORD"):
        print("ERROR: MOSDAC_USERNAME and MOSDAC_PASSWORD must be set in .env")
        sys.exit(1)
        
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data" / "mosdac"
    dataset_id = "3SIMG_L2B_CTP"
    target_file = "3SIMG_29MAY2025_1200_L2B_CTP_V01R00.h5"
    
    target_dir = data_dir / "2025-05-29" / dataset_id
    target_path = target_dir / target_file
    
    # Check if already exists and verified
    manifest_path = data_dir / "manifest.json"
    manifest_data = []
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)
            
    # Look for it in manifest
    for entry in manifest_data:
        if entry["file_name"] == target_file and entry["status"] == "VERIFIED":
            if target_path.exists():
                print(f"File {target_file} already exists and is VERIFIED locally.")
                sys.exit(0)
    
    print(f"\nWaiting 15 seconds to avoid immediate 429...")
    time.sleep(15)
    
    provider = MOSDACSatelliteProvider()
    
    # Using a slightly wider window to ensure the file is found during discovery if needed.
    start_time = datetime(2025, 5, 29, 11, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc)
    
    print(f"\nAttempting to download {target_file}...")
    
    res = provider.download_files(dataset_id, [target_file], start_time, end_time, target_dir)
    result = res[0] if res else None
    
    if not result:
        print("No result returned.")
        sys.exit(1)
        
    # Update manifest
    updated = False
    for i, entry in enumerate(manifest_data):
        if entry["file_name"] == target_file:
            manifest_data[i] = {
                "dataset_id": result.dataset_id,
                "file_name": result.file_name,
                "status": result.status,
                "local_path": result.local_path,
                "file_size": result.file_size_bytes,
                "checksum": result.sha256_checksum,
                "error": result.error_message,
            }
            updated = True
            break
            
    if not updated:
        manifest_data.append({
            "dataset_id": result.dataset_id,
            "file_name": result.file_name,
            "status": result.status,
            "local_path": result.local_path,
            "file_size": result.file_size_bytes,
            "checksum": result.sha256_checksum,
            "error": result.error_message,
        })
        
    with open(manifest_path, "w") as f:
        json.dump(manifest_data, f, indent=4)
        
    print("\n--- Final Report ---")
    print(f"File: {result.file_name}")
    print(f"Status: {result.status}")
    if result.status == "VERIFIED":
        print(f"Size: {result.file_size_bytes} bytes")
        print(f"SHA-256: {result.sha256_checksum}")
        print(f"HDF5 Structural Validation: OK")
    else:
        print(f"Error: {result.error_message}")
        print(f"HDF5 Structural Validation: N/A")
        
    print(f"Manifest Status: UPDATED")

if __name__ == "__main__":
    run_single_retry()
