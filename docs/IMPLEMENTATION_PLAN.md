# StormFusion AI — Implementation Plan

> Phased roadmap from empty workspace to working prototype.

---

## Overview

This plan breaks the entire project into 8 phases. Each phase is self-contained and produces something testable. **No phase should be started without completing the previous one and getting user confirmation.**

---

## Phase 0: Documentation & Architecture ✅ COMPLETE

**Goal:** Establish the project foundation before writing any code.

**Deliverables:**
- [x] `AGENTS.md` — persistent rules for all AI agents
- [x] `README.md` — project overview
- [x] `docs/PROJECT_ARCHITECTURE.md` — full system architecture
- [x] `docs/MOSDAC_INTEGRATION.md` — MOSDAC satellite integration guide
- [x] `docs/DATA_CONTRACT.md` — data schemas and interfaces
- [x] `docs/IMPLEMENTATION_PLAN.md` — this document
- [x] `.gitignore` — version control exclusions
- [x] `.env.example` — environment variable template

**Exit Criteria:** User has reviewed and approved all documentation.

---

## Phase 1: Data Providers & Synthetic Data

**Goal:** Build the data provider interfaces and a working `SyntheticDataProvider` so we have data to work with immediately.

**Deliverables:**
1. **Python project setup**
   - `backend/` directory structure
   - `requirements.txt` with pinned versions
   - Virtual environment setup
   - Basic `pyproject.toml` or `setup.cfg`

2. **Core data models** (from DATA_CONTRACT.md)
   - `backend/app/models/data_types.py` — BoundingBox, DataSourceType, enums
   - `backend/app/models/metadata.py` — DatasetMetadata, ConnectionStatus
   - `backend/app/models/payload.py` — DataPayload, LightningDataPayload
   - `backend/app/models/forecast.py` — ForecastProduct, GridCellForecast

3. **DataProvider interface**
   - `backend/app/providers/base.py` — abstract DataProvider class
   - `backend/app/providers/factory.py` — DataProviderFactory

4. **SyntheticDataProvider**
   - `backend/app/providers/synthetic.py`
   - Generates deterministic (not random) synthetic data for:
     - Satellite brightness temperature fields
     - Radar reflectivity fields
     - Lightning flash patterns
     - NWP fields (CAPE, wind shear, etc.)
   - All outputs clearly marked `is_synthetic=True`
   - Works completely offline

5. **Tests**
   - Test that SyntheticDataProvider implements the interface
   - Test that data shapes match the contract
   - Test that all outputs carry synthetic flags

**Estimated Effort:** 2–3 sessions

**Exit Criteria:**
- `python -m pytest` passes all tests
- SyntheticDataProvider can generate sample data for all source types
- Data matches the contract in DATA_CONTRACT.md

---

## Phase 2: Ingestion + Quality Control + Grid Pipeline

**Goal:** Build the processing pipeline that takes raw data and produces a clean, aligned, gridded dataset.

**Deliverables:**
1. **Ingestion module**
   - `backend/pipeline/ingestion/` — reads data from providers into xarray
   - Handles HDF5, NetCDF formats (for real data later)
   - Passes through synthetic data unchanged

2. **Quality Control module**
   - `backend/pipeline/quality_control/` — range checks, consistency checks
   - Adds QC flags to data
   - Does NOT invent data to fill gaps

3. **Time Synchronization module**
   - `backend/pipeline/time_sync/` — aligns all sources to common analysis times
   - Nearest-neighbor temporal matching
   - Configurable tolerance windows

4. **Geospatial Alignment module**
   - `backend/pipeline/geo_alignment/` — reprojects to common CRS
   - Uses pyproj for coordinate transforms

5. **Common Grid module**
   - `backend/pipeline/common_grid/` — interpolates all sources to uniform grid
   - Configurable grid resolution
   - Handles missing sources gracefully

6. **Integration test**
   - Synthetic data → full pipeline → clean gridded output
   - Verify output shapes, coordinates, metadata

**Estimated Effort:** 3–4 sessions

**Exit Criteria:**
- Synthetic data flows through the entire pipeline
- Output is a clean xarray.Dataset on a regular lat/lon grid
- QC flags are present and correct

---

## Phase 3: Feature Extraction & Multimodal Fusion

**Goal:** Extract scientifically meaningful features and combine them into a single tensor.

**Deliverables:**
1. **Feature extraction module**
   - `backend/pipeline/feature_extraction/`
   - Satellite features: BT, BT differences, temporal trends
   - Radar features: reflectivity, VIL, echo tops
   - Lightning features: flash density, polarity ratios
   - NWP features: CAPE, CIN, wind shear, moisture convergence

2. **Multimodal fusion module**
   - `backend/pipeline/fusion/`
   - Stacks all features into a single tensor
   - Shape: `(lat, lon, time_steps, channels)`
   - Handles missing channels with masks

3. **Feature documentation**
   - Document each feature: name, units, scientific rationale, source paper
   - Add to `docs/FEATURES.md`

**Estimated Effort:** 2–3 sessions

**Exit Criteria:**
- Feature extraction produces documented, physically meaningful features
- Fusion produces a correctly shaped tensor
- All features are documented with scientific rationale

---

## Phase 4: ML Model (Baseline)

**Goal:** Build a simple baseline ML model. Not expected to be accurate — just to prove the architecture works end-to-end.

