from .base import PlatformBase
class FacebookPlatform(PlatformBase):
    def publish(self, content):
        return f"Facebook发布：{content}"
    def test(self):
        return "Facebook平台测试成功"