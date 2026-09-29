# StormFusion AI — Common Grid Data-Integrity Audit

> **Phase 12**: Audit of the real satellite-to-common-grid transformation to verify geographic and numerical integrity, specifically addressing unintentional interpolation artifacts.

## 1. Objective
Verify whether the CommonGridder correctly translates native INSAT-3DS observations onto the 0.5-degree geographic grid without distorting physical ranges or mathematically hallucinating values in observation gaps. 

## 2. Source Data
- **Timestamps Audited**: `12:00`, `12:30`, `13:00`, `13:30`, `14:00`, `14:30` (29 May 2025)
- **Variables Audited**: `IMG_TIR1`, `IMG_WV` (L1B), `CTT`, `CTP` (L2B)
- **Characteristics**: Multi-resolution (4km IR, coarse CTP). Contains large contiguous NaN regions (outer space, cloud-free zones for CTP).

## 3. Target Grid
- **Resolution**: 0.5 degrees (~55km)
- **Bounding Box**: Lat: 8.4°N to 37.6°N, Lon: 68.7°E to 97.2°E (India BBOX)
- **Target Shape**: 59 latitudes × 58 longitudes (3,422 cells)

## 4. Source Validity vs 5. Target Validity
### Missing-Data Masking Issue
The native L1B data contains roughly **25-30% NaN values** globally across the raw arrays (primarily mapping to outer space beyond the Earth disk). The native CTP arrays contain even higher NaN percentages because Cloud Top Pressure is only valid where clouds actually exist.

Despite this, the current CommonGridder output reports **100% finite data (0.0% NaN)** for all target cells within the `[59, 58]` grid. 

## 6. Extrapolation Analysis (The `griddata` Triangulation Bug)
The `100% finite output` is a mathematical artifact of the interpolation algorithm rather than genuine satellite coverage. 

**Root Cause:**
1. The `CommonGridder` strips all `NaN` values from the source arrays to optimize `scipy.interpolate.griddata` execution (`valid = np.isfinite(...)`).
2. `griddata` constructs a Delaunay triangulation using the remaining valid coordinate points.
3. The convex hull of the remaining points spans the entire Earth disk.
4. Any missing data regions (such as clear skies for CTP, or missing scan lines) become "holes" in the point cloud.
5. Delaunay triangulation connects the edges of these holes. `griddata` then performs `linear` interpolation across the voids.

**Result**: Target grid cells falling within these data voids are quietly assigned mathematically interpolated values, inventing data where none was physically measured.

## 7. Geographic Coverage
- **Source Domain**: The native coordinate matrices map a complete hemisphere (approx -81° to +81° Lat/Lon).
- **Target Domain**: The India BBOX (8.4°N to 37.6°N, 68.7°E to 97.2°E) lies completely inside the outer convex hull of the source domain.
- Because the target grid lies deeply within the bounding hull, `griddata` treats every target point as an *interpolation* rather than an *extrapolation*. This is why `griddata` does not apply its default `fill_value=np.nan` (which only applies strictly outside the convex hull).

## 8. Numerical Range Comparison
Since `linear` interpolation computes convex combinations of neighboring points, the generated target values are strictly bounded by the native min/max values of the valid points.
- It does **not** create extreme mathematical outliers (no values shoot to infinity).
- It does **not** exceed native ranges.
- However, for variables like `CTP`, interpolating pressure smoothly across thousands of miles of clear sky produces meteorologically invalid pressure fields.

## 9. Six-Timestamp Consistency
The 100% finite masking behavior is perfectly consistent across all six timestamps. The target grid shape uniformly remains `59 × 58`, and the `0.0% NaN` output reproduces identically for every timestamp because the target grid never intersects the outer space boundary (the only region outside the valid triangulation hull).

## 10. Subsampling Analysis
The CommonGridder currently drops a significant fraction of points (e.g. keeping only every 3rd or 4th point) for massive arrays (like the 12M point VIS grid) to prevent memory exhaustion (`OOM`) during Delaunay triangulation.

While this drastically improves runtime and prevents crashing, it effectively smooths out small-scale local extrema. However, given the massive scale disparity between the 1km source and the ~50km target grid, the down-sampling does not drastically alter the regional statistical mean.

## 11. Missing-Data Handling Policy
**Current Behavior:**
- Source NaNs are dropped.
- Holes inside the data coverage are interpolated across.
- Target cells have no indication they were synthesized from distant edges.

## 12. Findings & 13. Limitations
1. **Unintended Void Filling**: The pipeline is silently generating artificial data across large missing data zones (particularly critical for CTP/CTT).
2. **Loss of Native Masks**: The genuine spatial structure of the clouds is lost because the clear-sky NaNs are discarded.

## 14. Recommended Correction (For Next Phase)
**DO NOT use this output for scientific validation or model training.**

**Required Implementation Fix:**
To correctly preserve native data masks, the `CommonGridder` must be updated to apply a maximum-distance threshold for interpolation, or it must re-apply the native NaN mask to the target grid. 
1. Use `scipy.spatial.cKDTree` to measure the distance from each target cell to the nearest *valid* source observation.
2. If the distance exceeds a physical threshold (e.g., 10-15 km), force the target cell to `NaN`.
This will retain the structural integrity of the satellite observations and correctly reflect missing data in the downstream pipeline.
