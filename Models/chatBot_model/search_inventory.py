from chromadb import PersistentClient
from sentence_transformers import SentenceTransformer
from chromadb.config import Settings
import os

model = SentenceTransformer('all-MiniLM-L6-v2')


def search_inventory(query, collection_name="products_collection"):
    if not os.path.exists("latest_chroma_path.txt"):
        return []

    with open("latest_chroma_path.txt") as f:
        path = f.read().strip()

    if not os.path.exists(path):
        return []

    client = PersistentClient(path=path, settings=Settings(allow_reset=True))
    collection = client.get_or_create_collection(name=collection_name)

    query_vector = model.encode([query])[0]

    results = collection.query(query_embeddings=[query_vector], n_results=5)

    if not results or not results['documents'] or not results['documents'][0]:
        return []

    return [
        {
            "description": results['documents'][0][i],
            "metadata": results['metadatas'][0][i]
        }
        for i in range(len(results['documents'][0]))
    ]
