"""
StormFusion AI — Pipeline Package

The processing pipeline transforms raw data from providers into
a clean, aligned, gridded dataset ready for feature extraction.

Pipeline stages (in order):
1. Ingestion     — reads data from providers into xarray
2. Quality Control — range checks, consistency, QC flags
3. Time Sync     — aligns all sources to common analysis times
4. Geo Alignment — reprojects to common coordinate reference system
5. Common Grid   — interpolates everything to one uniform grid
6. Feature Ext   — computes derived features (gradients, indices)
7. Fusion        — stacks everything into an ML-ready tensor
8. Prediction    — runs the ML baseline to generate ForecastProducts

Each stage is a separate module. They are designed to be run in
sequence, but each can also be tested independently.
"""
