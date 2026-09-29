import torch
import torch.nn as nn
from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class SpatiotemporalConfig:
    input_channels: int
    sequence_length: int
    spatial_height: int
    spatial_width: int
    hidden_channels: int = 32
    forecast_horizon: int = 1
    output_heads: int = 2
    dropout: float = 0.1
    mask_handling_strategy: str = "concatenate"

class ConvLSTMCell(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, kernel_size: int = 3):
        super().__init__()
        self.hidden_dim = hidden_dim
        padding = kernel_size // 2
        self.conv = nn.Conv2d(
            in_channels=input_dim + hidden_dim,
            out_channels=4 * hidden_dim,
            kernel_size=kernel_size,
            padding=padding
        )

    def forward(self, x: torch.Tensor, h: Optional[torch.Tensor] = None, c: Optional[torch.Tensor] = None):
        B, _, H, W = x.shape
        if h is None:
            h = torch.zeros(B, self.hidden_dim, H, W, device=x.device, dtype=x.dtype)
        if c is None:
            c = torch.zeros(B, self.hidden_dim, H, W, device=x.device, dtype=x.dtype)

        combined = torch.cat([x, h], dim=1)
        gates = self.conv(combined)
        i, f, o, g = torch.chunk(gates, 4, dim=1)
        
        i = torch.sigmoid(i)
        f = torch.sigmoid(f)
        o = torch.sigmoid(o)
        g = torch.tanh(g)
        
        c_next = f * c + i * g
        h_next = o * torch.tanh(c_next)
        
        return h_next, c_next

class SpatialEncoder(nn.Module):
    def __init__(self, in_channels: int, hidden_channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, hidden_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(hidden_channels)
        self.act1 = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(hidden_channels, hidden_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(hidden_channels)
        self.act2 = nn.ReLU(inplace=True)

    def forward(self, x: torch.Tensor):
        x = self.act1(self.bn1(self.conv1(x)))
        x = self.act2(self.bn2(self.conv2(x)))
        return x

class SpatiotemporalModel(nn.Module):
    """
    StormFusion AI - Spatiotemporal Nowcasting Model
    Consumes sequential meteorological tensors [B, T, C, H, W] and validity masks.
    """
    def __init__(self, config: SpatiotemporalConfig):
        super().__init__()
        self.config = config
        
        # Option A: Concatenate validity masks as additional input channels
        effective_in_channels = config.input_channels
        if config.mask_handling_strategy == "concatenate":
            effective_in_channels *= 2
            
        self.encoder = SpatialEncoder(in_channels=effective_in_channels, hidden_channels=config.hidden_channels)
        
        self.temporal = ConvLSTMCell(input_dim=config.hidden_channels, hidden_dim=config.hidden_channels)
        
        # Spatial Decoder / Prediction Head
        # Output [B, forecast_horizon, output_heads, H, W]
        self.decoder = nn.Conv2d(
            in_channels=config.hidden_channels, 
            out_channels=config.output_heads * config.forecast_horizon,
            kernel_size=3, 
            padding=1
        )

    def forward(self, features: torch.Tensor, validity_mask: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        features: [B, T, C, H, W]
        validity_mask: [B, T, C, H, W] boolean/float mask
        """
        B, T, C, H, W = features.shape
        
        # Explicit Missing Data Strategy
        # Fill NaNs with 0 to make it finite, rely on mask to tell the model what's observed vs missing.
        features = torch.nan_to_num(features, nan=0.0)
        
        h, c = None, None
        
        for t in range(T):
            x_t = features[:, t, :, :, :]
            m_t = validity_mask[:, t, :, :, :].float()
            
            if self.config.mask_handling_strategy == "concatenate":
                x_t = torch.cat([x_t, m_t], dim=1) # Shape: [B, 2C, H, W]
                
            enc_t = self.encoder(x_t)
            h, c = self.temporal(enc_t, h, c)
            
        # h contains the aggregated spatiotemporal state from the last timestep
        # Decode the last hidden state into predictions
        out = self.decoder(h) # [B, heads * horizon, H, W]
        
        out = out.view(B, self.config.forecast_horizon, self.config.output_heads, H, W)
        
        return {
            "logits": out, # Uncalibrated logits, NOT probabilities yet!
            "thunderstorm_logits": out[:, :, 0:1, :, :],
            "lightning_logits": out[:, :, 1:2, :, :]
        }

class StormFusionLoss(nn.Module):
    """
    Computes loss while strictly respecting target validity masks.
    """
    def __init__(self):
        super().__init__()
        # Binary Cross Entropy with Logits for robust numerical stability
        self.bce_loss = nn.BCEWithLogitsLoss(reduction='none')

    def forward(self, preds: torch.Tensor, targets: torch.Tensor, target_mask: torch.Tensor):
        """
        preds: [B, H, W] or [B, T, H, W] logits
        targets: [B, H, W] binary
        target_mask: [B, H, W] boolean mask denoting valid target points
        """
        loss_matrix = self.bce_loss(preds, targets)
        
        # Apply mask: do not calculate loss over invalid target pixels
        valid_losses = loss_matrix[target_mask]
        
        if valid_losses.numel() == 0:
            return torch.tensor(0.0, device=preds.device, requires_grad=True)
            
        return valid_losses.mean()

class ModelFactory:
    @staticmethod
    def create_model(model_type: str, config: SpatiotemporalConfig) -> nn.Module:
        if model_type.lower() == "convlstm":
            return SpatiotemporalModel(config)
        raise ValueError(f"Unsupported model type: {model_type}")
