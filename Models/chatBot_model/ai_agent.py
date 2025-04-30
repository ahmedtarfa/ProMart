from typing import List, Dict, Annotated
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from load_data import load_and_embed_inventory
from search_inventory import search_inventory
import google.generativeai as genai

GOOGLE_API_KEY = "AIzaSyC3TgIJ6txQgv47pQn-8Y4i_E1ScF8wZ2o"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

inventory_loaded = False

def refresh_inventory_data():
    global inventory_loaded
    load_and_embed_inventory(csv_path="data/inventory.csv")
    inventory_loaded = True

def send_data(query: str, history: List[Dict[str, str]]) -> str:
    historical_context = "\n".join([f"User: {item['user']}\nAssistant: {item['assistant']}" for item in history[-2:]]) # Consider the last 1-2 turns
    augmented_query = f"{historical_context}\nUser: {query}" if history else query
    context = search_inventory(augmented_query)

    prompt_text =  f"""
        You are a professional sales assistant for an inventory of products.
        The customer may ask detailed about the products.
        Always do your best to suggest the closest matching product from the inventory, even if it's not an exact match.
        Be confident like a real salesperson trying to help the customer find the best alternative.
        if information of the descriptions is incomplete so you can search in web with same product name.

        If the exact answer is not in the context,
        recommend the nearest product that matches what the customer is looking for.
        Only if absolutely nothing is close, then say: "I don't have enough information to answer that."
        i customer ask you in arabic answer with arabic you may answer with egypt local language

        Only mention stock availability as 'in stock' or 'out of stock' — no quantities.

        Here is the context (top products from search):
        {context}

        Recent conversation:
        {historical_context}

        Customer Query:
        {query}

        Your Answer:
    """
    response = model.generate_content(prompt_text)
    return response.text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    history: List[Dict[str, str]] # Include the updated history in the response

@app.on_event("startup")
async def startup_event():
    refresh_inventory_data()
    if not inventory_loaded:
        print("Warning: Inventory data loading might have failed.")

@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not inventory_loaded:
        raise HTTPException(status_code=503, detail="Inventory data is not loaded yet.")
    try:
        response_text = send_data(request.query, request.history)
        updated_history = request.history + [{"user": request.query, "assistant": response_text}]
        return ChatResponse(response=response_text, history=updated_history)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing the query: {e}")

if __name__ == "__main__":
    import uvicorn
    refresh_inventory_data() # Load data if running directly for debugging
    uvicorn.run(app, host="192.168.0.105", port=2020)