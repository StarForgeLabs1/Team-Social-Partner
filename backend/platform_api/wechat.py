from .base import PlatformBase
class WechatPlatform(PlatformBase):
    def publish(self, content):
        return f"Wechat发布：{content}"
    def test(self):
        return "Wechat平台测试成功"