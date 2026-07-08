from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.core.config import settings
from src.core.database import get_session
from src.schemas.alert import AlertItem
from src.schemas.file import FileItem, FileUpdate
from src.services.file import create_file, delete_file, get_file, list_alerts, list_files, update_file
from src.tasks import scan_file_for_threats

router = APIRouter()


@router.get("/files", response_model=list[FileItem])
async def list_files_view(session: AsyncSession = Depends(get_session)):
    return await list_files(session=session)


@router.get("/alerts", response_model=list[AlertItem])
async def list_alerts_view(session: AsyncSession = Depends(get_session)):
    return await list_alerts(session=session)


@router.post("/files", response_model=FileItem, status_code=201)
async def create_file_view(
    title: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    file_item = await create_file(title=title, upload_file=file, session=session)
    scan_file_for_threats.delay(file_item.id)
    return file_item


@router.get("/files/{file_id}", response_model=FileItem)
async def get_file_view(file_id: str, session: AsyncSession = Depends(get_session)):
    return await get_file(file_id, session=session)


@router.patch("/files/{file_id}", response_model=FileItem)
async def update_file_view(
    file_id: str,
    payload: FileUpdate,
    session: AsyncSession = Depends(get_session),
):
    return await update_file(file_id=file_id, title=payload.title, session=session)


@router.get("/files/{file_id}/download")
async def download_file(file_id: str, session: AsyncSession = Depends(get_session)):
    file_item = await get_file(file_id, session=session)
    stored_path = settings.STORAGE_DIR / file_item.stored_name
    if not stored_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored file not found")
    return FileResponse(
        path=stored_path,
        media_type=file_item.mime_type,
        filename=file_item.original_name,
    )


@router.delete("/files/{file_id}", status_code=204)
async def delete_file_view(file_id: str, session: AsyncSession = Depends(get_session)):
    await delete_file(file_id, session=session)