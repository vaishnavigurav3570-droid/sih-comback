# StormFusion AI — Project Architecture

> Full system architecture for AIML-based thunderstorm and lightning nowcasting.

---

## 1. System Overview

StormFusion AI takes in data from five different types of atmospheric sensors, processes and aligns that data, feeds it into a machine learning model, and produces thunderstorm/lightning forecasts for the next 15–90 minutes.

### In Plain English

Think of it like this:

1. **Gather** — We collect data from satellites, radars, lightning detectors, weather models, and ground stations.
2. **Clean** — We check the data for errors and fix what we can.
3. **Align** — All data gets put on the same clock and the same map grid.
4. **Extract** — We pull out the important features (like "how cold is the cloud top?" or "is there rotation in the radar signal?").
5. **Fuse** — We combine all features into one unified picture.
6. **Predict** — A machine learning model looks at the fused data and predicts: "Will there be a thunderstorm here in 30 minutes?"
7. **Alert** — If the risk is high, generate alerts.
8. **Display** — Show everything on a map in a web dashboard.

---

## 2. Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                               │
│                                                                   │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌─────┐ ┌───────────┐  │
│  │ INSAT-3DS│ │ Doppler  │ │ Lightning │ │ NWP │ │ Surface   │  │
│  │ Satellite│ │ Radar    │ │ Network   │ │Model│ │ Stations  │  │
│  │ (MOSDAC) │ │          │ │           │ │     │ │ (AWS)     │  │
│  └────┬─────┘ └────┬─────┘ └─────┬─────┘ └──┬──┘ └─────┬─────┘  │
│       │             │             │           │          │         │
└───────┼─────────────┼─────────────┼───────────┼──────────┼────────┘
        │             │             │           │          │
        ▼             ▼             ▼           ▼          ▼
┌───────────────────────────────────────────────────────────────────┐
│                    DATA PROVIDER LAYER                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              DataProvider Interface (ABC)                  │   │
│  │  search_datasets()  download()  get_metadata()  validate()│   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                   │
│  Implementations:                                                │
│  ┌─────────────┐ ┌─────────────┐ ┌───────────┐ ┌─────────────┐  │
│  │ MOSDAC      │ │ Radar       │ │ Lightning │ │ Synthetic   │  │
│  │ Satellite   │ │ Provider    │ │ Provider  │ │ Provider    │  │
│  │ Provider    │ │             │ │           │ │ (Demo Mode) │  │
│  └─────────────┘ └─────────────┘ └───────────┘ └─────────────┘  │
│                                                                   │
│  DataProviderFactory → creates the right provider based on config│
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                            │
│                                                                   │
│  ┌───────────┐  ┌─────────────┐  ┌──────────────────┐           │
│  │ Ingestion │→ │ Quality     │→ │ Time             │           │
│  │           │  │ Control     │  │ Synchronization  │           │
│  └───────────┘  └─────────────┘  └────────┬─────────┘           │
│                                            │                     │
│  ┌──────────────────┐  ┌──────────────┐    │                     │
│  │ Geospatial       │← │ Common Grid  │← ──┘                    │
│  │ Alignment        │→ │ Generation   │                          │
│  └──────────────────┘  └──────┬───────┘                          │
│                               │                                   │
│  ┌──────────────────┐  ┌──────┴───────┐                          │
│  │ Feature          │← ┘              │                          │
│  │ Extraction       │                 │                          │
│  └────────┬─────────┘                 │                          │
│           │                           │                          │
│  ┌────────▼─────────┐                 │                          │
│  │ Multimodal       │                 │                          │
│  │ Fusion           │                 │                          │
│  └────────┬─────────┘                 │                          │
└───────────┼───────────────────────────┘──────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    PREDICTION ENGINE                              │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Spatiotemporal ML Model                        │  │
│  │                                                             │  │
│  │  Input: fused feature tensor (space × time × channels)     │  │
│  │                                                             │  │
│  │  Output per grid cell, per lead time (+15/+30/+60/+90):    │  │
│  │    • thunderstorm_probability  (0.0–1.0)                   │  │
│  │    • lightning_probability     (0.0–1.0)                   │  │
│  │    • storm_intensity           (categorical/float)         │  │
│  │    • storm_movement_vector     (speed, direction)          │  │
│  │    • confidence                (0.0–1.0)                   │  │
│  │    • sensor_health             (per source)                │  │
│  │    • explanation               (evidence text)             │  │
│  └─────────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                    RISK & ALERT LAYER                             │
│                                                                   │
│  Thresholds → Alert levels → Notification rules                  │
│  Color-coded risk maps for administrative regions                │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                    DELIVERY LAYER                                 │
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────────────────────────┐ │
│  │ FastAPI Backend  │    │ React + TypeScript Dashboard        │ │
│  │                  │    │                                      │ │
│  │ REST API:        │    │ • MapLibre GL map with layers       │ │
│  │ /api/v1/forecast │◄──►│ • Probability overlays              │ │
│  │ /api/v1/status   │    │ • Time slider (+15/+30/+60/+90)    │ │
│  │ /api/v1/health   │    │ • Storm tracks                      │ │
│  │ /api/v1/data     │    │ • Sensor health panel               │ │
│  └─────────────────┘    └──────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow in Detail

