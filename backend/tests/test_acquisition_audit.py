import pytest
import json
import tempfile
from pathlib import Path
from backend.app.models.acquisition import TargetAcquisitionManifest, RadarAcquisitionRequest, LightningAcquisitionRequest
from backend.pipeline.acquisition_audit import AcquisitionAuditor

def test_manifest_deserialization():
    data = {
        "event_date": "2025-05-29",
        "region": "Maharashtra",
        "radar": {
            "status": "NOT_ACQUIRED",
            "source": "IMD DWR",
            "stations": ["Mumbai"],
            "requested_window_ist": ["11:30", "15:30"],
            "preferred_times_ist": ["12:00"],
            "format": "NetCDF",
            "access_route": "Email"
        },
        "lightning": {
            "status": "NOT_ACQUIRED",
            "source": "IITM ILLN",
            "requested_window_ist": ["11:30", "15:30"],
            "format": "CSV",
            "access_route": "Email"
        },
        "scientific_status": "REAL_TARGETS_NOT_YET_ACQUIRED"
    }
    
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.json') as f:
        json.dump(data, f)
        temp_path = f.name
        
    try:
        manifest = AcquisitionAuditor.load_manifest(temp_path)
        assert manifest.event_date == "2025-05-29"
        assert manifest.radar.stations == ["Mumbai"]
        assert manifest.scientific_status == "REAL_TARGETS_NOT_YET_ACQUIRED"
    finally:
        Path(temp_path).unlink()

def test_manifest_validation_rejects_unacquired():
    manifest = TargetAcquisitionManifest(
        event_date="2025-05-29",
        region="Maharashtra",
        radar=RadarAcquisitionRequest(
            status="NOT_ACQUIRED", source="", stations=[], requested_window_ist=[], preferred_times_ist=[], format="", access_route=""
        ),
        lightning=LightningAcquisitionRequest(
            status="NOT_ACQUIRED", source="", requested_window_ist=[], format="", access_route=""
        ),
        scientific_status="REAL_TARGETS_NOT_YET_ACQUIRED"
    )
    assert AcquisitionAuditor.validate_manifest(manifest) is False

def test_manifest_validation_accepts_acquired():
    manifest = TargetAcquisitionManifest(
        event_date="2025-05-29",
        region="Maharashtra",
        radar=RadarAcquisitionRequest(
            status="ACQUIRED", source="", stations=[], requested_window_ist=[], preferred_times_ist=[], format="", access_route=""
        ),
        lightning=LightningAcquisitionRequest(
            status="ACQUIRED", source="", requested_window_ist=[], format="", access_route=""
        ),
        scientific_status="REAL_TARGETS_ACQUIRED"
    )
    assert AcquisitionAuditor.validate_manifest(manifest) is True

def test_prevention_of_synthetic_data_classification():
    manifest = TargetAcquisitionManifest(
        event_date="2025-05-29",
        region="Maharashtra",
        radar=RadarAcquisitionRequest(
            status="SYNTHETIC", source="", stations=[], requested_window_ist=[], preferred_times_ist=[], format="", access_route=""
        ),
        lightning=LightningAcquisitionRequest(
            status="SYNTHETIC", source="", requested_window_ist=[], format="", access_route=""
        ),
        scientific_status="SYNTHETIC_TARGETS_USED"
    )
    # Validation must strictly reject synthetic targets as real targets
    assert AcquisitionAuditor.validate_manifest(manifest) is False

def test_prevention_of_server_error_as_not_available():
    # If a server error occurred, the status should be SERVER_ERROR, not NOT_AVAILABLE
    # Here we just verify that a SERVER_ERROR status is not treated as acquired
    manifest = TargetAcquisitionManifest(
        event_date="2025-05-29",
        region="Maharashtra",
        radar=RadarAcquisitionRequest(
            status="SERVER_ERROR", source="", stations=[], requested_window_ist=[], preferred_times_ist=[], format="", access_route=""
        ),
        lightning=LightningAcquisitionRequest(
            status="SERVER_ERROR", source="", requested_window_ist=[], format="", access_route=""
        ),
        scientific_status="SERVER_ERROR"
    )
    assert AcquisitionAuditor.validate_manifest(manifest) is False
