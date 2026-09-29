import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def audit_public_benchmark(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Audit logic to ensure we don't mix non-overlapping data
    radar_avail = manifest.get("radar_availability", False)
    light_avail = manifest.get("lightning_raw_availability", False)
    overlap = manifest.get("temporal_overlap_found", False)
    
    if radar_avail and light_avail and not overlap:
        logger.warning("Radar and Lightning exist, but timestamps do not overlap.")
        return {"status": "PUBLIC_DATASET_FOUND_BUT_NOT_SCIENTIFICALLY_COMPATIBLE", "valid": False}
        
    return {"status": manifest.get("status", "UNKNOWN"), "valid": overlap}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = audit_public_benchmark(Path("docs/public_indian_benchmark_manifest.json"))
    print(f"Audit Result: {result}")
