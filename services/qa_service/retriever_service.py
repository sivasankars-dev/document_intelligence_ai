import hashlib

from shared.cache import get_cache_service
from shared.config.settings import settings


def _retrieval_cache_key(query: str, document_id: str, top_k: int) -> str:
    q_hash = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
    return f"qa:retrieval:v1:{document_id}:{top_k}:{q_hash}"


def retrieve_document_chunks(query: str, document_id: str, top_k: int = 5):
    cache = get_cache_service()
    cache_key = _retrieval_cache_key(query=query, document_id=document_id, top_k=top_k)
    cached_documents = cache.get_json(cache_key)
    if isinstance(cached_documents, list):
        return cached_documents

    from services.extraction_service.vector_service import collection, embeddings

    query_vector = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        where={"document_id": document_id},
        n_results=top_k
    )

    documents = results.get("documents", [[]])[0]
    cache.set_json(
        cache_key,
        documents,
        ttl_seconds=settings.QA_RETRIEVAL_CACHE_TTL_SECONDS,
    )

    return documents
