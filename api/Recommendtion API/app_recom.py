from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import pickle
import uvicorn

# Load trained recommendation data and ratings files
try:
    with open("customer_recommendation_data.pkl", "rb") as f:
        customer_data = pickle.load(f)
    print("Customer recommendation data loaded successfully.")
except Exception as e:
    print(f"Error loading customer recommendation data: {e}")
    customer_data = None

# Load rating data
try:
    with open("original_ratings.pkl", "rb") as f:
        original_ratings = pickle.load(f)
    print("Original ratings data loaded successfully.")
except Exception as e:
    print(f"Error loading original ratings data: {e}")
    original_ratings = None

try:
    with open("predicted_ratings.pkl", "rb") as f:
        predicted_ratings = pickle.load(f)
    print("Predicted ratings data loaded successfully.")
except Exception as e:
    print(f"Error loading predicted ratings data: {e}")
    predicted_ratings = None

app = FastAPI()

class UserRequest(BaseModel):
    customer_id: str = None  # Optional field for customer ID

def format_recommendations(df):
    """Format the DataFrame to return it as a list of dicts with proper keys."""
    if df is None or df.empty:
        return []

    df = df.rename(columns={
        'Product ID': 'id',
        'Product Name': 'product_name',
        'Product Description': 'product_description',
        'price': 'price',
        'Rate': 'rate',
        'Category': 'category',
        'Yahoo Image URL': 'image_url'
    })

    return df.to_dict(orient="records")

@app.post("/recommend_by_user")
def recommend_products_by_user(request: UserRequest):
    if customer_data is None:
        return {
            "status": "error",
            "message": "Customer recommendation data not loaded.",
            "recommendations": []
        }

    customer_id = request.customer_id

    if customer_id and customer_id in original_ratings['Customer ID'].values:
        # Use original and predicted ratings for logged-in user
        user_original_ratings = original_ratings[original_ratings['Customer ID'] == customer_id]
        user_predicted_ratings = predicted_ratings[predicted_ratings['Customer ID'] == customer_id]

        # Merge original and predicted ratings
        user_ratings = pd.merge(user_original_ratings, user_predicted_ratings, on='Product ID', suffixes=('_original', '_predicted'))

        # Filter products with rate >= 3
        user_ratings = user_ratings[user_ratings['Rate_predicted'] >= 3]
        user_ratings = user_ratings.sort_values(by='Rate_predicted', ascending=False)

        # Take the top 5 recommendations based on predicted ratings
        recommended_products = user_ratings.head(5)

        print("Recommendations for customer:", recommended_products.to_dict(orient="records"))

        return {
            "status": "success",
            "customer_id": customer_id,
            "message": "Recommendations fetched successfully.",
            "recommendations": format_recommendations(recommended_products)
        }
    else:
        # If no customer_id or not logged in, show top-rated products for each category
        if customer_data is None:
            return {
                "status": "error",
                "message": "Customer recommendation data not loaded.",
                "recommendations": []
            }

        # Get all unique products with rate >= 3
        high_rate_products = customer_data[customer_data['Rate'] >= 3][['Product ID', 'Product Name', 'Product Description', 'price', 'Rate', 'Category', 'Yahoo Image URL']].drop_duplicates()

        # Exclude products with any missing attribute
        high_rate_products = high_rate_products.dropna(subset=['Product Name', 'Product Description', 'Yahoo Image URL', 'Rate', 'Category', 'price'])

        # Sort by rate descending and take the top 5 per category
        high_rate_products = high_rate_products.sort_values(by='Rate', ascending=False)

        # Group by category and take the top 5 products for each category
        top_products_per_category = high_rate_products.groupby('Category').head(5)

        print("High rate recommendations:", top_products_per_category.to_dict(orient="records"))

        return {
            "status": "success",
            "message": "Top rated recommendations fetched successfully.",
            "recommendations": format_recommendations(top_products_per_category)
        }

@app.get("/high_rate_recommendations")
def get_high_rate_recommendations():
    if customer_data is None:
        return {
            "status": "error",
            "message": "Customer recommendation data not loaded.",
            "recommendations": []
        }

    # Get all unique products with rate >= 3
    high_rate_products = customer_data[customer_data['Rate'] >= 3][['Product ID', 'Product Name', 'Product Description', 'price', 'Rate', 'Category', 'Yahoo Image URL']].drop_duplicates()

    # Exclude products with any missing attribute
    high_rate_products = high_rate_products.dropna(subset=['Product Name', 'Product Description', 'Yahoo Image URL', 'Rate', 'Category', 'price'])

    # Sort by rate descending and take the top 5
    top_rated_products = high_rate_products.sort_values(by='Rate', ascending=False).head(20)

    print("High rate recommendations:", top_rated_products.to_dict(orient="records"))

    return {
        "status": "success",
        "message": "Top rated recommendations fetched successfully.",
        "recommendations": format_recommendations(top_rated_products)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="192.168.1.90", port=1115)  # Note: different port if needed