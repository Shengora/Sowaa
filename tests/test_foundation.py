import pytest
from bot.config import Settings
from bot.services.encryption import encrypt_data, decrypt_data

def test_admin_ids_parsing():
    settings = Settings(admin_ids="123, 456,789 ")
    assert settings.parsed_admin_ids == [123, 456, 789]

def test_encryption():
    raw_data = "Secret Address 123"
    encrypted = encrypt_data(raw_data)

    assert encrypted != raw_data
    assert type(encrypted) == str

    decrypted = decrypt_data(encrypted)
    assert decrypted == raw_data

def test_encryption_none():
    assert encrypt_data(None) is None
    assert decrypt_data(None) is None