import hashlib

from shared.cache import get_cache_service
from shared.config.settings import settings


def _retrieval_cache_key(query: str, document_id: str, top_k: int) -> str:
    q_hash = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()
    return f"qa:retrieval:v1:{document_id}:{top_k}:{q_hash}"


def retrieve_document_evidence(query: str, document_id: str, top_k: int = 5):
    cache = get_cache_service()
    cache_key = _retrieval_cache_key(query=query, document_id=document_id, top_k=top_k)
    cached_evidence = cache.get_json(cache_key)
    if isinstance(cached_evidence, list):
        return cached_evidence

    from services.extraction_service.vector_service import collection, embeddings

    query_vector = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_vector],
        where={"document_id": document_id},
        n_results=top_k
    )

    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    evidence = []
    for idx, text in enumerate(documents):
        metadata = metadatas[idx] if idx < len(metadatas) and isinstance(metadatas[idx], dict) else {}
        evidence.append(
            {
                "chunk_id": ids[idx] if idx < len(ids) else None,
                "document_id": metadata.get("document_id", document_id),
                "chunk_index": metadata.get("chunk_index", idx),
                "text": text,
                "distance": distances[idx] if idx < len(distances) else None,
            }
        )

    cache.set_json(
        cache_key,
        evidence,
        ttl_seconds=settings.QA_RETRIEVAL_CACHE_TTL_SECONDS,
    )

    return evidence


def retrieve_document_chunks(query: str, document_id: str, top_k: int = 5):
    evidence = retrieve_document_evidence(query=query, document_id=document_id, top_k=top_k)
    return [item.get("text", "") for item in evidence if item.get("text")]
