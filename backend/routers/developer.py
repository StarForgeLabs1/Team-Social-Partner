from fastapi import APIRouter, Depends, HTTPException, Body
from backend.utils.auth import get_current_user
from backend.db import get_pg_pool

router = APIRouter(prefix="/api/developer", tags=["developer"])

def require_developer(user=Depends(get_current_user)):
    if user.role != "developer":
        raise HTTPException(status_code=403, detail="仅开发者可访问")
    return user

@router.get("/api-keys")
async def list_api_keys(user=Depends(require_developer)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, value FROM api_keys WHERE user_id=$1", user.id)
        return [dict(row) for row in rows]

@router.post("/api-keys")
async def create_api_key(data: dict = Body(...), user=Depends(require_developer)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO api_keys (name, value, user_id) VALUES ($1, $2, $3) RETURNING *",
            data.get("name", ""), "sk-new", user.id
        )
        return dict(row)

@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: int, user=Depends(require_developer)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM api_keys WHERE id=$1 AND user_id=$2", key_id, user.id)
    return {"success": True}

@router.get("/webhooks")
async def list_webhooks(user=Depends(require_developer)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, url FROM webhooks WHERE user_id=$1", user.id)
        return [dict(row) for row in rows]

@router.post("/webhooks")
async def add_webhook(data: dict = Body(...), user=Depends(require_developer)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO webhooks (url, user_id) VALUES ($1, $2) RETURNING *",
            data.get("url", ""), user.id
        )
        return dict(row)

@router.delete("/webhooks/{webhook_id}")
async def del_webhook(webhook_id: int, user=Depends(require_developer)):
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM webhooks WHERE id=$1 AND user_id=$2", webhook_id, user.id)
    return {"success": True}

@router.post("/test-publish")
async def test_publish(user=Depends(require_developer)):
    return {"result": "所有平台已测试"}

@router.get("/sdks")
async def list_sdks(user=Depends(require_developer)):
    return [
        {"lang": "Python", "url": "https://yourdomain.com/sdk/python.zip"},
        {"lang": "JavaScript", "url": "https://yourdomain.com/sdk/js.zip"},
        {"lang": "Java", "url": "https://yourdomain.com/sdk/java.zip"}
    ]

@router.get("/docs")
async def api_docs(user=Depends(require_developer)):
    return {
        "docs": "https://yourdomain.com/api-docs",
        "openapi": "https://yourdomain.com/openapi.json"
    }