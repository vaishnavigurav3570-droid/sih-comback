# Part 16 — Spatiotemporal ML Network Architecture

## 1. Model Objective
The `SpatiotemporalModel` establishes the numerical foundation for StormFusion AI's machine learning capabilities. It is designed specifically to ingest sequential multimodal meteorological tensors, aggregate spatial information into a hidden state, and forecast future severe weather states.

## 2. Input Tensor Contract
The model accepts batched Spatiotemporal features.
- **Input Shape**: `[Batch, Time, Channels, Height, Width]`
- **Example Run**: `[1, 6, 11, 59, 58]` (1 batch, 6 timestamps, 11 features, 59x58 grid).
- **Channels**: Fully configurable via `SpatiotemporalConfig.input_channels`.

## 3. Missing-Data Handling
- Missing pixels (`NaN`) in the feature tensor are safely zero-filled explicitly before computation via `torch.nan_to_num`.
- A parallel `validity_mask` of exact same shape `[B, T, C, H, W]` is supplied alongside the tensor.
- **Strategy**: Masking uses the `concatenate` technique. The binary mask is explicitly appended along the channel dimension before the first layer, transforming 11 channels into 22 channels. The network structurally learns to treat zeros differently when the accompanying mask is zero vs one.

## 4. Architecture
The architecture comprises three main blocks:
- **Spatial Encoder**: Processes each timestamp independently using a series of 2D Convolutions, Batch Normalization, and ReLU activations. Extracts local texture gradients and storm-scale features.
- **Temporal Component**: See below.
- **Spatial Decoder / Prediction Head**: Processes the final hidden temporal state via a `Conv2d` block, mapping the internal feature space to specific predictive output heads. Output shape is preserved strictly at `59 x 58`.

## 5. Temporal Component
Because weather evolves over time, the network uses a **ConvLSTMCell** for sequential temporal processing.
- The `ConvLSTMCell` sweeps over the $T$ frames, preserving the exact spatial dimension `[H, W]` inside its Cell state $C$ and Hidden state $H$ across each step. This permits tracking moving storm systems across timestamps without flattening space.

## 6. Output Heads
The model currently outputs uncalibrated **logits** across two pre-configured heads:
- **Head 0**: Thunderstorm Probability
- **Head 1**: Lightning Probability (or Density)

The model returns a dictionary of output tensors preserving spatial shape. It explicitly does **NOT** apply a naive 0.5 threshold logic natively—this is deferred to future inference calibration processes.

## 7. Forecast Horizon
- The `forecast_horizon` is natively configurable in the `SpatiotemporalConfig`.
- The current default is 1 (representing a single forecast step into the future).
- The resulting prediction shape is `[Batch, Horizon, Heads, Height, Width]`.

## 8. Loss Functions
`StormFusionLoss` uses `BCEWithLogitsLoss`.
- Logits are used natively for numerical stability (preventing vanishing gradients compared to standard BCE with Sigmoid).
- **Critical Addition**: The loss explicitly wraps operations in a spatial validity mask logic. If target labels are missing at certain pixels (e.g. offshore or incomplete radar sweeps), those pixels are dropped from the loss mean and do not emit gradients.

## 9. Configuration & Extensibility
All network topology factors are governed by `SpatiotemporalConfig`:
- Sequence length
- Input and hidden channels
- Target horizon
- Masks & dropout

## 10. Parameter Count & Performance
- **Model Type**: ConvLSTM
- **Trainable Parameters**: ~121,988
- **Footprint**: Highly optimized prototype. Fits comfortably on CPU inference (approx 0.05 seconds inference time per forward pass sequence).
- **Scaling**: Extensible to GPUs natively through standard PyTorch `.to('cuda')`.

## 11. Provenance Limitations & Target Status
- The six-timestamp sample pipeline explicitly passes `MIXED` provenance due to synthetic integration.
- The current target inputs have NO SCIENTIFIC GROUND TRUTH LABELS mapped to them.

## 12. Why the model is NOT yet validated
- The model structure is completely initialized with *randomized weights*.
- `optimizer.step()` has never been called.
- No real-world scientific metrics (CSI, FAR, POD, Brier scores) can be presented.
- Storm prediction accuracy is effectively zero until future phases procure real target data and execute a rigorous train-validation-test curriculum.
