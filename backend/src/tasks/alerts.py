from src.core.database import async_session_factory
from src.models.alert import Alert
from src.models.file import StoredFile
from src.tasks.celery_app import celery_app
from src.tasks.utils import run_in_worker_loop


async def _send_file_alert(file_id: str) -> None:
    async with async_session_factory() as session:
        file_item = await session.get(StoredFile, file_id)
        if not file_item:
            return

        if file_item.processing_status == "failed":
            alert = Alert(file_id=file_id, level="critical", message="File processing failed")
        elif file_item.requires_attention:
            alert = Alert(
                file_id=file_id,
                level="warning",
                message=f"File requires attention: {file_item.scan_details}",
            )
        else:
            alert = Alert(file_id=file_id, level="info", message="File processed successfully")

        session.add(alert)
        await session.commit()


@celery_app.task
def send_file_alert(file_id: str) -> None:
    run_in_worker_loop(_send_file_alert(file_id))
