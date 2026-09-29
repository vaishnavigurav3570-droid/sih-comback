# ML Dataset and DataLoader Architecture

## 1. Overview
The `StormFusionDataset` and `stormfusion_collate_fn` form the final pipeline integration layer bridging the analytical meteorological processing pipeline and the Spatiotemporal ConvLSTM network. 

Crucially, **no training has been performed**. This component exists purely to cleanly batch historical sequential data for the eventual ML loop, maintaining strict compliance with spatial masking, missing-data semantics, and chronological boundaries.

## 2. Dataset Abstraction and Lazy Loading
- The `StormFusionDataset` inherits from `torch.utils.data.Dataset`.
- It accepts a list of chronologically sorted metadata records (`timestamp`, `provenance`).
- It implements **lazy loading**: the dataset dynamically invokes a provided `load_sample_fn` exclusively when `__getitem__` is queried. This prevents the memory-catastrophic loading of the entire historical archive (e.g., thousands of INSAT-3DS HDF5 files) into a single giant GPU/CPU tensor.

## 3. Sliding-Window Logic
Configured via `SlidingWindowConfig`.
- **sequence_length**: Number of historical steps used as inputs.
- **forecast_horizon**: Number of future steps to predict.
- **stride**: The shift step between consecutive sliding windows.
- **maximum_allowed_gap**: Ensures windows are explicitly invalidated if the chronological gap between available files is larger than expected (e.g., missing radar sweeps). It strictly prevents the network from implicitly learning to "skip" hours in the input sequence.

## 4. Leakage Prevention & Temporal Splits
The system enforces robust leakage prevention through `DatasetSplitConfig`:
- **TRAIN, VALIDATION, TEST** sets are explicitly chronologically partitioned based on temporal boundaries (`train_end_time`, `val_end_time`).
- The `Dataset` filters its available metadata strictly prior to constructing sliding windows.
- It is impossible for a sliding window to straddle a partition boundary, as the records are filtered *before* the windows are calculated.
- Random dataset shuffling *prior* to splitting is strictly prohibited to preserve chronological integrity.

## 5. Sample Schema and Tensor Shapes
A single dataset sample yields:
```
features:          [Time, Channels, Height, Width]
validity_mask:     [Time, Channels, Height, Width]
target:            [Horizon, Heads, Height, Width]
target_mask:       [Horizon, Heads, Height, Width]
input_timestamps:  List[datetime]
target_timestamps: List[datetime]
provenance:        str (REAL, SYNTHETIC, MIXED)
```

## 6. DataLoader & Collation
The customized `stormfusion_collate_fn` handles batching without destroying complex metadata (like `datetime` objects and `provenance` strings).
Resulting batch shapes:
```
features:          [Batch, Time, Channels, Height, Width]
validity_mask:     [Batch, Time, Channels, Height, Width]
target:            [Batch, Horizon, Heads, Height, Width]
target_mask:       [Batch, Horizon, Heads, Height, Width]
```

## 7. Target-Mask Semantics & Missing Targets
- Part 16 model implementation relies on `StormFusionLoss`, which requires a target validity mask.
- `TargetBuilder` abstracts the logic of fetching targets.
- **Missing Target ≠ Negative Target**: If real observations for the target time are unavailable (e.g., radar is offline), the corresponding target slice values might be generated as 0, but the `target_mask` will explicitly be `0` (False). This ensures the loss function ignores these pixels rather than mistakenly penalizing the model for incorrectly forecasting a storm that "wasn't there."

## 8. Current Six-Timestamp Limitation
- The current repository contains exactly 6 real historical timestamps.
- **This is a Structural Demonstration only.**
- Attempting to train the ConvLSTM on 6 timestamps (which yields just 2 sliding windows of sequence=4, horizon=1) is scientifically invalid. It cannot measure forecast skill.
- The pipeline simply demonstrates that the tensors successfully reach the model in the correct topology.
