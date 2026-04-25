from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.agents import router as agents_router
from app.routes.export import router as export_router
from app.routes.health import router as health_router
from app.routes.leads import router as leads_router
from app.routes.pipeline import router as pipeline_router
from app.routes.projects import router as projects_router

app = FastAPI(title="RelayWorks AI")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(projects_router)
app.include_router(leads_router)
app.include_router(agents_router)
app.include_router(export_router)
app.include_router(pipeline_router)


@app.get("/")
def root():
    return {"message": "RelayWorks AI backend is running"}
