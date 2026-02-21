import uuid
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

    vectors = embeddings.embed_documents(chunks)
    ids = [str(uuid.uuid4()) for _ in chunks]
    metadata = [{"document_id": document_id} for _ in chunks]
    collection.add(
        documents=chunks,
        embeddings=vectors,
        ids=ids,
        metadatas=metadata
    )
