"""
Data Upload and Processing Module for ChurnGuard Dashboard
Allows customers to upload their own datasets and get predictions
"""

import pandas as pd
import numpy as np
import streamlit as st
from typing import Dict, List, Tuple
import io

class DataUploadProcessor:
    """Handle customer data uploads and preprocessing"""
    
    # Required columns for churn prediction
    REQUIRED_COLUMNS = [
        'customer_id', 'tenure', 'monthly_charges'
    ]
    
    # Optional but recommended columns
    OPTIONAL_COLUMNS = [
        'contract', 'payment_method', 'internet_service', 
        'online_security', 'tech_support', 'total_charges',
        'senior_citizen', 'partner', 'dependents'
    ]
    
    def __init__(self):
        self.data = None
        self.processed_data = None
        self.validation_results = {}
        
    def validate_file(self, file) -> Tuple[bool, str]:
        """Validate uploaded file format and size"""
        # Check file type
        if file.name.endswith('.csv'):
            file_type = 'csv'
        elif file.name.endswith(('.xlsx', '.xls')):
            file_type = 'excel'
        else:
            return False, "Unsupported file format. Please upload CSV or Excel files."
        
        # Check file size (max 50MB)
        file_size = file.size / (1024 * 1024)  # Convert to MB
        if file_size > 50:
            return False, f"File too large ({file_size:.1f}MB). Maximum size is 50MB."
        
        return True, file_type
    
    def load_data(self, file, file_type: str) -> Tuple[bool, str]:
        """Load data from uploaded file"""
        try:
            if file_type == 'csv':
                self.data = pd.read_csv(file)
            else:  # excel
                self.data = pd.read_excel(file)
            
            if self.data.empty:
                return False, "File is empty. Please upload a file with data."
            
            return True, f"Successfully loaded {len(self.data)} records"
            
        except Exception as e:
            return False, f"Error reading file: {str(e)}"
    
    def validate_columns(self) -> Dict:
        """Validate that required columns are present"""
        if self.data is None:
            return {'valid': False, 'message': 'No data loaded'}
        
        columns = self.data.columns.tolist()
        columns_lower = [col.lower().strip() for col in columns]
        
        # Check required columns
        missing_required = []
        for req_col in self.REQUIRED_COLUMNS:
            if req_col not in columns_lower:
                missing_required.append(req_col)
        
        if missing_required:
            return {
                'valid': False,
                'message': f"Missing required columns: {', '.join(missing_required)}",
                'missing': missing_required,
                'present': columns
            }
        
        # Check optional columns
        present_optional = []
        for opt_col in self.OPTIONAL_COLUMNS:
            if opt_col in columns_lower:
                present_optional.append(opt_col)
        
        return {
            'valid': True,
            'message': 'All required columns present',
            'missing': [],
            'present': columns,
            'optional_present': present_optional
        }
    
    def standardize_columns(self):
        """Standardize column names to match expected format"""
        if self.data is None:
            return
        
        # Convert all column names to lowercase and strip whitespace
        self.data.columns = self.data.columns.str.lower().str.strip()
        
        # Rename common variations
        column_mapping = {
            'customerid': 'customer_id',
            'id': 'customer_id',
            'customer': 'customer_id',
            'monthlycharges': 'monthly_charges',
            'monthly_charge': 'monthly_charges',
            'totalcharges': 'total_charges',
            'total_charge': 'total_charges',
        }
        
        self.data.rename(columns=column_mapping, inplace=True)
    
    def clean_data(self) -> Dict:
        """Clean and preprocess the data"""
        if self.data is None:
            return {'success': False, 'message': 'No data to clean'}
        
        results = {
            'original_rows': len(self.data),
            'removed_duplicates': 0,
            'removed_nulls': 0,
            'fixed_types': []
        }
        
        # Remove duplicates
        before = len(self.data)
        self.data.drop_duplicates(subset=['customer_id'], keep='first', inplace=True)
        results['removed_duplicates'] = before - len(self.data)
        
        # Handle missing values in critical columns
        before = len(self.data)
        self.data.dropna(subset=['customer_id', 'tenure', 'monthly_charges'], inplace=True)
        results['removed_nulls'] = before - len(self.data)
        
        # Fix data types
        try:
            self.data['customer_id'] = self.data['customer_id'].astype(str)
            self.data['tenure'] = pd.to_numeric(self.data['tenure'], errors='coerce')
            self.data['monthly_charges'] = pd.to_numeric(self.data['monthly_charges'], errors='coerce')
            results['fixed_types'] = ['customer_id', 'tenure', 'monthly_charges']
        except Exception as e:
            results['type_error'] = str(e)
        
        # Remove rows with invalid numeric values
        self.data = self.data[
            (self.data['tenure'] >= 0) & 
            (self.data['monthly_charges'] > 0)
        ]
        
        results['final_rows'] = len(self.data)
        results['success'] = True
        
        self.processed_data = self.data.copy()
        
        return results
    
    def get_data_summary(self) -> Dict:
        """Get summary statistics of the uploaded data"""
        if self.processed_data is None:
            return {}
        
        summary = {
            'total_customers': len(self.processed_data),
            'avg_tenure': self.processed_data['tenure'].mean(),
            'avg_monthly_charges': self.processed_data['monthly_charges'].mean(),
            'min_tenure': self.processed_data['tenure'].min(),
            'max_tenure': self.processed_data['tenure'].max(),
            'columns': self.processed_data.columns.tolist()
        }
        
        # Add contract distribution if available
        if 'contract' in self.processed_data.columns:
            summary['contract_distribution'] = self.processed_data['contract'].value_counts().to_dict()
        
        return summary
    
    def prepare_for_prediction(self) -> pd.DataFrame:
        """Prepare data for model prediction"""
        if self.processed_data is None:
            return None
        
        # Return a copy of the processed data
        return self.processed_data.copy()
    
    def get_sample_template(self) -> pd.DataFrame:
        """Generate a sample template for users to download"""
        template = pd.DataFrame({
            'customer_id': ['CUST-001', 'CUST-002', 'CUST-003'],
            'tenure': [12, 24, 6],
            'monthly_charges': [65.50, 89.99, 45.00],
            'contract': ['Month-to-month', 'One year', 'Two year'],
            'payment_method': ['Electronic check', 'Bank transfer', 'Credit card'],
            'internet_service': ['Fiber optic', 'DSL', 'No'],
            'total_charges': [786.00, 2159.76, 270.00]
        })
        
        return template


