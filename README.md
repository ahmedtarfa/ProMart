# 🛍️ ProMart – AI-Powered E-Commerce Platform Integrated with Odoo

**ProMart** is our graduation project — an intelligent e-commerce system that combines the power of AI and ERP to create a scalable, real-world solution. Instead of building a traditional web store, we chose to integrate with **Odoo ERP**, giving us a strong business backend while leveraging modern AI/ML to deliver a smarter customer and admin experience.

---

## 🚀 Key Features

### 🤖 1. Assel – AI Sales Chatbot
- Built with **Gemini Flash 1.5**
- Talks in **Arabic and English**
- Recommends products using **RAG (Retrieval-Augmented Generation)**
- Uses **ChromaDB** as a vector store for semantic search
- Pulls live inventory data from Odoo

### 💬 2. EchoSent – Sentiment Analysis
- Fine-tuned **Hugging Face LLM** to support Arabic reviews
- Predicts customer sentiment (rating from 1 to 5)
- Can be integrated with future social media monitoring tools

### 🔍 3. SeekSense – Vector-Based Product Search
- Replaces traditional keyword search
- Handles **spelling mistakes and vague queries**
- Uses **cosine similarity** with vector embeddings

### 📈 4. Seerly – Sales Forecasting
- Uses **Facebook Prophet** with **grid search optimization**
- Predicts daily sales based on admin parameters
- Helps admins make data-driven decisions

### 🎯 5. Aletheia Recommendation Engine
- Personalized product recommendations using **SVD (Singular Value Decomposition)**
- Learns from each customer’s purchase history and ratings

---

## 🧾 Why Odoo?

We integrated ProMart with **Odoo ERP** to take advantage of its robust features:
- Admin can manage inventory, customers, and products
- Real-time sales dashboards
- Seamless integration with our ML models
- Handles automated emails for sign-up, purchase, and password reset

---

## 👤 Roles

### 👨‍💼 Admin:
- Full control over inventory, product catalog, and customer data
- View real-time dashboards and forecasts with **Seerly**
- Analyze customer feedback using **EchoSent**

### 🛍️ Customer:
- Smart search via **SeekSense**
- Personalized recommendations via **Aletheia**
- Real-time AI assistance through **Assel chatbot**
- Auto email notifications on key actions

---

## 📂 Repository Structure
