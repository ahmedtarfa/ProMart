from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
from get_data_odoo import get_ecommerce_products_from_odoo
from global_store import latest_chroma_path, current_chroma_client
import time, os, gc


def load_and_embed_inventory(collection_name="products_collection"):
    global latest_chroma_path, current_chroma_client

    if current_chroma_client is not None:
        del current_chroma_client
        current_chroma_client = None
        gc.collect()

    time.sleep(2)
    new_path = f"./chroma_store_{time.time()}"
    latest_chroma_path = new_path

    products = get_ecommerce_products_from_odoo()
    if not products:
        print("No products found.")
        return

    model = SentenceTransformer('all-MiniLM-L6-v2')
    descriptions = [
        f"description:{p['description_ecommerce']} price:{p['price']} name:{p['name']}"
        for p in products
    ]
    embeddings = model.encode(descriptions, device='cpu')

    client = PersistentClient(path=new_path)
    current_chroma_client = client

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass

    collection = client.get_or_create_collection(name=collection_name)
    collection.add(
        documents=descriptions,
        embeddings=embeddings.tolist(),
        ids=[str(p['id']) for p in products],
        metadatas=[
            {
                'name': p['name'],
                'id': p['id'],
                'price': p['price'],
                'category': p['ecommerce_categories'],
                'stock': p['stock_quantity']
            } for p in products
        ]
    )

    with open("latest_chroma_path.txt", "w") as f:
        f.write(new_path)

    time.sleep(2)
