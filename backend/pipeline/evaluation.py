import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

from backend.app.models.evaluation import EvaluationMetrics, SampleManifest, BaselinePrediction

class DataLeakageAuditor:
    """Enforces strict chronological checks across the entire dataset to prevent leakage."""
    
    @staticmethod
    def audit(manifests: List[SampleManifest]) -> bool:
        """Returns True if the dataset is completely safe from chronological and split leakage."""
        sample_ids = set()
        split_map = {}
        
        for m in manifests:
            # 1. Duplicate sample check
            if m.sample_id in sample_ids:
                raise ValueError(f"Data Leakage: Duplicate sample ID {m.sample_id}")
            sample_ids.add(m.sample_id)
            
            # 2. Future observation appearing in inputs
            if any(ts > m.forecast_origin for ts in m.input_timestamps):
                raise ValueError(f"Data Leakage: Input timestamp is strictly after forecast origin.")
                
            # 3. Target timestamp before/at origin
            if m.target_timestamp <= m.forecast_origin:
                raise ValueError(f"Data Leakage: Target {m.target_timestamp} before/at origin {m.forecast_origin}")
                
            # 4. Cross-split contamination (Track event groupings by date)
            if m.split_assignment:
                event_date = m.target_timestamp.date()
                if event_date in split_map:
                    if split_map[event_date] != m.split_assignment:
                        raise ValueError(f"Data Leakage: Event {event_date} appears in multiple splits ({split_map[event_date]} and {m.split_assignment})")
                split_map[event_date] = m.split_assignment
                
        return True

class EventSplitter:
    """Partitions data chronologically while ensuring distinct meteorological events don't cross boundaries."""
    
    @staticmethod
    def split(manifests: List[SampleManifest], train_ratio: float = 0.7, val_ratio: float = 0.15) -> Dict[str, List[SampleManifest]]:
        """Splits based on explicit date-boundaries, not random shuffling."""
        if not manifests:
            return {"TRAIN": [], "VALIDATION": [], "TEST": []}
            
        manifests = sorted(manifests, key=lambda x: x.target_timestamp)
        # Group by contiguous events (simplified to Day boundaries to prevent storm-system leakage)
        unique_days = sorted(list(set([m.target_timestamp.date() for m in manifests])))
        
        train_idx = int(len(unique_days) * train_ratio)
        val_idx = int(len(unique_days) * (train_ratio + val_ratio))
        
        train_days = set(unique_days[:train_idx])
        val_days = set(unique_days[train_idx:val_idx])
        test_days = set(unique_days[val_idx:])
        
        splits = {"TRAIN": [], "VALIDATION": [], "TEST": []}
        
        for m in manifests:
            d = m.target_timestamp.date()
            if d in train_days:
                m.split_assignment = "TRAIN"
                splits["TRAIN"].append(m)
            elif d in val_days:
                m.split_assignment = "VALIDATION"
                splits["VALIDATION"].append(m)
            else:
                m.split_assignment = "TEST"
                splits["TEST"].append(m)
                
        return splits

class BaselineModels:
    """Implementations of untrained baseline nowcasting methods."""
    
    @staticmethod
    def persistence(input_sequence: np.ndarray) -> BaselinePrediction:
        """Predicts that the last observed state persists exactly."""
        # input_sequence: [Time, Heads, H, W]
        prediction = input_sequence[-1].copy()
        return BaselinePrediction(baseline_name="Persistence", prediction_tensor=prediction)
        
    @staticmethod
    def climatology(historical_mean: np.ndarray) -> BaselinePrediction:
        """Predicts the historical average probability/value."""
        return BaselinePrediction(baseline_name="Climatology", prediction_tensor=historical_mean)

class MetricCalculator:
    """Calculates scientific evaluation metrics for nowcasting."""
    
    @staticmethod
    def evaluate_binary(predictions: np.ndarray, targets: np.ndarray, masks: np.ndarray, threshold: float = 0.5) -> EvaluationMetrics:
        """Calculates metrics safely ignoring masked regions."""
        # Validate shapes
        assert predictions.shape == targets.shape == masks.shape
        
        valid_preds = (predictions[masks] > threshold).astype(int)
        valid_targets = (targets[masks] > 0.5).astype(int) # Assuming target is already binary 0/1
        
        tp = np.sum((valid_preds == 1) & (valid_targets == 1))
        fp = np.sum((valid_preds == 1) & (valid_targets == 0))
        tn = np.sum((valid_preds == 0) & (valid_targets == 0))
        fn = np.sum((valid_preds == 0) & (valid_targets == 1))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        far = fp / (tp + fp) if (tp + fp) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        
        # Critical Success Index (Hits / (Hits + False Alarms + Misses))
        csi = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0
        
        # Brier Score (Mean squared error of probabilities)
        # For BS we use the raw probabilities, not the thresholded ones
        prob_preds = predictions[masks]
        brier = np.mean((prob_preds - valid_targets) ** 2) if len(prob_preds) > 0 else 0.0
        
        return EvaluationMetrics(
            precision=float(precision),
            recall=float(recall),
            far=float(far),
            f1=float(f1),
            csi=float(csi),
            brier_score=float(brier),
            confusion_matrix={"TP": int(tp), "FP": int(fp), "TN": int(tn), "FN": int(fn)}
        )
