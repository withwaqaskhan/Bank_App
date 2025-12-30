import os
import ast
import random
from datetime import datetime

# Filenames
FILE = "user_data.txt"
TRANS_FILE = "transactions.txt"
ACTIVITY_FILE = "activity_logs.txt"  
SENTIMENT_FILE = "sentiment_logs.txt" 

def init_db():
    """Ensures necessary files exist."""
    if not os.path.exists(FILE):
        with open(FILE, "w") as f: pass 
    if not os.path.exists(TRANS_FILE):
        with open(TRANS_FILE, "w") as f: pass
    if not os.path.exists(ACTIVITY_FILE): 
        with open(ACTIVITY_FILE, "w") as f: pass
    if not os.path.exists(SENTIMENT_FILE):
        with open(SENTIMENT_FILE, "w") as f: pass
    if not os.path.exists("data"):
        os.makedirs("data")

# --- FRAUD DETECTION SUPPORT ---

def get_current_step():
    """XGBoost step logic: Total transactions + 1."""
    transactions = get_transactions()
    return len(transactions) + 1

# --- SENTIMENT LOGGING ---

def log_sentiment(account_no, user_name, message, sentiment, confidence, important_word, action):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "account_no": account_no,
        "user_name": user_name,
        "message": message,
        "sentiment": sentiment,
        "confidence": confidence,
        "important_word": important_word,
        "action": action
    }
    try:
        with open(SENTIMENT_FILE, "a") as f:
            f.write(str(entry) + "\n")
    except: pass

def get_sentiment_logs():
    logs = []
    if not os.path.exists(SENTIMENT_FILE): return []
    try:
        with open(SENTIMENT_FILE, "r") as f:
            for line in f:
                if line.strip():
                    logs.append(ast.literal_eval(line.strip()))
    except: pass
    return logs

# --- ACTIVITY LOGGING ---

def log_activity(account_no, activity_text):
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "account_no": account_no,
        "activity": activity_text
    }
    try:
        with open(ACTIVITY_FILE, "a") as f:
            f.write(str(entry) + "\n")
    except: pass

def get_recent_activities(account_no, limit=3):
    activities = []
    try:
        if os.path.exists(ACTIVITY_FILE):
            with open(ACTIVITY_FILE, "r") as f:
                lines = f.readlines()
                for line in reversed(lines):
                    act = ast.literal_eval(line.strip())
                    if act['account_no'] == account_no:
                        activities.append(act['activity'])
                    if len(activities) >= limit: break
    except: pass
    return activities

# --- CHAT HISTORY ---

def save_chat_message(account_no, role, message):
    history_file = f"data/chat_history_{account_no}.txt"
    entry = {"role": role, "content": message, "time": datetime.now().strftime("%H:%M")}
    with open(history_file, "a") as f:
        f.write(str(entry) + "\n")

def get_chat_history(account_no, limit=10):
    history_file = f"data/chat_history_{account_no}.txt"
    if not os.path.exists(history_file): return []
    messages = []
    with open(history_file, "r") as f:
        lines = f.readlines()
        for line in lines[-limit:]:
            messages.append(ast.literal_eval(line.strip()))
    return messages

# --- PURANA CODE (FIXED & UNCHANGED) ---

def get_users():
    init_db()
    users = []
    try:
        with open(FILE, "r") as f:
            for line in f:
                if line.strip():
                    user_dict = ast.literal_eval(line.strip())
                    if 'balance' not in user_dict: user_dict['balance'] = 0.0
                    if 'failed_tries' not in user_dict: user_dict['failed_tries'] = 0
                    if 'is_locked' not in user_dict: user_dict['is_locked'] = False
                    if 'face_id' not in user_dict: user_dict['face_id'] = None
                    users.append(user_dict)
    except Exception as e: 
        return []
    return users

def get_next_face_id():
    users = get_users()
    if not users: return 101
    ids = [int(u['face_id']) for u in users if u.get('face_id') is not None]
    if not ids: return 101
    return max(ids) + 1

def save_user(data):
    users = get_users()
    if any(str(u['cnic']) == str(data['cnic']) for u in users):
        return False, "An account with this CNIC already exists."
    if any(u['email'].lower() == data['email'].lower() for u in users):
        return False, "This email is already registered."
    data['account_no'] = generate_unique_account_no()
    if 'face_id' not in data: data['face_id'] = get_next_face_id()
    if 'balance' not in data: data['balance'] = 0.0 
    try:
        with open(FILE, "a") as f:
            f.write(str(data) + "\n")
        log_activity(data['account_no'], "Account Created and Registered")
        return True, f"Account Created! Your Account No is: {data['account_no']}"
    except Exception as e:
        return False, f"Error: {str(e)}"

def generate_unique_account_no():
    users = get_users()
    existing_nos = [u.get('account_no') for u in users]
    while True:
        new_no = f"BOP-{random.randint(10000000, 99999999)}"
        if new_no not in existing_nos: return new_no

# --- ✅ FINAL BULLET-PROOF UPDATE ---
def record_transaction(t_type="Transaction", amount=0.0, sender_acc=None, **kwargs):
    """
    PURANA CODE UNCHANGED: Handles category for EDA analysis.
    """
    final_sender = kwargs.get('account_no', sender_acc)
    final_type = kwargs.get('t_type', t_type)
    final_amount = kwargs.get('amount', amount)
    
    # --- ADDED CATEGORY LOGIC HERE ---
    log_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": final_type, 
        "amount": float(final_amount),
        "sender": final_sender,
        "receiver_acc": kwargs.get('receiver_acc', "N/A"),
        "receiver_name": kwargs.get('receiver_name', "N/A"),
        "status": kwargs.get('status', "Success"),
        "category": kwargs.get('category', "General") # <--- Line added as requested
    }
    
    with open(TRANS_FILE, "a") as f:
        f.write(str(log_entry) + "\n")
    
    if final_sender:
        log_activity(final_sender, f"{log_entry['status']} {final_type} of Rs.{final_amount}")

def get_transactions():
    init_db()
    transactions = []
    try:
        with open(TRANS_FILE, "r") as f:
            for line in f:
                if line.strip():
                    transactions.append(ast.literal_eval(line.strip()))
    except: return []
    return transactions

def update_balance(account_no, amount, is_deposit=True):
    users = get_users()
    updated = False
    for u in users:
        if u['account_no'] == account_no:
            if is_deposit:
                u['balance'] = round(float(u['balance']) + float(amount), 2)
            else:
                u['balance'] = round(float(u['balance']) - float(amount), 2)
            updated = True
            break
    if updated:
        with open(FILE, "w") as f:
            for u in users: f.write(str(u) + "\n")
        return True
    return False

def update_security_status(email, tries, lock=False):
    users = get_users()
    for u in users:
        if u['email'].lower() == email.lower():
            u['failed_tries'] = tries
            u['is_locked'] = lock
            if lock: log_activity(u['account_no'], "Account Locked due to Security/Fraud Alert")
            break
    with open(FILE, "w") as f:
        for u in users: f.write(str(u) + "\n")

def update_pin(cnic, new_pin):
    users = get_users()
    updated = False
    for u in users:
        if str(u['cnic']) == str(cnic):
            u['pin'] = str(new_pin)
            u['is_locked'] = False
            u['failed_tries'] = 0
            updated = True
            log_activity(u['account_no'], "PIN Reset Successful")
            break
    if updated:
        with open(FILE, "w") as f:
            for u in users: f.write(str(u) + "\n")
        return True
    return False