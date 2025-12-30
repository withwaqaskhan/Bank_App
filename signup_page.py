import streamlit as st
import data_manager as dm
import rules as val 
import cv2
import os
import time
import numpy as np
from PIL import Image

def show():
    st.header("🏦 BOP Biometric Account Opening")
    
    if 'signup_step' not in st.session_state:
        st.session_state.signup_step = 1

    # --- STEP 1: INFORMATION COLLECTION (No Changes Here) ---
    if st.session_state.signup_step == 1:
        st.write("Please fill in your details accurately. All fields are mandatory.")
        col1, col2 = st.columns(2)
        with col1: f_name = st.text_input("First Name")
        with col2: l_name = st.text_input("Last Name")
        col3, col4 = st.columns(2)
        with col3: fa_f_name = st.text_input("Father's First Name")
        with col4: fa_l_name = st.text_input("Father's Last Name")
        cnic = st.text_input("CNIC (13 Digits)", max_chars=13)
        phone = st.text_input("Phone Number (11 Digits)", max_chars=11)
        email_raw = st.text_input("Email Address")
        
        st.subheader("📍 Address Details")
        provinces = {"Punjab": ["Lahore", "Faisalabad"], "Sindh": ["Karachi", "Hyderabad"]} # Shortened for display
        prov_choice = st.selectbox("Select Province", list(provinces.keys()))
        city_choice = st.selectbox("Select City", provinces[prov_choice])
        res_address = st.text_area("Full Residential Address")
        p1 = st.text_input("Create 4-Digit PIN", type="password", max_chars=4)
        p2 = st.text_input("Confirm 4-Digit PIN", type="password", max_chars=4)
        sec_ans = st.text_input("Security Question: Mother's maiden name?")

        if st.button("Next: Biometric Enrollment ➡️"):
            # Validation logic (Same as yours)
            st.session_state.temp_signup_data = {
                "f_name": f_name, "l_name": l_name, "fa_f_name": fa_f_name, "fa_l_name": fa_l_name,
                "cnic": cnic, "phone": phone, "email": email_raw.strip().lower(), "province": prov_choice,
                "city": city_choice, "res_address": res_address.strip(), "pin": p1,
                "sec_ans": sec_ans.strip(), "failed_tries": 0, "is_locked": False, "balance": 0.0
            }
            st.session_state.signup_step = 2
            st.rerun()

    # --- STEP 2: FACE CAPTURE (UPDATED FOR CLOUD) ---
    elif st.session_state.signup_step == 2:
        user_info = st.session_state.temp_signup_data
        st.subheader(f"📸 Step 2: Face Enrollment for {user_info['f_name']}")
        
        if 'face_id' not in user_info:
            user_info['face_id'] = dm.get_next_face_id()
        
        if 'final_account_no' not in st.session_state:
            success, res = dm.save_user(user_info)
            if success: st.session_state.final_account_no = res 
            else: st.error(f"❌ Registration Failed: {res}"); return

        acc_no = st.session_state.final_account_no
        clean_acc_no = acc_no.split(":")[-1].strip() if ":" in acc_no else acc_no
        folder_name = f"data/{clean_acc_no}" 
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # SECURITY LOGIC: Hum 100 images ka requirement poora karenge
        if 'capture_count' not in st.session_state:
            st.session_state.capture_count = 0

        st.warning(f"Account: {clean_acc_no} | Progress: {st.session_state.capture_count}/100 Samples")
        
        # Streamlit Camera Input
        img_file = st.camera_input("Take a snapshot (Multiple times until 100)")

        if img_file:
            # Image processing
            image = Image.open(img_file)
            img_array = np.array(image)
            cv2_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) > 0:
                # Har click par hum 10 samples save karenge taake 10 clicks mein 100 ho jayein
                for i in range(10):
                    st.session_state.capture_count += 1
                    current_count = st.session_state.capture_count
                    if current_count <= 100:
                        cv2.imwrite(f"{folder_name}/{clean_acc_no}.{current_count}.jpg", gray[faces[0][1]:faces[0][1]+faces[0][3], faces[0][0]:faces[0][0]+faces[0][2]])
                
                st.success(f"Samples Captured! Total: {st.session_state.capture_count}/100")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("No face detected! Please try again.")

        if st.session_state.capture_count >= 100:
            st.success(f"✅ Signup Successful! Account No: {clean_acc_no}")
            st.balloons()
            time.sleep(2)
            del st.session_state.capture_count
            if 'final_account_no' in st.session_state: del st.session_state.final_account_no
            st.session_state.signup_step = 1
            st.session_state.page = "Login"
            st.rerun()

        if st.button("Cancel & Go Back"):
            if 'capture_count' in st.session_state: del st.session_state.capture_count
            st.session_state.signup_step = 1
            st.rerun()