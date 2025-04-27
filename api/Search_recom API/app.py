from sentence_transformers import SentenceTransformer
from chromadb import PersistentClient
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app=FastAPI()
df = pd.read_csv("all products.csv", encoding='ISO-8859-1')
df = df[["Product ID","Yahoo Image URL"]]
# Load model once globally and force it to use CUDA if available
model = SentenceTransformer('all-MiniLM-L6-v2')
device = "cuda" if model.device.type == "cuda" else "cpu"

class SearchRequest(BaseModel):
    query: str

def search_inventory(user_query: str, top_k: int = 5, chroma_path="./chroma_store",
                     collection_name="products_collection"):
    # Connect to ChromaDB
    client = PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(name=collection_name)

    # Encode query with device
    query_embedding = model.encode(user_query, device=device)

    # Search
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )

    # Format and return results
    formatted_results = []
    for i in range(len(results['documents'][0])):
        match = {
            "Product Name": results['documents'][0][i],
            "metadata": results['metadatas'][0][i]
        }
        formatted_results.append(match)

    return formatted_results

@app.post("/predict")
def search_product(request: SearchRequest):
    search_input = request.query
    results = search_inventory(search_input)

    search_results = []

    # Loop through the results and gather the details
    for i, item in enumerate(results, start=1):
        product_info = {
            "Product Name": item['Product Name'],
            "metadata": item["metadata"],
            "Yahoo Image URL": None  # Default value in case no image is found
        }

        metadata = item["metadata"]
        product_id = metadata.get('Product ID')

        # Now get the Yahoo Image URL for the matching Product ID
        matching_row = df[df["Product ID"] == product_id]

        if not matching_row.empty:
            product_info["Yahoo Image URL"] = matching_row.iloc[0]['Yahoo Image URL']
        else:
            product_info["Yahoo Image URL"] = "Not found"

        # Add the product info to the results list
        search_results.append(product_info)

    return {"search_results": search_results}

if __name__ == "__main__":
    uvicorn.run(app, host="192.168.0.105", port=1114)
