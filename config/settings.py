from pydantic_settings import BaseSettings
from typing import List, Optional

class NDRAConfig(BaseSettings):
    APP_NAME: str = "NDRA-PII (Neuro-Semantic Distributed Risk Analysis)"
    ENV: str = "dev"
    VERSION: str = "1.0.0"

    # Paths
    UPLOAD_DIR: str = "./uploads"
    ARTIFACTS_DIR: str = "./artifacts"

    # Presidio
    PRESIDIO_LANGUAGE: str = "en"

    # Vector DB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8000

    # LLM (Assistive Only)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Security / API hardening
    # List of allowed CORS origins.  Set via the CORS_ORIGINS environment
    # variable as a JSON array: CORS_ORIGINS='["https://app.example.com"]'
    # In production, replace with the exact frontend origin(s); never use "*".
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Maximum file upload size in bytes (default 50 MB).
    MAX_UPLOAD_BYTES: int = 50 * 1024 * 1024  # 50 MB

    # Whitelist of MIME types accepted by /analyze/upload.
    # Set via ALLOWED_UPLOAD_MIMES as a JSON array in the environment.
    ALLOWED_UPLOAD_MIMES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/csv",
        "application/json",
        "application/xml",
        "text/xml",
        "text/html",
        "message/rfc822",
    ]

    # List of absolute directory prefixes permitted for /analyze/path.
    # Set via ALLOWED_PATH_PREFIXES as a JSON array in the environment.
    # Leave empty (default) to disable the endpoint entirely (recommended for production).
    ALLOWED_PATH_PREFIXES: List[str] = []

    class Config:
        env_file = ".env"

settings = NDRAConfig()
