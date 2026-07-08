import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    STORAGE_DIR: Path = Path("storage/files")

    # --- PostgreSQL ---
    POSTGRES_USER: str = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv(
        'POSTGRES_PASSWORD',
        'postgres',
    )
    POSTGRES_HOST: str = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('POSTGRES_PORT', '5432'))
    POSTGRES_DB: str = os.getenv('POSTGRES_DB', 'testdb')
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://backend-redis:6379/0")

    def model_post_init(self, __context) -> None:
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def database_url(self) -> str:
        """Формирует URL подключения к PostgreSQL (asyncpg)."""
        return (
            f'postgresql+asyncpg://{self.POSTGRES_USER}:'
            f'{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:'
            f'{self.POSTGRES_PORT}/{self.POSTGRES_DB}'
        )

    # --- REDIS ---
    

settings = Settings()