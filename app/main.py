from fastapi import FastAPI

from app.backend.api.health import router as health_router
from app.backend.api.lotteries import router as lotteries_router
from app.backend.api.predict import router as predict_router
from app.backend.api.train import router as train_router
from app.config import ENV, PORT

app = FastAPI(
    docs_url="/docs" if ENV == "development" else None,
    redoc_url=None,
)

app.include_router(health_router)
app.include_router(lotteries_router)
app.include_router(predict_router)
app.include_router(train_router)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=PORT,
        reload=ENV == "development",
    )
