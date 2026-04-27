from app.ml.base_model import BaseModel
from app.config.registry import REGISTRY


def list_lotteries() -> list[str]:
    return list(REGISTRY.keys())


def get_model(lottery: str) -> BaseModel:
    cls = REGISTRY.get(lottery)
    if cls is None:
        raise ValueError(
            f"'{lottery}': lotería no registrada. "
            f"Disponibles: {list_lotteries()}"
        )
    return cls()
