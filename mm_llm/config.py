import os

from pydantic import AnyUrl, PostgresDsn, computed_field
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings


class LlmSettings(BaseSettings):
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
    MILVUS_API_KEY: str
    MILVUS_URI: str
    MILVUS_READ_USER_ID: str
    MILVUS_READ_PASSWORD: str

    ANTHROPIC_API_KEY: str

    UPSTAGE_API_KEY: str

    DEFAULT_EMBEDDING_MODEL: str

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
        env_file = ".dev.llm.env" if os.getenv("ENVIRONMENT", "DEV") == 'DEV' else ".prod.llm.env"
        env_file_encoding = "utf-8"

settings = LlmSettings() # type: ignore