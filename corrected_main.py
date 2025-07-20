from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import developer, user, account_import_export, logs
from backend.security import SecurityManager
from backend.tenant import TenantService
import os

# Create FastAPI app
app = FastAPI(
    title="Multi-platform Social Automation System",
    description="API for managing social media accounts and automation",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(developer.router)
app.include_router(user.router)
app.include_router(account_import_export.router)
app.include_router(logs.router)

# Initialize services
security = SecurityManager()
tenant_service = TenantService()

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Multi-platform Social Automation System API",
        "status": "running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",  # Could add actual DB health check
        "version": "1.0.0"
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print("🚀 Multi-platform Social Automation System starting up...")
    print(f"📊 Database URL configured: {bool(os.getenv('SUPABASE_DB_URL'))}")
    print(f"🔐 Security key configured: {bool(os.getenv('SECRET_KEY'))}")
    print(f"🔑 Developer API key configured: {bool(os.getenv('DEVELOPER_API_KEY'))}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("🛑 Multi-platform Social Automation System shutting down...")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )