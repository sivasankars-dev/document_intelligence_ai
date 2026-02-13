from services.extraction_service.vector_service import collection, embeddings

def retrieve_document_chunks(query: str, document_id: str, top_k: int = 5):
    query_vector = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        where={"document_id": document_id},
        n_results=top_k
    )

    documents = results.get("documents", [[]])[0]

    return documents
