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
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail=f"job '{job_id}' no encontrado",
        )
    return {"job_id": job_id, **job}
