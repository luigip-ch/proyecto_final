"""Expone endpoints para encolar y consultar entrenamientos de modelos."""

import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.backend.api.schemas import LotteryRequest
from app.backend.selector import get_model

router = APIRouter(prefix="/api")

# Registro en memoria de trabajos de entrenamiento.
# Estructura: { job_id: { "status": str, "lottery": str, "error": str|None } }
_jobs: dict[str, dict] = {}


@router.post("/train", status_code=202)
def train(req: LotteryRequest, background_tasks: BackgroundTasks) -> dict:
    """
    Encola el entrenamiento asíncrono del modelo de una lotería.

    Args:
        req: Payload con el slug de la lotería a entrenar.
        background_tasks: Administrador de tareas en segundo plano de FastAPI.

    Returns:
        Diccionario con identificador del trabajo, estado inicial y lotería.

    Raises:
        HTTPException: con estado 404 si la lotería no está registrada.
    """
    try:
        model = get_model(req.lottery)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "queued",
        "lottery": req.lottery,
        "error": None,
    }

    def _run_training() -> None:
        """
        Ejecuta el ciclo de entrenamiento y actualiza el estado del trabajo.

        Los errores se capturan para dejar el trabajo marcado como ``failed``
        junto con el mensaje de excepción.
        """
        _jobs[job_id]["status"] = "running"
        try:
            model.load_data()
            model.train()
            _jobs[job_id]["status"] = "completed"
        except Exception as exc:  # noqa: BLE001
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["error"] = str(exc)

    background_tasks.add_task(_run_training)

    return {"job_id": job_id, "status": "queued", "lottery": req.lottery}


@router.get("/train/{job_id}/status")
def train_status(job_id: str) -> dict:
    """
    Consulta el estado de un trabajo de entrenamiento previamente encolado.

    Args:
        job_id: Identificador UUID devuelto por ``POST /api/train``.

    Returns:
        Diccionario con identificador, estado, lotería y posible error.

    Raises:
        HTTPException: con estado 404 si el trabajo no existe.
    """
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"job '{job_id}' no encontrado",
        )
    return {"job_id": job_id, **job}
