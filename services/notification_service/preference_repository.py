from types import SimpleNamespace

from shared.cache import get_cache_service
from shared.config.settings import settings
from shared.models.notification_preference import NotificationPreference


def _cache_key(user_id) -> str:
    return f"notification:pref:v1:{user_id}"


def _serialize(pref: NotificationPreference) -> dict:
    return {
        "id": str(pref.id) if pref.id else None,
        "user_id": str(pref.user_id) if pref.user_id else None,
        "channel_priority": pref.channel_priority or ["email", "push", "sms"],
        "email_enabled": bool(pref.email_enabled),
        "sms_enabled": bool(pref.sms_enabled),
        "push_enabled": bool(pref.push_enabled),
        "quiet_hours_start": pref.quiet_hours_start,
        "quiet_hours_end": pref.quiet_hours_end,
    }


def get_user_preferences(db, user_id):
    cache = get_cache_service()
    key = _cache_key(user_id)
    cached = cache.get_json(key)
    if isinstance(cached, dict):
        return SimpleNamespace(**cached)

    pref = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )
    if pref is None:
        return None

    cache.set_json(
        key,
        _serialize(pref),
        ttl_seconds=settings.NOTIFICATION_PREF_CACHE_TTL_SECONDS,
    )
    return pref


def upsert_user_preferences(db, user_id, payload: dict):
    pref = (
        db.query(NotificationPreference)
        .filter(NotificationPreference.user_id == user_id)
        .first()
    )
    if pref is None:
        pref = NotificationPreference(user_id=user_id)
        db.add(pref)

    for field in [
        "channel_priority",
        "email_enabled",
        "sms_enabled",
        "push_enabled",
        "quiet_hours_start",
        "quiet_hours_end",
    ]:
        if field in payload and payload[field] is not None:
            setattr(pref, field, payload[field])

    db.commit()
    db.refresh(pref)

    cache = get_cache_service()
    key = _cache_key(user_id)
    cache.set_json(
        key,
        _serialize(pref),
        ttl_seconds=settings.NOTIFICATION_PREF_CACHE_TTL_SECONDS,
    )
    return pref