### 3.1 Ingestion

Each data source has its own ingestion adapter:

| Source | Format | Adapter |
|--------|--------|---------|
| INSAT-3DS Satellite | HDF5 / NetCDF | `MOSDACSatelliteProvider` wrapping `mdapi` |
| Doppler Radar | Radar-specific formats | `RadarDataProvider` |
| Lightning | Point observations | `LightningDataProvider` |
| NWP Model | GRIB2 / NetCDF | `NWPDataProvider` |
| Surface Stations | CSV / JSON | Future `StationDataProvider` |
| Demo Data | Generated in-memory | `SyntheticDataProvider` |

### 3.2 Quality Control

- Range checks (is the temperature physically possible?)
- Consistency checks (do neighboring pixels agree?)
- Missing data flagging (mark gaps, don't invent values)
- QC flags propagate through the entire pipeline

### 3.3 Time Synchronization

Different sources arrive at different times:
- Satellite: every 15–30 minutes
- Radar: every ~10 minutes (volume scan)
- Lightning: near-real-time (seconds)
- NWP: every 6–12 hours

The time sync module aligns all data to common analysis times using nearest-neighbor temporal matching with configurable tolerance windows.

### 3.4 Geospatial Alignment

All data must be projected onto the same coordinate reference system and grid:
- Target CRS: configurable (default: lat/lon WGS84)
- Target resolution: configurable (default: ~4 km for prototype)
- Reprojection uses `pyproj` and `rasterio`

### 3.5 Common Grid

After alignment, all sources are interpolated/regridded to a single uniform grid:
- Regular lat/lon grid covering the region of interest
- Each grid cell has values from all available sources
- Missing sources are flagged, not filled with fake values

### 3.6 Feature Extraction

Scientific features extracted per grid cell (examples):
- **Satellite:** Cloud-top brightness temperature (BT), BT difference (split window), OLR
- **Radar:** Reflectivity, vertically integrated liquid, echo tops, radial velocity
- **Lightning:** Flash count, flash density, polarity ratios
- **NWP:** CAPE, CIN, wind shear, moisture convergence, lifted index

### 3.7 Multimodal Fusion

Features from all sources are stacked into a single tensor:
- Shape: `(lat, lon, time_steps, channels)`
- Channels = all features from all sources
- Missing channels are masked, not zero-filled

### 3.8 Prediction

The ML model (architecture TBD — likely ConvLSTM or U-Net variant) takes the fused tensor and outputs probability/intensity maps for each lead time.

> ⚠️ The ML model is NOT implemented in Phase 0. This is the architecture plan.

---

## 4. Mode Switching

```python
# Pseudocode for provider selection
if config.mode == "DEMO":
    satellite_provider = SyntheticDataProvider(source_type="satellite")
    radar_provider = SyntheticDataProvider(source_type="radar")
    # ... all synthetic
elif config.mode == "LIVE":
    satellite_provider = MOSDACSatelliteProvider(credentials=...)
    radar_provider = RadarDataProvider(endpoint=...)
    # ... real sources, with fallback to synthetic
```

The pipeline code never knows whether data is real or synthetic — it only talks to the `DataProvider` interface.

---

## 5. Technology Decisions and Rationale

| Decision | Rationale |
|----------|-----------|
| FastAPI over Flask/Django | Async, automatic OpenAPI docs, type validation via Pydantic |
| xarray for gridded data | Standard in atmospheric science, handles NetCDF/HDF5 natively |
| MapLibre GL over Google Maps | Open-source, free, supports custom tile layers |
| SQLite → PostgreSQL path | SQLite for zero-config prototyping; PostGIS for spatial queries later |
| Abstract DataProvider | Swap data sources without touching pipeline code |
| Separate pipeline stages | Each stage is testable and replaceable independently |

---

## 6. Security Considerations

- MOSDAC credentials: server-side only, never in frontend bundle
- API endpoints: will need authentication in production
- Data files: stored outside web-accessible directories
- Environment variables: loaded from `.env`, never committed
- CORS: configured to allow only known frontend origins in production

---

## 7. Future Production Considerations

These are NOT implemented now but the architecture should not prevent them:

- Horizontal scaling of prediction workers
- Message queue (Redis/RabbitMQ) between pipeline stages
- Real-time WebSocket updates to the dashboard
- Containerization with Docker
- CI/CD pipeline
- Model versioning and A/B testing
- PostGIS for spatial queries
- Cloud deployment (GCP/AWS)
