import streamlit as st
import pandas as pd
import numpy as np
import joblib
import shap
import matplotlib.pyplot as plt

# Set page layout
st.set_page_config(page_title="Fraud Detection System", layout="wide")

st.title("🛡️ Real-Time Credit Card Fraud Detection System")
st.write("This dashboard leverages an advanced XGBoost model trained on millions of data points to predict and explain potential fraudulent transactions.")

# 1. Load the saved model and scaler
@st.cache_resource
def load_assets():
    model = joblib.load('models/fraud_xgb_model.pkl')
    scaler = joblib.load('models/data_scaler.pkl')
    return model, scaler

try:
    model, scaler = load_assets()
    st.sidebar.success("✅ ML Model Loaded Successfully")
except Exception as e:
    st.sidebar.error("❌ Error loading model. Did you run train_model.py?")

# 2. Sidebar Input Fields for Simulation
st.sidebar.header("📥 Simulate Transaction Details")

amount = st.sidebar.number_input("Transaction Amount ($)", min_value=0.0, max_value=100000.0, value=150.0, step=5.0)
time_step = st.sidebar.number_input("Time (Seconds elapsed since first txn)", min_value=0, max_value=172800, value=3600)

st.sidebar.subheader("Anonymized PCA Features (V1 - V28)")
st.sidebar.write("Adjust a few sliders to simulate abnormal transaction behavior:")
v14 = st.sidebar.slider("V14 (Highly critical for fraud)", -15.0, 15.0, 0.0)
v17 = st.sidebar.slider("V17 (Highly critical for fraud)", -15.0, 15.0, 0.0)
v12 = st.sidebar.slider("V12 Feature", -15.0, 15.0, 0.0)
v10 = st.sidebar.slider("V10 Feature", -15.0, 15.0, 0.0)

# Build a complete feature row filling defaults for other V-features
features = {}
for i in range(1, 29):
    features[f'V{i}'] = 0.0  # default neutral value

# Override with user inputs
features['V10'] = v10
features['V12'] = v12
features['V14'] = v14
features['V17'] = v17

# 3. Process Inputs
# Scale Amount and Time exactly how we did during training
scaled_amount = scaler.transform([[amount]])[0][0]
scaled_time = scaler.transform([[time_step]])[0][0]

features['scaled_amount'] = scaled_amount
features['scaled_time'] = scaled_time

# Convert to DataFrame matching the exact training column order
input_df = pd.DataFrame([features])

# --- Main Dashboard Logic ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🔮 Real-Time Prediction Engine")
    if st.button("Analyze Transaction", type="primary"):
        # Get probability and final prediction
        prob = model.predict_proba(input_df)[0][1]
        risk_score = int(prob * 100)
        
        st.metric(label="Calculated Fraud Risk Score", value=f"{risk_score}%")
        
        if risk_score >= 50:
            st.error("🚨 ALERT: POTENTIAL FRAUDULENT TRANSACTION DETECTED")
            st.warning(f"**Action Recommended:** Decline transaction instantly and dispatch an SMS alert to cardholder for Verification ID: {np.random.randint(10000, 99999)}.")
        else:
            st.success("✅ TRANSACTION APPROVED: Legitimate Pattern Identified.")
            
with col2:
    st.subheader("💡 Explainable AI (SHAP Insights)")
    st.write("Why did the model make this decision? Below are the top features pushing the risk score up (+) or down (-).")
    
    if st.button("Generate SHAP Explanation"):
        # Initialize SHAP explainer
        explainer = shap.TreeExplainer(model)
        shap_values = explainer(input_df)
        
        # Plot force plot or waterfall plot using matplotlib style
        fig, ax = plt.subplots(figsize=(10, 4))
        shap.plots.waterfall(shap_values[0], max_display=6, show=False)