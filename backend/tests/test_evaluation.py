import pytest
from datetime import datetime, timezone, timedelta
import numpy as np
import torch
import xarray as xr

from backend.app.models.multimodal import MultimodalSample
from backend.pipeline.target_builder import RealTargetBuilder, TargetQualityController
from backend.pipeline.evaluation import DataLeakageAuditor, EventSplitter, BaselineModels, MetricCalculator
from backend.app.models.evaluation import SampleManifest

# =====================================================================
# MOCKS
# =====================================================================

def _mock_sample(ts: datetime, provenance="SYNTHETIC", val=40.0) -> MultimodalSample:
    ds = xr.Dataset(
        data_vars={
            "synthetic_radar_reflectivity": (("latitude", "longitude"), np.array([[val, np.nan], [10.0, 5.0]])),
            "synthetic_lightning_flash_density": (("latitude", "longitude"), np.array([[5.0, 0.0], [0.0, 0.0]])),
        }
    )
    return MultimodalSample(
        target_timestamp=ts,
        dataset=ds,
        provenance=provenance,
        is_synthetic=(provenance=="SYNTHETIC"),
        warnings=[],
        variables_present=["synthetic_radar_reflectivity"]
    )

# =====================================================================
# TARGET BUILDER & QC TESTS
# =====================================================================

def test_real_target_unavailable_failure():
    """Requirement: Real target unavailable -> explicit failure"""
    builder = RealTargetBuilder(require_real=True)
    ts = datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc)
    sample = _mock_sample(ts, provenance="SYNTHETIC")
    
    with pytest.raises(ValueError, match="Strict REAL target requirement failed"):
        builder.build([ts - timedelta(minutes=30)], sample)

def test_synthetic_target_explicitly_flagged():
    """Requirement: Synthetic target cannot masquerade as real"""
    builder = RealTargetBuilder(require_real=False)
    ts = datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc)
    sample = _mock_sample(ts, provenance="SYNTHETIC")
    
    _, _, manifest = builder.build([ts - timedelta(minutes=30)], sample)
    assert manifest.provenance == "MIXED" # Contains synthetic data, downgraded

def test_target_timestamp_alignment():
    """Requirement: Target timestamp alignment & Future-data leakage rejection"""
    builder = RealTargetBuilder(require_real=False)
    ts = datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc)
    sample = _mock_sample(ts)
    
    # Try to build where origin is AFTER target
    origin = ts + timedelta(minutes=30)
    with pytest.raises(ValueError, match="Temporal Leakage"):
        builder.build([origin], sample)

def test_missing_target_masking():
    """Requirement: Missing target != negative target, Valid positive/negative distinction"""
    builder = RealTargetBuilder(require_real=False)
    ts = datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc)
    # mock sample has NaN at [0,1]
    sample = _mock_sample(ts)
    
    target, mask, _ = builder.build([ts - timedelta(minutes=30)], sample)
    
    # [0,1] was NaN. Target mask should be False (0)
    assert mask[0, 0, 1] == 0
    # [0,0] was 40.0. > 35 threshold, so target should be True (1)
    assert target[0, 0, 0] == 1.0
    assert mask[0, 0, 0] == 1
    # [1,0] was 10.0. < 35 threshold, so target should be False (0)
    assert target[0, 1, 0] == 0.0
    assert mask[0, 1, 0] == 1

def test_invalid_target_values():
    """Requirement: invalid target values & QC framework"""
    # -200 is impossible reflectivity
    sample = _mock_sample(datetime(2025, 5, 29, 13, 0, tzinfo=timezone.utc), val=-200.0)
    builder = RealTargetBuilder(require_real=False)
    _, _, manifest = builder.build([datetime(2025, 5, 29, 12, 0, tzinfo=timezone.utc)], sample)
    
    assert not manifest.qc_status.is_valid
    assert manifest.qc_status.impossible_values_count > 0

# =====================================================================
# EVALUATION FRAMEWORK TESTS
# =====================================================================

