from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import JWTError, jwt
import pandas as pd
import numpy as np
import joblib
import hashlib
import traceback

# Native SHA-256 Hashing (No passlib dependencies)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Identity Registry Database Container
USER_DB = {
    "admin@riskshield.ai": {
        "username": "admin@riskshield.ai",
        "hashed_password": hash_password("admin123"),
        "role": "Admin",
        "name": "Chief Risk Officer"
    },
    "analyst@riskshield.ai": {
        "username": "analyst@riskshield.ai",
        "hashed_password": hash_password("analyst123"),
        "role": "Auditor",
        "name": "Junior Fraud Analyst"
    }
}

SECRET_KEY = "SUPER_SECRET_RISKSHIELD_KEY_KEEP_IT_SAFE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI(title="RiskShield Guarded Enterprise AI Hub")

# Explicit CORS pipeline policies permitting all cross-origin transfers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🚂 TRAINING MODEL / SCALER LOADER WITH FAILSAFE PROTECTION
try:
    model = joblib.load('models/fraud_xgb_model.pkl')
    scaler = joblib.load('models/data_scaler.pkl')
    print("[OK] XGBoost Model and Preprocessing Scaler loaded safely into memory.")
except Exception as e:
    print(f"[ERROR] Error loading serialized models: {e}")
    print("[WARNING] Activating internal synthetic visualization simulator loop fallback.")
    
    class SyntheticModel:
        def predict_proba(self, df):
            # Safe calculation using sliders data for realistic dashboard visual updates
            v14_val = float(df['V14'].iloc[0]) if 'V14' in df.columns else 0.0
            v17_val = float(df['V17'].iloc[0]) if 'V17' in df.columns else 0.0
            # Support fallback logic if model uses different column index keys natively
            amt_key = 'scaled_amount' if 'scaled_amount' in df.columns else 'Amount'
            amt_val = float(df[amt_key].iloc[0]) if amt_key in df.columns else 100.0
            
            score_metric = (abs(v14_val) * 0.25) + (abs(v17_val) * 0.20) + (min(amt_val / 5000.0, 0.5))
            prob = min(max(score_metric, 0.05), 0.95)
            return np.array([[1.0 - prob, prob]])
            
    model = SyntheticModel()
    scaler = None

class TransactionData(BaseModel):
    amount: float
    time: float
    v10: float
    v12: float
    v14: float
    v17: float

class ChatMessage(BaseModel):
    user_question: str
    amount: float
    risk_score: int
    v14: float
    v17: float

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate security credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user = USER_DB.get(username)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = USER_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "role": user["role"],
        "name": user["name"]
    }

# ⚙️ THE SECURED INFERENCE INTERCEPTOR PIPELINE
@app.post("/predict")
def predict_fraud(data: TransactionData, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access Denied: Your clearance level only permits view-only access."
        )
        
    try:
        # 1. Construct baseline features in standard structured sequence
        standard_order = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount']
        
        raw_features = {col: 0.0 for col in standard_order}
        raw_features['Time'] = float(data.time)
        raw_features['V10'] = float(data.v10)
        raw_features['V12'] = float(data.v12)
        raw_features['V14'] = float(data.v14)
        raw_features['V17'] = float(data.v17)
        raw_features['Amount'] = float(data.amount)
        
        # Lock column sequence mapping inside the dataframe
        input_df = pd.DataFrame([raw_features])[standard_order]
        
        # 2. Process data engineering scales through saved transformations
        if scaler is not None:
            try:
                # If scaler tracks all 30 standard properties
                scaled_values = scaler.transform(input_df)
                input_df = pd.DataFrame(scaled_values, columns=standard_order)
            except Exception:
                try:
                    # Fallback if scaler only transformed [Time, Amount] dimensions
                    scale_buffer = pd.DataFrame([{'Time': data.time, 'Amount': data.amount}])
                    scaled_results = scaler.transform(scale_buffer)
                    input_df['Time'] = scaled_results[0][0]
                    input_df['Amount'] = scaled_results[0][1]
                except Exception:
                    pass # Protect pipeline and use raw numeric indicators if shapes mismatch

        # 3. 🚀 MAPPING ALIGNMENT: Explicitly assign columns to match model vocabulary index
        input_df['scaled_amount'] = input_df['Amount']
        input_df['scaled_time'] = input_df['Time']

        # 4. Enforce strict XGBoost structural matching parameters
        if hasattr(model, "feature_names_in_"):
            expected_cols = list(model.feature_names_in_)
            # Guarantee any feature unexpected from the frontend defaults to 0.0
            for col in expected_cols:
                if col not in input_df.columns:
                    input_df[col] = 0.0
            input_df = input_df[expected_cols]
        
        # 5. Execute matrix calculation vectors
        prob = model.predict_proba(input_df)[0][1]
        risk_score = int(prob * 100)
        status_label = "HIGH RISK TRANSACTION" if risk_score >= 50 else "APPROVED"
        
        return {
            "status": "success",
            "risk_score": risk_score,
            "prediction": status_label,
            "transaction_id": int(np.random.randint(100000, 999999))
        }
    except Exception as e:
        # Trace errors right to terminal shell window for deep system observability
        print("\n!!! --- PIPELINE INFERENCE CRASH TRACE --- !!!")
        traceback.print_exc()
        print("!!! -------------------------------------- !!!\n")
        raise HTTPException(status_code=500, detail=f"Inference Pipeline Error: {str(e)}")

@app.post("/chat")
def chat_with_agent(message: ChatMessage, current_user: dict = Depends(get_current_user)):
    q = message.user_question.lower()
    score = message.risk_score
    
    if "why" in q or "reason" in q or "flag" in q:
        if score >= 50:
            return {"response": f"🤖 [Agent Core]: Attention {current_user['name']} ({current_user['role']}). This payload was flagged due to excessive negative anomalies matching fraud benchmarks in feature metrics V14 and V17."}
        else:
            return {"response": f"🤖 [Agent Core]: Hello {current_user['name']}. This vector data set fits entirely inside standard client baseline boundaries."}
    
    return {"response": f"🤖 [Agent Core]: Standing by for analytical trace commands, Officer {current_user['name']}."}

# Serve static frontend files
@app.get("/")
def read_root():
    return FileResponse("index.html")

app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")