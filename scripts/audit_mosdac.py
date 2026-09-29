import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.providers.mosdac import MOSDACSatelliteProvider

def audit_mosdac():
    provider = MOSDACSatelliteProvider()
    print("==================================================")
    print("MOSDAC DATASET SEARCH AUDIT")
    print("==================================================")
    
    start = datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)
    end = datetime(2025, 5, 29, 15, 0, tzinfo=timezone.utc)
    
    # Attempting to search for common MOSDAC strings (heuristic)
    keywords = ["3SIMG", "3SCSG", "DWR", "RADAR", "LIGHTNING", "NWP", "NCUM", "GFS", "PRECIP"]
    
    # We will search by fetching all datasets and filtering if possible, or using the provider's discover
    datasets = provider.discover_datasets(dataset_ids=keywords, start_time=start, end_time=end)
    
    if not datasets:
        print("No datasets discovered from MOSDAC.")
    else:
        for ds in datasets:
            print(f"Dataset ID: {ds.dataset_id}")
            print(f"Product Name: {ds.product_name}")
            print(f"Coverage: {ds.temporal_resolution}")
            print("---")
            
if __name__ == "__main__":
    audit_mosdac()
