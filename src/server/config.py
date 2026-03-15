from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8443
    dest_dir: str = "dest"
    sync_secret: str = "dev-secret-change-me"
    cert_dir: str = ".certs"
