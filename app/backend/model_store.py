"""Mantiene y persiste modelos entrenados para reutilizar predicciones."""

import pickle
import re
from pathlib import Path

from app.config import MODEL_STORE_DIR
from app.ml.base_model import BaseModel

_TRAINED_MODELS: dict[str, BaseModel] = {}
_SAFE_LOTTERY_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _model_path(lottery: str) -> Path:
    """
    Construye una ruta segura para el artefacto persistido de una lotería.

    Args:
        lottery: Slug interno de la lotería.

    Returns:
        Ruta del archivo ``.pkl`` asociado al slug.

    Raises:
        ValueError: si el slug contiene caracteres no aptos para nombre de
            archivo controlado por la aplicación.
    """
    if not _SAFE_LOTTERY_RE.fullmatch(lottery):
        raise ValueError(f"Slug de lotería inválido para persistencia: {lottery}")
    return Path(MODEL_STORE_DIR) / f"{lottery}.pkl"


def save_trained_model(lottery: str, model: BaseModel) -> None:
    """
    Guarda un modelo entrenado para reutilizarlo en predicciones.

    Args:
        lottery: Slug de la lotería asociada al modelo.
        model: Instancia ya cargada y entrenada.
    """
    _TRAINED_MODELS[lottery] = model
    path = _model_path(lottery)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".pkl.tmp")
    with tmp_path.open("wb") as file:
        pickle.dump(model, file)
    tmp_path.replace(path)


def get_trained_model(lottery: str) -> BaseModel | None:
    """
    Obtiene el modelo entrenado de una lotería, si existe.

    Args:
        lottery: Slug de la lotería consultada.

    Returns:
        Modelo entrenado registrado en memoria o ``None`` si no existe.
    """
    model = _TRAINED_MODELS.get(lottery)
    if model is not None:
        return model

    path = _model_path(lottery)
    if not path.exists():
        return None

    with path.open("rb") as file:
        model = pickle.load(file)
    _TRAINED_MODELS[lottery] = model
    return model


def clear_trained_models(delete_files: bool = False) -> None:
    """
    Limpia modelos entrenados en memoria y opcionalmente en disco.

    Args:
        delete_files: Si es ``True``, elimina artefactos ``.pkl`` del
            directorio configurado. Se usa principalmente en pruebas.
    """
    _TRAINED_MODELS.clear()
    if not delete_files:
        return

    store_dir = Path(MODEL_STORE_DIR)
    if not store_dir.exists():
        return
    for path in store_dir.glob("*.pkl"):
        path.unlink()
