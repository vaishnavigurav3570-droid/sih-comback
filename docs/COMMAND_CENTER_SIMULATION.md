# StormFusion Command Center Simulation

## Purpose
The Command Center is a **Simulated Concept Demonstration** of the complete StormFusion operational workflow. It is designed to illustrate how the multimodal spatiotemporal AI will support emergency decision-making in a production setting.

## Separation from Real-Data Mode
To maintain scientific integrity and prevent confusion, the **Command Center (Simulation)** is entirely isolated from the **Real-Data Mode (Prototype)**.
- **Real-Data Mode**: Displays actual processed INSAT-3DS and DWR data. It validates the data pipeline and ML foundation.
- **Simulation Mode**: Uses deterministic, synthetic data to illustrate the final UX. It explicitly labels all AI outputs, alerts, and evidence as "SIMULATED".

## Simulation Engine
The simulation runs completely in the browser (`simulationEngine.ts`), ensuring it works even without backend connectivity. It uses deterministic interpolation based on a `timeOffsetMin` (0 to 60) to generate coherent storm states.

## Multimodal Simulation
As the primary simulated cell (`SF-014`) intensifies over time, the simulation engine coherently updates all simulated variables:
- **Satellite**: Cloud-top temperatures drop.
- **Radar**: Reflectivity core strengthens.
- **Lightning**: Flash rates increase.
- **NWP**: Local environment parameters adjust to support convection.

## AI Simulation & Threat Zones
The "Simulated AI" generates:
- Projected movement paths.
- Predictive intensity scaling.
- A geospatial **Threat Zone** polygon projecting the future location of the severe convective core.

## Alert Concept
When the simulated AI confidence reaches a critical threshold (e.g., intensity > 80, time +30m), an **Illustrative Alert** is generated. This demonstrates the future disaster-management capability of the system, explicitly explaining *why* the alert was triggered based on multimodal evidence.

## Limitations
- **Not a real forecast**: The physics and values in this mode are purely illustrative.
- **No real-time data**: This mode does not query real-time IMD feeds.
- **Local execution**: The engine relies entirely on React state and fixed deterministic paths.
