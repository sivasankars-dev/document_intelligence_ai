from sqlalchemy.orm import Session
from shared.models.obligation import Obligation

class ObligationRepository:
    @staticmethod
    def create(db: Session, obligation: Obligation):
        db.add(obligation)
        db.commit()
        db.refresh(obligation)
        return obligation

    @staticmethod
    def get_by_document(db: Session, document_id):
        return (
            db.query(Obligation)
            .filter(Obligation.document_id == document_id)
            .all()
        )
