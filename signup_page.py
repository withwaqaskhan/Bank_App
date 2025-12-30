import streamlit as st
import data_manager as dm
import rules as val 
import cv2
import os
import time

def show():
    st.header("🏦 BOP Biometric Account Opening")
    
    # Initialize signup step if not present
    if 'signup_step' not in st.session_state:
        st.session_state.signup_step = 1

    # --- STEP 1: INFORMATION COLLECTION ---
    if st.session_state.signup_step == 1:
        st.write("Please fill in your details accurately. All fields are mandatory.")

        # 1. Name Section
        col1, col2 = st.columns(2)
        with col1:
            f_name = st.text_input("First Name", help="One word only, no spaces.")
        with col2:
            l_name = st.text_input("Last Name", help="One word only, no spaces.")

        col3, col4 = st.columns(2)
        with col3:
            fa_f_name = st.text_input("Father's First Name")
        with col4:
            fa_l_name = st.text_input("Father's Last Name")

        # 2. Personal Identification
        cnic = st.text_input("CNIC (13 Digits)", max_chars=13)
        phone = st.text_input("Phone Number (11 Digits)", max_chars=11)
        email_raw = st.text_input("Email Address (Must be .com)")

        # 3. Address Section
        st.subheader("📍 Address Details")
        provinces = {
            "Punjab": ["Lahore", "Faisalabad", "Rawalpindi", "Multan", "Gujranwala"],
            "Sindh": ["Karachi", "Hyderabad", "Sukkur", "Larkana"],
            "KPK": ["Peshawar", "Abbottabad", "Mardan"],
            "Balochistan": ["Quetta", "Gwadar", "Sibi"]
        }
        
        col_p, col_c = st.columns(2)
        with col_p:
            prov_choice = st.selectbox("Select Province", list(provinces.keys()))
        with col_c:
            city_choice = st.selectbox("Select City", provinces[prov_choice])
        
        res_address = st.text_area("Full Residential Address", placeholder="House No, Street Name, Area...")

        # 4. Security & PIN
        p1 = st.text_input("Create 4-Digit PIN", type="password", max_chars=4)
        p2 = st.text_input("Confirm 4-Digit PIN", type="password", max_chars=4)
        
        st.info("Required for account recovery.")
        sec_ans = st.text_input("Security Question: What is your mother's maiden name?")

        if st.button("Next: Biometric Enrollment ➡️"):
            email_clean = email_raw.strip().lower()
            users_list = dm.get_users()
            existing_emails = [u['email'] for u in users_list]

            # All Field Validations
            v_email, e_msg = val.validate_email(email_clean, existing_emails)
            v1, m1 = val.validate_no_space(f_name, "First Name")
            v2, m2 = val.validate_no_space(l_name, "Last Name")
            v5, m5 = val.validate_cnic(cnic)
            v8, m8 = val.validate_pin(p1, p2)

            if not v_email:
                st.error(f"🚨 Email Error: {e_msg}"); return
            
            other_errors = [m1, m2, m5, m8]
            current_error = next((msg for msg in other_errors if msg != ""), None)
            if current_error:
                st.error(f"🚨 Registration Blocked: {current_error}"); return

            if not res_address.strip() or len(res_address) < 10:
                st.error("🚨 Please provide a complete residential address."); return
            
            if not sec_ans.strip() or " " in sec_ans.strip():
                st.error("🚨 Security Answer must be a single word."); return

            # Store temporarily and move to Step 2
            st.session_state.temp_signup_data = {
                "f_name": f_name, "l_name": l_name, "fa_f_name": fa_f_name, "fa_l_name": fa_l_name,
                "cnic": cnic, "phone": phone, "email": email_clean, "province": prov_choice,
                "city": city_choice, "res_address": res_address.strip(), "pin": p1,
                "sec_ans": sec_ans.strip(), "failed_tries": 0, "is_locked": False, "balance": 0.0
            }
            st.session_state.signup_step = 2
            st.rerun()

    # --- STEP 2: FACE CAPTURE (100 IMAGES) ---
    elif st.session_state.signup_step == 2:
        user_info = st.session_state.temp_signup_data
        st.subheader(f"📸 Step 2: Face Enrollment for {user_info['f_name']}")
        
        # Unique Face ID generation
        if 'face_id' not in user_info:
            user_info['face_id'] = dm.get_next_face_id()
        
        # User save kar ke response check karein
        if 'final_account_no' not in st.session_state:
            success, res = dm.save_user(user_info)
            if success:
                # 'res' yahan naya Account Number hoga (e.g., BOP-123456)
                st.session_state.final_account_no = res 
            else:
                st.error(f"❌ Registration Failed: {res}")
                return

        # --- FIX: Account Number Extraction ---
        acc_no = st.session_state.final_account_no
        
        # Agar res mein poora message aa raha hai toh usse ID extract karein
        if ":" in acc_no:
            clean_acc_no = acc_no.split(":")[-1].strip()
        else:
            clean_acc_no = acc_no

        folder_name = f"data/{clean_acc_no}" 
        
        # Create Directory safely
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        st.warning(f"Account No: {clean_acc_no} generated. We need 100 samples for your profile.")
        
        if st.button("Start Face Capture"):
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
            cap = cv2.VideoCapture(0)
            count = 0
            
            progress_bar = st.progress(0)
            frame_placeholder = st.empty()

            while count < 100:
                ret, frame = cap.read()
                if not ret: break
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                
                for (x, y, w, h) in faces:
                    count += 1
                    # File naming: AccountNo.Count.jpg
                    cv2.imwrite(f"{folder_name}/{clean_acc_no}.{count}.jpg", gray[y:y+h, x:x+w])
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                frame_placeholder.image(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                progress_bar.progress(count / 100)
                
                if cv2.waitKey(1) & 0xFF == ord('q'): break
            
            cap.release()
            cv2.destroyAllWindows()

            if count >= 100:
                st.success(f"✅ Signup Successful! Account No: {clean_acc_no}")
                st.balloons()
                time.sleep(3)
                
                # Cleanup and Reset
                if 'final_account_no' in st.session_state: del st.session_state.final_account_no
                st.session_state.signup_step = 1
                st.session_state.page = "Login"
                st.rerun()

        if st.button("Cancel & Go Back"):
            if 'final_account_no' in st.session_state: del st.session_state.final_account_no
            st.session_state.signup_step = 1
            st.rerun()

    # Back to login button (outside steps)
    if st.button("Back to Login Menu"):
        st.session_state.signup_step = 1
        st.session_state.page = "Login"
        st.rerun()