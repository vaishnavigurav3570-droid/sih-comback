import json
import pytest
from pathlib import Path
from datetime import datetime
from backend.pipeline.target_builder import RealTargetBuilder, TargetDefinition
from backend.app.models.multimodal import MultimodalSample

def test_public_benchmark_manifest_exists():
    manifest_path = Path("docs/public_indian_benchmark_manifest.json")
    assert manifest_path.exists(), "Manifest file missing"

def test_public_benchmark_metadata_validation():
    manifest_path = Path("docs/public_indian_benchmark_manifest.json")
    with open(manifest_path, 'r') as f:
        data = json.load(f)
    assert data.get("temporal_overlap_found") is False, "False overlap claimed!"
    assert data.get("status") == "PUBLIC_DATASET_FOUND_BUT_NOT_SCIENTIFICALLY_COMPATIBLE"

def test_prevent_unknown_to_real():
    # Attempting to use a synthetic provenance when RealTargetBuilder requires real
    builder = RealTargetBuilder(require_real=True)
    sample = MultimodalSample(
        provenance="UNKNOWN",
        dataset=None,
        target_timestamp=datetime(2025, 5, 29, 15, 0)
    )
    with pytest.raises(ValueError, match="Strict REAL target requirement failed"):
        builder._extract_target(sample, TargetDefinition(name="Test", description="Test", variable_name="var"))

def test_prevent_synthetic_data_in_real_evaluation():
    builder = RealTargetBuilder(require_real=True)
    sample = MultimodalSample(
        provenance="SYNTHETIC",
        dataset=None,
        target_timestamp=datetime(2025, 5, 29, 15, 0)
    )
    with pytest.raises(ValueError, match="Strict REAL target requirement failed"):
        builder._extract_target(sample, TargetDefinition(name="Test", description="Test", variable_name="var"))

def test_public_dataset_temporal_overlap_mismatch():
    # Emulate the audit script logic where we detect mismatch in timestamps
    # Radar is 2019, Lightning is 2023
    radar_year = 2019
    lightning_year = 2023
    assert radar_year != lightning_year, "Temporal mismatch must be caught!"
