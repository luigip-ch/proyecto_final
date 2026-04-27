import os
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    docs_url="/docs" if os.getenv("ENV") == "development" else None,
    redoc_url=None,
)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}
