from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal

class Settings(BaseSettings):
    MAPBOX_TOKEN: str
    # Routing algorithm: 'mapbox' (chunked directions) or 'osrm' (point-to-point)
    # Note: OSRM requires a working server (public demo is rate-limited/unreliable)
    ROUTING_ALGORITHM: Literal["mapbox", "osrm"] = "mapbox"
    
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
