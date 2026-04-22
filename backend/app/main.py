from fastapi import FastAPI
from app.routes.health import router as health_router

app = FastAPI(title="RelayWorks AI")

app.include_router(health_router)


@app.get("/")
def root():
    return {"message": "RelayWorks AI backend is running"}
