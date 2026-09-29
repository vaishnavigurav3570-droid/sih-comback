import pytest
import torch
import numpy as np

from backend.pipeline.spatiotemporal import SpatiotemporalModel, SpatiotemporalConfig, StormFusionLoss, ModelFactory

def test_model_input_output_shape():
    config = SpatiotemporalConfig(
        input_channels=11,
        sequence_length=6,
        spatial_height=59,
        spatial_width=58,
        hidden_channels=16,
        forecast_horizon=1,
        output_heads=2
    )
    
    model = ModelFactory.create_model("convlstm", config)
    
    B, T, C, H, W = 1, 6, 11, 59, 58
    features = torch.randn(B, T, C, H, W)
    validity_mask = torch.ones(B, T, C, H, W, dtype=torch.bool)
    
    out = model(features, validity_mask)
    
    assert "logits" in out
    assert out["logits"].shape == (B, config.forecast_horizon, config.output_heads, H, W)
    assert out["thunderstorm_logits"].shape == (B, config.forecast_horizon, 1, H, W)
    assert out["lightning_logits"].shape == (B, config.forecast_horizon, 1, H, W)

def test_missing_input_values_and_mask_handling():
    config = SpatiotemporalConfig(
        input_channels=3,
        sequence_length=2,
        spatial_height=10,
        spatial_width=10,
        hidden_channels=8
    )
    model = ModelFactory.create_model("convlstm", config)
    
    features = torch.full((1, 2, 3, 10, 10), float('nan'))
    validity_mask = torch.zeros((1, 2, 3, 10, 10), dtype=torch.bool)
    
    # Forward pass should not fail on NaN, model replaces with 0 and uses mask
    out = model(features, validity_mask)
    assert not torch.isnan(out["logits"]).any()

def test_loss_masking():
    loss_fn = StormFusionLoss()
    
    preds = torch.tensor([[[0.0, 10.0], [-10.0, 0.0]]]) # Logits
    targets = torch.tensor([[[0.0, 1.0], [0.0, 1.0]]])
    
    # Everything valid
    mask_all = torch.tensor([[[True, True], [True, True]]])
    loss_all = loss_fn(preds, targets, mask_all)
    
    # Only mask first row
    mask_partial = torch.tensor([[[True, True], [False, False]]])
    loss_partial = loss_fn(preds, targets, mask_partial)
    
    assert loss_all != loss_partial
    
def test_parameter_count_sanity():
    config = SpatiotemporalConfig(
        input_channels=11,
        sequence_length=6,
        spatial_height=59,
        spatial_width=58,
        hidden_channels=32,
        forecast_horizon=1,
        output_heads=2
    )
    model = ModelFactory.create_model("convlstm", config)
    total_params = sum(p.numel() for p in model.parameters())
    
    # Should be small enough for prototype (< 1M)
    assert total_params < 1_000_000

def test_deterministic_inference():
    config = SpatiotemporalConfig(
        input_channels=5,
        sequence_length=3,
        spatial_height=20,
        spatial_width=20,
        hidden_channels=16
    )
    model = ModelFactory.create_model("convlstm", config)
    model.eval()
    
    torch.manual_seed(42)
    features = torch.randn(1, 3, 5, 20, 20)
    mask = torch.ones(1, 3, 5, 20, 20, dtype=torch.bool)
    
    with torch.no_grad():
        out1 = model(features, mask)["logits"]
        out2 = model(features, mask)["logits"]
        
    assert torch.allclose(out1, out2)

def test_configurable_forecast_horizon_and_channels():
    config = SpatiotemporalConfig(
        input_channels=7,
        sequence_length=4,
        spatial_height=10,
        spatial_width=10,
        hidden_channels=16,
        forecast_horizon=3,
        output_heads=2
    )
    model = ModelFactory.create_model("convlstm", config)
    
    features = torch.randn(2, 4, 7, 10, 10)
    mask = torch.ones(2, 4, 7, 10, 10, dtype=torch.bool)
    
    out = model(features, mask)
    assert out["logits"].shape == (2, 3, 2, 10, 10) # B, horizon, heads, H, W
