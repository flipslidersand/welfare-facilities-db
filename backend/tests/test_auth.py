import pytest
from app.auth import hash_api_key, verify_api_key, generate_api_key


def test_hash_api_key():
    key = "test-key-123"
    hashed = hash_api_key(key)
    assert len(hashed) == 64
    assert isinstance(hashed, str)


def test_verify_api_key():
    key = "test-key-123"
    hashed = hash_api_key(key)
    assert verify_api_key(key, hashed) is True


def test_verify_api_key_mismatch():
    key = "test-key-123"
    hashed = hash_api_key(key)
    assert verify_api_key("wrong-key", hashed) is False


def test_generate_api_key():
    key1 = generate_api_key()
    key2 = generate_api_key()
    assert len(key1) > 0
    assert key1 != key2
    assert isinstance(key1, str)
