from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MAPBOX_TOKEN: str
    OPENAI_API_KEY: str | None = None
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
