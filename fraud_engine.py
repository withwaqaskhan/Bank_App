import joblib
import pandas as pd
import os
import warnings
import numpy as np

# Warnings ignore karne ke liye
warnings.filterwarnings("ignore", category=UserWarning)

# ========================================================
# 1. Model Path Setup (CLOUD COMPATIBLE - MULTI-PATH CHECK)
# ========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Linux servers par 'Fraud' aur 'fraud' alag hote hain, isliye hum dono check karenge
path_options = [
    os.path.join(BASE_DIR, "Fraud", "xgboost_fraud_pipeline.pkl"),
    os.path.join(BASE_DIR, "fraud", "xgboost_fraud_pipeline.pkl"),
    os.path.join(os.getcwd(), "Fraud", "xgboost_fraud_pipeline.pkl")
]

MODEL_PATH = None
for p in path_options:
    if os.path.exists(p):
        MODEL_PATH = p
        break

# ========================================================
# 2. Load Model Pipeline
# ========================================================
fraud_model = None
MODEL_LOADED = False

try:
    if MODEL_PATH:
        fraud_model = joblib.load(MODEL_PATH)
        MODEL_LOADED = True
        print(f"✅ Fraud Detection Engine Active! Loaded from: {MODEL_PATH}")
    else:
        MODEL_LOADED = False
        print("🚨 Error: Model file not found in any expected location.")
        # Cloud Logs ke liye directory structure print karein
        print(f"Current Directory Contents: {os.listdir(BASE_DIR)}")
except Exception as e:
    MODEL_LOADED = False
    print(f"🚨 Error loading Fraud Model: {e}")

# ========================================================
# 3. Predict Function (Your Original Logic - COMPLETELY UNCHANGED)
# ========================================================
def predict_fraud(step, trans_type, amount, oldbalanceOrg, newbalanceOrig, oldbalanceDest=0.0, newbalanceDest=None):
    """
    Inputs are passed as a DataFrame to let the Pipeline's OneHotEncoder handle 'type'.
    """
    if not MODEL_LOADED:
        print("🚨 Model not loaded. Skipping check.")
        return False, 0.0

    try:
        # A. Data Sanitization (Numeric values ko float banayein)
        def to_num(val):
            try:
                # Agar value None ya khali hai toh 0.0
                return float(val) if (val is not None and str(val).strip() != "") else 0.0
            except:
                return 0.0

        f_step = int(to_num(step)) if step else 1
        f_amount = to_num(amount)
        f_oldOrg = to_num(oldbalanceOrg)
        f_newOrig = to_num(newbalanceOrig)
        
        # Requirement: oldbalanceDest 0.0, newbalanceDest hamesha amount
        f_oldDest = to_num(oldbalanceDest)
        f_newDest = to_num(newbalanceDest) if newbalanceDest is not None else f_amount

        # B. 7-Feature DataFrame (String 'type' for the Encoder)
        data = pd.DataFrame([{
            'step': f_step,
            'type': str(trans_type).upper(), # e.g., 'CASH_OUT'
            'amount': f_amount,
            'oldbalanceOrg': f_oldOrg,
            'newbalanceOrig': f_newOrig,
            'oldbalanceDest': f_oldDest,
            'newbalanceDest': f_newDest
        }])

        # C. Prediction using Pipeline
        probs = fraud_model.predict_proba(data)
        fraud_probability = float(probs[0][1]) 

        # Terminal Debugging
        print(f"\n--- 🛡️ AI Security Analysis ---")
        print(f"Features Sent to Pipeline:\n{data.iloc[0]}")
        print(f"Risk Score: {fraud_probability:.4f}")
        
        # D. Dynamic Threshold Logic
        threshold = 0.3
        if f_newOrig == 0 and f_amount > 0:
            threshold = 0.1
            print("🚩 Pattern: Account Wipeout Detected")

        is_fraud = fraud_probability >= threshold
        return is_fraud, fraud_probability

    except Exception as e:
        print(f"⚠️ Pipeline/Encoder Error: {e}")
        return False, 0.0