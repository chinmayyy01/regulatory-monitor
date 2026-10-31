import pytest

from app.auth.passwords import hash_password, verify_password


def test_password_roundtrip():
    stored = hash_password("correct-horse-battery-staple")
    assert stored.startswith("scrypt$")
    assert verify_password("correct-horse-battery-staple", stored)


def test_wrong_password_fails():
    stored = hash_password("correct-horse-battery-staple")
    assert not verify_password("wrong-password-entirely", stored)


def test_each_hash_has_its_own_salt():
    first = hash_password("correct-horse-battery-staple")
    second = hash_password("correct-horse-battery-staple")
    assert first != second
    assert verify_password("correct-horse-battery-staple", first)
    assert verify_password("correct-horse-battery-staple", second)


def test_short_password_rejected():
    with pytest.raises(ValueError):
        hash_password("short")


def test_malformed_hash_is_rejected():
    assert not verify_password("anything", "not-a-hash")
    assert not verify_password("anything", "bcrypt$1$2$3$4$5")
