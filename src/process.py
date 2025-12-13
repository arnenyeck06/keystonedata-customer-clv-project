import pandas as pd
import numpy as np
import psycopg2
from cassandra.cluster import Cluster
from datetime import datetime
import json
import argparse
import sys
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# Database configs
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'churn_db',
    'user': 'churn_user',
    'password': 'churn_pass'
}

CASSANDRA_CONFIG = {
    'contact_points': ['localhost'],
    'port': 9042
}

def load_structured_data():
    """Load customer data from PostgreSQL"""
    print("Loading structured data from PostgreSQL...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    query = """
        SELECT 
            customer_id, gender, senior_citizen, partner, dependents,
            tenure, phone_service, multiple_lines, internet_service,
            online_security, online_backup, device_protection,
            tech_support, streaming_tv, streaming_movies, contract,
            paperless_billing, payment_method, monthly_charges,
            total_charges, churn
        FROM customers
    """
    
    df = pd.read_sql(query, conn)
    conn.close()
    
    print(f"Loaded {len(df):,} customer records")
    return df

def clean_data(df):
    """Clean and prepare structured data"""
    print("\nCleaning data...")
    
    original_count = len(df)
    
    # Handle TotalCharges - convert to numeric
    df['total_charges'] = pd.to_numeric(df['total_charges'], errors='coerce')
    
    # Fill missing TotalCharges with MonthlyCharges
    df['total_charges'].fillna(df['monthly_charges'], inplace=True)
    
    # Convert binary columns
    df['senior_citizen'] = df['senior_citizen'].astype(int)
    
    # Drop rows with nulls
    df.dropna(inplace=True)
    
    print(f"Cleaned data: {len(df):,} records (removed {original_count - len(df)} rows)")
    return df

def engineer_basic_features(df):
    """Create basic features from structured data"""
    print("\nEngineering basic features...")
    
    # Tenure categories
    df['tenure_group'] = pd.cut(df['tenure'], 
                                 bins=[0, 12, 24, 48, 72],
                                 labels=['0-1yr', '1-2yr', '2-4yr', '4yr+'])
    
    # Service counts
    service_cols = ['phone_service', 'multiple_lines', 'internet_service',
                    'online_security', 'online_backup', 'device_protection',
                    'tech_support', 'streaming_tv', 'streaming_movies']
    
    df['total_services'] = 0
    for col in service_cols:
        df['total_services'] += (df[col] == 'Yes').astype(int)
    
    # Monthly charges category
    df['charges_category'] = pd.cut(df['monthly_charges'],
                                     bins=[0, 30, 60, 90, 150],
                                     labels=['Low', 'Medium', 'High', 'Very High'])
    
    # Contract risk score
    contract_risk = {
        'Month-to-month': 1.0,
        'One year': 0.5,
        'Two year': 0.2
    }
    df['contract_risk'] = df['contract'].map(contract_risk)
    
    # Payment method risk
    payment_risk = {
        'Electronic check': 1.0,
        'Mailed check': 0.7,
        'Bank transfer (automatic)': 0.3,
        'Credit card (automatic)': 0.3
    }
    df['payment_risk'] = df['payment_method'].map(payment_risk)
    
    # Average monthly revenue
    df['avg_monthly_revenue'] = df['total_charges'] / (df['tenure'] + 1)
    
    # Has family indicator
    df['has_family'] = ((df['partner'] == 'Yes') | (df['dependents'] == 'Yes')).astype(int)
    
    # Internet service indicator
    df['has_internet'] = (df['internet_service'] != 'No').astype(int)
    
    print(f"Created 8 new features")
    return df

def load_event_features():
    """Load and aggregate event data from Cassandra"""
    print("\nLoading event features from Cassandra...")
    
    try:
        cluster = Cluster(**CASSANDRA_CONFIG)
        session = cluster.connect('churn_keyspace')
        
        result = session.execute("SELECT customer_id, event_type, event_data FROM customer_events")
        
        events_data = []
        for row in result:
            events_data.append({
                'customer_id': row.customer_id,
                'event_type': row.event_type,
                'event_data': row.event_data
            })
        
        cluster.shutdown()
        
        if not events_data:
            print("Warning: No events found in Cassandra")
            return pd.DataFrame()
        
        events_df = pd.DataFrame(events_data)
        
        # Aggregate by customer
        event_features = events_df.groupby('customer_id').agg({
            'event_type': 'count'
        }).rename(columns={'event_type': 'total_events'})
        
        # Count specific event types
        event_types = events_df.groupby(['customer_id', 'event_type']).size().unstack(fill_value=0)
        event_features = event_features.join(event_types, how='left')
        event_features.fillna(0, inplace=True)
        
        # Calculate risk indicators
        if 'payment_failed' in event_features.columns:
            event_features['payment_fail_rate'] = event_features['payment_failed'] / (event_features['total_events'] + 1)
        else:
            event_features['payment_fail_rate'] = 0
        
        if 'support_call' in event_features.columns:
            event_features['support_frequency'] = event_features['support_call'] / (event_features['total_events'] + 1)
        else:
            event_features['support_frequency'] = 0
        
        print(f"Extracted event features for {len(event_features):,} customers")
        return event_features.reset_index()
        
    except Exception as e:
        print(f"Error loading events: {e}")
        return pd.DataFrame()

def load_ticket_features():
    """Load and aggregate support ticket data from Cassandra"""
    print("\nLoading ticket features from Cassandra...")
    
    try:
        cluster = Cluster(**CASSANDRA_CONFIG)
        session = cluster.connect('churn_keyspace')
        
        result = session.execute("SELECT customer_id, ticket_type, sentiment FROM support_tickets")
        
        tickets_data = []
        for row in result:
            tickets_data.append({
                'customer_id': row.customer_id,
                'ticket_type': row.ticket_type,
                'sentiment': row.sentiment
            })
        
        cluster.shutdown()
        
        if not tickets_data:
            print("Warning: No tickets found in Cassandra")
            return pd.DataFrame()
        
        tickets_df = pd.DataFrame(tickets_data)
        
        # Aggregate by customer
        ticket_features = tickets_df.groupby('customer_id').agg({
            'ticket_type': 'count'
        }).rename(columns={'ticket_type': 'total_tickets'})
        
        # Sentiment counts
        sentiment_counts = tickets_df.groupby(['customer_id', 'sentiment']).size().unstack(fill_value=0)
        ticket_features = ticket_features.join(sentiment_counts, how='left')
        ticket_features.fillna(0, inplace=True)
        
        # Calculate sentiment score
        if 'negative' in ticket_features.columns and 'positive' in ticket_features.columns:
            ticket_features['sentiment_score'] = (
                ticket_features.get('positive', 0) - ticket_features.get('negative', 0)
            ) / (ticket_features['total_tickets'] + 1)
        else:
            ticket_features['sentiment_score'] = 0
        
        print(f"Extracted ticket features for {len(ticket_features):,} customers")
        return ticket_features.reset_index()
        
    except Exception as e:
        print(f"Error loading tickets: {e}")
        return pd.DataFrame()

def merge_all_features(df, event_features, ticket_features):
    """Merge all features together"""
    print("\nMerging all features...")
    
    # Merge event features
    if not event_features.empty:
        df = df.merge(event_features, on='customer_id', how='left')
        event_cols = [col for col in event_features.columns if col != 'customer_id']
        df[event_cols] = df[event_cols].fillna(0)
    else:
        df['total_events'] = 0
        df['payment_fail_rate'] = 0
        df['support_frequency'] = 0
    
    # Merge ticket features
    if not ticket_features.empty:
        df = df.merge(ticket_features, on='customer_id', how='left')
        ticket_cols = [col for col in ticket_features.columns if col != 'customer_id']
        df[ticket_cols] = df[ticket_cols].fillna(0)
    else:
        df['total_tickets'] = 0
        df['sentiment_score'] = 0
    
    print(f"Merged features: {len(df):,} records")
    return df

def encode_categorical(df):
    """Encode categorical variables"""
    print("\nEncoding categorical variables...")
    
    # Binary encoding
    binary_cols = ['gender', 'partner', 'dependents', 'phone_service', 
                   'paperless_billing', 'churn']
    
    for col in binary_cols:
        if col in df.columns:
            df[col] = (df[col] == 'Yes').astype(int)
    
    # One-hot encoding
    categorical_cols = ['multiple_lines', 'internet_service', 'online_security',
                       'online_backup', 'device_protection', 'tech_support',
                       'streaming_tv', 'streaming_movies', 'contract', 
                       'payment_method', 'tenure_group', 'charges_category']
    
    categorical_cols = [col for col in categorical_cols if col in df.columns]
    df_encoded = pd.get_dummies(df, columns=categorical_cols, drop_first=True)
    
    print(f"Encoded categorical variables. Total features: {len(df_encoded.columns)}")
    return df_encoded

def save_processed_data(df):
    """Save processed data to CSV"""
    print("\nSaving processed data...")
    
    output_path = 'data/processed/processed_churn_data.csv'
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path}")
    print(f"Shape: {df.shape}")
    
    # Save feature list
    feature_cols = [col for col in df.columns if col not in ['customer_id', 'churn']]
    with open('data/processed/feature_list.txt', 'w') as f:
        for col in feature_cols:
            f.write(f"{col}\n")
    print(f"Saved feature list: {len(feature_cols)} features")
    
    # Save statistics
    stats = df.describe()
    stats.to_csv('data/processed/data_statistics.csv')
    print("Saved data statistics")

def process_pipeline():
    """Run the complete processing pipeline"""
    print("=" * 60)
    print("STARTING DATA PROCESSING PIPELINE")
    print("=" * 60)
    
    start_time = datetime.now()
    
    df = load_structured_data()
    df = clean_data(df)
    df = engineer_basic_features(df)
    
    event_features = load_event_features()
    ticket_features = load_ticket_features()
    
    df = merge_all_features(df, event_features, ticket_features)
    df = encode_categorical(df)
    
    save_processed_data(df)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Final dataset: {df.shape[0]:,} rows x {df.shape[1]:,} columns")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Data Processing Pipeline')
    parser.add_argument('--run', action='store_true', help='Run the processing pipeline')
    
    args = parser.parse_args()
    
    if args.run:
        process_pipeline()
    else:
        print("Usage: python src/process.py --run")
