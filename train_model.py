import pandas as pd
import numpy as np
from xgboost import XGBClassifier
import joblib
import os

def execute_model_training():
    print("⏳ Training Machine Learning Matrix via XGBoost Optimized Estimators...")
    
    np.random.seed(42)
    samples = 2000
    
    # Match the explicit schema vocabulary required by the inference gate
    feature_names = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount'] + ['scaled_amount', 'scaled_time']
    
    # Generate synthetic observations with structural markers for fraud anomalies
    X_train = pd.DataFrame(np.random.randn(samples, len(feature_names)), columns=feature_names)
    X_train['Time'] = np.random.uniform(0, 172800, samples)
    X_train['Amount'] = np.random.exponential(scale=88.0, size=samples)
    X_train['scaled_time'] = X_train['Time'] / 10000.0
    X_train['scaled_amount'] = X_train['Amount'] / 10.0
    
    # Create an explicit rule mapping deep negative deviations to positive target labels
    y_train = np.where((X_train['V14'] < -2.0) | (X_train['V17'] < -2.0) | (X_train['Amount'] > 2500), 1, 0)
    
    # Configure production tree depth scales
    model = XGBClassifier(
        n_estimators=50,
        max_depth=4,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/fraud_xgb_model.pkl')
    print("✅ XGBoost Model optimized and saved into 'models/fraud_xgb_model.pkl'")

if __name__ == '__main__':
    execute_model_training()