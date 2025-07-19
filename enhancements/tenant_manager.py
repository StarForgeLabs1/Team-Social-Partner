from typing import Dict
from core.models import User  # 直接引用原模型

class TenantController:
    def __init__(self):
        self.tenants: Dict[str, Dict] = {}
        
    def create_tenant(self, admin: User, resources: Dict):
        """ 与原仓库用户系统兼容 """
        tenant_id = f"tenant_{admin.user_id[:8]}"
        self.tenants[tenant_id] = {
            "admin": admin,
            "resources": resources,
            "is_active": True
        }
        return tenant_id
