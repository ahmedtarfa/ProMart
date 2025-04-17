import uvicorn
import joblib
from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

app = FastAPI()

predicted_df = joblib.load("predicted_ratings.pkl")
matrix = joblib.load("original_ratings.pkl")

def recommend_products(predictions_df, original_df, user_id, num_recommendations=5):
    # Get user's predictions and sort them in descending order of predicted ratings
    user_predictions = predictions_df.loc[user_id].sort_values(ascending=False)

    # Remove items the user has already rated
    known_ratings = original_df.loc[user_id].dropna().index  # Items the user has already rated
    recommended_items = user_predictions.drop(known_ratings)

    # Select the top N recommendations
    top_recommendations = recommended_items.head(num_recommendations)

    return top_recommendations

class ModelInput(BaseModel):
    user_id: str

@app.post("/predict/")
def recommendtion(user_id: ModelInput):
    recommend_product = recommend_products(predicted_df, matrix, user_id.user_id)

    return [
        {"product_id": idx, "predicted_rating": float(score)}
        for idx, score in recommend_product.items()
    ]

if __name__ == '__main__':
    uvicorn.run(app, host='192.168.1.21', port=1112)