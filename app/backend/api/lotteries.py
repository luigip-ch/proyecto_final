from fastapi import APIRouter

from app.backend.selector import list_lotteries
from app.config import LOTTERY_DISPLAY_NAMES

router = APIRouter(prefix="/api")


@router.get("/lotteries")
def lotteries() -> dict:
    items = [
        {
            "id": key,
            "name": LOTTERY_DISPLAY_NAMES.get(key, key.capitalize()),
        }
        for key in list_lotteries()
    ]
    return {"lotteries": items}
