from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared.schemas.user_schema import UserCreate, UserResponse
from shared.database.session import get_db
from services.auth_service.auth_service import AuthService

router = APIRouter()
auth_service = AuthService()


@router.post("/register", response_model=UserResponse)
def register(
    payload: UserCreate,
    db: Session = Depends(get_db)
):
    user = auth_service.create_user(
        db=db,
        email=payload.email,
        password=payload.password
    )

    return user
