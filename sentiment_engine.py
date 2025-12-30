import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = "bank_sentiment_model"

# Label mapping (Confirmed from your screenshots)
id2label = {0: "Negative", 1: "Neutral", 2: "Positive"}

try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
    MODEL_LOADED = True
except Exception as e:
    MODEL_LOADED = False
    print(f"⚠️ Load Error: {e}")

def get_sentiment_analysis(text):
    if not MODEL_LOADED:
        return "Neutral", "0%", "N/A", "No Action"

    # 1. BERT Prediction
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        probs = F.softmax(outputs.logits, dim=-1)
    
    conf, idx = torch.max(probs, dim=-1)
    sentiment = id2label[idx.item()]
    confidence_score = conf.item() * 100

    # 2. Advanced Logic Calibration
    text_lower = text.lower().replace("!", "").replace("?", "")
    
    # Keyword Lists
    danger_words = ["bad", "steal", "money", "worst", "fraud", "kaha", "poor", "ghalat", "hate", "blocked", "sad"]
    happy_words = ["good", "great", "love", "amazing", "resolved", "thank", "best", "fast", "smooth", "happy", "wow"]

    # --- Rule A: Force Positive ---
    # Agar model Neutral de raha hai lekin "great/love" jaise words hain
    if any(word in text_lower for word in happy_words) and sentiment == "Neutral":
        sentiment = "Positive"
        confidence_score = max(confidence_score, 70.0)

    # --- Rule B: Force Negative ---
    # Agar model Neutral de raha hai lekin "bad/steal" jaise words hain
    if any(word in text_lower for word in danger_words) and sentiment == "Neutral":
        sentiment = "Negative"
        confidence_score = max(confidence_score, 75.0)

    # 3. Intelligent Important Word Extraction
    words = text_lower.replace(",", "").replace(".", "").split()
    important_word = "N/A"
    
    # Priority Order: Negative > Positive > Longest Word
    for w in words:
        if w in danger_words:
            important_word = w
            break
    
    if important_word == "N/A":
        for w in words:
            if w in happy_words:
                important_word = w
                break
                
    if important_word == "N/A" and words:
        important_word = max(words, key=len)

    # 4. Action Logic (Refined)
    if sentiment == "Negative":
        action = "Urgent Agent Escalation"
    elif sentiment == "Positive":
        action = "Customer Delight Noted"
    else:
        action = "Monitor Normally"
    
    return sentiment, f"{confidence_score:.1f}%", important_word, action