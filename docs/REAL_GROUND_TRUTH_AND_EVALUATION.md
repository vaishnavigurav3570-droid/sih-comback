# Real Ground-Truth and Evaluation Framework

## 1. Current Target Source Audit
- **INSAT-3DS Satellite**: `REAL` (Available locally)
- **Doppler Weather Radar**: `UNAVAILABLE` (Locally). Currently running explicitly in `SYNTHETIC` mode.
- **Lightning Mapping Array**: `UNAVAILABLE` (Locally). Currently running explicitly in `SYNTHETIC` mode.
- **NWP (GFS/NCUM)**: `UNAVAILABLE` (Locally). Currently running explicitly in `SYNTHETIC` mode.

**CONCLUSION: REAL GROUND-TRUTH TARGET DATASET CURRENTLY UNAVAILABLE.**
The system relies strictly on synthetic/demonstration generators for the targets until true files are provided. At no point do these synthetic outputs masquerade as scientifically valid real labels.

## 2. Target Definitions
The `TargetDefinition` architecture cleanly abstracts the criteria defining a positive weather event:
- **Thunderstorm Occurrence**: `is_binary=True`, configured explicitly via physical threshold (e.g., radar reflectivity > 35 dBZ).
- **Lightning Density**: `is_binary=False`, representing explicit flash density/count.

## 3. Temporal Alignment
- Forecast Origin ($T_0$) is strictly derived as the maximum timestamp within the input historical sequence.
- **Strict Leakage Prevention**: Target timestamps must be strictly strictly greater than $T_0$. The system (`DataLeakageAuditor` and `RealTargetBuilder`) physically raises `ValueError` if temporal boundaries cross.

## 4. Spatial Alignment
Target variables are gridded natively through the existing `CommonGridder`. This uses KD-Tree masking to ensure the exact same missing-data geometries observed during ingestion apply equally to the target dataset, preventing synthetic interpolation across physical data voids.

## 5. Missing-Target Semantics
- **Rule:** Missing observation ≠ Negative Class.
- Missing values (`NaN`) in the raw target arrays correctly populate as `False (0)` inside the `target_mask` tensor.
- The downstream loss function ignores these pixels, preventing the network from falsely updating weights based on unobserved domains.

## 6. Target Quality Control (QC)
The `TargetQualityController` ensures fundamental sanity on raw arrays before manifesting them as dataset labels:
- Temporal order validation.
- NaN percentage profiling.
- Impossible-value detection (e.g., -200 dBZ).
Generates a `TargetQCResult` logged into every sample's manifest.

## 7. Event-Aware Data Splitting
Random shuffling (spatial or temporal) destroys independence and introduces severe data leakage for meteorological systems.
The `EventSplitter` groups sliding windows uniquely by day/event.
- `TRAIN` = Event A (e.g., May 1)
- `VALIDATION` = Event B (e.g., May 5)
- `TEST` = Event C (e.g., May 10)
A `DataLeakageAuditor` formally verifies that no event crosses boundaries.

## 8. Leakage Auditor
Audits the overall `SampleManifest` repository to ensure:
- Zero duplicate samples.
- Zero future data in inputs.
- Zero target timestamps $\leq$ Forecast Origin.
- Zero cross-split contamination.

## 9. Baseline Definitions
Two untrained baselines are implemented in `BaselineModels`:
1. **Persistence:** The last observed input frame is copied forward into the target forecast horizon.
2. **Climatology:** Predicts a stationary historical probability mean.

## 10. Metrics Implemented
Configurable binary threshold metrics:
- Precision
- Recall / Probability of Detection (POD)
- False Alarm Rate (FAR)
- F1 Score
- Critical Success Index (CSI)
Probabilistic metrics:
- Brier Score
All metrics explicitly adhere to the `target_mask`, bypassing missing pixels natively.

## 11. Calibration
Probabilistic calibration interfaces (e.g., Brier score) have been established. However, no calibration is run because the Part 16 model remains completely untrained.

## 12. Scientific Manifest
Every evaluated slice generates a `SampleManifest` tracking:
- Provenance (strictly downgraded to `MIXED` if synthetic data touches the label).
- Metadata versioning.
- Traceable timestamps.

## 13. Current Scientific Limitations
- The provided six local satellite timestamps do not constitute a dataset capable of establishing model accuracy, generalization, calibration, or event detection skill. 
- Real metrics cannot be run because true IMD radar/lightning data is absent.
- The framework is entirely structured and unit-tested to operate correctly *the moment* real MOSDAC target arrays are ingested.
