from sqlalchemy.ext.asyncio import AsyncSession

from src.models.alert import Alert


async def create_alert(
        file_id: str,
        level: str,
        message: str,
        session: AsyncSession,
) -> Alert:
    alert = Alert(file_id=file_id, level=level, message=message)
    session.add(alert)
    await session.commit()
    await session.refresh(alert)
    return alert