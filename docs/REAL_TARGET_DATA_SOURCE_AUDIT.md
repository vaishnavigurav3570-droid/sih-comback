# Real Target Data Source Audit

## 1. Local Files Discovered
- **Location:** `C:\Users\Vedant\Documents\mosdac`
- **Findings:**
  - `3SIMG_29MAY2025_1200_L1B_STD_V01R00.h5`
  - `3SIMG_29MAY2025_1200_L2B_CTP_V01R00.h5`
  - *(...10 more files for 12:30, 13:00, 13:30, 14:00, 14:30)*
- **Product Name:** INSAT-3DS Imager L1B STD & L2B CTP
- **Provenance:** **REAL**
- **Date Coverage:** 29 May 2025
- **Temporal Resolution:** 30 min
- **Spatial Resolution:** Native (mapped to 0.5° target)
- **Status:** **VERIFIED_AVAILABLE**
- **Target Suitability:** POOR (These are inputs, not occurrence labels).

## 2. MOSDAC Products Investigated
- **Radar (DWR):** SEARCH_ONLY / NOT_FOUND via mdapi.
- **Lightning:** SEARCH_ONLY / NOT_FOUND via mdapi.
- **Precipitation:** SEARCH_ONLY / NOT_FOUND via mdapi.
- **NWP (GFS/NCUM):** SEARCH_ONLY / NOT_FOUND via mdapi.

## 3. IMD Radar Investigation
- **Product Name:** IMD DWR Reflectivity
- **Variables:** Radar Reflectivity (dBZ)
- **Accessibility:** NOT_FOUND in automated repository/mdapi footprint.
- **Candidate Target:** `reflectivity > 35 dBZ` remains a valid definition, but real files are missing.

## 4. Lightning Investigation
- **Product Name:** Unknown (Damini/GLM/LI)
- **Variables:** Lightning Flashes
- **Accessibility:** NOT_FOUND in automated footprint.
- **Candidate Target:** Flash density > 0 remains structurally valid, but requires real ingest.

## 5. NWP Investigation
- **Product Name:** NCUM / GFS
- **Variables:** CAPE, CIN, Wind
- **Accessibility:** NOT_FOUND
- **Scientific Interpretation:** NWP serves as an input modality. It should not strictly act as a "ground-truth target" for actual storms, as it is just another forecast.

## 6. Exact Products Verified
- **VERIFIED FACT:** 12 `3SIMG` INSAT-3DS files are fully verified, structurally sound, and physically resident on disk for 29 May 2025.

## 7. Exact Products Search-Visible Only
- None. `discover_datasets` failed to find DWR or Lightning in the immediate mdapi index for 29 May 2025.

## 8. Download/Access Errors
- `discover_datasets` returned an empty set for radar and lightning queries.
- Previous manual/mdapi steps observed 500/503 errors and authentication rate limits (noted from earlier project phases).

## 9. 29 May 2025 & 12:00-15:00 Compatibility
- **Satellite:** EXCELLENT. Matches completely.
- **Radar/Lightning/NWP:** INCOMPATIBLE (Data does not exist locally).

## 10. Temporal & Spatial Compatibility
- Grid (59x58 at 0.5° over India) is fully compatible with IMD DWR bounds or Lightning networks (which operate natively over India).
- Temporal cadence for Radar is typically 10 minutes (Highly compatible). Lightning is continuous (Excellent compatibility).

## 11. Unresolved Gaps & Recommended Path
- **Gap:** The project lacks any real ground-truth label files to train against.
- **Recommended Next Step:** The user must manually download representative HDF5/NetCDF files for IMD Radar (DWR) and Lightning (e.g., from IMD portals or Damini archives) for 29 May 2025 and place them in the project data directories.
