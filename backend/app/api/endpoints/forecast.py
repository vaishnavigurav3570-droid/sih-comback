"""
StormFusion AI — Forecast Endpoints
"""

import structlog
from backend.app.core.config import AppMode, get_settings
from backend.app.models.data_types import INDIA_BBOX
from backend.app.models.forecast import ForecastProduct
from backend.app.providers.factory import DataProviderFactory
from backend.pipeline.common_grid import GridSpec
from backend.pipeline.orchestrator import Pipeline
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()
logger = structlog.get_logger()


@router.get("/now", response_model=ForecastProduct)
async def get_nowcast(
    mode: str = Query("demo", description="Mode to run in: 'live' or 'demo'"),
    use_heuristic: bool = Query(
        True, description="Use simple heuristic instead of heavy ML model"
    ),
):
    """
    Trigger the prediction pipeline and return the latest nowcast.
    """
    logger.info("Received nowcast request", mode=mode)

    try:
        # Get settings and override mode if requested
        settings = get_settings()
        is_demo = mode.lower() == "demo"
        settings.stormfusion_mode = AppMode.DEMO if is_demo else AppMode.LIVE

        # Initialize providers
        factory = DataProviderFactory(settings)
        providers = factory.get_all_providers()

        # Configure pipeline
        # For the prototype, we use a very coarse grid (1.0 degree) to keep response times fast
        # A real system would use 0.1 or 0.05 degrees.
        grid_spec = GridSpec(bbox=INDIA_BBOX, resolution_deg=1.0)

        # We inject the use_dummy_heuristic flag into the Predictor via the Pipeline constructor
        # (Though we'll need to update orchestrator to accept predictor kwargs if we want to pass this directly,
        # or we just rely on the default behavior). For now, let's assume we can patch Predictor or just use
        # the default Predictor which auto-detects TORCH_AVAILABLE.
        # Actually, let's update Pipeline to accept predictor_kwargs.

        pipeline = Pipeline(
            providers=providers,
            grid_spec=grid_spec,
            predictor_kwargs={"use_dummy_heuristic": use_heuristic},
        )

        # Run pipeline
        result = pipeline.run()

        if not result.success:
            logger.error("Pipeline failed", errors=result.errors)
            raise HTTPException(
                status_code=500, detail=f"Pipeline execution failed: {result.errors}"
            )

        if (
            result.prediction_result is None
            or result.prediction_result.forecast_product is None
        ):
            raise HTTPException(
                status_code=500,
                detail="Pipeline succeeded but produced no forecast product",
            )

        return result.prediction_result.forecast_product

    except Exception as e:
        logger.exception("Failed to generate nowcast")
        raise HTTPException(status_code=500, detail=str(e))
