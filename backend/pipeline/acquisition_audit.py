import json
from pathlib import Path
from backend.app.models.acquisition import TargetAcquisitionManifest

class AcquisitionAuditor:
    @staticmethod
    def load_manifest(filepath: str) -> TargetAcquisitionManifest:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return TargetAcquisitionManifest.from_dict(data)

    @staticmethod
    def validate_manifest(manifest: TargetAcquisitionManifest) -> bool:
        if manifest.scientific_status != "REAL_TARGETS_ACQUIRED":
            return False
        if manifest.radar.status != "ACQUIRED" or manifest.lightning.status != "ACQUIRED":
            return False
        return True
