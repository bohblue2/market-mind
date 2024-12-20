import os

from pydantic import PostgresDsn, computed_field 
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings


class XingSettings(BaseSettings):
    XING_APP_KEY: str
    XING_APP_SECRET: str

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    
    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URL(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    class Config:
        env_file = (
            ".env.dev.xing" if os.getenv("ENVIRONMENT", "DEV") == 'DEV' else
            ".env.stage.xing" if os.getenv("ENVIRONMENT", "STAGE") == 'STAGE' else
            ".env.prod.xing" if os.getenv("ENVIRONMENT", "PROD") == 'PROD' else
            ".env.xing"
        )
        env_file_encoding = "utf-8"

settings = XingSettings() # type: ignore