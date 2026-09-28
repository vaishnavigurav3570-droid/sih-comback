# AGENTS.md — StormFusion AI

> **This file is the single source of truth for every AI agent working on this project.**
> Read this file FIRST before writing any code, documentation, or making any architectural decision.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project Name** | StormFusion AI |
| **Problem Statement** | SIH 2026 — PS26072 |
| **Goal** | AIML-based nowcasting of thunderstorm and lightning using atmospheric observation including multiple radars, satellite, lightning, and model data |
| **Stage** | Prototype (NOT a validated operational system) |
| **Primary User** | Beginner programmer building with Google Antigravity |

---

## 2. Scientific Integrity Rules (NON-NEGOTIABLE)

These rules must NEVER be violated. Any agent that violates them is producing harmful output.

1. **Never claim synthetic data is real meteorological data.** Every synthetic/simulated value must be explicitly labeled as `SIMULATED` or `SYNTHETIC` in code, API responses, and UI.
2. **Never invent model accuracy.** Do not fabricate precision, recall, F1, POD, FAR, CSI, or any other metric. If a model has not been validated against a real held-out dataset, say so.
3. **Never invent live IMD/MOSDAC data.** If real data is unavailable, use the `SyntheticDataProvider` and mark all outputs accordingly.
4. **Never expose MOSDAC credentials to the frontend.** SSO username/password must stay server-side only.
5. **Never hardcode credentials.** All secrets go in environment variables loaded from `.env` (which is gitignored).
6. **Never reverse-engineer undocumented MOSDAC authentication.** Use the official `mdapi` client as the preferred integration path.
7. **Never call the prototype "scientifically validated"** until a real validation dataset has been used and documented.
8. **Every external scientific claim must cite a source** in project documentation (paper, IMD bulletin, textbook, etc.).
9. **Use deterministic synthetic values** for demonstrations. Do not use `random()` for scientific demos when a deterministic function (e.g., sine wave, known distribution) would be more honest and reproducible.

---

## 3. Architecture Constraints

### 3.1 Data Provider Interface

All data sources MUST implement a common interface so the prediction pipeline never cares where data came from:

```
DataProvider (abstract)
├── SyntheticDataProvider      — always available, offline demo
├── MOSDACSSatelliteProvider   — real INSAT-3DS via mdapi
├── RadarDataProvider          — Doppler Weather Radar
├── LightningDataProvider      — lightning observations
└── NWPDataProvider            — numerical weather prediction model output
```

Key methods every provider must support (conceptually):
- `search_datasets(region, time_range, **filters) → List[DatasetMetadata]`
- `download(dataset_id, **params) → DataPayload`
- `get_metadata(dataset_id) → DatasetMetadata`
- `validate_connection() → ConnectionStatus`

A `DataProviderFactory` must be used to instantiate the correct provider based on configuration.

### 3.2 Processing Pipeline

```
Data Sources → Ingestion → Quality Control → Time Synchronization
→ Geospatial Alignment → Common Grid → Feature Extraction
→ Multimodal Fusion → Spatiotemporal Model → Forecast Products
→ Risk/Alert Layer → Dashboard/API
```

Each stage is a separate module. Do not merge stages.

### 3.3 Demo Mode vs Live Mode

| Mode | Behavior |
|---|---|
| `DEMO` | All data from `SyntheticDataProvider`. Works offline. Every value labeled `SIMULATED`. |
| `LIVE` | Real data from MOSDAC/Radar/Lightning/NWP. Falls back to DEMO for any unavailable source. |

The application MUST always work in DEMO mode even if zero external services are available.

### 3.4 Database

- Start with SQLite for prototyping.
- All database access goes through a repository/service layer.
- Repository interfaces must be compatible with PostgreSQL/PostGIS migration later.
- Never write raw SQL in route handlers or business logic.

### 3.5 Frontend/Backend Separation

- **Backend:** Python + FastAPI
- **Frontend:** React + TypeScript + MapLibre GL (or Leaflet) + TailwindCSS
- Frontend and backend communicate only via documented REST API endpoints.
- No server-side rendering of React.

