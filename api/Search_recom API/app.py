# app.py

from fastapi import FastAPI
from pydantic import BaseModel
from gensim.models import Word2Vec
import pandas as pd
import pickle
import uvicorn

# Load trained model and data
model = Word2Vec.load("word2vec.model")

with open("product_data.pkl", "rb") as f:
    df = pickle.load(f)

app = FastAPI()

class SearchRequest(BaseModel):
    query: str

@app.post("/predict")
def search_word2vec_products(request: SearchRequest):
    search_input = request.query.lower().split()
    search_terms = [word for word in search_input if word in model.wv.key_to_index]

    if not search_terms:
        return {
            "query": request.query,
            "message": "None of the search terms exist in the model vocabulary.",
            "recommendations": []
        }

    similar_words = model.wv.most_similar(positive=search_terms, topn=10)
    similar_keywords = [word for word, _ in similar_words]

    mask = df['Full Description'].str.lower().apply(
        lambda x: any(sim_word in x for sim_word in similar_keywords)
    )

    recommended_products = df[mask][['Product ID', 'Product Name']].drop_duplicates().head(10)

    return {
        "query": request.query,
        "similar_keywords": similar_keywords,
        "recommendations": recommended_products.to_dict(orient="records")
    }

if __name__ == "__main__":
    uvicorn.run(app, host="192.168.0.107", port=1114)