def test_event_aware_split_behavior():
    """Requirement: event-aware split behavior & train/test event separation"""
    builder = RealTargetBuilder(require_real=False)
    manifests = []
    
    # 3 distinct days
    for day in [1, 2, 3]:
        ts = datetime(2025, 5, day, 12, 0, tzinfo=timezone.utc)
        sample = _mock_sample(ts)
        _, _, m = builder.build([ts - timedelta(minutes=30)], sample)
        manifests.append(m)
        
    splits = EventSplitter.split(manifests, train_ratio=0.4, val_ratio=0.4)
    
    # Event on Day 1 -> TRAIN
    # Event on Day 2 -> VALIDATION
    # Event on Day 3 -> TEST
    assert len(splits["TRAIN"]) == 1
    assert len(splits["VALIDATION"]) == 1
    assert len(splits["TEST"]) == 1
    
    assert splits["TRAIN"][0].target_timestamp.day == 1

def test_leakage_auditor_detects_contamination():
    """Requirement: Leakage checks & duplicate sample detection"""
    builder = RealTargetBuilder(require_real=False)
    ts1 = datetime(2025, 5, 1, 12, 0, tzinfo=timezone.utc)
    ts2 = datetime(2025, 5, 1, 13, 0, tzinfo=timezone.utc)
    
    _, _, m1 = builder.build([ts1 - timedelta(minutes=30)], _mock_sample(ts1))
    _, _, m2 = builder.build([ts2 - timedelta(minutes=30)], _mock_sample(ts2))
    
    m1.split_assignment = "TRAIN"
    m2.split_assignment = "TEST" # Contamination! Same day event in different splits
    
    with pytest.raises(ValueError, match="Data Leakage: Event 2025-05-01 appears in multiple splits"):
        DataLeakageAuditor.audit([m1, m2])
        
    # Test duplicate ID
    m2.split_assignment = "TRAIN"
    m2.sample_id = m1.sample_id
    with pytest.raises(ValueError, match="Data Leakage: Duplicate sample ID"):
        DataLeakageAuditor.audit([m1, m2])

def test_baseline_interfaces():
    """Requirement: baseline interface"""
    input_seq = np.array([[[1.0, 0.0], [0.0, 1.0]], [[0.0, 1.0], [1.0, 0.0]]])
    
    pred = BaselineModels.persistence(input_seq)
    assert pred.baseline_name == "Persistence"
    assert np.array_equal(pred.prediction_tensor, input_seq[-1])

def test_metric_correctness():
    """Requirement: metric correctness on controlled toy arrays & configurable threshold"""
    targets = np.array([[1.0, 1.0], [0.0, 0.0]])
    preds = np.array([[0.8, 0.3], [0.9, 0.1]])
    masks = np.array([[True, True], [True, False]]) # Ignore bottom right
    
    # Threshold 0.5
    # valid targets: [1, 1], [0]
    # valid preds:   [1, 0], [1]
    
    # TP: [0,0] (1 and 1) -> 1
    # FP: [1,0] (0 target, 1 pred) -> 1
    # FN: [0,1] (1 target, 0 pred) -> 1
    # TN: None
    
    metrics = MetricCalculator.evaluate_binary(preds, targets, masks, threshold=0.5)
    
    assert metrics.confusion_matrix["TP"] == 1
    assert metrics.confusion_matrix["FP"] == 1
    assert metrics.confusion_matrix["FN"] == 1
    
    assert metrics.precision == 0.5  # 1 / (1 + 1)
    assert metrics.recall == 0.5     # 1 / (1 + 1)
    assert metrics.csi == 1/3        # 1 / (1 + 1 + 1)
    
    # Brier Score check: Mean squared error of probabilities
    # Targets: [1, 1, 0]
    # Preds: [0.8, 0.3, 0.9]
    # Errors: [0.2, 0.7, 0.9] -> Squared: [0.04, 0.49, 0.81] -> Mean: 1.34 / 3 = 0.4466...
    assert np.isclose(metrics.brier_score, (0.04 + 0.49 + 0.81) / 3)
