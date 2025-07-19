from fastapi import APIRouter, Body
from datetime import datetime
from backend.db import get_pg_pool

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("/")
async def list_logs():
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, message, timestamp FROM logs ORDER BY timestamp DESC")
        return [dict(row) for row in rows]

@router.post("/")
async def add_log(log: dict = Body(...)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO logs (message, timestamp) VALUES ($1, $2) RETURNING *",
            log["message"], datetime.utcnow()
        )
        return dict(row)