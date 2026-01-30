from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager following Singleton pattern."""

    # Spain (PRO) database
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    # Ireland (Ukie) database
    client_ireland: Optional[AsyncIOMotorClient] = None
    db_ireland: Optional[AsyncIOMotorDatabase] = None


db = Database()


async def connect_to_mongo() -> None:
    """Establish connection to MongoDB databases."""
    settings = get_settings()

    # Connect to Spain (PRO) database
    db.client = AsyncIOMotorClient(
        settings.mongodb_url,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000
    )
    db.db = db.client[settings.database_name]

    # Test Spain connection
    try:
        await db.client.admin.command('ping')
        logger.info(f"Connected to MongoDB (Spain): {settings.database_name}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB (Spain): {e}")
        raise

    # Connect to Ireland (Ukie) database if configured
    if settings.mongodb_url_ireland:
        try:
            db.client_ireland = AsyncIOMotorClient(
                settings.mongodb_url_ireland,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                maxPoolSize=10
            )
            db.db_ireland = db.client_ireland[settings.database_name_ireland]

            # Test Ireland connection
            await db.client_ireland.admin.command('ping')
            logger.info(f"Connected to MongoDB (Ireland): {settings.database_name_ireland}")
        except Exception as e:
            logger.warning(f"Failed to connect to MongoDB (Ireland): {e}")
            logger.warning("Ukie features will be unavailable")
            db.client_ireland = None
            db.db_ireland = None


async def close_mongo_connection() -> None:
    """Close all MongoDB connections."""
    if db.client:
        db.client.close()
        logger.info("Closed MongoDB connection (Spain)")

    if db.client_ireland:
        db.client_ireland.close()
        logger.info("Closed MongoDB connection (Ireland)")


def get_database() -> AsyncIOMotorDatabase:
    """Get Spain database instance for dependency injection."""
    if db.db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return db.db


def get_database_ireland() -> AsyncIOMotorDatabase:
    """Get Ireland database instance for dependency injection."""
    if db.db_ireland is None:
        raise RuntimeError("Ireland database not available. Check MONGODB_URL_IRELAND configuration.")
    return db.db_ireland