def generate_predictions_for_upload(data: pd.DataFrame) -> pd.DataFrame:
    """
    Generate churn predictions for uploaded customer data
    This is a simulation - replace with actual model in production
    """
    import random
    
    predictions = []
    
    for idx, row in data.iterrows():
        # Simulate prediction based on features
        # In production, this would use your trained model
        
        # Simple heuristic for demo
        tenure = row['tenure']
        monthly_charges = row['monthly_charges']
        
        # Lower tenure and higher charges = higher churn risk
        base_risk = 0.5
        tenure_factor = max(0, (24 - tenure) / 24 * 0.3)
        charge_factor = min(0.2, (monthly_charges - 50) / 100 * 0.2)
        
        churn_probability = base_risk + tenure_factor + charge_factor + random.uniform(-0.1, 0.1)
        churn_probability = max(0.05, min(0.95, churn_probability))
        
        if churn_probability > 0.7:
            risk_level = 'HIGH'
        elif churn_probability > 0.4:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        predictions.append({
            'customer_id': row['customer_id'],
            'churn_probability': round(churn_probability, 3),
            'risk_level': risk_level,
            'prediction': 'Will Churn' if churn_probability > 0.5 else 'Will Stay',
            'tenure': tenure,
            'monthly_charges': monthly_charges
        })
    
    return pd.DataFrame(predictions)


def export_results_to_csv(predictions_df: pd.DataFrame) -> bytes:
    """Export prediction results to CSV for download"""
    output = io.StringIO()
    predictions_df.to_csv(output, index=False)
    return output.getvalue().encode('utf-8')


def export_results_to_excel(predictions_df: pd.DataFrame) -> bytes:
    """Export prediction results to Excel for download"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        predictions_df.to_excel(writer, index=False, sheet_name='Churn Predictions')
    return output.getvalue()
