from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
import uuid
import secrets
from datetime import datetime
from backend.db import get_pg_pool

router = APIRouter(prefix="/api/developer", tags=["developer"])

class APIKeyCreate(BaseModel):
    key_name: str
    platform: str

class APIKeyResponse(BaseModel):
    id: str
    key_name: str
    platform: str
    is_active: bool
    created_at: datetime
    # Don't expose actual key_value for security

class DeveloperStats(BaseModel):
    api_quota: int
    api_usage: int
    remaining_quota: int
    is_developer: bool

async def verify_developer_key(developer_api_key: str = Header(...)):
    """Verify developer API key"""
    if not developer_api_key:
        raise HTTPException(status_code=401, detail="Developer API key required")
    
    pool = await get_pg_pool()
    async with pool.acquire() as connection:
        developer = await connection.fetchrow(
            "SELECT user_id FROM developer_settings WHERE developer_key = $1 AND is_developer = true",
            developer_api_key
        )
        
        if not developer:
            raise HTTPException(status_code=401, detail="Invalid developer API key")
        
        return developer['user_id']

@router.post("/register")
async def register_as_developer(user_id: str):
    """Register a user as a developer"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Check if user exists
            user = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Check if already a developer
            existing = await connection.fetchrow(
                "SELECT id FROM developer_settings WHERE user_id = $1",
                uuid.UUID(user_id)
            )
            
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail="User is already registered as developer"
                )
            
            # Generate developer key
            developer_key = f"dev_{secrets.token_urlsafe(32)}"
            
            # Insert developer settings
            await connection.execute(
                """INSERT INTO developer_settings 
                   (user_id, developer_key, is_developer, api_quota, api_usage)
                   VALUES ($1, $2, true, 10000, 0)""",
                uuid.UUID(user_id), developer_key
            )
            
            return {
                "message": "Developer registration successful",
                "developer_key": developer_key,
                "api_quota": 10000
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/stats", response_model=DeveloperStats)
async def get_developer_stats(user_id: str = Depends(verify_developer_key)):
    """Get developer API usage statistics"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            stats = await connection.fetchrow(
                """SELECT api_quota, api_usage, is_developer 
                   FROM developer_settings WHERE user_id = $1""",
                user_id
            )
            
            if not stats:
                raise HTTPException(status_code=404, detail="Developer settings not found")
            
            return DeveloperStats(
                api_quota=stats['api_quota'],
                api_usage=stats['api_usage'],
                remaining_quota=stats['api_quota'] - stats['api_usage'],
                is_developer=stats['is_developer']
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key: APIKeyCreate, 
    user_id: str = Depends(verify_developer_key)
):
    """Create a new API key for a platform"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Generate secure API key
            key_value = f"{api_key.platform}_{secrets.token_urlsafe(40)}"
            
            # Insert API key
            key_id = await connection.fetchval(
                """INSERT INTO api_keys (user_id, key_name, key_value, platform)
                   VALUES ($1, $2, $3, $4) RETURNING id""",
                user_id, api_key.key_name, key_value, api_key.platform
            )
            
            # Fetch created key (without exposing key_value)
            created_key = await connection.fetchrow(
                "SELECT id, key_name, platform, is_active, created_at FROM api_keys WHERE id = $1",
                key_id
            )
            
            response_data = dict(created_key)
            response_data['key_value'] = key_value  # Only show once during creation
            
            return response_data
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/api-keys", response_model=List[APIKeyResponse])
async def get_api_keys(user_id: str = Depends(verify_developer_key)):
    """Get all API keys for the developer"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            keys = await connection.fetch(
                """SELECT id, key_name, platform, is_active, created_at 
                   FROM api_keys WHERE user_id = $1 ORDER BY created_at DESC""",
                user_id
            )
            
            return [APIKeyResponse(**dict(key)) for key in keys]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, user_id: str = Depends(verify_developer_key)):
    """Delete an API key"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Check if key exists and belongs to user
            existing_key = await connection.fetchrow(
                "SELECT id FROM api_keys WHERE id = $1 AND user_id = $2",
                uuid.UUID(key_id), user_id
            )
            
            if not existing_key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            # Delete key
            await connection.execute(
                "DELETE FROM api_keys WHERE id = $1", uuid.UUID(key_id)
            )
            
            return {"message": "API key deleted successfully"}
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/api-keys/{key_id}/toggle")
async def toggle_api_key(key_id: str, user_id: str = Depends(verify_developer_key)):
    """Toggle API key active status"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Check if key exists and belongs to user
            existing_key = await connection.fetchrow(
                "SELECT id, is_active FROM api_keys WHERE id = $1 AND user_id = $2",
                uuid.UUID(key_id), user_id
            )
            
            if not existing_key:
                raise HTTPException(status_code=404, detail="API key not found")
            
            # Toggle status
            new_status = not existing_key['is_active']
            await connection.execute(
                "UPDATE api_keys SET is_active = $1, updated_at = $2 WHERE id = $3",
                new_status, datetime.utcnow(), uuid.UUID(key_id)
            )
            
            return {
                "message": f"API key {'activated' if new_status else 'deactivated'} successfully",
                "is_active": new_status
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid key ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/increment-usage")
async def increment_api_usage(user_id: str = Depends(verify_developer_key)):
    """Increment API usage counter"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Get current usage and quota
            current = await connection.fetchrow(
                "SELECT api_usage, api_quota FROM developer_settings WHERE user_id = $1",
                user_id
            )
            
            if not current:
                raise HTTPException(status_code=404, detail="Developer settings not found")
            
            if current['api_usage'] >= current['api_quota']:
                raise HTTPException(status_code=429, detail="API quota exceeded")
            
            # Increment usage
            new_usage = await connection.fetchval(
                """UPDATE developer_settings 
                   SET api_usage = api_usage + 1, updated_at = $1
                   WHERE user_id = $2 RETURNING api_usage""",
                datetime.utcnow(), user_id
            )
            
            return {
                "current_usage": new_usage,
                "quota": current['api_quota'],
                "remaining": current['api_quota'] - new_usage
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")