import pytest
from bot.config import config

def test_database_url_uses_sqlite_in_tests():
    assert config.database_url.startswith("sqlite"), "DATABASE_URL must be sqlite in tests to prevent connecting to real database"