from fastapi import APIRouter

from src.api.v1.endpoints.files import router as files_router

router = APIRouter()
router.include_router(files_router)
