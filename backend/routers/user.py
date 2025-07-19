from fastapi import APIRouter, HTTPException, Body
from backend.db import get_pg_pool

router = APIRouter(prefix="/api/users", tags=["user"])

@router.get("/")
async def list_users():
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, username, nickname, platform FROM users")
        return [dict(row) for row in rows]

@router.post("/")
async def create_user(user: dict = Body(...)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO users (username, nickname, platform) VALUES ($1, $2, $3) RETURNING *",
            user["username"], user.get("nickname", ""), user.get("platform", "")
        )
        return dict(row)

@router.put("/{user_id}")
async def update_user(user_id: int, user: dict = Body(...)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "UPDATE users SET username=$1, nickname=$2, platform=$3 WHERE id=$4 RETURNING *",
            user["username"], user.get("nickname", ""), user.get("platform", ""), user_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        return dict(row)

@router.delete("/{user_id}")
async def delete_user(user_id: int):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM users WHERE id=$1", user_id)
    return {"success": True}