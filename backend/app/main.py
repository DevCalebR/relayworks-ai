from fastapi import FastAPI

from app.routes.agents import router as agents_router
from app.routes.health import router as health_router
from app.routes.projects import router as projects_router

app = FastAPI(title="RelayWorks AI")

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(agents_router)


@app.get("/")
def root():
    return {"message": "RelayWorks AI backend is running"}
