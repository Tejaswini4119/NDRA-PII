from pydantic_settings import BaseSettings
from typing import Optional

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

    class Config:
        env_file = ".env"

settings = NDRAConfig()
