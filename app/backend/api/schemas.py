"""Contiene los esquemas Pydantic compartidos por los endpoints."""

from pydantic import BaseModel


class LotteryRequest(BaseModel):
    """Payload común para endpoints que reciben una lotería por slug."""

    lottery: str
