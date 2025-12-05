from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # MongoDB connection for LudaFarma-PRO
    mongodb_url: str = "mongodb://iimReports:Reports2019@localhost:27017/LudaFarma-PRO?readPreference=primary&directConnection=true&ssl=false"
    database_name: str = "LudaFarma-PRO"
    
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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance (Singleton pattern)."""
    return Settings()
