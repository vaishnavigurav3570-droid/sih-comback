import os
import sys
import numpy as np
from datetime import datetime, timezone
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.pipeline.orchestrator import Pipeline
from backend.pipeline.common_grid import GridSpec
from backend.app.providers.factory import DataProviderFactory
from backend.app.models.data_types import BoundingBox

def calculate_metrics(predicted_probs: np.ndarray, truth_binary: np.ndarray, threshold: float = 0.5):
    """Calculate standard meteorological verification metrics."""
    pred_binary = (predicted_probs >= threshold).astype(int)
    truth_binary = truth_binary.astype(int)
    
    hits = np.sum((pred_binary == 1) & (truth_binary == 1))
    false_alarms = np.sum((pred_binary == 1) & (truth_binary == 0))
    misses = np.sum((pred_binary == 0) & (truth_binary == 1))
    correct_negatives = np.sum((pred_binary == 0) & (truth_binary == 0))
    
    pod = hits / (hits + misses) if (hits + misses) > 0 else 0.0
    far = false_alarms / (hits + false_alarms) if (hits + false_alarms) > 0 else 0.0
    csi = hits / (hits + misses + false_alarms) if (hits + misses + false_alarms) > 0 else 0.0
    
    # Brier Score (Mean Squared Error of probabilities)
    brier_score = np.mean((predicted_probs - truth_binary) ** 2)
    
    return {
        "POD": pod,
        "FAR": far,
        "CSI": csi,
        "BrierScore": brier_score,
        "Hits": int(hits),
        "FalseAlarms": int(false_alarms),
        "Misses": int(misses)
    }

def run_validation():
    print("========================================")
    print(" StormFusion AI - Phase 8 Validation Run")
    print("========================================")
    print("NOTE: Real MOSDAC data download failed due to 503 Server Error.")
    print("Falling back to SYNTHETIC validation for pipeline verification.")
    print("========================================\n")
    
    from backend.app.core.config import get_settings
    
    # Get providers, explicitly forcing synthetic fallback since MOSDAC fails
    factory = DataProviderFactory(get_settings())
    providers = factory.get_all_providers()
    orchestrator = Pipeline(providers=providers, predictor_kwargs={'use_dummy_heuristic': True})
    
    bbox = BoundingBox(south=18.0, north=20.0, west=72.0, east=74.0)
    analysis_time = datetime.now(timezone.utc)
    
    print("Running pipeline to generate synthetic forecast...")
    forecast_result = orchestrator.run(
        analysis_time=analysis_time,
        region=bbox,
    )
    
    forecast_product = forecast_result.prediction_result.forecast_product if forecast_result.prediction_result else None
    if not forecast_product:
        print("Failed to generate forecast product.")
        return
        
    print(f"Generated {len(forecast_product.grid_forecasts)} grid forecasts.")
    
    # We will simulate a "truth" mask to evaluate the metrics against.
    # In reality, this would be a future radar/lightning observation.
    print("Simulating synthetic 'truth' observations for evaluation...")
    
    # Create arrays for metrics
    predictions_ts = []
    truth_ts = []
    
    for cell in forecast_product.grid_forecasts:
        # Get the prediction
        pred = cell.thunderstorm_probability
        predictions_ts.append(pred)
        
        # Simulate a truth value that is somewhat correlated with the prediction
        # so our synthetic model shows "skill".
        # We add some noise to make it realistic.
        noise = np.random.normal(0, 0.2)
        actual_val = np.clip(pred + noise, 0, 1)
        # Binary truth (did a thunderstorm happen or not)
        truth_binary = 1 if actual_val >= 0.5 else 0
        truth_ts.append(truth_binary)
        
    predictions_ts = np.array(predictions_ts)
    truth_ts = np.array(truth_ts)
    
    metrics = calculate_metrics(predictions_ts, truth_ts, threshold=0.5)
    
    print("\n--- Validation Metrics (SYNTHETIC MODE) ---")
    print(f"Probability of Detection (POD) : {metrics['POD']:.3f} (Ideal: 1.0)")
    print(f"False Alarm Ratio (FAR)        : {metrics['FAR']:.3f} (Ideal: 0.0)")
    print(f"Critical Success Index (CSI)   : {metrics['CSI']:.3f} (Ideal: 1.0)")
    print(f"Brier Score                    : {metrics['BrierScore']:.3f} (Ideal: 0.0)")
    print(f"Hits: {metrics['Hits']}, Misses: {metrics['Misses']}, False Alarms: {metrics['FalseAlarms']}")
    print("-------------------------------------------\n")
    
    print("⚠️ WARNING: These metrics are generated using a heuristic baseline model")
    print("and synthetic proxy truths. They DO NOT represent real-world predictive skill.")
    print("The system is structurally validated, but scientifically unvalidated.")
    print("\nValidation run complete.")

if __name__ == "__main__":
    run_validation()
