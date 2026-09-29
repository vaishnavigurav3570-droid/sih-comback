import pytest
from datetime import datetime, timezone, timedelta
from backend.app.models.data_discovery import TargetCandidateInfo, calculate_temporal_compatibility, calculate_spatial_compatibility
from backend.pipeline.data_source_audit import DataSourceAuditor

def test_provenance_classification():
    candidate = TargetCandidateInfo(
        source="Test", product="Test", modality="TEST",
        provenance="UNKNOWN", format="HDF5", date_coverage="2025-05-29",
        time_resolution="30m", spatial_resolution="1km", geographic_coverage="India",
        variables="Reflectivity", target_suitability="EXCELLENT", input_suitability="EXCELLENT",
        may_29_available=False, time_window_compatible=False, access_status="NOT_FOUND", limitations="None"
    )
    assert candidate.provenance == "UNKNOWN"
    assert candidate.provenance != "REAL"

def test_candidate_compatibility_schema():
    candidate = TargetCandidateInfo(
        source="Test", product="Test", modality="TEST",
        provenance="REAL", format="HDF5", date_coverage="2025-05-29",
        time_resolution="30m", spatial_resolution="1km", geographic_coverage="India",
        variables="Reflectivity", target_suitability="EXCELLENT", input_suitability="EXCELLENT",
        may_29_available=True, time_window_compatible=True, access_status="VERIFIED_AVAILABLE", limitations="None"
    )
    d = candidate.to_dict()
    assert d["REAL/SYNTHETIC/UNKNOWN"] == "REAL"
    assert d["29-May-2025 availability"] == "Yes"
    assert d["12:00–15:00 compatibility"] == "Yes"

def test_timestamp_compatibility_calculation():
    target = datetime(2025, 5, 29, 15, 0, tzinfo=timezone.utc)
    
    # Exact match
    source_exact = datetime(2025, 5, 29, 15, 0, tzinfo=timezone.utc)
    res_exact = calculate_temporal_compatibility(source_exact, target)
    assert res_exact["is_acceptable"] is True
    assert res_exact["time_offset_minutes"] == 0.0

    # 10 min offset
    source_near = datetime(2025, 5, 29, 15, 10, tzinfo=timezone.utc)
    res_near = calculate_temporal_compatibility(source_near, target)
    assert res_near["is_acceptable"] is True
    assert res_near["time_offset_minutes"] == 10.0

    # 30 min offset
    source_far = datetime(2025, 5, 29, 15, 30, tzinfo=timezone.utc)
    res_far = calculate_temporal_compatibility(source_far, target)
    assert res_far["is_acceptable"] is False
    assert res_far["time_offset_minutes"] == 30.0

def test_spatial_compatibility_calculation():
    # Fully inside
    assert calculate_spatial_compatibility((10.0, 20.0), (70.0, 80.0)) is True
    # Fully outside
    assert calculate_spatial_compatibility((-10.0, 0.0), (40.0, 50.0)) is False
    # Partial overlap
    assert calculate_spatial_compatibility((30.0, 40.0), (90.0, 100.0)) is True

def test_auditor_missing_dir():
    auditor = DataSourceAuditor()
    auditor.audit_local_files("non_existent_directory_for_test")
    # Should safely return without crashing
    assert len(auditor.candidates) == 0

def test_auditor_api_results():
    auditor = DataSourceAuditor()
    auditor.audit_mosdac_api()
    assert len(auditor.candidates) >= 3
    # Check that UNKNOWN is not treated as REAL
    for c in auditor.candidates:
        assert c.provenance == "UNKNOWN"
        assert c.access_status == "NOT_FOUND"
