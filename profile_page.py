import streamlit as st

def show():
    # 1. Access user data
    user = st.session_state.get('logged_in_user')
    
    if not user:
        st.session_state.page = "Login"
        st.rerun()
        return

    st.header("👤 Personal Profile")
    st.write("Manage your account information and share your QR code.")

    # 2. Profile Details in Cards
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container(border=True):
            st.subheader("Personal Info")
            st.write(f"**Full Name:** {user['f_name']} {user['l_name']}")
            st.write(f"**Father Name:** {user['fa_f_name']} {user['fa_l_name']}")
            st.write(f"**CNIC:** {user['cnic']}")
            st.write(f"**Phone:** {user['phone']}")
            st.write(f"**Email:** {user['email']}")

    with col2:
        with st.container(border=True):
            st.subheader("Account Status")
            st.write(f"**Account No:** {user['account_no']}")
            st.write(f"**Current Balance:** Rs. {user.get('balance', 0.0):,.2f}")
            st.write(f"**Province:** {user['province']}")
            st.write(f"**City:** {user['city']}")
            st.write(f"**Security:** {'✅ Locked' if user.get('is_locked') else '🟢 Active'}")

    st.divider()

    # 3. Virtual QR Code Section
    st.subheader("📲 Your Payment QR Code")
    st.info("Other users can scan this to send you money instantly.")
    
    # --- UPDATED QR DATA ---
    # Sirf Account Number rakha hai taake scanner database se match kar sakay
    qr_display = f"{user['account_no']}"
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.markdown(f"""
            <div style="background-color:white; padding:20px; border: 5px solid #1e3d59; border-radius:10px; text-align:center;">
                <img src="https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_display}" />
                <h4 style="color:#1e3d59; margin-top:10px;">{user['account_no']}</h4>
                <p style="color:gray; font-size:12px;">Scan to Pay {user['f_name']}</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # 4. Address & Action
    st.write(f"🏠 **Residential Address:** {user.get('res_address', 'Not Provided')}")
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.page = "Dashboard"
        st.rerun()