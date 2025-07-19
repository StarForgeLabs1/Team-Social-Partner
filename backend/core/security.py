# backend/core/security.py
from cryptography.fernet import Fernet
import os

class Security:
    def __init__(self):
        self.key = os.getenv("SECRET_KEY") or Fernet.generate_key().decode()
    
    def encrypt(self, text: str) -> str:
        return Fernet(self.key).encrypt(text.encode()).decode()
    
    def decrypt(self, token: str) -> str:
        return Fernet(self.key).decrypt(token.encode()).decode()
