import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

import tensorflow as tf
import numpy as np
from transformers import TFAutoModelForSequenceClassification, AutoTokenizer

import re
import string
import nltk
import emoji
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.stem.isri import ISRIStemmer
from langid import classify  # To detect language for handling Arabic and English separately

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')
nltk.download('omw-1.4')

app = FastAPI()
model = TFAutoModelForSequenceClassification.from_pretrained(".//finetuned_sentiment2")
tokenizer = AutoTokenizer.from_pretrained(".//finetuned_sentiment2")

rejection_words = {"لا", "لم", "ليس"}
rejection_words_en = {"not", "no", "never"}
# Initialize
stop_words_en = set(stopwords.words('english')) - rejection_words_en
stop_words_ar = set(stopwords.words('arabic')) - rejection_words
lemmatizer_en = WordNetLemmatizer()

# Arabic lemmatization placeholder function (use a more advanced tool if needed)
def arabic_lemmatize(word):
    word = ISRIStemmer().suf32(word)
    return word

def clean_text(text: str) -> str:
    text = emoji.demojize(text)            # Remove emojis
    text = text.lower()                                     # Lowercase
    text = re.sub(r'\d+', '', text)                         # Remove numbers
    text = text.translate(str.maketrans('', '', string.punctuation))  # Remove punctuation
    text = re.sub(r'\s+', ' ', text).strip()                # Normalize whitespace

    words = word_tokenize(text)  # Tokenize the text
    cleaned_words = []

    for word in words:
        if word in stop_words_en or word in stop_words_ar:
            continue
        language, _ = classify(word)  # Classify the language of the word
        if language == 'ar':  # Arabic word
            cleaned_words.append(arabic_lemmatize(word))
        else:  # English word
            cleaned_words.append(lemmatizer_en.lemmatize(word))

    return ' '.join(cleaned_words)


class ModelInput(BaseModel):
    reviews: list[str]

class predOutput(BaseModel):
    review: str
    rate: int

def predict_sentiment(texts: list[str]) -> list[int]:
    # Tokenize
    inputs = tokenizer(texts, truncation=True, padding=True, max_length=512, return_tensors="tf")

    # Run prediction
    outputs = model(**inputs)
    logits = outputs.logits
    probs = tf.nn.softmax(logits, axis=-1)
    preds = tf.argmax(probs, axis=1).numpy()
    preds = preds + 1

    return preds.tolist()


@app.post("/predict/", response_model=list[predOutput])
def sentiment_analysis(data: ModelInput):
    cleaned_reviews = [clean_text(text) for text in data.reviews]
    predictions = predict_sentiment(cleaned_reviews)

    return [
        predOutput(review=review, rate=rate)
        for review, rate in zip(data.reviews, predictions)
    ]

if __name__ == '__main__':
    uvicorn.run(app, host='192.168.0.107', port=1113)