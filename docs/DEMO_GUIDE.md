# StormFusion AI — Demo Presenter Guide

This guide is designed for the presenter demonstrating StormFusion AI to the SIH judges. The application is now built as a "Data-Centric Atmospheric Observation Console."

## 1. Preparation
1. Start the FastAPI backend: `python -m uvicorn backend.app.main:app --reload`
2. Start the Vite frontend: `npm run dev`
3. Open `http://localhost:5173`.
4. Ensure the application is on the **LANDING** view.

## 2. The Demonstration Sequence

### Start: The Landing Screen
- **What appears:** A clean, data-oriented landing screen confirming this is a "REAL-DATA PROTOTYPE".
- **Presenter action:** Click the massive **▶ START DEMO** button.

---

### STAGE 01 — OBSERVE REAL SATELLITE DATA
- **What appears:** The app plunges directly into the Satellite Console. The map flies to India. The 6-frame satellite timeline begins playing automatically. The right panel updates with real scene metrics.
- **What it means:** The system has successfully ingested, quality-controlled, and grid-aligned real INSAT-3DS data from MOSDAC (29 May 2025).
- **Presenter explanation:** *"Here we are showing the first step: acquiring and processing real INSAT-3DS satellite observations. This is not synthetic data; these are six actual frames processed into our common spatiotemporal grid, with real-time metrics shown on the right."*
- **Action:** Wait for the timeline to play through. The demo will automatically pause and advance to Stage 02.

---

### STAGE 02 — FROM OBSERVATION TO EXTRAPOLATION
- **What appears:** The Extrapolated layer activates. An amber warning badge appears: "EXTRAPOLATED • NOT VALIDATED FORECAST".
- **What it means:** Phase-correlation has calculated apparent cloud motion to generate a 30-minute extrapolation.
- **Presenter explanation:** *"From raw observations, we extract features to map storm development. Using apparent cloud motion, the system generates a 30-minute extrapolation. It is critical to note this is a deterministic baseline, not a calibrated ML probability."*
- **Action:** Click **Next: Radar →**.

---

### STAGE 03 — REAL RADAR OBSERVATION
- **What appears:** The application switches to the RADAR console. The map flies to Mumbai. The 2019 DWR radar reflectivities load. A prominent red box explains "INDEPENDENT REAL OBSERVATIONS".
- **What it means:** The pipeline can successfully ingest and process independent DWR radar volumes.
- **Scientific Caveat (CRITICAL):** Point out the red box.
- **Presenter explanation:** *"We now switch to an independent radar observation from Mumbai (2019). We use this to demonstrate our radar target-building pipeline. These are two independent events; they are NOT combined as a single training sample, preserving scientific integrity."*
- **Action:** Click **Next: Architecture →**.

---

### STAGE 04 — WHERE DOES THE AI FIT?
- **What appears:** The application switches to the SYSTEM console. The Multimodal Architecture flowchart and the status checklists (Real Data Demonstrated, Implemented Architecture, Scientific Gate Remaining) are displayed.
- **What it means:** Explains what the prototype has achieved today, and what the next operational steps are.
- **Presenter explanation:** *"So where does the ML fit? We have built the complete data engineering pipeline and the ML architecture. The remaining scientific gate—which requires massive historical data acquisition—is the actual paired training and forecast validation."*
- **Action:** Click **Finish** to exit the demo and allow manual exploration.

## 3. Answering Judge Questions
If judges ask to see specific data layers:
1. Navigate to the **SATELLITE** or **RADAR** tab from the top bar.
2. In the **SATELLITE** console, use the bottom layer toggle buttons (e.g., *Cooling Rate*, *CTT Component*) to manually explore the real satellite data. Point out the right-hand analysis panel updating as you scrub the timeline.
3. In the **RADAR** console, use the layer toggles to switch between Reflectivity (REF), Velocity (VEL), and Spectrum Width (WIDTH).
