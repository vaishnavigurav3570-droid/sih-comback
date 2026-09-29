# StormFusion AI — Real Satellite Pipeline Integration

> **Phase 11C Documentation**: Ingestion and geospatial alignment of real INSAT-3DS multi-resolution satellite data.

---

## 1. Local Real-Data Mode
To support offline development and bypass unreliable live API downloads during prototyping, StormFusion AI supports a **local real-data mode**.

By defining `MOSDAC_LOCAL_DATA_ROOT` in the application configuration or `.env`, the `MOSDACSatelliteProvider` automatically reads local HDF5 files using the `INSAT3DSParser` instead of invoking the `mdapi.py` downloader.

- **Data is explicitly marked `REAL`**.
- The `DataSourceStatus` and provenance metadata reflect genuine ingestion.
- Missing files for requested timestamps will result in genuine failures, properly propagated up the pipeline, rather than silently falling back to synthetic placeholders.

## 2. Provider Flow & Timestamp Matching
The provider expects L1B and CTP files to exist concurrently for given timestamps. 
When asked to provide a dataset for a specific analysis time (e.g., `2025-05-29 12:00`):
1. The provider formats the timestamp into the INSAT-3DS filename pattern (`HHMM`).
2. It locates both `3SIMG_29MAY2025_{HHMM}_L1B_STD_V01R00.h5` and `3SIMG_29MAY2025_{HHMM}_L2B_CTP_V01R00.h5`.
3. It parses them sequentially using the `INSAT3DSParser`.
4. It combines both datasets using `xarray.merge()` and returns a single `DataPayload`.

## 3. Multi-Resolution Native Grids
INSAT-3DS datasets are structurally varied. The `DataPayload` produced at the ingestion stage faithfully preserves these native grids and their 2D geographic coordinate arrays:
- **VIS/SWIR:** 11264 × 11220 (1 km)
- **IR/WV:** 2816 × 2805 (4 km)
- **CTP:** 313 × 312 (coarse cloud grid)

The pipeline does **not** rely on unsafe arbitrary array reshaping (like `np.resize` or `reshape`). Instead, it treats every pixel as an absolute geographic point.

## 4. Quality Control (QC)
The `QualityController` was upgraded to process all numeric variables inside `xarray.Dataset` objects natively.
- **Continuous values** (like CTT) are checked against their physical range limits.
- **Radiometric values** (like IMG_TIR1 radiance) are skipped for physical bounds checks unless explicitly configured (since default bounds were configured for Brightness Temperatures in Kelvin), but are correctly checked for NaNs and missing values.
- **NaN propagation**: Missing values or fill values identified during parsing are accurately retained. 

*Limitation:* Since previous synthetic tests relied on arbitrary `bt_tir1` limits, the quality scores for real radiometric parameters might artificially appear 'degraded' due to off-disk bounds mismatches or heavy cloud occlusion (NaN values).

## 5. Common-Grid Conversion & Interpolation
Because the native INSAT-3DS geolocation coordinates are 2D arrays rather than orthogonal 1D arrays, `xarray`'s built-in `interp()` function cannot reproject them. 

The `CommonGridder` relies on `scipy.interpolate.griddata` to project the 2D coordinate space onto the target 1D orthogonal latitude/longitude uniform grid:
1. Coordinates and values are flattened.
2. NaNs are dropped to maximize efficiency.
3. Huge native arrays (e.g. 12M+ points for VIS) are intelligently downsampled (sub-sampled dynamically) to prevent memory overload during interpolation.
4. Data is gridded using explicitly selected methods:
   - **Continuous Physical Quantities:** Uses `linear` interpolation (e.g., CTT, SWIR).
   - **Categorical/Quality Flags:** Uses `nearest` neighbor interpolation (e.g., CSBT flags).

## 6. Target Grid Definition
The target common grid is defined by the project's standard limits:
- **Bounding Box:** India (`south=8.4, north=37.6, west=68.7, east=97.2`)
- **Resolution:** 0.5 degrees (~50-55km spacing)
- **Coordinate System:** Decimal degrees (WGS84 EPSG:4326)

*Note:* Downscaling 1km satellite imagery to a 50km uniform grid represents a substantial loss of meteorological detail. This resolution was chosen to align with the existing `CommonGridder` defaults.

## 7. Pipeline Provenance & Synthetic vs. Real Modalities
A single multimodal batch may contain both real and synthetic data.
- The `DataPayload.metadata.is_synthetic` property explicitly identifies whether the observation is REAL or SYNTHETIC.
- The satellite arrays carry an internal `source="MOSDAC"` and `is_synthetic=False` attribute tag after parsing and regridding.
- If Radar or Lightning sources are synthetic, their respective payloads will carry `is_synthetic=True`. The overall ingestion batch respects these varied provenance traits.

## 8. Limitations & Scientific Integrity
- **Scientific Validation:** This integration demonstrates *software engineering and geospatial capability*. It proves StormFusion AI can physically digest raw HDF5 files and align them. It **DOES NOT** imply that the interpolation method chosen is meteorologically ideal for training a nowcasting model, nor does it claim forecast accuracy.
- **Grid Density:** The 0.5° target grid is exceptionally coarse.
- **Radiometric Calibration:** L1B imagery provides radiance, not necessarily Brightness Temperature (BT). Further specific calibration logic might be required by the ML model.
