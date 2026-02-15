import uuid

from shared.models.obligation import Obligation
from services.obligation_service.obligation_repository import ObligationRepository


class FakeDBSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = []

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        self.committed = True

    def refresh(self, obj):
        self.refreshed.append(obj)


def test_create_obligation():
    db_session = FakeDBSession()
    obligation = Obligation(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Insurance Renewal",
        status="PENDING",
    )

    created = ObligationRepository.create(db_session, obligation)

    assert created is obligation
    assert db_session.added == [obligation]
    assert db_session.committed is True
    assert db_session.refreshed == [obligation]
