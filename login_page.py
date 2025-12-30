import streamlit as st
import data_manager as dm
import rules as val

def show():
    st.header("🔐 Secure BOP Login")
    st.write("Please enter your credentials to initiate biometric verification.")
    
    # --- STEP A: CREDENTIALS ---
    with st.container(border=True):
        email = st.text_input("Email Address", placeholder="user@example.com").strip().lower()
        pin = st.text_input("Enter 4-Digit PIN", type="password", max_chars=4)

        if st.button("Next: Verify Identity ➡️", use_container_width=True):
            # 1. Check for empty fields
            if not email or not pin:
                st.error("🚨 Notification: All fields are mandatory.")
                return

            # --- STEP B: BACKEND SEARCH ---
            users = dm.get_users()
            user = next((u for u in users if u['email'].lower() == email), None)

            if not user:
                st.error("❌ Invalid Credentials: User not found.")
                return

            # --- FRAUD PROTECTION / LOCKOUT CHECK ---
            # Agar Fraud Model ne ya failed attempts ne account lock kiya hai
            if user.get('is_locked') == True:
                st.error("🚫 Your account is currently LOCKED for security reasons.")
                st.warning("Please click on 'Reset PIN' below to verify your identity (Face Scan) and unlock your account.")
                # AI Log for security
                dm.log_activity(user.get('account_no', 'Unknown'), "Blocked login attempt on locked account.")
                return

            # Validate PIN using rules.py logic
            is_valid, message, should_lock = val.check_transaction_pin(pin, user)

            if is_valid:
                # RESET TRIALS ON SUCCESS
                dm.update_security_status(email, 0, False)
                
                # --- STEP C: TARGET IDENTIFICATION ---
                st.session_state.temp_user = user 
                st.session_state.page = "Verify" 
                
                st.success(f"✅ Credentials Verified for {user['f_name']}!")
                st.info("Initiating Biometric Face Scan...")
                st.rerun()
            
            else:
                # FAILURE LOGIC (3-Attempts Rule)
                if should_lock:
                    dm.update_security_status(email, 3, True)
                    st.error(f"🚨 {message}")
                else:
                    new_tries = user.get('failed_tries', 0) + 1
                    dm.update_security_status(email, new_tries, False)
                    st.error(f"❌ {message}")

    # --- NAVIGATION ---
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 New User? Open Account", use_container_width=True):
            st.session_state.page = "Signup"
            st.rerun()
    with col2:
        # Reset logic remains the same to handle both PIN loss and Fraud Lockouts
        if st.button("🔑 Locked? Reset PIN", use_container_width=True):
            st.session_state.page = "Reset"
            st.rerun()