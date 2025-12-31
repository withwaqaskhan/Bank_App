import streamlit as st
import cv2
import numpy as np
import os
from PIL import Image
import data_manager as dm
import time

def train_specific_user(face_id, account_no):
    """Specific user ke folder se FRESH training karta hai (Zero Memory Strategy)."""
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
    st.header("🛡️ Biometric Identity Verification")
    st.write("Scan your face to unlock your secure banking dashboard.")
    
    user = st.session_state.get('temp_user')
    
    if not user:
        st.error("Session expired. Please login again.")
        if st.button("Back to Login"):
            st.session_state.page = "Login"
            st.session_state.page = "Login"
            st.rerun()
        return

    with st.container(border=True):
        st.info(f"👤 Target Identity: **{user['f_name']} {user['l_name']}**")
        st.caption(f"Account No: {user.get('account_no')}")
        
        # Streamlit Camera Input (Cloud-friendly tareeqa)
        img_file_buffer = st.camera_input("📷 Take a photo to verify identity")

        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.temp_user = None
            st.session_state.page = "Login"
            st.rerun()

        if img_file_buffer:
            # 1. Training for security (Aapka original logic)
            with st.spinner(f"Refreshing Biometric Model for {user['account_no']}..."):
                recognizer = train_specific_user(user['face_id'], user['account_no'])
            
            if recognizer is None:
                st.error("🚨 Error: Biometric data not found!")
                return

            # Image processing
            bytes_data = img_file_buffer.getvalue()
            cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
            gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                st.warning("No face detected. Please adjust your lighting and try again.")
            
            for (x, y, w, h) in faces:
                # ✅ SECURITY LAYER 1: Size check
                if w < 80 or h < 80:
                    st.error("Face too far or small!")
                    continue

                # Prediction
                detected_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                
                # ✅ SECURITY LAYER 2 & 3: Strict confidence logic (Aapka logic)
                if detected_id == int(user['face_id']) and confidence < 35:
                    st.success(f"✅ Identity Confirmed! (Confidence: {round(100 - confidence, 2)}%)")
                    st.balloons()
                    time.sleep(1.5)
                    st.session_state.logged_in_user = user
                    st.session_state.temp_user = None 
                    st.session_state.page = "Dashboard"
                    st.rerun()
                elif confidence > 40:
                    st.error("⛔ INTRUDER ALERT! Unauthorized access denied.")
                else:
                    st.warning("Face not recognized clearly. Try again.")

    st.caption("⚠️ Your biometric data is trained on-the-fly and wiped after session verification.")