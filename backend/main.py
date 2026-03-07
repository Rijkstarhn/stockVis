from fastapi import FastAPI

from routers.analyze import router as analyze_router


def create_app() -> FastAPI:
    app = FastAPI(title="stockVis API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(analyze_router)

    return app


app = create_app()
