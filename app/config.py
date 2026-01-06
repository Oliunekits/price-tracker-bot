from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    BOT_TOKEN: str
    DATABASE_URL: str
    CHECK_INTERVAL_SECONDS: int = 60
    TIMEZONE: str = "Europe/Kyiv"
    LOG_LEVEL: str = "INFO"

settings = Settings()
