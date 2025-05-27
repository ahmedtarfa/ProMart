from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib
import uvicorn
import pickle

app = FastAPI()

# Load customer data from pickle
try:
    with open('customer_recommendation_data.pkl', 'rb') as f:
        customer_data = pickle.load(f)
    print("Customer data loaded successfully.")
    print("First 5 rows:")
    print(customer_data.head())
except Exception as e:
    print(f"Error loading customer data: {e}")
    customer_data = None

# Load product data
try:
    product_data = pd.read_csv("all products.csv")
    print("Product data loaded successfully.")
except Exception as e:
    print(f"Error loading product data: {e}")
    product_data = None

# Load original interactions
try:
    original_interactions = joblib.load("original_ratings.pkl")
    print("Original interactions loaded successfully.")
except Exception as e:
    print(f"Error loading original interactions: {e}")
    original_interactions = None

# Load predicted ratings
try:
    predicted_ratings = joblib.load("predicted_ratings.pkl")
    print("Predicted ratings loaded successfully.")
except Exception as e:
    print(f"Error loading predicted ratings: {e}")
    predicted_ratings = None


# Request Model
class UserRequest(BaseModel):
    customer_id: str = None


# Recommendation logic
def recommend_products(predicted_ratings, original_interactions, user_id, num_recommendations=20):
    try:
        if user_id not in predicted_ratings.index:
            print(f"User ID '{user_id}' not found in predictions.")
            return pd.Series(dtype='float64')

        user_predictions = predicted_ratings.loc[user_id].sort_values(ascending=False)

        known_interactions = (
            original_interactions.loc[user_id].dropna().index
            if original_interactions is not None and user_id in original_interactions.index
            else pd.Index([])
        )

        recommended_items = user_predictions.drop(known_interactions, errors='ignore')
        print("Recommended product IDs:", recommended_items.head(num_recommendations).index.tolist())
        return recommended_items.head(num_recommendations)
    except Exception as e:
        print(f"Error in recommend_products: {e}")
        return pd.Series(dtype='float64')


def format_recommendations(df):
    if df is None or df.empty:
        return []

    df = df.replace([float('inf'), float('-inf')], pd.NA).fillna({
        'Price': 0.0,
        'Product Name_y': '',
        'Product Description': '',
        'Category': '',
        'Yahoo Image URL': ''
    })

    return [{
        'id': row.get('Product ID'),
        'product_name': row.get('Product Name_y'),
        'product_description': row.get('Product Description'),
        'price': float(row.get('Price')) if pd.notnull(row.get('Price')) else 0.0,
        'category': row.get('Category'),
        'image_url': row.get('Yahoo Image URL')
    } for _, row in df.iterrows()]


@app.post("/recommend_by_user")
def recommend_products_by_user(request: UserRequest):
    user_id = request.customer_id
    print(f"Received user ID: {user_id}")

    if predicted_ratings is None or customer_data is None or product_data is None:
        return {"status": "error", "message": "Data not loaded correctly.", "recommendations": []}

    if user_id in predicted_ratings.index:
        recommended_series = recommend_products(predicted_ratings, original_interactions, user_id)

        if recommended_series.empty:
            return {
                "status": "success",
                "user_id": user_id,
                "message": "No new recommendations available.",
                "recommendations": []
            }

        recommended_df = product_data[
            product_data['Product ID'].isin(recommended_series.index)
        ][[
            'Product ID', 'Product Name', 'Product Description', 'Price', 'Category', 'Yahoo Image URL'
        ]].drop_duplicates(subset=['Product ID'])

        # Fix column naming for consistency
        recommended_df = recommended_df.rename(columns={'Product Name': 'Product Name_y'})

        formatted = format_recommendations(recommended_df)

        return {
            "status": "success",
            "user_id": user_id,
            "message": "Recommendations fetched successfully.",
            "recommendations": formatted
        }

    # If user_id not found, fallback to top-selling products
    top_selling_ids = customer_data.groupby('Product ID')['Order ID'].count().sort_values(ascending=False).head(50).index
    top_df = customer_data[customer_data['Product ID'].isin(top_selling_ids)][[
        'Product ID', 'Product Name_y', 'Product Description', 'Price', 'Rate', 'Category', 'Yahoo Image URL'
    ]].drop_duplicates(subset=['Product ID'])

    grouped = {
        category: format_recommendations(group)
        for category, group in top_df.groupby('Category')
    }

    return {
        "status": "success",
        "message": "Top selling products returned by category.",
        "recommendations": grouped
    }


@app.get("/high_sales_product_recommendation")
def get_high_sales_products():
    if customer_data is None:
        return {"status": "error", "message": "Customer data not loaded.", "recommendations": []}

    top_selling_ids = customer_data.groupby('Product ID')['Order ID'].count().sort_values(ascending=False).head(50).index
    top_df = customer_data[customer_data['Product ID'].isin(top_selling_ids)][[
        'Product ID', 'Product Name_y', 'Product Description', 'Price', 'Rate', 'Category', 'Yahoo Image URL'
    ]].drop_duplicates(subset=['Product ID'])

    grouped = {
        category: format_recommendations(group)
        for category, group in top_df.groupby('Category')
    }

    return {
        "status": "success",
        "message": "Top selling products returned by category.",
        "recommendations": grouped
    }


if __name__ == "__main__":
    uvicorn.run(app, host="11.11.11.17", port=1115)