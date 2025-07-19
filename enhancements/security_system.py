from cryptography.fernet import Fernet
import hashlib

class SecurityEngine:
    def __init__(self):
        self.cipher_key = Fernet.generate_key()
        
    def encrypt_content(self, content: str) -> bytes:
        """ 兼容原仓库Post模型的加密方法 """
        return Fernet(self.cipher_key).encrypt(content.encode())
    
    def generate_fingerprint(self, data: str) -> str:
        """ 用于追踪内容泄露 """
        return hashlib.sha3_256(data.encode()).hexdigest()
