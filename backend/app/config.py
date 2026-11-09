import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    APP_NAME: str = "VyaparVoice"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+psycopg://postgres@localhost:5433/vyaparvoice"
    TEST_DATABASE_URL: str = "postgresql+psycopg://postgres@localhost:5433/vyaparvoice_test"
    SECRET_KEY: str = "vyaparvoice_super_secret_jwt_key_2026_gnani_ai_challenge"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000"]
    
    # Gnani AI Configuration
    GNANI_API_KEY: str = ""
    GNANI_API_BASE_URL: str = "https://api.vachana.ai"
    GNANI_STT_ENDPOINT: str = "https://api.vachana.ai/stt/v3"
    GNANI_TTS_ENDPOINT: str = "https://api.vachana.ai/api/v1/tts/inference"
    GNANI_STT_MODEL: str = "prisma-v3.0"
    GNANI_TTS_MODEL: str = "timbre-v3.0"
    
    DEMO_MODE: bool = True

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [x.strip() for x in v.split(",") if x.strip()]
        return v

settings = Settings()
