import hashlib
import bcrypt
from sqlalchemy.orm import Session
from shared.models.user import User

class AuthService:
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

    def create_user(self, db: Session, email: str, password: str):
        hashed_password = self.hash_password(password)
        user = User(
            email=email,
            password_hash=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return user
