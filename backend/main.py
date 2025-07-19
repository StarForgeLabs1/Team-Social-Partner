from fastapi import FastAPI
from backend.routers import developer, user, account_import_export, logs

app = FastAPI()
app.include_router(developer.router)
app.include_router(user.router)
app.include_router(account_import_export.router)
app.include_router(logs.router)
from security import SecurityManager
from tenant import TenantService

security = SecurityManager()
tenant_service = TenantService()

# 使用示例
encrypted = security.encrypt("敏感数据")
tenant_id = tenant_service.create_tenant("测试租户")
