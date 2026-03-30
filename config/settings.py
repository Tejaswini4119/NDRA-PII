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

    # API key for protecting /analyze/* and /audit/* endpoints.
    # When set, every request to those endpoints must include the header:
    #   X-API-Key: <value>
    # Leave unset (default) to disable auth (only for local development).
    API_KEY: Optional[str] = None

    # Maximum number of /analyze/* requests per minute per IP address.
    # Set to 0 to disable rate limiting.
    RATE_LIMIT_PER_MINUTE: int = 60

    # ------------------------------------------------------------------
    # Production freeze controls
    # ------------------------------------------------------------------
    # When enabled (default), NDRA only accepts the verified ingestion formats
    # listed in FROZEN_SUPPORTED_MIMES. This disables partial/experimental
    # ingestion behavior and keeps end-to-end behavior deterministic.
    FREEZE_WORKING_SYSTEM: bool = True

    # Explicit allowlist used when FREEZE_WORKING_SYSTEM is enabled.
    # Configure via JSON array env var if needed.
    FROZEN_SUPPORTED_MIMES: List[str] = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain",
        "text/markdown",
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "application/json",
        "application/xml",
        "text/xml",
        "application/x-yaml",
        "text/yaml",
        "text/html",
        "message/rfc822",
    ]

    # Opt-in switch for image metadata ingestion, MSG parsing, and archive
    # recursion. Ignored while FREEZE_WORKING_SYSTEM is True.
    ENABLE_EXPERIMENTAL_INGESTION: bool = False

    class Config:
        env_file = ".env"

settings = NDRAConfig()
