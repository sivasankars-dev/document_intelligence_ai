import hashlib
import chromadb
from chromadb.config import Settings
from langchain_openai import OpenAIEmbeddings

from services.extraction_service.chunking_service import chunk_text
from shared.config.settings import settings

CHROMA_DIR = settings.CHROMA_DIR

# Initialize persistent Chroma client
chroma_client = chromadb.PersistentClient(
    path=CHROMA_DIR,
    settings=Settings(anonymized_telemetry=False),
)

collection = chroma_client.get_or_create_collection(
    name="document_knowledge"
)


class _LazyEmbeddings:
    def __init__(self):
        self._instance = None

    def _get_instance(self):
        if self._instance is None:
            self._instance = OpenAIEmbeddings()
        return self._instance

    def __getattr__(self, name):
        return getattr(self._get_instance(), name)


embeddings = _LazyEmbeddings()

def store_document_chunks(document_id: str, text: str):
    chunks = chunk_text(text)

    if not chunks:
        return

    # Keep chunk IDs stable and avoid duplicate rows on re-ingestion.
    try:
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass

    vectors = embeddings.embed_documents(chunks)
    ids = []
    metadata = []
    for idx, chunk in enumerate(chunks):
        chunk_hash = hashlib.sha1(chunk.encode("utf-8")).hexdigest()[:12]
        chunk_id = f"{document_id}:{idx}:{chunk_hash}"
        ids.append(chunk_id)
        metadata.append({"document_id": document_id, "chunk_index": idx})

    collection.add(
        documents=chunks,
        embeddings=vectors,
        ids=ids,
        metadatas=metadata
    )
