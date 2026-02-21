from sqlalchemy.orm import Session
from shared.models.risk import Risk

class RiskRepository:
    @staticmethod
    def create(db: Session, risk: Risk):
        db.add(risk)
        db.commit()
        db.refresh(risk)
        return risk
