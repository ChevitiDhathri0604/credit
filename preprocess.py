import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib
import os

def build_scaler():
    print("⏳ Initializing Preprocessing Transformation Pipeline...")
    
    # Simulating standard layout distributions matching baseline datasets
    np.random.seed(42)
    synthetic_records = 2000
    
    standard_order = ['Time'] + [f'V{i}' for i in range(1, 29)] + ['Amount']
    synthetic_data = np.random.randn(synthetic_records, len(standard_order))
    
    df = pd.DataFrame(synthetic_data, columns=standard_order)
    # Give Time and Amount realistic baseline spreads
    df['Time'] = np.random.uniform(0, 172800, synthetic_records)
    df['Amount'] = np.random.exponential(scale=88.0, size=synthetic_records)
    
    # Configure and fit the StandardScaler to calculate mean & variance properties
    scaler = StandardScaler()
    scaler.fit(df)
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(scaler, 'models/data_scaler.pkl')
    print("✅ Preprocessing Scaler successfully generated and saved into 'models/data_scaler.pkl'")

if __name__ == '__main__':
    build_scaler()