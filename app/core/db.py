from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class Settings(BaseSettings):
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    db_host: str = "localhost"
    db_port: int = 3306
    db_name: str = "darfin"
    db_user: str = "root"
    db_password: str = ""
    database_url: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_url(self) -> str:
        if self.database_url and not self._is_default_database_url(self.database_url):
            return self.database_url

        user = quote_plus(self.db_user)
        password = quote_plus(self.db_password)
        host = self.db_host
        port = self.db_port
        name = self.db_name
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}"

    @staticmethod
    def _is_default_database_url(value: str) -> bool:
        return (
            "postgres:postgres@localhost:5432/darfin_investment" in value
            or "postgres:postgres@127.0.0.1:5432/darfin_investment" in value
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
engine = create_engine(settings.sqlalchemy_database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
