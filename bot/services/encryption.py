from bot.config import config
from cryptography.fernet import Fernet

_cipher_suite = Fernet(config.encryption_key.encode())

def encrypt_data(data: str | None) -> str | None:
    if data is None:
        return None
    return _cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(data: str | None) -> str | None:
    if data is None:
        return None
    return _cipher_suite.decrypt(data.encode()).decode()