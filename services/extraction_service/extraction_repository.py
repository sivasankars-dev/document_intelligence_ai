from shared.models.extracted_fact import ExtractedFact
import uuid

def store_extracted_facts(db, document_id: str, facts: list):
    for fact in facts:
        extracted_fact = ExtractedFact(
            id=str(uuid.uuid4()),
            document_id=document_id,
            key=fact["key"],
            value=fact["value"],
            confidence_score=fact["confidence_score"]
        )
        db.add(extracted_fact)
    db.commit()
    
    
