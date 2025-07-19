# backend/middlewares/rate_limiter.py
from fastapi import Request

async def rate_limiter(request: Request, call_next):
    # 60次/分钟限流
    client_ip = request.client.host
    if request.app.state.requests.get(client_ip, 0) > 60:
        return JSONResponse({"error": "Rate limit exceeded"}, status_code=429)
    return await call_next(request)
