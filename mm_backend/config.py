import os
from typing import Annotated, Any

from pydantic import AnyUrl, BeforeValidator, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)

class BackendSettings(BaseSettings):
    DEBUG: bool = True
    ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = [] # type: ignore
    
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    
    ALEMBIC_DB_URL: str
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    LANGCHAIN_TRACING_V2: bool
    LANGCHAIN_ENDPOINT: AnyUrl
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str

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
    
    def __post_init__(self):
        def display_all_fields(self):
            """
            Display all configuration values.
            """
            for field_name, field_value in self.__dict__.items():
                print(f"{field_name}: {field_value}")
        display_all_fields(self)
    
    class Config:
        env_file = (
            ".env.dev.backend" if os.getenv("ENVIRONMENT", "DEV") == 'DEV' else
            ".env.stage.backend" if os.getenv("ENVIRONMENT", "STAGE") == 'STAGE' else
            ".env.prod.backend" if os.getenv("ENVIRONMENT", "PROD") == 'PROD' else
            ".env.backend"
        )
        env_file_encoding = "utf-8"

settings = BackendSettings() # type: ignore