from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    openai_api_key: str = ""
    primary_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-4o"
    transcription_model: str = "whisper-1"
    database_path: str = "runtime/calls.sqlite3"
    workers: int = Field(default=2, ge=1, le=4)


settings = Settings()
