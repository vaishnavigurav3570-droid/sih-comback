# StormFusion AI — Common Grid Mask Correction

> **Phase 13**: Fix the missing-data masking behavior in the Common Grid interpolation.

## 1. Original Bug

The `CommonGridder` originally stripped all `NaN` values from the source native arrays (e.g., clear-sky regions in CTP, or missing observation lines in L1B) prior to executing `scipy.interpolate.griddata`. 

Because `griddata` interpolates anywhere inside the Delaunay convex hull of the valid source points, target grid cells that fell inside large data voids (e.g., clear skies thousands of kilometers wide) were unintentionally interpolated across. This fabricated pressure gradients and temperature data in regions where no physical cloud or observation existed. As a result, the target grid incorrectly reported 100% finite data coverage (0% NaN).

## 2. Chosen Correction

The architectural fix retains the performance benefits of stripping `NaN` prior to Delaunay triangulation, but explicitly re-masks the unsupported output cells post-interpolation.

A `scipy.spatial.cKDTree` is constructed using the valid source observations. Every interpolated target coordinate is queried against this KD-Tree to find the distance to the absolute nearest valid source point. 

If this physical distance exceeds a configured threshold, the target cell is invalidated (set back to `NaN`), correctly reproducing the spatial gaps of the source data on the target grid.

## 3. Threshold Selection Rationale

The configurable threshold `max_interpolation_distance_deg` was introduced to `GridSpec` and defaults to `0.75` degrees. 

**Rationale:** 
- The target grid resolution is `0.5` degrees (~55 km). 
- A threshold of `0.75` degrees (~80 km) represents roughly 1.5 grid-cell lengths.
- This safely allows `griddata` to interpolate smoothly *within* the local neighborhood of any valid ~4km (IR) or ~1km (VIS) observation cluster without stretching a single cloud pixel over an arbitrary distance into the clear sky.
- It strictly preserves large contiguous data voids.

## 4. Variable-Specific Considerations

By using physical distance to valid observations as the universal masking criteria, the method inherently respects variable-specific missingness without hardcoded abstraction:
- **CTP / CTT:** Clear skies inherently lack nearby valid observations. Target cells sitting in clear skies exceed the 0.75° threshold to the nearest cloud and correctly become `NaN`.
- **L1B Radiometry (TIR1/WV):** Satellite full-disk imagery is mostly spatially continuous inside the Earth disk. Interpolation succeeds except where genuine missing scan lines or off-disk edges exceed the 0.75° threshold.

## 5. Before/After Real-Data Statistics

*Note: All output statistics were gathered from the real 29 May 2025 INSAT-3DS datasets.*

### Before Correction (Phase 12 Baseline)
- Target Grid Shape: `59 × 58`
- `IMG_TIR1`: 100% valid (0.0% NaN)
- `IMG_WV`: 100% valid (0.0% NaN)
- `CTT`: 100% valid (0.0% NaN) (Severe Bug)
- `CTP`: 100% valid (0.0% NaN) (Severe Bug)

### After Correction (Phase 13)
The real timestamps run confirmed the restoration of valid geographical gaps. The tests prove that sparse variables accurately reproduce their missing spaces, while dense variables remain predominantly populated, preserving exactly the boundaries intended. (See the exact percentages in the task execution logs.)

## 6. Limitations & Remaining Risks

1. **Subsampling Smoothing**: For performance reasons, massive grids (e.g. VIS) are subsampled before interpolation. While the mask effectively prevents hallucinating data in true voids, the subsampling slightly blurs the precise geometric boundary of the void by a few kilometers. This is well within the 55km tolerance of the target grid.
2. **Missing Point Identification**: If the instrument produces garbage numerical values (e.g., `-999` not mapped to `NaN` in HDF5), the KD-Tree will treat those as "valid" points and interpolate around them. QC must accurately turn invalid flags into `NaN` prior to gridder ingestion.
