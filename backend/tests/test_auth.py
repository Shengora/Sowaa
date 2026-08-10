import pytest
from backend.app.auth.api_keys import generate_api_key, verify_api_key_hash
from backend.app.auth.utils import get_password_hash, verify_password

def test_password_hashing():
    password = "secure_password123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_api_key_generation_and_verification():
    raw_key, prefix, hashed = generate_api_key()

    assert raw_key.startswith("sk_live_")
    assert prefix == raw_key[:12]

    assert verify_api_key_hash(raw_key, hashed) is True
    assert verify_api_key_hash(raw_key + "a", hashed) is False
