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

    st.header("💸 Manual Money Transfer")
    st.write("Enter recipient details to verify and transfer funds.")

    # --- Session State Initialize ---
    if 'verified_recipient' not in st.session_state:
        st.session_state.verified_recipient = None
    if 'temp_amount' not in st.session_state:
        st.session_state.temp_amount = 0.0

    # 1. Input Section
    with st.container(border=True):
        receiver_acc = st.text_input("Recipient Account Number", placeholder="BOP-XXXXXXXX")
        amount = st.text_input("Amount to Transfer (Rs.)")
        
        if st.button("Verify Recipient"):
            if not receiver_acc or not amount:
                st.error("Please enter both Account Number and Amount.")
            elif receiver_acc == user['account_no']:
                st.error("You cannot transfer to your own account.")
            else:
                all_users = dm.get_users()
                recipient = next((u for u in all_users if u['account_no'] == receiver_acc), None)
                
                if not recipient:
                    st.error("❌ Recipient account not found.")
                    dm.log_activity(user['account_no'], f"Failed transfer attempt to: {receiver_acc}")
                else:
                    v_amt, m_amt = val.validate_transaction_amount(amount, user['balance'], is_transfer=True)
                    if not v_amt:
                        st.error(m_amt)
                    else:
                        current_step = dm.get_current_step()
                        amt_val = float(amount)
                        is_fraud, prob_score = fe.predict_fraud(
                            step=current_step,
                            trans_type='TRANSFER',
                            amount=amt_val,
                            oldbalanceOrg=user['balance'],
                            newbalanceOrig=user['balance'] - amt_val,
                            oldbalanceDest=recipient.get('balance', 0),
                            newbalanceDest=recipient.get('balance', 0) + amt_val
                        )

                        if is_fraud and prob_score > 0.3:
                            st.warning(f"🚨 Security Alert: High Risk Transaction ({prob_score*100:.1f}%)")
                        
                        st.session_state.verified_recipient = recipient
                        st.session_state.temp_amount = amt_val
                        st.success("✅ Recipient Verified. See details below.")

    # 2. Display Phase (Tabular Form & PIN Gate)
    if st.session_state.verified_recipient:
        target = st.session_state.verified_recipient
        final_amt = st.session_state.temp_amount
        
        st.write("---")
        st.subheader("📋 Recipient Information")
        
        st.table({
            "Detail Field": ["Full Name", "Account Number", "Phone / Contact", "Transfer Amount"],
            "Information": [
                f"{target.get('f_name', 'N/A')} {target.get('l_name', 'N/A')}",
                target.get('account_no', 'N/A'),
                target.get('phone', 'N/A'),
                f"Rs. {final_amt:,.2f}"
            ]
        })

        pin_confirm = st.text_input("Enter your 4-Digit Security PIN", type="password", max_chars=4)

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🚀 Send Money", use_container_width=True):
                is_valid, msg, should_lock = val.check_transaction_pin(pin_confirm, user)
                
                if should_lock:
                    dm.update_security_status(user['email'], 3, lock=True)
                    st.error("🚨 Account Locked due to too many failed PIN attempts.")
                    st.session_state.logged_in_user = None
                    st.session_state.page = "Login"
                    st.rerun()
                elif not is_valid:
                    st.error(f"❌ {msg}")
                else:
                    if dm.update_balance(user['account_no'], final_amt, is_deposit=False):
                        dm.update_balance(target['account_no'], final_amt, is_deposit=True)
                        
                        # --- UPDATE: Added category="Transfer" for EDA ---
                        dm.record_transaction(
                            "Transfer", 
                            final_amt, 
                            user['account_no'], 
                            receiver_acc=target['account_no'], 
                            receiver_name=f"{target['f_name']} {target['l_name']}",
                            category="Transfer" # Ye EDA graph ko help karega
                        )
                        
                        st.balloons()
                        st.success(f"Successfully transferred Rs. {final_amt} to {target['f_name']}")
                        st.session_state.verified_recipient = None
                        st.session_state.temp_amount = 0.0
                    else:
                        st.error("Transaction Error. Please try again.")
        
        with col2:
            if st.button("❌ Cancel"):
                st.session_state.verified_recipient = None
                st.rerun()

    st.write("---")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state.verified_recipient = None
        st.session_state.page = "Dashboard"
        st.rerun()