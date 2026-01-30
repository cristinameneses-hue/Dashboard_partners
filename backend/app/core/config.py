from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List, Optional
import os
import secrets


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # MongoDB connection for LudaFarma-PRO (Spain)
    # SECURITY: Must be set via environment variable, no hardcoded defaults
    mongodb_url: str = os.getenv(
        "MONGODB_URL",
        "mongodb://localhost:27017/LudaFarma-PRO"  # Safe default without credentials
    )
    database_name: str = "LudaFarma-PRO"

    # MongoDB connection for LudaFarma-Ireland (Ukie)
    mongodb_url_ireland: str = ""  # Set via MONGODB_URL_IRELAND in .env
    database_name_ireland: str = "LudaFarma-Ireland"

    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_minutes: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "30"))

    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret(cls, v: str) -> str:
        """Validate JWT secret key - MUST be set in production."""
        environment = os.getenv("ENVIRONMENT", "development")
        if environment == "production":
            if not v or len(v) < 32:
                raise ValueError(
                    "CRITICAL: JWT_SECRET_KEY must be set and at least 32 characters in production. "
                    "Generate with: openssl rand -hex 32"
                )
        elif not v:
            # Development: generate a random key but warn
            import logging
            logging.warning(
                "JWT_SECRET_KEY not set - using random key. "
                "Sessions will be invalidated on server restart."
            )
            return secrets.token_hex(32)
        return v

    # Google OAuth Configuration
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # Allowed email domain for authentication (e.g., "ludapartners.com")
    allowed_email_domain: Optional[str] = os.getenv("ALLOWED_EMAIL_DOMAIN")

    # CORS Configuration - parsed from comma-separated string
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from environment variable (comma-separated)."""
        origins = os.getenv("CORS_ORIGINS_RAW", "http://localhost:5173,http://localhost:3000")
        return [o.strip() for o in origins.split(",") if o.strip()]

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "development")

    # Cookie security - only use secure cookies in production (HTTPS)
    @property
    def cookie_secure(self) -> bool:
        """Use secure cookies only in production (requires HTTPS)."""
        return self.environment == "production"

    @property
    def cookie_samesite(self) -> str:
        """SameSite cookie policy - lax for development, strict for production."""
        return "strict" if self.environment == "production" else "lax"
    
    # Cancelled state ID
    cancelled_state_id: str = "5a54c525b2948c860f00000d"
    
    # Active partners
    partners: List[str] = [
        "glovo", "glovo-otc", "uber", "justeat", 
        "amazon", "carrefour", "danone", "procter", 
        "enna", "nordic", "chiesi", "ferrer"
    ]
    
    # Partners without tags (can't calculate % active pharmacies)
    partners_without_tags: List[str] = ["uber", "justeat"]

    # Ireland-specific partners (Ukie)
    partners_ireland: List[str] = [
        "justeat", "justeat-ireland", "justeat-uk",
        "uber", "uber-ireland", "uber-uk"
    ]
    
    # Partner tag mappings (partner name -> possible tags in pharmacies)
    partner_tags: dict = {
        "glovo": ["GLOVO"],
        "glovo-otc": ["GLOVO-OTC_2H", "GLOVO-OTC_48H"],
        "amazon": ["AMAZON_2H", "AMAZON_48H"],
        "carrefour": ["CARREFOUR_2H", "CARREFOUR_48H"],
        "danone": ["DANONE_2H", "DANONE_48H"],
        "procter": ["PROCTER_2H", "PROCTER_48H"],
        "enna": ["ENNA_2H", "ENNA_48H"],
        "nordic": ["NORDIC_2H", "NORDIC_48H"],
        "chiesi": ["CHIESI_48H", "CHIESI_BACKUP"],
        "ferrer": ["FERRER_2H", "FERRER_48H"],
    }
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env vars not defined in the model


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (Singleton pattern)."""
    return Settings()
