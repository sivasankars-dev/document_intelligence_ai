from types import SimpleNamespace

from services.notification_service.preference_repository import get_user_preferences


class _FakeCache:
    def __init__(self):
        self.store = {}

    def get_json(self, key):
        return self.store.get(key)

    def set_json(self, key, value, ttl_seconds):
        self.store[key] = value


class _FakeQuery:
    def __init__(self, preference, calls):
        self.preference = preference
        self.calls = calls

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        self.calls["count"] += 1
        return self.preference


class _FakeDB:
    def __init__(self, preference, calls):
        self.preference = preference
        self.calls = calls

    def query(self, _model):
        return _FakeQuery(self.preference, self.calls)


def test_get_user_preferences_uses_cache(monkeypatch):
    fake_cache = _FakeCache()
    monkeypatch.setattr(
        "services.notification_service.preference_repository.get_cache_service",
        lambda: fake_cache,
    )

    calls = {"count": 0}
    preference = SimpleNamespace(
        id="pref-1",
        user_id="user-1",
        channel_priority=["email", "push", "sms"],
        email_enabled=True,
        sms_enabled=False,
        push_enabled=True,
        quiet_hours_start="22:00",
        quiet_hours_end="06:00",
    )
    db = _FakeDB(preference, calls)

    first = get_user_preferences(db, "user-1")
    second = get_user_preferences(db, "user-1")

    assert first.user_id == "user-1"
    assert second.user_id == "user-1"
    assert calls["count"] == 1
