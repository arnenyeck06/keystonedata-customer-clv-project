"""
"""
Data Processing Module for Dashboard
Handles uploaded data processing, model training, and insights generation
"""
import pandas as pd
import numpy as np
import joblib
import os
import sys
import tempfile
import subprocess
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report,
    confusion_matrix
)
from imblearn.over_sampling import SMOTE
import psycopg2

# Add parent directory to path
sys.path.insert(0, os.path.abspath('..'))

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

def validate_uploaded_data(df):
    """Validate uploaded CSV file has required columns"""
    required_columns = [
        'customerID', 'gender', 'SeniorCitizen', 'Partner', 'Dependents',
        'tenure', 'PhoneService', 'MultipleLines', 'InternetService',
        'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
        'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract',
        'PaperlessBilling', 'PaymentMethod', 'MonthlyCharges',
        'TotalCharges', 'Churn'
    ]

    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        return False, f"Missing required columns: {', '.join(missing_cols)}"

    if len(df) == 0:
        return False, "Uploaded file is empty"

    return True, "Data validated successfully"

# (rest of file unchanged)
