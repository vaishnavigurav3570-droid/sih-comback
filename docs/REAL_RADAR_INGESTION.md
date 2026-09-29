# Real Mumbai DWR Radar Ingestion

## Exact Radar File
- **File:** `polar_MUM190720194254.nc`
- **Format:** NetCDF (CF/Radial standard)
- **Source:** IMD Mumbai DWR (Doppler Weather Radar)

## What Was Actually Observed
The radar file contains a single volume scan from the Mumbai DWR on **20 July 2019**, starting at **19:42:54 UTC** and ending at **19:49:37 UTC**. It contains 10 sweeps (elevation angles) and provides 3,585 rays with 1,600 range bins each. 

## Radar Metadata
- **Radar ID:** MUM
- **Latitude:** 18.9013 N
- **Longitude:** 72.8076 E
- **Altitude:** 100.0 m
- **Sweep Count:** 10 sweeps
- **Volume Start:** 2019-07-20T19:42:54+00:00
- **Volume End:** 2019-07-20T19:49:37+00:00

## Available Variables
The file contains the following physical variables:
- **REF:** Equivalent Reflectivity Factor (dBZ)
- **VEL:** Mean Doppler Velocity (m/s)
- **WIDTH:** Doppler Spectrum Width (m/s)

## Missing-Value Handling
The raw radar file uses extreme fill values (typically > 1e30) for missing observations (e.g., areas with no echoes, out of range, or beam blockage). 
- Over 93% of the volume represents missing data using these fill values.
- The `RadarParser` explicitly detects values > 1e30 and converts them strictly to `NaN`.
- Missing values are NEVER interpolated or zeroed out, preserving the observational structure.

## Target Representation
A configurable reflectivity target mask has been implemented. 
- **Default Threshold:** 35.0 dBZ
- **EVENT:** Pixel value `1.0` (REF >= Threshold)
- **NON-EVENT:** Pixel value `0.0` (REF < Threshold)
- **MISSING:** Pixel value `NaN` (Missing/Fill Value)

> **Note:** We DO NOT claim that 35 dBZ is a scientifically validated thunderstorm threshold for this project. It is currently a structural placeholder for pipeline verification.

## Spatial Compatibility
- **Radar Extent:** Latitudes ~16.73 N to 21.07 N, Longitudes ~70.53 E to 75.08 E.
- **Overlap:** The radar's spatial footprint sits perfectly within the StormFusion Common Grid (`INDIA_BBOX`: Lat 8.4-37.6 N, Lon 68.7-97.2 E).

## Temporal Compatibility
The radar observation time is `2019-07-20T19:42:54+00:00`.
When matched against the nearest theoretical INSAT-3DR satellite slot (which operate on 30-min cycles):
- **Nearest Satellite Slot:** `2019-07-20T19:30:00+00:00`
- **Offset:** 774 seconds (~12.9 minutes)
This difference easily falls within standard temporal tolerance boundaries for nowcasting integration (typically 15 minutes).

## What Is Implemented
- Complete `RadarParser` that correctly loads CF/Radial NetCDF data.
- Preservation of physical units and missing-value (`NaN`) semantics.
- Binary EVENT/NON-EVENT target representation with configurable thresholds.
- Spatial transformation engine using an Azimuthal Equidistant projection (spherical approx via `pyproj`) to convert polar coordinates (`range`, `azimuth`, `elevation`) to geographic coordinates (`latitude`, `longitude`).
- Thorough regression test suite for real-data provenance verification.

## What Remains Incomplete
- **Gridding/Rasterization:** The current parser extracts the polar coordinates and converts them to geographic lat/lon pairs but does not fully rasterize the sweep volumes directly onto the 0.5-degree `INDIA_BBOX` grid for the model. 
- **Volumetric Compositing:** We are not yet compositing the 10 elevations into a 2D composite reflectivity maximum (MAXZ).

## Scientific Limitations
**This is a real radar observation, not a validated ML ground-truth dataset.**
One radar volume cannot establish forecast skill. 
We strictly assert that no POD, FAR, CSI, F1, or other verification metrics should be derived from this single file to imply generalized predictive accuracy. 
