"""Expone el endpoint de predicción para los modelos de lotería."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.backend.api.schemas import LotteryRequest
from app.backend.selector import get_model
from app.config import OPTIMAL_SUM_MAX, OPTIMAL_SUM_MIN, SERIE_PADDING

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

    # result = [miles, centenas, decenas, unidades, serie]
    # Los 4 dígitos se devuelven por separado para preservar ceros a la izquierda.
    digits = result[:4]
    serie = result[4]

    even_count = sum(1 for d in digits if d % 2 == 0)
    odd_count = 4 - even_count
    total_sum = sum(digits)

    return {
        "lottery": req.lottery,
        "prediction": {
            "main_numbers": digits,
            "special_number": None,
            "serie": str(serie).zfill(SERIE_PADDING),
        },
        "statistics": {
            "even_count": even_count,
            "odd_count": odd_count,
            "even_odd_ratio": f"{even_count}:{odd_count}",
            "sum": total_sum,
            "sum_in_optimal_range": OPTIMAL_SUM_MIN <= total_sum <= OPTIMAL_SUM_MAX,
            "optimal_sum_range": {"min": OPTIMAL_SUM_MIN, "max": OPTIMAL_SUM_MAX},
            "frequency_score": 0.0,
            "pattern_score": 0.0,
        },
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
