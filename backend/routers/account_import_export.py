from fastapi import APIRouter, UploadFile, File, Response
import csv
import io
from backend.db import get_pg_pool

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

@router.post("/import")
async def import_accounts(file: UploadFile = File(...)):
    content = await file.read()
    decoded = content.decode()
    reader = csv.DictReader(io.StringIO(decoded))
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        count = 0
        async with conn.transaction():
            for row in reader:
                await conn.execute(
                    "INSERT INTO accounts (username, platform) VALUES ($1, $2)",
                    row["username"], row["platform"]
                )
                count += 1
    return {"count": count}

@router.get("/export")
async def export_accounts():
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, username, platform FROM accounts")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "username", "platform"])
    writer.writeheader()
    for acc in rows:
        writer.writerow(dict(acc))
    return Response(content=output.getvalue(), media_type="text/csv")