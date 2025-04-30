from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient

# Load model once globally (faster for repeated use)
model = SentenceTransformer('all-MiniLM-L6-v2')


def search_inventory(user_query: str, top_k: int = 5 , chroma_path="./chroma_store",
                     collection_name="products_collection"):
    # Connect to ChromaDB
    client = PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    # Encode query
    query_embedding = model.encode(user_query)

    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Format and return results
    formatted_results = []
    for i in range(len(results['documents'][0])):
        match = {
            "description": results['documents'][0][i],
            "metadata": results['metadatas'][0][i]
        }
        formatted_results.append(match)

    return formatted_results

# if __name__ == '__main__':
#     result = search_inventory("i want a smart phone")
#     print(result)