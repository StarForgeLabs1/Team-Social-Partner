from typing import Dict
from datetime import datetime

class TenantService:
    def __init__(self):
        self.tenants: Dict[str, dict] = {}
    
    def create_tenant(self, name: str) -> str:
        tenant_id = f"tenant_{datetime.now().timestamp()}"
        self.tenants[tenant_id] = {
            "name": name,
            "created_at": datetime.now()
        }
        return tenant_id
