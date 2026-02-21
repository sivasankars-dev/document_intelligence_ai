import hashlib
import time
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from shared.config.settings import settings
from shared.models.user import User


class AuthService:
    _redis_client = None
    _fallback_store: dict[str, tuple[str, int]] = {}
    _password_hasher = PasswordHasher()

    def __init__(self):
        if AuthService._redis_client is None:
            AuthService._redis_client = self._init_redis_client()

    def _init_redis_client(self):
        try:
            import redis

            return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception:
            return None

    def _set_with_ttl(self, key: str, value: str, ttl_seconds: int):
        ttl_seconds = max(1, ttl_seconds)
        if self._redis_client is not None:
            self._redis_client.setex(key, ttl_seconds, value)
            return

        expires_at = int(time.time()) + ttl_seconds
        self._fallback_store[key] = (value, expires_at)

    def _get(self, key: str):
        if self._redis_client is not None:
            return self._redis_client.get(key)

        value = self._fallback_store.get(key)
        if not value:
            return None

        stored_value, expires_at = value
        if int(time.time()) >= expires_at:
            self._fallback_store.pop(key, None)
            return None

        return stored_value

    def _delete(self, key: str):
        if self._redis_client is not None:
            self._redis_client.delete(key)
            return

        self._fallback_store.pop(key, None)

    def hash_password(self, password: str):
        return self._password_hasher.hash(password)

    def _is_legacy_bcrypt_hash(self, hashed_password: str) -> bool:
        return hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$")

    def verify_password(self, plain_password: str, hashed_password: str):
        # Verify current Argon2 hashes.
        try:
            return self._password_hasher.verify(hashed_password, plain_password)
        except VerifyMismatchError:
            return False
        except InvalidHash:
            pass
        except Exception:
            return False

        # Backward compatibility for previously stored bcrypt hashes.
        if self._is_legacy_bcrypt_hash(hashed_password):
            try:
                # Historical format in this project was bcrypt(sha256(password)).
                pre_hashed = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
                return bcrypt.checkpw(pre_hashed.encode("utf-8"), hashed_password.encode("utf-8"))
            except Exception:
                return False

        return False

    def get_user_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, db: Session, user_id):
        return db.query(User).filter(User.id == user_id).first()

    def create_user(self, db: Session, email: str, password: str):
        existing_user = self.get_user_by_email(db=db, email=email)
        if existing_user:
            raise ValueError("User with this email already exists")

        hashed_password = self.hash_password(password)
        user = User(
            email=email,
            password_hash=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    def authenticate_user(self, db: Session, email: str, password: str):
        user = self.get_user_by_email(db=db, email=email)
        if not user:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Migrate legacy bcrypt hashes to Argon2 after successful login.
        if self._is_legacy_bcrypt_hash(user.password_hash):
            user.password_hash = self.hash_password(password)
            db.commit()
            db.refresh(user)
        else:
            # Keep Argon2 parameters current over time.
            try:
                if self._password_hasher.check_needs_rehash(user.password_hash):
                    user.password_hash = self.hash_password(password)
                    db.commit()
                    db.refresh(user)
            except Exception:
                pass

        if not user.is_active:
            return None

        return user

    def _create_token(self, user: User, token_type: str, expires_in_seconds: int):
        now = datetime.now(timezone.utc)
        expire_at = now + timedelta(seconds=expires_in_seconds)
        jti = str(uuid.uuid4())

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "type": token_type,
            "jti": jti,
            "iat": int(now.timestamp()),
            "exp": int(expire_at.timestamp()),
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return token, expires_in_seconds

    def create_access_token(self, user: User):
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        return self._create_token(user=user, token_type="access", expires_in_seconds=expires_in)

    def create_refresh_token(self, user: User):
        expires_in = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        token, ttl = self._create_token(
            user=user,
            token_type="refresh",
            expires_in_seconds=expires_in
        )
        payload = self.decode_token(token, verify_exp=False)
        refresh_key = self._refresh_key(str(user.id), payload["jti"])
        self._set_with_ttl(refresh_key, "1", ttl)
        return token, ttl

    def create_token_pair(self, user: User):
        access_token, access_ttl = self.create_access_token(user)
        refresh_token, refresh_ttl = self.create_refresh_token(user)
        return access_token, access_ttl, refresh_token, refresh_ttl

    def decode_token(self, token: str, verify_exp: bool = True):
        options = {"verify_exp": verify_exp}
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options=options,
            )
        except JWTError as exc:
            raise ValueError("Invalid or expired token") from exc

    def decode_access_token(self, token: str):
        payload = self.decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        return payload

    def decode_refresh_token(self, token: str):
        payload = self.decode_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Invalid token type")
        return payload

    def _revoked_key(self, jti: str):
        return f"auth:revoked:{jti}"

    def _refresh_key(self, user_id: str, jti: str):
        return f"auth:refresh:{user_id}:{jti}"

    def revoke_token(self, token: str):
        try:
            payload = self.decode_token(token, verify_exp=False)
        except ValueError:
            return

        exp = int(payload.get("exp", int(time.time()) + 60))
        ttl = exp - int(time.time())
        jti = payload.get("jti")
        if jti:
            self._set_with_ttl(self._revoked_key(jti), "1", ttl)

        if payload.get("type") == "refresh":
            user_id = payload.get("sub")
            if user_id and jti:
                self._delete(self._refresh_key(str(user_id), str(jti)))

    def is_token_revoked(self, token: str):
        try:
            payload = self.decode_token(token, verify_exp=False)
        except ValueError:
            return True

        jti = payload.get("jti")
        if not jti:
            return True

        return self._get(self._revoked_key(jti)) is not None

    def refresh_access_token(self, db: Session, refresh_token: str):
        if self.is_token_revoked(refresh_token):
            raise ValueError("Refresh token has been revoked")

        payload = self.decode_refresh_token(refresh_token)
        user_id = payload.get("sub")
        jti = payload.get("jti")
        if not user_id or not jti:
            raise ValueError("Invalid refresh token")

        refresh_key = self._refresh_key(str(user_id), str(jti))
        if self._get(refresh_key) is None:
            raise ValueError("Refresh token is not active")

        user = self.get_user_by_id(db=db, user_id=user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        self.revoke_token(refresh_token)
        return self.create_token_pair(user)


def get_auth_service() -> AuthService:
    return AuthService()
