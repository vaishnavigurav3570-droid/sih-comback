import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Ensure backend module is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.models.data_types import BoundingBox

def run_discovery():
    print("========================================")
    print(" StormFusion AI — Live MOSDAC Discovery")
    print("========================================")
    
    load_dotenv()
    
    username = os.getenv("MOSDAC_USERNAME")
    password = os.getenv("MOSDAC_PASSWORD")
    
    if not username or not password:
        print("ERROR: MOSDAC_USERNAME and MOSDAC_PASSWORD must be set in .env")
        sys.exit(1)
        
    print(f"Authenticated as: {username}")
    
    provider = MOSDACSatelliteProvider()
    
    datasets = ["3SIMG_L1B_STD", "3SIMG_L2B_CTP"]
    
    # Target Event: 29 May 2025 12:00 to 14:30
    start_time = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    end_time = datetime(2025, 5, 29, 14, 30, tzinfo=timezone.utc)
    bbox = BoundingBox(south=8.4, north=37.6, west=68.7, east=97.2)
    
    print(f"Target Window: {start_time.isoformat()} to {end_time.isoformat()}\n")
    
    try:
        results = provider.discover_datasets(datasets, start_time, end_time, bbox)
        
        print(f"{'Dataset':<20} {'Timestamp':<25} {'File':<40} {'Status'}")
        print("-" * 95)
        for r in results:
            ts_str = r.timestamp.strftime("%Y-%m-%d %H:%M") if r.timestamp else "UNKNOWN"
            fname = r.file_name or "UNKNOWN"
            print(f"{r.dataset_id:<20} {ts_str:<25} {fname:<40} {r.availability_status}")
            
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_discovery()
