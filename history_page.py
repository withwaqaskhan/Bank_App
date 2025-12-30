import streamlit as st
import data_manager as dm
import rules as val

def show():
    user = st.session_state.get('logged_in_user')
    if not user:
        st.session_state.page = "Login"
        st.rerun()
        return

    st.header("📜 Transaction History")
    st.write("Review your recent account activity, AI insurance estimates, and security logs.")

    # 1. Fetch Data
    all_transactions = dm.get_transactions()
    # Filter only for this user (either as sender or receiver)
    user_history = [
        t for t in all_transactions 
        if t['sender'] == user['account_no'] or t['receiver_acc'] == user['account_no']
    ]

    if not user_history:
        st.info("No transactions found yet. Start by making a deposit or checking insurance!")
        if st.button("Back to Dashboard"):
            st.session_state.page = "Dashboard"
            st.rerun()
        return

    # 2. Filters & Search
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search = st.text_input("🔍 Search by Recipient Name or Account", placeholder="e.g. John Doe")
    with col2:
        # NAYA: Added 'Insurance AI' in filter types
        t_filter = st.selectbox("Type", ["All", "Deposit", "Transfer", "CASH_OUT", "INSURANCE_PREMIUM", "Security Alert"])
    with col3:
        st.write("") # Spacer
        if st.button("Clear Filters", use_container_width=True):
            st.rerun()

    # Apply Filtering Logic
    filtered_data = user_history
    if search:
        filtered_data = [t for t in filtered_data if search.lower() in t.get('receiver_name', '').lower() or search.lower() in t.get('receiver_acc', '').lower()]
    
    if t_filter != "All":
        if t_filter == "Security Alert":
            filtered_data = [t for t in filtered_data if t.get('status') != "Success" and t.get('status') != "AI_Estimated"]
        else:
            filtered_data = [t for t in filtered_data if t['type'] == t_filter]

    # 3. Display Data in a Professional Table
    st.divider()
    
    st.markdown("""
        <style>
        .table-head { font-weight: bold; background-color: #f0f2f6; padding: 10px; border-radius: 5px; }
        .status-blocked { color: #d32f2f; font-weight: bold; background-color: #ffebee; padding: 2px 5px; border-radius: 3px; }
        .status-success { color: #2e7d32; font-weight: bold; }
        .status-ai { color: #1e3d59; font-weight: bold; background-color: #e3f2fd; padding: 2px 5px; border-radius: 3px; }
        </style>
    """, unsafe_allow_html=True)

    if not filtered_data:
        st.warning("No records match your filters.")
    else:
        # Create a clean display
        for t in reversed(filtered_data): # Show newest first
            status_text = t.get('status', 'Success')
            is_fraud_hit = status_text not in ["Success", "AI_Estimated"]
            is_insurance = t['type'] == "INSURANCE_PREMIUM"
            
            # Icon Selection
            if is_insurance:
                icon = "🏥"
            elif is_fraud_hit:
                icon = "🚨"
            else:
                icon = "✅"
            
            label = f"{t['date']} - {t['type'].replace('_', ' ')}: Rs. {t['amount']:,.2f} {icon}"
            
            with st.expander(label):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Category:** {t['type']}")
                    st.write(f"**Amount:** Rs. {t['amount']:,.2f}")
                    
                    if status_text == "AI_Estimated":
                        st.markdown(f"**Status:** <span class='status-ai'>🤖 {status_text}</span>", unsafe_allow_html=True)
                    elif is_fraud_hit:
                        st.markdown(f"**Status:** <span class='status-blocked'>{status_text}</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"**Status:** <span class='status-success'>{status_text}</span>", unsafe_allow_html=True)
                
                with c2:
                    if t['type'] == "Transfer":
                        if t['sender'] == user['account_no']:
                            st.write(f"**To:** {t.get('receiver_name', 'N/A')}")
                            st.write(f"**Account:** {t.get('receiver_acc', 'N/A')}")
                        else:
                            st.write(f"**From:** {t['sender']}")
                            st.write("**Note:** Incoming Transfer")
                    elif is_insurance:
                        st.write("**Service:** Health Insurance AI")
                        st.write("**Note:** Calculated based on Health Profile")
                    else:
                        st.write("**Transaction Mode:** Online/ATM")

    st.divider()
    if st.button("⬅️ Back to Dashboard", key="back_btn"):
        st.session_state.page = "Dashboard"
        st.rerun()