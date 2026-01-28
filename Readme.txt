# 🏦 AI-Powered Banking System

**Multi-Model AI Architecture | CV • ML • NLP • GenAI**

A production-ready banking platform that integrates **5 AI models** to deliver **secure authentication, fraud detection, intelligent customer support, and data-driven financial decisions**.

---

## 🚀 Why This Project Matters

* Demonstrates **end-to-end AI system design**, not just isolated models
* Combines **Computer Vision, Classical ML, NLP, and LLMs** in one pipeline
* Solves **real banking problems**: security, fraud, customer support, pricing

---

## 🧠 AI Models Implemented (5 Total)

### 🔹 Face Recognition — *OpenCV + LBPH*

* Trained on **100 biometric samples per user**
* Identity + face verified simultaneously
* Prevents unauthorized access via automatic blocking

### 🔹 Fraud Detection — *XGBoost*

* Supervised ML model trained on transaction behavior
* Generates **real-time risk scores**
* High-risk transactions trigger alerts and account blocking

### 🔹 Insurance Premium Prediction — *CatBoost*

* Regression model trained on customer financial profiles
* Predicts insurance premiums based on behavior patterns
* Enables data-driven pricing decisions

### 🔹 Banking Policy Chatbot — *LLaMA 3.1 + RAG*

* RAG pipeline built on banking policy PDFs
* FAISS vector database for semantic retrieval
* Generates accurate, context-aware responses

### 🔹 Sentiment & Intent Analysis — *BERT*

* Fine-tuned on banking conversations
* Detects customer sentiment (Positive / Neutral / Negative)
* Flags high-risk emotional states for urgent action

---

## 🔁 System Architecture (High-Level)

1. **Biometric Login** via Face Recognition
2. **Transaction Processing** → Fraud Detection (XGBoost)
3. **Policy Queries** → RAG-based LLM Chatbot
4. **Customer Messages** → BERT Sentiment Analysis
5. **Insurance Requests** → CatBoost Prediction Model

All components are modular and production-ready.

---

## 🛠️ Tech Stack

* **Language:** Python
* **Computer Vision:** OpenCV (LBPH)
* **Machine Learning:** XGBoost, CatBoost
* **NLP:** BERT
* **Generative AI:** LLaMA 3.1
* **Vector Database:** FAISS
* **Frontend / App Layer:** Streamlit
* **Deployment:** Streamlit Cloud / Hugging Face Spaces

---

## 🎯 Key Skills Demonstrated

* End-to-end ML & AI system design
* Multi-model orchestration
* RAG (Retrieval-Augmented Generation)
* Real-time risk scoring & decision logic
* Secure AI-driven authentication
* Production-ready deployment mindset