**Deliverables:**
1. **Prediction module**
   - `backend/pipeline/prediction/`
   - Abstract model interface
   - Baseline model (could be simple ConvNet, random forest on features, or rule-based)

2. **Training script** (if using ML)
   - Train on synthetic data (clearly labeled as such)
   - Save model checkpoints

3. **Inference pipeline**
   - Takes fused tensor → produces ForecastProduct
   - Outputs for all lead times (+15, +30, +60, +90)

4. **Evaluation framework**
   - Metrics: POD, FAR, CSI, Brier Score (standard meteorological verification)
   - Clearly state: "Evaluated on synthetic data only — NOT validated"

**Estimated Effort:** 3–4 sessions

> ⚠️ **Important:** No accuracy claims until validated on real data. The model trained on synthetic data proves the pipeline works, nothing more.

**Exit Criteria:**
- Model produces forecast outputs in the correct schema
- Evaluation framework is in place (even if metrics are meaningless on synthetic data)
- Documentation clearly states validation status

---

## Phase 5: FastAPI Backend & API

**Goal:** Expose the pipeline as a REST API.

**Deliverables:**
1. **FastAPI application**
   - `backend/app/main.py` — app setup, CORS, middleware
   - `backend/app/api/v1/` — versioned routes

2. **API endpoints**
   | Method | Path | Description |
   |--------|------|-------------|
   | GET | `/api/v1/health` | System health + sensor status |
   | GET | `/api/v1/forecast` | Get latest forecast for a region |
   | GET | `/api/v1/forecast/{id}` | Get specific forecast by ID |
   | GET | `/api/v1/data/status` | Data provider health |
   | POST | `/api/v1/forecast/run` | Trigger a new forecast run |

3. **Database layer**
   - SQLite for storing forecast history
   - Repository pattern (compatible with PostgreSQL later)

4. **API documentation**
   - Auto-generated OpenAPI/Swagger docs
   - Additional `docs/API.md`

**Estimated Effort:** 2–3 sessions

**Exit Criteria:**
- API serves forecast data in the correct schema
- Health endpoints work
- Demo mode works through the API
- OpenAPI docs are accessible at `/docs`

---

## Phase 6: React Dashboard

**Goal:** Build the visualization frontend.

**Deliverables:**
1. **React + TypeScript project setup**
   - Vite-based setup
   - TailwindCSS configured

2. **Map component**
   - MapLibre GL (or Leaflet) showing India
   - Probability overlay layers (color-coded)
   - Time slider for lead times

3. **Dashboard panels**
   - Forecast summary card
   - Sensor health status
   - Storm track visualization
   - Clear "DEMO MODE" / "SIMULATED" indicators

4. **API integration**
   - Fetch from FastAPI backend
   - Loading states, error handling

**Estimated Effort:** 3–4 sessions

**Exit Criteria:**
- Map shows probability overlays
- Time slider switches between lead times
- Demo mode is clearly indicated
- Dashboard looks professional (not a toy)

---

## Phase 7: MOSDAC Live Integration

**Goal:** Connect to real MOSDAC satellite data.

**Deliverables:**
1. **MOSDACSatelliteProvider implementation**
   - Wraps `mdapi` client
   - Implements full DataProvider interface
   - Download caching
   - Error handling + fallback

2. **Real data pipeline test**
   - Download real INSAT-3DS data
   - Run through the full pipeline
   - Compare with synthetic data outputs

3. **Hybrid mode**
   - Some sources real, some synthetic
   - UI shows which sources are live vs. synthetic

**Estimated Effort:** 2–3 sessions

> ⚠️ Requires MOSDAC credentials. Cannot be completed without them.

**Exit Criteria:**
- Real satellite data flows through the pipeline
- Fallback to synthetic works when MOSDAC is unavailable
- Data source attribution is correct in all outputs

---

## Phase 8: Validation & Testing

**Goal:** Validate the system against real weather events (if data is available).

**Deliverables:**
1. **Validation dataset** — Real thunderstorm cases from historical data
2. **Verification metrics** — POD, FAR, CSI, lead time accuracy
3. **Performance report** — Honest assessment of model skill
4. **Final documentation** — Updated architecture, known limitations, future work

**Estimated Effort:** Variable (depends on data availability)

**Exit Criteria:**
- Honest performance report with real metrics
- Known limitations documented
- Presentation-ready for SIH evaluation

---

## Summary Timeline

```
Phase 0 ████████████████ ← YOU ARE HERE (Complete)
Phase 1 ░░░░░░░░░░░░░░░░ ← NEXT
Phase 2 ░░░░░░░░░░░░░░░░░░░░
Phase 3 ░░░░░░░░░░░░░░░░
Phase 4 ░░░░░░░░░░░░░░░░░░░░
Phase 5 ░░░░░░░░░░░░░░░░
Phase 6 ░░░░░░░░░░░░░░░░░░░░
Phase 7 ░░░░░░░░░░░░░░░░
Phase 8 ░░░░░░░░░░░░░░░░░░░░░░░░
```

> **Total estimated effort:** 20–28 working sessions, assuming ~2–3 hours per session.

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-28 | Start with documentation, not code | Prevents architectural mistakes that are expensive to fix later |
| 2026-09-28 | SQLite for prototype DB | Zero configuration, good enough for prototype |
| 2026-09-28 | Synthetic data first | Unblocks all pipeline development without external dependencies |
| 2026-09-28 | Wrap mdapi, don't rewrite | Respect the official API; reduce maintenance burden |
