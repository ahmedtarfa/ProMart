from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import time
from get_data_odoo import get_ecommerce_products_from_odoo

def load_and_embed_inventory(collection_name="products_collection"):
    # Load inventory data from Odoo
    products = get_ecommerce_products_from_odoo()

    if not products:
        print("No products retrieved.")
        return

    # Load embedding model
    model_name = 'all-MiniLM-L6-v2'
    model = SentenceTransformer(model_name)
    device = 'cpu'  # Force CPU usage
    print("Running on CPU.")

    # Extract descriptions for embedding
    descriptions = [p['description_ecommerce'] for p in products]
    start_time = time.time()
    embeddings = model.encode(descriptions, device=device)
    end_time = time.time()
    print(f"Embedding time: {end_time - start_time:.2f} seconds")

    # Set up ChromaDB
    client = PersistentClient(path="./chroma_store")

    # Drop old collection if exists
    try:
        client.delete_collection(name=collection_name)
    except:
        pass

    # Create new collection
    collection = client.get_or_create_collection(name=collection_name)

    # Add embedded products
    collection.add(
        documents=descriptions,
        embeddings=embeddings.tolist(),
        ids=[str(p['id']) if p['id'] else p['name'] for p in products],
        metadatas=[
            {
                'name': p['name'],
                'id': p['id'],
                'price': p['price'],
                'category': p['ecommerce_categories'],
                'stock': p['stock_quantity']
            }
            for p in products
        ]
    )

if __name__ == "__main__":
    total_start_time = time.time()
    load_and_embed_inventory()
    print(f"Total time: {time.time() - total_start_time:.2f} seconds")
