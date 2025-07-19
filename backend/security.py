from cryptography.fernet import Fernet
import base64
import os

class SecurityManager:
    def __init__(self):
        self.key = base64.urlsafe_b64encode(os.urandom(32))
        self.cipher = Fernet(self.key)
    
    def encrypt(self, text: str) -> str:
        return self.cipher.encrypt(text.encode()).decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        return self.cipher.decrypt(encrypted_text.encode()).decode()
