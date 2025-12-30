import streamlit as st
import data_manager as dm
import rules as val
import fraud_engine as fe

def show():
    user = st.session_state.get('logged_in_user')
    if not user:
        st.session_state.page = "Login"
        st.rerun()
        return

    st.header("🏧 ATM Cash Withdrawal")
    st.info(f"Current Balance: Rs. {user['balance']:,.2f}")

    # 1. Input Section
    with st.container(border=True):
        acc_no = st.text_input("Confirm Account Number", value=user['account_no'])
        amount_input = st.text_input("Enter Amount to Withdraw (Rs.)", placeholder="e.g. 5000")

    # 2. Logic execution
    if st.button("Initiate Withdrawal"):
        if acc_no.strip() != user['account_no'].strip():
            st.error("❌ Account number mismatch!")
            return

        # Amount validate karein (Balance check on)
        v_amt, m_amt = val.validate_transaction_amount(amount_input, user['balance'], is_transfer=True)
        
        if not v_amt:
            st.error(f"❌ {m_amt}")
        else:
            try:
                amt_val = float(amount_input)
                current_bal = float(user['balance'])
                
                # --- MODEL INPUT PREPARATION ---
                current_step = dm.get_current_step()
                
                # Model prediction call (Directly sending 'CASH_OUT' string for OneHotEncoder)
                is_fraud, prob_score = fe.predict_fraud(
                    step=current_step,
                    trans_type='CASH_OUT',
                    amount=amt_val,
                    oldbalanceOrg=current_bal,
                    newbalanceOrig=current_bal - amt_val,
                    oldbalanceDest=0.0, 
                    newbalanceDest=amt_val
                )
                st.write(f"DEBUG -> Model Loaded: {fe.MODEL_LOADED} | Risk Score: {prob_score}")

                if is_fraud:
                    st.session_state.atm_fraud = True
                    st.session_state.atm_amount = amt_val
                    st.session_state.atm_prob = prob_score
                    st.rerun() 
                else:
                    st.session_state.atm_confirm = True
                    st.session_state.atm_amount = amt_val
                    st.session_state.atm_fraud = False
            except ValueError:
                st.error("❌ Please enter a valid numeric amount.")

    # --- FRAUD ALERT NOTIFICATION ---
    if st.session_state.get('atm_fraud'):
        prob_percent = st.session_state.get('atm_prob', 0) * 100
        st.error(f"🚨 **Fraud Alert: Suspicious ATM withdrawal of Rs. {st.session_state.atm_amount:,.2f} detected!** (Risk Score: {prob_percent:.1f}%)")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Ignore & Approve", use_container_width=True):
                st.session_state.atm_confirm = True
                st.session_state.atm_fraud = False 
                st.rerun()
        with col2:
            if st.button("🚫 BLOCK ACCOUNT", use_container_width=True):
                dm.update_security_status(user['email'], tries=3, lock=True)
                # Clear session to logout
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.session_state.page = "Login"
                st.rerun()

    # --- PIN CONFIRMATION ---
    if st.session_state.get('atm_confirm') and not st.session_state.get('atm_fraud'):
        st.divider()
        st.subheader("Final Step: Enter PIN")
        pin = st.text_input("4-Digit PIN", type="password", max_chars=4, key="atm_pin_input")
        
        if st.button("Confirm Cash Out", key="final_atm_btn", use_container_width=True):
            is_valid, msg, should_lock = val.check_transaction_pin(pin, user)
            if is_valid:
                amt = st.session_state.atm_amount
                # Database update
                if dm.update_balance(user['account_no'], amt, is_deposit=False):
                    dm.record_transaction("CASH_OUT", amt, user['account_no'], status="Success")
                    st.success(f"💸 Rs. {amt:,.2f} Withdrawal Successful! Collect your cash.")
                    st.balloons()
                    
                    # Reset States & Update Balance
                    st.session_state.atm_confirm = False
                    user['balance'] -= amt
                    st.rerun()
            else:
                st.error(f"❌ {msg}")
                if should_lock:
                    st.session_state.page = "Login"
                    st.rerun()

    if st.button("⬅️ Dashboard"):
        st.session_state.page = "Dashboard"
        st.rerun()