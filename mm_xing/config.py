import os

from pydantic_settings import BaseSettings


class XingSettings(BaseSettings):
    XING_APP_KEY: str
    XING_APP_SECRET: str

    class Config:
        env_file = (
            ".env.dev.xing" if os.getenv("ENVIRONMENT", "DEV") == 'DEV' else
            ".env.stage.xing" if os.getenv("ENVIRONMENT", "STAGE") == 'STAGE' else
            ".env.prod.xing" if os.getenv("ENVIRONMENT", "PROD") == 'PROD' else
            ".env.xing"
        )
        env_file_encoding = "utf-8"

settings = XingSettings() # type: ignore