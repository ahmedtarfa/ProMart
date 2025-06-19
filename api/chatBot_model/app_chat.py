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
import spacy

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

inventory_loaded = True  # Later can be refreshed in background

# Load spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading en_core_web_sm model for spaCy...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Helper functions
def extract_keywords(sentence: str) -> list[str]:
    doc = nlp(sentence.lower())
    keywords = [
        token.lemma_ for token in doc
        if token.pos_ in ["NOUN", "PROPN"]
        and not token.is_stop
        and not token.is_punct
        and token.lemma_ not in ["item", "product", "thing", "kind", "type"]
    ]
    return keywords

def contains_arabic(text: str) -> bool:
    return bool(re.search(r'[\u0600-\u06FF]', text))

def translate_text_if_arabic(text: str, target_language: str = "en") -> str:
    if contains_arabic(text):
        return GoogleTranslator(source='auto', target=target_language).translate(text)
    return text

def format_result_for_prompt(results):
    return "\n".join(
        f"{i+1}. link --> <<{item['metadata']['id']}>> {item['metadata']['name']} - {item['description']} - {item['metadata'].get('availability', 'availability unknown')}"
        for i, item in enumerate(results)
    )

# Main chatbot logic
def send_data(query: str, history: List[Dict[str, str]]) -> tuple[str, str, str]:
    keywords = extract_keywords(translate_text_if_arabic(query))
    current_context = search_inventory(keywords)
    current_context_text = format_result_for_prompt(current_context)

    previous_contexts = "\n".join(
        item["context"] for item in history[-2:] if "context" in item
    )
    context_text = (previous_contexts + "\n" + current_context_text).strip() if previous_contexts else current_context_text

    historical_context = "\n".join(
        f"User: {item['user']}\nAssistant: {item['assistant']}\nContext_history: {item['context']}"
        for item in history[-2:]
    )

    prompt_text = f"""
Your name is "aseel" (Arabic: "أصيل"). You are a professional sales assistant working for "proMart".

🛍️ Your job is to help customers by suggesting the most relevant products from the inventory.
✅ Always prioritize matching real products.
✅ Be confident, helpful, and concise.

🌐 Language Handling:
- If the Customer Query is in English, reply fully in English.
- If the Customer Query is in Arabic, reply in Egyptian Arabic 🇪🇬.
- If the Customer Query is Franco Arabic, reply in Franco Arabic.
- ❌ Avoid mixing Arabic and English in the same sentence.

📦 Product Mentions:
- Mention products using the format: link --> <<Product ID>>
- The Product ID must always be wrapped in << >>.

📦 Stock:
- Show availability as either **'in stock'** or **'out of stock'** only.

🗂️ If multiple products are relevant, list them clearly in a structured list.

❓ If no match is found:
-recommend the best output you see and keep talk with customer "preferd"
- Respond with: **"I don't have enough information to answer that."** or **"Give Me More Information please"**

---
if customer ask you any question reply to him using your knowlage if not in my data
___
📚 Context:
{context_text}

💬 Conversation History:
{historical_context}

🧑‍💼 Customer Query:
{query}

---

🤖 Your Answer:
"""
    response = model.generate_content(prompt_text).text
    print("[RESPONCE]:",response)
    final_response = bot_response_with_odoo_url(response)
    print("\n\n[FINAL_RESPONSE]:",final_response)
    return final_response, current_context_text, historical_context

# FastAPI setup
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response schemas
class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    response: str
    history: List[Dict[str, str]]

# Endpoint
@app.post("/chat/", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    if not inventory_loaded:
        raise HTTPException(status_code=503, detail="Inventory not loaded.")
    try:
        response_text, context_text, _ = send_data(request.query, request.history)
        updated_history = request.history + [{
            "user": request.query,
            "assistant": response_text,
            "context": context_text
        }]
        return ChatResponse(response=response_text, history=updated_history)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {e}")

# Entry point
if __name__ == "__main__":
    import uvicorn
    print("Start Chatbot API\n")
    ip = os.getenv("IP", "127.0.0.1")
    uvicorn.run(app, host=ip, port=2020)
