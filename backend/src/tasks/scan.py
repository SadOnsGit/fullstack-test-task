from pathlib import Path

from src.core.database import async_session_factory
from src.models.file import StoredFile
from src.tasks.celery_app import celery_app
from src.tasks.metadata import extract_file_metadata
from src.tasks.utils import run_in_worker_loop

SUSPICIOUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".sh", ".js"}
MAX_CLEAN_SIZE_BYTES = 10 * 1024 * 1024


async def _scan_file_for_threats(file_id: str) -> None:
    async with async_session_factory() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        file_item.processing_status = "processing"
        reasons: list[str] = []
        extension = Path(file_item.original_name).suffix.lower()

        if extension in SUSPICIOUS_EXTENSIONS:
            reasons.append(f"suspicious extension {extension}")

        if file_item.size > MAX_CLEAN_SIZE_BYTES:
            reasons.append("file is larger than 10 MB")

        if extension == ".pdf" and file_item.mime_type not in {
            "application/pdf",
            "application/octet-stream",
        }:
            reasons.append("pdf extension does not match mime type")

        file_item.scan_status = "suspicious" if reasons else "clean"
        file_item.scan_details = ", ".join(reasons) if reasons else "no threats found"
        file_item.requires_attention = bool(reasons)
        await session.commit()

    extract_file_metadata.delay(file_id)


@celery_app.task
def scan_file_for_threats(file_id: str) -> None:
    run_in_worker_loop(_scan_file_for_threats(file_id))
