import hashlib

import bcrypt

from services.auth_service.auth_service import AuthService


def test_hash_password_uses_argon2():
    service = AuthService()
    hashed = service.hash_password("secret123")

    assert hashed.startswith("$argon2")
    assert service.verify_password("secret123", hashed)


def test_verify_legacy_bcrypt_sha256_hash():
    service = AuthService()
    legacy_pre_hash = hashlib.sha256("secret123".encode("utf-8")).hexdigest()
    legacy_hash = bcrypt.hashpw(legacy_pre_hash.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    assert service.verify_password("secret123", legacy_hash)
