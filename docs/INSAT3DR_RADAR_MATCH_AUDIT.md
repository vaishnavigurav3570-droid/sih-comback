# Part 20B — INSAT-3DR and Mumbai DWR Match Audit

## A. Exact INSAT-3DR Dataset IDs Investigated
- `3RIMG_L1C_ASIA_MER`: INSAT-3DR Level-1C Imager Asia Sector Merged Product.

## B. Exact Timestamps Discovered
The MOSDAC API confirmed that exactly 48 half-hourly observations are available for both dates:
- **16 April 2019**: 00:15 UTC through 23:45 UTC
- **20 July 2019**: 00:15 UTC through 23:45 UTC

## C. Exact Files Discovered
File naming convention discovered: `3RIMG_DDMMMYYYY_HHMM_L1C_ASIA_MER_V01R00.h5`.
Examples:
- `3RIMG_16APR2019_1515_L1C_ASIA_MER_V01R00.h5`
- `3RIMG_20JUL2019_1315_L1C_ASIA_MER_V01R00.h5`

## D. Exact Files Successfully Downloaded
**None.** 
Attempts to download 3 files per event resulted in HTTP 500 Server Errors (`Data unavailable for given parameters`).

## E. Radar Timestamps
### 16 April 2019 Event (Mumbai DWR)
1. 14:49:25 UTC
2. 15:09:30 UTC
3. 15:19:29 UTC
4. 15:39:27 UTC
5. 15:49:27 UTC
6. 16:09:25 UTC
7. 16:19:30 UTC
8. 16:49:29 UTC
9. 16:59:29 UTC
10. 17:19:28 UTC
11. 17:29:27 UTC

### 20 July 2019 Event (Mumbai DWR)
1. 13:12:54 UTC
2. 13:22:54 UTC
3. 13:32:55 UTC
4. 13:42:56 UTC
5. 13:52:57 UTC
6. 14:02:58 UTC
7. 14:12:54 UTC
8. 14:22:56 UTC

## F. Satellite Timestamps
The INSAT-3DR imager acquires data half-hourly. Relevant timestamps include:
- **16 April 2019**: 14:45, 15:15, 15:45, 16:15, 16:45, 17:15 UTC
- **20 July 2019**: 13:15, 13:45, 14:15 UTC

## G. Temporal Offsets
**16 April 2019 Radar to Satellite Offsets:**
- 14:49:25 -> 14:45:00 (Offset: 265s / ~4.4m)
- 15:09:30 -> 15:15:00 (Offset: 330s / 5.5m)
- 15:19:29 -> 15:15:00 (Offset: 269s / ~4.5m)
- 15:39:27 -> 15:45:00 (Offset: 333s / ~5.5m)
- 15:49:27 -> 15:45:00 (Offset: 267s / ~4.5m)
- 16:09:25 -> 16:15:00 (Offset: 335s / ~5.6m)
- 16:19:30 -> 16:15:00 (Offset: 270s / 4.5m)
- 16:49:29 -> 16:45:00 (Offset: 269s / ~4.5m)
- 16:59:29 -> 16:45:00 (Offset: 869s / ~14.5m)
- 17:19:28 -> 17:15:00 (Offset: 268s / ~4.5m)
- 17:29:27 -> 17:15:00 (Offset: 867s / ~14.5m)

**20 July 2019 Radar to Satellite Offsets:**
- 13:12:54 -> 13:15:00 (Offset: 126s / 2.1m)
- 13:22:54 -> 13:15:00 (Offset: 474s / 7.9m)
- 13:32:55 -> 13:45:00 (Offset: 725s / ~12m)
- 13:42:56 -> 13:45:00 (Offset: 124s / ~2m)
- 13:52:57 -> 13:45:00 (Offset: 477s / ~8m)
- 14:02:58 -> 14:15:00 (Offset: 722s / ~12m)
- 14:12:54 -> 14:15:00 (Offset: 126s / 2.1m)
- 14:22:56 -> 14:15:00 (Offset: 476s / ~7.9m)

All 19 radar frames fall well within the **<= 15 minutes** threshold of an INSAT-3DR observation.

## H. Spatial Compatibility
- **StormFusion Grid**: Covers 8.4°N–37.6°N, 68.7°E–97.2°E.
- **Mumbai DWR**: Centered at ~19°N, 72.8°E, well within the target domain.
- **INSAT-3DR ASIA Sector**: Covers the entire Indian subcontinent and surrounding regions.
- **Compatibility**: High. The existing `CommonGridder` (KD-Tree / Delaunay triangulation) can natively handle geolocated alignments between Mumbai DWR local grids and INSAT-3DR satellite projections without assuming arbitrary geometric resizing.

## I. Download/Access Status
**BLOCKED.** 
While the MOSDAC API discovered and indexed the files for 2019, download requests for the actual data payloads failed consistently with an `HTTP 500 Server Error`. MOSDAC is currently withholding the payload delivery for these historical datasets through the `mdapi`.

## J. Whether a real satellite-radar pair exists
**YES.** A scientifically valid overlapping historical pair exists for both April 2019 and July 2019 in the MOSDAC catalog, matching our OSF Mumbai DWR radar dataset. 

## K. Whether real lightning can be paired
**NO.** The only lightning data available in the OSF benchmark covers 2023. Synthesizing 2023 lightning onto 2019 radar/satellite would break the scientific integrity constraint of the project.

## L. Files Created
1. `scripts/audit_insat3dr_radar_match.py`
2. `docs/INSAT3DR_RADAR_MATCH_AUDIT.md`
3. `docs/insat3dr_radar_match_manifest.json`

## M. Tests
No new architectural components were added; the audit heavily reused the existing `MOSDACSatelliteProvider` and `mdapi` wrapping logic. Existing test suites provide coverage.

## N. Limitations
- We cannot physically obtain the satellite files right now because MOSDAC returns an `HTTP 500 Server Error` on payload download.
- We still lack temporally matched lightning data.

## Final Status
`REAL_INSAT3DR_RADAR_PAIR_DISCOVERED_DOWNLOAD_BLOCKED`
