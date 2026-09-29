# StormFusion AI — Final Dashboard Documentation

## 1. Overview
The final StormFusion AI frontend has been rebuilt from a static presentation webpage into a **Data-Centric Atmospheric Observation Console**. The primary goal is to make the application feel like a running operational system where the real scientific data is the hero, taking up ~75% of the viewport.

## 2. Core Philosophy
- **Data as the Hero**: The MapLibre visualization occupies the entire viewport, with controls and panels floating on top.
- **Scientific Honesty**: Every layer, metric, and inference explicitly discloses its scientific status. E.g., the extrapolation product carries a permanent "EXTRAPOLATED • NOT VALIDATED FORECAST" badge.
- **Robustness**: The frontend handles null API responses, 500 errors, and missing metadata without crashing, replacing white-screens-of-death with graceful fallback states (via a global `ErrorBoundary` and object optional-chaining).

## 3. Application Structure
The UI operates in four exclusive views navigated from the top command bar:
1. **LANDING**: The entry point. Explains the multimodal workflow and provides a massive "START DEMO" action to plunge the user directly into the data.
2. **SATELLITE (Nowcast Console)**: Explores the 6 real INSAT-3DS observations. Features a bottom timeline scrubber, layer toggles, and a right-hand analysis panel showing real-time scene metrics (Data Coverage, Cooling Rate, CTP).
3. **RADAR (Observation Console)**: Renders the real Mumbai DWR (Doppler Weather Radar) dataset from 2019, showcasing the independent target-building pipeline. Includes controls to toggle Reflectivity, Velocity, and Spectrum Width.
4. **SYSTEM (Architecture & Provenance)**: Explains the necessity of a multimodal approach (Radar + Satellite + Lightning + NWP) via an architecture flowchart and explicitly lists the scientific status of each component.
5. **COMMAND CENTER (Simulation Mode)**: A concept demonstrator for the intended operational product. It features a completely isolated deterministic simulation engine showing an end-to-end workflow (monitoring, detection, explanation, threat zones, and alerts) using synthetic parameters.

## 4. REAL DATA MODE vs SIMULATION MODE
The application explicitly separates the prototype evidence from the operational vision.
- **REAL DATA MODE**: Surfaces real, processed observations (Satellite, Radar) to prove that the data-ingestion and preprocessing pipeline works.
- **SIMULATION MODE**: An illustrative conceptual UI ("Command Center") using synthetic data, demonstrating how emergency responders would interact with the final validated AI outputs (e.g. multimodal threat alerts, projected threat zones).

## 5. Demo Mode
Triggered by the primary action button on the Landing page or Top Bar. It is a guided sequence of floating overlays that automate the console state to demonstrate the pipeline:
1. **01 — OBSERVE**: Demonstrates the real 2025 satellite ingestion with automatic timeline playback.
2. **02 — EXTRAPOLATION**: Demonstrates feature extraction and phase-correlation for a 30-minute deterministic extrapolation.
3. **03 — RADAR**: Switches to the 2019 Radar volume, explicitly explaining why the dates differ (not a paired training sample).
4. **04 — AI FIT**: Displays the architecture and the remaining scientific gates (Training, Calibration, Validation).

## 6. Technical Resilience
- **React Error Boundary**: Implemented in `main.tsx` to trap any uncaught `TypeError` and provide a recovery UI.
- **Safe Payload Extraction**: All backend dictionaries (`radarMeta`, `nowcastData`) are verified for `undefined` properties before accessing `.substring()` or `.toFixed()`.
- **MapLibre State Safety**: Map manipulation (e.g., `.flyTo()`) is wrapped in optional chaining, and layers verify `map.isStyleLoaded()` before injecting GeoJSON sources, preventing race conditions on rapid tab switching.
