import os
import asyncpg

DATABASE_URL = os.getenv("SUPABASE_DB_URL")

async def get_pg_pool():
    if not hasattr(get_pg_pool, "pool"):
        get_pg_pool.pool = await asyncpg.create_pool(DATABASE_URL)
    return get_pg_pool.pool