import streamlit as st
import cv2
import numpy as np
import os
from PIL import Image
import data_manager as dm
import rules as val 
import time

def train_specific_user(face_id, account_no):
    """Specific user ke folder se FRESH training (Zero Memory Logic)."""
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    path = f"data/{account_no}"
    
    if not os.path.exists(path) or len(os.listdir(path)) == 0:
        return None

    face_samples = []
    ids = []
    
    try:
        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)
            gray_img = Image.open(img_path).convert('L')
            img_numpy = np.array(gray_img, 'uint8')
            face_samples.append(img_numpy)
            ids.append(int(face_id))
            
        recognizer.train(face_samples, np.array(ids))
        return recognizer
    except:
        return None

def show():
    st.header("🔄 Advanced PIN Recovery")
    
    if 'reset_step' not in st.session_state:
        st.session_state.reset_step = 1
    if 'reset_user_data' not in st.session_state:
        st.session_state.reset_user_data = None

    # --- STEP 1: VERIFY CREDENTIALS (No Changes) ---
    if st.session_state.reset_step == 1:
        st.subheader("🛡️ Step 1: Basic Information")
        with st.container(border=True):
            r_email = st.text_input("Registered Email").strip().lower()
            r_cnic = st.text_input("13-Digit CNIC", max_chars=13)
            r_phone = st.text_input("Registered Phone", max_chars=11)

            if st.button("Verify Details ➡️", use_container_width=True):
                v_cnic, m_cnic = val.validate_cnic(r_cnic)
                v_phone, m_phone = val.validate_phone(r_phone)
                
                if not v_cnic or not v_phone:
                    st.error(f"{m_cnic if not v_cnic else m_phone}")
                    return

                users = dm.get_users()
                user = next((u for u in users if u['email'] == r_email and 
                             str(u['cnic']) == str(r_cnic) and 
                             str(u['phone']) == str(r_phone)), None)
                
                if user:
                    st.session_state.reset_user_data = user
                    st.session_state.reset_step = 2
                    st.rerun()
                else:
                    st.error("❌ Identity Mismatch: Provided details do not match.")

    # --- STEP 2: SECURITY QUESTION (No Changes) ---
    elif st.session_state.reset_step == 2:
        user = st.session_state.reset_user_data
        st.subheader("👤 Step 2: Identity Confirmation")
        st.success(f"Hello, **{user['f_name']} {user['l_name']}**!")
        
        with st.container(border=True):
            ans = st.text_input(f"Security Question: What is your mother's maiden name?", type="password")
            if st.button("Confirm & Proceed to Biometrics", use_container_width=True):
                if ans.strip().lower() == user['sec_ans'].strip().lower():
                    st.session_state.reset_step = 3
                    st.rerun()
                else:
                    st.error("❌ Incorrect Security Answer.")

    # --- STEP 3: FACE VERIFICATION (UPDATED FOR CLOUD) ---
    elif st.session_state.reset_step == 3:
        user = st.session_state.reset_user_data
        st.subheader("📸 Step 3: Biometric Face Scan")
        st.info(f"Scanning for Account: {user['account_no']}")
        
        # Streamlit Camera Input instead of cv2.VideoCapture
        img_file = st.camera_input("Verify identity to reset PIN")

        if img_file:
            with st.spinner("Verifying Biometrics..."):
                recognizer = train_specific_user(user['face_id'], user['account_no'])
                
                if recognizer is None:
                    st.error("🚨 Biometric data not found!")
                    return

                # Convert image for processing
                image = Image.open(img_file)
                img_array = np.array(image)
                cv2_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
                
                face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                if len(faces) > 0:
                    for (x, y, w, h) in faces:
                        detected_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                        
                        # Strict Security Logic
                        if detected_id == int(user['face_id']) and confidence < 35:
                            st.success(f"✅ Identity Verified! (Confidence: {round(100-confidence, 1)}%)")
                            time.sleep(1.5)
                            st.session_state.reset_step = 4
                            st.rerun()
                        else:
                            st.error("❌ Face Mismatch! Access Denied.")
                else:
                    st.warning("No face detected. Please ensure proper lighting.")

    # --- STEP 4: NEW PIN SETTING (No Changes) ---
    elif st.session_state.reset_step == 4:
        st.subheader("🔑 Step 4: Set New PIN")
        with st.container(border=True):
            new_p1 = st.text_input("New 4-Digit PIN", type="password", max_chars=4)
            new_p2 = st.text_input("Confirm New PIN", type="password", max_chars=4)

            if st.button("Update PIN & Unlock Account", use_container_width=True):
                v_pin, m_pin = val.validate_pin(new_p1, new_p2)
                if v_pin:
                    dm.update_pin(st.session_state.reset_user_data['cnic'], new_p1)
                    st.success("✅ PIN reset successful! Please login.")
                    st.balloons()
                    time.sleep(2)
                    st.session_state.reset_step = 1
                    st.session_state.page = "Login"
                    st.rerun()
                else:
                    st.error(m_pin)

    if st.button("❌ Cancel Recovery"):
        st.session_state.reset_step = 1
        st.session_state.reset_user_data = None
        st.session_state.page = "Login"
        st.rerun()