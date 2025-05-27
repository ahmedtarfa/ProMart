from typing import List, Dict, Annotated
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from load_data import load_and_embed_inventory
from search_inventory import search_inventory
from get_product import bot_response_with_odoo_url  # Renamed for clarity
import google.generativeai as genai
import os
from dotenv import load_dotenv
from googletrans import Translator
import re

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

inventory_loaded = False

def refresh_inventory_data():
    global inventory_loaded
    load_and_embed_inventory()
    inventory_loaded = True

def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate_text_if_arabic(text: str, target_language: str = "en") -> str:
    if contains_arabic(text):
        translator = Translator()
        translated = translator.translate(text, dest=target_language)
        return translated.text
    else:
        return text

def send_data(query: str, history: List[Dict[str, str]]) -> str:
    historical_context = "\n".join([f"User: {item['user']}\nAssistant: {item['assistant']}" for item in history[-2:]]) # Consider the last 1-2 turns
    context = search_inventory(translate_text_if_arabic(query))

    prompt_text = f"""
        You are a professional sales assistant for an inventory of products.
        The customer may ask detailed about the products.
        Always do your best to suggest the closest matching product from the inventory, even if it's not an exact match.
        **Prioritize finding direct product matches for the customer's request.**
        Be confident like a real salesperson trying to help the customer find the best alternative.
        If descriptions are incomplete, you may search the web with the product name to get more details.

        - If the customer asks in Arabic, always reply in Egyptian Arabic in a natural, friendly style.
        - If the customer asks in English, reply in English.
        - If you cannot understand the Arabic question, politely ask the customer to rephrase in Arabic, still using Egyptian Arabic.

        If the exact answer is not in the context,
        recommend the nearest product that matches what the customer is looking for.
        **Only if absolutely nothing in the provided context is a close match to the customer's primary request (e.g., if they ask for a phone and the context only has message books), then say:** "I don't have enough information to answer that."
        Each product you talk about you should write " link --> <<Product ID int only>>" replacing Product ID with the one from the context and product_name also.
        Please keep product IDs exactly as given in the context, do NOT change or invent new IDs.

        Only mention stock availability as 'in stock' or 'out of stock' — no quantities.

        Make the response well-structured, like splitting the list of products you are listing.

        Here is the context (top products from search):
        {context}

        Recent conversation:
        {historical_context}

        Customer Query:
        {query}

        Your Answer:
    """
    response_text_from_gemini = model.generate_content(prompt_text).text
    final_response = bot_response_with_odoo_url(response_text_from_gemini)
    print(final_response)
    return final_response


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
    history: List[Dict[str, str]]  # Include the updated history in the response


@app.get("/refresh_inventory/")
async def refresh_inventory():
    try:
        refresh_inventory_data()
        print("FINISH LOAD DATA")
        return {"status": "success", "message": "Inventory refreshed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

    print("Start bot\n")
    ip = os.getenv("IP")
    uvicorn.run(app, host=ip, port=2020)
