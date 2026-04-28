"""Expone el endpoint de predicción para los modelos de lotería."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.backend.api.schemas import LotteryRequest
from app.backend.selector import get_model
from app.config import (
    DEFAULT_PREDICTION_FORMAT,
    LOTTERY_PREDICTION_FORMATS,
    SERIE_PADDING,
)

router = APIRouter(prefix="/api")


@router.post("/predict")
def predict(req: LotteryRequest) -> dict:
    """
    Genera una predicción para la lotería solicitada.

    Carga y entrena el modelo en la misma petición antes de producir la
    respuesta normalizada de la API.

    Args:
        req: Payload con el slug de la lotería.

    Returns:
        Diccionario con predicción, estadísticas derivadas y timestamp UTC.

    Raises:
        HTTPException: con estado 404 si la lotería no está registrada.
    """
    try:
        model = get_model(req.lottery)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    model.load_data()
    model.train()
    result = model.predict()

    prediction_format = LOTTERY_PREDICTION_FORMATS.get(
        req.lottery,
        DEFAULT_PREDICTION_FORMAT,
    )
    main_count = int(prediction_format["main_count"])
    has_special = bool(prediction_format["has_special"])
    has_serie = bool(prediction_format["has_serie"])
    expected_len = main_count + int(has_special) + int(has_serie)

    if len(result) < expected_len:
        raise HTTPException(
            status_code=500,
            detail=(
                f"predicción inválida para '{req.lottery}': se esperaban "
                f"{expected_len} valores y se recibieron {len(result)}"
            ),
        )

    main_numbers = result[:main_count]
    cursor = main_count

    special_number = None
    if has_special:
        special_number = result[cursor]
        cursor += 1

    serie = None
    if has_serie:
        serie = str(result[cursor]).zfill(SERIE_PADDING)

    even_count = sum(1 for n in main_numbers if n % 2 == 0)
    odd_count = len(main_numbers) - even_count
    total_sum = sum(main_numbers)

    optimal_sum_min = prediction_format["optimal_sum_min"]
    optimal_sum_max = prediction_format["optimal_sum_max"]
    if optimal_sum_min is None or optimal_sum_max is None:
        sum_in_optimal_range = None
        optimal_sum_range = None
    else:
        sum_in_optimal_range = int(optimal_sum_min) <= total_sum <= int(optimal_sum_max)
        optimal_sum_range = {"min": int(optimal_sum_min), "max": int(optimal_sum_max)}

    return {
        "lottery": req.lottery,
        "prediction": {
            "main_numbers": main_numbers,
            "special_number": special_number,
            "serie": serie,
        },
        "statistics": {
            "even_count": even_count,
            "odd_count": odd_count,
            "even_odd_ratio": f"{even_count}:{odd_count}",
            "sum": total_sum,
            "sum_in_optimal_range": sum_in_optimal_range,
            "optimal_sum_range": optimal_sum_range,
            "frequency_score": 0.0,
            "pattern_score": 0.0,
        },
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
