import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR.parent / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    APP_NAME: str = "ReqPilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Startup behavior: disabled by default so normal app boots do not mutate the DB.
    INIT_DB_ON_STARTUP: bool = os.getenv("INIT_DB_ON_STARTUP", "false").lower() == "true"
    SEED_DEMO_DATA_ON_STARTUP: bool = os.getenv("SEED_DEMO_DATA_ON_STARTUP", "false").lower() == "true"
    
    # Database configuration (defaults to SQLite aiosqlite for instant portability)
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'reqpilot.db'}")
    
    # Authentication
    JWT_SECRET: str = os.getenv("JWT_SECRET", "reqpilot-super-secret-key-change-in-prod-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    
    # LLM API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_API_KEYS: str = os.getenv("GROQ_API_KEYS", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    
    # Quality Scoring Weights (Section 10 of Blueprint)
    QUALITY_WEIGHTS: dict = {
        "completeness": 0.20,
        "clarity": 0.15,
        "atomicity": 0.15,
        "consistency": 0.20,
        "testability": 0.15,
        "feasibility": 0.10,
        "traceability": 0.05,
    }

settings = Settings()


