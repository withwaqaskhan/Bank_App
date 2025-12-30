import re

def validate_no_space(text, field_name):
    """Rule 1: No spaces, only letters, minimum 2 characters."""
    if not text or len(text.strip()) < 2:
        return False, f"{field_name} cannot be empty or too short."
    if " " in text:
        return False, f"{field_name} must be a single word (No spaces allowed)."
    if not text.isalpha():
        return False, f"{field_name} should only contain letters (A-Z)."
    return True, ""

def validate_cnic(cnic):
    """Rule: Exactly 13 digits, strictly digits only."""
    if not cnic.isdigit() or len(cnic) != 13:
        return False, "CNIC Error: Must be exactly 13 digits (No spaces or dashes)."
    return True, ""

def validate_phone(phone):
    """Rule: Exactly 11 digits, must start with 03."""
    if not phone.isdigit() or len(phone) != 11:
        return False, "Phone Error: Must be exactly 11 digits (e.g. 03001234567)."
    if not phone.startswith("03"):
        return False, "Phone Error: Must start with 03."
    return True, ""

def validate_email(email, existing_emails):
    """Your Precise 11-step manual parsing logic."""
    email = email.strip().lower()

    # 1. Empty check
    if email == "":
        return False, "Email is required."
    # 2. Space check
    elif " " in email:
        return False, "Email must not contain spaces."
    # 3. Exactly one @
    elif email.count("@") != 1:
        return False, "Email must contain exactly one '@'."
    # 4. Must end with .com ONLY
    elif not email.endswith(".com"):
        return False, "Only '.com' email addresses are allowed."

    # 5. Split local & domain
    local_part, domain_part = email.split("@")

    # 6. Local part validation
    if len(local_part) < 2:
        return False, "Email username is too short."
    elif local_part.startswith(".") or local_part.endswith("."):
        return False, "Email username cannot start or end with dot."
    elif ".." in local_part:
        return False, "Email username cannot contain consecutive dots."

    # 7. Allowed characters in local part
    allowed_local = "abcdefghijklmnopqrstuvwxyz0123456789._-"
    for ch in local_part:
        if ch not in allowed_local:
            return False, "Invalid character in email username."

    # 8. Domain must contain exactly ONE dot (before com)
    if domain_part.count(".") != 1:
        return False, "Invalid domain format."

    domain_name, extension = domain_part.split(".")

    # 9. Extension must be 'com'
    if extension != "com":
        return False, "Only '.com' extension is allowed."

    # 10. Domain name checks
    if len(domain_name) < 2:
        return False, "Invalid domain name."
    elif ".." in domain_name:
        return False, "Domain cannot contain consecutive dots."
    elif not domain_name.isalpha():
        return False, "Domain name must contain only letters."

    # 11. Uniqueness check
    elif email in [e.lower() for e in existing_emails]:
        return False, "An account with this email already exists."

    return True, ""

def validate_pin(pin, confirm_pin=None):
    """Exactly 4 digits check."""
    if not pin.isdigit() or len(pin) != 4:
        return False, "PIN Error: Must be exactly 4 digits."
    if confirm_pin is not None and pin != confirm_pin:
        return False, "PIN Error: PINs do not match."
    return True, ""

# --- BANKING SECURITY RULES ---

def check_transaction_pin(entered_pin, user_data):
    """Handles the 3-attempt blocking logic with fixed Remaining Attempts."""
    if user_data.get('is_locked', False):
        return False, "ACCOUNT BLOCKED: Please reset your PIN.", True

    if str(entered_pin) == str(user_data['pin']):
        return True, "Success", False
    else:
        new_tries = user_data.get('failed_tries', 0) + 1
        if new_tries >= 3:
            return False, "Account Blocked! 3 incorrect attempts reached.", True
        else:
            # --- UPDATED LOGIC PER YOUR REQUEST ---
            # Agar hum 3-1 karte hain toh pehle attempt pe 2 dikhayega
            remaining = 3 - new_tries 
            return False, f"Incorrect PIN. Remaining Attempts: {remaining}", False

def validate_transaction_amount(amount, current_balance, is_transfer=True):
    """
    Logic: is_transfer=True (Withdraw/Transfer) checks balance.
           is_transfer=False (Deposit) skips balance check.
    """
    try:
        amt = float(amount)
        if amt <= 0:
            return False, "Amount must be greater than 0."
        
        # Sirf tab check karein jab balance se paise nikalne hon (is_transfer=True)
        if is_transfer:
            if amt > current_balance:
                return False, f"Insufficient Balance. Available: Rs. {current_balance:,.2f}"
            
        return True, ""
    except ValueError:
        return False, "Please enter a valid numeric amount."