from typing import List, Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from search_inventory import search_inventory
from get_product_url import bot_response_with_odoo_url
import google.generativeai as genai
import os
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
import re
import traceback

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

inventory_loaded = True  # You can later refresh in background

def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate_text_if_arabic(text: str, target_language: str = "en") -> str:
    if contains_arabic(text):
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    return text

def format_result_for_prompt(results):
    return "\n".join(
        f"{i+1}. {item['metadata']['name']} (ID: {item['metadata']['id']}) - {item['description']}"
        for i, item in enumerate(results)
    )

def send_data(query: str, history: List[Dict[str, str]]) -> str:
    context = search_inventory(translate_text_if_arabic(query))
    context_text = format_result_for_prompt(context)

    historical_context = "\n".join(
        [f"User: {item['user']}\nAssistant: {item['assistant']}" for item in history[-2:]]
    )

    prompt_text = f"""
    Your name is "aseel" in Arabic "أصيل" with model name "mart-v01" and you work for "proMart".
    You are a professional sales assistant for an inventory of products.
    Always suggest the closest matching product from the inventory.
    Prioritize matching real products and be confident and helpful.

    - If the customer asks in Arabic, reply in Egyptian Arabic.
    - If in English, reply in English.
    - Donot replay with multiple language unless customer ask you.
    - Mention product like this: link --> <<Product ID>> , product id is decimal only between <<id>>.

    Show availability as 'in stock' or 'out of stock' only.
    Split multiple products into a clean structured list.

    If no good match, say: "I don't have enough information to answer that."

    Context:
    {context}

    Conversation:
    {historical_context}

    Customer Query:
    {query}

    Your Answer:
    """
    response = model.generate_content(prompt_text).text
    print("[Gemini Response]:", response)
    return bot_response_with_odoo_url(response)

# FastAPI app
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
    history: List[Dict[str, str]]

@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not inventory_loaded:
        raise HTTPException(status_code=503, detail="Inventory not loaded.")
    try:
        response_text = send_data(request.query, request.history)
        updated_history = request.history + [{"user": request.query, "assistant": response_text}]
        return ChatResponse(response=response_text, history=updated_history)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# === Run Uvicorn if Standalone ===
if __name__ == "__main__":
    import uvicorn
    print("Start Chatbot API\n")
    ip = os.getenv("IP", "127.0.0.1")
    uvicorn.run(app, host=ip, port=2020)
