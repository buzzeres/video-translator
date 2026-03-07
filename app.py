from __future__ import annotations
import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.router import router
from config.settings import get_settings
from services.file_manager import FileManager
from services.job_store import JobStore
from workers.job_runner import WorkerPool

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    settings.workspace_dir.mkdir(parents=True, exist_ok=True)

    app = FastAPI(title="Video Translator", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    job_store = JobStore()
    file_manager = FileManager(settings)
    worker_pool = WorkerPool(settings, job_store, file_manager)

    app.state.settings = settings
    app.state.job_store = job_store
    app.state.file_manager = file_manager
    app.state.worker_pool = worker_pool

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return FileResponse("static/index.html")

    @app.on_event("shutdown")
    async def on_shutdown():
        worker_pool.shutdown()

    return app


app = create_app()

if __name__ == "__main__":
    settings = get_settings()
    logger.info(f"Starting Video Translator on http://{settings.host}:{settings.port}")
    uvicorn.run(
        "app:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )
