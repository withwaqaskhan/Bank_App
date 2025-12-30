import joblib
import pandas as pd
import os
import data_manager as dm # History save karne ke liye

# Files ka path set karein
MODEL_DIR = "Insurance_model"

def predict_insurance_premium(age, bmi, children, blood_pressure, gender, diabetic, smoker, account_no):
    try:
        # 1. Models aur Encoders load karein
        model = joblib.load(os.path.join(MODEL_DIR, "best_model.pkl"))
        le_gender = joblib.load(os.path.join(MODEL_DIR, "label_encoder_gender.pkl"))
        le_diabetic = joblib.load(os.path.join(MODEL_DIR, "label_encoder_diabetic.pkl"))
        le_smoker = joblib.load(os.path.join(MODEL_DIR, "label_encoder_smoker.pkl"))
        scaler = joblib.load(os.path.join(MODEL_DIR, "scaler.pkl"))

        # 2. Categorical Encoding
        gender_encoded = le_gender.transform([gender])[0]
        diabetic_encoded = le_diabetic.transform([diabetic])[0]
        smoker_encoded = le_smoker.transform([smoker])[0]

        # 3. Numeric Scaling
        numeric_data = pd.DataFrame([[age, bmi, blood_pressure, children]], 
                                    columns=['age', 'bmi', 'bloodpressure', 'children'])
        scaled_numeric = scaler.transform(numeric_data)

        # 4. Final Input Vector
        final_input = pd.DataFrame([[
            scaled_numeric[0][0], gender_encoded, scaled_numeric[0][1],
            scaled_numeric[0][2], diabetic_encoded, scaled_numeric[0][3], smoker_encoded
        ]], columns=['age', 'gender', 'bmi', 'bloodpressure', 'diabetic', 'children', 'smoker'])

        # 5. Prediction
        prediction = model.predict(final_input)
        premium_amt = float(prediction[0])

        # 6. Save to History (Updated for EDA)
        # Category "Medical" add kar di gayi hai taake EDA graphs sahi banein
        dm.record_transaction(
            t_type="Insurance", 
            amount=premium_amt, 
            account_no=account_no,
            category="Medical", 
            status="AI_Estimated"
        )
        
        return premium_amt

    except Exception as e:
        print(f"🚨 Insurance Prediction Error: {e}")
        return None