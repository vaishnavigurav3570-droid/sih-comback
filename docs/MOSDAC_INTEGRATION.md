# StormFusion AI — MOSDAC Integration Guide

> How we connect to India's Meteorological and Oceanographic Satellite Data Archival Centre (MOSDAC) for INSAT-3DS satellite data.

---

## 1. What Is MOSDAC?

MOSDAC (https://mosdac.gov.in) is operated by ISRO's Space Applications Centre (SAC). It provides:

- **INSAT-3DS** satellite imagery (our primary satellite source)
- Various derived products (cloud properties, precipitation, OLR, etc.)
- Historical and near-real-time data

Access requires **SSO credentials** (username/password) registered on the MOSDAC portal.

---

## 2. Official mdapi Client

MOSDAC provides an official Python client library called `mdapi` for programmatic data download.

### 2.1 Installation

```bash
pip install mdapi
```

> ⚠️ If `mdapi` is not available on PyPI, it may need to be installed from MOSDAC's distribution. Check https://mosdac.gov.in for the latest instructions.

### 2.2 Core Workflow

The official `mdapi` workflow requires these parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `username` | MOSDAC SSO username | (from .env) |
| `password` | MOSDAC SSO password | (from .env) |
| `datasetId` | Unique ID for the data product | See Section 4 |
| `startTime` | Start of time range | `"2026-09-28T00:00:00"` |
| `endTime` | End of time range | `"2026-09-28T12:00:00"` |
| `count` | Max number of files to return | `10` |
| `boundingBox` | Geographic region `[W, S, E, N]` | `[68.0, 6.0, 98.0, 38.0]` |
| `gId` | Granule ID (optional) | — |
| `download_settings` | Output directory, format prefs | `{"output_dir": "./data/raw"}` |

### 2.3 Pseudocode (how mdapi works conceptually)

```python
import mdapi

# Authenticate
client = mdapi.Client(username="...", password="...")

# Search for available datasets
results = client.search(
    datasetId="INSAT3DS_IMG_TIR1",
    startTime="2026-09-28T00:00:00",
    endTime="2026-09-28T06:00:00",
    boundingBox=[68.0, 6.0, 98.0, 38.0],
    count=5
)

# Download files
for item in results:
    client.download(item, output_dir="./data/raw/satellite/")
```

> ⚠️ The exact API may differ. Always check the latest `mdapi` documentation. The above is our architectural understanding.

---

## 3. Our Integration Architecture

We do NOT call `mdapi` directly from our pipeline code. Instead, we wrap it:

```
Pipeline Code
    │
    ▼
MOSDACSatelliteProvider (our adapter)
    │
    ▼
mdapi (official MOSDAC client)
    │
    ▼
MOSDAC Servers
```

### 3.1 Why Wrap It?

1. **Uniform interface** — `MOSDACSatelliteProvider` implements the same `DataProvider` interface as `RadarDataProvider`, `SyntheticDataProvider`, etc. The pipeline doesn't care which one it's talking to.
2. **Credential isolation** — Credentials are loaded from environment variables in one place and never passed further than the provider.
3. **Error handling** — We add retry logic, timeout handling, and graceful fallback to demo mode.
4. **Caching** — We can cache downloaded files locally to avoid re-downloading.
5. **Testability** — We can mock `MOSDACSatelliteProvider` in tests without needing real MOSDAC access.

### 3.2 MOSDACSatelliteProvider Interface

```python
class MOSDACSatelliteProvider(DataProvider):
    """
    Adapter around the official mdapi client for MOSDAC satellite data.
    """

    def __init__(self, username: str, password: str, cache_dir: Path):
        """Credentials from environment variables only."""
        ...

    def search_datasets(
        self,
        dataset_id: str,
        start_time: datetime,
        end_time: datetime,
        bounding_box: BoundingBox,
        count: int = 10,
    ) -> list[DatasetMetadata]:
        """Search MOSDAC for available data files."""
        ...

    def download(
        self,
        dataset_id: str,
        output_dir: Path,
        **kwargs,
    ) -> DataPayload:
        """Download a specific dataset file."""
        ...

    def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get metadata for a specific dataset."""
        ...

    def validate_connection(self) -> ConnectionStatus:
        """Check if MOSDAC credentials are valid and service is reachable."""
        ...
```

---

## 4. INSAT-3DS Data Products of Interest

These are the satellite products we plan to use for thunderstorm nowcasting:

| Product | Dataset ID (tentative) | Physical Variable | Relevance |
|---------|----------------------|-------------------|-----------|
| TIR1 (10.8 μm) | `INSAT3DS_IMG_TIR1` | Cloud-top brightness temperature | Deep convection detection |
| TIR2 (12.0 μm) | `INSAT3DS_IMG_TIR2` | Brightness temperature | Split-window technique |
| MIR (3.9 μm) | `INSAT3DS_IMG_MIR` | Mid-infrared BT | Thin cirrus, fog detection |
| VIS (0.65 μm) | `INSAT3DS_IMG_VIS` | Visible reflectance | Daytime cloud identification |
| WV (6.7 μm) | `INSAT3DS_IMG_WV` | Water vapor BT | Upper-tropospheric moisture |
| OLR | `INSAT3DS_OLR` | Outgoing longwave radiation | Deep convection proxy |
| CMT | `INSAT3DS_CMT` | Cloud motion vectors | Storm movement |
| QPE | `INSAT3DS_QPE` | Quantitative precip estimate | Rainfall intensity |

> ⚠️ **Dataset IDs are tentative.** They must be verified against the actual MOSDAC catalog. Never assume a dataset ID is correct until validated.

### 4.1 Key Satellite Features for Nowcasting

From scientific literature (references in docs), the most important satellite-derived indicators for thunderstorm nowcasting include:

1. **BT(10.8)** — Cold cloud tops indicate deep convection. Threshold ~220 K for strong storms.
2. **BT(10.8) − BT(12.0)** — Split-window difference. Helps identify overshooting tops.
3. **BT(6.7) − BT(10.8)** — Water vapor minus infrared difference. Indicates tropopause-penetrating convection.
4. **Temporal BT trends** — Rapidly cooling cloud tops suggest intensifying convection.
5. **Cloud motion vectors** — Direction and speed of storm movement.

> 📚 Source: These features are commonly referenced in IMD nowcasting literature and WMO guidelines for satellite-based convective diagnostics.

---

## 5. Credential Security

### Rules (NON-NEGOTIABLE)

| Rule | Detail |
|------|--------|
| Storage | `.env` file only (gitignored) |
| Backend access | Loaded via `os.environ` or `pydantic Settings` |
| Frontend access | ❌ NEVER. Not even via API response. |
| Logging | ❌ Never log credentials |
| Error messages | ❌ Never include credentials in error messages |
| Caching | ❌ Never persist credentials beyond current process |

### Environment Variables

```bash
MOSDAC_USERNAME=your_username_here
MOSDAC_PASSWORD=your_password_here
```

---

## 6. Download Caching Strategy

To avoid hammering MOSDAC servers and to support offline development:

1. Downloaded files are stored in `data/raw/satellite/` with a structured path:
   ```
   data/raw/satellite/{dataset_id}/{YYYY}/{MM}/{DD}/{filename}
   ```
2. Before downloading, check if the file already exists locally.
3. Metadata (timestamps, checksums) are stored in a local SQLite catalog.
4. Cache can be cleared manually or by a cleanup script.

---

## 7. Error Handling & Fallback

```
Attempt MOSDAC download
    │
    ├── Success → Use real data, mark source="MOSDAC"
    │
    ├── Auth failure → Log warning, fall back to SyntheticDataProvider
    │                   Mark source="SYNTHETIC", show warning in UI
    │
    ├── Timeout → Retry (max 3), then fall back to Synthetic
    │
    └── Dataset not found → Log error, fall back to Synthetic
```

The system NEVER crashes because MOSDAC is unavailable. It gracefully degrades to demo mode.

---

## 8. Testing Without MOSDAC Access

If you don't have MOSDAC credentials:

1. Set `STORMFUSION_MODE=DEMO` in `.env`
2. The `SyntheticDataProvider` generates deterministic synthetic satellite data
3. All synthetic data is marked as `source: "SYNTHETIC"` in every output
4. The pipeline, features, and dashboard all work identically — just with fake data

This is the default mode and requires zero external access.

---

## 9. Future Enhancements

- Real-time streaming via MOSDAC data feeds (if available)
- Multi-satellite support (INSAT-3D archive data)
- Cloud-optimized storage (COG/Zarr) for large satellite archives
- Automated data freshness monitoring
