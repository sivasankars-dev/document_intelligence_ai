from shared.database.session import SessionLocal

from services.qa_service.retriever_service import retrieve_document_chunks
from services.extraction_service.extraction_prompt import build_extraction_prompt
from services.extraction_service.extraction_llm import run_extraction_llm
from services.extraction_service.extraction_repository import save_extracted_facts



def run_extraction_pipeline(document_id: str):
    db = SessionLocal()
    # Step 1: Retrieve relevant document chunks
    try:
        chunks = retrieve_document_chunks(query="Extract facts", document_id=document_id, top_k=5)
        if not chunks:
            return
        prompt = build_extraction_prompt(chunks)
        facts  = run_extraction_llm(prompt)
        save_extracted_facts(db, document_id=document_id, facts=facts)
        
    except Exception as e:
        print(f"Error retrieving document chunks: {e}")
        return   
    finally:
        db.close()


# Backward-compatible alias
extraction_pipeline = run_extraction_pipeline
