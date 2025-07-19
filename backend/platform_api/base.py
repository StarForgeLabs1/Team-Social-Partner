class PlatformBase:
    def publish(self, content):
        raise NotImplementedError
    def get_accounts(self):
        return []
    def test(self):
        return "Base platform test success"