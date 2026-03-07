from fastapi import APIRouter
from api.endpoints import jobs, upload, stream, download

router = APIRouter()
router.include_router(jobs.router)
router.include_router(upload.router)
router.include_router(stream.router)
router.include_router(download.router)
