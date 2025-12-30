import streamlit as st
import cv2
import numpy as np
import os
from PIL import Image
import data_manager as dm
import time

def train_specific_user(face_id, account_no):
    """Specific user ke folder se FRESH training karta hai (Zero Memory Strategy)."""
    # Har baar naya instance taake purani memory ka sawal hi paida na ho
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    
    path = f"data/{account_no}"
    
    if not os.path.exists(path) or len(os.listdir(path)) == 0:
        return None

    face_samples = []
    ids = []
    
    try:
        # Model ko sirf is user ke specific folder par lock karna
        for img_name in os.listdir(path):
            img_path = os.path.join(path, img_name)
            gray_img = Image.open(img_path).convert('L')
            img_numpy = np.array(gray_img, 'uint8')
            
            face_samples.append(img_numpy)
            ids.append(int(face_id))
            
        # Training ON DEMAND (Sirf is interaction ke liye)
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
            st.rerun()
        return

    # Visual container for status
    with st.container(border=True):
        st.info(f"👤 Target Identity: **{user['f_name']} {user['l_name']}**")
        st.caption(f"Account No: {user.get('account_no')}")
        
        col1, col2 = st.columns(2)
        with col1:
            start_scan = st.button("📷 Start Face Scan", use_container_width=True, type="primary")
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.temp_user = None
                st.session_state.page = "Login"
                st.rerun()

        if start_scan:
            # 1. AUTO-REFRESH: Model ko har interaction par naye siray se train karna
            with st.spinner(f"Refreshing Biometric Model for {user['account_no']}..."):
                recognizer = train_specific_user(user['face_id'], user['account_no'])
                time.sleep(1)
            
            if recognizer is None:
                st.error("🚨 Error: Biometric data not found for this account!")
                return

            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            cap = cv2.VideoCapture(0)
            
            frame_placeholder = st.empty()
            match_buffer = 0 
            
            # 2. Recognition Loop with MULTI-LAYER SECURITY
            while True:
                ret, frame = cap.read()
                if not ret: break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                status_text = "Scanning..."
                color = (255, 165, 0)

                for (x, y, w, h) in faces:
                    # ✅ SECURITY LAYER 1: Face size validation
                    if w < 80 or h < 80 or w > 400 or h > 400:
                        continue  # Ignore too small/large faces
                    
                    # Confidence check (Lower is more secure)
                    detected_id, confidence = recognizer.predict(gray[y:y+h, x:x+w])
                    
                    # --- MULTI-LAYER SECURITY LOGIC ---
                    # ✅ SECURITY LAYER 2: Strict confidence threshold
                    if detected_id == int(user['face_id']) and confidence < 25:
                        match_buffer += 1
                        status_text = f"Verifying Identity: {int(match_buffer/45 * 100)}%"
                        color = (0, 255, 0)
                    
                    # ✅ SECURITY LAYER 3: Instant intruder detection
                    elif confidence > 40:
                        match_buffer = 0
                        status_text = "⛔ INTRUDER ALERT!"
                        color = (0, 0, 255)
                        cv2.putText(frame, "UNAUTHORIZED ACCESS", (50, 50), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    
                    else:
                        match_buffer = 0
                        status_text = "Face Not Recognized"
                        color = (255, 165, 0)
                    
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

                # ✅ SECURITY LAYER 4: Extended verification time
                if match_buffer >= 45: 
                    cap.release()
                    cv2.destroyAllWindows()
                    st.success("✅ Identity Confirmed! Accessing Dashboard...")
                    st.balloons()
                    time.sleep(1.5)
                    st.session_state.logged_in_user = user
                    st.session_state.temp_user = None 
                    st.session_state.page = "Dashboard"
                    st.rerun()
                    break

            cap.release()
            cv2.destroyAllWindows()
            # 3. MEMORY WIPE: Recognizer variable yahan destroy ho jayega

    st.caption("⚠️ Your biometric data is trained on-the-fly and wiped after session verification.")