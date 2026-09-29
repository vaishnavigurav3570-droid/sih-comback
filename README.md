# StormFusion AI ⚡

**AIML-based Nowcasting of Thunderstorm and Lightning**

> Smart India Hackathon 2026 — Problem Statement PS26072

---

## What Is This?

StormFusion AI is a prototype system that fuses multiple atmospheric data sources — satellite imagery (INSAT-3DS via MOSDAC), Doppler weather radar, lightning observations, NWP model output, and surface station data — to produce short-range thunderstorm and lightning nowcasts at +15, +30, +60, and +90 minutes.

> ⚠️ **This is a research prototype.** It has NOT been scientifically validated against operational verification datasets. Do not use it for real-world safety decisions.

---

## Current Status

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Documentation + Architecture | ✅ Complete |
| 1 | Data providers + Synthetic data | ✅ Complete |
| 2 | Ingestion + QC + Grid pipeline | ✅ Complete |
| 3 | Feature extraction + Fusion | ✅ Complete |
| 4 | ML model (baseline) | ⚠️ Partial |
| 5 | FastAPI backend + API | ⚠️ Partial |
| 6 | React dashboard | ✅ Complete |
| 7 | MOSDAC live integration | ⚠️ Partial |
| 8 | Validation + Testing | ❌ Not Impl. |

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend, later)
- Git

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd stormfusion

# Create a Python virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Copy environment variables
cp .env.example .env

# Install dependencies (once requirements.txt exists)
pip install -r backend/requirements.txt
```

### Run in Demo Mode

```bash
# Set STORMFUSION_MODE=DEMO in your .env file (this is the default)
# Then start the backend:
cd backend
uvicorn app.main:app --reload
```

Demo mode works fully offline with synthetic data. Every simulated value is clearly labeled.

### Run the Frontend

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DATA SOURCES                         │
│  Satellite(MOSDAC)  Radar  Lightning  NWP  Stations    │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────┐
│   Data Provider Layer    │  ← Unified interface for all sources
│   (+ SyntheticProvider)  │    including offline demo data
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│   Processing Pipeline    │
│  Ingest → QC → TimeSync │
│  → GeoAlign → Grid      │
│  → Features → Fusion    │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│   Prediction Engine      │  ← Spatiotemporal ML model
│  +15/+30/+60/+90 min    │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│   Risk & Alert Layer     │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│   FastAPI Backend        │
│   React Dashboard        │
│   MapLibre Visualization │
└──────────────────────────┘
```

See [docs/PROJECT_ARCHITECTURE.md](docs/PROJECT_ARCHITECTURE.md) for the full architecture document.

---

## Key Documentation

| Document | Purpose |
|----------|---------|
| [AGENTS.md](AGENTS.md) | Rules for all AI agents working on this project |
| [docs/PROJECT_ARCHITECTURE.md](docs/PROJECT_ARCHITECTURE.md) | Full system architecture |
| [docs/MOSDAC_INTEGRATION.md](docs/MOSDAC_INTEGRATION.md) | MOSDAC satellite data integration guide |
| [docs/DATA_CONTRACT.md](docs/DATA_CONTRACT.md) | Data schemas and interfaces |
| [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) | Phased implementation roadmap |

---

## Project Principles

1. **Scientific honesty** — Never fake data or metrics.
2. **Demo always works** — Offline mode with synthetic data is always available.
3. **Transparency** — Every simulated value is labeled. Every claim cites a source.
4. **Modular design** — Swap any data source without rewriting the pipeline.
5. **Beginner-friendly** — Code and docs should be understandable.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React, TypeScript, MapLibre GL / Leaflet, TailwindCSS |
| Backend | Python, FastAPI |
| Scientific | NumPy, xarray, SciPy, scikit-learn, PyTorch |
| Geospatial | rasterio, pyproj, shapely, geopandas |
| Database | SQLite (prototype) → PostgreSQL/PostGIS (production) |
| Satellite | MOSDAC `mdapi` client |

---

## License

TBD — Academic / Research use.

---

## Team

StormFusion AI — SIH 2026 Team
