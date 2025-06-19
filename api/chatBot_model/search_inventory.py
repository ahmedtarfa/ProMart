from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from chromadb.config import Settings
import os

model = SentenceTransformer('all-MiniLM-L6-v2')

def search_inventory(keywords: list[str], collection_name="products_collection"):
    if not os.path.exists("latest_chroma_path.txt"):
        return []

    with open("latest_chroma_path.txt") as f:
        path = f.read().strip()
        print("\npath",path)

    if not os.path.exists(path):
        return []

    client = PersistentClient(path=path, settings=Settings(allow_reset=True))
    collection = client.get_or_create_collection(name=collection_name)

    if not keywords:
        return []

    # Encode all keywords
    query_vectors = model.encode(keywords)

    all_results = []
    seen_ids = set()

    for vector in query_vectors:
        results = collection.query(query_embeddings=[vector], n_results=5)

        if not results or not results['documents'] or not results['documents'][0]:
            continue

        for i in range(len(results['documents'][0])):
            metadata = results['metadatas'][0][i]
            if metadata['id'] not in seen_ids:
                seen_ids.add(metadata['id'])
                all_results.append({
                    "description": results['documents'][0][i],
                    "metadata": metadata
                })

    return all_results
