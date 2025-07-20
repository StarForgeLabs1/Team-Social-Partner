from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid
from datetime import datetime
from backend.db import get_pg_pool

router = APIRouter(prefix="/api/users", tags=["users"])

class UserCreate(BaseModel):
    user_account: str
    user_platform: str
    email: Optional[str] = None
    password: str

class UserResponse(BaseModel):
    id: str
    user_account: str
    user_platform: str
    email: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Check if user already exists
            existing_user = await connection.fetchrow(
                "SELECT id FROM users WHERE user_account = $1 AND user_platform = $2",
                user.user_account, user.user_platform
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="User with this account and platform already exists"
                )
            
            # Hash password (simplified - in production use proper password hashing)
            password_hash = f"hashed_{user.password}"
            
            # Insert new user
            user_id = await connection.fetchval(
                """INSERT INTO users (user_account, user_platform, email, password_hash) 
                   VALUES ($1, $2, $3, $4) RETURNING id""",
                user.user_account, user.user_platform, user.email, password_hash
            )
            
            # Fetch the created user
            created_user = await connection.fetchrow(
                "SELECT * FROM users WHERE id = $1", user_id
            )
            
            return UserResponse(**dict(created_user))
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/", response_model=List[UserResponse])
async def get_users():
    """Get all users"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            users = await connection.fetch(
                "SELECT * FROM users ORDER BY created_at DESC"
            )
            return [UserResponse(**dict(user)) for user in users]
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """Get a specific user by ID"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            user = await connection.fetchrow(
                "SELECT * FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
                
            return UserResponse(**dict(user))
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    """Update a user"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Check if user exists
            existing_user = await connection.fetchrow(
                "SELECT * FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not existing_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Build update query dynamically
            update_fields = []
            values = []
            param_count = 1
            
            if user_update.email is not None:
                update_fields.append(f"email = ${param_count}")
                values.append(user_update.email)
                param_count += 1
                
            if user_update.is_active is not None:
                update_fields.append(f"is_active = ${param_count}")
                values.append(user_update.is_active)
                param_count += 1
            
            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")
            
            update_fields.append(f"updated_at = ${param_count}")
            values.append(datetime.utcnow())
            values.append(uuid.UUID(user_id))
            
            query = f"""
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count + 1}
                RETURNING *
            """
            
            updated_user = await connection.fetchrow(query, *values)
            return UserResponse(**dict(updated_user))
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.delete("/{user_id}")
async def delete_user(user_id: str):
    """Delete a user"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            # Check if user exists
            existing_user = await connection.fetchrow(
                "SELECT id FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            if not existing_user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete user (CASCADE will handle related records)
            await connection.execute(
                "DELETE FROM users WHERE id = $1", uuid.UUID(user_id)
            )
            
            return {"message": "User deleted successfully"}
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{user_id}/social-accounts")
async def get_user_social_accounts(user_id: str):
    """Get all social accounts for a user"""
    pool = await get_pg_pool()
    
    try:
        async with pool.acquire() as connection:
            accounts = await connection.fetch(
                """SELECT id, platform, account_handle, account_status, created_at 
                   FROM social_accounts WHERE user_id = $1 ORDER BY created_at DESC""",
                uuid.UUID(user_id)
            )
            
            return [dict(account) for account in accounts]
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")