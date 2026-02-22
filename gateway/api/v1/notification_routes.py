from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from gateway.dependencies.auth import get_current_user
from shared.database.session import get_db
from shared.schemas.notification_schema import (
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from services.notification_service.preference_repository import (
    get_user_preferences,
    upsert_user_preferences,
)


router = APIRouter()


@router.get("/preferences", response_model=NotificationPreferenceResponse)
def get_preferences(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    pref = get_user_preferences(db, user["user_id"])
    if pref is None:
        pref = upsert_user_preferences(
            db,
            user["user_id"],
            {
                "channel_priority": ["email", "push", "sms"],
                "email_enabled": True,
                "sms_enabled": False,
                "push_enabled": True,
                "quiet_hours_start": None,
                "quiet_hours_end": None,
            },
        )

    return NotificationPreferenceResponse(
        channel_priority=list(pref.channel_priority or ["email", "push", "sms"]),
        email_enabled=bool(pref.email_enabled),
        sms_enabled=bool(pref.sms_enabled),
        push_enabled=bool(pref.push_enabled),
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
    )


@router.post("/preferences", response_model=NotificationPreferenceResponse)
def update_preferences(
    payload: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    pref = upsert_user_preferences(db, user["user_id"], payload.model_dump(exclude_unset=True))
    return NotificationPreferenceResponse(
        channel_priority=list(pref.channel_priority or ["email", "push", "sms"]),
        email_enabled=bool(pref.email_enabled),
        sms_enabled=bool(pref.sms_enabled),
        push_enabled=bool(pref.push_enabled),
        quiet_hours_start=pref.quiet_hours_start,
        quiet_hours_end=pref.quiet_hours_end,
    )
