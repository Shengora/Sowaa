import secrets
import hashlib
from typing import Tuple

def generate_api_key() -> Tuple[str, str, str]:
    """
    Generates a new API key.
    Returns: (raw_key, key_prefix, hashed_key)
    """
    raw_secret = secrets.token_urlsafe(32)
    raw_key = f"sk_live_{raw_secret}"
    key_prefix = raw_key[:12]

    # We use SHA-256 for high entropy API secrets as standard practice,
    # instead of bcrypt which is better for low-entropy passwords.
    hashed_key = hashlib.sha256(raw_key.encode()).hexdigest()

    return raw_key, key_prefix, hashed_key

def verify_api_key_hash(raw_key: str, hashed_key: str) -> bool:
    """Verifies that the provided raw key matches the hash."""
    return hashlib.sha256(raw_key.encode()).hexdigest() == hashed_key
