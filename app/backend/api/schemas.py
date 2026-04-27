from pydantic import BaseModel


class LotteryRequest(BaseModel):
    lottery: str
