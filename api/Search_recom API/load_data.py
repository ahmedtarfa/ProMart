import pandas as pd
from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import torch  # Import PyTorch
import time

def load_and_embed_inventory(csv_path="inventory.csv", collection_name="products_collection"):
    # Load inventory data
    df = pd.read_csv(csv_path)

    # Loadx embedding model and move it to the GPU if available
    model_name = 'all-MiniLM-L6-v2'
    model = SentenceTransformer(model_name)
    if torch.cuda.is_available():
        device = 'cuda'
    else:
        device = 'cpu'
        print("CUDA not available, using CPU.")
    model.to(device)

    start_time = time.time()
    embeddings = model.encode(df['Product Description'].tolist(), device=device)
    end_time = time.time()
    embedding_time = end_time - start_time
    print(f"Embedding time: {embedding_time:.2f} seconds")
    df['embedding'] = embeddings.tolist()

    # Set up ChromaDB with persistence
    client = PersistentClient(path="./chroma_store")

    # Drop existing collection if exists
    try:
        client.delete_collection(name=collection_name)
    except:
        pass

    # Create fresh collection
    collection = client.get_or_create_collection(name=collection_name)

    # Add data
    df['full_description'] = df['Product Name Cleaned'] + ". " + df['Product Description']

    collection.add(
        documents=df['full_description'].tolist(),
        metadatas=df[['Product ID', 'Product Name Cleaned', 'Price','Product Description']].to_dict(orient='records'),
        ids=df['Product ID'].astype(str).tolist(),
        embeddings=df['embedding'].tolist()
    )


if __name__ == "__main__":
    total_start_time = time.time()
    load_and_embed_inventory()
    total_end_time = time.time()
    total_time = total_end_time - total_start_time