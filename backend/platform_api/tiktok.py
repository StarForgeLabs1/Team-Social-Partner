from .base import PlatformBase

class TikTokPlatform(PlatformBase):
    def publish(self, content):
        return f"TikTok发布：{content}"
    def test(self):
        return "TikTok平台测试成功"
    def get_accounts(self):
        return [{"id": "tiktok001", "nickname": "小Tik"}]