---

## 4. Coding Standards

### 4.1 Python (Backend + Scientific)

- Python 3.10+
- Use type hints everywhere.
- Use `pydantic` models for API request/response schemas.
- Use `abc.ABC` and `abc.abstractmethod` for interfaces.
- Use `pathlib.Path` instead of string paths.
- Use `logging` module, never `print()` for production code.
- Format with `black`. Lint with `ruff`.
- Tests with `pytest`.

### 4.2 TypeScript (Frontend)

- Strict TypeScript — no `any` types without justification.
- Functional React components with hooks.
- Meaningful component names.

### 4.3 File Organization

```
stormfusion/
├── backend/
│   ├── app/                  # FastAPI application
│   │   ├── api/              # Route handlers
│   │   ├── core/             # Config, security, dependencies
│   │   ├── models/           # Pydantic schemas + DB models
│   │   ├── services/         # Business logic
│   │   └── providers/        # Data providers (MOSDAC, Radar, etc.)
│   ├── pipeline/             # Processing pipeline stages
│   │   ├── ingestion/
│   │   ├── quality_control/
│   │   ├── time_sync/
│   │   ├── geo_alignment/
│   │   ├── common_grid/
│   │   ├── feature_extraction/
│   │   ├── fusion/
│   │   └── prediction/
│   ├── tests/
│   └── requirements.txt
├── frontend/                 # React + TypeScript app
├── docs/                     # Project documentation
├── data/                     # Local data directory (gitignored)
│   ├── raw/
│   ├── processed/
│   └── synthetic/
└── scripts/                  # Utility scripts
```

---

## 5. MOSDAC Integration Rules

1. Wrap the official `mdapi` client — do NOT rewrite its download logic.
2. Our `MOSDACSatelliteProvider` is an adapter around `mdapi`.
3. Required parameters for MOSDAC queries: `datasetId`, `startTime`, `endTime`, `count`, `boundingBox`, `gId`, `download_settings`.
4. MOSDAC credentials come from environment variables: `MOSDAC_USERNAME`, `MOSDAC_PASSWORD`.
5. Never cache credentials in application state beyond the current session.
6. Document every `datasetId` we use and what physical variable it represents.

---

## 6. Prediction Outputs

For each forecast lead time (+15, +30, +60, +90 min), the system must produce:

| Output | Type | Range |
|---|---|---|
| Thunderstorm probability | float | 0.0–1.0 |
| Lightning probability | float | 0.0–1.0 |
| Storm intensity | categorical / float | scale TBD |
| Storm movement vector | (speed_kmh, direction_deg) | — |
| Confidence | float | 0.0–1.0 |
| Sensor health | dict per source | OK / DEGRADED / UNAVAILABLE |
| Explanation/evidence | structured text | — |

In DEMO mode, all values must carry a `source: "SYNTHETIC"` flag.

---

## 7. What NOT To Do

- ❌ Do not build the ML model until the data pipeline is working.
- ❌ Do not build the dashboard until the API is working.
- ❌ Do not create fake scientific metrics.
- ❌ Do not skip error handling.
- ❌ Do not use `pip install` globally — use virtual environments.
- ❌ Do not continue to the next phase without user confirmation.
- ❌ Do not auto-commit without the user's knowledge.

---

## 8. Phase Progression

| Phase | Focus | Status |
|---|---|---|
| **Phase 0** | Documentation + Architecture | ✅ Complete |
| **Phase 1** | Data providers + Synthetic data + Interfaces | ✅ Complete |
| **Phase 2** | Ingestion + QC + Grid pipeline | ✅ Complete |
| **Phase 3** | Feature extraction + Fusion | ✅ Complete |
| **Phase 4** | ML model (baseline) | ✅ Complete |
| **Phase 5** | FastAPI backend + API | ✅ Complete |
| **Phase 6** | React dashboard | ✅ Complete |
| **Phase 7** | MOSDAC live integration | ✅ Complete |
| **Phase 8** | Validation + Testing | ✅ Complete |

**Rule: Never jump phases. Always ask the user before proceeding.**
