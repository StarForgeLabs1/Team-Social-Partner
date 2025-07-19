# 用户模型修改
class User:
    def __init__(self):
        self.account = None  # 对应 user_account
        self.platform = None  # 对应 user_platform

# API密钥模型修改
class APIKey:
    def __init__(self):
        self.name = None  # 对应 key_name
        self.value = None  # 对应 key_value
