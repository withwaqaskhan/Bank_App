import streamlit as st
import data_manager as dm
import login_page
import signup_page
import reset_page
import verify_page
import dashboard_page
import deposit_page
import transfer_page
import history_page
import eda_page
import profile_page
import atm_page  # --- NAYA: ATM Page import kiya ---
# Nayi Import for AI
import bank_bot_logic as bot 
import sentiment_engine as se 
from dotenv import load_dotenv

# 0. Load Environment Variables
load_dotenv()

# --- INITIALIZATION ---
st.set_page_config(page_title="BOP Digital Banking", page_icon="🏦", layout="centered")

dm.init_db()

if 'page' not in st.session_state:
    st.session_state.page = "Login"

if 'temp_user' not in st.session_state:
    st.session_state.temp_user = None

if 'logged_in_user' not in st.session_state:
    st.session_state.logged_in_user = None

if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR LOGOUT & NAV ---
if st.session_state.logged_in_user:
    user = st.session_state.logged_in_user
    with st.sidebar:
        st.title("🏦 BOP Menu")
        st.write(f"👤 **User:** {user['f_name']}")
        st.write(f"💳 **Acc:** {user['account_no']}")
        st.divider()
        
        if st.button("🏠 Home Dashboard"):
            st.session_state.page = "Dashboard"
            st.rerun()
            
        if st.button("🚪 Logout"):
            st.session_state.messages = []
            st.session_state.logged_in_user = None
            st.session_state.temp_user = None
            st.session_state.page = "Login"
            st.rerun()

# --- AI BOT INTERFACE ---
def show_bot():
    if st.session_state.logged_in_user:
        st.divider()
        with st.expander("💬 BOP Smart Assistant", expanded=False):
            st.caption("Ask me about bank policies or your recent activities.")
            
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            if prompt := st.chat_input("How can I help you?"):
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                user_profile = st.session_state.logged_in_user
                s_label, s_conf, s_word, s_action = se.get_sentiment_analysis(prompt)
                
                dm.log_sentiment(
                    account_no=user_profile['account_no'],
                    user_name=f"{user_profile['f_name']} {user_profile['l_name']}",
                    message=prompt,
                    sentiment=s_label,
                    confidence=s_conf,
                    important_word=s_word,
                    action=s_action
                )

                with st.chat_message("assistant"):
                    recent_acts = dm.get_recent_activities(user_profile['account_no'])
                    with st.spinner("Thinking..."):
                        response = bot.generate_smart_response(
                            user_query=prompt,
                            user_profile=user_profile,
                            recent_activities=recent_acts
                        )
                        st.markdown(response)
                
                st.session_state.messages.append({"role": "assistant", "content": response})
                dm.save_chat_message(user_profile['account_no'], "user", prompt)
                dm.save_chat_message(user_profile['account_no'], "assistant", response)

# --- MAIN ROUTING LOGIC ---
def main():
    page = st.session_state.page

    # Public Pages
    if page == "Login":
        login_page.show()
    elif page == "Signup":
        signup_page.show()
    elif page == "Reset":
        reset_page.show()
    
    # Secure Verification Page
    elif page == "Verify":
        if st.session_state.temp_user:
            verify_page.show()
        else:
            st.session_state.page = "Login"
            st.rerun()

    # Private Pages (ATM added to the list)
    elif page in ["Dashboard", "Deposit", "Transfer", "History", "EDA", "Profile", "ATM"]:
        if st.session_state.logged_in_user:
            if page == "Dashboard":
                dashboard_page.show()
            elif page == "Deposit":
                deposit_page.show()
            elif page == "Transfer":
                transfer_page.show()
            elif page == "History":
                history_page.show()
            elif page == "EDA":
                eda_page.show()
            elif page == "Profile":
                profile_page.show()
            elif page == "ATM":  # --- NAYA: ATM Routing ---
                atm_page.show()
            
            show_bot()
        else:
            st.error("🚨 Unauthorized Access. Please Login first.")
            st.session_state.page = "Login"
            st.rerun()

if __name__ == "__main__":
    main()