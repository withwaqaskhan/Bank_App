import streamlit as st
import data_manager as dm
import rules as val

def show():
    # 1. Access user data
    user = st.session_state.get('logged_in_user')
    
    if not user:
        st.session_state.page = "Login"
        st.rerun()
        return

    st.header("💰 Deposit Funds")
    st.write("Add money to your BOP account securely.")

    # 2. Deposit Form
    with st.container(border=True):
        amount = st.text_input("Enter Amount (Rs.)", placeholder="e.g. 5000")
        pin_input = st.text_input("Enter 4-Digit PIN to Confirm", type="password", max_chars=4)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Confirm Deposit", use_container_width=True):
                # --- CHANGE HERE: is_transfer=False taake balance check skip ho jaye ---
                v_amt, m_amt = val.validate_transaction_amount(amount, user['balance'], is_transfer=False)
                
                if not v_amt:
                    st.error(f"❌ {m_amt}")
                    dm.log_activity(user['account_no'], f"Attempted deposit with invalid amount: {amount}")
                    return

                # Step B: Validate PIN & Check Lock Status (3-Attempt Rule)
                is_valid_pin, message, should_lock = val.check_transaction_pin(pin_input, user)

                if should_lock:
                    dm.update_security_status(user['email'], 3, lock=True)
                    dm.log_activity(user['account_no'], "CRITICAL: Account locked during deposit attempt due to 3 failed PINs")
                    
                    st.error(f"🚨 {message}")
                    st.session_state.logged_in_user = None # Force Logout
                    st.session_state.page = "Login"
                    st.rerun()
                
                elif not is_valid_pin:
                    new_tries = user.get('failed_tries', 0) + 1
                    dm.update_security_status(user['email'], new_tries, lock=False)
                    dm.log_activity(user['account_no'], f"Failed PIN attempt ({new_tries}/3) during Deposit")
                    st.error(f"❌ {message}")
                
                else:
                    # Step C: Process Success
                    amt_float = float(amount)
                    dm.update_balance(user['account_no'], amt_float, is_deposit=True)
                    dm.update_security_status(user['email'], 0, lock=False)
                    
                    # --- UPDATED: Added category="Savings" for EDA ---
                    dm.record_transaction(
                        t_type="Deposit",
                        amount=amt_float,
                        sender_acc=user['account_no'],
                        receiver_acc="Self",
                        receiver_name="Self",
                        status="Success",
                        category="Savings"  # Ye line EDA graphs ke liye add ki gayi hai
                    )
                    
                    dm.log_activity(user['account_no'], f"Successfully deposited Rs. {amt_float}")
                    st.success(f"✅ Successfully deposited Rs. {amt_float:,.2f}")
                    st.balloons()
                    # User data refresh taake naya balance nazar aaye
                    st.rerun() 
                    
        with col2:
            if st.button("Back to Dashboard", use_container_width=True):
                st.session_state.page = "Dashboard"
                st.rerun()

    # 3. Quick Info Card
    st.info("ℹ️ Your account will be blocked after 3 failed PIN attempts.")