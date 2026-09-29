# Part 20A — Public Indian Real Radar + Lightning Benchmark Acquisition

## A. OSF Accessibility
The OSF project [https://osf.io/h8tw5/](https://osf.io/h8tw5/) is fully public and accessible via both the web UI and the OSF API without authentication.

## B. Files Discovered
- `Radar_raw_data/` containing raw `nc` files.
- `Lightning data/` containing `csv` files.
- `Era5 data/` containing `.csv` metadata.
- `Radiosonde data/` containing `.out` profiles.

## C. Real Radar Files Discovered
Raw polar netCDF files are available for multiple DWR stations (MUM, PTN, DLI, VSK, KKL, MBR) spanning select dates between 2005 and 2020. 

## D. Real Lightning Files Discovered
Raw event-level lightning CSV files (`may23.csv`, `jun23.csv`) are available for 2023. Aggregated statistical data is available for 2019-2022 (e.g., `latitudinal_ic_cg_jjas_19_22.csv`), but these do not contain individual event timestamps or coordinates.

## E. Mumbai Availability
Radar data for Mumbai (MUM) is available for:
- 16 April 2019 (11 consecutive timestamps spanning 20:19 to 22:59 UTC).
- 20 July 2019 (8 consecutive timestamps spanning 18:42 to 19:52 UTC).

## F. Other Station Availability
Radar data is also available for:
- DLI (Delhi)
- PTN (Patna)
- VSK (Visakhapatnam)
- KKL (Karaikal)
- MBR (Mohanbari)

## G. Candidate Event Dates
- Radar: 16 April 2019, 20 July 2019.
- Lightning: May 2023, June 2023.

## H. Selected Event and Exact Reason
**NONE.** No event could be selected because there is zero temporal overlap between the available raw radar data (2019) and raw lightning data (2023) in this public repository. Synthetically mixing 2019 radar with 2023 lightning is scientifically invalid and forbidden by project rules.

## I. Radar Variables and Units
Based on `polar_MUM190720194254.nc`:
- `REF`: Reflectivity (dBZ)
- `VEL`: Mean doppler velocity (m/s)
- `WIDTH`: Doppler spectrum width (m/s)
- Coordinates: `range` (meters), `azimuth` (degrees), `elevation` (degrees)

## J. Lightning Variables
Based on `may23.csv`:
- `FlashID`, `LightningTimeString`
- `Latitude`, `Longitude`, `Height`
- `StrokeType`, `Amplitude`, `Confidence`

## K. Temporal Overlap
0 seconds.

## L. Spatial Overlap
Not applicable due to lack of temporal overlap.

## M. Number of Usable Timestamps
0 matched timestamps.

## N. Real Target Feasibility
Impossible using only this repository without fabricating data.

## O. INSAT-3DR Matching Feasibility
Not investigated because a real radar+lightning event could not be established.

## P. Files Created/Modified
- `docs/PUBLIC_INDIAN_REAL_BENCHMARK.md`
- `docs/public_indian_benchmark_manifest.json`
- `scripts/audit_public_indian_benchmark.py`
- `backend/tests/test_public_indian_benchmark.py`

## Q. Test Count
150 collected, 150 passed.

## R. Remaining Limitations
We still lack a perfectly matched (Time + Space) real Indian radar + real Indian lightning target dataset for end-to-end scientific evaluation.

## S. Exact Next Action
STOP HERE. The public repository was audited but is scientifically incompatible for a joint multimodal ML benchmark. Must wait for the official IMD/IITM data acquisition request (Part 19B) or locate an alternative overlapping dataset.
