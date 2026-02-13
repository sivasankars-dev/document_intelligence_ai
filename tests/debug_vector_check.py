import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.extraction_service.vector_service import collection, embeddings


def main():
    parser = argparse.ArgumentParser(description="Debug Chroma vector search")
    parser.add_argument(
        "--query",
        default="insurance renewal date",
        help="Natural-language query text",
    )
    parser.add_argument(
        "--doc-id",
        default=None,
        help="Optional document_id filter",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of results to return",
    )
    args = parser.parse_args()

    query_vector = embeddings.embed_query(args.query)

    query_kwargs = {
        "query_embeddings": [query_vector],
        "n_results": args.top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if args.doc_id:
        query_kwargs["where"] = {"document_id": args.doc_id}

    results = collection.query(**query_kwargs)
    ids = (results.get("ids") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    print("\n===== VECTOR SEARCH RESULTS =====")
    print(f"query={args.query!r} top_k={args.top_k} doc_id={args.doc_id}")
    print(f"matched={len(ids)}")

    for idx, item_id in enumerate(ids):
        preview = documents[idx][:200].replace("\n", " ") if idx < len(documents) else ""
        metadata = metadatas[idx] if idx < len(metadatas) else {}
        distance = distances[idx] if idx < len(distances) else None
        print(f"\n#{idx + 1}")
        print(f"id: {item_id}")
        print(f"distance: {distance}")
        print(f"metadata: {metadata}")
        print(f"preview: {preview}")


if __name__ == "__main__":
    main()
