from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    MAPBOX_TOKEN: str
    # Routing algorithm: 'mapbox' (chunked directions) or 'osrm' (point-to-point)
    ROUTING_ALGORITHM: Literal["mapbox", "osrm"] = "osrm"
    # OSRM server URL (local Docker container)
    OSRM_URL: str = "http://localhost:5001"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()

