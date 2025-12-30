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
    # 1. Bilkul naya recognizer (Purani memory khatam)
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    # Path ko account_no par set kiya (Jese Verify page mein hai)
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
            
        # Sirf isi folder par training
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

    # --- STEP 1: VERIFY CREDENTIALS ---
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

    # --- STEP 2: SECURITY QUESTION ---
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

    # --- STEP 3: FACE VERIFICATION (Updated Logic) ---
    elif st.session_state.reset_step == 3:
        user = st.session_state.reset_user_data
        st.subheader("📸 Step 3: Biometric Face Scan")
        st.info(f"Scanning for Account: {user['account_no']}")
        
        if st.button("Start Scan", use_container_width=True, type="primary"):
            with st.spinner("Initializing Isolated Biometric Sensor..."):
                # Yahan account_no pass kiya taake folder sahi dhoond sakay
                recognizer = train_specific_user(user['face_id'], user['account_no'])
                time.sleep(1)
            
            if recognizer is None:
                st.error("🚨 Biometric data not found! System could not locate your face profile.")
                return

            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            cap = cv2.VideoCapture(0)
            frame_placeholder = st.empty()
            match_buffer = 0

            while True:
                ret, frame = cap.read()
                if not ret: break
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)

                status_text = "Scanning..."
                color = (255, 165, 0)

                for (x, y, w, h) in faces:
                    # Confidence and ID Predict
                    detected_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                    
                    # Verify page wali Strict Logic (Score < 35)
                    if detected_id == int(user['face_id']) and confidence < 35:
                        match_buffer += 1
                        status_text = f"Identity Verified: {int(match_buffer/30 * 100)}%"
                        color = (0, 255, 0)
                    else:
                        match_buffer = 0
                        status_text = "Mismatch!"
                        color = (0, 0, 255)
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                if match_buffer >= 30:
                    cap.release()
                    cv2.destroyAllWindows()
                    st.session_state.reset_step = 4
                    st.rerun()
                    break

            cap.release()
            cv2.destroyAllWindows()

    # --- STEP 4: NEW PIN SETTING ---
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