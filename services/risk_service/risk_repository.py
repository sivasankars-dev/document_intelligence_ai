from sqlalchemy.orm import Session
from shared.models.risk import Risk

class RiskRepository:
    @staticmethod
    def create(db: Session, risk: Risk):
        db.add(risk)
        db.commit()
        db.refresh(risk)
        return risk

    @staticmethod
    def get_by_document(db: Session, document_id):
        return (
            db.query(Risk)
            .filter(Risk.document_id == document_id)
            .order_by(Risk.created_at.desc())
            .all()
        )
