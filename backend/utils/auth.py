from fastapi import Request

class User:
    def __init__(self, id: int = 1, role: str = "developer"):
        self.id = id
        self.role = role

def get_current_user(request: Request):
    # 简单版本，始终返回开发者用户
    return User()