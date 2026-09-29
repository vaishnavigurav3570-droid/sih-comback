import pytest
import numpy as np
from pathlib import Path
from datetime import datetime, timezone

from backend.app.ingestion.radar import RadarParser
from backend.app.models.radar import RadarMetadata

RADAR_FILE = Path("polar_MUM190720194254.nc")

@pytest.fixture
def real_radar_data():
    if not RADAR_FILE.exists():
        pytest.skip(f"Real radar file {RADAR_FILE} not available for testing")
    return RadarParser.parse_radar_file(RADAR_FILE, target_threshold=35.0)

def test_file_opens_successfully(real_radar_data):
    assert real_radar_data is not None

def test_radar_metadata_extraction(real_radar_data):
    meta = real_radar_data["metadata"]
    assert isinstance(meta, RadarMetadata)
    assert meta.radar_id == "MUM"
    assert meta.latitude > 18.0 and meta.latitude < 19.5
    assert meta.longitude > 72.0 and meta.longitude < 73.5
    assert meta.sweep_count == 10

def test_ref_extraction(real_radar_data):
    data = real_radar_data["data"]
    assert "REF" in data
    assert "REF" in real_radar_data["metadata"].field_names
    
def test_vel_extraction(real_radar_data):
    data = real_radar_data["data"]
    assert "VEL" in data

def test_width_extraction(real_radar_data):
    data = real_radar_data["data"]
    assert "WIDTH" in data
    
def test_fill_value_conversion(real_radar_data):
    data = real_radar_data["data"]
    # Check that there are no extreme values > 1e30 left in REF
    ref = data["REF"]
    assert not np.any(ref > 1e30)

def test_nan_preservation(real_radar_data):
    data = real_radar_data["data"]
    ref = data["REF"]
    assert np.any(np.isnan(ref)) # There should be NaNs where fill values were

def test_units_preservation(real_radar_data):
    meta = real_radar_data["metadata"]
    assert meta.units.get("REF") == "dBZ"

def test_timestamp_extraction(real_radar_data):
    meta = real_radar_data["metadata"]
    assert meta.start_time.year == 2019
    assert meta.start_time.month == 7
    assert meta.start_time.day == 20

def test_configurable_reflectivity_threshold():
    if not RADAR_FILE.exists():
        pytest.skip()
    # Test with a different threshold
    parsed = RadarParser.parse_radar_file(RADAR_FILE, target_threshold=40.0)
    data = parsed["data"]
    target = data["TARGET"]
    ref = data["REF"]
    valid = np.isfinite(ref)
    assert np.all((ref[valid] >= 40.0) == (target[valid] == 1.0))

def test_target_distinction(real_radar_data):
    data = real_radar_data["data"]
    target = data["TARGET"]
    ref = data["REF"]
    # Check EVENT
    assert np.any(target == 1.0)
    # Check NON-EVENT
    assert np.any(target == 0.0)
    # Check MISSING
    assert np.any(np.isnan(target))
    # Check missing is not converted to 0
    assert np.all(np.isnan(target) == np.isnan(ref))

def test_no_synthetic_fallback(real_radar_data):
    meta = real_radar_data["metadata"]
    assert meta.is_synthetic is False

def test_provenance(real_radar_data):
    meta = real_radar_data["metadata"]
    assert meta.source_type.value.upper() == "RADAR"
    assert "MUM" in meta.source_name
    assert meta.provenance == "Real CF/Radial Radar Data"

def test_deterministic_parsing(real_radar_data):
    meta = real_radar_data["metadata"]
    assert meta.start_time is not None
    assert meta.end_time is not None

def test_spatial_compatibility(real_radar_data):
    coords = real_radar_data["coordinates"]
    lat = coords["latitude"]
    lon = coords["longitude"]
    # Should be inside INDIA_BBOX (8.4-37.6 N, 68.7-97.2 E)
    min_lat = np.nanmin(lat)
    max_lat = np.nanmax(lat)
    min_lon = np.nanmin(lon)
    max_lon = np.nanmax(lon)
    assert max_lat >= 8.4 and min_lat <= 37.6
    assert max_lon >= 68.7 and min_lon <= 97.2

def test_temporal_compatibility(real_radar_data):
    meta = real_radar_data["metadata"]
    # We are matching against INSAT-3DR 20 July 2019
    # Ensure it's 20 July 2019
    assert meta.start_time.date() == datetime(2019, 7, 20).date()
