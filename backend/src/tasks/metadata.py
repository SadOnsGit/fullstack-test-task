from pathlib import Path

from src.core.config import settings
from src.core.database import async_session_factory
from src.models.file import StoredFile
from src.tasks.alerts import send_file_alert
from src.tasks.celery_app import celery_app
from src.tasks.utils import run_in_worker_loop


async def _extract_file_metadata(file_id: str) -> None:
    async with async_session_factory() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        stored_path = settings.STORAGE_DIR / file_item.stored_name
        if not stored_path.exists():
            file_item.processing_status = "failed"
            file_item.scan_status = file_item.scan_status or "failed"
            file_item.scan_details = "stored file not found during metadata extraction"
            await session.commit()
            send_file_alert.delay(file_id)
            return

        metadata: dict = {
            "extension": Path(file_item.original_name).suffix.lower(),
            "size_bytes": file_item.size,
            "mime_type": file_item.mime_type,
        }

        if file_item.mime_type.startswith("text/"):
            content = stored_path.read_text(encoding="utf-8", errors="ignore")
            metadata["line_count"] = len(content.splitlines())
            metadata["char_count"] = len(content)
        elif file_item.mime_type == "application/pdf":
            content = stored_path.read_bytes()
            metadata["approx_page_count"] = max(content.count(b"/Type /Page"), 1)

        file_item.metadata_json = metadata
        file_item.processing_status = "processed"
        await session.commit()

    send_file_alert.delay(file_id)


@celery_app.task
def extract_file_metadata(file_id: str) -> None:
    run_in_worker_loop(_extract_file_metadata(file_id))
