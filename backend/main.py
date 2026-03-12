from fastapi import FastAPI

from db import init_db
from routers.analyze import router as analyze_router
from routers.etf import router as etf_router


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title="stockVis API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(analyze_router)
    app.include_router(etf_router)

    return app


app = create_app()
