import hashlib
import uuid
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from shared.config.settings import settings
from shared.models.user import User

class AuthService:
    _revoked_tokens: set[str] = set()

    def _pre_hash(self, password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def hash_password(self, password: str):
        pre_hashed = self._pre_hash(password)
        hashed = bcrypt.hashpw(pre_hashed.encode("utf-8"), bcrypt.gensalt())
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str):
        pre_hashed = self._pre_hash(plain_password)
        return bcrypt.checkpw(
            pre_hashed.encode("utf-8"),
            hashed_password.encode("utf-8")
        )

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

        if not user.is_active:
            return None

        return user

    def create_access_token(self, user: User):
        now = datetime.now(timezone.utc)
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        expire_at = now + timedelta(seconds=expires_in)

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "type": "access",
            "jti": str(uuid.uuid4()),
            "iat": int(now.timestamp()),
            "exp": int(expire_at.timestamp()),
        }
        token = jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return token, expires_in

    def decode_access_token(self, token: str):
        try:
            return jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except JWTError as exc:
            raise ValueError("Invalid or expired token") from exc

    def revoke_token(self, token: str):
        self._revoked_tokens.add(token)

    def is_token_revoked(self, token: str):
        return token in self._revoked_tokens


def get_auth_service() -> AuthService:
    return AuthService()
