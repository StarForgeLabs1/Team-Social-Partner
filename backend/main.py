from fastapi import FastAPI
from backend.routers import developer, user, account_import_export, logs

app = FastAPI()
app.include_router(developer.router)
app.include_router(user.router)
app.include_router(account_import_export.router)
app.include_router(logs.router)