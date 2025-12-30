import streamlit as st
import data_manager as dm
import insurance_engine as ie
import cv2
import numpy as np
from PIL import Image

def show():
    # 1. Access user data
    user_data = st.session_state.get('logged_in_user')
    
    # 2. Safety Check
    if not user_data:
        st.session_state.page = "Login"
        st.rerun()
        return

    # 3. Refresh user data
    all_users = dm.get_users()
    current_user = next((u for u in all_users if u['account_no'] == user_data['account_no']), user_data)
    st.session_state.logged_in_user = current_user 

    # --- AI CONTEXT TRIGGER ---
    if 'dashboard_logged' not in st.session_state:
        dm.log_activity(current_user['account_no'], "Visited Home Dashboard")
        st.session_state.dashboard_logged = True

    # 4. Header & Balance Summary
    st.title(f"🏦 Welcome back, {current_user['f_name']}!")
    
    st.markdown(f"""
        <div style="background-color:#1e3d59; padding:20px; border-radius:10px; border-left: 8px solid #ff6e40;">
            <h3 style="color:white; margin:0;">Available Balance</h3>
            <h1 style="color:#ff6e40; margin:0;">Rs. {current_user.get('balance', 0.0):,.2f}</h1>
            <p style="color:white; opacity:0.8;">Account No: {current_user['account_no']}</p>
        </div>
    """, unsafe_allow_html=True)

    st.write("---")

    # ========================================================
    # 🚀 NAVIGATION LOGIC
    # ========================================================
    
    if 'show_insurance' not in st.session_state: st.session_state.show_insurance = False
    if 'show_qr_scan' not in st.session_state: st.session_state.show_qr_scan = False

    # --- A. INSURANCE FORM ---
    if st.session_state.show_insurance:
        st.header("🏥 Health Insurance Premium Predictor")
        if st.button("⬅️ Back to Quick Actions"):
            st.session_state.show_insurance = False
            st.rerun()

        with st.form("insurance_form"):
            c1, c2 = st.columns(2)
            with c1:
                age = st.number_input("Age", min_value=18, max_value=100, value=25)
                bmi = st.number_input("BMI", min_value=10.0, max_value=50.0, value=22.5)
                children = st.number_input("Children", min_value=0, max_value=10, value=0)
            with c2:
                bp = st.number_input("Blood Pressure", min_value=80, max_value=200, value=120)
                gender = st.selectbox("Gender", ["male", "female"])
                diabetic = st.selectbox("Diabetic?", ["No", "Yes"])
                smoker = st.selectbox("Smoker?", ["No", "Yes"])
            
            submit_btn = st.form_submit_button("Predict Premium", use_container_width=True)

        if submit_btn:
            prediction = ie.predict_insurance_premium(age, bmi, children, bp, gender, diabetic, smoker, current_user['account_no'])
            if prediction:
                st.success(f"### 💸 Estimated Yearly Premium: Rs. {prediction:,.2f}")
                st.balloons()

    # --- B. SCAN & PAY SECTION (UPDATED) ---
    elif st.session_state.show_qr_scan:
        st.header("📸 Scan QR & Pay")
        if st.button("⬅️ Back to Dashboard"):
            st.session_state.show_qr_scan = False
            st.rerun()

        uploaded_qr = st.file_uploader("Upload Recipient's QR Code Image", type=['png', 'jpg', 'jpeg'])
        
        if uploaded_qr:
            file_bytes = np.asarray(bytearray(uploaded_qr.read()), dtype=np.uint8)
            opencv_img = cv2.imdecode(file_bytes, 1)
            detector = cv2.QRCodeDetector()
            data, _, _ = detector.detectAndDecode(opencv_img)

            if data:
                target_user = next((u for u in dm.get_users() if u['account_no'] == data), None)
                if target_user:
                    st.success("✅ Recipient Found")
                    st.table({
                        "Field": ["Recipient Name", "Account Number", "Verification"],
                        "Details": [target_user.get('user_name', target_user.get('f_name')), target_user['account_no'], "Verified ✅"]
                    })
                    
                    # --- BALANCE CHECK ADDED HERE TO PREVENT CRASH ---
                    user_balance = float(current_user.get('balance', 0.0))
                    if user_balance < 1.0:
                        st.error("⚠️ Your balance is too low to make a transfer.")
                        amt = st.number_input("Enter Amount (Rs.)", value=0.0, disabled=True)
                    else:
                        amt = st.number_input(
                            "Enter Amount (Rs.)", 
                            min_value=1.0, 
                            max_value=user_balance, 
                            value=1.0,
                            step=1.0
                        )

                    pin = st.text_input("Enter Your Transaction PIN", type="password")
                    
                    if st.button("🚀 Confirm & Send Money", use_container_width=True):
                        if str(current_user['pin']) == str(pin):
                            if user_balance >= amt and dm.update_balance(current_user['account_no'], amt, is_deposit=False):
                                dm.update_balance(target_user['account_no'], amt, is_deposit=True)
                                
                                # Category "Transfer" added for EDA
                                dm.record_transaction(
                                    "QR Transfer", amt, current_user['account_no'], 
                                    receiver_acc=target_user['account_no'], 
                                    receiver_name=target_user.get('user_name', target_user.get('f_name')),
                                    category="Transfer"
                                )
                                st.success(f"Successfully sent Rs.{amt} to {target_user.get('f_name')}")
                                st.balloons()
                                st.rerun()
                            else: st.error("Transaction Failed! Low Balance or System Error.")
                        else: st.error("Incorrect PIN!")
                else:
                    st.error("❌ User does not exist in our records.")
            else:
                st.warning("No QR code detected. Please upload a clear image.")

    # --- C. DEFAULT BUTTONS ---
    else:
        st.subheader("🚀 Quick Actions")
        col1, col2, col3 = st.columns(3)
        is_locked = current_user.get('is_locked', False)
        
        with col1:
            if st.button("💰 Deposit Money", use_container_width=True):
                st.session_state.page = "Deposit"; st.rerun()
            if st.button("🏥 Insurance AI", use_container_width=True):
                st.session_state.show_insurance = True; st.rerun()
            if st.button("📊 Financial EDA", use_container_width=True):
                st.session_state.page = "EDA"; st.rerun()

        with col2:
            if st.button("💸 Manual Transfer", use_container_width=True, disabled=is_locked):
                st.session_state.page = "Transfer"
                st.rerun()
                
            if st.button("📸 Scan QR & Pay", use_container_width=True, disabled=is_locked):
                st.session_state.show_qr_scan = True
                st.rerun()
                
            if st.button("🏧 ATM Cash Out", use_container_width=True, disabled=is_locked):
                st.session_state.page = "ATM"; st.rerun()

        with col3:
            if st.button("👤 View Profile", use_container_width=True):
                st.session_state.page = "Profile"; st.rerun()
            if st.button("📜 History", use_container_width=True):
                st.session_state.page = "History"; st.rerun()
            if st.button("🔒 Logout", use_container_width=True):
                st.session_state.logged_in_user = None; st.session_state.page = "Login"; st.rerun()

    st.divider()
    if not current_user.get('is_locked') and not st.session_state.show_insurance and not st.session_state.show_qr_scan:
        st.info("💡 Tip: Use 'Manual Transfer' to send money via account number.")