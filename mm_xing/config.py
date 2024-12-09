import os

from pydantic_settings import BaseSettings


class XingSettings(BaseSettings):
    XING_APP_KEY: str
    XING_APP_SECRET: str

    class Config:
        env_file = (
            ".dev.xing.env" if os.getenv("ENVIRONMENT", "DEV") == 'DEV' else
            ".stage.xing.env" if os.getenv("ENVIRONMENT", "STAGE") == 'STAGE' else
            ".prod.xing.env"
        )
        env_file_encoding = "utf-8"

settings = XingSettings() # type: ignore