import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.models.data_types import BoundingBox

def run_live_test():
    print("========================================")
    print(" StormFusion AI — Live MOSDAC Test")
    print("========================================")
    
    # Load credentials from .env
    load_dotenv()
    
    username = os.getenv("MOSDAC_USERNAME")
    password = os.getenv("MOSDAC_PASSWORD")
    
    if not username or not password:
        print("ERROR: MOSDAC_USERNAME and MOSDAC_PASSWORD must be set in .env")
        print("Test aborted.")
        sys.exit(1)
        
    print(f"Testing connection for user: {username}")
    
    provider = MOSDACSatelliteProvider()
    
    status = provider.validate_connection()
    if not status.is_connected:
        print(f"Connection validation failed: {status.message}")
        sys.exit(1)
        
    print("Connection validated. Searching and downloading dataset 3SIMG_L1B_STD...")
    
    bbox = BoundingBox(south=8.4, north=37.6, west=68.7, east=97.2)
    start_time = datetime.now(timezone.utc)
    
    try:
        payload = provider.download(
            dataset_id="3SIMG_L1B_STD",
            bounding_box=bbox,
            start_time=start_time,
            end_time=start_time
        )
        
        print("\nSUCCESS: Data payload successfully downloaded and parsed via xarray!")
        print(f"Dataset ID: {payload.metadata.dataset_id}")
        print(f"Is Synthetic? {payload.metadata.is_synthetic}")
        print(f"Observation marked as: {payload.data.attrs.get('is_synthetic')}")
        print(f"Variables found: {list(payload.data.data_vars.keys())}")
        
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_live_test()
