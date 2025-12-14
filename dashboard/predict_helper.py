import pandas as pd
import numpy as np
import joblib
import psycopg2
import sys
import os
from datetime import datetime

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

class ChurnPredictor:
    """Churn prediction model wrapper"""
    
    def __init__(self, model_path='../data/models/logistic_regression_model.pkl',
                 scaler_path='../data/models/scaler.pkl',
                 feature_names_path='../data/models/feature_names.pkl'):
        """Load model and artifacts"""
        print("Loading model artifacts...")
        
        try:
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            self.feature_names = joblib.load(feature_names_path)
            print(f"Model loaded: {model_path}")
            print(f"Scaler loaded: {scaler_path}")
            print(f"Features loaded: {len(self.feature_names)} features")
        except Exception as e:
            print(f"Error loading model artifacts: {e}")
            self.model = None
            self.scaler = None
            self.feature_names = None
    
    def get_customer_data(self, customer_id):
        """Fetch customer data from PostgreSQL"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            
            query = "SELECT * FROM customers WHERE customer_id = %s"
            cursor.execute(query, (customer_id,))
            result = cursor.fetchone()
            
            if not result:
                cursor.close()
                conn.close()
                return None
            
            columns = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()
            
            customer_dict = dict(zip(columns, result))
            return customer_dict
            
        except Exception as e:
            print(f"Error fetching customer data: {e}")
            return None
    
    def preprocess_customer(self, customer_dict):
        """Preprocess single customer data"""
        df = pd.DataFrame([customer_dict])
        
        # Basic preprocessing
        df['total_charges'] = pd.to_numeric(df['total_charges'], errors='coerce')
        df['total_charges'].fillna(df['monthly_charges'], inplace=True)
        df['senior_citizen'] = df['senior_citizen'].astype(int)
        
        # Engineer features
        df['tenure_group'] = pd.cut(df['tenure'], 
                                     bins=[0, 12, 24, 48, 72],
                                     labels=['0-1yr', '1-2yr', '2-4yr', '4yr+'])
        
        service_cols = ['phone_service', 'multiple_lines', 'internet_service',
                        'online_security', 'online_backup', 'device_protection',
                        'tech_support', 'streaming_tv', 'streaming_movies']
        
        df['total_services'] = 0
        for col in service_cols:
            if col in df.columns:
                df['total_services'] += (df[col] == 'Yes').astype(int)
        
        df['charges_category'] = pd.cut(df['monthly_charges'],
                                         bins=[0, 30, 60, 90, 150],
                                         labels=['Low', 'Medium', 'High', 'Very High'])
        
        contract_risk = {'Month-to-month': 1.0, 'One year': 0.5, 'Two year': 0.2}
        df['contract_risk'] = df['contract'].map(contract_risk)
        
        payment_risk = {'Electronic check': 1.0, 'Mailed check': 0.7,
                       'Bank transfer (automatic)': 0.3, 'Credit card (automatic)': 0.3}
        df['payment_risk'] = df['payment_method'].map(payment_risk)
        
        df['avg_monthly_revenue'] = df['total_charges'] / (df['tenure'] + 1)
        df['has_family'] = ((df['partner'] == 'Yes') | (df['dependents'] == 'Yes')).astype(int)
        df['has_internet'] = (df['internet_service'] != 'No').astype(int)
        
        # Add missing features
        df['total_events'] = 0
        df['payment_fail_rate'] = 0
        df['support_frequency'] = 0
        df['total_tickets'] = 0
        df['sentiment_score'] = 0
        
        # Encode categorical
        binary_cols = ['gender', 'partner', 'dependents', 'phone_service', 'paperless_billing']
        for col in binary_cols:
            if col in df.columns:
                df[col] = (df[col] == 'Yes').astype(int)
        
        categorical_cols = ['multiple_lines', 'internet_service', 'online_security',
                           'online_backup', 'device_protection', 'tech_support',
                           'streaming_tv', 'streaming_movies', 'contract', 
                           'payment_method', 'tenure_group', 'charges_category']
        
        df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
        
        # Align with training features
        for col in self.feature_names:
            if col not in df_encoded.columns:
                df_encoded[col] = 0
        
        X = df_encoded[self.feature_names]
        return X
    
    def predict(self, customer_id):
        """Make prediction for a customer"""
        if self.model is None:
            return None
            
        customer_dict = self.get_customer_data(customer_id)
        if customer_dict is None:
            return None
        
        X = self.preprocess_customer(customer_dict)
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        probability = self.model.predict_proba(X_scaled)[0]
        
        churn_prob = probability[1]
        risk_level = 'HIGH' if churn_prob > 0.7 else 'MEDIUM' if churn_prob > 0.4 else 'LOW'
        
        return {
            'customer_id': customer_id,
            'prediction': int(prediction),
            'churn_probability': float(churn_prob),
            'risk_level': risk_level,
            'timestamp': datetime.now().isoformat()
        }
    
    def predict_batch(self, customer_ids):
        """Make predictions for multiple customers"""
        results = []
        for customer_id in customer_ids:
            result = self.predict(customer_id)
            if result:
                results.append(result)
        return results
