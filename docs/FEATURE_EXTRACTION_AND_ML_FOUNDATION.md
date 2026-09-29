# Part 15 — Feature Extraction and ML Model Foundation

## 1. Feature Registry
The pipeline utilizes an authoritative explicit registry (`FeatureMetadata`) rather than scattering definitions in model code.
Every feature explicitly defines:
- **name**: Identifier for the channel index.
- **source_modality**: e.g., `satellite`, `radar`, `lightning`, `satellite_derived`.
- **physical_meaning**: Scientific justification.
- **units**: (e.g., K, dBZ).
- **is_continuous**: Differentiates scalars vs categorical/count types.
- **depends_on_synthetic**: Tracks provenance.
- **normalization_method**: Standardized recommendation (z-score vs min-max) to be utilized by future normalization layers.

## 2. Raw Features
Mapped directly from source payloads where available:
- `IMG_TIR1` (10.8 μm Brightness Temperature)
- `IMG_TIR2` (12.0 μm Brightness Temperature)
- `IMG_WV` (6.7 μm Brightness Temperature)
- `CTP` (Cloud Top Pressure)
- `CTT` (Cloud Top Temperature)
- `synthetic_radar_reflectivity`
- `synthetic_nwp_cape`
- `synthetic_lightning_flash_density`

## 3. Derived Features
- **TIR1_TIR2_DIFF**: The "Split Window" difference. Essential for identifying optical depth, separating thin cirrus from deep convection.

## 4. Temporal Features
- **TIR1_TEMPORAL_DIFF**: Calculates `TIR1[t] - TIR1[t-1]`. Useful for identifying rapidly cooling (updraft) cloud tops.
- *Handling*: If the preceding frame is missing (or it's the first frame), the resulting temporal difference correctly propagates as `NaN`.

## 5. Spatial Features
- **TIR1_SPATIAL_GRAD**: Magnitude of the spatial gradient. Useful for detecting cloud edges, fronts, and outflow boundaries.
- *Handling*: Gradient magnitudes where the source pixel is `NaN` are strictly reverted to `NaN` to prevent hallucinated spatial structure.

## 6. Missing-Data Representation
ML tensors often fail on `NaN`. Thus, the architecture establishes:
- **tensor**: Core (T, C, H, W) numpy tensor where missing fields remain `np.nan`.
- **validity_mask**: Separate boolean mask (True = valid, False = missing) ensuring ML models can cleanly differentiate 0.0 from an unobserved pixel.

## 7. Normalization Contract
- Each feature carries a `normalization_method` flag (`z-score`, `min-max`, etc.).
- Normalization logic is strictly deferred. This prevents temporal data leakage by ensuring normalization statistics are exclusively fitted during future training splits, rather than across the holistic pipeline run.

## 8. Tensor Layout
The standardized tensor outputs from `FeatureExtractor` as:
**Shape**: `(BatchTime, Channels, Latitude, Longitude)`
- The Spatial dimensions perfectly match the `59 x 58` common grid format constraint.

## 9. Channel Ordering
Channels are mapped to indices via deterministic ordering (dict-insertion order from the `FeatureExtractor.registry`).
The `MLFeatureBatch.feature_names` array explicitly maps `[0 -> IMG_TIR1, 1 -> IMG_TIR2 ... N -> synthetic_nwp_cape]`.

## 10. Provenance
- Individual channels flag `depends_on_synthetic = True` if utilizing synthetic source code.
- The overarching `MLFeatureBatch` computes a unified provenance string (`REAL`, `SYNTHETIC`, `MIXED`).

## 11. Target/Label Contract
The future prediction logic (e.g. thunderstorm or lightning classification) will ingest the aforementioned spatial-temporal masks to derive classification labels, BUT these labels must **not** be treated as "Ground Truth" while they rely on deterministic synthetic formulas. 

## 12. Leakage Prevention
The `MLFeatureBatch` structure forces sequential alignment by `target_timestamp`. This guarantees that historical tensors never observe future data inadvertently, enforcing safe sliding-window batching techniques for spatiotemporal architectures.

## 13. Current Synthetic-Data Limitations
Because `Radar`, `Lightning`, and `NWP` modalities remain completely synthetic (no real source HDF5/GRIB data verified locally):
- Models trained on this tensor will essentially learn to fit the mathematical assumptions coded in `SyntheticDataProvider`.
- No scientific thunderstorm prediction logic can be rigorously claimed.

## 14. Model Interface
The extracted `MLFeatureBatch` serves as the exact numerical data contract (`ModelInput`) meant to feed into `BaselineCNN` or any subsequent Convolutional/Spatiotemporal PyTorch models downstream.

## 15. What is NOT yet scientifically validated
The pipeline creates the *Data Architecture* necessary for thunderstorm prediction. However, no model has been trained, hyperparameter-tuned, validated, or assessed for forecasting skill. 
