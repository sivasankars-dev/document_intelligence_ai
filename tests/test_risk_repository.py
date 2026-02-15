import uuid

from shared.models.risk import Risk
from services.risk_service.risk_repository import RiskRepository

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


def test_create_risk():
    db_session = FakeDBSession()
    risk = Risk(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        description="Payment missed",
        severity="HIGH",
    )

    created = RiskRepository.create(db_session, risk)

    assert created is risk
    assert db_session.added == [risk]
    assert db_session.committed is True
    assert db_session.refreshed == [risk]
