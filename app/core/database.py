"""
MongoDB Database Connection and Models

Handles database connectivity and provides async database operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from datetime import datetime
from app.config import get_settings

# Global database client
_mongodb_client: Optional[AsyncIOMotorClient] = None
_mongodb_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongodb():
    """Initialize MongoDB connection."""
    global _mongodb_client, _mongodb_db
    
    settings = get_settings()
    
    try:
        _mongodb_client = AsyncIOMotorClient(settings.mongodb_url)
        _mongodb_db = _mongodb_client[settings.mongodb_db_name]
        
        # Test connection
        await _mongodb_client.admin.command('ping')
        print(f"✓ Connected to MongoDB: {settings.mongodb_db_name}")
        
        # Create indexes
        await _mongodb_db.uploaded_contracts.create_index("upload_id")
        await _mongodb_db.uploaded_contracts.create_index("uploaded_at")
        await _mongodb_db.uploaded_contracts.create_index("language")
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        print("  Continuing without MongoDB - file upload will be disabled")


async def close_mongodb_connection():
    """Close MongoDB connection."""
    global _mongodb_client
    
    if _mongodb_client:
        _mongodb_client.close()
        print("✓ MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get the database instance."""
    if _mongodb_db is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongodb() first.")
    return _mongodb_db


async def save_uploaded_contract(
    upload_id: str,
    filename: str,
    language: str,
    code: str,
    file_url: str,
    analysis_result: dict = None
) -> str:
    """
    Save an uploaded contract to MongoDB.
    
    Returns the document ID.
    """
    db = get_database()
    
    document = {
        "upload_id": upload_id,
        "filename": filename,
        "language": language,
        "code": code,
        "file_url": file_url,
        "analysis_result": analysis_result,
        "uploaded_at": datetime.now(),
        "analyzed": analysis_result is not None
    }
    
    result = await db.uploaded_contracts.insert_one(document)
    return str(result.inserted_id)


async def get_uploaded_contract(upload_id: str) -> Optional[dict]:
    """Get an uploaded contract by upload_id."""
    db = get_database()
    contract = await db.uploaded_contracts.find_one({"upload_id": upload_id})
    
    if contract:
        contract["_id"] = str(contract["_id"])
    
    return contract


async def get_recent_uploads(limit: int = 20) -> list[dict]:
    """Get recent uploaded contracts."""
    db = get_database()
    
    cursor = db.uploaded_contracts.find().sort("uploaded_at", -1).limit(limit)
    contracts = await cursor.to_list(length=limit)
    
    for contract in contracts:
        contract["_id"] = str(contract["_id"])
    
    return contracts


async def update_contract_analysis(upload_id: str, analysis_result: dict):
    """Update the analysis result for an uploaded contract."""
    db = get_database()
    
    await db.uploaded_contracts.update_one(
        {"upload_id": upload_id},
        {
            "$set": {
                "analysis_result": analysis_result,
                "analyzed": True,
                "analyzed_at": datetime.now()
            }
        }
    )
