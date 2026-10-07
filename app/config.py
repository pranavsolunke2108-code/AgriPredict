import os
from pathlib import Path
from dotenv import load_dotenv

# Automatically load .env file from project root
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()


class Settings:
    """Application and Database Configuration loaded from environment variables."""

    # MySQL Database Configuration (Least-Privilege App Account)
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "agripredict_app")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "agripredict")
    DB_POOL_NAME: str = os.getenv("DB_POOL_NAME", "agripredict_pool")
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))

    # MySQL Migration / DDL User (for schema migrations & DDL setup)
    DB_MIGRATE_USER: str = os.getenv("DB_MIGRATE_USER", "agripredict_migrate")
    DB_MIGRATE_PASSWORD: str = os.getenv("DB_MIGRATE_PASSWORD", "")

    # JWT Session Configuration
    JWT_SECRET: str = os.getenv("JWT_SECRET", "agripredict-secret-key-change-in-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours


settings = Settings()
