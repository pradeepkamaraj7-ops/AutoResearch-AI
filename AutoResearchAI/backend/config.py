import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BASE_DIR / "data"

# Ensure data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load .env file from AutoResearchAI/.env or current working directory
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings:
    """Application Configuration Settings"""
    PROJECT_NAME: str = "AutoResearch AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")

    BASE_DIR: Path = BASE_DIR
    BACKEND_DIR: Path = BACKEND_DIR
    FRONTEND_DIR: Path = FRONTEND_DIR
    DATA_DIR: Path = DATA_DIR

    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Groq AI settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "groq/compound").strip()
    # Fallback models in case groq/compound is busy or restricted
    GROQ_FALLBACK_MODEL: str = os.getenv("GROQ_FALLBACK_MODEL", "groq/compound-mini").strip()

    # Database settings
    DATABASE_PATH: Path = DATA_DIR / "autoresearch.db"
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_PATH}")

    # Crawling settings
    CRAWL_TIMEOUT_SECONDS: int = int(os.getenv("CRAWL_TIMEOUT_SECONDS", "15"))
    MAX_CRAWL_PAGES: int = int(os.getenv("MAX_CRAWL_PAGES", "3"))
    USER_AGENT: str = os.getenv(
        "USER_AGENT",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 AutoResearchAI/1.0"
    )

    # Allowed domains for automotive research (priority domains)
    PRIORITY_DOMAINS: list[str] = [
        "tatamotors.com",
        "hyundai.com",
        "mahindra.com",
        "marutisuzuki.com",
        "toyotabharat.com",
        "kia.com",
        "cardekho.com",
        "zigwheels.com",
        "carwale.com",
        "autocarindia.com",
        "araiindia.com",
        "nhtsa.gov",
        "team-bhp.com",
        "overdrive.in"
    ]

    # CORS
    CORS_ORIGINS: list[str] = ["*"]

    @property
    def is_groq_configured(self) -> bool:
        """Check if a non-placeholder Groq API key is configured."""
        return bool(
            self.GROQ_API_KEY
            and self.GROQ_API_KEY != "your_groq_api_key_here"
            and len(self.GROQ_API_KEY) > 10
        )

settings = Settings()
