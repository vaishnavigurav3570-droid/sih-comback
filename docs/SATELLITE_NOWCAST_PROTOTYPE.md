# Satellite Nowcast Prototype (Phase 21)

## Overview
The StormFusion AI `SatelliteNowcastPrototype` module implements a deterministic, physics-informed nowcasting baseline using real INSAT-3DS satellite data. 
**This is NOT a machine-learned prediction.** It serves as the physical baseline that future ML models must outperform.

## Implementation Principles
1. **No Synthetic Training Labels**: To strictly adhere to the project's scientific integrity rules, we do not train an ML model (ConvLSTM) using synthetic/simulated ground-truth data (radar/lightning) to predict real-world phenomena.
2. **Deterministic Derivation**: We formulate a heuristic "Storm Development Indicator" that combines multiple physical atmospheric signals known to correlate with convective initiation.
3. **Apparent Cloud Motion**: We estimate the short-term future location of clouds using global phase correlation (FFT-based) over consecutive frames of Thermal Infrared (TIR1) imagery, generating global `u` and `v` motion vectors.

## Physical Heuristics
The Storm Development Indicator combines three primary satellite-derived features:
1. **Cloud Top Cooling Rate (Temporal Difference):** Extracted from `IMG_TIR1` (or `CTT`). A rapid decrease in brightness temperature between $t-1$ and $t$ suggests a rapidly growing convective updraft.
2. **Cloud Boundary Gradients (Spatial Structure):** The magnitude of the spatial gradient of `IMG_TIR1` serves to identify distinct, structured cloud boundaries typically associated with deep convection, differentiating them from flat stratus decks.
3. **Cloud Phase/Optical Depth (Split-Window Difference):** The difference `IMG_TIR1 - IMG_TIR2` highlights regions of varying optical thickness or ice-vs-water content, which helps filter out non-convective thin cirrus clouds.

## Output Structure
The output is encapsulated into NetCDF datasets containing:
- `storm_development_indicator` (Spatial Map, 0.0 to 1.0)
- `indicator_validity_mask` (Spatial Boolean Map indicating data availability)
- `extrapolated_indicator` (The indicator shifted according to estimated motion)
- `motion_u`, `motion_v` (Global vector components)
- `motion_speed`, `motion_direction` 
- `provenance = "SATELLITE"` (strictly enforced)
- `is_calibrated_probability = False` (reflecting its heuristic nature)

## Validation against ML Framework
The prototype outputs data matching the structure required by the downstream risk and API tiers, allowing the front-end dashboard and the full integration test suite to operate seamlessly. By using this explicit baseline, we maintain complete transparency regarding system capabilities while keeping the ML architecture poised for when genuine, temporally-overlapping radar/lightning truth data becomes accessible.
