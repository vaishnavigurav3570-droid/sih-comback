import os
import sys
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
from dotenv import load_dotenv

load_dotenv()


# Setup sys path so we can import backend
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from backend.app.providers.mosdac import MOSDACSatelliteProvider
from backend.app.models.data_types import BoundingBox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_audit():
    provider = MOSDACSatelliteProvider()
    if not provider.is_available:
        logger.error("MOSDAC provider not available. Check credentials.")
        return

    dataset_id = "3RIMG_L1C_ASIA_MER"
    
    events = [
        {
            "name": "16 April 2019",
            # Radar window: 16 April 2019 20:19–22:59 IST = 14:49 - 17:29 UTC
            "start": datetime(2019, 4, 16, 14, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2019, 4, 16, 18, 0, 0, tzinfo=timezone.utc),
            "radar_times": [
                datetime(2019, 4, 16, 14, 49, 25, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 15, 9, 30, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 15, 19, 29, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 15, 39, 27, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 15, 49, 27, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 16, 9, 25, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 16, 19, 30, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 16, 49, 29, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 16, 59, 29, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 17, 19, 28, tzinfo=timezone.utc),
                datetime(2019, 4, 16, 17, 29, 27, tzinfo=timezone.utc),
            ]
        },
        {
            "name": "20 July 2019",
            # Radar window: 20 July 2019 18:42–19:52 IST = 13:12 - 14:22 UTC
            "start": datetime(2019, 7, 20, 13, 0, 0, tzinfo=timezone.utc),
            "end": datetime(2019, 7, 20, 15, 0, 0, tzinfo=timezone.utc),
            "radar_times": [
                datetime(2019, 7, 20, 13, 12, 54, tzinfo=timezone.utc),
                datetime(2019, 7, 20, 13, 22, 54, tzinfo=timezone.utc),
                datetime(2019, 7, 20, 13, 32, 55, tzinfo=timezone.utc),
                datetime(2019, 7, 20, 13, 42, 56, tzinfo=timezone.utc),
                datetime(2019, 7, 20, 13, 52, 57, tzinfo=timezone.utc),
                datetime(2019, 7, 20, 14, 2, 58, tzinfo=timezone.utc),
                datetime(2019, 7, 20, 14, 12, 54, tzinfo=timezone.utc),
                datetime(2019, 7, 20, 14, 22, 56, tzinfo=timezone.utc),
            ]
        }
    ]
    
    bbox = BoundingBox(south=8.4, north=37.6, west=68.7, east=97.2)
    output_dir = Path("mosdac")
    
    for event in events:
        logger.info(f"--- Discovering for {event['name']} ---")
        try:
            results = provider.discover_datasets([dataset_id], event["start"], event["end"], bbox)
        except Exception as e:
            logger.error(f"Discovery failed: {e}")
            continue
            
        logger.info(f"Found {len(results)} files.")
        for r in results:
            logger.info(f"  {r.file_name} @ {r.timestamp}")
            
        # Try pairing
        if results:
            # Sort by time
            sat_times = sorted([r.timestamp for r in results if r.timestamp])
            logger.info(f"Satellite timestamps: {sat_times}")
            
            for rt in event["radar_times"]:
                nearest = None
                min_diff = timedelta(days=999)
                for st in sat_times:
                    diff = abs(rt - st)
                    if diff < min_diff:
                        min_diff = diff
                        nearest = st
                
                offset = min_diff.total_seconds()
                logger.info(f"Radar: {rt.strftime('%H:%M:%S UTC')} -> Nearest Sat: {nearest.strftime('%H:%M:%S UTC')} (Offset: {offset}s)")
        
        # Download attempt (up to 3 files)
        to_download = [r.file_name for r in results[:3] if r.file_name]
        if to_download:
            logger.info(f"Attempting to download: {to_download}")
            try:
                dl_results = provider.download_files(dataset_id, to_download, event["start"], event["end"], output_dir)
                for dr in dl_results:
                    logger.info(f"Download {dr.file_name}: Status={dr.status}, Error={dr.error_message}")
            except Exception as e:
                logger.error(f"Download process raised: {e}")

if __name__ == "__main__":
    run_audit()
